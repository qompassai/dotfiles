# PROTO Tools UI Panels
# 2026 PROTOWLF, Licensed under GPL-3.0

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
    CollectionProperty,
    PointerProperty,
)

if "protogat_utils" not in locals():
    from . import protogat_utils
else:
    import importlib
    protogat_utils = importlib.reload(protogat_utils)
from .protogat_utils import (
    get_current_quick_export_properties,
    get_current_multi_selected_batch_export_items,
    get_current_selected_batch_export_item
)

if "proto_fbx_utils" not in locals():
    from .fbx_export import proto_fbx_utils
else:
    import importlib
    proto_fbx_utils = importlib.reload(proto_fbx_utils)
from .fbx_export.proto_fbx_utils import (
    action_has_slot_with_name
)


addon_package_name = __package__
addon_package_name = addon_package_name.removesuffix(".src")

# Percentage splits of custom property split in exporter UI
export_split_percent = 0.3
export_objects_split_percent = 0.1


class ProtoToolsPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Game Asset Tools'


class PROTOTOOLS_PT_Export(bpy.types.Panel, ProtoToolsPanel):
    bl_label = 'PROTO FBX Export'
    
    def draw(self, context):
        layout = self.layout
        proto_quickexport = context.scene.proto_quickexport
        
        layout.prop(proto_quickexport, "quick_export_mode", expand=True)
        


class PROTOTOOLS_PT_Export_Quick(bpy.types.Panel, ProtoToolsPanel):
    bl_label = ""
    bl_parent_id = "PROTOTOOLS_PT_Export"
    
    def draw_header(self, context):
        layout = self.layout
        proto_quickexport = context.scene.proto_quickexport
        
        if proto_quickexport.quick_export_mode == "ExportSelected":
            self.layout.label(text="Export Selected")
        else:
            self.layout.label(text="Batch Export")
    
    def draw(self, context):
        layout = self.layout
        proto_quickexport = context.scene.proto_quickexport
        
        if proto_quickexport.quick_export_mode == "ExportSelected":
            panel_export_selected(layout, context)
        else:
            panel_batch_export(layout, context)


def panel_export_selected(layout, context):
    export_properties = get_current_quick_export_properties(context)
    
    # export_mode as tabs
    ## Create 3 columns, with wide center column, to add padding
    ## around the operator button
    #split = layout.split(factor=0.1)
    #gap = split.column()
    #col = split.column()
    #split = col.split(factor=0.88888)
    #col = split.column()
    #row = col.row(align=True)
    #row.prop(export_properties, "export_mode", expand=True)
    #
    
    box = layout.box()
    split = box.split(factor=export_split_percent)
    labelCol = split.column()
    labelCol.alignment = 'RIGHT'
    valueCol = split.column()
    
    labelCol.label(text=export_properties.bl_rna.properties["export_mode"].name)
    valueCol.prop(export_properties, "export_mode", text="")
    
    #box = layout.box()
    col = layout.column()
    
    if export_properties.export_mode == "Combined":
        col.label(text="Export Model + Animations:")
        
        split = col.split(factor=export_split_percent)
        labelCol = split.column()
        labelCol.alignment = 'RIGHT'
        valueCol = split.column()
        
        #labelCol.label(text="Mesh:")
        labelCol.label(text="File Path")
        valueCol.prop(export_properties, "model_path", text="")
        
        labelCol.label(text="")
        valueCol.operator("prototools.quick_export_mesh_and_animations", text="Export", icon='EXPORT') # text="Model + Animations"
        if export_properties.use_action_filter:
            labelCol.label(text="")
            row = valueCol.row()
            row.alignment = 'RIGHT'
            row.label(text="*Action filter enabled")
        
    else:
        col.label(text="Export Model:")
        
        split = col.split(factor=export_split_percent)
        labelCol = split.column()
        labelCol.alignment = 'RIGHT'
        valueCol = split.column()
        
        #labelCol.label(text="Mesh:")
        labelCol.label(text="File Path")
        valueCol.prop(export_properties, "model_path", text="")
        
        labelCol.label(text="")
        valueCol.operator("prototools.quick_export_mesh", text="Export Model", icon='EXPORT') # text="Model"
        
        
        col.label(text="Export Animation:")
        
        split = col.split(factor=export_split_percent)
        labelCol = split.column()
        labelCol.alignment = 'RIGHT'
        valueCol = split.column()
        
        labelCol.label(text="")
        valueCol.prop(export_properties, "one_file_per_action")
        
        if export_properties.one_file_per_action:
            labelCol.label(text="Folder")
            valueCol.prop(export_properties, "anim_folder_path", text="")
            
            labelCol.label(text="")
            
            row = valueCol.row(align=True)
            row.operator("prototools.quick_export_curaction", text="Active", icon='EXPORT')
            row.operator("prototools.quick_export_allactions", text="All", icon='EXPORT')
        else:
            labelCol.label(text="File Path")
            valueCol.prop(export_properties, "all_anims_path", text="")
            
            labelCol.label(text="")
            valueCol.operator("prototools.quick_export_allactions", text="Export All Actions", icon='EXPORT') # text="All Actions"
        
        
        if export_properties.use_action_filter:
            labelCol.label(text="")
            row = valueCol.row()
            row.alignment = 'RIGHT'
            row.label(text="*Action filter enabled")
        
        # Warnings for invalid settings
        #box = None
        #if export_properties.one_file_per_action == False and export_properties.remove_scale_from_bones:
        #    if box == None:
        #        box = valueCol.box()
        #        box.alert = True
        #    box.label(text="Remove Scale From Bones", icon="ERROR")
        #    box.label(text="requires 1 File Per Action")
        #if export_properties.one_file_per_action == False and export_properties.flat_bone_hierarchy:
        #    if box == None:
        #        box = valueCol.box()
        #        box.alert = True
        #    box.label(text="Flat Bone Hierarchy", icon="ERROR")
        #    box.label(text="requires 1 File Per Action")
        ...


