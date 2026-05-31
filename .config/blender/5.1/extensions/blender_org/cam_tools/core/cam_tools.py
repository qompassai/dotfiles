import bpy
import re
import mathutils
import bpy_extras
from bpy.app.handlers import persistent
from bpy.types import Operator, Panel, UIList, PropertyGroup, Menu
from bpy.props import IntProperty, PointerProperty, StringProperty, BoolProperty, EnumProperty

# ------------------------------------------------------------------------
# Internal State
# ------------------------------------------------------------------------

_is_syncing_camtools = False
_camtools_msgbus_owner = object()

# ------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------

def get_view3d_area_space(context):
    win = context.window
    if not win:
        return None, None, None

    for area in win.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            if not space or space.type != 'VIEW_3D':
                continue
            region = None
            for reg in area.regions:
                if reg.type == 'WINDOW':
                    region = reg
                    break
            if region:
                return area, space, region
    return None, None, None

def ensure_camera_collection(scene):
    root = scene.collection
    coll = root.children.get("Cameras")
    if coll is None:
        coll = bpy.data.collections.new("Cameras")
        root.children.link(coll)
    return coll

def get_target_camera(context):
    obj = context.view_layer.objects.active
    if obj and obj.type == 'CAMERA':
        return obj
    cam = context.scene.camera
    if cam and cam.type == 'CAMERA':
        return cam
    return None

def get_camera_groups(self, context):
    items = [("ALL", "All Cameras", "")]
    # Safety check for dynamic enum execution during add-on registration
    if context is None:
        return items
        
    scene = getattr(context, "scene", None)
    if not scene:
        scene = bpy.context.scene
        
    if scene:
        root = scene.collection
        cams_coll = root.children.get("Cameras")
        if cams_coll:
            for child in cams_coll.children:
                items.append((child.name, child.name, ""))
    return items

def get_unique_camera_name(original_name):
    clean_name = re.sub(r'(?:\.\d+|_copy|_\d+)+$', '', original_name)
    if not clean_name:
        clean_name = "Camera"
        
    existing_names = set(obj.name for obj in bpy.data.objects)
    highest_num = 0
    base_exists = False
    
    pattern = re.compile(r'^' + re.escape(clean_name) + r'(?:_(\d+))?$')
    
    for name in existing_names:
        m = pattern.match(name)
        if m:
            if name == clean_name:
                base_exists = True
            if m.group(1):
                num = int(m.group(1))
                if num > highest_num:
                    highest_num = num
                    
    if not base_exists and highest_num == 0:
        return clean_name
        
    new_num = highest_num + 1
    return f"{clean_name}_{new_num:02d}"

def sync_active_camera_index(context):
    global _is_syncing_camtools
    scene = context.scene
    if not hasattr(scene, "camtools"):
        return
        
    active = context.view_layer.objects.active
    if active and active.type == 'CAMERA':
        idx = scene.objects.find(active.name)
        if idx != -1 and scene.camtools.camera_index != idx:
            _is_syncing_camtools = True
            try:
                scene.camtools.camera_index = idx
            finally:
                _is_syncing_camtools = False

def clear_batch_checkmarks(scene):
    for obj in scene.objects:
        if obj.type == 'CAMERA' and hasattr(obj, "camtools"):
            obj.camtools.selected_for_ops = False

def perform_grouping(context, group_name, operator=None):
    scene = context.scene
    cams_marked = [
        obj for obj in scene.objects
        if obj.type == 'CAMERA' and hasattr(obj, "camtools") and obj.camtools.selected_for_ops
    ]
    
    cams_to_group = list(cams_marked)

    if not cams_to_group:
        active = context.view_layer.objects.active
        if active and active.type == 'CAMERA':
            cams_to_group = [active]
        else:
            if operator:
                operator.report({'WARNING'}, "No cameras marked or selected")
            return {'CANCELLED'}

    cams_coll = ensure_camera_collection(scene)
    sub_coll = cams_coll.children.get(group_name)
    
    if not sub_coll:
        sub_coll = bpy.data.collections.new(group_name)
        cams_coll.children.link(sub_coll)

    for cam in cams_to_group:
        for c in list(cam.users_collection):
            try:
                c.objects.unlink(cam)
            except RuntimeError:
                pass
        
        try:
            if cam.name not in sub_coll.objects:
                sub_coll.objects.link(cam)
        except Exception:
            # Fallback to prevent orphaned data if linking fails
            if cam.name not in cams_coll.objects:
                cams_coll.objects.link(cam)

    clear_batch_checkmarks(scene)
    sync_active_camera_index(context)
    return {'FINISHED'}

