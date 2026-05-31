# PROTO Tools Operators
# 2026 PROTOWLF, Licensed under GPL-3.0

import bpy
from bpy.props import (
    EnumProperty
)

from .fbx_export.proto_fbx_init import ProtoExportFBX_ExportListEntry

if "protogat_utils" not in locals():
    from . import protogat_utils
else:
    import importlib
    protogat_utils = importlib.reload(protogat_utils)
from .protogat_utils import (
    get_current_quick_export_properties,
    get_current_multi_selected_batch_export_items,
    get_current_selected_batch_export_item,
    #ensure_collection_visible,
    #restore_collection_visibility,
    #CollectionVisibilityInfo,
    get_new_export_item_name,
    validate_batch_export_item,
    get_object_name_split,
)

addon_package_name = __package__
addon_package_name = addon_package_name.removesuffix(".src")


# returns array of CollectionVisibilityInfo
#def select_and_force_visible_export_objects(objects):
#    bpy.ops.object.select_all(action='DESELECT')
#    visibility_infos = []
#    for ob in batch_export_item.export_objects:
#        # ensure collection visible
#        info = ensure_collection_visible(ob.users_collection[0])
#        visibility_infos.append(info)
#        
#        # select
#        bpy.context.view_layer.objects.active = ob
#        ob.select_set(state=True)
#
#
#def restore_export_object_visibility(visibility_infos):
#    for info in visibility_infos:
#        restore_collection_visibility(info)


class ProtoTools_BatchExport(bpy.types.Operator):
    """Export currently-selected Export Items"""
    bl_idname = "prototools.batch_export"
    bl_label = "Batch Export"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        current_export_items  = get_current_multi_selected_batch_export_items(context)[0]
        return len(current_export_items) > 0
    
    def execute(self, context):
        current_export_items, current_export_item_indices = get_current_multi_selected_batch_export_items(context)
        
        # Switch to object mode
        self.original_mode = context.mode
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        
        # Validate Export Items before starting batch export
        # Purposefully check all items, don't early-out
        all_passed = True
        error_entries = []
        for batch_export_item in current_export_items:
            errors = validate_batch_export_item(context, batch_export_item)
            
            if len(errors) > 0:
                all_passed = False
                
                errors_string = errors[0]
                for error in errors[1:]:
                    errors_string += "\n" + error
                
                error_entry = dict()
                error_entry["name"] = batch_export_item.name
                error_entry["header"] = batch_export_item.name
                error_entry["text"] = errors_string
                error_entry["icon"] = "CANCEL"
                error_entries.append(error_entry)
        if not all_passed:
            bpy.ops.prototools.infopopuparray('INVOKE_DEFAULT', title="Errors", entries=error_entries)
            return {'CANCELLED'}
        
        # Cache selected objects
        self.original_selected_objects = bpy.context.selected_objects
        self.original_active_selection = bpy.context.view_layer.objects.active
        
        # Iterate batch exports
        result = None
        fail = False
        failed_name = ""
        for i, batch_export_item in enumerate(current_export_items):
            export_properties = batch_export_item.export_properties
            export_index = current_export_item_indices[i]
            
            export_objects = []
            for export_object_entry in batch_export_item.export_objects:
                entry = dict()
                entry["name"] = export_object_entry.pointer.name
                entry["rename_name"] = export_object_entry.rename_name
                export_objects.append(entry)
            
            # Run export
            try:
                if batch_export_item.batch_export_item_mode == "ModelAndAnimations":
                    result = bpy.ops.prototools.quick_export_mesh_and_animations(export_name=batch_export_item.name, batch_export_item_index=export_index, export_object_list=export_objects)
                elif batch_export_item.batch_export_item_mode == "Model":
                    result = bpy.ops.prototools.quick_export_mesh(export_name=batch_export_item.name, batch_export_item_index=export_index, export_object_list=export_objects)
                elif batch_export_item.batch_export_item_mode == "Animations":
                    result = bpy.ops.prototools.quick_export_allactions(export_name=batch_export_item.name, batch_export_item_index=export_index, export_object_list=export_objects)
            except:
                fail = True
                failed_name = batch_export_item.name
            finally:
                # Delete duplicates
                #for ob in duplicate_objects:
                #    bpy.data.objects.remove(ob, do_unlink=(ob.type != "EMPTY"))
                #
                ## Restore object names
                #for ob, original_name in objects_to_original_names.items():
                #    ob.name = original_name
                
                if result == None or 'FINISHED' not in result:
                    fail = True
                    failed_name = batch_export_item.name
            
            # If export failed, stop batch
            if fail:
                break
        
        # Reselect original objects
        #bpy.ops.object.select_all(action='DESELECT')
        #for ob in self.original_selected_objects:
        #    ob.select_set(state=True)
        #bpy.context.view_layer.objects.active = self.original_active_selection
        
        # Switch to original mode
        try:
            bpy.ops.object.mode_set(mode=self.original_mode)
        except:
            pass
        
        # Report failure
        if fail:
            self.report({'ERROR'}, "Batch canceled! Export Item '" + failed_name + "' failed")
            return {'CANCELLED'}
        
        # Report success
        self.report({'INFO'}, str(len(current_export_items)) + " exports finished successfully")
        return {'FINISHED'}