class PROTOTOOLS_UL_BatchExportItemList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()
        row.prop(item, "name", text="", emboss=False, icon = "PACKAGE")
        
        col = row.row()
        col.alignment = 'RIGHT'
        col.prop(item, "multi_selected", text="", emboss=False, icon=('CHECKBOX_DEHLT', 'CHECKBOX_HLT')[item.multi_selected], icon_only=True)


class PROTOTOOLS_UL_BatchExportObjectList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()
        icon = "BLANK1"
        if item.rename_name != "" and not item.rename_name.isspace():
            icon = "CURRENT_FILE"
        row.label(icon=icon) # Gap to make it easier to select, and show if renamed
        row.prop(item, "pointer", text="", emboss=True)


def panel_batch_export(layout, context):
    proto_quickexport = context.scene.proto_quickexport
    
    # Export button (visible but disabled if no export items)
    current_export_items = get_current_multi_selected_batch_export_items(context)[0]
    num_current_export_items = len(current_export_items)
    export_text = "Export"
    if num_current_export_items > 1:
        export_text = "Export (" + str(num_current_export_items) + ")"
    
    # Create 3 columns, with wide center column, to add padding
    # around the operator button
    split = layout.split(factor=0.1)
    gap = split.column()
    col = split.column()
    split = col.split(factor=0.88888)
    col = split.column()
    row = col.row(align=True)
    
    op = row.operator("prototools.batch_export", text=export_text, icon='EXPORT')
    
    
    # Export Item List
    row = layout.row()
    row.label(icon="PACKAGE", text=proto_quickexport.bl_rna.properties["batch_export_items"].name)
    row = layout.row()
    col = row.column()
    col.template_list(
		"PROTOTOOLS_UL_BatchExportItemList",
		"batch_export_items_list",
		proto_quickexport,
		"batch_export_items",
		proto_quickexport,
		"batch_export_items_index",
        rows=5
	)
    
    col = row.column(align=True)
    col.operator("prototools.add_batch_export_item", icon="ADD", text="")
    col.operator("prototools.remove_batch_export_item", icon="REMOVE", text="")
    col.separator()
    col.operator("prototools.duplicate_batch_export_item", icon="DUPLICATE", text="")
    col.separator()
    if len(proto_quickexport.batch_export_items) > 0:
        col.operator("prototools.move_batch_export_item", icon="TRIA_UP", text="").direction = 'UP'
        col.operator("prototools.move_batch_export_item", icon="TRIA_DOWN", text="").direction = 'DOWN'
    
    
    # Batch Settings for selection
    batch_export_item = get_current_selected_batch_export_item(context)
    if batch_export_item == None:
        return
    
    # Name of Export Item
    layout.label(text=batch_export_item.name)
    
    export_properties = batch_export_item.export_properties
    if batch_export_item == None or export_properties == None:
        return
    
    split = layout.split(factor=export_split_percent)
    labelCol = split.column()
    labelCol.alignment = 'RIGHT'
    valueCol = split.column()
    
    # Export Mode
    labelCol.label(text=batch_export_item.bl_rna.properties["batch_export_item_mode"].name)
    valueCol.prop(batch_export_item, "batch_export_item_mode", text="")
    
    if batch_export_item.batch_export_item_mode == "ModelAndAnimations" or batch_export_item.batch_export_item_mode == "Model":
        labelCol.label(text="File Path")
        valueCol.prop(export_properties, "model_path", text="")
    else:
        labelCol.label(text="")
        valueCol.prop(export_properties, "one_file_per_action")
        if export_properties.one_file_per_action:
            labelCol.label(text="Folder")
            valueCol.prop(export_properties, "anim_folder_path", text="")
        else:
            labelCol.label(text="File Path")
            valueCol.prop(export_properties, "all_anims_path", text="")
    
    # Object selector
    layout.separator()
    split = layout.split(factor=export_objects_split_percent)
    labelCol = split.column()
    labelCol.alignment = 'RIGHT'
    valueCol = split.column()
    
    #labelCol.label(text="Objects")
    valueColRow = valueCol.row()
    col = valueColRow.column()
    row = col.row(align=True)
    row.label(text="Objects")
    row.operator("prototools.add_export_object", icon="ADD", text="Add")
    row.operator("prototools.remove_export_object", icon="REMOVE", text="Rmv")
    col.template_list(
        "PROTOTOOLS_UL_BatchExportObjectList",
        "batch_export_objects_list",
        batch_export_item,
        "export_objects",
        batch_export_item,
        "export_objects_index",
        rows=4
    )
    row = col.row(align=True)
    if batch_export_item.export_objects_index >= 0 and batch_export_item.export_objects_index < len(batch_export_item.export_objects):
        current_export_object_entry = batch_export_item.export_objects[batch_export_item.export_objects_index]
        if current_export_object_entry.pointer != None and current_export_object_entry.pointer.type != "ARMATURE":
            row.separator()
            split = row.split(factor=0.35)
            sublabelCol = split.column()
            sublabelCol.alignment = 'RIGHT'
            subvalueCol = split.column()
            sublabelCol.label(text=current_export_object_entry.bl_rna.properties["rename_name"].name)
            subvalueCol.prop(current_export_object_entry, "rename_name", text="")
    
    row = col.row(align=True)
    row.operator("prototools.select_export_objects")
    row.operator("prototools.deselect_export_objects")
    
    #col = valueColRow.column(align=True)
    #col.operator("prototools.add_export_object", icon="ADD", text="")
    #col.operator("prototools.remove_export_object", icon="REMOVE", text="")
    #col.separator()
    #if len(batch_export_item.export_objects) > 0:
    #    col.operator("prototools.move_export_object", icon="TRIA_UP", text="").direction = 'UP'
    #    col.operator("prototools.move_export_object", icon="TRIA_DOWN", text="").direction = 'DOWN'