# ------------------------------------------------------------------------
# Properties
# ------------------------------------------------------------------------

def update_camera_index(self, context):
    if context is None:
        return

    scene = context.scene
    if not scene or not hasattr(scene, "camtools"):
        return

    idx = scene.camtools.camera_index
    objs = scene.objects
    
    if idx < 0 or idx >= len(objs):
        return

    obj = objs[idx]
    if obj.type != 'CAMERA':
        return

    view_layer = context.view_layer
    if not view_layer:
        return

    for o in list(view_layer.objects):
        if o.select_get():
            o.select_set(False)

    obj.select_set(True)
    view_layer.objects.active = obj

class CamToolsSceneProps(PropertyGroup):
    camera_index: IntProperty(
        name="Camera Index",
        default=0,
        min=0,
        update=update_camera_index,
    )
    camera_group_filter: EnumProperty(
        name="Filter Group",
        items=get_camera_groups,
    )
    show_composition_guides: BoolProperty(
        name="Composition Guides",
        default=True,
    )
    show_dof: BoolProperty(
        name="Depth of Field",
        default=False, 
    )
    show_viewport_display: BoolProperty(
        name="Viewport Display",
        default=False,
    )

class CamToolsObjectProps(PropertyGroup):
    selected_for_ops: BoolProperty(
        name="Batch Select",
        default=False,
    )

# ------------------------------------------------------------------------
# MsgBus Sync
# ------------------------------------------------------------------------

def _camtools_on_active_change(*_args):
    global _is_syncing_camtools
    if _is_syncing_camtools:
        return

    context = bpy.context
    if not context or not context.window or not context.view_layer:
        return

    scene = context.scene
    if not scene or not hasattr(scene, "camtools"):
        return

    active = context.view_layer.objects.active
    if not active or active.type != 'CAMERA':
        return

    idx = scene.objects.find(active.name)
    if idx == -1 or scene.camtools.camera_index == idx:
        return

    _is_syncing_camtools = True
    try:
        scene.camtools.camera_index = idx
    finally:
        _is_syncing_camtools = False

def _camtools_msgbus_subscribe():
    bpy.msgbus.clear_by_owner(_camtools_msgbus_owner)
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.LayerObjects, "active"),
        owner=_camtools_msgbus_owner,
        args=(),
        notify=_camtools_on_active_change,
        options={'PERSISTENT'},
    )

def _camtools_msgbus_unsubscribe():
    bpy.msgbus.clear_by_owner(_camtools_msgbus_owner)

@persistent
def _camtools_load_post(_dummy):
    _camtools_msgbus_subscribe()

# ------------------------------------------------------------------------
# UI List
# ------------------------------------------------------------------------

class CAMTOOLS_UL_cameras(UIList):
    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flt_flags = []
        
        scene = context.scene
        filter_group = scene.camtools.camera_group_filter

        valid_cams = set()
        if filter_group != "ALL":
            root = scene.collection
            cams_coll = root.children.get("Cameras")
            if cams_coll:
                target_coll = cams_coll.children.get(filter_group)
                if target_coll:
                    valid_cams = set(target_coll.objects)

        for obj in items:
            if getattr(obj, "type", "") == 'CAMERA':
                if filter_group == "ALL" or obj in valid_cams:
                    flt_flags.append(self.bitflag_filter_item)
                else:
                    flt_flags.append(0)
            else:
                flt_flags.append(0)

        flt_neworder = bpy.types.UI_UL_list.sort_items_by_name(items, "name")
        return flt_flags, flt_neworder

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        obj = item
        if obj.type != 'CAMERA':
            return

        scene = context.scene
        row = layout.row(align=True)

        icon_cam = 'CAMERA_DATA'
        if scene.camera == obj:
            icon_cam = 'OUTLINER_OB_CAMERA'

        op = row.operator("camtools.activate_camera", text="", icon=icon_cam)
        op.camera_name = obj.name

        row.prop(obj, "name", text="", emboss=False)

        if scene.camtools.camera_group_filter == "ALL":
            cams_coll = scene.collection.children.get("Cameras")
            if cams_coll:
                for c in obj.users_collection:
                    if c.name in cams_coll.children.keys():
                        tag_row = row.row()
                        tag_row.active = False
                        tag_row.label(text=f"[{c.name}]")
                        break

        row.prop(obj, "hide_render", text="")
        row.separator(factor=1.5)
        row.prop(obj.camtools, "selected_for_ops", text="")

