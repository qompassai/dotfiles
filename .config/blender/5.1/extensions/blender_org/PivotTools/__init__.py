bl_info = {
    "name": "Pivot Tools",
    "author": "Henrik Drygas",
    "version": (1, 48, 13),  # patch: edit-mode drift fix for Bottom Center + author line
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > Pivot Tools",
    "description": "Fast pivot placement: object/world/cursor/bottom-center, Auto Pick with preview, BBox click targets, Saved Pivots.",
    "category": "Object",
}

import bpy
import math
import mathutils
from mathutils import Vector, Matrix
from bpy_extras import view3d_utils
import gpu
from gpu_extras.batch import batch_for_shader

ADDON_ID = __package__ if __package__ else __name__

def get_prefs():
    addon = bpy.context.preferences.addons.get(ADDON_ID)
    return addon.preferences if addon else None

def warn_transform_apply(context, operator=None):
    wm = getattr(context, "window_manager", None)
    if wm is None:
        return
    if wm.get("ptools_warned_apply", False):
        return
    wm["ptools_warned_apply"] = True
    msg = "Pivot Tools applies Location/Rotation/Scale transforms before placing the pivot."
    if operator is not None:
        try:
            operator.report({'WARNING'}, msg)
        except:
            pass

PTTOOLS_CONFIRM_TITLE = "Apply Transforms"
PTTOOLS_CONFIRM_MESSAGE = "Pivot Tools applies Location/Rotation/Scale transforms before placing the pivot."


def _apply_transforms_safe(context, obj):
    """Apply Location/Rotation/Scale for exactly one object, without affecting other selected objects."""
    view_layer = context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = [o for o in view_layer.objects if o.select_get()]

    try:
        # Isolate selection to the target object
        for o in prev_selected:
            o.select_set(False)
        obj.select_set(True)
        view_layer.objects.active = obj

        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    finally:
        # Restore selection and active object
        try:
            obj.select_set(False)
        except Exception:
            pass
        for o in prev_selected:
            try:
                o.select_set(True)
            except Exception:
                pass
        view_layer.objects.active = prev_active


class PivotToolsPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID

    hover_color: bpy.props.FloatVectorProperty(
        name="Highlight Color",
        subtype='COLOR', size=4, min=0.0, max=1.0,
        default=(1.0, 0.5, 0.0, 1.0),
        description="Color for Auto Pick preview and BBox targets"
    )

    adaptive_preview: bpy.props.BoolProperty(
        name="Adaptive Preview Size",
        default=True,
        description="Auto-scale preview by view distance & object size"
    )
    preview_px_min: bpy.props.IntProperty(
        name="Min Size (px)", default=12, min=6, max=128,
        description="Smallest screen size for the preview"
    )
    preview_px_max: bpy.props.IntProperty(
        name="Max Size (px)", default=40, min=8, max=256,
        description="Largest screen size for the preview"
    )
    density_influence: bpy.props.FloatProperty(
        name="Mesh Density Influence", default=0.6, min=0.0, max=2.0,
        description="Higher value shrinks preview more on dense meshes"
    )
    circle_radius: bpy.props.FloatProperty(
        name="Fixed Radius (fallback)", min=0.002, max=2.0, default=0.05,
        description="Used if Adaptive Preview Size is off"
    )

    confirm_transform_apply: bpy.props.BoolProperty(
        name="Confirm Before Applying Transforms",
        default=True,
        description="Show a confirmation dialog before Pivot Tools applies Location/Rotation/Scale transforms"
    )

    def draw(self, _context):
        col = self.layout.column(align=True)
        col.label(text="Auto Pick Preview")
        col.prop(self, "adaptive_preview")
        row = col.row(align=True)
        row.prop(self, "preview_px_min")
        row.prop(self, "preview_px_max")
        col.prop(self, "density_influence")
        self.layout.separator()
        self.layout.prop(self, "hover_color")
        self.layout.separator()
        self.layout.prop(self, "confirm_transform_apply")
        self.layout.separator()
        tip = self.layout.box()
        tip.label(text="Tip", icon='INFO')
        tip.label(text="Add panel buttons to Quick Favorites via right-click.")