class PROTOTOOLS_PT_Export_Quick_Options(bpy.types.Panel, ProtoToolsPanel):
    bl_label = ""
    bl_parent_id = "PROTOTOOLS_PT_Export_Quick"
    
    @classmethod
    def poll(cls, context):
        proto_quickexport = context.scene.proto_quickexport
        if proto_quickexport.quick_export_mode == "ExportSelected":
            return True
        
        export_properties = get_current_quick_export_properties(context)
        return export_properties != None
    
    def draw_header(self, context):
        layout = self.layout
        proto_quickexport = context.scene.proto_quickexport
        
        if proto_quickexport.quick_export_mode == "ExportSelected":
            self.layout.label(text="Options")
        else:
            batch_export_item = get_current_selected_batch_export_item(context)
            if batch_export_item == None:
                self.layout.label(text="Options - (no Export Item)")
            else:
                self.layout.label(text="Options - " + batch_export_item.name)
    
    def draw(self, context):
        layout = self.layout
        
        # Options Presets
        export_properties = get_current_quick_export_properties(context)
        if export_properties != None:
            row = layout.row()
            row.operator_menu_enum("prototools.quick_export_set_options_preset", "preset")
            row = row.row(align=True)
            op = row.operator("prototools.copy_quickexport_options", text="", icon="COPYDOWN")
            op.batch_export_item_index = export_properties.batch_export_item_index
            op = row.operator("prototools.paste_quickexport_options", text="", icon="PASTEDOWN")
            op.batch_export_item_index = export_properties.batch_export_item_index