# ------------------------------------------------------------------------
# Core Operators
# ------------------------------------------------------------------------

class VIEW3D_OT_add_camera_from_view_exact(Operator):
    bl_idname = "view3d.add_camera_from_view_exact"
    bl_label = "Add Camera From View"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        area, space, region = get_view3d_area_space(context)
        if not area or not space or not region:
            self.report({'ERROR'}, "No 3D Viewport found")
            return {'CANCELLED'}

        if space.type != 'VIEW_3D':
            self.report({'ERROR'}, "Active space is not a 3D View")
            return {'CANCELLED'}

        r3d = space.region_3d
        scene = context.scene

        new_cam_focal = space.lens / 2.0
        if scene.camera and scene.camera.type == 'CAMERA' and r3d.view_perspective == 'CAMERA':
            if getattr(space, "use_local_camera", False) and space.camera and space.camera.type == 'CAMERA':
                new_cam_focal = space.camera.data.lens
            else:
                new_cam_focal = scene.camera.data.lens

        obj = context.active_object
        if obj and obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.camera_add()
        cam_obj = context.active_object
        
        cam_obj.name = get_unique_camera_name("Camera")
        cam_data = cam_obj.data

        cam_data.passepartout_alpha = 0.85

        cam_coll = ensure_camera_collection(scene)
        for c in list(cam_obj.users_collection):
            try:
                c.objects.unlink(cam_obj)
            except RuntimeError:
                pass

        if cam_obj.name not in cam_coll.objects:
            cam_coll.objects.link(cam_obj)

        cam_obj.matrix_world = r3d.view_matrix.inverted()
        cam_data.lens = new_cam_focal

        scene.camera = cam_obj
        r3d.view_perspective = 'CAMERA'
        space.camera = cam_obj

        for o in context.selected_objects:
            o.select_set(False)
        cam_obj.select_set(True)
        context.view_layer.objects.active = cam_obj

        sync_active_camera_index(context)
        return {'FINISHED'}

class CAMTOOLS_OT_activate_camera(Operator):
    bl_idname = "camtools.activate_camera"
    bl_label = "Set Active & View Camera"
    bl_options = {'REGISTER', 'UNDO'}

    camera_name: StringProperty()

    def execute(self, context):
        cam = bpy.data.objects.get(self.camera_name)
        if not cam or cam.type != 'CAMERA':
            self.report({'WARNING'}, "Camera not found")
            return {'CANCELLED'}

        scene = context.scene
        scene.camera = cam

        for o in context.selected_objects:
            o.select_set(False)
        cam.select_set(True)
        context.view_layer.objects.active = cam

        area, space, region = get_view3d_area_space(context)
        if area and space and region:
            r3d = space.region_3d
            r3d.view_perspective = 'CAMERA'
            space.camera = cam

        return {'FINISHED'}

class CAMTOOLS_OT_duplicate_selected_camera(Operator):
    bl_idname = "camtools.duplicate_selected_camera"
    bl_label = "Duplicate Selected Camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        active = context.view_layer.objects.active

        if not active or active.type != 'CAMERA':
            self.report({'WARNING'}, "Active object is not a camera")
            return {'CANCELLED'}

        cam_coll = ensure_camera_collection(scene)
        new_obj = active.copy()
        new_obj.data = active.data.copy()
        new_obj.animation_data_clear()
        
        new_obj.name = get_unique_camera_name(active.name)
        cam_coll.objects.link(new_obj)

        for o in context.selected_objects:
            o.select_set(False)
        new_obj.select_set(True)
        context.view_layer.objects.active = new_obj

        scene.camera = new_obj
        
        clear_batch_checkmarks(scene)
        sync_active_camera_index(context)
        return {'FINISHED'}

