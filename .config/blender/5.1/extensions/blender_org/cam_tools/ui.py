import bpy
from bpy.types import Panel
from .core import cam_tools, cam_res


class CAMTOOLS_PT_Combined(Panel):
    bl_label = "Cam Tools"
    bl_idname = "CAMTOOLS_PT_combined"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cam-Tools"

    def draw(self, context):
        layout = self.layout

        # ---- Cam Tools Section ----
        box = layout.box()
      
        cam_tools.draw_camtools(box, context)

        layout.separator(factor=1.2)

        # ---- Cam-Res Section ----
        cam_res.draw_camres(layout, context)
