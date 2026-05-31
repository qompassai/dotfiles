import bpy
from . import tag_filter, catalogue_backup, utils, ui_state

# Gather classes for registration
classes = (
    # --- Catalogue Backup Classes ---
    catalogue_backup.ASSETCATALOGUE_OT_BackupNow,
    catalogue_backup.ASSETCATALOGUE_OT_BackupActive,
    catalogue_backup.ASSETCATALOGUE_OT_RestoreLast,
    catalogue_backup.ASSETCATALOGUE_OT_ClearBackups,

    # --- Tag Filter Classes (New) ---
    tag_filter.ATF_Props,
    tag_filter.ATF_OT_BuildLibraryIndex,
    tag_filter.ATF_OT_FilterByTagDirect,
    tag_filter.ATF_OT_ClearFilter,
    tag_filter.ATF_OT_PinCurrentTag,
    tag_filter.ATF_OT_UnpinCurrentTag,
    tag_filter.ATF_OT_ClearPinnedTags,
    tag_filter.ATF_OT_BrowseTagsPopup,
    tag_filter.ATFT_OT_SetAssetType,
    tag_filter.ATFT_OT_AllTypes,
)

def register_core():
    # Register all core classes
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Assign properties to Scene
    bpy.types.Scene.atf_props = bpy.props.PointerProperty(type=tag_filter.ATF_Props)

def unregister_core():
    # Remove properties
    if hasattr(bpy.types.Scene, "atf_props"):
        del bpy.types.Scene.atf_props

    # Unregister all core classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass