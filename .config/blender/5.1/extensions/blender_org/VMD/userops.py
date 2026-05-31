import bpy
from mathutils import Vector, Quaternion, Matrix, Color
from math import tan as math_tan

Translation = Matrix.Translation
Operator = bpy.types.Operator

# <<< 1mp (bpy.props
props = bpy.props
StringProperty = props.StringProperty
EnumProperty = props.EnumProperty
BoolProperty = props.BoolProperty
IntProperty = props.IntProperty
IntVectorProperty = props.IntVectorProperty
FloatVectorProperty = props.FloatVectorProperty
FloatProperty = props.FloatProperty
# >>>

from json import loads as json_loads

from . util.algebra import r_compose

from . api import r_bl_ID_by_uid, r_bbox_nodes, r_eevee_output


class OpsReport(Operator):
    __slots__ = ()

    def execute(self, context):
        try:
            return self.i_execute(context)
        except:
            if hasattr(self, 'except_with'):
                self.except_with()

            m.call_bug_report_dialog()
            return {'CANCELLED'}
        #|
    #|
    #|
class OpsReportModal(Operator):
    __slots__ = ()

    def invoke(self, context, event):
        try:
            return self.i_invoke(context, event)
        except:
            if hasattr(self, 'except_with'):
                self.except_with()

            m.call_bug_report_dialog()
            return {'CANCELLED'}
        #|
    def modal(self, context, event):
        try:
            return self.i_modal(context, event)
        except:
            if hasattr(self, 'except_with'):
                self.except_with()

            m.call_bug_report_dialog()
            return {'CANCELLED'}
        #|
    def execute(self, context):
        try:
            return self.i_execute(context)
        except:
            if hasattr(self, 'except_with'):
                self.except_with()

            m.call_bug_report_dialog()
            return {'CANCELLED'}
        #|
    #|
    #|
class PollEditMesh:
    __slots__ = ()

    @classmethod
    def poll(cls, context):
        if context.area.type == "VIEW_3D":
            ob = context.object
            if hasattr(ob, "mode") and ob.mode == "EDIT":
                if hasattr(ob, "type") and ob.type == "MESH": return True
        return False
        #|
    #|
    #|
class GrabCursor:
    __slots__ = ()

    def invoke_grab_cursor(self, context, event):
        self.mou_limit = min(context.area.width, context.area.height) // 2
        self.mou = [event.mouse_x, event.mouse_y]
        #|
    #|
    #|
class Bmesh:
    __slots__ = 'bm', 'verts_sel', 'edges_sel', 'faces_sel'

    def __init__(self, bm, verts_sel, edges_sel, faces_sel):
        self.bm = bm
        self.verts_sel = verts_sel
        self.edges_sel = edges_sel
        self.faces_sel = faces_sel
        #|
    #|
    #|

def check_area_type(self, context, ty='VIEW_3D'):
    if context.space_data.type == ty:
        return False
    self.report({'WARNING'}, "Active space must be a View3d")
    return True

KEYMAP_DEFAULT_slowdown_speedup = (
    {"cancel": {"RIGHTMOUSE"}, "confirm": {"LEFTMOUSE", "RET", "NUMPAD_ENTER"}, "slowdown": {"shift"}, "speedup": {"ctrl"}},
    # <<< 1precompile (type="modalKeymap")
    "{'cancel': ['RIGHTMOUSE'], 'confirm': ['LEFTMOUSE', 'RET', 'NUMPAD_ENTER'], 'slowdown': ['shift'], 'speedup': ['ctrl']}"
    # >>>
)

def modalKeymap(
        KEYMAP_DEFAULT={"cancel": {"RIGHTMOUSE"}, "confirm": {"LEFTMOUSE", "RET", "NUMPAD_ENTER"}},
        KEYMAP_STR='"cancel": "RIGHTMOUSE", "confirm": ["LEFTMOUSE", "RET", "NUMPAD_ENTER"]'
    ):
    class ModalKeymap:
        __slots__ = ()

        modal_keymap: StringProperty(
            name = "Modal Keymap",
            default = KEYMAP_STR,
            options = {'HIDDEN'})
        invoke_default: BoolProperty(
            name = "Invoke",
            default = True,
            options = {'HIDDEN'})

        def keymap_load(self):
            try:
                keymaps = {k: (set(e)  if isinstance(e, list) else {e})  for k, e in json_loads(self.modal_keymap).items()}
            except:
                keymaps = KEYMAP_DEFAULT

            if "cancel" not in keymaps:
                keymaps["cancel"] = set()
            if "confirm" not in keymaps:
                keymaps["confirm"] = set()

            self.keymaps = keymaps
            #|
        #|
        #|
    return ModalKeymap
    #|

class ModalSlowdownSpeedup:
    __slots__ = ()

    drag_speed: FloatProperty(
        name = "Drag Speed",
        default = 0.001,
        min = 0.00001,
        max = 10000.0,
        options = {'HIDDEN'})

    def get_trigger_slowdown_speedup(self):
        keymaps = self.keymaps
        if "slowdown" in keymaps:
            slowdown = keymaps["slowdown"] & {'alt', 'ascii', 'ctrl', 'oskey', 'shift'}
            self.trigger_slowdown = lambda event: any(getattr(event, k)  for k in slowdown)
        else:
            self.trigger_slowdown = lambda event: False

        if "speedup" in keymaps:
            speedup = keymaps["speedup"] & {'alt', 'ascii', 'ctrl', 'oskey', 'shift'}
            self.trigger_speedup = lambda event: any(getattr(event, k)  for k in speedup)
        else:
            self.trigger_speedup = lambda event: False

        self.drag_speed_fast = self.drag_speed * 10.0
        self.drag_speed_slow = self.drag_speed * 0.1
        #|
    #|
    #|


class OpsWinman(Operator):
    __slots__ = ()

    bl_idname = "wm.vmd_window_manager"
    bl_label = "VMD Window Manager"
    bl_options = {"REGISTER"}
    bl_description = "Open Window Manager in 3D Viewport"
    bl_keycategory = "3D View"

    def invoke(self, context, event):
        if call_admin(context):
            if m.P.is_first_use:
                from . dd import call_dd_license
                call_dd_license()

        m.Admin.REDRAW()
        return {'FINISHED'}
        #|
    #|
    #|

class OpsEditor(Operator):
    __slots__ = ()

    bl_idname = "wm.vmd_editor"
    bl_label = "VMD Editor"
    bl_options = {"REGISTER"}
    bl_description = "Open Editor in 3D Viewport"
    bl_keycategory = "3D View"

    # id_class: 
    use_pos: BoolProperty(
        name = "Override Position",
        description = "Use cursor position instead of default position.",
        default = True,
        options = set())
    pos_offset: IntVectorProperty(
        name = "Offset",
        description = "Window offset when Override Position is enabled.",
        size = 2,
        default = (-150, 15),
        subtype = "TRANSLATION",
        options = set())
    use_fit: BoolProperty(
        name = "Auto Size",
        description = "Use Auto Size instead of default size.",
        default = True,
        options = set())


    def invoke(self, context, event):
        if call_admin(context):
            if m.P.is_first_use:
                from . dd import call_dd_license
                call_dd_license()
            else:
                m.D_EDITOR[self.id_class](
                id_class = self.id_class,
                use_pos = self.use_pos,
                use_fit = self.use_fit,
                pos_offset = self.pos_offset,

                event = event)

        return {'FINISHED'}
        #|

class OpsLoadFactory(Operator):
    __slots__ = ()

    bl_idname = "wm.vmd_addon_factory"
    bl_label = "VMD Load Addon Factory Setting"
    bl_options = {"REGISTER"}
    bl_description = "Load vmdesk Factory Setting, this process cannot be 'Undo'"
    bl_keycategory = "Window"

    @classmethod
    def poll(cls, context):
        if m.P: return True
        return False

    def execute(self, context):
        if m.ADMIN: m.ADMIN.evt_sys_off(sleep=False)

        from . apps.settingeditor.areas import P_BL_RNA_PROPS

        def reset_prefs(pp):
            for identifier, rna in pp.bl_rna.properties.items():
                if identifier in {'bl_idname', 'name', 'rna_type'}: continue

                if rna.type == "POINTER":
                    reset_prefs(getattr(pp, identifier))
                    continue

                if hasattr(rna, "is_array") and rna.is_array:
                    setattr(pp, identifier, rna.default_array)
                else:
                    if rna.subtype == "BYTE_STRING":
                        setattr(pp, identifier, rna.default.encode('utf-8'))
                    else:
                        setattr(pp, identifier, rna.default)

        reset_prefs(m.P)
        self.report({'INFO'}, "Reset successful, requires manual saving of preferences")
        return {'FINISHED'}
        #|
    #|
    #|


class OpsReloadIcon(Operator):
    __slots__ = ()

    bl_idname = "wm.vmd_reload_icon"
    bl_label = "VMD Reload Icon"
    bl_options = {"REGISTER"}
    bl_description = "Reload icons after changing UI size"
    bl_keycategory = "Window"

    @classmethod
    def poll(cls, context):
        if m.P: return True
        return False

    def invoke(self, context, event):
        blg.reload_icon()
        return {'FINISHED'}
        #|
    #|
    #|
class OpsReloadFont(Operator):
    __slots__ = ()

    bl_idname = "wm.vmd_reload_font"
    bl_label = "VMD Reload Font"
    bl_options = {"REGISTER"}
    bl_description = "Reload UI Fonts after changing blender Theme / Text Rendering settings (like Subpixel Anti-Aliasing)"
    bl_keycategory = "Window"

    @classmethod
    def poll(cls, context):
        if m.P: return True
        return False

    def invoke(self, context, event):
        blg.reload_font()
        return {'FINISHED'}
        #|
    #|
    #|
