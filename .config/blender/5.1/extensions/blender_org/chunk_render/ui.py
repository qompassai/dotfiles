import bpy
from bpy.types import Panel, UIList
from .translations import iface_



class CHUNK_RENDER_PT_Region(Panel):
    bl_idname = "CHUNK_RENDER_PT_Region"
    bl_label = "Render Region"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        ps = scn.chunk_render_settings

        box1 = layout.box()
        row = box1.row()
        row.label(text=iface_("Step 1: Set Tile Grid"))
        row = box1.row()
        row.prop(ps, "CR_split_mode", text=iface_("Mode"))
        if ps.CR_split_mode == 'LEVELS':
            row = box1.row()
            row.prop(ps, "CR_level", text=iface_("Level"))
            row = box1.row()
            row.label(text=iface_("Current Grid: {cols} x {rows}").format(cols=ps.CR_reg_columns, rows=ps.CR_reg_rows))
        else:
            row = box1.row()
            col_left = row.column()
            col_left.alert = ps.CR_cols_pixel_error
            col_left.prop(ps, "CR_reg_columns", text=iface_("Columns (pixel mismatch)") if ps.CR_cols_pixel_error else iface_("Columns"))
            col_right = row.column()
            col_right.alert = ps.CR_rows_pixel_error
            col_right.prop(ps, "CR_reg_rows", text=iface_("Rows (pixel mismatch)") if ps.CR_rows_pixel_error else iface_("Rows"))

        row = box1.row(align=True)
        if scn.render.use_border:
            row.prop(ps, "CR_use_render_border", text=iface_("Use Render Border"), toggle=True)
            if ps.CR_use_render_border:
                row = box1.row(align=True)
                row.operator("chunk_render.align_border", text=iface_("Align Border (integer pixels)"), icon="CON_SHRINKWRAP")
        else:
            row.enabled = False
            row.prop(ps, "CR_use_render_border", text=iface_("Use Render Border (select a render border first)"), toggle=True)

        row = box1.row(align=True)
        row.prop(ps, "CR_overlay_enabled", text=iface_("Show Overlay Grid (Camera View Only)"), toggle=True)
        row = box1.row(align=True)
        row.prop(ps, "CR_bleed_pixels", text=iface_("Bleed Pixels"))

        box2 = layout.box()
        row = box2.row()
        row.label(text=iface_("Step 2: Run Chunk Render"))
        row = box2.row()
        row.operator("chunk_render.regions", text=iface_("Start Render"), icon="RENDER_STILL")
        row.enabled = not ps.CR_renderGo
        row = box2.row(align=True)
        row.prop(ps, "CR_save_region", text=iface_("Auto Merge Final Image"), toggle=True)
        sub = row.row(align=True)
        sub.enabled = ps.CR_save_region
        sub.prop(ps, "CR_delete_after_merge", text=iface_("Delete Tiles After Merge"), toggle=True)
        row = box2.row()
        row.operator("chunk_render.stop", text=iface_("Stop Render"), icon="CANCEL")
        row.enabled = ps.CR_renderGo
        if ps.CR_msg1 and ps.CR_renderGo:
            box2.label(text=ps.CR_msg1)

        adv = layout.box()
        row = adv.row()
        row.prop(ps, "CR_showAdvanced", text=iface_("Advanced Options"), toggle=True)
        if ps.CR_showAdvanced:
            adv_col = adv.column(align=True)
            adv_col.label(text=iface_("Saved Borders:"))
            row = adv_col.row()
            row.template_list("CHUNK_RENDER_UL_saved_borders", "", ps, "CR_saved_borders", ps, "CR_saved_borders_index", rows=3)
            list_col = row.column(align=True)
            list_col.operator("chunk_render.save_border", text="", icon='ADD')
            list_col.operator("chunk_render.remove_border", text="", icon='REMOVE')
            if len(ps.CR_saved_borders) > 0:
                adv_col.operator("chunk_render.restore_border", text=iface_("Restore Selected Border"), icon='VIEW_CAMERA')

            adv_col.separator()
            adv_col.label(text=iface_("Manual Tile Selection:"))
            adv_col.prop(ps, "CR_select_mode", text=iface_("Selection Mode"))
            if ps.CR_select_mode == 'CUSTOM':
                adv_col.prop(ps, "CR_custom_indices", text=iface_("Index List"))
                adv_col.label(text=iface_("Example: 0, 2, 5"), icon='INFO')

            adv_col.separator()
            adv_col.label(text=iface_("Re-Merge Existing Tiles:"))
            adv_col.prop(ps, "CR_remerge_folder", text=iface_("Tiles Folder"))
            adv_col.operator("chunk_render.remerge_tiles", text=iface_("Re-Merge Tiles"), icon='FILE_REFRESH')
            adv_col.label(text=iface_("Re-merge tries to preserve EXR channels, but"), icon='INFO')
            adv_col.label(text=iface_("100% lossless restoration of all channel data is still difficult"))


class CHUNK_RENDER_UL_saved_borders(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False, icon='FULLSCREEN_ENTER')