class CAMTOOLS_OT_delete_cameras(Operator):
    bl_idname = "camtools.delete_cameras"
    bl_label = "Delete Camera(s)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        cams_marked = [
            obj for obj in scene.objects
            if obj.type == 'CAMERA' and hasattr(obj, "camtools") and obj.camtools.selected_for_ops
        ]
        
        cams_to_delete = list(cams_marked)

        if not cams_to_delete:
            active = context.view_layer.objects.active
            if not active or active.type != 'CAMERA':
                self.report({'WARNING'}, "No cameras marked or selected")
                return {'CANCELLED'}
            cams_to_delete = [active]

        for cam_obj in cams_to_delete:
            if scene.camera == cam_obj:
                scene.camera = None
            bpy.data.objects.remove(cam_obj, do_unlink=True)

        if scene.camera is None:
            for obj in scene.objects:
                if obj.type == 'CAMERA':
                    scene.camera = obj
                    break
        
        active = context.view_layer.objects.active
        if not active or active.name not in scene.objects:
            if scene.camera:
                context.view_layer.objects.active = scene.camera
                scene.camera.select_set(True)

        clear_batch_checkmarks(scene)
        sync_active_camera_index(context)
        return {'FINISHED'}

class CAMTOOLS_OT_clear_batch_selection(Operator):
    bl_idname = "camtools.clear_batch_selection"
    bl_label = "Clear Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        clear_batch_checkmarks(context.scene)
        return {'FINISHED'}

# ------------------------------------------------------------------------
# Grouping System
# ------------------------------------------------------------------------

class CAMTOOLS_MT_group_menu(Menu):
    bl_idname = "CAMTOOLS_MT_group_menu"
    bl_label = "Group Cameras"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("camtools.create_new_group", text="+ Create New Group", icon='ADD')
        
        layout.separator()
        layout.operator_context = 'EXEC_DEFAULT'
        
        scene = context.scene
        cams_coll = scene.collection.children.get("Cameras")
        if cams_coll and cams_coll.children:
            for child in cams_coll.children:
                op = layout.operator("camtools.move_to_group", text=child.name, icon='OUTLINER_COLLECTION')
                op.group_name = child.name

class CAMTOOLS_OT_create_new_group(Operator):
    bl_idname = "camtools.create_new_group"
    bl_label = "Create New Group"
    bl_options = {'REGISTER', 'UNDO'}

    group_name: StringProperty(name="Name", default="Shot_01")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if not self.group_name.strip():
            self.report({'WARNING'}, "Group name cannot be empty")
            return {'CANCELLED'}
        return perform_grouping(context, self.group_name.strip(), self)

class CAMTOOLS_OT_move_to_group(Operator):
    bl_idname = "camtools.move_to_group"
    bl_label = "Move to Group"
    bl_options = {'REGISTER', 'UNDO'}

    group_name: StringProperty()

    def execute(self, context):
        if not self.group_name:
            return {'CANCELLED'}
        return perform_grouping(context, self.group_name, self)

class CAMTOOLS_OT_ungroup_cameras(Operator):
    bl_idname = "camtools.ungroup_cameras"
    bl_label = "Remove from Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        cams_marked = [
            obj for obj in scene.objects
            if obj.type == 'CAMERA' and hasattr(obj, "camtools") and obj.camtools.selected_for_ops
        ]
        
        cams_to_ungroup = list(cams_marked)

        if not cams_to_ungroup:
            active = context.view_layer.objects.active
            if active and active.type == 'CAMERA':
                cams_to_ungroup = [active]
            else:
                self.report({'WARNING'}, "No cameras marked or selected")
                return {'CANCELLED'}

        cams_coll = ensure_camera_collection(scene)

        for cam in cams_to_ungroup:
            for c in list(cam.users_collection):
                try:
                    c.objects.unlink(cam)
                except RuntimeError:
                    pass
            
            if cam.name not in cams_coll.objects:
                cams_coll.objects.link(cam)

        clear_batch_checkmarks(scene)
        sync_active_camera_index(context)
        return {'FINISHED'}