class OpsUiScale(Operator):
    __slots__ = ()

    bl_idname = "wm.vmd_ui_scale"
    bl_label = "VMD UI Scale"
    bl_options = {"REGISTER"}
    bl_description = "Set add-on UI scale"
    bl_keycategory = "Window"

    factor: FloatProperty(default=1.0)

    @classmethod
    def poll(cls, context):
        if m.P: return True
        return False

    def execute(self, context):
        fac = self.factor
        P = m.P
        pp = P.size

        if fac < 1.32:
            rnas = pp.bl_rna.properties
            pp.widget[:] = rnas["widget"].default_array
            pp.title[:] = rnas["title"].default_array
            pp.border[:] = rnas["border"].default_array
            pp.dd_border[:] = rnas["dd_border"].default_array
            pp.filter[:] = rnas["filter"].default_array
            pp.tb[:] = rnas["tb"].default_array
            pp.win_shadow_offset[:] = rnas["win_shadow_offset"].default_array
            pp.dd_shadow_offset[:] = rnas["dd_shadow_offset"].default_array
            pp.shadow_softness[:] = rnas["shadow_softness"].default_array
            pp.setting_list_border[:] = rnas["setting_list_border"].default_array
            pp.block[:] = rnas["block"].default_array
            pp.button[:] = rnas["button"].default_array

            P.ModifierEditor.area_list_inner = 8
        elif fac <= 1.34:
            pp.widget[:] = (24, 2, 8, 1)
            pp.title[:] = (36, 30)
            pp.border[:] = (5, 4, 1, 1)
            pp.dd_border[:] = (1, 1, 1)
            pp.filter[:] = (266, 2, 2, 2)
            pp.tb[:] = (36, 400, 4)
            pp.win_shadow_offset[:] = (-13, 27, -30, 8)
            pp.dd_shadow_offset[:] = (-8, 11, -15, 5)
            pp.shadow_softness[:] = (57, 20)
            pp.setting_list_border[:] = (11, 7, 1)
            pp.block[:] = (3, 3, 4, 4, 4, 20, 13, 1, 3, 3)
            pp.button[:] = (11, 1, 4, 340)

            P.ModifierEditor.area_list_inner = 11
        elif fac <= 1.67:
            pp.widget[:] = (30, 3, 10, 2)
            pp.title[:] = (45, 37)
            pp.border[:] = (7, 5, 2, 2)
            pp.dd_border[:] = (2, 2, 2)
            pp.filter[:] = (332, 3, 3, 3)
            pp.tb[:] = (45, 498, 5)
            pp.win_shadow_offset[:] = (-17, 33, -38, 10)
            pp.dd_shadow_offset[:] = (-10, 13, -18, 7)
            pp.shadow_softness[:] = (57, 20)
            pp.setting_list_border[:] = (13, 8, 2)
            pp.block[:] = (3, 3, 5, 5, 5, 25, 17, 2, 3, 3)
            pp.button[:] = (13, 2, 5, 425)

            P.ModifierEditor.area_list_inner = 13
        else:
            pp.widget[:] = (36, 4, 12, 2)
            pp.title[:] = (54, 44)
            pp.border[:] = (8, 6, 2, 2)
            pp.dd_border[:] = (2, 2, 2)
            pp.filter[:] = (400, 4, 4, 4)
            pp.tb[:] = (54, 600, 6)
            pp.win_shadow_offset[:] = (-20, 40, -46, 12)
            pp.dd_shadow_offset[:] = (-12, 16, -22, 8)
            pp.shadow_softness[:] = (57, 20)
            pp.setting_list_border[:] = (16, 10, 2)
            pp.block[:] = (4, 4, 6, 6, 6, 30, 20, 2, 4, 4)
            pp.button[:] = (16, 3, 6, 512)

            P.ModifierEditor.area_list_inner = 16

        blg.reload_icon()
        return {'FINISHED'}
    #|
    #|

class OpsBlNewWinRender(Operator):
    __slots__ = ()

    bl_idname = "wm.vmd_bl_new_win_render"
    bl_label = "New Window (Viewport Render)"
    bl_options = {"REGISTER"}
    bl_description = "Open a new main window and set it to rendering mode"

    def execute(self, context):
        first_r3d = None
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces[0]
                first_r3d = space.region_3d
                focal_length = space.lens
                clip_start = space.clip_start
                clip_end = space.clip_end
                lock_camera = space.lock_camera
                show_camera_passepartout = space.overlay.show_camera_passepartout
                use_render_border = space.use_render_border
                break

        bpy.ops.wm.window_new()
        bpy.context.area.type = 'VIEW_3D'
        space_data = bpy.context.space_data
        space_data.overlay.show_overlays = False
        space_data.show_gizmo = False
        space_data.shading.type = 'RENDERED'
        space_data.show_region_header = False

        if first_r3d is None: return {'FINISHED'}

        space_data.lens = focal_length
        space_data.clip_start = clip_start
        space_data.clip_end = clip_end
        space_data.lock_camera = lock_camera
        space_data.overlay.show_camera_passepartout = show_camera_passepartout
        space_data.use_render_border = use_render_border

        rv3d = space_data.region_3d
        rv3d.view_perspective = first_r3d.view_perspective
        rv3d.is_orthographic_side_view = first_r3d.is_orthographic_side_view
        rv3d.view_matrix = first_r3d.view_matrix
        rv3d.view_camera_zoom = first_r3d.view_camera_zoom
        rv3d.view_camera_offset = first_r3d.view_camera_offset
        rv3d.lock_rotation = first_r3d.lock_rotation
        rv3d.show_sync_view = first_r3d.show_sync_view
        rv3d.use_box_clip = first_r3d.use_box_clip
        rv3d.use_clip_planes = first_r3d.use_clip_planes
        rv3d.update()
        return {'FINISHED'}
        #|
    #|
    #|
def OpsBlNewWinRender_draw_rm(self, context):
    self.layout.operator("wm.vmd_bl_new_win_render")

def keymap_load(self):
    cls_name = self.__class__.__name__
    keymaps = {k: e  for k, e in json_loads(m.P.modal_keymaps.bl_rna.properties[cls_name].default).items()}
    try:
        user_keymaps = {k: e  for k, e in json_loads(getattr(m.P.modal_keymaps, cls_name)).items()}
        if not isinstance(user_keymaps, dict):
            self.report({'WARNING'}, "Modal Keymaps compilation error")
            user_keymaps = {}
    except:
        self.report({'WARNING'}, "Modal Keymaps compilation error")
        user_keymaps = {}

    for k, e in keymaps.copy().items():
        if k in user_keymaps:
            new_keymap = user_keymaps[k]

            if isinstance(new_keymap, str):
                keymaps[k] = new_keymap

    self.keymaps = keymaps
    #|