def gather_targets(context):
    if getattr(context.scene, "ptools_apply_all", False):
        return [o for o in context.selected_objects if o.type == 'MESH']
    obj = context.object
    return [obj] if (obj and obj.type == 'MESH') else []

def _bbox_min_mid_max_local(obj):
    bb = [mathutils.Vector(c) for c in obj.bound_box]
    xs, ys, zs = [v.x for v in bb], [v.y for v in bb], [v.z for v in bb]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    z_min, z_max = min(zs), max(zs)
    x_mid = 0.5*(x_min+x_max)
    y_mid = 0.5*(y_min+y_max)
    z_mid = 0.5*(z_min+z_max)
    return (x_min, x_mid, x_max), (y_min, y_mid, y_max), (z_min, z_mid, z_max)


def apply_pivot_bottom_center(obj):
    xs, ys, zs = _bbox_min_mid_max_local(obj)
    local_pt = Vector((xs[1], ys[1], zs[0]))
    mw = obj.matrix_world.copy()
    obj.data.transform(Matrix.Translation(-local_pt))
    obj.location = mw @ local_pt


def _combined_bbox_min_mid_max_world(objs):
    if not objs: return None
    all_pts = []
    for o in objs:
        mw = o.matrix_world
        for c in o.bound_box:
            all_pts.append(mw @ Vector(c))
    xs = [p.x for p in all_pts]; ys = [p.y for p in all_pts]; zs = [p.z for p in all_pts]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    z_min, z_max = min(zs), max(zs)
    x_mid = 0.5*(x_min+x_max)
    y_mid = 0.5*(y_min+y_max)
    z_mid = 0.5*(z_min+z_max)
    return (x_min, x_mid, x_max), (y_min, y_mid, y_max), (z_min, z_mid, z_max)

def _pixels_to_world_radius_at(context, world_point: Vector, px: int) -> float:
    area, region, rv3d = context.area, context.region, context.region_data
    if not (area and region and rv3d): return 0.0
    loc2d = view3d_utils.location_3d_to_region_2d(region, rv3d, world_point)
    if loc2d is None: return 0.0
    p1 = view3d_utils.region_2d_to_origin_3d(region, rv3d, (loc2d.x, loc2d.y))
    d1 = view3d_utils.region_2d_to_vector_3d(region, rv3d, (loc2d.x, loc2d.y))
    p2 = view3d_utils.region_2d_to_origin_3d(region, rv3d, (loc2d.x + px, loc2d.y))
    d2 = view3d_utils.region_2d_to_vector_3d(region, rv3d, (loc2d.x + px, loc2d.y))
    view_dir = (rv3d.view_rotation @ Vector((0, 0, -1.0))).normalized()
    plane_n, plane_p = view_dir, world_point
    def ray_plane(o, d):
        denom = d.dot(plane_n)
        if abs(denom) < 1e-8: return None
        t = (plane_p - o).dot(plane_n) / denom
        if t < 0: return None
        return o + d * t
    a = ray_plane(p1, d1); b = ray_plane(p2, d2)
    if a is None or b is None: return 0.0
    return (b - a).length

def _object_screen_coverage_and_density(context, obj):
    region, rv3d = context.region, context.region_data
    if not (obj and region and rv3d): return 0.0, 0.0, 0.0
    mw = obj.matrix_world
    corners = [mw @ Vector(c) for c in obj.bound_box]
    pts = [view3d_utils.location_3d_to_region_2d(region, rv3d, p) for p in corners]
    pts = [p for p in pts if p is not None]
    if len(pts) < 2: return 0.0, 0.0, 0.0
    xs = [p.x for p in pts]; ys = [p.y for p in pts]
    w = max(xs) - min(xs); h = max(ys) - min(ys)
    bbox_area = max(0.0, w*h)
    screen_area = max(1.0, region.width * region.height)
    coverage = max(0.0, min(1.0, bbox_area / screen_area))

    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    me = eval_obj.to_mesh()
    try:
        polys = len(me.polygons) if me else 0
    finally:
        eval_obj.to_mesh_clear()
    denom = max(1.0, bbox_area)
    density = polys / (denom / 300000.0) / 5000.0
    density = max(0.0, min(2.0, density))
    return coverage, density, bbox_area

