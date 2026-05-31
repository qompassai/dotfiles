bl_info = {
    "name": "Face Angle Analyzer v8.94",
    "author": "Astralis",
    "version": (8, 9, 4),
    "blender": (3, 6, 0),
    "location": "3D Viewport > Sidebar > FAA",
    "description": "Calculates and visualizes face orientation angles as a 2D overlay.",
    "warning": "This is a modal operator. Press ESC to stop.",
    "doc_url": "",
    "category": "Mesh",
}

import bpy
import bmesh
from mathutils import Vector, Euler
from math import degrees, radians
import gpu
from gpu_extras.batch import batch_for_shader
import blf 
import bpy_extras.view3d_utils

# Global variable to track running operator instance
_running_operator_v6 = None

# --- Helper: 2D Arc Generation ---
def get_arc_points(center, v_from, v_to, radius, steps=24):
    """Generates 3D vertices for a circular arc between two vectors."""
    angle_rad = v_from.angle(v_to)
    if angle_rad < radians(1.0): 
        return []
    axis = v_from.cross(v_to).normalized()
    if axis.length < 1e-6:
        return []

    from mathutils import Matrix
    verts = []
    for i in range(steps + 1):
        t = i / steps
        rot_mat = Matrix.Rotation(angle_rad * t, 4, axis)
        verts.append(center + (rot_mat @ v_from.normalized()) * radius)
    return verts