class ProtoTools_AddBatchExportItem(bpy.types.Operator):
    """Add new Export Item"""
    bl_idname = "prototools.add_batch_export_item"
    bl_label = "Add Export Item"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        proto_quickexport = context.scene.proto_quickexport
        proto_quickexport.batch_export_items.add()
        new_index = len(proto_quickexport.batch_export_items) - 1
        proto_quickexport.batch_export_items[new_index].name = get_new_export_item_name(context, proto_quickexport.batch_export_items[new_index].name, new_index)
        proto_quickexport.batch_export_items[new_index].export_properties.batch_export_item_index = new_index
        
        proto_quickexport.batch_export_items_index = new_index # select this entry in list
        return {'FINISHED'}


class ProtoTools_RemoveBatchExportItem(bpy.types.Operator):
    """Remove current selected Export Item\n\nNote: will not delete any objects in the scene"""
    bl_idname = "prototools.remove_batch_export_item"
    bl_label = "Remove Export Item"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        proto_quickexport = context.scene.proto_quickexport
        if len(proto_quickexport.batch_export_items) == 0:
            return False
        return True
    
    def execute(self, context):
        proto_quickexport = context.scene.proto_quickexport
        index = proto_quickexport.batch_export_items_index
        
        proto_quickexport.batch_export_items.remove(index)
        for i, batch_export_item in enumerate(proto_quickexport.batch_export_items):
            batch_export_item.export_properties.batch_export_item_index = i
        
        # Select the entry that was above the one we deleted
        proto_quickexport.batch_export_items_index = max(0,min(index - 1,len(proto_quickexport.batch_export_items) - 1))
        return {'FINISHED'}


class ProtoTools_DuplicateBatchExportItem(bpy.types.Operator):
    """Duplicate current selected Export Item"""
    bl_idname = "prototools.duplicate_batch_export_item"
    bl_label = "Duplicate Export Item"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        proto_quickexport = context.scene.proto_quickexport
        if len(proto_quickexport.batch_export_items) == 0:
            return False
        if proto_quickexport.batch_export_items_index < 0 or proto_quickexport.batch_export_items_index > len(proto_quickexport.batch_export_items) - 1:
            return False
        return True
    
    def execute(self, context):
        proto_quickexport = context.scene.proto_quickexport
        original_item = proto_quickexport.batch_export_items[proto_quickexport.batch_export_items_index]
        
        proto_quickexport.batch_export_items.add()
        new_index = len(proto_quickexport.batch_export_items) - 1
        proto_quickexport.batch_export_items[new_index].copy_from(original_item)
        proto_quickexport.batch_export_items[new_index].export_properties.batch_export_item_index = new_index
        
        # Make name unique
        split_name = get_object_name_split(proto_quickexport.batch_export_items[new_index].name)
        proto_quickexport.batch_export_items[new_index].name = get_new_export_item_name(context, split_name[0], new_index)
        
        proto_quickexport.batch_export_items_index = new_index
        return {'FINISHED'}