class CAMTOOLS_OT_clear_empty_groups(Operator):
    bl_idname = "camtools.clear_empty_groups"
    bl_label = "Clear Empty Groups"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        cams_coll = scene.collection.children.get("Cameras")
        
        if not cams_coll:
            return {'CANCELLED'}
            
        removed_any = False
        
        for child in list(cams_coll.children):
            if len(child.objects) == 0:
                if scene.camtools.camera_group_filter == child.name:
                    scene.camtools.camera_group_filter = "ALL"
                    
                bpy.data.collections.remove(child)
                removed_any = True
                
        if not removed_any:
            self.report({'INFO'}, "No empty groups found")
        else:
            self.report({'INFO'}, "Cleared empty camera groups")
            
        return {'FINISHED'}

# ------------------------------------------------------------------------
# Transforms & Corrections
# ------------------------------------------------------------------------

class CAMTOOLS_OT_mirror_camera_local_x(Operator):
    bl_idname = "camtools.mirror_camera_local_x"
    bl_label = "Mirror X (Local)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cam_obj = get_target_camera(context)
        if not cam_obj:
            self.report({'WARNING'}, "No active camera to mirror")
            return {'CANCELLED'}

        Sx = mathutils.Matrix.Scale(-1.0, 4, (1, 0, 0))
        cam_obj.matrix_world = cam_obj.matrix_world @ Sx
        return {'FINISHED'}

class CAMTOOLS_OT_mirror_camera_local_y(Operator):
    bl_idname = "camtools.mirror_camera_local_y"
    bl_label = "Mirror Y (Local)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cam_obj = get_target_camera(context)
        if not cam_obj:
            self.report({'WARNING'}, "No active camera to mirror")
            return {'CANCELLED'}

        Sy = mathutils.Matrix.Scale(-1.0, 4, (0, 1, 0))
        cam_obj.matrix_world = cam_obj.matrix_world @ Sy
        return {'FINISHED'}

class CAMTOOLS_OT_auto_level_verticals(Operator):
    bl_idname = "camtools.auto_level_verticals"
    bl_label = "Level Verticals"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cam_obj = get_target_camera(context)
        if not cam_obj:
            self.report({'WARNING'}, "No active camera to level")
            return {'CANCELLED'}

        scene = context.scene
        render = scene.render
        depsgraph = context.evaluated_depsgraph_get()

        mw = cam_obj.matrix_world
        R = mw.to_3x3()
        up_world = R.col[1]
        world_up = mathutils.Vector((0.0, 0.0, 1.0))

        if up_world.cross(world_up).length < 1e-4:
            return {'FINISHED'}

        ray_origin = cam_obj.location.copy()
        cam_rot_q = mw.to_quaternion()
        forward_pre = (cam_rot_q @ mathutils.Vector((0.0, 0.0, -1.0))).normalized()

        hit, hit_loc, _, _, _, _ = scene.ray_cast(depsgraph, ray_origin, forward_pre)
        target = hit_loc if hit else ray_origin + forward_pre * (cam_obj.data.dof.focus_distance or 10.0)

        loc, rot_q, scale_v = mw.decompose()
        forward = -R.col[2]
        forward_h = mathutils.Vector((forward.x, forward.y, 0.0))
        
        if forward_h.length < 1e-6:
            self.report({'WARNING'}, "Camera pointing straight up/down; cannot auto level robustly")
            return {'CANCELLED'}
        forward_h.normalize()

        new_forward = forward_h
        new_right = new_forward.cross(world_up)
        
        if new_right.length < 1e-6:
            self.report({'WARNING'}, "Degenerate orientation for auto level")
            return {'CANCELLED'}
            
        new_right.normalize()
        new_up = world_up

        new_R = mathutils.Matrix((new_right, new_up, -new_forward)).transposed()
        new_mw = mathutils.Matrix.LocRotScale(loc, new_R.to_quaternion(), scale_v)
        cam_obj.matrix_world = new_mw

        depsgraph.update()

        cam_data = cam_obj.data
        cam_data.shift_y = 0.0
        target_ndc = bpy_extras.object_utils.world_to_camera_view(scene, cam_obj, target)
        shift_y = target_ndc.y - 0.5

        aspect_ratio = (render.resolution_x / render.resolution_y) * (render.pixel_aspect_x / render.pixel_aspect_y)
        if cam_data.sensor_fit == 'HORIZONTAL' or (cam_data.sensor_fit == 'AUTO' and aspect_ratio > 1):
            shift_y /= aspect_ratio

        cam_data.shift_y = shift_y
        depsgraph.update()

        return {'FINISHED'}