# --- Main Modal Operator ---
class MESH_OT_FAA_Visualize_v6(bpy.types.Operator):
    bl_idname = "mesh.faa_visualize_v6"
    bl_label = "Calculate & Visualize Face"
    bl_description = "Calculates face orientation and draws a live 2D overlay. Press ESC to stop."
    bl_options = {'REGISTER', 'UNDO'}

    # --- Internal Operator Variables ---
    _draw_handle = None
    _shader_2d = None
    
    start_point_3d: Vector = None
    face_normal_3d: Vector = None
    line_length: float = 1.0
    base_line_length: float = 1.0  # Store the base line length
    arc_radius: float = 0.25
    
    # Angle results
    angles_text: str = "Calculating..."
    angle_simple_x: float = 0.0
    angle_simple_y: float = 0.0
    angle_simple_z: float = 0.0
    
    # Colors
    color_line = (0.2, 1.0, 1.0, 1.0) # Turquoise
    color_ball = (1.0, 0.2, 0.0, 1.0) # Orange-Red
    color_x = (1.0, 0.0, 0.0, 1.0) # Red
    color_y = (0.0, 1.0, 0.0, 1.0) # Green
    color_z = (0.259, 0.522, 1.0, 1.0) # Blue
    
    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH' and
                context.object is not None and
                context.object.type == 'MESH')
    
    def calculate_face_data(self, context):
        """Calculate all face data and angles. Returns True on success, False on failure."""
        obj = context.edit_object
        me = obj.data
        
        # Get bmesh from edit mesh
        bm = bmesh.from_edit_mesh(me)
        
        # CRITICAL: Ensure the bmesh is synced and lookup tables are updated
        bm.faces.ensure_lookup_table()
        
        selected_faces = [f for f in bm.faces if f.select]

        if not selected_faces:
            self.report({'WARNING'}, "No face selected. Please select a face in Edit Mode.")
            return False

        # Get the first selected face
        sel_face = selected_faces[0]
        
        # Calculate base line length based on average edge length
        edges = sel_face.edges
        if edges:
            total_length = 0.0
            for edge in edges:
                v1_co = obj.matrix_world @ edge.verts[0].co
                v2_co = obj.matrix_world @ edge.verts[1].co
                total_length += (v1_co - v2_co).length
            self.base_line_length = total_length / len(edges)
        
        # Apply the length multiplier from the UI
        self.line_length = self.base_line_length * context.scene.faa_props_v6.normal_line_length_multiplier
        
        # Get face center and normal in world space
        self.start_point_3d = obj.matrix_world @ sel_face.calc_center_median()
        self.face_normal_3d = (obj.matrix_world.to_3x3() @ sel_face.normal).normalized()

        # Calculate simple angles (angle between face normal and each axis)
        self.angle_simple_x = degrees(self.face_normal_3d.angle(Vector((1,0,0))))
        self.angle_simple_y = degrees(self.face_normal_3d.angle(Vector((0,1,0))))
        self.angle_simple_z = degrees(self.face_normal_3d.angle(Vector((0,0,1))))

        # Calculate rotational angles to match reference plane
        ref_vector = get_native_vector(context.scene.faa_native_plane_v6)
        quat_diff = ref_vector.rotation_difference(self.face_normal_3d)
        euler_diff = quat_diff.to_euler('XYZ')
        rot_X = degrees(euler_diff.x)
        rot_Y = degrees(euler_diff.y)
        rot_Z = degrees(euler_diff.z)
        
        native_name = {"X": "X-Axis", "Y": "Y-Axis", "Z": "Z-Axis"}
        self.angles_text = (
            f"Angle from Axes:\n"
            f"  X-Axis: {self.angle_simple_x:.2f} deg\n"
            f"  Y-Axis: {self.angle_simple_y:.2f} deg\n"
            f"  Z-Axis: {self.angle_simple_z:.2f} deg\n"
            f"\n"
            f"Reference Plane: {native_name[context.scene.faa_native_plane_v6]}\n"
            f"Euler Angle to Plane:\n"
            f"  X-Axis (Pitch): {rot_X:.2f} deg\n"
            f"  Y-Axis (Yaw): {rot_Y:.2f} deg\n"
            f"  Z-Axis (Roll): {rot_Z:.2f} deg"
        )
        
        self.arc_radius = context.scene.faa_props_v6.arc_radius
        
        # Store line thickness settings
        self.line_thickness_normal = context.scene.faa_props_v6.line_thickness_normal
        self.line_thickness_axes = context.scene.faa_props_v6.line_thickness_axes
        
        return True

    def invoke(self, context, event):
        """Called when the operator is first run."""
        global _running_operator_v6
        
        # If already running, recalculate with new selection
        if _running_operator_v6 is not None:
            if not _running_operator_v6.calculate_face_data(context):
                return {'CANCELLED'}
            context.area.tag_redraw()
            self.report({'INFO'}, "FAA recalculated for new face selection.")
            return {'FINISHED'}
        
        # First time running - calculate and start modal
        if not self.calculate_face_data(context):
            return {'CANCELLED'}
        
        # Initialize shader
        if not self._shader_2d:
            self._shader_2d = gpu.shader.from_builtin('UNIFORM_COLOR')
            
        # Add draw handler
        self._draw_handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback_2d_modal_v6, (self, context), 'WINDOW', 'POST_PIXEL'
        )
        
        # Set global reference to this operator
        _running_operator_v6 = self
        
        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        
        self.report({'INFO'}, "FAA visualization active. Press ESC to stop.")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # Check if properties have been updated and recalculate if needed
        if event.type == 'TIMER':
            # Update line length dynamically when the slider changes
            self.line_length = self.base_line_length * context.scene.faa_props_v6.normal_line_length_multiplier
            self.arc_radius = context.scene.faa_props_v6.arc_radius
            self.line_thickness_normal = context.scene.faa_props_v6.line_thickness_normal
            self.line_thickness_axes = context.scene.faa_props_v6.line_thickness_axes
            context.area.tag_redraw()
        
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cleanup()
            self.report({'INFO'}, "FAA visualization stopped.")
            return {'CANCELLED'}
            
        if not context.area or context.area.type != 'VIEW_3D':
            self.cleanup()
            self.report({'WARNING'}, "FAA stopped: View context lost.")
            return {'CANCELLED'}

        if event.type == 'MOUSEMOVE':
            context.area.tag_redraw()

        return {'PASS_THROUGH'}

    def cleanup(self):
        global _running_operator_v6
        
        if self._draw_handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_handle, 'WINDOW')
            self._draw_handle = None
        
        _running_operator_v6 = None
        
        # Redraw the 3D view to clear the overlay
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