def _smart_preview_px(context, obj, prefs):
    cov, dens, _ = _object_screen_coverage_and_density(context, obj)
    growth = math.sqrt(cov)
    base = prefs.preview_px_min + (prefs.preview_px_max - prefs.preview_px_min) * growth
    adj = base / (1.0 + prefs.density_influence * dens)
    return max(prefs.preview_px_min, min(prefs.preview_px_max, int(adj)))

class OBJECT_OT_pivot_to_bottom_center(bpy.types.Operator):
    bl_idname = "object.pivot_to_bottom_center"
    bl_label = "Origin to Bottom Center"
    bl_description = "Move origin to the bottom center of the object bounds (applies to selection if Apply to All Selected is enabled)"
    bl_options = {"REGISTER", "UNDO"}

    dont_show_again: bpy.props.BoolProperty(
        name="Don't show again",
        default=False,
        description="Disable the confirmation dialog in the add-on preferences"
    )

    @classmethod
    def poll(cls, context):
        obj = context.object
        return context.mode == 'OBJECT' and obj is not None and obj.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        layout.label(text=PTTOOLS_CONFIRM_MESSAGE, icon='INFO')
        layout.prop(self, "dont_show_again")

    def invoke(self, context, _event):
        prefs = get_prefs()
        if prefs and getattr(prefs, "confirm_transform_apply", True):
            return context.window_manager.invoke_props_dialog(self, width=420)
        return self.execute(context)

    def execute(self, context):
        prefs = get_prefs()
        if prefs and getattr(prefs, "confirm_transform_apply", True) and self.dont_show_again:
            prefs.confirm_transform_apply = False

        targets = gather_targets(context)
        if not targets:
            return {'CANCELLED'}

        warn_transform_apply(context, self)

        for obj in targets:
            if obj.type != 'MESH':
                continue
            context.view_layer.objects.active = obj
            _apply_transforms_safe(context, obj)
            apply_pivot_bottom_center(obj)

        return {'FINISHED'}

