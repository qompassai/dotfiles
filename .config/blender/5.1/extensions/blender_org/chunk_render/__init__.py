import bpy
from bpy.props import PointerProperty, BoolProperty
from bpy.types import AddonPreferences
from . import utils, properties, operators, ui
from .translations import translations_dict


class ChunkRenderPreferences(AddonPreferences):
    bl_idname = __package__

    show_render_progress: BoolProperty(
        name="Show Render Progress in 3D View",
        description="When chunk rendering starts, try to show the Render Result in a 3D View and restore the area afterward",
        default=False,
    )
    debug_logging: BoolProperty(
        name="Enable Debug Logging",
        description="Print detailed logs for chunk rendering and multilayer EXR merging",
        default=False,
    )

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(self, "show_render_progress")
        col.prop(self, "debug_logging")


classes = (
    properties.CR_SavedBorderItem,
    properties.ChunkRenderSettings,
    ui.CHUNK_RENDER_UL_saved_borders,
    ui.CHUNK_RENDER_PT_Region,
    operators.ChunkRenderStop,
    operators.ChunkRenderRegions,
    operators.CHUNK_RENDER_OT_cr_remerge_tiles,
    operators.CHUNK_RENDER_OT_cr_align_border,
    operators.CHUNK_RENDER_OT_cr_save_border,
    operators.CHUNK_RENDER_OT_cr_remove_border,
    operators.CHUNK_RENDER_OT_cr_restore_border,
    ChunkRenderPreferences,
)

def register():
    try:
        bpy.app.translations.unregister(__package__)
    except (AttributeError, KeyError, RuntimeError, ValueError):
        pass
    bpy.app.translations.register(__package__, translations_dict)
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.chunk_render_settings = PointerProperty(type=properties.ChunkRenderSettings)
    utils.cr_register_overlay_lifecycle()
    utils.cr_sync_draw_handler()


def unregister():
    utils.cr_unregister_overlay_lifecycle()
    utils.cr_unregister_draw_handler()
    if hasattr(bpy.types.Scene, "chunk_render_settings"):
        del bpy.types.Scene.chunk_render_settings
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            utils.cr_log(f"[Chunk Render] Failed to unregister class {cls.__name__}: {e}")
    try:
        bpy.app.translations.unregister(__package__)
    except (AttributeError, KeyError, RuntimeError, ValueError):
        pass