# --- New 2D Drawing Function (Tied to the Operator) ---
def draw_callback_2d_modal_v6(self, context):
    start_point_3d = self.start_point_3d
    face_normal_3d = self.face_normal_3d
    
    if not start_point_3d or not face_normal_3d:
        return
    
    # Dynamically update line length from the property
    line_length = self.base_line_length * context.scene.faa_props_v6.normal_line_length_multiplier
    axis_length = line_length * 0.75
    arc_radius = context.scene.faa_props_v6.arc_radius
    
    # Update thickness values dynamically
    line_thickness_normal = context.scene.faa_props_v6.line_thickness_normal
    line_thickness_axes = context.scene.faa_props_v6.line_thickness_axes

    normal_tip_3d = start_point_3d + face_normal_3d * line_length
    x_axis_vec = Vector((1.0, 0.0, 0.0))
    y_axis_vec = Vector((0.0, 1.0, 0.0))
    z_axis_vec = Vector((0.0, 0.0, 1.0))

    # Convert 3D to 2D
    def to_2d(point_3d):
        return bpy_extras.view3d_utils.location_3d_to_region_2d(
            context.region, context.space_data.region_3d, point_3d
        )
    
    start_2d = to_2d(start_point_3d)
    normal_tip_2d = to_2d(normal_tip_3d)
    
    if not start_2d or not normal_tip_2d:
        return
    
    shader = self._shader_2d
    if not shader:
        return

    # Draw thick lines using multiple passes
    def draw_thick_line(start, end, color, thickness):
        import math
        perpendicular = Vector((end.y - start.y, start.x - end.x)).normalized()
        
        for offset in range(-int(thickness/2), int(thickness/2) + 1):
            offset_vec = perpendicular * offset * 0.5
            verts = [
                (start.x + offset_vec.x, start.y + offset_vec.y),
                (end.x + offset_vec.x, end.y + offset_vec.y)
            ]
            batch = batch_for_shader(shader, 'LINES', {"pos": verts})
            shader.uniform_float("color", color)
            batch.draw(shader)
    
    # Draw main normal line with dynamic thickness
    draw_thick_line(start_2d, normal_tip_2d, self.color_line, line_thickness_normal)
    
    # Draw endpoint ball
    gpu.state.point_size_set(12.0)
    batch = batch_for_shader(shader, 'POINTS', {"pos": [(normal_tip_2d.x, normal_tip_2d.y)]})
    shader.uniform_float("color", self.color_ball)
    batch.draw(shader)
    
    # Draw starting point
    gpu.state.point_size_set(8.0)
    batch = batch_for_shader(shader, 'POINTS', {"pos": [(start_2d.x, start_2d.y)]})
    shader.uniform_float("color", self.color_line)
    batch.draw(shader)

    # Draw axis lines and arcs
    font_id = 0
    blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
    blf.size(font_id, 40)
    blf.position(font_id, 10, context.area.height - 50, 0)
    blf.draw(font_id, "Face Angle Analyzer")
    
    # Draw angle text info
    y_offset = context.area.height - 80
    for line in self.angles_text.split('\n'):
        blf.position(font_id, 10, y_offset, 0)
        blf.size(font_id, 14)
        blf.draw(font_id, line)
        y_offset -= 20

    # Draw axis visualizations
    def draw_visuals_for_axis(axis_vec_3d, color, angle):
        axis_tip_3d = start_point_3d + axis_vec_3d * axis_length
        axis_tip_2d = to_2d(axis_tip_3d)
        
        if not axis_tip_2d:
            return
        
        draw_thick_line(start_2d, axis_tip_2d, color, line_thickness_axes)
        
        gpu.state.point_size_set(6.0)
        batch = batch_for_shader(shader, 'POINTS', {"pos": [(axis_tip_2d.x, axis_tip_2d.y)]})
        shader.uniform_float("color", color)
        batch.draw(shader)
        
        # Draw arc
        arc_verts_3d = get_arc_points(start_point_3d, axis_vec_3d, face_normal_3d, arc_radius)
        arc_verts_2d = [to_2d(v) for v in arc_verts_3d]
        arc_verts_2d = [v for v in arc_verts_2d if v is not None]
        
        if len(arc_verts_2d) > 1:
            for i in range(len(arc_verts_2d) - 1):
                draw_thick_line(arc_verts_2d[i], arc_verts_2d[i + 1], color, 1.5)
        
        text = f"{angle:.1f} deg"
        mid_vec_3d = (axis_vec_3d.normalized() + face_normal_3d.normalized()).normalized()
        text_pos_3d = start_point_3d + mid_vec_3d * (arc_radius * 2.5)
        text_pos_2d = to_2d(text_pos_3d)
        
        if text_pos_2d:
            blf.color(font_id, color[0], color[1], color[2], 1.0)
            blf.size(font_id, 32)
            blf.position(font_id, text_pos_2d.x + 20, text_pos_2d.y + 20, 0)
            blf.draw(font_id, text)

    # Get visibility settings
    props = context.scene.faa_props_v6
    
    if props.show_x_axis:
        draw_visuals_for_axis(x_axis_vec, self.color_x, self.angle_simple_x)
    if props.show_y_axis:
        draw_visuals_for_axis(y_axis_vec, self.color_y, self.angle_simple_y)
    if props.show_z_axis:
        draw_visuals_for_axis(z_axis_vec, self.color_z, self.angle_simple_z)

    gpu.state.point_size_set(1.0)


