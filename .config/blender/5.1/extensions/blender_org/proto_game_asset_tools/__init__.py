# PROTO Game Asset Tools
# 2026 PROTOWLF, Licensed under GPL-3.0


bl_info = {
    "name": "PROTO Game Asset Tools",
    "author": "PROTOWLF",
    "version": (1, 5, 0),
    "blender": (4, 2, 0),
    "location": "3D View > Properties > PROTO",
    "description": "Tools for game assets, with fixed exports for Unreal/Source.",
    "category": "Import-Export",
    "doc_url" : "https://protowlf.com/blendergameassettools/"
    }


# import, reload if already imported
if "proto_fbx_init" not in locals():
    from .src.fbx_export import proto_fbx_init
    from . import preferences
    from .src import properties
    from .src import ui
    from .src import operators
    from .src import batch_export_operators
    from .src import vertex_group_to_vertex_color
    #print("PROTO Tools: Importing")
else:
    import importlib
    proto_fbx_init = importlib.reload(proto_fbx_init)
    preferences = importlib.reload(preferences)
    properties = importlib.reload(properties)
    ui = importlib.reload(ui)
    operators = importlib.reload(operators)
    batch_export_operators = importlib.reload(batch_export_operators)
    vertex_group_to_vertex_color = importlib.reload(vertex_group_to_vertex_color)
    #print("PROTO Tools: Reloading Scripts") 

import bpy
from bpy.app.handlers import persistent


# On File Load
@persistent
def on_load_post(dummy):
    preferences.update_prototools_panel_category()

bpy.app.handlers.load_post.append(on_load_post)

# On File Save
@persistent
def on_save_pre(dummy):
    properties.on_save_pre()

bpy.app.handlers.save_pre.append(on_save_pre)


def register():
    proto_fbx_init.register()
    preferences.register()
    properties.register()
    ui.register()
    operators.register()
    batch_export_operators.register()
    vertex_group_to_vertex_color.register()
    
    preferences.update_prototools_panel_category()
    

def unregister():
    vertex_group_to_vertex_color.unregister()
    batch_export_operators.unregister()
    operators.unregister()
    ui.unregister()
    properties.unregister()
    preferences.unregister()
    proto_fbx_init.unregister()
    

if __name__ == "__main__":
    register()