# ------------------------------------------------------------------------
# UI Rendering
# ------------------------------------------------------------------------

def draw_camtools(layout, context):
    scene = context.scene
    camtools = scene.camtools

    layout.separator(factor=0.5)

    add_cam_row = layout.row()
    add_cam_row.scale_y = 1.5  
    add_cam_row.operator("view3d.add_camera_from_view_exact", icon='CAMERA_DATA')

    layout.separator()

    split = layout.split(factor=0.5)
    split.separator()
    
    filter_row = split.row(align=True)
    filter_row.prop(camtools, "camera_group_filter", text="")
    filter_row.separator(factor=0.5)
    filter_row.operator("camtools.clear_empty_groups", text="", icon='PANEL_CLOSE')
    
    layout.template_list(
        "CAMTOOLS_UL_cameras",
        "",
        scene,
        "objects",
        camtools,
        "camera_index",
        rows=5,
    )

    cams_marked_count = sum(
        1 for obj in scene.objects 
        if obj.type == 'CAMERA' and hasattr(obj, "camtools") and obj.camtools.selected_for_ops
    )
    
    if cams_marked_count > 0:
        clear_row = layout.row()
        clear_row.alignment = 'RIGHT'
        clear_row.operator("camtools.clear_batch_selection", text=f"Clear {cams_marked_count} Selected", icon='X')

    layout.separator(factor=0.5)

    toolbar_row = layout.row()
    toolbar_row.scale_y = 1.5  
    
    split = toolbar_row.split(factor=0.5) 
    split.operator("camtools.duplicate_selected_camera", text="Duplicate", icon='DUPLICATE')
    
    right_row = split.row()
    
    grp_row = right_row.row(align=True) 
    grp_row.scale_x = 1.2
    
    cams_coll = scene.collection.children.get("Cameras")
    if cams_coll and len(cams_coll.children) > 0:
        op = grp_row.operator("wm.call_menu", text="", icon='OUTLINER_OB_GROUP_INSTANCE') 
        op.name = "CAMTOOLS_MT_group_menu"
    else:
        grp_row.operator("camtools.create_new_group", text="", icon='OUTLINER_OB_GROUP_INSTANCE')

    grp_row.scale_x = 1.2
    grp_row.separator(factor=0.5)  
    grp_row.operator("camtools.ungroup_cameras", text="", icon='GROUP') 
    
    del_row = right_row.row()
    del_row.alignment = 'RIGHT'
    del_row.scale_x = 1.2
    del_row.operator("camtools.delete_cameras", text="", icon='TRASH')

    layout.separator()

    cam_obj = get_target_camera(context)
    if not cam_obj:
        layout.label(text="No active camera", icon='ERROR')
        return

    cam = cam_obj.data
    box = layout.box()
    box.label(text=f"Active: {cam_obj.name}", icon='CAMERA_DATA')

    col = box.column(align=True)
    col.prop(cam, "lens", text="Focal Length")
    col.separator()

    row = col.row(align=True)
    row.prop(cam, "shift_x", text="Shift X")
    row.prop(cam, "shift_y", text="Shift Y")
    
    col.separator()
    row = col.row(align=True)
    row.prop(cam, "clip_start", text="Clip Start")
    row.prop(cam, "clip_end", text="Clip End")

    col.separator()
    row = col.row(align=True)
    row.operator("camtools.auto_level_verticals", text="Level Verticals", icon='AXIS_TOP')

    col.separator()
    row = box.row(align=True)
    row.label(text="Mirror (Local):")
    row.operator("camtools.mirror_camera_local_x", text="X")
    row.operator("camtools.mirror_camera_local_y", text="Y")

    layout.separator()

    dof = cam.dof
    dof_outer = layout.box()
    header = dof_outer.row(align=True)
    icon = 'TRIA_DOWN' if camtools.show_dof else 'TRIA_RIGHT'
    header.prop(camtools, "show_dof", text="", icon=icon, emboss=False)
    header.label(text="Depth of Field")

    if camtools.show_dof:
        col = dof_outer.column(align=True)
        row = col.row(align=True)
        row.prop(dof, "use_dof", text="Enable")

        sub = col.column(align=True)
        sub.enabled = dof.use_dof
        sub.prop(dof, "focus_distance", text="Focus Distance")
        sub.separator(factor=0.5)

        row = sub.row(align=True)
        split_row = row.split(factor=0.35, align=True)
        split_row.label(text="Focus Object")
        split_row.prop(dof, "focus_object", text="")

        if dof.focus_object:
            # Using .location to safely approximate distance without triggering depsgraph evaluations in the UI draw loop
            cam_loc = cam_obj.location
            target_loc = dof.focus_object.location
            dist = (cam_loc - target_loc).length
            
            feed_row = sub.row()
            feed_row.alignment = 'RIGHT'
            feed_row.label(text=f"Dist to Target: {dist:.3f}m (Approx)", icon='INFO')

        sub.separator()

        if hasattr(dof, "aperture_fstop"):
            sub.prop(dof, "aperture_fstop", text="Aperture (f-stop)")

    layout.separator()

    vbox_outer = layout.box()
    header = vbox_outer.row(align=True)
    icon = 'TRIA_DOWN' if camtools.show_viewport_display else 'TRIA_RIGHT'
    header.prop(camtools, "show_viewport_display", text="", icon=icon, emboss=False)
    header.label(text="Viewport Display")

    if camtools.show_viewport_display:
        col = vbox_outer.column(align=True)
        col.label(text="Passepartout:")
        col.prop(cam, "show_passepartout", text="Enable")
        col.prop(cam, "passepartout_alpha", text="Opacity")

        vbox_outer.separator()

        comp_box = vbox_outer.box()
        header = comp_box.row(align=True)
        icon = 'TRIA_DOWN' if camtools.show_composition_guides else 'TRIA_RIGHT'
        header.prop(camtools, "show_composition_guides", text="", icon=icon, emboss=False)
        header.label(text="Composition Guides")

        if camtools.show_composition_guides:
            col = comp_box.column(align=True)
            row = col.row(align=True)
            row.prop(cam, "show_composition_thirds", text="Thirds")
            row.prop(cam, "show_composition_center", text="Center")

            row = col.row(align=True)
            row.prop(cam, "show_composition_center_diagonal", text="Diagonal")
            row.prop(cam, "show_composition_golden", text="Golden")

            row = col.row(align=True)
            row.prop(cam, "show_composition_golden_tria_a", text="Golden Tri A")
            row.prop(cam, "show_composition_golden_tria_b", text="Golden Tri B")

            row = col.row(align=True)
            row.prop(cam, "show_composition_harmony_tri_a", text="Harmony Tri A")
            row.prop(cam, "show_composition_harmony_tri_b", text="Harmony Tri B")

# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------

classes = (
    CamToolsSceneProps,
    CamToolsObjectProps,
    CAMTOOLS_UL_cameras,
    VIEW3D_OT_add_camera_from_view_exact,
    CAMTOOLS_OT_activate_camera,
    CAMTOOLS_OT_duplicate_selected_camera,
    CAMTOOLS_OT_delete_cameras,
    CAMTOOLS_OT_clear_batch_selection,
    CAMTOOLS_MT_group_menu,
    CAMTOOLS_OT_create_new_group,
    CAMTOOLS_OT_move_to_group,
    CAMTOOLS_OT_ungroup_cameras,
    CAMTOOLS_OT_clear_empty_groups,
    CAMTOOLS_OT_mirror_camera_local_x,
    CAMTOOLS_OT_mirror_camera_local_y,
    CAMTOOLS_OT_auto_level_verticals,
)

def register_camtools():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.camtools = PointerProperty(type=CamToolsSceneProps)
    bpy.types.Object.camtools = PointerProperty(type=CamToolsObjectProps)

    _camtools_msgbus_subscribe()
    if _camtools_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_camtools_load_post)

def unregister_camtools():
    _camtools_msgbus_unsubscribe()
    if _camtools_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_camtools_load_post)

    del bpy.types.Scene.camtools
    del bpy.types.Object.camtools

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)