# --- Stop Operator ---
class MESH_OT_FAA_Stop_v6(bpy.types.Operator):
    bl_idname = "mesh.faa_stop_v6"
    bl_label = "Stop FAA Visualization"
    bl_description = "Stop the FAA visualization overlay"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global _running_operator_v6
        
        if _running_operator_v6:
            _running_operator_v6.cleanup()
            _running_operator_v6 = None
            self.report({'INFO'}, "FAA visualization stopped.")
        
        return {'FINISHED'}


# --- Helper Function ---
def get_native_vector(native_plane):
    if native_plane == 'X': return Vector((1.0, 0.0, 0.0))
    elif native_plane == 'Y': return Vector((0.0, 1.0, 0.0))
    elif native_plane == 'Z': return Vector((0.0, 0.0, 1.0))
    return Vector((0.0, 0.0, 1.0)) 

# --- Panel ---
class VIEW3D_PT_face_angle_analyzer_v6(bpy.types.Panel):
    bl_label = "Face Angle Analyzer"
    bl_idname = "VIEW3D_PT_FAA_PANEL_v6"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "FAA" 

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Check if operator is running
        global _running_operator_v6
        is_running = _running_operator_v6 is not None

        row = layout.row(align=True)
        if is_running:
            row.operator(MESH_OT_FAA_Visualize_v6.bl_idname, 
                        text="Recalculate", 
                        icon='FILE_REFRESH')
            row.operator("mesh.faa_stop_v6",
                        text="Stop", 
                        icon='CANCEL')
        else:
            row.operator(MESH_OT_FAA_Visualize_v6.bl_idname, 
                        text="Calculate & Visualize", 
                        icon='PLAY')

        layout.separator()

        box = layout.box()
        
        if is_running and _running_operator_v6:
            lines = _running_operator_v6.angles_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Section headers
                if line == "Angle from Axes:":
                    box.label(text=line, icon='DRIVER_ROTATIONAL_DIFFERENCE')
                    current_section = "angles"
                elif line.startswith("Reference Plane:"):
                    layout.separator()
                    box = layout.box()
                    box.label(text="Reference Native Plane:", icon='ORIENTATION_GLOBAL')
                    plane_name = line.split(": ")[1]
                    box.prop(scene, "faa_native_plane_v6", text="")
                    current_section = "reference"
                elif line == "Euler Angle to Plane:":
                    box.label(text="Euler Angle to Plane:", icon='CON_ROTLIKE')
                    current_section = "rotation"
                elif ":" in line:
                    # Data lines
                    key, val = line.split(":", 1)
                    row = box.row(align=True)
                    row.label(text=key.strip() + ":")
                    row.label(text=val.strip())
        else:
            box.label(text="No Face Selected.")

        layout.separator()

        box = layout.box()
        box.label(text="Visualization Settings:", icon='OUTLINER_OB_EMPTY')
        
        # FIXED: Properly organized line properties
        box.label(text="Line Properties:")
        box.prop(scene.faa_props_v6, "normal_line_length_multiplier", text="Normal Line Length")  # Controls LENGTH
        box.prop(scene.faa_props_v6, "line_thickness_normal", text="Normal Line Thickness")  # Controls THICKNESS
        box.prop(scene.faa_props_v6, "line_thickness_axes", text="Axis Line Thickness")
        
        box.prop(scene.faa_props_v6, "arc_radius", text="Arc Radius")
        
        box.label(text="Show Axes:")
        row = box.row(align=True)
        row.prop(scene.faa_props_v6, "show_x_axis", text="X", toggle=True)
        row.prop(scene.faa_props_v6, "show_y_axis", text="Y", toggle=True)
        row.prop(scene.faa_props_v6, "show_z_axis", text="Z", toggle=True)