class PROTOTOOLS_PT_Export_Quick_Options_Scene(bpy.types.Panel, ProtoToolsPanel):
    bl_label = "Scene"
    bl_parent_id = "PROTOTOOLS_PT_Export_Quick_Options"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        # Only draw if exactly 1 export item is active
        return get_current_quick_export_properties(context) != None
    
    def draw(self, context):
        layout = self.layout
        export_properties = get_current_quick_export_properties(context)
        layout.use_property_split = True
        layout.use_property_decorate = False # keyframe/animate properties
        
        layout.prop(export_properties, "apply_modifiers")
        layout.prop(export_properties, "move_to_origin")
        layout.prop(export_properties, "scene_conversion_mode")
        if export_properties.scene_conversion_mode == "Custom":
            layout.separator()
            layout.prop(export_properties, "bake_scale_mode")
            if export_properties.bake_scale_mode == "Custom":
                layout.prop(export_properties, "bake_scale_custom")
            layout.prop(export_properties, "scene_rotation_mode")
            layout.prop(export_properties, "skip_armature_object")
            if export_properties.skip_armature_object == False:
                layout.prop(export_properties, "armature_name")


class PROTOTOOLS_UL_Export_Quick_Options_ActionList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()
        row.prop(item.action, "name", text="", emboss=False)
        col = row.row()
        col.alignment = 'RIGHT'
        col.prop(item, "keep", text="", emboss=True, icon_only=True) #emboss=False, icon=('CHECKBOX_DEHLT', 'CHECKBOX_HLT')[item.multi_selected], icon_only=True)


class PROTOTOOLS_MT_ActionList_Context_Menu(bpy.types.Menu):
    bl_label = "Action List Operations"

    def draw(self, context):
        layout = self.layout
        
        op = layout.operator("prototools.set_all_quick_export_actionlist", text="Enable All")
        op.enable = True
        op = layout.operator("prototools.set_all_quick_export_actionlist", text="Disable All")
        op.enable = False


class PROTOTOOLS_PT_Export_Quick_Options_Actions(bpy.types.Panel, ProtoToolsPanel):
    bl_label = "Actions"
    bl_parent_id = "PROTOTOOLS_PT_Export_Quick_Options"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        proto_quickexport = context.scene.proto_quickexport
        
        if proto_quickexport.quick_export_mode == "BatchExport":
            # In batch mode, hide if exporting Model only
            batch_export_item = get_current_selected_batch_export_item(context)
            return batch_export_item != None and batch_export_item.batch_export_item_mode != "Model"
        
        # Only draw if exactly 1 export item is active
        return get_current_quick_export_properties(context) != None
    
    def draw(self, context):
        layout = self.layout
        export_properties = get_current_quick_export_properties(context)
        layout.use_property_split = True
        layout.use_property_decorate = False # keyframe/animate properties
        
        if export_properties.export_mode == "Separate":
            layout.separator()
            layout.prop(export_properties, "action_name_style")
            if export_properties.action_name_style != "Action":
                layout.prop(export_properties, "action_name_sharedname")
            layout.prop(export_properties, "animation_force_dummy_mesh")
        
        col = layout.column()
        col.use_property_split = False
        top_row = col.row()
        top_row.label(text="", icon="ACTION")
        top_row.prop(export_properties, "use_action_filter")
        if export_properties.use_action_filter == True:
            row = col.row()
            row.template_list(
                "PROTOTOOLS_UL_Export_Quick_Options_ActionList",
                "proto_quick_export_action_list",
                export_properties,
                "action_filter",
                export_properties,
                "action_filter_index",
                rows=4
            )
            
            side_bar = row.column(align=True)
            side_bar.operator("prototools.refresh_quick_export_actionlist", icon="FILE_REFRESH", text="")
            side_bar.separator()
            side_bar.menu("PROTOTOOLS_MT_ActionList_Context_Menu", icon='DOWNARROW_HLT', text="")