class OBJECT_OT_pick_geom_pivot_auto(bpy.types.Operator):
    """Hover a face to preview; click to set origin to nearest of face center / edge mid / vertex.
    Temporarily shows wireframe overlay for clarity, then restores your settings."""
    bl_idname = "object.pick_geom_pivot_auto"
    bl_label = "Pick Geometry Pivot (Auto)"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Interactive: hover to preview and click to place the origin on a smart point (applies transforms first); shows temporary wireframe"

    dont_show_again: bpy.props.BoolProperty(
        name="Don't show again",
        default=False,
        description="Disable the confirmation dialog in the add-on preferences"
    )

    _ptools_confirm_xy = None

    _handle = None
    hit_world = None
    best_local = None
    _obj_ref = None

    _overlay_states = None   # [(overlay_ref, old_show_wireframes)]
    _obj_wire_prev = None    # bool or None

    def draw(self, context):
        layout = self.layout
        layout.label(text=PTTOOLS_CONFIRM_MESSAGE, icon='INFO')
        layout.prop(self, "dont_show_again")

    def invoke(self, context, event):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Active object must be a mesh")
            return {'CANCELLED'}

        prefs = get_prefs()
        if prefs and getattr(prefs, "confirm_transform_apply", True):
            # Keep the real click coordinates so the modal tool starts immediately after OK.
            try:
                self._ptools_confirm_xy = (int(event.mouse_region_x), int(event.mouse_region_y))
            except Exception:
                self._ptools_confirm_xy = None
            self.dont_show_again = False
            return context.window_manager.invoke_props_dialog(self, width=420)

        return self._start(context, event)

    def execute(self, context):
        prefs = get_prefs()
        if prefs and getattr(prefs, "confirm_transform_apply", True) and self.dont_show_again:
            prefs.confirm_transform_apply = False

        # Rebuild a minimal event-like object from the stored click, so OK immediately enters the tool.
        evt = None
        if self._ptools_confirm_xy is not None:
            mx, my = self._ptools_confirm_xy
            class _Evt: pass
            evt = _Evt()
            evt.mouse_region_x = mx
            evt.mouse_region_y = my
        return self._start(context, evt)

    def _start(self, context, event):
        obj = context.object
        context.view_layer.objects.active = obj

        _apply_transforms_safe(context, obj)
        warn_transform_apply(context, self)

        self._obj_ref = obj
        self._wire_begin(context, obj)

        self._handle = bpy.types.SpaceView3D.draw_handler_add(self._draw, (self,), 'WINDOW', 'POST_VIEW')
        context.window_manager.modal_handler_add(self)
        if event is not None:
            self._raycast(context, event)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'MIDDLEMOUSE','WHEELUPMOUSE','WHEELDOWNMOUSE','MOUSEPAN','NDOF_MOTION'}:
            return {'PASS_THROUGH'}
        if event.type == 'MOUSEMOVE':
            self._raycast(context, event)
            for a in context.screen.areas:
                if a.type=='VIEW_3D': a.tag_redraw()
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if self.hit_world: self._snap_and_apply(context)
            self.finish(); return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE','ESC'}:
            self.finish(); return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def finish(self):
        if self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle,'WINDOW')
        self._wire_end()
        self._handle = None

    def _wire_begin(self, context, obj):
        self._overlay_states = []
        scr = context.screen
        if scr:
            for area in scr.areas:
                if area.type == 'VIEW_3D':
                    sp = area.spaces.active
                    if hasattr(sp, "overlay") and hasattr(sp.overlay, "show_wireframes"):
                        self._overlay_states.append((sp.overlay, sp.overlay.show_wireframes))
                        sp.overlay.show_wireframes = True
                    area.tag_redraw()

        prev = getattr(obj, "show_wire", None)
        if isinstance(prev, bool):
            self._obj_wire_prev = prev
            try:
                obj.show_wire = True
            except:
                self._obj_wire_prev = None  # fail quietly

    def _wire_end(self):
        if self._overlay_states:
            for overlay, old in self._overlay_states:
                try:
                    overlay.show_wireframes = old
                except:
                    pass
        self._overlay_states = None

        obj = self._obj_ref
        if obj is not None and self._obj_wire_prev is not None:
            try:
                obj.show_wire = self._obj_wire_prev
            except:
                pass
        self._obj_wire_prev = None

    def _raycast(self, context, event):
        region, rv3d = context.region, context.region_data
        if not (region and rv3d): self.hit_world=None; return
        coord = (event.mouse_region_x, event.mouse_region_y)
        origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        obj = context.object
        dg = context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(dg)
        eval_mesh = eval_obj.to_mesh()
        hit, loc, _norm, fi = eval_obj.ray_cast(origin, direction)
        if not (hit and fi >= 0):
            self.hit_world = None
            eval_obj.to_mesh_clear()
            return
        try:
            poly = eval_mesh.polygons[fi]
            best_vert = None; best_vert_dist = 1e9
            for v in poly.vertices:
                w = obj.matrix_world @ eval_mesh.vertices[v].co
                d = (w - loc).length
                if d < best_vert_dist:
                    best_vert_dist = d; best_vert = eval_mesh.vertices[v].co.copy()
            best_edge = None; best_edge_dist = 1e9
            for i in range(len(poly.vertices)):
                v1 = poly.vertices[i]; v2 = poly.vertices[(i+1)%len(poly.vertices)]
                mid = (eval_mesh.vertices[v1].co + eval_mesh.vertices[v2].co) * 0.5
                w = obj.matrix_world @ mid
                d = (w - loc).length
                if d < best_edge_dist:
                    best_edge_dist = d; best_edge = mid.copy()
            center = mathutils.Vector()
            for v in poly.vertices: center += eval_mesh.vertices[v].co
            center /= len(poly.vertices)
            center_w = obj.matrix_world @ center
            center_dist = (center_w - loc).length
            m = min(best_vert_dist, best_edge_dist, center_dist)
            self.best_local = best_vert if m==best_vert_dist else (best_edge if m==best_edge_dist else center)
            self.hit_world = obj.matrix_world @ self.best_local
        finally:
            eval_obj.to_mesh_clear()

    def _snap_and_apply(self, context):
        obj = context.object; local = self.best_local
        if obj is None or local is None: return
        obj.data.transform(Matrix.Translation(-local))
        obj.location = obj.matrix_world @ local

    def _draw(self, _context=None):
        prefs = get_prefs()
        if prefs is None:
            return
        if not self.hit_world:
            return
        if prefs.adaptive_preview:
            obj = self._obj_ref
            px_target = _smart_preview_px(bpy.context, obj, prefs)
            radius = max(1e-5, _pixels_to_world_radius_at(bpy.context, self.hit_world, px_target))
        else:
            radius = max(1e-5, prefs.circle_radius)

        rv3d = bpy.context.region_data
        axis = (rv3d.view_rotation @ Vector((0.0, 0.0, -1.0))).normalized() if rv3d else Vector((0,0,1))
        up = Vector((0,1,0))
        ortho1 = axis.cross(up)
        if ortho1.length == 0: ortho1 = axis.cross(Vector((1,0,0)))
        ortho1.normalize(); ortho2 = axis.cross(ortho1).normalized()
        center = self.hit_world
        segments = 48
        verts = [center] + [center + radius*(math.cos(2*math.pi*i/segments)*ortho1 + math.sin(2*math.pi*i/segments)*ortho2) for i in range(segments+1)]

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        gpu.state.depth_test_set('NONE')
        shader.bind(); shader.uniform_float('color', tuple(prefs.hover_color))
        batch_for_shader(shader, 'TRI_FAN', {'pos': verts}).draw(shader)
        gpu.state.depth_test_set('LESS_EQUAL')

