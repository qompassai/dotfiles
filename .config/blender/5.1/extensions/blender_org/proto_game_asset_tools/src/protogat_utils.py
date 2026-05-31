# PROTO Tools Operators
# 2026 PROTOWLF, Licensed under GPL-3.0


import bpy
from bpy.types import(
    LayerCollection
)


# Get the current selected (i.e. highlighted) Batch Export Item, regardless of Multi-Selections
# Returns None if not in Batch mode, or if none exist / are selected
def get_current_selected_batch_export_item(context):
    proto_quickexport = context.scene.proto_quickexport
    
    if proto_quickexport.quick_export_mode == "BatchExport":
        if len(proto_quickexport.batch_export_items) > 0:
            if proto_quickexport.batch_export_items_index >= 0 and proto_quickexport.batch_export_items_index <  len(proto_quickexport.batch_export_items):
                return proto_quickexport.batch_export_items[proto_quickexport.batch_export_items_index]
    
    return None


# Get list of current multi-selected Batch Export Items, and list of their indices in the Export Item Collection
# If user has no items checked, the current selected one in the list is returned
# If user has at least 1 item checked, that is the list that will be returned
def get_current_multi_selected_batch_export_items(context):
    proto_quickexport = context.scene.proto_quickexport
    num_items = len(proto_quickexport.batch_export_items)
    if num_items == 0:
        return [], []
    
    # Get list of checked item (as in, user checked the checkbox next to them)
    checked_items = []
    checked_items_indices = []
    for i, item in enumerate(proto_quickexport.batch_export_items):
        if item.multi_selected:
            checked_items.append(item)
            checked_items_indices.append(i)
    
    if len(checked_items) > 0:
        return checked_items, checked_items_indices
    elif proto_quickexport.batch_export_items_index >= 0 and proto_quickexport.batch_export_items_index < num_items:
        return [proto_quickexport.batch_export_items[proto_quickexport.batch_export_items_index]], [proto_quickexport.batch_export_items_index]
    
    return [], []


def get_current_quick_export_properties(context):
    proto_quickexport = context.scene.proto_quickexport
    
    if proto_quickexport.quick_export_mode == "ExportSelected":
        return proto_quickexport.export_selected_properties
    else:
        current_batch_export_item = get_current_selected_batch_export_item(context)
        if current_batch_export_item != None:
            return current_batch_export_item.export_properties
    
    return None


def get_batch_export_properties_by_index(context, batch_export_index):
    proto_quickexport = context.scene.proto_quickexport
    
    if batch_export_index < 0 or batch_export_index >= len(proto_quickexport.batch_export_items):
        return None
    
    return proto_quickexport.batch_export_items[batch_export_index].export_properties


# Special rsplit that detects a '.001' style suffix
def get_object_name_split(full_name):
    final_split = []
    split_name = full_name.rsplit(".", 1)
    if len(split_name) > 1 and split_name[1].isdigit():
        final_split = split_name
    else:
        final_split.append(full_name)
    return final_split


# Get new name of export item, will add '.001' style suffixes on duplicate names
def get_new_export_item_name(context, base_name, skip_index):
    proto_quickexport = context.scene.proto_quickexport
    cur_number = 0
    for i, item in enumerate(proto_quickexport.batch_export_items):
        if i == skip_index:
            continue
        split_name = get_object_name_split(item.name)
        if split_name[0] == base_name:
            if len(split_name) > 1 and split_name[1].isdigit():
                cur_number = max(cur_number, int(split_name[1]) + 1)
            else:
                cur_number = max(cur_number, 1)
    if cur_number > 0:
        return base_name + "." + str(cur_number).zfill(3)
    return base_name


def validate_batch_export_object(context, batch_export_item, export_object, errors):
    if export_object.pointer == None:
        errors.append("Undefined Object in export's Object list. Remove this entry from list")
        return False
    if context.scene.objects.get(export_object.pointer.name) == None:
        # This means the object was deleted from the scene, while it was entered as an export object.
        # The Object List keeps the object's reference counter alive, preventing it from being removed
        # from the file.
        # We don't have a way to detect object deletion, so we catch it here and remove it from the
        # properties for the user, but still throw an error for them
        errors.append("Object '" + export_object.pointer.name + "' in export's Object list was deleted from the scene. Remove this entry from list")
        return False
    return True