class ProtoTools_MoveBatchExportItem(bpy.types.Operator):
    """Moves selected Export Item up/down in the list"""
    bl_idname = "prototools.move_batch_export_item"
    bl_label = "Move Export Item"
    bl_options = {'UNDO'}
    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),))
    
    @classmethod
    def poll(cls, context):
        proto_quickexport = context.scene.proto_quickexport
        if len(proto_quickexport.batch_export_items) <= 1:
            return False
        if proto_quickexport.batch_export_items_index < 0 or proto_quickexport.batch_export_items_index > len(proto_quickexport.batch_export_items) - 1:
            return False
        return True
    
    def execute(self, context):
        proto_quickexport = context.scene.proto_quickexport
        
        # Make sure this is a valid move
        if self.direction == 'UP' and proto_quickexport.batch_export_items_index <= 0:
            return {'CANCELLED'}
        elif self.direction == 'DOWN' and proto_quickexport.batch_export_items_index >= len(proto_quickexport.batch_export_items) - 1:
            return {'CANCELLED'}
        
        index = proto_quickexport.batch_export_items_index
        other_index = index-1 if self.direction == 'UP' else index+1
        
        proto_quickexport.batch_export_items.move(other_index, index)
        proto_quickexport.batch_export_items[other_index].export_properties.batch_export_item_index = other_index
        proto_quickexport.batch_export_items[index].export_properties.batch_export_item_index = index
        
        proto_quickexport.batch_export_items_index = other_index # select original entry in moved spot
        return {'FINISHED'}


class ProtoTools_AddExportObject(bpy.types.Operator):
    """Add new Export Object entry, or add selected Objects if there is an active selection"""
    bl_idname = "prototools.add_export_object"
    bl_label = "Add Export Object"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        batch_export_item = get_current_selected_batch_export_item(context)
        if batch_export_item == None:
            return
        
        # try and add selected meshes as entries
        valid_selection = False
        if bpy.context.view_layer.objects.active != None:
            valid_selection = True
            active_ob = bpy.context.view_layer.objects.active
            other_obs = []
            for ob in bpy.context.selected_objects:
                if ob.name != active_ob.name:
                    other_obs.append(ob)
            
            batch_export_item.export_objects.add()
            new_index = len(batch_export_item.export_objects) - 1
            batch_export_item.export_objects[new_index].pointer = active_ob
            batch_export_item.export_objects_index = new_index
            for ob in other_obs:
                batch_export_item.export_objects.add()
                new_index = len(batch_export_item.export_objects) - 1
                batch_export_item.export_objects[new_index].pointer = ob
        
        if not valid_selection:
            # add one blank entry
            batch_export_item.export_objects.add()
            new_index = len(batch_export_item.export_objects) - 1
            batch_export_item.export_objects_index = new_index
        return {'FINISHED'}


class ProtoTools_RemoveExportObject(bpy.types.Operator):
    """Remove current selected Export Object entry\n\nNote: will not delete the Object in the scene"""
    bl_idname = "prototools.remove_export_object"
    bl_label = "Remove Export Object"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        batch_export_item = get_current_selected_batch_export_item(context)
        if batch_export_item == None:
            return False
        if len(batch_export_item.export_objects) == 0:
            return False
        return True
    
    def execute(self, context):
        batch_export_item = get_current_selected_batch_export_item(context)
        index = batch_export_item.export_objects_index
        
        batch_export_item.export_objects.remove(index)
        
        # Select the entry that was above the one we deleted
        batch_export_item.export_objects_index = max(0,min(index - 1,len(batch_export_item.export_objects) - 1))
        return {'FINISHED'}