class OpsBlViewRotate(Operator):
    __slots__ = (
        'keymaps',
        'keystate',
        'mou',
        'mou_init',
        'i_modal',
        'rv3d',
        'rv3d_data',
        'cam',)

    bl_idname = "view3d.vmd_rotate"
    bl_label = "VMD View Rotate"
    bl_options = {"REGISTER", "GRAB_CURSOR", "BLOCKING"}
    bl_description = "Viewport Rotate / Walk / Dolly"

    TIMER = None
    IS_LAST_PERSP = True
    LAST_CAM_TYPE = 'PERSP'

    orbit_speed: FloatProperty(default=0.00698, min=0.00001, max=99999.0)
    dolly_speed: FloatProperty(default=0.1, min=0.00001, max=99999.0)
    walk_orbit_speed: FloatProperty(default=0.002, min=0.00001, max=99999.0)
    walk_speed: FloatProperty(default=10.0, min=0.00001, max=99999.0)
    fast_fac: FloatProperty(default=5.0, min=0.00001, max=99999.0)
    slow_fac: FloatProperty(default=0.2, min=0.00001, max=99999.0)
    ccceleration_increment: FloatProperty(default=0.05, min=0.00001, max=99999.0)

    def timer_add(self, context):
        if OpsBlViewRotate.TIMER is None:
            OpsBlViewRotate.TIMER = context.window_manager.event_timer_add(0.00001, window=context.window)
        #|
    def time_remove(self, context):
        if OpsBlViewRotate.TIMER is None: return

        context.window_manager.event_timer_remove(OpsBlViewRotate.TIMER)
        OpsBlViewRotate.TIMER = None

        #|
    def is_cam_side_view(self):
        loc, rot, sca = self.cam.matrix_world.decompose()
        rot_euler = rot.to_euler()

        return all(abs(round(rot_euler[i] * 1.27323954474) / 1.27323954474 - rot_euler[i]) < 1e-6  for i in range(3))
        #|
    def status_text_upd(self, context):
        context.workspace.status_text_set(f'Walk Speed: {self.walk_speed}  |  Dolly Speed: {self.dolly_speed}')
        #|

    def fin(self, context):

        self.time_remove(context)
        context.workspace.status_text_set(None)
        context.window.cursor_warp(*self.mou_init)
        context.window.cursor_modal_restore()

        rv3d = self.rv3d
        if rv3d.view_perspective == 'CAMERA':
            rv3d.view_matrix = self.cam.matrix_world.normalized().inverted()
        elif hasattr(self, 'rv3d_data') and 'view_distance' in self.rv3d_data:
            rv3d_data = self.rv3d_data
            rv3d.view_distance = rv3d_data['view_distance']
            rv3d.view_location -= (rv3d.view_rotation @ Vector((0.0, 0.0, 1.0))) * rv3d_data['view_distance']
        return {'FINISHED'}
        #|

    def invoke(self, context, event):
        if check_area_type(self, context) is True: return {'CANCELLED'}

        v3d = context.space_data
        rv3d = v3d.region_3d

        self.rv3d = rv3d
        keymap_load(self)
        keymaps = self.keymaps
        self.keystate = {k: False  for k in keymaps.keys()}
        self.keystate['cancel'] = True
        self.rv3d_data = {}
        context.workspace.status_text_set(f'Dolly: {keymaps["dolly"]} | Walk Forward: {keymaps["forward"]} | Backward: {keymaps["backward"]} | Left: {keymaps["left"]} | Right: {keymaps["right"]} | Up: {keymaps["up"]} | Down: {keymaps["down"]} | Fast: {keymaps["fast"]} | Slow: {keymaps["slow"]} | Speed Up: {keymaps["speed_up"]} | Speed Down: {keymaps["speed_down"]}')

        unlock_camera = True

        if rv3d.view_perspective == 'CAMERA' and context.scene.camera:
            cam = context.scene.camera

            if v3d.lock_camera:
                unlock_camera = False
                self.i_modal = self.i_modal_cam_orbit
                self.cam = cam

                if cam.data.type == 'ORTHO':
                    if self.is_cam_side_view():
                        rv3d.is_orthographic_side_view = False

                        if OpsBlViewRotate.LAST_CAM_TYPE != 'ORTHO':
                            cam.data.type = OpsBlViewRotate.LAST_CAM_TYPE
                else:
                    OpsBlViewRotate.LAST_CAM_TYPE = cam.data.type
                    rv3d.view_matrix = cam.matrix_world.normalized().inverted()
            else:
                if cam.data.type == 'ORTHO':
                    rv3d.view_perspective = 'ORTHO'
                else:
                    rv3d.view_perspective = 'PERSP'

        if unlock_camera is True:
            if rv3d.view_perspective == 'PERSP':
                self.i_modal = self.i_modal_orbit

                OpsBlViewRotate.IS_LAST_PERSP = True
            elif rv3d.view_perspective == 'ORTHO':
                self.i_modal = self.i_modal_orbit

                if rv3d.is_orthographic_side_view:
                    if OpsBlViewRotate.IS_LAST_PERSP is True:
                        rv3d.view_perspective = 'PERSP'
                else:
                    OpsBlViewRotate.IS_LAST_PERSP = False
            else:
                return {'CANCELLED'}

        self.mou_init = [event.mouse_x, event.mouse_y]
        self.mou = [event.mouse_x, event.mouse_y]

        context.window.cursor_modal_set('NONE')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        #|

    def modal(self, context, event):
        try:
            keymaps = self.keymaps
            keystate = self.keystate

            if event.value == 'RELEASE':
                if event.type == 'ESC':
                    return self.fin(context)

                if event.type == keymaps['cancel']: keystate['cancel'] = False
                if event.type == keymaps['dolly']: keystate['dolly'] = False
                if event.type == keymaps['snap']: keystate['snap'] = False
                if event.type == keymaps['left']: keystate['left'] = False
                if event.type == keymaps['right']: keystate['right'] = False
                if event.type == keymaps['up']: keystate['up'] = False
                if event.type == keymaps['down']: keystate['down'] = False
                if event.type == keymaps['forward']: keystate['forward'] = False
                if event.type == keymaps['backward']: keystate['backward'] = False
                if event.type == keymaps['fast']: keystate['fast'] = False
                if event.type == keymaps['slow']: keystate['slow'] = False
                if event.type == keymaps['speed_up']: keystate['speed_up'] = False
                if event.type == keymaps['speed_down']: keystate['speed_down'] = False

                if all(e is False for e in keystate.values()):
                    return self.fin(context)
            else:
                if event.type == keymaps['cancel']: keystate['cancel'] = True
                if event.type == keymaps['dolly']: keystate['dolly'] = True
                if event.type == keymaps['snap']: keystate['snap'] = True
                if event.type == keymaps['left']: keystate['left'] = True
                if event.type == keymaps['right']: keystate['right'] = True
                if event.type == keymaps['up']: keystate['up'] = True
                if event.type == keymaps['down']: keystate['down'] = True
                if event.type == keymaps['forward']: keystate['forward'] = True
                if event.type == keymaps['backward']: keystate['backward'] = True
                if event.type == keymaps['fast']: keystate['fast'] = True
                if event.type == keymaps['slow']: keystate['slow'] = True
                if event.type == keymaps['speed_up']: keystate['speed_up'] = True
                if event.type == keymaps['speed_down']: keystate['speed_down'] = True

            return self.i_modal(context, event)
        except Exception as ex:
            (print(str(ex)))
            self.fin(context)
            self.report({'ERROR'}, "Please check the console")
            return {'CANCELLED'}
        #|

    def to_snap_mode(self, context, event):

        self.i_modal = self.i_modal_snap

        rv3d = self.rv3d

        if rv3d.view_perspective == 'CAMERA':
            return
        elif rv3d.view_perspective == 'PERSP':
            rv3d.is_orthographic_side_view = True
            rv3d.view_perspective = 'ORTHO'
        else:
            rv3d.is_orthographic_side_view = True
        #|
    def to_orbit_mode(self, context, event):

        self.i_modal = self.i_modal_orbit

        rv3d = self.rv3d

        if rv3d.view_perspective == 'CAMERA':
            return
        elif rv3d.view_perspective == 'PERSP':
            rv3d.is_orthographic_side_view = True
            rv3d.view_perspective = 'ORTHO'
        elif rv3d.view_perspective == 'ORTHO':
            rv3d.is_orthographic_side_view = False
            if OpsBlViewRotate.IS_LAST_PERSP is True:
                rv3d.view_perspective = 'PERSP'
        else:
            return
        #|
    def to_walk_mode(self, context, event):

        self.i_modal = self.i_modal_walk

        rv3d = self.rv3d

        if rv3d.view_perspective == 'CAMERA':
            return
        elif rv3d.view_perspective == 'PERSP':
            rv3d_data = self.rv3d_data
            rv3d_data['view_distance'] = rv3d.view_distance

            rv3d.view_distance = 0.0
            rv3d.view_location += (rv3d.view_rotation @ Vector((0.0, 0.0, 1.0))) * rv3d_data['view_distance']

        self.status_text_upd(context)
        self.timer_add(context)
        #|

    def i_modal_orbit(self, context, event):
        keystate = self.keystate
        if keystate['snap'] is True:
            self.to_snap_mode(context, event)
            return {'RUNNING_MODAL'}
        if keystate['left'] is True or keystate['right'] is True or keystate['up'] is True or keystate['down'] is True or keystate['forward'] is True or keystate['backward'] is True:
            self.to_walk_mode(context, event)
            return {'RUNNING_MODAL'}

        rv3d = self.rv3d

        if keystate['dolly'] is True:
            if keystate['speed_up'] is True:
                self.dolly_speed += self.ccceleration_increment
                self.status_text_upd(context)
            elif keystate['speed_down'] is True:
                self.dolly_speed -= self.ccceleration_increment
                self.status_text_upd(context)

            rv3d.view_rotation = Quaternion((0.0, 0.0, 1.0), (self.mou[0] - event.mouse_x) * self.orbit_speed) @ rv3d.view_rotation

            view_matrix = rv3d.view_matrix
            vec = Vector((view_matrix[2][0], view_matrix[2][1], 0.0))

            if keystate['fast'] is True:
                rv3d.view_location += vec * (self.mou[1] - event.mouse_y) * self.dolly_speed * self.fast_fac
            elif keystate['slow'] is True:
                rv3d.view_location += vec * (self.mou[1] - event.mouse_y) * self.dolly_speed * self.slow_fac
            else:
                rv3d.view_location += vec * (self.mou[1] - event.mouse_y) * self.dolly_speed
        else:
            rv3d.view_rotation = Quaternion((0.0, 0.0, 1.0), (self.mou[0] - event.mouse_x) * self.orbit_speed) @ rv3d.view_rotation @ Quaternion((1.0, 0.0, 0.0), (event.mouse_y - self.mou[1]) * self.orbit_speed)

        self.mou[0] = event.mouse_x
        self.mou[1] = event.mouse_y
        return {'RUNNING_MODAL'}
        #|
    def i_modal_snap(self, context, event):
        if self.keystate['snap'] is False:
            self.to_orbit_mode(context, event)
            return {'RUNNING_MODAL'}

        return {'RUNNING_MODAL'}
        #|
    def i_modal_walk(self, context, event):
        if event.type == 'TIMER': pass
        else: return {'RUNNING_MODAL'}

        keystate = self.keystate
        rv3d = self.rv3d
        rot = rv3d.view_rotation.to_euler()

        if keystate['dolly'] is True: pass
        else:
            if rot.x > 0:
                rot.x += (event.mouse_y - self.mou[1]) * self.walk_orbit_speed
                if rot.x < 0: rot.x = 0.00001
                elif rot.x > 3.14159: rot.x = 3.14159
            else:
                rot.x += (event.mouse_y - self.mou[1]) * self.walk_orbit_speed
                if rot.x > 0: rot.x = -0.00001
                elif rot.x < -3.14159: rot.x = -3.14159

        rot.z += (self.mou[0] - event.mouse_x) * self.walk_orbit_speed
        rv3d.view_rotation = rot.to_quaternion()

        view_matrix = rv3d.view_matrix
        vec = Vector()

        if keystate['forward'] is True:
            vec.x -= view_matrix[2][0]
            vec.y -= view_matrix[2][1]
        elif keystate['backward'] is True:
            vec.x += view_matrix[2][0]
            vec.y += view_matrix[2][1]
        if keystate['left'] is True:
            vec.x -= view_matrix[0][0]
            vec.y -= view_matrix[0][1]
        elif keystate['right'] is True:
            vec.x += view_matrix[0][0]
            vec.y += view_matrix[0][1]
        if keystate['up'] is True:
            vec.z += 1.0
        elif keystate['down'] is True:
            vec.z -= 1.0
        if keystate['speed_up'] is True:
            self.walk_speed += self.ccceleration_increment
            self.status_text_upd(context)
        elif keystate['speed_down'] is True:
            self.walk_speed -= self.ccceleration_increment
            self.status_text_upd(context)

        if vec.length_squared == 0:
            if keystate['dolly'] is True:
                dolly_vec = Vector((view_matrix[2][0], view_matrix[2][1], 0.0)) * (self.mou[1] - event.mouse_y) * self.dolly_speed

                if keystate['fast'] is True:
                    rv3d.view_location += dolly_vec * self.fast_fac
                elif keystate['slow'] is True:
                    rv3d.view_location += dolly_vec * self.slow_fac
                else:
                    rv3d.view_location += dolly_vec
        else:
            if keystate['dolly'] is True:
                dolly_vec = Vector((view_matrix[2][0], view_matrix[2][1], 0.0)) * (self.mou[1] - event.mouse_y) * self.dolly_speed

                if keystate['fast'] is True:
                    rv3d.view_location += vec.normalized() * self.TIMER.time_delta * self.walk_speed * self.fast_fac + dolly_vec * self.fast_fac
                elif keystate['slow'] is True:
                    rv3d.view_location += vec.normalized() * self.TIMER.time_delta * self.walk_speed * self.slow_fac + dolly_vec * self.slow_fac
                else:
                    rv3d.view_location += vec.normalized() * self.TIMER.time_delta * self.walk_speed + dolly_vec
            else:
                if keystate['fast'] is True:
                    rv3d.view_location += vec.normalized() * self.TIMER.time_delta * self.walk_speed * self.fast_fac
                elif keystate['slow'] is True:
                    rv3d.view_location += vec.normalized() * self.TIMER.time_delta * self.walk_speed * self.slow_fac
                else:
                    rv3d.view_location += vec.normalized() * self.TIMER.time_delta * self.walk_speed

        self.mou[0] = event.mouse_x
        self.mou[1] = event.mouse_y
        return {'RUNNING_MODAL'}
        #|

    def to_cam_snap_mode(self, context, event):

        self.i_modal = self.i_modal_cam_snap

        rv3d = self.rv3d
        cam = self.cam

        cam.data.type = 'ORTHO'
        rv3d.is_orthographic_side_view = True
        loc, rot, sca = cam.matrix_world.decompose()
        rot_euler = rot.to_euler()

        rot_euler.x = round(rot_euler.x * 1.27323954474) / 1.27323954474
        rot_euler.y = round(rot_euler.y * 1.27323954474) / 1.27323954474
        rot_euler.z = round(rot_euler.z * 1.27323954474) / 1.27323954474

        rot = rot_euler.to_quaternion()
        offset = (rot @ Vector((0.0, 0.0, 1.0))) * rv3d.view_distance

        cam.matrix_world = r_compose(rv3d.view_location + offset, rot, sca)
        cam.data.ortho_scale = 2.0 * rv3d.view_distance * math_tan(cam.data.angle / 2.0)
        #|
    def to_cam_orbit_mode(self, context, event):

        self.i_modal = self.i_modal_cam_orbit

        rv3d = self.rv3d

        rv3d.is_orthographic_side_view = False
        self.cam.data.type = OpsBlViewRotate.LAST_CAM_TYPE
        #|
    def to_cam_walk_mode(self, context, event):
        self.i_modal = self.i_modal_cam_walk
        self.status_text_upd(context)
        self.timer_add(context)
        #|

    def i_modal_cam_orbit(self, context, event):
        keystate = self.keystate
        if keystate['snap'] is True:
            self.to_cam_snap_mode(context, event)
            return {'RUNNING_MODAL'}
        if keystate['left'] is True or keystate['right'] is True or keystate['up'] is True or keystate['down'] is True or keystate['forward'] is True or keystate['backward'] is True:
            self.to_cam_walk_mode(context, event)
            return {'RUNNING_MODAL'}

        rv3d = self.rv3d
        if keystate['dolly'] is True:
            if keystate['speed_up'] is True:
                self.dolly_speed += self.ccceleration_increment
                self.status_text_upd(context)
            elif keystate['speed_down'] is True:
                self.dolly_speed -= self.ccceleration_increment
                self.status_text_upd(context)

            new_rot = Quaternion((0.0, 0.0, 1.0), (self.mou[0] - event.mouse_x) * self.orbit_speed) @ rv3d.view_rotation

            mat_rot = new_rot.to_matrix().to_4x4()

            view_matrix = rv3d.view_matrix
            vec = Vector((view_matrix[2][0], view_matrix[2][1], 0.0)) * (self.mou[1] - event.mouse_y)

            if keystate['fast'] is True:
                rv3d.view_location += vec * self.dolly_speed * self.fast_fac
            elif keystate['slow'] is True:
                rv3d.view_location += vec * self.dolly_speed * self.slow_fac
            else:
                rv3d.view_location += vec * self.dolly_speed

            self.cam.matrix_world = Translation(rv3d.view_location + (mat_rot @ Translation((0, 0, rv3d.view_distance))).to_translation()) @ mat_rot
        else:
            new_rot = Quaternion((0.0, 0.0, 1.0), (self.mou[0] - event.mouse_x) * self.orbit_speed) @ rv3d.view_rotation @ Quaternion((1.0, 0.0, 0.0), (event.mouse_y - self.mou[1]) * self.orbit_speed)

            # mat_rot = new_rot.to_matrix().to_4x4()
            # offset = mat_rot @ Translation((0, 0, rv3d.view_distance))
            # new_loc = rv3d.view_location + offset.to_translation()

            # self.cam.matrix_world = Translation(new_loc) @ mat_rot

            mat_rot = new_rot.to_matrix().to_4x4()
            self.cam.matrix_world = Translation(rv3d.view_location + (mat_rot @ Translation((0, 0, rv3d.view_distance))).to_translation()) @ mat_rot

        context.view_layer.update()

        self.mou[0] = event.mouse_x
        self.mou[1] = event.mouse_y
        return {'RUNNING_MODAL'}
        #|
    def i_modal_cam_snap(self, context, event):
        if self.keystate['snap'] is False:
            self.to_cam_orbit_mode(context, event)
            return {'RUNNING_MODAL'}

        return {'RUNNING_MODAL'}
        #|
    def i_modal_cam_walk(self, context, event):
        if event.type == 'TIMER': pass
        else: return {'RUNNING_MODAL'}

        keystate = self.keystate
        rv3d = self.rv3d
        cam = self.cam
        loc, rot, sca = cam.matrix_world.decompose()
        rot = rv3d.view_rotation.to_euler()

        if keystate['dolly'] is True: pass
        else:
            if rot.x > 0:
                rot.x += (event.mouse_y - self.mou[1]) * self.walk_orbit_speed
                if rot.x < 0: rot.x = 0.00001
                elif rot.x > 3.14159: rot.x = 3.14159
            else:
                rot.x += (event.mouse_y - self.mou[1]) * self.walk_orbit_speed
                if rot.x > 0: rot.x = -0.00001
                elif rot.x < -3.14159: rot.x = -3.14159

        rot.z += (self.mou[0] - event.mouse_x) * self.walk_orbit_speed
        rot = rot.to_quaternion()
        # rv3d.view_rotation = rot

        view_matrix = rv3d.view_matrix
        vec = Vector()

        if keystate['forward'] is True:
            vec.x -= view_matrix[2][0]
            vec.y -= view_matrix[2][1]
        elif keystate['backward'] is True:
            vec.x += view_matrix[2][0]
            vec.y += view_matrix[2][1]
        if keystate['left'] is True:
            vec.x -= view_matrix[0][0]
            vec.y -= view_matrix[0][1]
        elif keystate['right'] is True:
            vec.x += view_matrix[0][0]
            vec.y += view_matrix[0][1]
        if keystate['up'] is True:
            vec.z += 1.0
        elif keystate['down'] is True:
            vec.z -= 1.0
        if keystate['speed_up'] is True:
            self.walk_speed += self.ccceleration_increment
            self.status_text_upd(context)
        elif keystate['speed_down'] is True:
            self.walk_speed -= self.ccceleration_increment
            self.status_text_upd(context)

        if vec.length_squared == 0:
            if keystate['dolly'] is True:
                dolly_vec = Vector((view_matrix[2][0], view_matrix[2][1], 0.0)) * (self.mou[1] - event.mouse_y) * self.dolly_speed

                if keystate['fast'] is True:
                    loc += dolly_vec * self.fast_fac
                elif keystate['slow'] is True:
                    loc += dolly_vec * self.slow_fac
                else:
                    loc += dolly_vec
        else:
            if keystate['dolly'] is True:
                dolly_vec = Vector((view_matrix[2][0], view_matrix[2][1], 0.0)) * (self.mou[1] - event.mouse_y) * self.dolly_speed

                if keystate['fast'] is True:
                    offset = vec.normalized() * self.TIMER.time_delta * self.walk_speed * self.fast_fac + dolly_vec * self.fast_fac
                elif keystate['slow'] is True:
                    offset = vec.normalized() * self.TIMER.time_delta * self.walk_speed * self.slow_fac + dolly_vec * self.slow_fac
                else:
                    offset = vec.normalized() * self.TIMER.time_delta * self.walk_speed + dolly_vec
            else:
                if keystate['fast'] is True:
                    offset = vec.normalized() * self.TIMER.time_delta * self.walk_speed * self.fast_fac
                elif keystate['slow'] is True:
                    offset = vec.normalized() * self.TIMER.time_delta * self.walk_speed * self.slow_fac
                else:
                    offset = vec.normalized() * self.TIMER.time_delta * self.walk_speed

            loc += offset

        cam.matrix_world = r_compose(loc, rot, sca)

        self.mou[0] = event.mouse_x
        self.mou[1] = event.mouse_y
        return {'RUNNING_MODAL'}
        #|
    #|
    #|
