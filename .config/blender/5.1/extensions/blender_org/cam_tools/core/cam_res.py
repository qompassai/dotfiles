

import bpy
from bpy.app.handlers import persistent
from bpy.types import PropertyGroup, Panel, Operator
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    PointerProperty,
)


_camres_is_updating = False


# ------------------------------------------------------------------------
# Presets
# ------------------------------------------------------------------------
FIXED_PRESETS = [
    ("1280x720", "1280 × 720", "Fixed resolution"),
    ("1920x1080", "1920 × 1080", "Fixed resolution"),
    ("2560x1440", "2560 × 1440", "Fixed resolution"),
    ("3840x2160", "3840 × 2160", "Fixed resolution"),
    ("4096x2160", "4096 × 2160", "Fixed resolution"),
]

RATIO_PRESETS = [
    ("RATIO_1_1", "1:1", "Square — Instagram, profile pics"),
    ("RATIO_4_3", "4:3", "Old TV, still photography, Micro 4/3 cameras"),
    ("RATIO_16_9", "16:9", "Widescreen HD, UHD, most video production"),
    ("RATIO_21_9", "21:9", "CinemaScope / Ultrawide monitors"),
    ("RATIO_2_39_1", "2.39:1", "Modern cinema widescreen"),
    ("RATIO_3_2", "3:2", "35mm photography, DSLR standard"),
    ("RATIO_5_4", "5:4", "Medium format still photography"),
]

PRESET_ITEMS = [("CUSTOM", "Custom", "Enter values manually")] + FIXED_PRESETS + RATIO_PRESETS

RATIO_MAP = {
    "RATIO_1_1": (1, 1),
    "RATIO_4_3": (4, 3),
    "RATIO_16_9": (16, 9),
    "RATIO_21_9": (21, 9),
    "RATIO_2_39_1": (239, 100),
    "RATIO_3_2": (3, 2),
    "RATIO_5_4": (5, 4),
}


def parse_fixed_preset(key):
    try:
        parts = key.split("x")
        return int(parts[0]), int(parts[1])
    except Exception:
        return None


def compute_from_ratio(base_long_side, ratio_num, ratio_den, orientation):
    if orientation == "LANDSCAPE":
        width = base_long_side
        height = max(1, int(round(base_long_side * (ratio_den / ratio_num))))
    else:
        height = base_long_side
        width = max(1, int(round(base_long_side * (ratio_den / ratio_num))))
    return width, height


# ------------------------------------------------------------------------
# Core helpers 
# ------------------------------------------------------------------------
def copy_xy_aspect(src, dst):
    dst.resolution_x = src.resolution_x
    dst.resolution_y = src.resolution_y
    dst.pixel_aspect_x = src.pixel_aspect_x
    dst.pixel_aspect_y = src.pixel_aspect_y


# ------------------------------------------------------------------------
# PropertyGroups
# ------------------------------------------------------------------------
class CamResResolutionProps(PropertyGroup):
    use_custom_resolution: BoolProperty(
        name="Use Cam-Res",
        description="Use custom resolution for this camera",
        default=False,
    )

    resolution_x: IntProperty(
        name="Resolution X",
        default=1920,
        min=1,
        subtype="PIXEL",
        update=lambda self, ctx: camera_res_manual_update(self, ctx),
    )
    resolution_y: IntProperty(
        name="Resolution Y",
        default=1080,
        min=1,
        subtype="PIXEL",
        update=lambda self, ctx: camera_res_manual_update(self, ctx),
    )
    resolution_percentage: IntProperty(
        name="Scale (%)",
        description="Per-camera render scale (only if custom scale enabled)",
        default=100,
        min=1,
        max=1000,
        subtype="PERCENTAGE",
    )
    pixel_aspect_x: FloatProperty(
        name="Pixel Aspect X",
        default=1.0,
        min=1.0,
        max=200.0,
    )
    pixel_aspect_y: FloatProperty(
        name="Pixel Aspect Y",
        default=1.0,
        min=1.0,
        max=200.0,
    )

    preset: EnumProperty(
        name="Preset",
        items=PRESET_ITEMS,
        default="CUSTOM",
        update=lambda self, ctx: camera_preset_update(self, ctx),
    )
    orientation: EnumProperty(
        name="Orientation",
        items=[("LANDSCAPE", "Landscape", ""), ("PORTRAIT", "Portrait", "")],
        default="LANDSCAPE",
        update=lambda self, ctx: camera_orientation_update(self, ctx),
    )
    use_custom_scale: BoolProperty(
        name="Use Custom Scale",
        description="Override global scene scale for this camera",
        default=False,
    )

    # Internal guard to avoid marking as CUSTOM when presets update res X/Y
    internal_updating: BoolProperty(
        name="Internal Updating",
        default=False,
        options={'HIDDEN'},
    )