class ProtoTools_MoveExportObject(bpy.types.Operator):
    """Moves selected Export Object entry up/down in the list"""
    bl_idname = "prototools.move_export_object"
    bl_label = "Move Export Object"
    bl_options = {'UNDO'}
    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),))
    
    @classmethod
    def poll(cls, context):
        batch_export_item = get_current_selected_batch_export_item(context)
        if batch_export_item == None:
            return
        if len(batch_export_item.export_objects) <= 1:
            return False
        if batch_export_item.export_objects_index < 0 or batch_export_item.export_objects_index > len(batch_export_item.export_objects) - 1:
            return False
        return True
    
    def execute(self, context):
        batch_export_item = get_current_selected_batch_export_item(context)
        
        # Make sure this is a valid move
        if self.direction == 'UP' and batch_export_item.export_objects_index <= 0:
            return {'CANCELLED'}
        elif self.direction == 'DOWN' and batch_export_item.export_objects_index >= len(batch_export_item.export_objects) - 1:
            return {'CANCELLED'}
        
        index = batch_export_item.export_objects_index
        other_index = index-1 if self.direction == 'UP' else index+1
        
        batch_export_item.export_objects.move(other_index, index)
        batch_export_item.export_objects_index = other_index
        return {'FINISHED'}


class ProtoTools_SelectExportObjects(bpy.types.Operator):
    """Select all Export Objects in the list"""
    bl_idname = "prototools.select_export_objects"
    bl_label = "Select All"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        batch_export_item = get_current_selected_batch_export_item(context)
        if batch_export_item == None:
            return False
        if len(batch_export_item.export_objects) == 0:
            return False
        return True
    
    def execute(self, context):
        batch_export_item = get_current_selected_batch_export_item(context)
        
        # Don't deselect? I think the standard convention is to add to current selection
        #bpy.ops.object.select_all(action='DESELECT')
        
        skipped_any_meshes = False
        for ob_entry in batch_export_item.export_objects:
            if ob_entry.pointer in context.selectable_objects:
                ob_entry.pointer.select_set(state=True)
            else:
                skipped_any_meshes = True
        
        if batch_export_item.export_objects[0].pointer in context.selectable_objects:
            bpy.context.view_layer.objects.active = batch_export_item.export_objects[0].pointer
        
        # Warn if any selection was skipped due to being out of the view layer
        if skipped_any_meshes:
            bpy.ops.prototools.infopopup('INVOKE_DEFAULT', title="Info", text="Some meshes could not be selected (not in the view layer?)", icon='INFO')
        
        return {'FINISHED'}


class ProtoTools_DeselectExportObjects(bpy.types.Operator):
    """Deselect all Export Objects in the list"""
    bl_idname = "prototools.deselect_export_objects"
    bl_label = "Deselect All"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        batch_export_item = get_current_selected_batch_export_item(context)
        if batch_export_item == None:
            return False
        if len(batch_export_item.export_objects) == 0:
            return False
        return True
    
    def execute(self, context):
        batch_export_item = get_current_selected_batch_export_item(context)
        
        for ob_entry in batch_export_item.export_objects:
            ob_entry.pointer.select_set(state=False)
            if ob_entry.pointer == bpy.context.view_layer.objects.active:
                bpy.context.view_layer.objects.active = None
        return {'FINISHED'}



operator_classes = (
    ProtoTools_BatchExport,
    ProtoTools_AddBatchExportItem,
    ProtoTools_RemoveBatchExportItem,
    ProtoTools_DuplicateBatchExportItem,
    ProtoTools_MoveBatchExportItem,
    
    ProtoTools_AddExportObject,
    ProtoTools_RemoveExportObject,
    ProtoTools_MoveExportObject,
    ProtoTools_SelectExportObjects,
    ProtoTools_DeselectExportObjects,
)


def register():
    for operator in operator_classes:
        bpy.utils.register_class(operator)


def unregister():
    for operator in operator_classes:
        bpy.utils.unregister_class(operator)

