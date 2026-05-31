bl_info = {
    "name": "Origin_move_like_maya",
    "author": "Deepak",
    "version": (1, 4, 0),
    "blender": (4, 5, 3),
    "description": "D: Toggle; LMB: Move; S: Toggle between Mesh (Vert/Edge/Face) and Adaptive Grid.",
    "category": "3D View",
}

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector, Matrix
import math

class ViewportState:
    def __init__(self):
        self.shading_type = {}
        self.show_wireframes = {}
        self.prev_snap = None
        self.prev_snap_elements = None
        self.prev_show_gizmo_object_translate = {}

    def save_and_enable(self, context):
        for area in context.screen.areas:
            if area.type != "VIEW_3D": continue
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    ptr = area.as_pointer()
                    self.shading_type[ptr] = space.shading.type
                    self.show_wireframes[ptr] = space.overlay.show_wireframes
                    space.shading.type = "SOLID"
                    space.overlay.show_wireframes = True
                    self.prev_show_gizmo_object_translate[ptr] = space.show_gizmo_object_translate
                    space.show_gizmo_object_translate = True

        ts = context.scene.tool_settings
        self.prev_snap = ts.use_snap
        self.prev_snap_elements = set(ts.snap_elements)
        ts.use_snap = True
        ts.snap_elements = {'VERTEX', 'EDGE', 'FACE'}

    def restore(self, context):
        for area in context.screen.areas:
            if area.type != "VIEW_3D": continue
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    ptr = area.as_pointer()
                    if ptr in self.shading_type: space.shading.type = self.shading_type[ptr]
                    if ptr in self.show_wireframes: space.overlay.show_wireframes = self.show_wireframes[ptr]
                    if ptr in self.prev_show_gizmo_object_translate:
                        space.show_gizmo_object_translate = self.prev_show_gizmo_object_translate[ptr]

        ts = context.scene.tool_settings
        if self.prev_snap is not None: ts.use_snap = self.prev_snap
        if self.prev_snap_elements is not None: ts.snap_elements = set(self.prev_snap_elements)