class OpsBlViewDolly(Operator):
    __slots__ = (
        'keymaps',
        'keystate',
        'mou',
        'mou_init',
        'i_modal',
        'rv3d',
        'rv3d_data',
        'cam',)

    bl_idname = "view3d.vmd_dolly"
    bl_label = "VMD View Dolly"
    bl_options = {"REGISTER", "GRAB_CURSOR", "BLOCKING"}
    bl_description = "Viewport Dolly / Pan"

    TIMER = None

    walk_orbit_speed: FloatProperty(default=0.002, min=0.00001, max=99999.0)
    dolly_speed: FloatProperty(default=0.1, min=0.00001, max=99999.0)
    pan_speed: FloatProperty(default=0.02, min=0.00001, max=99999.0)
    fast_fac: FloatProperty(default=5.0, min=0.00001, max=99999.0)
    slow_fac: FloatProperty(default=0.2, min=0.00001, max=99999.0)
    ccceleration_increment: FloatProperty(default=0.05, min=0.00001, max=99999.0)

    def timer_add(self, context):
        if OpsBlViewDolly.TIMER is None:
            OpsBlViewDolly.TIMER = context.window_manager.event_timer_add(0.00001, window=context.window)
        #|
    def time_remove(self, context):
        if OpsBlViewDolly.TIMER is None: return

        context.window_manager.event_timer_remove(OpsBlViewDolly.TIMER)
        OpsBlViewDolly.TIMER = None

        #|

    def status_text_upd(self, context):
        context.workspace.status_text_set(f'Walk Speed: {self.walk_speed}')
        #|

    def fin(self, context):

        self.time_remove(context)
        context.workspace.status_text_set(None)
        context.window.cursor_warp(*self.mou_init)
        context.window.cursor_modal_restore()

        return {'FINISHED'}
        #|

    def invoke(self, context, event):
        if check_area_type(self, context) is True: return {'CANCELLED'}

        v3d = context.space_data
        rv3d = v3d.region_3d

        self.rv3d = rv3d
        keymap_load(self)
        keymaps = self.keymaps
        self.keystate = {k: False  for k in keymaps.keys()}
        self.rv3d_data = {}
        context.workspace.status_text_set(' ')

        unlock_camera = True

        if rv3d.view_perspective == 'CAMERA' and context.scene.camera:
            return {'CANCELLED'}
            cam = context.scene.camera

            if v3d.lock_camera:
                unlock_camera = False
                self.i_modal = self.i_modal_cam_orbit
                self.cam = cam

            else:
                if cam.data.type == 'ORTHO':
                    rv3d.view_perspective = 'ORTHO'
                else:
                    rv3d.view_perspective = 'PERSP'

        if unlock_camera is True:
            if rv3d.view_perspective == 'PERSP':
                self.i_modal = self.i_modal_dolly

            elif rv3d.view_perspective == 'ORTHO':
                return {'CANCELLED'}

            else:
                return {'CANCELLED'}

        self.mou_init = [event.mouse_x, event.mouse_y]
        self.mou = [event.mouse_x, event.mouse_y]

        context.window.cursor_modal_set('NONE')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        #|

    def modal(self, context, event):
        try:
            keymaps = self.keymaps
            keystate = self.keystate

            if event.value == 'RELEASE':
                if event.type in {'ESC', keymaps['cancel']}:
                    return self.fin(context)

                if event.type == keymaps['pan']: keystate['pan'] = False
                # if event.type == keymaps['left']: keystate['left'] = False
                # if event.type == keymaps['right']: keystate['right'] = False
                # if event.type == keymaps['up']: keystate['up'] = False
                # if event.type == keymaps['down']: keystate['down'] = False
                # if event.type == keymaps['forward']: keystate['forward'] = False
                # if event.type == keymaps['backward']: keystate['backward'] = False
                if event.type == keymaps['fast']: keystate['fast'] = False
                if event.type == keymaps['slow']: keystate['slow'] = False
                # if event.type == keymaps['speed_up']: keystate['speed_up'] = False
                # if event.type == keymaps['speed_down']: keystate['speed_down'] = False
            else:
                if event.type == keymaps['pan']: keystate['pan'] = True
                # if event.type == keymaps['left']: keystate['left'] = True
                # if event.type == keymaps['right']: keystate['right'] = True
                # if event.type == keymaps['up']: keystate['up'] = True
                # if event.type == keymaps['down']: keystate['down'] = True
                # if event.type == keymaps['forward']: keystate['forward'] = True
                # if event.type == keymaps['backward']: keystate['backward'] = True
                if event.type == keymaps['fast']: keystate['fast'] = True
                if event.type == keymaps['slow']: keystate['slow'] = True
                # if event.type == keymaps['speed_up']: keystate['speed_up'] = True
                # if event.type == keymaps['speed_down']: keystate['speed_down'] = True

            return self.i_modal(context, event)
        except Exception as ex:
            (print(str(ex)))
            self.fin(context)
            self.report({'ERROR'}, "Please check the console")
            return {'CANCELLED'}
        #|

    def to_pan_mode(self, context, event):

        self.i_modal = self.i_modal_pan
        #|
    def to_dolly_mode(self, context, event):

        self.i_modal = self.i_modal_dolly
        #|

    def i_modal_dolly(self, context, event):
        keystate = self.keystate
        if keystate['pan'] is True:
            self.to_pan_mode(context, event)
            return {'RUNNING_MODAL'}

        rv3d = self.rv3d
        rot = rv3d.view_rotation.to_euler()
        rot.z += (self.mou[0] - event.mouse_x) * self.walk_orbit_speed
        rv3d.view_rotation = rot.to_quaternion()

        view_matrix = rv3d.view_matrix
        vec = Vector((view_matrix[2][0], view_matrix[2][1], 0.0))

        if keystate['fast'] is True:
            rv3d.view_location += vec.normalized() * (self.mou[1] - event.mouse_y) * self.dolly_speed * self.fast_fac
        elif keystate['slow'] is True:
            rv3d.view_location += vec.normalized() * (self.mou[1] - event.mouse_y) * self.dolly_speed * self.slow_fac
        else:
            rv3d.view_location += vec.normalized() * (self.mou[1] - event.mouse_y) * self.dolly_speed

        self.mou[0] = event.mouse_x
        self.mou[1] = event.mouse_y
        return {'RUNNING_MODAL'}
        #|
    def i_modal_pan(self, context, event):
        keystate = self.keystate
        if keystate['pan'] is False:
            self.to_dolly_mode(context, event)
            return {'RUNNING_MODAL'}

        rv3d = self.rv3d
        view_matrix = rv3d.view_matrix
        vec = Vector((view_matrix[0][0], view_matrix[0][1], 0.0))
        vec *= self.mou[0] - event.mouse_x
        vec.z = self.mou[1] - event.mouse_y

        if keystate['fast'] is True:
            rv3d.view_location += vec * self.pan_speed * self.fast_fac
        elif keystate['slow'] is True:
            rv3d.view_location += vec * self.pan_speed * self.slow_fac
        else:
            rv3d.view_location += vec * self.pan_speed

        self.mou[0] = event.mouse_x
        self.mou[1] = event.mouse_y
        return {'RUNNING_MODAL'}
        #|
    #|
    #|
class OpsBlViewZoom(Operator):
    __slots__ = (
        'keymaps',
        'keystate',
        'mou',
        'mou_init',
        'i_modal',
        'rv3d',
        'rv3d_data',
        'cam',)

    bl_idname = "view3d.vmd_zoom"
    bl_label = "VMD View Zoom"
    bl_options = {"REGISTER", "GRAB_CURSOR", "BLOCKING"}
    bl_description = "Viewport Zoom"

    zoom_speed: FloatProperty(default=0.005, min=0.00001, max=99999.0)
    zoom_speed_cam_unlock: FloatProperty(default=0.02, min=0.00001, max=99999.0)
    fast_fac: FloatProperty(default=5.0, min=0.00001, max=99999.0)
    slow_fac: FloatProperty(default=0.2, min=0.00001, max=99999.0)

    def fin(self, context):

        # context.workspace.status_text_set(None)
        context.window.cursor_warp(*self.mou_init)
        context.window.cursor_modal_restore()

        return {'FINISHED'}
        #|

    def invoke(self, context, event):
        if check_area_type(self, context) is True: return {'CANCELLED'}

        v3d = context.space_data
        rv3d = v3d.region_3d

        self.rv3d = rv3d
        keymap_load(self)
        keymaps = self.keymaps
        self.keystate = {k: False  for k in keymaps.keys()}
        self.rv3d_data = {}
        context.workspace.status_text_set(' ')

        if rv3d.view_perspective == 'CAMERA' and context.scene.camera:
            self.cam = context.scene.camera

            if v3d.lock_camera:
                if self.cam.data.type == 'ORTHO':
                    self.i_modal = self.i_modal_cam_lock_ortho
                else:
                    self.i_modal = self.i_modal_cam_lock
            else:
                self.i_modal = self.i_modal_cam_unlock
        else:
            self.i_modal = self.i_modal_zoom

        self.mou_init = [event.mouse_x, event.mouse_y]
        self.mou = [event.mouse_x, event.mouse_y]

        context.window.cursor_modal_set('NONE')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        #|

    def modal(self, context, event):
        try:
            keymaps = self.keymaps
            keystate = self.keystate

            if event.value == 'RELEASE':
                if event.type in {'ESC', keymaps['cancel']}:
                    return self.fin(context)

                if event.type == keymaps['fast']: keystate['fast'] = False
                if event.type == keymaps['slow']: keystate['slow'] = False
            else:
                if event.type == keymaps['fast']: keystate['fast'] = True
                if event.type == keymaps['slow']: keystate['slow'] = True

            return self.i_modal(context, event)
        except Exception as ex:
            (print(str(ex)))
            self.fin(context)
            self.report({'ERROR'}, "Please check the console")
            return {'CANCELLED'}
        #|

    def i_modal_zoom(self, context, event):
        rv3d = self.rv3d
        keystate = self.keystate

        if keystate['fast'] is True:
            rv3d.view_distance += (self.mou[1] - event.mouse_y) * max(0.00001, rv3d.view_distance * self.zoom_speed * self.fast_fac)
        elif keystate['slow'] is True:
            rv3d.view_distance += (self.mou[1] - event.mouse_y) * max(0.00001, rv3d.view_distance * self.zoom_speed * self.slow_fac)
        else:
            rv3d.view_distance += (self.mou[1] - event.mouse_y) * max(0.00001, rv3d.view_distance * self.zoom_speed)

        self.mou[0] = event.mouse_x
        self.mou[1] = event.mouse_y
        return {'RUNNING_MODAL'}
        #|
    def i_modal_cam_lock(self, context, event):
        rv3d = self.rv3d
        keystate = self.keystate

        view_matrix = rv3d.view_matrix

        if keystate['fast'] is True:
            le = (self.mou[1] - event.mouse_y) * max(0.00001, rv3d.view_distance * self.zoom_speed * self.fast_fac)
        elif keystate['slow'] is True:
            le = (self.mou[1] - event.mouse_y) * max(0.00001, rv3d.view_distance * self.zoom_speed * self.slow_fac)
        else:
            le = (self.mou[1] - event.mouse_y) * max(0.00001, rv3d.view_distance * self.zoom_speed)

        self.cam.location += Vector((view_matrix[2][0], view_matrix[2][1], view_matrix[2][2])).normalized() * le
        rv3d.view_distance += le

        self.mou[0] = event.mouse_x
        self.mou[1] = event.mouse_y
        return {'RUNNING_MODAL'}
        #|
    def i_modal_cam_lock_ortho(self, context, event):
        rv3d = self.rv3d
        keystate = self.keystate

        if keystate['fast'] is True:
            self.cam.data.ortho_scale += (self.mou[1] - event.mouse_y) * max(0.00001, self.zoom_speed * 3.0 * self.fast_fac)
        elif keystate['slow'] is True:
            self.cam.data.ortho_scale += (self.mou[1] - event.mouse_y) * max(0.00001, self.zoom_speed * 3.0 * self.slow_fac)
        else:
            self.cam.data.ortho_scale += (self.mou[1] - event.mouse_y) * max(0.00001, self.zoom_speed * 3.0)

        self.mou[0] = event.mouse_x
        self.mou[1] = event.mouse_y
        return {'RUNNING_MODAL'}
        #|
    def i_modal_cam_unlock(self, context, event):
        rv3d = self.rv3d
        keystate = self.keystate
 
        if keystate['fast'] is True:
            rv3d.view_camera_zoom += (event.mouse_y - self.mou[1]) * max(0.00001, self.zoom_speed_cam_unlock * 3.0 * self.fast_fac)
        elif keystate['slow'] is True:
            rv3d.view_camera_zoom += (event.mouse_y - self.mou[1]) * max(0.00001, self.zoom_speed_cam_unlock * 3.0 * self.slow_fac)
        else:
            rv3d.view_camera_zoom += (event.mouse_y - self.mou[1]) * max(0.00001, self.zoom_speed_cam_unlock * 3.0)

        self.mou[0] = event.mouse_x
        self.mou[1] = event.mouse_y
        return {'RUNNING_MODAL'}
        #|

    #|
    #|