class PROTOTOOLS_PT_Export_Quick_Options_ShapeKeys(bpy.types.Panel, ProtoToolsPanel):
    bl_label = "Shape Key Animation"
    bl_parent_id = "PROTOTOOLS_PT_Export_Quick_Options"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        proto_quickexport = context.scene.proto_quickexport
        
        if proto_quickexport.quick_export_mode == "BatchExport":
            # In batch mode, hide if exporting Model only
            batch_export_item = get_current_selected_batch_export_item(context)
            return batch_export_item != None and batch_export_item.batch_export_item_mode != "Model"
        
        # Only draw if exactly 1 export item is active
        return get_current_quick_export_properties(context) != None
    
    def draw_header(self, context):
        layout = self.layout
        export_properties = get_current_quick_export_properties(context)
        layout.prop(export_properties, "export_shapekey_animation", text="")
    
    def draw(self, context):
        layout = self.layout
        export_properties = get_current_quick_export_properties(context)
        
        body = layout.column()
        body.use_property_split = True
        body.use_property_decorate = False # keyframe/animate properties
        body.active = export_properties.export_shapekey_animation
        
        if export_properties.export_mode == "Separate":
            body.prop(export_properties, "shapekey_export_mode")
        
        col = body.column(heading="Include")
        col.prop(export_properties, "export_zeroed_shapekeys")


class PROTOTOOLS_PT_Export_Quick_Options_CustomProperties(bpy.types.Panel, ProtoToolsPanel):
    bl_label = "Custom Property Animation"
    bl_parent_id = "PROTOTOOLS_PT_Export_Quick_Options"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        proto_quickexport = context.scene.proto_quickexport
        
        if proto_quickexport.quick_export_mode == "BatchExport":
            # In batch mode, hide if exporting Model only
            batch_export_item = get_current_selected_batch_export_item(context)
            return batch_export_item != None and batch_export_item.batch_export_item_mode != "Model"
        
        # Only draw if exactly 1 export item is active
        return get_current_quick_export_properties(context) != None
    
    def draw_header(self, context):
        layout = self.layout
        export_properties = get_current_quick_export_properties(context)
        layout.prop(export_properties, "export_custom_property_animation", text="")
    
    def draw(self, context):
        layout = self.layout
        export_properties = get_current_quick_export_properties(context)
        
        layout.use_property_split = True
        layout.use_property_decorate = False # keyframe/animate properties
        
        #layout.prop(export_properties, "export_custom_property_animation")
        sub = layout.column(heading="Include")
        sub.active = export_properties.export_custom_property_animation
        sub.prop(export_properties, "export_zeroed_custom_properties")
        sub.prop(export_properties, "export_non_deform_custom_properties")
        sub.prop(export_properties, "export_armature_object_custom_properties")
        sub.prop(export_properties, "export_armature_data_custom_properties")


