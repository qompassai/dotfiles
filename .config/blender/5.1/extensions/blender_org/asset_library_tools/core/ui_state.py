import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty
from contextlib import suppress

# ---------- registration for UI state ----------

def register_ui_state():
    # Scene props for Catalogue Backup UI
    bpy.types.Scene.assetcatalogue_show_cleanup = bpy.props.BoolProperty(
        name="Show Cleanup",
        description="Show cleanup options for backup folders",
        default=False,
        options={'SKIP_SAVE'},
    )

    bpy.types.Scene.assetcatalogue_show_ui = bpy.props.BoolProperty(
        name="Show Catalogue Backup",
        description="Show catalogue backup tools panel",
        default=False, # collapsed by default
        options={'SKIP_SAVE'},
    )

def unregister_ui_state():
    # remove Scene props (catalogue UI)
    with suppress(Exception):
        del bpy.types.Scene.assetcatalogue_show_cleanup
    with suppress(Exception):
        del bpy.types.Scene.assetcatalogue_show_ui