class OpsBlViewMode(Operator):
    __slots__ = 'total_time'

    bl_idname = "object.vmd_mode_set"
    bl_label = "VMD Mode Set"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Toggle object / edit mode"

    key_hold_duration: FloatProperty(name='Key Hold duration', default=0.2, min=0.0, max=5.0)
    use_mode_color: BoolProperty(name='Use Mode Color')
    object_mode_color: FloatVectorProperty(name='Object Mode Color', subtype='COLOR_GAMMA', default=(0.2405, ) * 3, min=0.0, max=1.0)
    edit_mode_color: FloatVectorProperty(name='Edit Mode Color', subtype='COLOR_GAMMA', default=(0.2405, ) * 3, min=0.0, max=1.0)
    object_mode_show_floor: IntProperty(name='Object Mode Show Floor', default=0, min=-1, max=1)
    edit_mode_show_floor: IntProperty(name='Edit Mode Show Floor', default=1, min=-1, max=1)
    edit_mode_material: StringProperty(name='Edit Mode Material', default='(VMD Edit)')

    TEMP = {}
    TIMER = None

    def fin(self, context):

        self.time_remove(context)
        return {'FINISHED'}
        #|
    def timer_add(self, context):
        if OpsBlViewMode.TIMER is None:
            OpsBlViewMode.TIMER = context.window_manager.event_timer_add(0.00001, window=context.window)
        #|
    def time_remove(self, context):
        if OpsBlViewMode.TIMER is None: return

        context.window_manager.event_timer_remove(OpsBlViewMode.TIMER)
        OpsBlViewMode.TIMER = None

        #|

    def invoke(self, context, event):
        if check_area_type(self, context) is True: return {'CANCELLED'}

        self.total_time = 0.0
        self.timer_add(context)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        #|
    def modal(self, context, event):
        try:
            if event.type == 'TIMER':
                self.total_time += OpsBlViewMode.TIMER.time_delta
                if self.total_time > self.key_hold_duration:
                    self.switch_mode(context, event, False)
                    return self.fin(context)
                return {'RUNNING_MODAL'}

            if event.type == 'ESC' or event.value == 'RELEASE': pass
            else: return {'RUNNING_MODAL'}

            self.switch_mode(context, event)
            return self.fin(context)
        except:
            return self.fin(context)
        #|

    def switch_mode(self, context, event, use_switch_material=None):
        objects_in_mode = bpy.context.objects_in_mode[:]

        bpy.ops.object.mode_set(mode='EDIT', toggle=True)

        active_space = context.area.spaces.active
        shading = active_space.shading
        use_color = (self.use_mode_color == True and shading.background_type == 'VIEWPORT')

        if bpy.context.mode == 'OBJECT':
            if use_color:
                shading.background_color = Color(self.object_mode_color).from_srgb_to_scene_linear()
            if self.object_mode_show_floor != -1:
                active_space.overlay.show_floor = bool(self.object_mode_show_floor)

            if self.edit_mode_material:
                material = bpy.data.materials.get(self.edit_mode_material)
                temp = self.__class__.TEMP

                if material and objects_in_mode and temp:
                    materials = bpy.data.materials
                    for ob in objects_in_mode:
                        if ob.type == 'MESH' and ob.active_material is material and ob.session_uid in temp:
                            mat_uid = temp[ob.session_uid]
                            if mat_uid is None:
                                ob.active_material = None
                            else:
                                mat_set = r_bl_ID_by_uid(materials, temp[ob.session_uid])

                                if mat_set:
                                    ob.active_material = mat_set

                    temp.clear()

        elif bpy.context.mode == 'EDIT_MESH':
            if use_switch_material is None:
                use_switch_material = (self.total_time <= self.key_hold_duration)
            if use_color:
                shading.background_color = Color(self.edit_mode_color).from_srgb_to_scene_linear()
            if self.edit_mode_show_floor != -1:
                active_space.overlay.show_floor = bool(self.edit_mode_show_floor)
            if self.edit_mode_material and use_switch_material:
                material = bpy.data.materials.get(self.edit_mode_material)
                if material and bpy.context.objects_in_mode:
                    temp = self.__class__.TEMP

                    for ob in bpy.context.objects_in_mode:
                        if ob.type == 'MESH' and len(ob.material_slots) <= 1:
                            temp[ob.session_uid] = (ob.active_material.session_uid  if ob.active_material else None)
                            ob.active_material = material
        #|
    #|
    #|