class VIEW3D_OT_pivot_move_snap_modal(bpy.types.Operator):
    bl_idname = "view3d.pivot_move_snap_modal_toggle"
    bl_label = "Pivot Move Snap (Toggle)"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    
    is_active = False
    snapping_mode = 'GEOM' 

    def _get_adaptive_grid_size(self, context):
        rv3d = context.region_data
        dist = rv3d.view_distance
        base_grid_scale = context.space_data.overlay.grid_scale
        exponent = math.floor(math.log10(dist)) if dist > 0 else 0
        adaptive_step = (10 ** exponent) * 0.1 * base_grid_scale
        return max(adaptive_step, 0.0001)

    def invoke(self, context, event):
        if VIEW3D_OT_pivot_move_snap_modal.is_active:
            self._finish_and_restore(context)
            VIEW3D_OT_pivot_move_snap_modal.is_active = False
            context.workspace.status_text_set(None)
            return {'FINISHED'}

        if context.area.type != 'VIEW_3D' or context.mode != 'OBJECT':
            self.report({'WARNING'}, "Object Mode in 3D View required")
            return {'CANCELLED'}

        self.viewport_state = ViewportState()
        self.dragging = False
        self.viewport_state.save_and_enable(context)
        context.window_manager.modal_handler_add(self)
        context.workspace.status_text_set("Pivot Edit: LMB drag | D: Exit | S: Toggle Mesh/Grid Snap")
        VIEW3D_OT_pivot_move_snap_modal.is_active = True
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        obj = context.active_object
        if not obj: return {'CANCELLED'}

        if event.type == 'D' and event.value == 'PRESS':
            self._finish_and_restore(context)
            VIEW3D_OT_pivot_move_snap_modal.is_active = False
            context.workspace.status_text_set(None)
            return {'FINISHED'}

        if event.type == 'S' and event.value == 'PRESS':
            self.snapping_mode = 'GRID' if self.snapping_mode == 'GEOM' else 'GEOM'
            self.report({'INFO'}, f"Snapping Mode: {'MESH (V/E/F)' if self.snapping_mode == 'GEOM' else 'ADAPTIVE GRID'}")
            return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE':
            self.dragging = (event.value == 'PRESS')
            return {'RUNNING_MODAL'}

        if self.dragging and event.type == 'MOUSEMOVE':
            self._update_pivot_from_mouse(context, event, obj)
            return {'RUNNING_MODAL'}

        if event.type in {'ESC', 'RIGHTMOUSE'}:
            self._finish_and_restore(context)
            VIEW3D_OT_pivot_move_snap_modal.is_active = False
            context.workspace.status_text_set(None)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def _update_pivot_from_mouse(self, context, event, obj):
        region = context.region
        rv3d = context.region_data
        coord = (event.mouse_region_x, event.mouse_region_y)
        deps = context.evaluated_depsgraph_get()
        
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        ray_dir = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)

        hit_obj, hit_loc, _, _, _, _ = context.scene.ray_cast(deps, ray_origin, ray_dir)
        target_world = hit_loc if hit_obj else None

        refined_loc = self._snap_refine(context, event, target_world, ray_origin, ray_dir, obj)
        if refined_loc:
            target_world = refined_loc

        if target_world is None:
            dist = (obj.location - ray_origin).length
            target_world = ray_origin + ray_dir * dist
            if self.snapping_mode == 'GRID':
                g_size = self._get_adaptive_grid_size(context)
                target_world = Vector((round(target_world.x / g_size) * g_size,
                                       round(target_world.y / g_size) * g_size,
                                       round(target_world.z / g_size) * g_size))

        self._move_origin_only(obj, target_world)
        context.area.tag_redraw()

    def _snap_refine(self, context, event, surface_hit_loc, ray_origin, ray_dir, obj):
        if self.snapping_mode == 'GRID':
            grid_size = self._get_adaptive_grid_size(context)
            base_pos = surface_hit_loc if surface_hit_loc else (ray_origin + ray_dir * (obj.location - ray_origin).length)
            return Vector((round(base_pos.x / grid_size) * grid_size,
                          round(base_pos.y / grid_size) * grid_size,
                          round(base_pos.z / grid_size) * grid_size))

        # --- GEOMETRY SNAPPING (Restored Vertex, Edge, Face) ---
        region = context.region
        rv3d = context.region_data
        mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        deps = context.evaluated_depsgraph_get()
        
        threshold_px = 25.0
        best_loc = None
        best_dist_sq = threshold_px**2
        cam_pos = rv3d.view_matrix.inverted().translation
        surface_depth = (surface_hit_loc - cam_pos).length if surface_hit_loc else float('inf')

        for ob in context.visible_objects:
            if ob.type not in {'MESH', 'CURVE', 'FONT', 'SURFACE'}: continue
            mw = ob.matrix_world
            try:
                eval_obj = ob.evaluated_get(deps)
                mesh = eval_obj.to_mesh()
            except: continue
            if not mesh: continue

            # Create list of all possible snap points
            points = [mw @ v.co for v in mesh.vertices] # Vertices
            points += [(mw @ mesh.vertices[e.vertices[0]].co + mw @ mesh.vertices[e.vertices[1]].co) * 0.5 for e in mesh.edges] # Edge Midpoints
            points += [mw @ p.center for p in mesh.polygons] # Face Centers

            for p_world in points:
                p_depth = (p_world - cam_pos).length
                # Depth buffer: only snap to things not hidden behind faces
                if p_depth > surface_depth + 0.05: continue 
                
                screen_p = view3d_utils.location_3d_to_region_2d(region, rv3d, p_world)
                if screen_p:
                    d_sq = (screen_p - mouse_pos).length_squared
                    if d_sq < best_dist_sq:
                        best_dist_sq = d_sq
                        best_loc = p_world
            eval_obj.to_mesh_clear()
            
        return best_loc

    def _move_origin_only(self, obj, new_origin_world):
        if not hasattr(obj.data, "transform"): return
        M = obj.matrix_world.copy()
        offset_world = new_origin_world - M.translation
        M_no_trans = M.copy()
        M_no_trans.translation = (0,0,0)
        offset_local = M_no_trans.inverted() @ offset_world
        obj.data.transform(Matrix.Translation(-offset_local))
        if hasattr(obj.data, "update"): obj.data.update()
        obj.location = new_origin_world

    def _finish_and_restore(self, context):
        try: self.viewport_state.restore(context)
        except: pass

addon_keymaps = []

def register():
    bpy.utils.register_class(VIEW3D_OT_pivot_move_snap_modal)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(VIEW3D_OT_pivot_move_snap_modal.bl_idname, 'D', 'PRESS')
        addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps: km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(VIEW3D_OT_pivot_move_snap_modal)

if __name__ == "__main__":
    register()