# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025  Bohdan Hrytsenko
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.



bl_info = {
    "name": "BH Smart Sym",
    "author": "Bohdan Hrytsenko",
    "version": (0, 9, 0),
    "blender": (4, 4, 0),
    "location": "Edit Mode (Alt+X)",
    "description": "Smart Symmetrize with solid unified arrows (shaft + tip) that appear instantly and stay synced.",
    "doc_url": "https://www.linkedin.com/in/bohdan-hrytsenko/",
    "category": "Mesh",
}

import bpy
import gpu
import bmesh
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix
from bpy_extras import view3d_utils


# ---------- Preferences ----------
class SmartSymPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    arrow_size: bpy.props.FloatProperty(
        name="Arrow Size (px)",
        description="Fixed on-screen size of arrows",
        default=80.0, min=30.0, max=200.0,
    )

    hotkey_type: bpy.props.StringProperty(default="X")
    hotkey_ctrl: bpy.props.BoolProperty(default=False)
    hotkey_shift: bpy.props.BoolProperty(default=False)
    hotkey_alt: bpy.props.BoolProperty(default=True)
    waiting_input: bpy.props.BoolProperty(default=False)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Arrow Settings:")
        col.prop(self, "arrow_size")

        col.separator()
        col.label(text="Hotkey Settings:")
        if not self.waiting_input:
            row = col.row(align=True)
            hotkey = self._format_hotkey()
            row.operator("bh_sym.change_hotkey", text=f"Change Hotkey ({hotkey})")
            col.operator("bh_sym.reset_hotkey", text="Reset to Default (Alt+X)")
        else:
            col.label(text="Press new hotkey combination...", icon="KEYINGSET")

    def _format_hotkey(self):
        parts = []
        if self.hotkey_ctrl: parts.append("Ctrl")
        if self.hotkey_shift: parts.append("Shift")
        if self.hotkey_alt: parts.append("Alt")
        parts.append(self.hotkey_type)
        return " + ".join(parts)


# ---------- Hotkey management ----------
addon_keymaps = []


def register_hotkey():
    prefs = bpy.context.preferences.addons[__name__].preferences
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return
    km = kc.keymaps.new(name="Mesh", space_type="EMPTY")
    kmi = km.keymap_items.new(
        "mesh.smart_symmetrize_modal",
        type=prefs.hotkey_type,
        value="PRESS",
        ctrl=prefs.hotkey_ctrl,
        shift=prefs.hotkey_shift,
        alt=prefs.hotkey_alt,
    )
    addon_keymaps.append((km, kmi))


def unregister_hotkey():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


# ---------- Hotkey Operators ----------
class BH_OT_ChangeHotkey(bpy.types.Operator):
    bl_idname = "bh_sym.change_hotkey"
    bl_label = "Change Hotkey"

    def invoke(self, context, event):
        prefs = bpy.context.preferences.addons[__name__].preferences
        prefs.waiting_input = True
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        prefs = bpy.context.preferences.addons[__name__].preferences
        if event.value == 'PRESS':
            if event.type in {'ESC', 'RIGHTMOUSE'}:
                prefs.waiting_input = False
                return {'CANCELLED'}
            if event.type in {'LEFT_SHIFT', 'RIGHT_SHIFT', 'LEFT_CTRL', 'RIGHT_CTRL', 'LEFT_ALT', 'RIGHT_ALT'}:
                return {'RUNNING_MODAL'}

            unregister_hotkey()
            prefs.hotkey_type = event.type
            prefs.hotkey_ctrl = event.ctrl
            prefs.hotkey_shift = event.shift
            prefs.hotkey_alt = event.alt
            prefs.waiting_input = False
            register_hotkey()
            self.report({'INFO'}, f"New hotkey: {prefs._format_hotkey()}")
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


class BH_OT_ResetHotkey(bpy.types.Operator):
    bl_idname = "bh_sym.reset_hotkey"
    bl_label = "Reset Hotkey"

    def execute(self, context):
        prefs = bpy.context.preferences.addons[__name__].preferences
        unregister_hotkey()
        prefs.hotkey_type = "X"
        prefs.hotkey_ctrl = False
        prefs.hotkey_shift = False
        prefs.hotkey_alt = True
        register_hotkey()
        self.report({'INFO'}, "Hotkey reset to Alt+X")
        return {'FINISHED'}