class PROTOTOOLS_PT_Export_Quick_Options_Advanced(bpy.types.Panel, ProtoToolsPanel):
    bl_label = 'Advanced'
    bl_parent_id = "PROTOTOOLS_PT_Export_Quick_Options"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        # Only draw if exactly 1 export item is active
        return get_current_quick_export_properties(context) != None
    
    def draw(self, context):
        layout = self.layout
        export_properties = get_current_quick_export_properties(context)
        
        layout.use_property_split = True
        layout.use_property_decorate = False # keyframe/animate properties
        
        layout.prop(export_properties, "remove_scale_from_bones")
        layout.prop(export_properties, "remove_bone_rotation")
        layout.prop(export_properties, "flat_bone_hierarchy")
        if export_properties.flat_bone_hierarchy == True:
            layout.prop(export_properties, "flat_bone_hierarchy_root")
        
        # Animation only properties
        show_anim_props = True
        proto_quickexport = context.scene.proto_quickexport
        if proto_quickexport.quick_export_mode == "BatchExport":
            # In batch mode, hide if exporting Model only
            batch_export_item = get_current_selected_batch_export_item(context)
            show_anim_props = (batch_export_item != None and batch_export_item.batch_export_item_mode != "Model")
        if show_anim_props:
            layout.prop(export_properties, "bake_anim_simplify_factor")
            layout.prop(export_properties, "dont_simplify_root_bone")
            layout.prop(export_properties, "min_two_frames")
            
            if export_properties.export_mode == "Separate":
                col = layout.column()
                col.enabled = export_properties.shapekey_export_mode == 'ArmatureCustomProps'
                col.prop(export_properties, "armature_shapekey_scale")


# DEPRECATED - confusing, not super useful
#class PROTOTOOLS_PT_ManualExport(bpy.types.Panel, ProtoToolsPanel):
#    bl_label = 'Manual Export'
#    bl_parent_id = "PROTOTOOLS_PT_Export"
#    bl_options = {'DEFAULT_CLOSED'}
#    
#    def draw(self, context):
#        layout = self.layout
#        
#        # Create 3 columns, with wide center column, to add padding
#        # around the operator button
#        split = layout.split(factor=0.1)
#        gap = split.column()
#        col = split.column()
#        split = col.split(factor=0.88888)
#        col = split.column()
#        row = col.row(align=True)
#        
#        row.operator("proto_export_scene.fbx", text="PROTO FBX Export...")