class OBJECT_OT_bbox_click_pivot(bpy.types.Operator):
    """Show 27 grid points; click to place origin (combined bounds if 'Apply to All Selected')."""
    bl_idname = "object.bbox_click_pivot"
    bl_label = "BBox Click Targets"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Interactive: click one of 27 grid points to place origin (applies transforms first; uses combined selection bounds if Apply All)"

    dont_show_again: bpy.props.BoolProperty(
        name="Don't show again",
        default=False,
        description="Disable the confirmation dialog in the add-on preferences"
    )

    _handle = None
    _points_world = []   # [Vector]
    _obj_refs = []       # objects to affect
    _hover_idx = None

    _hit_radius_px = 12
    _half_size_px = 10
    _hover_scale = 1.35

    def draw(self, context):
        layout = self.layout
        layout.label(text=PTTOOLS_CONFIRM_MESSAGE, icon='INFO')
        layout.prop(self, "dont_show_again")

    def invoke(self, context, event):
        prefs = get_prefs()
        if prefs and getattr(prefs, "confirm_transform_apply", True):
            self.dont_show_again = False
            return context.window_manager.invoke_props_dialog(self, width=420)
        return self._start(context)

    def execute(self, context):
        prefs = get_prefs()
        if prefs and getattr(prefs, "confirm_transform_apply", True) and self.dont_show_again:
            prefs.confirm_transform_apply = False
        return self._start(context)

    def _start(self, context):
        warn_transform_apply(context, self)
        objs = [o for o in context.selected_objects if o.type == 'MESH'] if getattr(context.scene, "ptools_apply_all", False) else ([context.object] if (context.object and context.object.type=='MESH') else [])
        if not objs:
            self.report({'WARNING'}, "No mesh objects selected/active")
            return {'CANCELLED'}

        self._obj_refs = objs
        self._build_points(context, objs)

        if self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self._handle = None

        self._handle = bpy.types.SpaceView3D.draw_handler_add(self._draw_post_view, (self,), 'WINDOW', 'POST_VIEW')
        context.window_manager.modal_handler_add(self)

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'MIDDLEMOUSE','WHEELUPMOUSE','WHEELDOWNMOUSE','MOUSEPAN','NDOF_MOTION'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            self._hover_idx = self._hit_test(context, event)
            for a in context.screen.areas:
                if a.type == 'VIEW_3D':
                    a.tag_redraw()
            return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            idx = self._hit_test(context, event)
            if idx is not None:
                world_point = self._points_world[idx]
                self._apply_pivot_to_targets(context, world_point)
                self.finish()
                return {'FINISHED'}
            return {'RUNNING_MODAL'}

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.finish()
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self):
        if self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        self._handle = None

    def _build_points(self, context, objs):
        def _bbox_local(obj):
            xs, ys, zs = _bbox_min_mid_max_local(obj)
            mw = obj.matrix_world
            for z in zs:
                for y in ys:
                    for x in xs:
                        yield mw @ Vector((x, y, z))

        self._points_world.clear()
        apply_all = getattr(context.scene, "ptools_apply_all", False)
        if apply_all and len(objs) > 1:
            axes = _combined_bbox_min_mid_max_world(objs)
            if axes is None: return
            xs, ys, zs = axes
            for z in zs:
                for y in ys:
                    for x in xs:
                        self._points_world.append(Vector((x, y, z)))
        else:
            self._points_world.extend(_bbox_local(objs[0]))

    def _hit_test(self, context, event):
        region, rv3d = context.region, context.region_data
        if not (region and rv3d): return None
        mx, my = event.mouse_region_x, event.mouse_region_y
        best_i, best_d = None, 1e9
        for i, wpos in enumerate(self._points_world):
            p2d = view3d_utils.location_3d_to_region_2d(region, rv3d, wpos)
            if p2d is None: continue
            d = (p2d - Vector((mx, my))).length
            if d < self._hit_radius_px and d < best_d:
                best_d = d; best_i = i
        return best_i

    def _apply_pivot_to_targets(self, context, world_point: Vector):
        for obj in self._obj_refs:
            bpy.context.view_layer.objects.active = obj
            _apply_transforms_safe(context, obj)
            inv = obj.matrix_world.inverted()
            local_pt = inv @ world_point
            obj.data.transform(Matrix.Translation(-local_pt))
            obj.location = world_point

    def _draw_post_view(self, _context=None):
        prefs = get_prefs()
        if prefs is None:
            return
        color = tuple(prefs.hover_color)

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('LESS_EQUAL')

        base_col = (color[0], color[1], color[2], max(0.25, color[3]*0.85))
        hover_col = (min(1.0, color[0]*1.05), min(1.0, color[1]*1.05), min(1.0, color[2]*1.05), 1.0)

        tris = []
        tris_hover = []
        for i, wpos in enumerate(self._points_world):
            half = max(1e-5, _pixels_to_world_radius_at(bpy.context, wpos, self._half_size_px))
            if self._hover_idx == i:
                half *= self._hover_scale
                dest = tris_hover
            else:
                dest = tris
            hx = hy = hz = half
            x0, x1 = wpos.x - hx, wpos.x + hx
            y0, y1 = wpos.y - hy, wpos.y + hy
            z0, z1 = wpos.z - hz, wpos.z + hz
            v000 = Vector((x0, y0, z0)); v001 = Vector((x0, y0, z1))
            v010 = Vector((x0, y1, z0)); v011 = Vector((x0, y1, z1))
            v100 = Vector((x1, y0, z0)); v101 = Vector((x1, y0, z1))
            v110 = Vector((x1, y1, z0)); v111 = Vector((x1, y1, z1))
            dest.extend([
                v110, v101, v111,   v110, v100, v101,
                v010, v001, v000,   v010, v011, v001,
                v010, v111, v011,   v010, v110, v111,
                v000, v101, v100,   v000, v001, v101,
                v011, v111, v101,   v011, v101, v001,
                v000, v110, v010,   v000, v100, v110,
            ])

        if tris:
            batch = batch_for_shader(shader, 'TRIS', {"pos": tris})
            shader.bind(); shader.uniform_float('color', base_col); batch.draw(shader)
        if tris_hover:
            batch_h = batch_for_shader(shader, 'TRIS', {"pos": tris_hover})
            shader.bind(); shader.uniform_float('color', hover_col); batch_h.draw(shader)

        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')