# ---------- Geometry ----------
def make_solid_arrow(base, direction, length):
    dir_n = direction.normalized()
    tip = base + dir_n * length
    shaft_mid = base + dir_n * (length * 0.75)

    side = dir_n.cross(Vector((0, 1, 0)))
    if side.length < 1e-6:
        side = Vector((1, 0, 0))
    side.normalize()
    side2 = dir_n.cross(side).normalized()

    head_w = length * 0.12
    points = [
        base,
        shaft_mid,
        tip,
        shaft_mid + side * head_w,
        tip,
        shaft_mid - side * head_w,
        tip,
        shaft_mid + side2 * head_w,
        tip,
        shaft_mid - side2 * head_w,
    ]
    return points, tip


# ---------- Operator ----------
class MESH_OT_smart_symmetrize_modal(bpy.types.Operator):
    bl_idname = "mesh.smart_symmetrize_modal"
    bl_label = "Smart Symmetrize"
    bl_options = {'REGISTER', 'UNDO'}

    _handle = None
    _timer = None
    _arrows = []
    _hover = None

    # режим mirror: "ORIGIN" або "CURSOR"
    _mirror_mode = "ORIGIN"

    def _update_status_text(self, context):
        ws = getattr(context, "workspace", None)
        if ws is None:
            return
        mode_label = "Origin" if self._mirror_mode == "ORIGIN" else "3D Cursor"
        ws.status_text_set(
            f"Smart Symmetrize | LMB: Apply | C: 3D Cursor Mirror | V: Origin Mirror | Current: {mode_label} | RMB/Esc: Cancel"
        )

    def _clear_status_text(self, context):
        ws = getattr(context, "workspace", None)
        if ws is not None:
            ws.status_text_set(None)

    def update_arrows(self, context):
        obj = context.object
        if not obj:
            return

        prefs = bpy.context.preferences.addons[__name__].preferences
        arrow_px = prefs.arrow_size
        region = context.region
        rv3d = context.space_data.region_3d

        # База для стрілок: або Origin об'єкта, або 3D Cursor (з ротацією)
        if self._mirror_mode == "CURSOR":
            cursor = context.scene.cursor
            origin = cursor.location
            basis = cursor.rotation_euler.to_matrix()
            axes = {
                'X': basis @ Vector((1, 0, 0)),
                'Y': basis @ Vector((0, 1, 0)),
                'Z': basis @ Vector((0, 0, 1)),
            }
        else:
            origin = obj.matrix_world.translation
            basis = obj.matrix_world.to_3x3()
            axes = {
                'X': basis @ Vector((1, 0, 0)),
                'Y': basis @ Vector((0, 1, 0)),
                'Z': basis @ Vector((0, 0, 1)),
            }

        self._arrows.clear()

        view_dir = (rv3d.view_rotation @ Vector((0, 0, -1))).normalized()
        colors = {'X': (1, 0.1, 0.1, 1), 'Y': (0.1, 1, 0.1, 1), 'Z': (0.1, 0.5, 1, 1)}
        dark_mul = 0.45

        for axis_name, vec in axes.items():
            for sign in (1, -1):
                color = colors[axis_name] if sign > 0 else tuple(c * dark_mul for c in colors[axis_name][:3]) + (1,)
                dir_ws = vec * sign
                dot_val = abs(dir_ws.normalized().dot(view_dir))
                if dot_val > 0.96:
                    tilt = view_dir.cross(dir_ws).normalized() * 0.1
                    dir_ws = (dir_ws + tilt).normalized()
                p_origin_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, origin)
                if not p_origin_2d:
                    continue
                offset_2d = p_origin_2d + Vector((arrow_px, 0))
                p_tip_ws = view3d_utils.region_2d_to_location_3d(region, rv3d, offset_2d, origin)
                length = (p_tip_ws - origin).length
                points, tip = make_solid_arrow(origin, dir_ws, length)
                self._arrows.append({'axis': axis_name, 'sign': sign, 'points': points, 'tip': tip, 'color': color})

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        if event.type == 'TIMER':
            self.update_arrows(context)

        # Перемикання режимів mirror: C (3D Cursor), V (Origin)
        if event.type in {'C', 'V'} and event.value == 'PRESS':
            if event.type == 'C':
                self._mirror_mode = "CURSOR"
                self.report({'INFO'}, "Smart Sym: Mirror from 3D Cursor")
            else:
                self._mirror_mode = "ORIGIN"
                self.report({'INFO'}, "Smart Sym: Mirror from Origin")

            self.update_arrows(context)
            self._update_status_text(context)
            if context.area:
                context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        if event.type in {
            'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
            'WHEELINMOUSE', 'WHEELOUTMOUSE'
        } or (event.type == 'MOUSEMOVE' and event.alt):
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            mx, my = event.mouse_region_x, event.mouse_region_y
            region, rv3d = context.region, context.space_data.region_3d
            tol = 20
            self._hover = None
            for i, a in enumerate(self._arrows):
                tip_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, a['tip'])
                if tip_2d and (mx - tip_2d.x) ** 2 + (my - tip_2d.y) ** 2 <= tol ** 2:
                    self._hover = i
                    break

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.finish(context)
            return {'CANCELLED'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and self._hover is not None:
            a = self._arrows[self._hover]
            direction = ("POSITIVE" if a['sign'] > 0 else "NEGATIVE") + "_" + a['axis']

            if self._mirror_mode == "ORIGIN":
                # стандартний режим (як і раніше)
                bpy.ops.mesh.symmetrize(direction=direction, threshold=0.0001)
            else:
                # режим від 3D Cursor з урахуванням ротації курсора
                obj = context.object
                if obj and obj.type == 'MESH':
                    me = obj.data
                    bm = bmesh.from_edit_mesh(me)

                    M = obj.matrix_world.copy()
                    M_inv = M.inverted()

                    cursor = context.scene.cursor
                    C = cursor.location.copy()
                    R = cursor.rotation_euler.to_matrix()
                    R_inv = R.inverted()

                    # 1) локал -> світ -> простір курсора
                    for v in bm.verts:
                        world = M @ v.co
                        v_cursor = R_inv @ (world - C)
                        v.co = v_cursor
                    bmesh.update_edit_mesh(me, loop_triangles=False)

                    # 2) симетрія в просторі курсора (X/Y/Z = осі курсора)
                    bpy.ops.mesh.symmetrize(direction=direction, threshold=0.0001)

                    # 3) повертаємо назад: простір курсора -> світ -> локал
                    bm = bmesh.from_edit_mesh(me)
                    for v in bm.verts:
                        world = R @ v.co + C
                        v_local = M_inv @ world
                        v.co = v_local
                    bmesh.update_edit_mesh(me, loop_triangles=False)

            self.finish(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        obj = context.object
        if not obj or obj.type != 'MESH' or context.mode != 'EDIT_MESH':
            self.report({'WARNING'}, "Edit Mode mesh required")
            return {'CANCELLED'}

        self._mirror_mode = "ORIGIN"
        self._update_status_text(context)

        self._shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        self.update_arrows(context)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.25, window=context.window)

        if context.area.type == 'VIEW_3D':
            self._handle = bpy.types.SpaceView3D.draw_handler_add(
                self.draw_callback, (context,), 'WINDOW', 'POST_VIEW'
            )
            wm.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D area required")
            return {'CANCELLED'}

    def finish(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
        if self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        if context.area:
            context.area.tag_redraw()
        self._clear_status_text(context)

    def draw_callback(self, context):
        gpu.state.blend_set('ALPHA')
        for i, a in enumerate(self._arrows):
            col = (1, 1, 0, 1) if i == self._hover else a['color']
            batch = batch_for_shader(self._shader, 'LINE_STRIP', {"pos": a['points']})
            self._shader.bind()
            self._shader.uniform_float("color", col)
            batch.draw(self._shader)
        gpu.state.blend_set('NONE')


# ---------- Register ----------
classes = (
    SmartSymPreferences,
    BH_OT_ChangeHotkey,
    BH_OT_ResetHotkey,
    MESH_OT_smart_symmetrize_modal,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_hotkey()


def unregister():
    unregister_hotkey()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