class OpsBlViewLocal(Operator):
    __slots__ = ()

    bl_idname = "view3d.vmd_localview"
    bl_label = "VMD Loal View"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Toggle local view"

    use_animation: BoolProperty(name='Use Animation', default=True)
    use_mode_color: BoolProperty(name='Use Mode Color', default=True)
    bring_camera: BoolProperty(name='Bring Camera', default=True)
    local_mode_color: FloatVectorProperty(name='Local Mode Color', subtype='COLOR_GAMMA', default=(0.2405, 0.25, 0.2405), min=0.0, max=1.0)
    global_mode_color: FloatVectorProperty(name='Global Mode Color', subtype='COLOR_GAMMA', default=(0.2405, ) * 3, min=0.0, max=1.0)
    local_mode_show_floor: IntProperty(name='Local Mode Show Floor', default=-1, min=-1, max=1)
    global_mode_show_floor: IntProperty(name='Global Mode Show Floor', default=-1, min=-1, max=1)

    def invoke(self, context, event):
        if check_area_type(self, context) is True: return {'CANCELLED'}

        cam_selected = True
        if self.bring_camera and context.scene.camera:
            cam_selected = context.scene.camera.select_get()
            if not cam_selected:
                context.scene.camera.select_set(True)

        if self.use_animation:
            bpy.ops.view3d.localview('INVOKE_DEFAULT')
        else:
            bpy.ops.view3d.localview()

        active_space = context.space_data
        shading = active_space.shading
        use_color = (self.use_mode_color == True and shading.background_type == 'VIEWPORT')

        if context.space_data.local_view:
            if use_color:
                shading.background_color = Color(self.local_mode_color).from_srgb_to_scene_linear()
            if self.local_mode_show_floor != -1:
                active_space.overlay.show_floor = bool(self.local_mode_show_floor)
        else:
            if use_color:
                shading.background_color = Color(self.global_mode_color).from_srgb_to_scene_linear()
            if self.global_mode_show_floor != -1:
                active_space.overlay.show_floor = bool(self.global_mode_show_floor)

        if not cam_selected and self.bring_camera and context.scene.camera:
            context.scene.camera.select_set(False)
        return {'FINISHED'}
        #|
    #|
    #|
class OpsBlViewSync(Operator):
    __slots__ = ()

    bl_idname = "view3d.vmd_view_sync"
    bl_label = "VMD View Sync"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Synchronize view matrix across all viewports (from the active viewport) at once."

    sync_overlays_gizmo: BoolProperty(name='Sync Overlays and Gizmo')
    sync_shading_type: BoolProperty(name='Sync Shading Type')

    def execute(self, context):
        if check_area_type(self, context) is True: return {'CANCELLED'}

        space_data = context.space_data
        rv3d = space_data.region_3d

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type != 'VIEW_3D': continue
                if hasattr(area, 'spaces') and hasattr(area.spaces, 'active'):
                    space = area.spaces.active
                    r = space.region_3d

                    space.lens = space_data.lens
                    space.clip_start = space_data.clip_start
                    space.clip_end = space_data.clip_end
                    space.lock_camera = space_data.lock_camera
                    space.overlay.show_camera_passepartout = space_data.overlay.show_camera_passepartout
                    space.use_render_border = space_data.use_render_border

                    r.view_perspective = rv3d.view_perspective
                    r.is_orthographic_side_view = rv3d.is_orthographic_side_view
                    r.view_matrix = rv3d.view_matrix
                    r.view_camera_zoom = rv3d.view_camera_zoom
                    r.view_camera_offset = rv3d.view_camera_offset
                    r.lock_rotation = rv3d.lock_rotation
                    r.show_sync_view = rv3d.show_sync_view
                    r.use_box_clip = rv3d.use_box_clip
                    r.use_clip_planes = rv3d.use_clip_planes
                    r.update()

                    if self.sync_shading_type:
                        space.shading.type = space_data.shading.type
                    if self.sync_overlays_gizmo:
                        space.overlay.show_overlays = space_data.overlay.show_overlays
                        space.show_gizmo = space_data.show_gizmo
        return {'FINISHED'}
        #|

class OpsBlObjectSelectChild(Operator):
    __slots__ = ()

    bl_idname = "object.vmd_select_child"
    bl_label = "VMD Select Child"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Select all child objects of the selected objects recursively"

    method: EnumProperty(
        items=[
            ('CHILDREN_RECURSIVE', "Children Recursive", ""),
            ('COLLECTION_RECURSIVE', "Collection Recursive", ""),
        ],
        name="Method",
        description="",
    )

    def execute(self, context):
        if check_area_type(self, context) is True: return {'CANCELLED'}

        active = bpy.context.object
        method = self.method

        def select_child(ob):
            if hasattr(ob, 'children_recursive'):
                for o in ob.children_recursive:
                    o.select_set(True)

        if method == 'CHILDREN_RECURSIVE':
            for ob in context.selected_objects:
                select_child(ob)

        elif method == 'COLLECTION_RECURSIVE':
            select_grouped = bpy.ops.object.select_grouped
            select_grouped(extend=True, type='COLLECTION')
            for ob in context.selected_objects:
                select_child(ob)
        else:
            return {'CANCELLED'}

        return {'FINISHED'}
        #|
    #|
    #|