class PToolsSavedPivot(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="Pivot")
    location: bpy.props.FloatVectorProperty(name="World Location", subtype='XYZ', size=3, default=(0.0,0.0,0.0))

class PTOOLS_UL_saved_pivots(bpy.types.UIList):
    bl_idname = "PTOOLS_UL_saved_pivots"
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        sp = item
        row = layout.row(align=True)
        row.prop(sp, "name", text="", emboss=False, icon='EMPTY_ARROWS')
        coords = f"({sp.location[0]:.2f}, {sp.location[1]:.2f}, {sp.location[2]:.2f})"
        row.label(text=coords)
class OBJECT_OT_pivot_add_saved(bpy.types.Operator):
    bl_idname = "object.ptools_add_saved_pivot"
    bl_label = "Add Slot"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Create (+) a new empty pivot slot; then use Save Pivot"
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.object is not None and context.object.type == 'MESH'
    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            return False
        if getattr(context.scene, "ptools_apply_all", False):
            return any(o.type == 'MESH' for o in context.selected_objects)
        return context.object is not None and context.object.type == 'MESH'



    def execute(self, context):
        col = context.scene.ptools_saved_pivots
        item = col.add()
        item.location = (0.0, 0.0, 0.0)
        item.name = f"Pivot {len(col)}"
        context.scene.ptools_saved_index = len(col)-1
        return {'FINISHED'}