class PROTOTOOLS_PT_ActionSelector(bpy.types.Panel, ProtoToolsPanel):
    bl_label = 'Quick Action Select'
    
    def draw(self, context):
        settings = bpy.context.preferences.addons[addon_package_name].preferences
        
        layout = self.layout
        proto_actionselect = context.scene.proto_actionselect
        
        layout.label(text="Actions", icon="ACTION")
        
        # Create 3 columns, with wide center column, to add padding
        # around the operator button
        #split = layout.split(factor=0.1)
        #gap = split.column()
        #col = split.column()
        #split = col.split(factor=0.88888)
        #col = split.column()
        #row = col.row(align=True)
        
        col = layout.column()
        row = col.row(align=True)
        
        if context.active_object != None:
            if context.active_object.animation_data != None:
                row.template_ID(context.active_object.animation_data, "action", new="prototools.actionnew", unlink="prototools.actionunlink", filter='AVAILABLE')
                current_action = context.active_object.animation_data.action
                
                # Possibly show buttons to fix problems
                box = None
                
                # Warning / operator to delete animation data on mesh
                # Commented out, decided not to warn about this
                #if context.active_object.type == 'MESH' and context.active_object.animation_data != None:
                #    if box == None:
                #        box = col.box()
                #        box.alert = True
                #    box.label(text="Mesh animation data detected!", icon="ERROR")
                #    box.label(text="Can cause animation export issues")
                #    row = box.row(align=True)
                #    # Display button to delete animation data
                #    row.operator("prototools.delete_mesh_animation_data", icon="TRASH")
                
                if current_action != None:
                    # Delete action button
                    row.operator("prototools.actiondelete", text="", icon="TRASH")
                    
                    if bpy.app.version >= (4, 4, 0):
                        # Blender 4.4 and up
                        if settings.action_slot_behavior == "ARMATURE_NAME":
                            if action_has_slot_with_name(current_action, "Legacy Slot"):
                                if box == None:
                                    box = col.box()
                                    box.alert = True
                                box.label(text="Legacy Action Slot data detected!", icon="ERROR")
                                row = box.row(align=True)
                                # Display button to update Legacy Slot to armature name
                                row.operator("prototools.update_legacy_slot", icon="SHADERFX") #DECORATE_OVERRIDE
                                # Display button to delete Legacy Slot
                                row.operator("prototools.delete_legacy_slot", icon="TRASH")
                            
                            current_slot = context.active_object.animation_data.action_slot
                            if current_slot == None:
                                # No slot selected
                                if box == None:
                                    box = col.box()
                                    box.alert = True
                                    
                                box.label(text="No Action Slot assigned!", icon="ERROR")
                                if action_has_slot_with_name(current_action, context.active_object.name):
                                    # Display button to switch to the correctly-named slot
                                    box.operator("prototools.switch_to_object_name_slot", text="Switch to Slot '" + context.active_object.name + "'", icon="DECORATE_OVERRIDE")
                                else:
                                    # Display button to create a new slot
                                    box.operator("prototools.create_object_name_slot", text="Create Slot '" + context.active_object.name + "'", icon="FILE_NEW")
                                
                                    
                            elif current_slot.name_display != "Legacy Slot" and current_slot.name_display != context.active_object.name:
                                # Some other slot selected
                                if box == None:
                                    box = col.box()
                                    box.alert = True
                                    
                                box.label(text="Action Slot does not match Object name!", icon="ERROR")
                                if action_has_slot_with_name(current_action, context.active_object.name):
                                    # Display button to switch to the correctly-named slot
                                    box.operator("prototools.switch_to_object_name_slot", text="Switch to Slot '" + context.active_object.name + "'", icon="DECORATE_OVERRIDE")
                                else:
                                    # Display button to create a new slot
                                    box.operator("prototools.create_object_name_slot", text="Create Slot '" + context.active_object.name + "'", icon="FILE_NEW")
                                    # Display button to rename current slot to armature name
                                    box.operator("prototools.rename_current_slot_to_object_name", text="Rename Slot '" + current_slot.name_display + "' to '" + context.active_object.name + "'", icon="FILE_TEXT")
                        
                        elif settings.action_slot_behavior == "MANUAL":
                            # Slot selection widget
                            row = col.row(align=True)
                            
                            animated_id = context.active_object
                            adt = animated_id and animated_id.animation_data
                            if not adt or not adt.action or not adt.action.is_action_layered:
                                return
                            row.context_pointer_set("animated_id", animated_id)
                            row.template_search(adt, "action_slot", adt, "action_suitable_slots", new="anim.slot_new_for_id", unlink="anim.slot_unassign_from_id")
                            
                            current_slot = context.active_object.animation_data.action_slot
                            if current_slot != None:
                                # Delete action button
                                row.operator("prototools.action_slot_delete", text="", icon="TRASH")
                    
            else:
                row.operator("prototools.makeanimdata", icon="PLUS")
            
        
        # Frame range, set timeline widgets
        if context.active_object != None and context.active_object.animation_data != None and context.active_object.animation_data.action != None:
            action = context.active_object.animation_data.action
            col.prop(action, "use_frame_range")
            col2 = col.column()
            col2.active = action.use_frame_range
            row = col2.row(align=True)
            row.prop(action, "frame_start", text="Start")
            row.prop(action, "frame_end", text="End")
            
            col3 = col.column()
            split = col3.split(factor=0.7)
            col3_1 = split.column()
            col3_2 = split.column()
            col3_1.operator("prototools.timelinetoaction")
            col3_2.prop(proto_actionselect, "set_timeline_ignore_zero")
            
            # If this custom property does not exist on the action, we display a "dummy" property to set it for the first time
            #if "Export Shapekey Animation" in action:
            #    col.prop(action, '["Export Shapekey Animation"]')
            #else:
            #    col.prop(proto_actionselect, "cur_action_shapekey_data")
        else:
            # Dummy version that is always disabled
            colDisabled = col.column()
            colDisabled.active = False
            colDisabled.prop(proto_actionselect, "dummy_action_use_frame_range")
            col2 = colDisabled.column()
            row = col2.row(align=True)
            row.prop(proto_actionselect, "dummy_action_frame_start", text="Start")
            row.prop(proto_actionselect, "dummy_action_frame_end", text="End")
            
            split = col2.split(factor=0.7)
            col2_1 = split.column()
            col2_2 = split.column()
            row = col2.row(align=False)
            col2_1.operator("prototools.timelinetoaction")
            col2_2.prop(proto_actionselect, "set_timeline_ignore_zero")
            
            # always show dummy
            #colDisabled.prop(proto_actionselect, "cur_action_shapekey_data")