class OpsBlNodePreview(Operator):
    __slots__ = ()

    bl_idname = "node.vmd_preview"
    bl_label = "VMD Node Preview"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Preview node"

    preview_next: BoolProperty(name='Preview Next Socket', default=False)

    VIEWER_NAME = '(VMD Viewer)'

    @staticmethod
    def is_visible_socket(socket):
        if socket.hide: return False
        if socket.type == 'CUSTOM': return False
        return socket.enabled
        #|
    @staticmethod
    def check_active(active):
        return active and active.outputs and any(OpsBlNodePreview.is_visible_socket(out) for out in active.outputs)
        #|
    @staticmethod
    def r_first_output_index(outputs):
        for i, out in enumerate(outputs):
            if OpsBlNodePreview.is_visible_socket(out):
                return i

        return -1
        #|
    @staticmethod
    def r_next_output_index(outputs, ind):
        output_ind = ind
        for r in range(ind + 1, len(outputs)):
            if OpsBlNodePreview.is_visible_socket(outputs[r]):
                output_ind = r
                break

        if output_ind == ind:
            for r in range(0, len(outputs)):
                if OpsBlNodePreview.is_visible_socket(outputs[r]):
                    output_ind = r
                    break
        return output_ind
        #|
    @staticmethod
    def add_viewer_next_to_active(nodes, active, level_ind, space_data):
        viewer = None

        if level_ind == 0:
            if space_data.tree_type == 'ShaderNodeTree':
                viewer = nodes.new(type='ShaderNodeOutputMaterial')
            elif space_data.tree_type == 'GeometryNodeTree':
                viewer = nodes.new(type='NodeGroupOutput')
            elif space_data.tree_type == 'CompositorNodeTree':
                viewer = nodes.new(type='CompositorNodeViewer')
            else:
                return viewer

        else:
            viewer = nodes.new(type='NodeGroupOutput')

        viewer.name = viewer.label = OpsBlNodePreview.VIEWER_NAME
        viewer.location = active.location
        viewer.location[0] += active.dimensions.x + 30.0 * bpy.context.preferences.system.ui_scale

        return viewer
        #|
    @staticmethod
    def is_already_connected_to_output_node(active, output_nodes, good_output_index, target_name='Surface'):
        socket = active.outputs[good_output_index]
        if socket.is_linked:
            for link in socket.links:
                if link.is_hidden or link.is_muted: continue
                if link.to_node in output_nodes:
                    if target_name == None or link.to_socket.name == target_name:
                        if link.to_node.name == OpsBlNodePreview.VIEWER_NAME:
                            return None
                        return True

        return False
        #|
    @staticmethod
    def sockets_find(sockets, socket):
        for r, e in enumerate(sockets):
            if e == socket:
                return r

        return -1
        #|
    @staticmethod
    def r_geo_out_socket(viewer):
        for inp in viewer.inputs:
            if inp.bl_idname == 'NodeSocketGeometry':
                return inp

        return None
        #|

    def do_preview_next(self, context, space_data, level_ind):
        node_tree = space_data.path[level_ind].node_tree
        nodes = node_tree.nodes
        active = nodes.active
        if not active: return False

        if level_ind == 0 and space_data.tree_type == 'CompositorNodeTree':
            vmd_viewer = None

            for e in nodes:
                if e.type == 'VIEWER' and e.name == OpsBlNodePreview.VIEWER_NAME:
                    vmd_viewer = e
                    break

            if vmd_viewer is None: return False

            viewer_inp = None
            for e in vmd_viewer.inputs:
                if e.bl_idname == 'NodeSocketColor':
                    viewer_inp = e
                    break

            if viewer_inp is None: return False

            links = viewer_inp.links
            if links:
                l = links[0]
                if l.from_node == active:
                    ind = self.sockets_find(active.outputs, l.from_socket)
                    next_ind = self.r_next_output_index(active.outputs, ind)
                    node_tree.links.new(active.outputs[next_ind], viewer_inp)
            return

        if level_ind == 0 and space_data.tree_type != 'GeometryNodeTree':
            vmd_viewer = None

            for e in nodes:
                if e.type == 'OUTPUT_MATERIAL' and e.name == OpsBlNodePreview.VIEWER_NAME:
                    vmd_viewer = e
                    break

            if vmd_viewer is None: return False

            if 'Surface' in vmd_viewer.inputs:
                links = vmd_viewer.inputs['Surface'].links
                if links:
                    l = links[0]
                    if l.from_node == active:
                        ind = self.sockets_find(active.outputs, l.from_socket)
                        next_ind = self.r_next_output_index(active.outputs, ind)
                        node_tree.links.new(active.outputs[next_ind], vmd_viewer.inputs['Surface'])
        else:
            current_ind = -1
            is_good_ind = False
            for r, socket in enumerate(active.outputs):
                if socket.is_linked:
                    for link in socket.links:

                        if link.to_node.type == 'GROUP_OUTPUT' and link.to_node.name == OpsBlNodePreview.VIEWER_NAME:
                            if space_data.tree_type == 'GeometryNodeTree' and level_ind == 0:
                                if link.to_socket.bl_idname == 'NodeSocketGeometry':
                                    current_ind = r
                                    is_good_ind = True
                                    break
                            else:
                                if link.to_socket.name == OpsBlNodePreview.VIEWER_NAME:
                                    current_ind = r
                                    is_good_ind = True
                                    break
                if is_good_ind is True: break

            if is_good_ind is False: return False

            next_ind = self.r_next_output_index(active.outputs, current_ind)
            inp_socket = active.outputs[next_ind]
            items_tree = node_tree.interface.items_tree
            items_tree[items_tree.find(link.to_socket.name)].socket_type = inp_socket.bl_idname
            node_tree.links.new(inp_socket, link.to_socket)
        #|
    def do_current_level(self, context, space_data, level_ind, set_active=None):

        edit_tree = space_data.path[level_ind].node_tree
        nodes = edit_tree.nodes
        active = nodes.active

        if set_active:
            good_output_index = OpsBlNodePreview.VIEWER_NAME

            new_active = None
            for e in nodes:
                if e.type == 'GROUP' and e.hide == False and e.mute == False:
                    if e.node_tree == set_active:
                        new_active = e

            if new_active is None:
                self.remove_all_vmd_viewer(context, space_data)
                self.report({'WARNING'}, "Lower level node group not found or node group has been hidden")
                return True

            nodes.active = new_active
            active = new_active
        else:
            if not self.check_active(active): return False

            good_output_index = self.r_first_output_index(active.outputs)
            if good_output_index == -1: return False

        self.remove_all_vmd_viewer_on_level(context, space_data, level_ind)
        viewer = self.add_viewer_next_to_active(nodes, active, level_ind, space_data)
        if viewer is None: return False

        if level_ind == 0:
            if space_data.tree_type == 'ShaderNodeTree':
                output_nodes = [e for e in nodes if e.type == 'OUTPUT_MATERIAL']
                connect_state = self.is_already_connected_to_output_node(active, output_nodes, good_output_index)
                if connect_state in {True, None}:
                    nodes.remove(viewer)

                    if connect_state is None:
                        self.remove_all_vmd_viewer(context, space_data)
                        return True
                    return False

                edit_tree.links.new(active.outputs[good_output_index], viewer.inputs['Surface'])
                viewer.is_active_output = True
                return True
            elif space_data.tree_type == 'GeometryNodeTree':
                out_socket = self.r_geo_out_socket(viewer)
                if not out_socket:
                    self.report({'WARNING'}, "Output Geometry socket is required")
                    return False
                edit_tree.links.new(active.outputs[good_output_index], out_socket)
                viewer.is_active_output = True
                return True
            elif space_data.tree_type == 'CompositorNodeTree':
                out_socket = None
                for inp in viewer.inputs:
                    if inp.bl_idname == 'NodeSocketColor':
                        out_socket = inp
                        break

                if not out_socket:
                    self.report({'WARNING'}, "Output socket not found")
                    return False

                edit_tree.links.new(active.outputs[good_output_index], out_socket)
                nodes.active = viewer
                nodes.active = active
                return True
            return False

        inp_socket = active.outputs[good_output_index]
        interface = edit_tree.interface
        interface.new_socket(OpsBlNodePreview.VIEWER_NAME, in_out='OUTPUT', socket_type=inp_socket.bl_idname)
        viewer.is_active_output = True

        edit_tree.links.new(inp_socket, viewer.inputs[OpsBlNodePreview.VIEWER_NAME])
        self.do_current_level(context, space_data, level_ind - 1, bpy.data.node_groups[edit_tree.name])
        return True
        #|
    def remove_items_tree_item_safe(self, interface):
        for it in interface.items_tree:
            if it.name == OpsBlNodePreview.VIEWER_NAME:
                interface.remove(it)
                return True
        return False
        #|
    def remove_all_vmd_viewer_on_level(self, context, space_data, level_ind):
        path = space_data.path[level_ind]

        for e in path.node_tree.nodes:
            if e.type in {'OUTPUT_MATERIAL', 'GROUP_OUTPUT', 'VIEWER'}:
                if e.name == OpsBlNodePreview.VIEWER_NAME:
                    path.node_tree.nodes.remove(e)

        if level_ind == 0: pass
        else:
            # -RANDOM CRASH-
            # interface = path.node_tree.interface
            # for it in interface.items_tree:
            #     if it.name == OpsBlNodePreview.VIEWER_NAME:
            #         interface.remove(it)

            while True:
                interface = path.node_tree.interface
                if self.remove_items_tree_item_safe(interface): continue
                break
        #|
    def remove_all_vmd_viewer(self, context, space_data):
        for ind in range(len(space_data.path) - 1, -1, -1):
            self.remove_all_vmd_viewer_on_level(context, space_data, ind)
        #|

    def invoke(self, context, event):
        if check_area_type(self, context, 'NODE_EDITOR') is True: return {'CANCELLED'}

        space_data = context.space_data

        if space_data.tree_type not in {'ShaderNodeTree', 'GeometryNodeTree', 'CompositorNodeTree'}: return {'CANCELLED'}

        if 'FINISHED' not in (bpy.ops.node.select(location=(event.mouse_region_x, event.mouse_region_y), extend=False)):
            return {'CANCELLED'}

        level_ind = len(space_data.path) - 1

        in_preview = False
        if level_ind == 0:
            for out in space_data.edit_tree.nodes.active.outputs:
                for l in out.links:
                    if l.to_node.type in {'OUTPUT_MATERIAL', 'GROUP_OUTPUT', 'VIEWER'} and l.to_node.name == OpsBlNodePreview.VIEWER_NAME:
                        if space_data.tree_type == 'CompositorNodeTree':
                            if l.to_socket.bl_idname == 'NodeSocketColor':
                                in_preview = True
                        elif l.to_socket.name == 'Surface' or l.to_socket.bl_idname == 'NodeSocketGeometry':
                            in_preview = True
        else:
            nodes = space_data.path[level_ind].node_tree.nodes
            for out in nodes.active.outputs:
                for l in out.links:
                    if l.to_node.type == 'GROUP_OUTPUT' and l.to_socket.name == OpsBlNodePreview.VIEWER_NAME:
                        in_preview = True



        if in_preview:
            if self.preview_next:
                if self.do_preview_next(context, space_data, level_ind) is False:
                    return {'CANCELLED'}
            else:
                self.remove_all_vmd_viewer(context, space_data)
            return {'FINISHED'}

        if self.do_current_level(context, space_data, level_ind) is False:
            return {'CANCELLED'}

        return {'FINISHED'}
        #|
    #|
    #|
class OpsBlEeveeReset(Operator):
    __slots__ = ()

    bl_idname = "view3d.vmd_eevee_material_reset"
    bl_label = "VMD Eevee Material Reset"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Reset selected eevee material"

    surface_node: StringProperty(name='Surface Node', default='')

    def execute(self, context):

        if check_area_type(self, context) is True: return {'CANCELLED'}

        for ob in context.selected_objects:
            if not hasattr(ob, 'active_material'): continue

            mat = ob.active_material
            if not mat: continue

            tree = mat.node_tree
            nodes = tree.nodes
            bbox = r_bbox_nodes(nodes)
            out_node = r_eevee_output(nodes)

            ui_scale = context.preferences.system.ui_scale

            if not out_node:
                out_node = nodes.new(type='ShaderNodeOutputMaterial')
                out_node.target = 'EEVEE'

                if self.surface_node:
                    shader_group = bpy.data.node_groups.get(self.surface_node)
                    if not shader_group:
                        self.report({'WARNING'}, "Surface node not found")
                        return {'CANCELLED'}

                    if not hasattr(shader_group, 'type') or shader_group.type != 'SHADER':
                        self.report({'WARNING'}, "Surface node type error")
                        return {'CANCELLED'}

                    shader_node = nodes.new(type='ShaderNodeGroup')
                    shader_node.node_tree = shader_group
                else:
                    shader_node = nodes.new(type='ShaderNodeBsdfPrincipled')

                tree.links.new(shader_node.outputs['BSDF'], out_node.inputs['Surface'])
                shader_node.location[:] = bbox[1], bbox[2] - 50 * ui_scale
                out_node.location[:] = shader_node.location.x + shader_node.width + 30 * ui_scale, shader_node.location.y
        return {'FINISHED'}
        #|
    #|
    #|


classes = (
    OpsWinman,
    OpsEditor,
    OpsLoadFactory,
    OpsReloadIcon,
    OpsReloadFont,
    OpsUiScale,
    OpsBlNewWinRender,
    OpsBlViewRotate,
    OpsBlViewDolly,
    OpsBlViewZoom,
    OpsBlViewMode,
    OpsBlViewLocal,
    OpsBlViewSync,
    OpsBlObjectSelectChild,
    OpsBlNodePreview,
    OpsBlEeveeReset,
)

def register():
    bpy.types.TOPBAR_MT_window.prepend(OpsBlNewWinRender_draw_rm)
    #|
def unregister():
    bpy.types.TOPBAR_MT_window.remove(OpsBlNewWinRender_draw_rm)
    #|

## _file_ ##
def late_import():
    #|
    from .  import VMD

    m = VMD.m
    call_admin = m.call_admin
    kill_admin = m.kill_admin

    blg = VMD.utilbl.blg

    globals().update(locals())
    #|