class OBJECT_OT_pivot_remove_saved(bpy.types.Operator):
    bl_idname = "object.ptools_remove_saved_pivot"
    bl_label = "Remove Slot"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Delete (−) the selected pivot slot"

    @classmethod
    def poll(cls, context):
        col = getattr(context.scene, "ptools_saved_pivots", None)
        idx = getattr(context.scene, "ptools_saved_index", -1)
        return context.mode == 'OBJECT' and bool(col) and 0 <= idx < len(col)

    def execute(self, context):
        col = context.scene.ptools_saved_pivots
        idx = context.scene.ptools_saved_index
        col.remove(idx)
        context.scene.ptools_saved_index = min(max(0, idx-1), len(col)-1)
        return {'FINISHED'}

class OBJECT_OT_pivot_save_to_slot(bpy.types.Operator):
    bl_idname = "object.ptools_save_pivot_to_slot"
    bl_label = "Save Pivot"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Save current origin (world space) to selected slot"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.object is not None and context.scene.ptools_saved_pivots and 0 <= context.scene.ptools_saved_index < len(context.scene.ptools_saved_pivots)

    def execute(self, context):
        obj = context.object
        if not obj:
            self.report({'WARNING'}, "No active object")
            return {'CANCELLED'}
        col = context.scene.ptools_saved_pivots
        idx = context.scene.ptools_saved_index
        slot = col[idx]
        slot.location = (obj.matrix_world @ Vector((0,0,0)))
        self.report({'INFO'}, f"Saved pivot to '{slot.name}'")
        return {'FINISHED'}

class OBJECT_OT_pivot_load_from_slot(bpy.types.Operator):
    bl_idname = "object.ptools_load_pivot_from_slot"
    bl_label = "Load Pivot"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Apply selected saved pivot to target objects"

    @classmethod
    def poll(cls, context):
        col = getattr(context.scene, "ptools_saved_pivots", None)
        idx = getattr(context.scene, "ptools_saved_index", -1)
        return context.mode == 'OBJECT' and bool(col) and 0 <= idx < len(col)

    def execute(self, context):
        col = context.scene.ptools_saved_pivots
        idx = context.scene.ptools_saved_index
        world_point = Vector(col[idx].location)

        objs = gather_targets(context)
        if not objs:
            self.report({'WARNING'}, "No mesh targets")
            return {'CANCELLED'}

        for obj in objs:
            bpy.context.view_layer.objects.active = obj
            _apply_transforms_safe(context, obj)
            inv = obj.matrix_world.inverted()
            local_pt = inv @ world_point
            obj.data.transform(Matrix.Translation(-local_pt))
            obj.location = world_point

        self.report({'INFO'}, f"Loaded pivot to {len(objs)} object(s)")
        return {'FINISHED'}