# Retrun if the given batch export item is set up correctly for export
# Write errors for the user if not
def validate_batch_export_item(context, batch_export_item):
    export_properties = batch_export_item.export_properties
    errors = []
    
    if batch_export_item.batch_export_item_mode == "ModelAndAnimations" or batch_export_item.batch_export_item_mode == "Model":
        # Validate filepath (with file name)
        if export_properties.model_path == "" or export_properties.model_path == "/":
            errors.append("Set an export filepath")
        elif export_properties.model_path[-1] == '/' or export_properties.model_path[-1] == '\\':
            errors.append("Must specify a file name")
        
        # Must have objects
        if batch_export_item.export_objects == None or len(batch_export_item.export_objects) == 0:
            errors.append("Add Objects to export")
        else:
            found_mesh = False
            num_armatures = 0
            armature = None
            for export_object in batch_export_item.export_objects:
                if validate_batch_export_object(context, batch_export_item, export_object, errors):
                    if export_object.pointer.type == "MESH":
                        found_mesh = True
                    elif export_object.pointer.type == "ARMATURE":
                        num_armatures += 1
                        armature = export_object.pointer
            if found_mesh == False:
                errors.append("No Meshes in export")
            if num_armatures > 1:
                errors.append("Multiple Armatures in export, maximum 1 allowed")
            
            # Make sure armature has bones (if we're exporting one)
            if armature != None and (armature.pose == None or len(armature.pose.bones) == 0):
                errors.append("Invalid Armature in export - no bones")
    
    elif batch_export_item.batch_export_item_mode == "Animations":
        # We use a different path property with one_file_per_action
        filepath = export_properties.all_anims_path
        filepath_folder = export_properties.anim_folder_path
        
        # Validate file / folder
        if export_properties.one_file_per_action:
            if filepath_folder == "" or filepath_folder == "/":
                errors.append("Set an export path")
            if filepath_folder[-1] != '/' and filepath_folder[-1] != '\\': # Should be a path to a folder
                errors.append("Must specify a folder name")
        else:
            if filepath == "" or filepath == "/":
                errors.append("Set an export path")
            if filepath[-1] == '/' or filepath[-1] == '\\': # Should be a path to a file
                errors.append("Must specify a file name")
        
        # Must have objects
        if batch_export_item.export_objects == None or len(batch_export_item.export_objects) == 0:
            errors.append("Add Objects to export")
        else:
            # Cannot select multiple objects
            if len(batch_export_item.export_objects) > 1:
                errors.append("Must export 1 Armature only")
            else:
                # Must have exactly 1 armature selected
                armature = None
                for export_object in batch_export_item.export_objects:
                    if validate_batch_export_object(context, batch_export_item, export_object, errors):
                        if export_object.pointer.type == 'ARMATURE':
                            if armature != None:
                                errors.append("Multiple Armatures in export, maximum 1 allowed")
                            armature = export_object.pointer
                if armature == None:
                    errors.append("Must export 1 Armature")
                
                # Make sure armature has bones
                if armature.pose == None or len(armature.pose.bones) == 0:
                    errors.append("Invalid Armature in export - no bones")
    
    return errors


# returns dictionary of objects to original names
#def duplicate_and_rename_export_objects(self, context, batch_export_item):
#    duplicate_objects = []
#    objects_to_original_names = {}
#    
#    # iterate through all to get final names, to see if any match
#    # * if so, we need to copy data so that we can join duplicates
#    final_name_and_types = {} # name, object type
#    final_names = []
#    do_duplicate_data = False
#    for export_object in batch_export_item.export_objects:
#        final_name = export_object.pointer.name
#        if export_object.pointer.type == "MESH" and export_object.rename_name != "" and not export_object.rename_name.isspace():
#            final_name = export_object.rename_name
#        
#        if final_name in final_name_and_types:
#            if final_name_and_types[final_name] != "MESH" or export_object.pointer.type != "MESH":
#                # ERROR: can only join meshes together!
#                self.report({'ERROR'}, "Invalid Object re-naming - Mesh re-named to same name as a non-Mesh Object. Can only join Meshes.")
#                return None, None
#            do_duplicate_data = True
#        
#        final_names.append(final_name)
#        final_name_and_types[final_name] = export_object.pointer.type
#    
#    do_duplicate_data = True
#    
#    # iterate, perform duplication
#    for i, export_object in enumerate(batch_export_item.export_objects):
#        # duplicate object
#        duplicate_object = None
#        if do_duplicate_data:
#            # duplicate object and data
#            duplicate_object = export_object.pointer.copy()
#            if export_object.pointer.type != 'EMPTY':
#                duplicate_object.data = export_object.pointer.data.copy()
#        else:
#            # duplicate object, NOT data
#            duplicate_object = export_object.pointer.copy()
#        bpy.context.scene.collection.objects.link(duplicate_object)
#        
#        # perform renaming, add to duplicate_objects
#        other_ob = context.scene.objects.get(final_names[i])
#        if other_ob != None:
#            if other_ob in duplicate_objects: # other_ob in [entry.pointer for entry in batch_export_item.export_objects]
#                # Same name as another export object, join into that one
#                bpy.ops.object.select_all(action='DESELECT')
#                bpy.context.view_layer.objects.active = other_ob
#                other_ob.select_set(state=True)
#                duplicate_object.select_set(state=True)
#                bpy.ops.object.join()
#            else:
#                # Give temp name to other object
#                objects_to_original_names[other_ob] = other_ob.name
#                other_ob.name = other_ob.name + "_BATCHTEMPNAME"
#                
#                # Rename duplicate
#                duplicate_object.name = final_names[i]
#                
#                # Add to duplicate_objects
#                duplicate_objects.append(duplicate_object)
#    
#    return duplicate_objects, objects_to_original_names, do_duplicate_data


class CollectionVisibilityInfo():
    originally_excluded: bool
    layer_collection: LayerCollection
    
    def __init__(self, originally_excluded = False, layer_collection = None):
        self.originally_excluded = originally_excluded
        self.layer_collection = layer_collection


# Forces collection of given name to be visible in view layer (if it's not already),
# Returns a struct of data to pass into restore_collection_visibility(), and a bool for success (if bool is False, collection was not found)
def ensure_collection_visible(layer_collection):
    info = CollectionVisibilityInfo()
    if layer_collection == None:
        info.originally_excluded = False
        return info, False
    
    info.layer_collection = layer_collection
    info.originally_excluded = layer_collection.exclude
    layer_collection.exclude = False
    return info, True


def restore_collection_visibility(collection_visibility_info):
    if collection_visibility_info.originally_excluded:
        collection_visibility_info.layer_collection.exclude = True