class PROTOTOOLS_PT_VertexColors(bpy.types.Panel, ProtoToolsPanel):
    bl_label = 'Vertex Color Tools'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        proto_vertextools = context.scene.proto_vertextools
        
        layout.label(text="Fill Vertex Color", icon="VPAINT_HLT")
        
        fill_weight = 1.0
        fill_skip_mask = True
        if context.mode == "PAINT_VERTEX":
            col = layout.column()
            col.use_property_split = True
            col.use_property_decorate = False # keyframe/animate properties
            
            col.prop(proto_vertextools, "fill_weight", slider=True)
            col.prop(proto_vertextools, "fill_skip_mask")
            fill_weight = proto_vertextools.fill_weight
            fill_skip_mask = proto_vertextools.fill_skip_mask
        
        # Create 3 columns, with wide center column, to add padding
        # around the operator button
        split = layout.split(factor=0.1)
        gap = split.column()
        col = split.column()
        split = col.split(factor=0.88888)
        col = split.column(align=True)
        row = col.row(align=True)
        row.scale_y = 1.2
        
        row = col.row(align=True)
        row.scale_y = 1.2
        
        channels = ["R","G","B","A"]
        for channel in channels:
            op = row.operator("prototools.fill_vertex_color", text=channel)
            op.channel = channel
            op.weight = fill_weight
            op.skip_mask = fill_skip_mask
        
        row = col.row(align=True)
        row.scale_y = 1.2
        
        for channel in channels:
            op = row.operator("prototools.fill_vertex_color", text="Clear")
            op.channel = channel
            op.weight = 0.0
            op.skip_mask = fill_skip_mask
        
        
        layout.label(text="Vertex Group to Vertex Color", icon="GROUP_VERTEX")
        
        group_to_color_invert = False
        group_to_color_skip_mask = True
        if context.mode == "PAINT_VERTEX":
            col = layout.column()
            col.use_property_split = True
            col.use_property_decorate = False # keyframe/animate properties
            
            col.prop(proto_vertextools, "group_to_color_invert")
            col.prop(proto_vertextools, "group_to_color_skip_mask")
            group_to_color_invert = proto_vertextools.group_to_color_invert
            group_to_color_skip_mask = proto_vertextools.group_to_color_skip_mask
        
        # Create 3 columns, with wide center column, to add padding
        # around the operator button
        split = layout.split(factor=0.1)
        gap = split.column()
        col = split.column()
        split = col.split(factor=0.88888)
        col = split.column(align=True)
        row = col.row(align=True)
        row.scale_y = 1.2
        
        label_str = "Group: none"
        if context.active_object != None and context.active_object.vertex_groups.active != None:
            label_str = "Group: " + context.active_object.vertex_groups.active.name
        row.label(text=label_str)
        
        row = col.row(align=True)
        row.scale_y = 1.2
        
        for channel in channels:
            op = row.operator("prototools.vertex_group_to_vertex_color", text=channel)
            op.channel = channel
            op.invert = group_to_color_invert
            op.skip_mask = group_to_color_skip_mask


panel_classes = (
    PROTOTOOLS_PT_Export,
    PROTOTOOLS_PT_Export_Quick,
    PROTOTOOLS_UL_BatchExportItemList,
    PROTOTOOLS_UL_BatchExportObjectList,
    PROTOTOOLS_PT_Export_Quick_Options,
    PROTOTOOLS_PT_Export_Quick_Options_Scene,
    PROTOTOOLS_UL_Export_Quick_Options_ActionList,
    PROTOTOOLS_MT_ActionList_Context_Menu,
    PROTOTOOLS_PT_Export_Quick_Options_Actions,
    PROTOTOOLS_PT_Export_Quick_Options_ShapeKeys,
    PROTOTOOLS_PT_Export_Quick_Options_CustomProperties,
    PROTOTOOLS_PT_Export_Quick_Options_Advanced,
    #PROTOTOOLS_PT_ManualExport,
    PROTOTOOLS_PT_ActionSelector,
    PROTOTOOLS_PT_VertexColors
)


def register():
    for panel_class in panel_classes:
        bpy.utils.register_class(panel_class)


def unregister():
    for panel_class in panel_classes:
        bpy.utils.unregister_class(panel_class)