class VIEW3D_PT_pivot_tools_multi(bpy.types.Panel):
    bl_label = "Pivot Tools"
    bl_idname = "VIEW3D_PT_pivot_tools_multi"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Pivot Tools"

    def draw(self, context):
        layout = self.layout
        if context.mode != 'OBJECT':
            box = layout.box()
            box.label(text="Object Mode required", icon='INFO')
            return
        layout.prop(context.scene, "ptools_apply_all", text="Apply to All Selected")
        layout.separator()

        layout.label(text="Common")
        row = layout.row(align=True)
        row.operator('object.pivot_to_bottom_center', text='Bottom Center', icon='TRIA_DOWN_BAR')

        layout.separator()
        layout.label(text="Interactive")
        row = layout.row(align=True)
        row.operator('object.pick_geom_pivot_auto', text="Auto Pick", icon='RESTRICT_SELECT_OFF')
        row.operator('object.bbox_click_pivot', text="BBox Click Targets", icon='SNAP_FACE')

        layout.separator()

        header = layout.row(align=True)
        icon = 'TRIA_DOWN' if context.scene.ptools_show_saved else 'TRIA_RIGHT'
        header.prop(context.scene, "ptools_show_saved", text="", icon=icon, emboss=False)
        header.label(text="Saved Pivots")

        if context.scene.ptools_show_saved:
            row = layout.row()
            split = row.split(factor=0.8)
            col_list = split.column()
            col_buttons = split.column(align=True)

            col_list.template_list(
                "PTOOLS_UL_saved_pivots",
                "",
                context.scene, "ptools_saved_pivots",
                context.scene, "ptools_saved_index",
                rows=3
            )

            col_buttons.operator("object.ptools_add_saved_pivot", text="", icon='ADD')
            col_buttons.operator("object.ptools_remove_saved_pivot", text="", icon='REMOVE')

            row2 = layout.row(align=True)
            row2.operator("object.ptools_save_pivot_to_slot", text="Save Pivot", icon='EXPORT')
            row2.operator("object.ptools_load_pivot_from_slot", text="Load Pivot", icon='IMPORT')

classes = (
    PivotToolsPreferences,  OBJECT_OT_pivot_to_bottom_center,
    OBJECT_OT_pick_geom_pivot_auto,
    OBJECT_OT_bbox_click_pivot,
    PToolsSavedPivot,
    PTOOLS_UL_saved_pivots,
    OBJECT_OT_pivot_add_saved,
    OBJECT_OT_pivot_remove_saved,
    OBJECT_OT_pivot_save_to_slot,
    OBJECT_OT_pivot_load_from_slot,
    VIEW3D_PT_pivot_tools_multi,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ptools_apply_all = bpy.props.BoolProperty(
        name="Apply to All Selected", default=True,
        description="Apply operations to all selected meshes"
    )
    bpy.types.Scene.ptools_saved_pivots = bpy.props.CollectionProperty(type=PToolsSavedPivot)
    bpy.types.Scene.ptools_saved_index = bpy.props.IntProperty(default=-1)
    bpy.types.Scene.ptools_show_saved = bpy.props.BoolProperty(
        name="Show Saved Pivots", default=True,
        description="Toggle the Saved Pivots section"
    )

def unregister():
    del bpy.types.Scene.ptools_show_saved
    del bpy.types.Scene.ptools_saved_index
    del bpy.types.Scene.ptools_saved_pivots
    del bpy.types.Scene.ptools_apply_all
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == '__main__':
    register()