class CamResSceneProps(PropertyGroup):
    original_resolution: PointerProperty(type=CamResResolutionProps)

    enable_overrides: BoolProperty(
        name="Enable Overrides",
        default=True,
        description="Apply per-camera resolution to the scene render settings",
    )

    global_scale_backup: IntProperty(default=100)
    last_was_custom: BoolProperty(default=False)
    last_was_custom_scale: BoolProperty(default=False)

    # Collapse toggle for the Cam-Res section
    show_camres_section: BoolProperty(
        name="Show Cam-Res Section",
        description="Show or hide the Camera Resolution section",
        default=False, # start collapsed
    )

    show_advanced: BoolProperty(
        name="Advanced Properties",
        description="Show advanced Cam-Res options",
        default=False,
    )


# ------------------------------------------------------------------------
# Update callbacks
# ------------------------------------------------------------------------
def camera_preset_update(self, context):
    if self.internal_updating:
        return

    preset = self.preset
    orientation = self.orientation

    if preset == "CUSTOM":
        return

    fixed = parse_fixed_preset(preset)
    if fixed:
        x, y = fixed
    elif preset in RATIO_MAP:
        num, den = RATIO_MAP[preset]
        current_x = int(self.resolution_x)
        current_y = int(self.resolution_y)
        long_side = max(current_x, current_y, 1920)
        x, y = compute_from_ratio(long_side, num, den, orientation)
    else:
        return

    self.internal_updating = True
    try:
        self.resolution_x = int(x)
        self.resolution_y = int(y)
    finally:
        self.internal_updating = False


def camera_orientation_update(self, context):
    if self.internal_updating:
        return

    preset = self.preset
    orientation = self.orientation

    if preset in RATIO_MAP:
        num, den = RATIO_MAP[preset]
        current_x = int(self.resolution_x)
        current_y = int(self.resolution_y)
        long_side = max(current_x, current_y)
        x, y = compute_from_ratio(long_side, num, den, orientation)
        self.internal_updating = True
        try:
            self.resolution_x = int(x)
            self.resolution_y = int(y)
        finally:
            self.internal_updating = False
    else:
        rx = int(self.resolution_x)
        ry = int(self.resolution_y)
        if orientation == "PORTRAIT" and rx > ry:
            self.internal_updating = True
            try:
                self.resolution_x, self.resolution_y = ry, rx
            finally:
                self.internal_updating = False
        elif orientation == "LANDSCAPE" and rx < ry:
            self.internal_updating = True
            try:
                self.resolution_x, self.resolution_y = ry, rx
            finally:
                self.internal_updating = False


def camera_res_manual_update(self, context):
    if self.internal_updating:
        return
    self.preset = "CUSTOM"


# ------------------------------------------------------------------------
# Handler
# ------------------------------------------------------------------------
@persistent
def camres_update_handler(scene_or_depsgraph, depsgraph=None):
    """Apply per-camera resolution overrides to scene.render.

    Works for both:
      - depsgraph_update_pre(depsgraph)
      - frame_change_pre(scene)
    """
    global _camres_is_updating

    # Avoid recursive re-entry 
    if _camres_is_updating:
        return

    # Figure out the actual scene depending on which handler called us
    # - frame_change_pre: scene_or_depsgraph is a Scene
    # - depsgraph_update_pre: scene_or_depsgraph is a Depsgraph
    if hasattr(scene_or_depsgraph, "render") and hasattr(scene_or_depsgraph, "camres_settings"):
        scene = scene_or_depsgraph  # called from frame_change_pre(scene)
    elif hasattr(scene_or_depsgraph, "scene_eval"):
        scene = scene_or_depsgraph.scene_eval  # called from depsgraph_update_pre(depsgraph)
    else:
        return

    if not hasattr(scene, "camres_settings"):
        return

    settings = scene.camres_settings
    render = scene.render

    cam_obj = scene.camera if scene.camera and scene.camera.type == 'CAMERA' else None
    cam_props = cam_obj.data.camres if cam_obj else None

    prev_custom = settings.last_was_custom
    prev_custom_scale = settings.last_was_custom_scale

    if settings.enable_overrides and cam_props and cam_props.use_custom_resolution:
        curr_custom = True
        curr_custom_scale = bool(cam_props.use_custom_scale)
    else:
        curr_custom = False
        curr_custom_scale = False

    _camres_is_updating = True
    try:
        # --- Resolution backup/restore (X/Y + aspect) ---
        if curr_custom and not prev_custom:
            copy_xy_aspect(render, settings.original_resolution)

        if curr_custom:
            copy_xy_aspect(cam_props, render)
        elif prev_custom and not curr_custom:
            copy_xy_aspect(settings.original_resolution, render)

        # --- Scale backup/restore (resolution_percentage) ---
        if curr_custom_scale and not prev_custom_scale:
            settings.global_scale_backup = render.resolution_percentage

        if curr_custom_scale:
            render.resolution_percentage = cam_props.resolution_percentage
        elif prev_custom_scale and not curr_custom_scale:
            render.resolution_percentage = settings.global_scale_backup

        settings.last_was_custom = curr_custom
        settings.last_was_custom_scale = curr_custom_scale

    finally:
        _camres_is_updating = False



# ------------------------------------------------------------------------
# Operators
# ------------------------------------------------------------------------
class CR_OT_ClearCameraOverride(Operator):
    bl_idname = "cr.clear_camera_override"
    bl_label = "Disable Cam-Res (Selected)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            if obj.type == 'CAMERA':
                cam = obj.data.camres
                cam.use_custom_resolution = False
                cam.use_custom_scale = False
                count += 1
        self.report({'INFO'}, f"Disabled Cam-Res on {count} camera(s)")
        return {'FINISHED'}


class CR_OT_ClearAllOverrides(Operator):
    bl_idname = "cr.clear_all_overrides"
    bl_label = "Disable Cam-Res (All Cameras)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for cam in bpy.data.cameras:
            props = cam.camres
            props.use_custom_resolution = False
            props.use_custom_scale = False
            count += 1
        self.report({'INFO'}, f"Disabled Cam-Res on {count} camera(s)")
        return {'FINISHED'}


# ------------------------------------------------------------------------
# PANEL HELPER
# ------------------------------------------------------------------------


def draw_camres(layout, context):
    """Shared UI for Cam-Res, reusable from any panel."""
    scene = context.scene
    settings = scene.camres_settings
    cam_obj = (
        context.object
        if context.object and context.object.type == 'CAMERA'
        else scene.camera
    )

    # Outer box + header with collapse toggle
    outer = layout.box()
    header = outer.row(align=True)
    icon = 'TRIA_DOWN' if settings.show_camres_section else 'TRIA_RIGHT'
    header.prop(
        settings,
        "show_camres_section",
        text="",
        icon=icon,
        emboss=False,
    )
    header.label(text="Resolution Per Camera")

    # Early exit when collapsed
    if not settings.show_camres_section:
        return

    # Inner column for existing contents
    col = outer.column()
    col.label(
        text=f"Scene Resolution: {scene.render.resolution_x} × {scene.render.resolution_y}"
    )

    if cam_obj and cam_obj.type == 'CAMERA':
        cam_props = cam_obj.data.camres

        col.prop(cam_props, "use_custom_resolution", text="Use Cam-Res")
        col.separator()

        box = col.box()
        box.enabled = cam_props.use_custom_resolution

        # Res X / Res Y
        split = box.split(factor=0.5, align=True)
        split.scale_y = 1.2
        split.prop(cam_props, "resolution_x", text="Res X")
        split.prop(cam_props, "resolution_y", text="Res Y")

        # Preset row 
        row = box.row(align=True)
        row.scale_y = 1.2
        row.prop(cam_props, "preset", text="Preset")

        # Orientation
        row = box.row(align=True)
        row.scale_y = 1.2
        row.label(text="Orientation")
        sub = row.row(align=True)
        sub.scale_x = 1.2
        sub.prop(cam_props, "orientation", text="")

        # Custom Scale
        row = box.row(align=True)
        row.prop(cam_props, "use_custom_scale", text="Custom Scale")
        sub = row.row(align=True)
        sub.enabled = cam_props.use_custom_scale and cam_props.use_custom_resolution
        sub.prop(cam_props, "resolution_percentage", text="", slider=True)

    else:
        col.separator()
        col.label(text="Select a camera to edit Cam-Res", icon="INFO")

    col.separator()
    adv = col.box()
    row = adv.row()
    row.prop(
        settings,
        "show_advanced",
        icon="PREFERENCES",
        text="Advanced Properties",
        emboss=True,
    )

    if settings.show_advanced:
        sub = adv.column(align=True)
        sub.prop(settings, "enable_overrides", text="Enable Overrides")
        sub.operator("cr.clear_camera_override", icon="TRASH")
        sub.operator("cr.clear_all_overrides", icon="X")



class CR_PT_Panel(Panel):
    bl_label = "Cam-Res"
    bl_idname = "CR_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Cam-Res"

    def draw(self, context):
        draw_camres(self.layout, context)





# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------
classes = (
    CamResResolutionProps,
    CamResSceneProps,
    CR_OT_ClearCameraOverride,
    CR_OT_ClearAllOverrides,
    # CR_PT_Panel, # now drawn via combined panel in ui.py
)


def register_camres():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Camera.camres = PointerProperty(type=CamResResolutionProps)
    bpy.types.Scene.camres_settings = PointerProperty(type=CamResSceneProps)

    if camres_update_handler not in bpy.app.handlers.depsgraph_update_pre:
        bpy.app.handlers.depsgraph_update_pre.append(camres_update_handler)
    if camres_update_handler not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(camres_update_handler)


def unregister_camres():
    for hlist in (bpy.app.handlers.depsgraph_update_pre, bpy.app.handlers.frame_change_pre):
        hlist[:] = [h for h in hlist if h is not camres_update_handler]

    if hasattr(bpy.types.Scene, "camres_settings"):
        del bpy.types.Scene.camres_settings
    if hasattr(bpy.types.Camera, "camres"):
        del bpy.types.Camera.camres

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


