
import bpy
from .core import cam_tools, cam_res
from . import ui



def register():
    cam_tools.register_camtools()
    cam_res.register_camres()
    bpy.utils.register_class(ui.CAMTOOLS_PT_Combined)

def unregister():
    bpy.utils.unregister_class(ui.CAMTOOLS_PT_Combined)
    cam_res.unregister_camres()
    cam_tools.unregister_camtools()
