bl_info = {
    "name": "HiFi Architecture Builder v4.5.8",
    "author": "Malik Nomi",
    "version": (4, 5, 8),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > HiFi Builder",
    "description": "Massive Prop Expansion, Draggable UI, 3-Step AAA Sollumz Pipeline",
    "category": "Mesh Generator",
}

import bpy, math
from .utils import APPLY_LOCK, PREVIEW_PREFIX, get_unit_scale, cleanup_previews
from .props import HiFiProperties, HiFiSelectedProps
from .ui import (HIFI_PT_main, HIFI_PT_generator, HIFI_PT_transform, HIFI_PT_utils, HIFI_PT_inspector)

from .operators import (
    HIFI_OT_generate, HIFI_OT_clear_previews, HIFI_OT_join_cleanup,
    HIFI_OT_load_selected_params, HIFI_OT_apply_transform_to_selected,
    HIFI_OT_copy_transform, HIFI_OT_orphan_cleanup, HIFI_OT_game_export
)

from .hifi_auto_anim import (
    HIFI_OT_anim_step1_rig, 
    HIFI_OT_anim_step2_clipdict, 
    HIFI_OT_anim_step3_ytyp
)

classes = (
    HiFiProperties, HiFiSelectedProps,
    HIFI_PT_main, HIFI_PT_generator, HIFI_PT_transform, HIFI_PT_utils, HIFI_PT_inspector,
    HIFI_OT_generate, HIFI_OT_clear_previews, HIFI_OT_join_cleanup,
    HIFI_OT_load_selected_params, HIFI_OT_apply_transform_to_selected,
    HIFI_OT_copy_transform, HIFI_OT_orphan_cleanup, HIFI_OT_game_export,
    HIFI_OT_anim_step1_rig, HIFI_OT_anim_step2_clipdict, HIFI_OT_anim_step3_ytyp
)

def register():
    for c in classes: bpy.utils.register_class(c)
    bpy.types.Scene.hifi_props = bpy.props.PointerProperty(type=HiFiProperties)
    bpy.types.Scene.hifi_sel_props = bpy.props.PointerProperty(type=HiFiSelectedProps)

def unregister():
    for c in reversed(classes):
        try: bpy.utils.unregister_class(c)
        except: pass
    try: del bpy.types.Scene.hifi_props
    except: pass
    try: del bpy.types.Scene.hifi_sel_props
    except: pass
    cleanup_previews()

if __name__ == "__main__":
    register()
