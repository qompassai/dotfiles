import bpy
import math
from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    StringProperty,
    EnumProperty,
    CollectionProperty,
)
from .utils import cr_refresh_overlay, get_border_range, cr_get_effective_resolution


class CR_SavedBorderItem(PropertyGroup):
    name: StringProperty(name="Name", default="Unnamed Region")
    min_x: FloatProperty()
    max_x: FloatProperty()
    min_y: FloatProperty()
    max_y: FloatProperty()


class ChunkRenderSettings(PropertyGroup):

    def _cr_divisors(self, n: int):
        if n <= 1:
            return [1]
        divs = set()
        for i in range(1, int(math.isqrt(n)) + 1):
            if n % i == 0:
                divs.add(i)
                divs.add(n // i)
        return sorted(divs)

    def _compute_valid_grids(self, resx: int, resy: int):
        dx = self._cr_divisors(int(resx))
        dy = self._cr_divisors(int(resy))
        candidates = []
        for cols in dx:
            for rows in dy:
                candidates.append(((cols, rows), cols * rows, abs(cols - rows), abs(resx / cols - resy / rows)))
        candidates.sort(key=lambda x: (x[1], x[2], x[3]))
        return [c[0] for c in candidates]

    def _get_scene_for_update(self, context=None):
        scene = getattr(context, "scene", None) if context is not None else None
        if scene is None:
            scene = getattr(self, "id_data", None)
        return scene

    def sync_level_grid(self, context=None):
        if getattr(self, 'CR_split_mode', 'LEVELS') != 'LEVELS':
            return
        scene = self._get_scene_for_update(context)
        if scene is None:
            return
        rnd = getattr(scene, "render", None)
        if rnd is None:
            return
        grids = self._compute_valid_grids(rnd.resolution_x, rnd.resolution_y)
        if not grids:
            return
        lvl = max(1, min(int(self.CR_level), len(grids)))
        cols, rows = grids[lvl - 1]
        if int(self.CR_reg_columns) != cols or int(self.CR_reg_rows) != rows:
            self.CR_reg_columns, self.CR_reg_rows = cols, rows

    def level_update(self, context):
        if getattr(self, "_cr_level_applying", False):
            return
        setattr(self, "_cr_level_applying", True)
        try:
            self.sync_level_grid(context)
        finally:
            setattr(self, "_cr_level_applying", False)

    def bleed_update(self, context):
        if getattr(self, "_cr_bleeding", False):
            return
        scene = self._get_scene_for_update(context)
        if scene is None:
            return
        setattr(self, "_cr_bleeding", True)
        try:
            rnd = scene.render
            perc = rnd.resolution_percentage / 100.0
            bminx, bmaxx, bminy, bmaxy = get_border_range(rnd, self.CR_use_render_border)
            chunk_w = (rnd.resolution_x * perc * (bmaxx - bminx)) / max(1, self.CR_reg_columns)
            chunk_h = (rnd.resolution_y * perc * (bmaxy - bminy)) / max(1, self.CR_reg_rows)
            limit = int(min(chunk_w, chunk_h) * 0.3)
            if self.CR_bleed_pixels > limit:
                self.CR_bleed_pixels = limit
        finally:
            setattr(self, "_cr_bleeding", False)

    def method_update(self, context):
        self.sync_level_grid(context)
        self.bleed_update(context)
        cr_refresh_overlay()

    def checkColsRows(self, context):
        if getattr(self, "_cr_checking", False):
            return
        setattr(self, "_cr_checking", True)
        try:
            rnd = context.scene.render
            resx, resy = cr_get_effective_resolution(rnd, self.CR_use_render_border and rnd.use_border)
            self.CR_cols_pixel_error = (resx % max(1, int(self.CR_reg_columns))) != 0
            self.CR_rows_pixel_error = (resy % max(1, int(self.CR_reg_rows))) != 0
            self.bleed_update(context)
            cr_refresh_overlay()
        finally:
            setattr(self, "_cr_checking", False)

    def cr_border_mode_update(self, context):
        self.bleed_update(context)
        cr_refresh_overlay()

    def overlay_update(self, context):
        self.sync_level_grid(context)
        cr_refresh_overlay()

    CR_cols_pixel_error: BoolProperty(name="Column Pixel Mismatch", default=False)
    CR_rows_pixel_error: BoolProperty(name="Row Pixel Mismatch", default=False)
    CR_split_mode: EnumProperty(
        name="Split Mode",
        description="Choose how the image is split into tiles",
        items=(
            ('LEVELS', "Levels", ""),
            ('MANUAL', "Manual", ""),
        ),
        default='LEVELS',
        update=method_update,
    )
    CR_level: IntProperty(name="Level", description="Pick a preset grid density", default=1, min=1, update=method_update)
    CR_reg_rows: IntProperty(name="Rows", description="Set how many tile rows to render", default=1, min=1, max=64, update=checkColsRows)
    CR_reg_columns: IntProperty(name="Columns", description="Set how many tile columns to render", default=1, min=1, max=64, update=checkColsRows)

    def get_use_render_border(self):
        scn = self.id_data
        if not getattr(scn.render, "use_border", False):
            return False
        return self.get("CR_use_render_border", False)

    def set_use_render_border(self, value):
        self["CR_use_render_border"] = value

    CR_use_render_border: BoolProperty(
        name="Use Render Border",
        description="Split only the current render border area into tiles",
        default=False,
        get=get_use_render_border,
        set=set_use_render_border,
        update=cr_border_mode_update,
    )
    CR_saved_border_min_x: FloatProperty(name="min_x", default=0.0)
    CR_saved_border_max_x: FloatProperty(name="max_x", default=1.0)
    CR_saved_border_min_y: FloatProperty(name="min_y", default=0.0)
    CR_saved_border_max_y: FloatProperty(name="max_y", default=1.0)
    CR_overlay_enabled: BoolProperty(name="Show Overlay Grid", description="Show the tile grid overlay in camera view", default=False, update=overlay_update)
    CR_bleed_pixels: IntProperty(name="Bleed Pixels", description="Extend each tile by extra pixels to reduce edge issues", default=0, min=0, max=512, update=bleed_update)

    CR_select_mode: EnumProperty(
        name="Selection Mode",
        description="Choose whether to render all tiles or only specific indices",
        items=(
            ('ALL', "All", ""),
            ('CUSTOM', "Custom", ""),
        ),
        default='ALL',
        update=lambda self, ctx: cr_refresh_overlay(),
    )
    CR_custom_indices: StringProperty(name="Custom Indices", description="Enter tile indices such as 0, 2, 5", default="")
    CR_save_region: BoolProperty(name="Auto Merge Tiles", description="Automatically merge finished tiles into the final image", default=False)
    CR_delete_after_merge: BoolProperty(name="Delete Tiles After Merge", description="Delete tile files after a successful merge", default=False)
    CR_remerge_folder: StringProperty(name="Tiles Folder", description="Select the folder that contains existing tile files", default="", subtype='DIR_PATH')

    CR_msg1: StringProperty(name="Status Message", default="")
    CR_showAdvanced: BoolProperty(name="Show Advanced Settings", description="Show saved borders and re-merge tools", default=False)
    CR_saved_borders: CollectionProperty(type=CR_SavedBorderItem, name="Saved Borders")
    CR_saved_borders_index: IntProperty(name="Selected Border", default=0)
    CR_oldoutputfilepath: StringProperty(name="Previous Output Path", default="")
    CR_oldPerc: IntProperty(name="Previous Resolution Percentage", default=100)
    CR_old_use_border: BoolProperty(name="Previous Border Enabled", default=False)
    CR_old_use_crop: BoolProperty(name="Previous Crop Enabled", default=False)
    CR_old_border_min_x: FloatProperty(name="Previous Border Min X", default=0.0)
    CR_old_border_max_x: FloatProperty(name="Previous Border Max X", default=1.0)
    CR_old_border_min_y: FloatProperty(name="Previous Border Min Y", default=0.0)
    CR_old_border_max_y: FloatProperty(name="Previous Border Max Y", default=1.0)
    CR_oldCompositorDevice: StringProperty(name="Previous Compositor Device", default="")
    CR_renderGo: BoolProperty(name="Render In Progress", default=False)
    CR_cntrnd: IntProperty(name="Render Counter", default=0)
    CR_maxrnd: IntProperty(name="Render Total", default=0)
    CR_done_count: IntProperty(name="Completed Tiles", default=0)
    CR_active_index: IntProperty(name="Active Tile Index", default=-1)