# --- Registration ---

def update_drawing_settings_v6(self, context):
    # Force a redraw when properties change
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

class FAA_Properties_v6(bpy.types.PropertyGroup):
    arc_radius: bpy.props.FloatProperty(
        name="Arc Radius",
        description="Radius of the angle visualization arcs",
        default=0.25, min=0.01, max=5.0, precision=3,
        update=update_drawing_settings_v6
    )
    normal_line_length_multiplier: bpy.props.FloatProperty(
        name="Normal Line Length",
        description="Length multiplier for the face normal visualization line",
        default=1.0, min=0.1, max=5.0, precision=2,
        update=update_drawing_settings_v6
    )
    line_thickness_normal: bpy.props.FloatProperty(
        name="Normal Line Thickness",
        description="Thickness of the face normal line",
        default=4.0, min=1.0, max=20.0, precision=1,
        update=update_drawing_settings_v6
    )
    line_thickness_axes: bpy.props.FloatProperty(
        name="Axes Line Thickness",
        description="Thickness of the axis lines",
        default=2.0, min=1.0, max=20.0, precision=1,
        update=update_drawing_settings_v6
    )
    show_x_axis: bpy.props.BoolProperty(
        name="Show X-Axis",
        description="Display X-axis line, arc, and angle",
        default=True,
        update=update_drawing_settings_v6
    )
    show_y_axis: bpy.props.BoolProperty(
        name="Show Y-Axis",
        description="Display Y-axis line, arc, and angle",
        default=True,
        update=update_drawing_settings_v6
    )
    show_z_axis: bpy.props.BoolProperty(
        name="Show Z-Axis",
        description="Display Z-axis line, arc, and angle",
        default=True,
        update=update_drawing_settings_v6
    )

classes = (
    MESH_OT_FAA_Visualize_v6,
    MESH_OT_FAA_Stop_v6,
    VIEW3D_PT_face_angle_analyzer_v6,
    FAA_Properties_v6, 
)

def register_properties():
    bpy.types.Scene.faa_native_plane_v6 = bpy.props.EnumProperty(
        name="Native Plane",
        description="The global axis plane (normal) to compare the selected face against.",
        items=[
            ('Z', "Z-Axis (Up)", "Compare to the global Z-axis"),
            ('Y', "Y-Axis (Forward)", "Compare to the global Y-axis"),
            ('X', "X-Axis (Side)", "Compare to the global X-axis"),
        ],
        default='Z',
    )
    bpy.types.Scene.faa_props_v6 = bpy.props.PointerProperty(type=FAA_Properties_v6)

def unregister_properties():
    del bpy.types.Scene.faa_native_plane_v6
    del bpy.types.Scene.faa_props_v6 

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    register_properties()

def unregister():
    global _running_operator_v6
    
    # Stop any running operator
    if _running_operator_v6:
        _running_operator_v6.cleanup()
        _running_operator_v6 = None

    unregister_properties()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == '__main__':
    try:
        unregister()
    except Exception:
        pass
    register()