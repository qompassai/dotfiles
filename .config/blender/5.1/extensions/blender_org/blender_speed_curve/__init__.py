if "bpy" in locals():
    import importlib
    importlib.reload(math_utils)
    importlib.reload(ui)
    importlib.reload(draw_handler)
else:
    import bpy
    from . import ui
    from . import draw_handler
    from . import math_utils

classes = (
    ui.SpeedCurveProperties,
    ui.GRAPH_OT_set_interpolation,
    ui.GRAPH_PT_speed_curve_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.speed_curve_props = bpy.props.PointerProperty(type=ui.SpeedCurveProperties)

def unregister():
    draw_handler.unregister_draw_handler()
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.speed_curve_props

if __name__ == "__main__":
    register()
