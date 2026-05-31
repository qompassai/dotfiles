# PROTO FBX Export Utils
# 2026 PROTOWLF, Licensed under GPL-3.0
# Some code from Blender v4.2.3 fbx_utils.py, export_fbx_bin.py
#
# Utility functions doing the heavy-lifting of the PROTO FBX export wrapper


import bpy
from bpy.props import (
    StringProperty
)

import bmesh
import mathutils
from mathutils import Matrix, Vector
from math import radians
from . import proto_export_fbx_bin
from bpy_extras.object_utils import AddObjectHelper, object_data_add

addon_package_name = __package__
addon_package_name = addon_package_name.removesuffix(".src.fbx_export")


# From Blender v4.2.3 fbx_utils.py
def ensure_object_not_in_edit_mode(context, obj):
    """Objects in Edit mode usually cannot be exported because much of the API used when exporting is not available for
    Objects in Edit mode.

    Exiting the currently active Object (and any other Objects opened in multi-editing) from Edit mode is simple and
    should be done with `bpy.ops.mesh.mode_set(mode='OBJECT')` instead of using this function.

    This function is for the rare case where an Object is in Edit mode, but the current context mode is not Edit mode.
    This can occur from a state where the current context mode is Edit mode, but then the active Object of the current
    View Layer is changed to a different Object that is not in Edit mode. This changes the current context mode, but
    leaves the other Object(s) in Edit mode.
    """
    if obj.mode != 'EDIT':
        return True

    # Get the active View Layer.
    view_layer = context.view_layer

    # A View Layer belongs to a scene.
    scene = view_layer.id_data

    # Get the current active Object of this View Layer, so we can restore it once done.
    orig_active = view_layer.objects.active

    # Check if obj is in the View Layer. If obj is not in the View Layer, it cannot be set as the active Object.
    # We don't use `obj.name in view_layer.objects` because an Object from a Library could have the same name.
    is_in_view_layer = any(o == obj for o in view_layer.objects)

    do_unlink_from_scene_collection = False
    try:
        if not is_in_view_layer:
            # There might not be any enabled collections in the View Layer, so link obj into the Scene Collection
            # instead, which is always available to all View Layers of that Scene.
            scene.collection.objects.link(obj)
            do_unlink_from_scene_collection = True
        view_layer.objects.active = obj

        # Now we're finally ready to attempt to change obj's mode.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')
        if obj.mode == 'EDIT':
            # The Object could not be set out of EDIT mode and therefore cannot be exported.
            return False
    finally:
        # Always restore the original active Object and unlink obj from the Scene Collection if it had to be linked.
        view_layer.objects.active = orig_active
        if do_unlink_from_scene_collection:
            scene.collection.objects.unlink(obj)

    return True


#def refresh_action_filter(proto_quickexport):
#    # Remove entries for actions that no longer exist
#    for i, entry in enumerate(proto_quickexport.action_filter):
#        if entry.action is None:
#            proto_quickexport.action_filter.remove(i)
#    
#    # Add entries for new actions
#    for action in bpy.data.actions:
#        if id(action) not in [id(item.action) for item in proto_quickexport.action_filter]:
#            item = proto_quickexport.action_filter.add()
#            item.action = action
#            item.keep = True


def refresh_action_filter(action_filter):
    # Remove entries for actions that no longer exist
    for i, entry in enumerate(action_filter):
        if entry.action is None:
            action_filter.remove(i)
    
    # Add entries for new actions
    for action in bpy.data.actions:
        if id(action) not in [id(item.action) for item in action_filter]:
            item = action_filter.add()
            item.action = action
            item.keep = True


def do_bone_warning(self, option_names, bone_name, warning_str):
        final_str = ""
        if len(option_names) > 0:
            final_str += option_names[0]
            for option_name in option_names[1:]:
                final_str += ", " + option_name
            final_str += " - "
        
        final_str += "'" + bone_name + "' - " + warning_str
        self.warnings.append(final_str)


def get_action_filepath(context, folderpath, action_name, action_name_style, action_name_sharedname):
    if action_name_style == "Action":
        return folderpath + action_name + ".fbx"
    if action_name_style == "Name_Action":
        return folderpath + action_name_sharedname + "_" + action_name + ".fbx"
    if action_name_style == "Name-Action":
        return folderpath + action_name_sharedname + "-" + action_name + ".fbx"
    if action_name_style == "Name@Action":
        return folderpath + action_name_sharedname + "@" + action_name + ".fbx"


# Adapted from Blender v4.2.3 export_fbx_bin.py save()
def get_export_objects(context, use_selection=False, use_visible=False, use_active_collection=False, collection="", export_object_list=[]):
    """
    Get the objects the user wishes to export
    """
    
    object_list = []
    
    if len(export_object_list) > 0:
        # use export list instead of current selection
        for entry in export_object_list:
            object_list.append(bpy.data.objects[entry.name])
            
    else:
        # Standard exporter object selection
        source_collection = None
        if use_active_collection:
            source_collection = context.view_layer.active_layer_collection.collection
        elif collection:
            local_collection = bpy.data.collections.get((collection, None))
            if local_collection:
                source_collection = local_collection
            else:
                operator.report({'ERROR'}, "Collection '%s' was not found" % collection)
                empty = []
                return empty
    
        if source_collection:
            if use_selection:
                ctx_objects = tuple(obj for obj in source_collection.all_objects if obj.select_get())
            else:
                ctx_objects = source_collection.all_objects
        else:
            if use_selection:
                ctx_objects = context.selected_objects
            else:
                ctx_objects = context.view_layer.objects
        if use_visible:
            ctx_objects = tuple(obj for obj in ctx_objects if obj.visible_get())
        
        for obj in tuple(ctx_objects):
            object_list.append(obj)
    
    # Ensure no Objects are in Edit mode.
    # Copy to a tuple for safety, to avoid the risk of modifying ctx_objects while iterating.
    # Also copy these to a list because we want to return a list not a tuple
    final_list = []
    for obj in object_list:
        if not ensure_object_not_in_edit_mode(context, obj):
            operator.report({'ERROR'}, "%s could not be set out of Edit Mode, so cannot be exported" % obj.name)
            empty = []
            return empty
        final_list.append(obj)

    return final_list


def get_actions_for_armature(armature, original_armature_name, do_armature_slot_name_filter, action_names_whitelist=list()):
    settings = bpy.context.preferences.addons[addon_package_name].preferences
    
    # Detect all actions that manipulate this armature
    # NOTE: This is not a perfect solution -- in the future maybe have the user specify which actions to export
    actions = []
    
    if bpy.app.version < (4, 4, 0):
        # Pre-Action-Slots version
        # Peek into the fcurve data of each action, to see if we find a bone in our armature
        for action in bpy.data.actions:
            valid_action = False
            for fcurve in action.fcurves:
                if fcurve.data_path.startswith("pose.bones"):
                    bone_name = fcurve.group.name
                    if bone_name in armature.pose.bones:
                        valid_action = True
                    break
            if valid_action:
                if len(action_names_whitelist) > 0:
                    if action.name in action_names_whitelist:
                        actions.append(action)
                else:
                    actions.append(action)
    else:
        # Peek into the fcurve data of each action, to see if we find a bone in our armature
        for action in bpy.data.actions:
            valid_action = False
            for layer in action.layers:
                for strip in layer.strips:
                    for slot in action.slots:
                        channelbag = strip.channelbag(slot)
                        if channelbag != None:
                            for fcurve in channelbag.fcurves:
                                if fcurve.data_path.startswith("pose.bones"):
                                    bone_name = fcurve.group.name
                                    if bone_name in armature.pose.bones:
                                        valid_action = True
                                    break
                        
                        if valid_action and do_armature_slot_name_filter and settings.action_slot_behavior == "ARMATURE_NAME":
                            # Ensure the slot matches the name of the armature object
                            if slot.name_display != original_armature_name:
                                valid_action = False
                        
                        if valid_action:
                            if len(action_names_whitelist) > 0:
                                if action.name in action_names_whitelist:
                                    actions.append(action)
                            else:
                                actions.append(action)
    
    # use a set to remove duplicates
    return list(set(actions))


def find_slot_in_action_for_armature(action, armature):
    settings = bpy.context.preferences.addons[addon_package_name].preferences
    
    # Peek into the fcurve data of each action, to see if we find a bone in our armature
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                channelbag = strip.channelbag(slot)
                if channelbag != None:
                    for fcurve in channelbag.fcurves:
                        if fcurve.data_path.startswith("pose.bones"):
                            bone_name = fcurve.group.name
                            if bone_name in armature.pose.bones:
                                return slot
    
    return None
    
    
def action_has_slot_with_name(action, slot_name):
    found_slot = False
    for slot in action.slots:
        if slot.name_display == slot_name:
            found_slot = True
            break;
    return found_slot


def select_objects_for_export(context, final_export_objects):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in final_export_objects:
        bpy.context.view_layer.objects.active = ob
        ob.select_set(state=True)


def get_meshes_for_armatures(context, armatures):
    # Get all meshes deformed by armatures
    armature_objects = []
    for ob in bpy.context.view_layer.objects:
        if ob.type == 'MESH':
            for armature in armatures:
                #print("Object " + ob.name + " has shapekeys")
                #print("armature.name: " + armature.name)
                if ob.parent == armature: # Get this mesh if its parent is the armature
                    #print("Object " + ob.name + " considered for shapekey anim export")
                    armature_objects.append(ob)
                else: # Or if it uses the armature with a modifier
                    for modifier in ob.modifiers:
                        if modifier.type == 'ARMATURE' and modifier.object.name == armature.name:
                            #print("Object " + ob.name + " considered for shapekey anim export")
                            armature_objects.append(ob)
    
    return armature_objects


def get_shapekey_objects_to_duplicate_from_armature_meshes(context, armature_meshes, original_export_objects):
    extra_objects = []
    for ob in armature_meshes:
        if ob.data.shape_keys != None and ob not in original_export_objects:
            extra_objects.append(ob)
    
    return extra_objects


def duplicate_export_objects(self, context, export_objects_to_duplicate, export_objects_to_shapekey_dummy, non_export_objects_to_duplicate, armature_export_name, export_object_list):
    """
    Duplicate objects the user wishes to export, and associate duplicate meshes with any appropriate duplicate armatures
    export_objects_to_duplicate - objects to be included in the export (minus those in export_objects_to_shapekey_dummy)
    export_objects_to_shapekey_dummy - objects to be included in the export, but be turned into a shapekey dummy mesh
    non_export_objects_to_duplicate - objects not included in the export
    """
    
    duplicate_objects = []
    mesh_objects = []
    original_to_duplicate_armatures = {}
    renamed_objects = {}
    duplicate_armatures = []
    armature_original_names = []
    final_export_objects = []
    
    all_objects_to_duplicate = list(export_objects_to_duplicate + export_objects_to_shapekey_dummy + non_export_objects_to_duplicate)
    
    for ob in all_objects_to_duplicate:
        # duplicate object
        duplicate_object = ob.copy()
        if ob.type != 'EMPTY':
            duplicate_object.data = ob.data.copy()
        
        # link duplicate to root scene collection (we know it won't be a linked collection!)
        context.scene.collection.objects.link(duplicate_object)
        context.view_layer.update()
        
        # Select duplicate
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = duplicate_object
        duplicate_object.select_set(state=True)
        
        # Cache mapping between original/duplicate armatures
        # Make duplicate armatures local (if linked)
        if ob.type == 'ARMATURE':
            duplicate_armatures.append(duplicate_object)
            armature_original_names.append(ob.name)
            original_to_duplicate_armatures[ob] = duplicate_object
            if duplicate_object.library != None or duplicate_object.override_library != None:
                bpy.ops.object.make_local(type='SELECT_OBDATA')
        
        duplicate_objects.append(duplicate_object)
        
        # For mesh objects, if linked, make the object and its data local
        # NOTE: I was actually able to modify drivers of a library-override object without making them
        # local, which is weird... keeping this here anyway just in-case
        if ob.type == 'MESH':
            mesh_objects.append(duplicate_object)
            if duplicate_object.library != None or duplicate_object.override_library != None:
                bpy.ops.object.make_local(type='SELECT_OBDATA')
        
        # Add to export list (if appropriate)
        if ob in export_objects_to_duplicate or ob in export_objects_to_shapekey_dummy:
            final_export_objects.append(duplicate_object)
        
        # Prepare dummy meshes
        if ob in export_objects_to_shapekey_dummy:
            # Clear geometry and set it to a dummy quad
            scale = 0.01
            verts = [mathutils.Vector((-1 * scale, 1 * scale, 0)),
                     mathutils.Vector((-1 * scale, -1 * scale, 0)),
                     mathutils.Vector((1 * scale, -1 * scale, 0)),
                     mathutils.Vector((1 * scale, 1 * scale, 0)),]
            bm = bmesh.new()
            bm.from_mesh(duplicate_object.data)
            bm.clear()
            for v in verts:
                bm.verts.new(v)
            bm.faces.new(bm.verts)
            
            # Validate bmesh data structures
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            deform_layer = bm.verts.layers.deform.verify()
            
            # Skin the vertices to bones in the armature (if skin information exists)
            # We just need it to be skinned at all, but it's hard to tell what Vertex Groups
            # are actually associated with the armature, so just weight all of them
            for v in bm.verts:
                for vertex_group in duplicate_object.vertex_groups:
                    v[deform_layer][vertex_group.index] = 1.0
            
            bm.to_mesh(duplicate_object.data)
            bm.free()
            
            # Add UVs
            bpy.ops.mesh.uv_texture_add()
            
            # Remove Materials
            if bpy.app.version >= (5, 0, 0):
                bpy.ops.object.material_slot_remove_all()
            else:
                num_material_slots = len(ob.material_slots)
                if num_material_slots > 0:
                    ob.active_material_index = 0
                    for i in range(num_material_slots):
                        bpy.ops.object.material_slot_remove()
                    
    
    # Rename objects
    # Original objects get a temp name (will be renamed later)
    dupe_names = []
    for i, original_object in enumerate(all_objects_to_duplicate):
        original_name = original_object.name
        
        # Get final name for dupe (user may have specified a rename name in export_object_list)
        dupe_name = original_name
        for entry in export_object_list:
            if original_name == entry.name and entry.rename_name != "" and not entry.rename_name.isspace():
                dupe_name = entry.rename_name
        if dupe_name in dupe_names:
            # Warn user about name collision
            self.warnings.append("Multiple export objects with name '" + dupe_name + "', names will not be accurate in export! Name collision caused by renaming Export Objects in Batch Export")
        dupe_names.append(dupe_name)
        
        # Give temp name to object that already has our dupe_name name (if one exists), and cache it for cleanup later
        object_with_dupe_name = bpy.data.objects.get(dupe_name)
        if object_with_dupe_name != None:
            object_with_dupe_name.name = dupe_name + "_temp"
            renamed_objects[object_with_dupe_name] = dupe_name
        
        duplicate_objects[i].name = dupe_name
    
    # Rename armature (if user specified an override)
    # (This dictionary will only ever be 0 or 1 long, but might as well lay groundwork for eventually supporting multiple armatures)
    if not armature_export_name == "" and not armature_export_name.isspace():
        for original_armature, duplicate_armature in original_to_duplicate_armatures.items():
            duplicate_armature.name = armature_export_name
    
    # Associate duplicate meshes with duplicate armatures
    for mesh_ob in mesh_objects:
        # re-parent
        if mesh_ob.parent in original_to_duplicate_armatures:
            #print( "re-parenting dupe object " + mesh_ob.name + " from " + mesh_ob.parent.name + " to " + original_to_duplicate_armatures[mesh_ob.parent].name)
            # Transform gets messed up when mesh is parented to a bone, so cache and reset it
            cached_world_transform = mesh_ob.matrix_world
            mesh_ob.parent = original_to_duplicate_armatures[mesh_ob.parent]
            mesh_ob.matrix_world = cached_world_transform
        
        # re-associate armature modifier
        for mod in mesh_ob.modifiers:
            if mod.type != 'ARMATURE':
                continue
            if mod.object == None:
                continue
            if mod.object in original_to_duplicate_armatures:
                #print( "re-associating armature modifier for " + mesh_ob.name + " from " + mod.object.name + " to " + original_to_duplicate_armatures[mod.object].name)
                mod.object = original_to_duplicate_armatures[mod.object]
        
        # Shapekey drivers - re-map drivers driven by the armature
        shape_keys = mesh_ob.data.shape_keys
        if shape_keys != None and shape_keys.animation_data != None and shape_keys.animation_data.drivers != None:
            drivers = shape_keys.animation_data.drivers
            for driver_fcurve in drivers:
                # re-map vars using the armature
                for var in driver_fcurve.driver.variables:
                    for target in var.targets:
                        for original_armature, duplicate_armature in original_to_duplicate_armatures.items():
                            if target.id == original_armature.id_data:
                                target.id = duplicate_armature.id_data
        
        
        
    # Update dependencies
    #depsgraph.update()
    context.evaluated_depsgraph_get().update()
        
    return duplicate_objects, renamed_objects, duplicate_armatures, armature_original_names, final_export_objects


def create_dummy_shapekey_meshes(context, armature, final_export_objects):
    """
    Create a tiny dummy mesh (for export) that has all the shapekeys present on the given armature's deformed meshes
    final_export_objects - make sure we don't create a dummy of an object already included in the export
    NOTE: we run get_meshes_with_shapekeys_for_armature again here on purpose, because we probably have duplicate objects
    """
    scale = 0.01
    verts = [mathutils.Vector((-1 * scale, 1 * scale, 0)),
             mathutils.Vector((-1 * scale, -1 * scale, 0)),
             mathutils.Vector((1 * scale, -1 * scale, 0)),
             mathutils.Vector((1 * scale, 1 * scale, 0)),]
    edges = []
    faces = [[0, 1, 2, 3]]
    
    dummy_meshes = []
    
    objects = proto_export_fbx_bin.get_meshes_with_shapekeys_for_armature(armature)
    for ob in objects:
        # Don't create dummy of object already in export
        if ob in final_export_objects:
            continue
        
        # Don't create dummy if object doesn't really have shapekeys
        # (must have at least 2 entries, because 1st entry is basis)
        if ob.data.shape_keys == None or len(ob.data.shape_keys.key_blocks) <= 1:
            continue
        
        ## duplicate object
        #duplicate_object = ob.copy()
        #duplicate_object.data = ob.data.copy()
        #
        ## Rename new object to name of original
        #original_name = ob.name
        #ob.name = original_name + "_temp"
        #duplicate_object.name = original_name
        #
        ## link duplicate to root scene collection (we know it won't be a linked collection!)
        #bpy.context.scene.collection.objects.link(duplicate_object)
        #bpy.context.view_layer.update()
        #
        ## Clear geometry and set it to a dummy quad
        #bm = bmesh.new()
        #bm.from_mesh(duplicate_object.data)
        #bm.clear()
        #for v in verts:
        #    bm.verts.new(v)
        #bm.faces.new(bm.verts)
        #bm.to_mesh(duplicate_object.data)
        #bm.free()
        
        
        
        ## Make new object
        #meshdata = bpy.data.meshes.new(name="tempname")
        #meshdata.from_pydata(verts, edges, faces)
        #new_ob = object_data_add(context, meshdata, operator=None, name="tempname")
        #
        ## Rename new object to name of duplicate
        ## Original objects get a temp name (will be renamed later)
        #original_name = ob.name
        #ob.name = original_name + "_temp"
        #new_ob.name = original_name
        #
        ## Select new object
        #bpy.ops.object.select_all(action='DESELECT')
        #bpy.context.view_layer.objects.active = new_ob
        #new_ob.select_set(state=True)
        #
        ## Add first shapekey entry (basis)
        #bpy.ops.object.shape_key_add(from_mix=False)
        #
        ## Copy over shape keys (names only)
        #for i, shape in enumerate(ob.data.shape_keys.key_blocks[1:]): # skip the first shapekey (the basis)
        #    bpy.ops.object.shape_key_add(from_mix=False)
        #    new_ob.data.shape_keys.key_blocks[i].name = shape.name
        #
        ## Set parent to Armature
        #cached_world_transform = new_ob.matrix_world
        #new_ob.parent = armature
        #new_ob.matrix_world = cached_world_transform
        
        dummy_meshes.append(new_ob)
    
    return dummy_meshes


def force_scale_object(ob, unit_scale, transform, apply):
    # Select object
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(state=True)
    
    # unlock scale, in case it's locked
    ob.lock_scale[0] = False
    ob.lock_scale[1] = False
    ob.lock_scale[2] = False
    
    # disable drivers on transform
    disabled_drivers = []
    if ob.animation_data:
        for driver in ob.animation_data.drivers:
            if driver.data_path in ['location', 'rotation_euler', 'rotation_quaternion', 'scale']:
                if driver.mute == False:
                    driver.mute = True
                    disabled_drivers.append(driver)
    
    # disable constraints
    disabled_constraints = []
    for constraint in ob.constraints:
        if constraint.enabled:
            constraint.enabled = False
            disabled_constraints.append(constraint)
    
    if transform:
        # scale the object
        ob.location *= unit_scale
        ob.scale *= unit_scale
    
    if apply:
        # apply scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    bpy.context.evaluated_depsgraph_get().update()
    #return disabled_drivers, disabled_constraints
    
    # re-enable drivers on transform
    for driver in disabled_drivers:
        driver.mute = False
    
    # re-enable constraints
    for constraint in disabled_constraints:
        constraint.enabled = True


# rotate -90 in x, to account for FBX file forward
def force_fbx_rotate_object(ob, transform, apply):
    #print("force_fbx_rotate_object: " + ob.name)
    # Select object
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(state=True)
    
    # unlock rotation and location, in case it's locked
    ob.lock_rotation[0] = False
    ob.lock_rotation[1] = False
    ob.lock_rotation[2] = False
    ob.lock_location[0] = False
    ob.lock_location[1] = False
    ob.lock_location[2] = False
    
    # disable drivers on transform
    disabled_drivers = []
    if ob.animation_data:
        for driver in ob.animation_data.drivers:
            if driver.data_path in ['location', 'rotation_euler', 'rotation_quaternion', 'scale']:
                if driver.mute == False:
                    driver.mute = True
                    disabled_drivers.append(driver)
                    
    # disable constraints
    disabled_constraints = []
    for constraint in ob.constraints:
        if constraint.enabled:
            constraint.enabled = False
            disabled_constraints.append(constraint)
    
    # set object to XYZ rotation mode (save original mode
    original_rotation_mode = ob.rotation_mode
    if original_rotation_mode != 'XYZ':
        ob.rotation_mode = 'XYZ'
    
    if transform:
        # rotate the object
        ob.rotation_euler.x -= radians(90)
        
        # swizzle translation
        old_z = ob.location.z
        ob.location.z = ob.location.y * -1.0
        ob.location.y = old_z
    
    if apply:
        # apply rotation (NOT location)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    
    bpy.context.evaluated_depsgraph_get().update()
    #return disabled_drivers, disabled_constraints
    
    # re-enable drivers on transform
    for driver in disabled_drivers:
        driver.mute = False
    
    # re-enable constraints
    for constraint in disabled_constraints:
        constraint.enabled = True


# Scale scale/location keyframes on the root object (not bones)
def unit_scale_action(action, unit_scale):
    #print("unit_scale_action " + action.name)
    if bpy.app.version < (4, 4, 0):
        # Pre-Action-Slots version
        for fcurve in action.fcurves:
            if 'location' in fcurve.data_path:
                #print("scaling curve " + fcurve.data_path)
                for point in fcurve.keyframe_points:
                    point.co[1] *= unit_scale
                    point.handle_left[1] *= unit_scale
                    point.handle_right[1] *= unit_scale
    else:
        # Action-Slots version
        for layer in action.layers:
            for strip in layer.strips:
                # NOTE: we *could* only scale the slot that matches the armature, but maybe there are
                # cases where the other slots' animations matter for the armature's final pose?
                for slot in action.slots:
                    channelbag = strip.channelbag(slot)
                    if channelbag != None:
                        for fcurve in channelbag.fcurves:
                            if 'location' in fcurve.data_path:
                                for point in fcurve.keyframe_points:
                                    point.co[1] *= unit_scale
                                    point.handle_left[1] *= unit_scale
                                    point.handle_right[1] *= unit_scale


def unscale_action(action, unit_scale):
    if bpy.app.version < (4, 4, 0):
        # Pre-Action-Slots version
        for fcurve in action.fcurves:
            if 'location' in fcurve.data_path:
                for point in fcurve.keyframe_points:
                    point.co[1] *= 1.0 / unit_scale
                    point.handle_left[1] *= 1.0 / unit_scale
                    point.handle_right[1] *= 1.0 / unit_scale
    else:
        # Action-Slots version
        for layer in action.layers:
            for strip in layer.strips:
                # NOTE: we *could* only scale the slot that matches the armature, but maybe there are
                # cases where the other slots' animations matter for the armature's final pose?
                for slot in action.slots:
                    channelbag = strip.channelbag(slot)
                    if channelbag != None:
                        for fcurve in channelbag.fcurves:
                            if 'location' in fcurve.data_path:
                                for point in fcurve.keyframe_points:
                                    point.co[1] *= 1.0 / unit_scale
                                    point.handle_left[1] *= 1.0 / unit_scale
                                    point.handle_right[1] *= 1.0 / unit_scale


def transform_object_and_children(context, ob, unit_scale, bake_z_forward, remove_bone_rotation, object_children, only_apply, in_out_helper_armatures):
    if ob.type == 'ARMATURE':
        # for armatures, if we need to rotate, create a helper armature that is transformed without applying
        if bake_z_forward or remove_bone_rotation:
            helper_armature = ob.copy()
            helper_armature.data = ob.data.copy()
            context.scene.collection.objects.link(helper_armature)
            in_out_helper_armatures.append(helper_armature)
        
            if unit_scale != 1.0:
                force_scale_object(helper_armature, unit_scale, not only_apply, True)
        
            force_fbx_rotate_object(helper_armature, not only_apply, False)
    
    # this object
    if unit_scale != 1.0:
        force_scale_object(ob, unit_scale, not only_apply, True)
    if bake_z_forward:
        force_fbx_rotate_object(ob, not only_apply, True)
    
    # children
    if ob in object_children:
        for child in object_children[ob]:
            transform_object_and_children(context, child, unit_scale, bake_z_forward, remove_bone_rotation, object_children, True, in_out_helper_armatures)


def transform_object(context, ob, unit_scale, bake_z_forward, in_out_helper_armatures):
    if ob.type == 'ARMATURE':
        # for armatures, if we need to rotate, create a helper armature that is transformed without applying
        if bake_z_forward:
            helper_armature = ob.copy()
            helper_armature.data = ob.data.copy()
            context.scene.collection.objects.link(helper_armature)
            in_out_helper_armatures.append(helper_armature)
        
            if unit_scale != 1.0:
                force_scale_object(helper_armature, unit_scale, True, True)
        
            force_fbx_rotate_object(helper_armature, True, False)
    
    # this object
    if unit_scale != 1.0:
        force_scale_object(ob, unit_scale, True, True)
    if bake_z_forward:
        force_fbx_rotate_object(ob, True, True)


def transform_export_objects(self, context, unit_scale, bake_z_forward, remove_bone_rotation, move_to_origin, skip_armature_object, objects, armatures, actions, out_helper_armatures, out_helper_empties, out_scale_changed_actions):
    """
    Scale/Rotate export objects, adjust scene unit scale, to bake unit conversion into the exported objects
    """
    
    original_object_parents = {}
    parented_to_armature_bone_meshes = []
    object_children = {}
    root_objects = []
    
    armature = None
    if len(armatures) > 0:
        armature = armatures[0]
    
    # Pre-process objects
    for ob in objects:
        def get_parent_of_object_in_list_recursive(test_ob, object_list):
            if test_ob.parent == None:
                return None
            if test_ob.parent in object_list:
                return test_ob.parent
            return get_parent_of_object_in_list_recursive(test_ob.parent, object_list)
        
        # Get parent of this object (if that parent/distant-parent is in the list)
        parent_in_list = get_parent_of_object_in_list_recursive(ob, objects)
        
        # populate children dictionary
        # * Only populate objects in the export list
        # * Strip out intermediate parents that are not in list, but maintain connections between parents/children that are
        # also populate list of objects that are the start of a chain of children
        # * We need to do this, because something might have a parent NOT in the export
        #   list, and still needs to be treated as if it doesn't have a parent
        if parent_in_list != None:
            if parent_in_list not in object_children:
                object_children[parent_in_list] = []
            object_children[parent_in_list].append(ob)
        
        # is this an armature mesh?
        # * Make sure all objects manipulated by the armature are parented to it during the transformation,
        #   then re-parent them to their original parent (in the export list) after
        is_armature_mesh = False
        for modifier in ob.modifiers:
            if armature != None and modifier.type == 'ARMATURE' and modifier.object.name == armature.name:
                is_armature_mesh = True
        
        # Determine if this is a root object among the export objects
        if parent_in_list == None and not is_armature_mesh:
            root_objects.append(ob)
                
        # Parent to armature (temporarily) if this is an armature mesh not parented to armature
        if is_armature_mesh and parent_in_list != armature: #ob.parent != armature:
            # We need to cache what to re-parent to after transforming, but we should only re-parent
            # to something in the export list (remember this is a duplicate object, we aren't messing up the user's real scene)
            if parent_in_list != None:
                original_object_parents[ob] = parent_in_list
            ob.parent = armature
            
            if armature not in object_children:
                object_children[armature] = []
            object_children[armature].append(ob)
        
        # parented_to_armature_bone_meshes
        # * These meshes don't have armature modifiers and are simply parented to bones
        # * These have extra problems with scaling and need their world transform set manually
        if is_armature_mesh == False and ob.parent == armature and ob.parent_type == 'BONE':
            parented_to_armature_bone_meshes = ob
            # parent to object instead temporarily
            cached_matrix = mesh.matrix_world
            mesh.parent_type = 'OBJECT'
            mesh.matrix_world = cached_matrix
            object_children[parent_in_list].append(ob)
    
    
    # ------------------------------------
    if move_to_origin:
        # Move exported objects to the origin before export
        # We assume that all root objects in the export have their origins zero'd
        original_locations = []
        for ob in root_objects:
            if ob.location in original_locations:
                self.warnings.append("'Move To Origin' enabled, but multiple un-parented export objects had different origins! Export may be incorrect")
            original_locations.append(ob.location)
            ob.location = (0,0,0)
    else:
        if skip_armature_object:
            for ob in root_objects:
                if ob.type == "ARMATURE" and ob.location != Vector((0.0,0.0,0.0)):
                    self.warnings.append("Armature not at location (0,0,0), 'Skip Armature Object' is enabled, and 'Move To Origin' is not enabled. This may cause unexpected transforms on exported objects. Recommended to move Armature to (0,0,0) or enable 'Move To Origin'")
    
    # perform scene transforming
    for ob in root_objects:
        transform_object_and_children(context, ob, unit_scale, bake_z_forward, remove_bone_rotation, object_children, False, out_helper_armatures)
        #transform_object(context, ob, unit_scale, bake_z_forward, out_helper_armatures)
    
    if len(out_helper_armatures) > 0 and bake_z_forward:
        # Create empty object with the same rotation (un-applied), and constrain the helper_armatures to it
        # Avoids animation keys on the armature object itself messing with our transformations
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        new_empty = context.object
        #if unit_scale != 1.0:
        #    new_empty.scale *= unit_scale
        new_empty.rotation_euler.x -= radians(90)
        
        for helper_armature in out_helper_armatures:
            constraint = helper_armature.constraints.new('COPY_TRANSFORMS')
            constraint.target = new_empty
        out_helper_empties.append(new_empty)
    # ------------------------------------
    
    
    # meshes parented to bones - parent back to bone (must get and reset world transform)
    for mesh in parented_to_armature_bone_meshes:
        cached_matrix = mesh.matrix_world
        mesh.parent_type = 'BONE'
        mesh.matrix_world = cached_matrix
    
    # restore parents of re-parented objects
    for ob, parent in original_object_parents:
        ob.parent = parent
    
    # perform action transforming for scaling
    if armature != None and unit_scale != 1.0:
        for action in actions:
            # Scale keys in actions
            unit_scale_action(action, unit_scale)
            
            # Rotate keys in actions
            # DEPRECATED - helper armature not used
            #if bake_z_forward:
            #    fbx_rotate_action(action)
            
            out_scale_changed_actions.append(action)
    
    # Reset constraints that don't play nicely with scale
    def reset_armature_constraints(_armature):
        for pb in _armature.pose.bones:
            for constraint in pb.constraints:
                # Warnings
                if unit_scale != 1.0 and constraint.type == 'LIMIT_LOCATION' and (constraint.owner_space == 'WORLD'):
                    do_bone_warning(self, ["Bake Unit Scale"], pb.name, "World-space LIMIT LOCATION constraint! May not export correctly, consider pose-space instead.")
                
                if unit_scale != 1.0 and constraint.type == 'COPY_TRANSFORMS':
                    if constraint.target_space == 'WORLD' and constraint.owner_space == 'WORLD':
                        if constraint.target != _armature:
                            do_bone_warning(self, ["Bake Unit Scale"], pb.name, "World-space COPY TRANSFORMS constraint to another object! May not export correctly, consider pose-space instead.")
                    elif constraint.target_space == 'WORLD' or constraint.owner_space == 'WORLD':
                        do_bone_warning(self, ["Bake Unit Scale"], pb.name, "COPY TRANSFORMS constraint with one space as world-space! May not export correctly, consider pose-space instead.")
                
                if unit_scale != 1.0 and constraint.type == 'TRANSFORM' and (constraint.target_space == 'WORLD' or constraint.owner_space == 'WORLD'):
                    if constraint.target_space == 'WORLD' and constraint.owner_space == 'WORLD':
                        if constraint.target != _armature:
                            do_bone_warning(self, ["Bake Unit Scale"], pb.name, "World-space TRANSFORM constraint to another object! May not export correctly, consider pose-space instead.")
                    elif constraint.target_space == 'WORLD' or constraint.owner_space == 'WORLD':
                        do_bone_warning(self, ["Bake Unit Scale"], pb.name, "TRANSFORM constraint with one space as world-space! May not export correctly, consider pose-space instead.")
                
                if constraint.type == "STRETCH_TO":
                    #print("reset stretch to")
                    constraint.rest_length = constraint.rest_length * unit_scale
                elif constraint.type == "CHILD_OF":
                    #print("reset child of")
                    # Manually re-calculate the inverse
                    # (don't use set_inverse_pending, because we don't know what pose this armature was in when the user set the inverse)
                    loc, rot, sca = constraint.inverse_matrix.decompose()
                    scale_matrix = mathutils.Matrix.Scale(unit_scale, 3)
                    loc = loc @ scale_matrix
                    constraint.inverse_matrix = mathutils.Matrix.LocRotScale(loc, rot, sca)
                elif constraint.type == "TRANSFORM":
                    if constraint.map_from == "LOCATION":
                        constraint.from_min_x *= unit_scale
                        constraint.from_min_y *= unit_scale
                        constraint.from_min_z *= unit_scale
                        constraint.from_max_x *= unit_scale
                        constraint.from_max_y *= unit_scale
                        constraint.from_max_z *= unit_scale
                    if constraint.map_to == "LOCATION":
                        constraint.to_min_x *= unit_scale
                        constraint.to_min_y *= unit_scale
                        constraint.to_min_z *= unit_scale
                        constraint.to_max_x *= unit_scale
                        constraint.to_max_y *= unit_scale
                        constraint.to_max_z *= unit_scale
                elif constraint.type == "LIMIT_LOCATION":
                    constraint.min_x *= unit_scale
                    constraint.min_y *= unit_scale
                    constraint.min_z *= unit_scale
                    constraint.max_x *= unit_scale
                    constraint.max_y *= unit_scale
                    constraint.max_z *= unit_scale
    if unit_scale != 1.0:
        for armature in armatures:
            reset_armature_constraints(armature)
        for helper_armature in out_helper_armatures:
            reset_armature_constraints(helper_armature)
    
    #depsgraph = context.evaluated_depsgraph_get()
    #depsgraph.update()
    
    for ob in objects:
        # Scale mesh modifiers that are influenced by scale
        for modifier in ob.modifiers:
            if modifier.type == "MIRROR":
                modifier.merge_threshold *= unit_scale
            elif modifier.type == "SOLIDIFY":
                modifier.thickness *= unit_scale
            elif modifier.type == "BEVEL":
                modifier.width *= unit_scale
            elif modifier.type == 'SHRINKWRAP':
                if modifier.target:
                    tar_average_scale = (modifier.target.scale[0] + modifier.target.scale[1] + modifier.target.scale[2]) / 3
                    modifier.offset *= tar_average_scale
            elif modifier.type == "LIMIT_LOCATION":
                modifier.max_x *= unit_scale
                modifier.max_y *= unit_scale
                modifier.max_z *= unit_scale
                modifier.min_x *= unit_scale
                modifier.min_y *= unit_scale
                modifier.min_z *= unit_scale
        
        # Shapekey drivers
        # if it uses an expression involving location, scale the expression
        if armature != None and hasattr(ob.data, 'shape_keys'):
            shape_keys = ob.data.shape_keys
            if shape_keys != None and shape_keys.animation_data != None and shape_keys.animation_data.drivers != None:
                drivers = shape_keys.animation_data.drivers
                for driver_fcurve in drivers:
                    # check if any vars use location of armature
                    scale_expression = False
                    for var in driver_fcurve.driver.variables:
                        for target in var.targets:
                            if target.id == armature.id_data and 'location' in target.data_path:
                                scale_expression = True
                                break
                        if scale_expression:
                            break
                    
                    # scale location expression
                    if scale_expression and driver_fcurve.driver.type == 'SCRIPTED':
                        driver_fcurve.driver.expression = "(" + driver_fcurve.driver.expression + ") / " + str(unit_scale)

    # Counter-scale the scene's unit scale
    #context.scene.unit_settings.system = 'METRIC'
    context.scene.unit_settings.scale_length = 1 / unit_scale
    
    context.view_layer.update()


def apply_min_two_frames_to_actions(armature, actions, original_action_frame_ranges):
    for action in actions:
        frame_start, frame_end = action.frame_range
        if frame_start == frame_end:
            # Cache current settings to restore later
            original_action_frame_ranges[action] = (action.use_frame_range, action.frame_range)
            
            # Set manual frame range that's 1 longer
            action.use_frame_range = True
            action.frame_range = frame_start, frame_end + 1


def create_ordered_bone_list_recursive(pb, armature, ordered_bone_list):
    # Add bone to the list
    ordered_bone_list.append(pb)
    
    # recursively iterate bone's children
    for child in pb.children:
        create_ordered_bone_list_recursive(child, armature, ordered_bone_list)


def warn_incompatible_constraints(self, context, armature, pbone, constraint, remove_bone_rotation, fbx_rotate_bones):
    # warn users if there are any potentially incompatible constraints
    # (NOTE: we're iterating the regular armature, but actually warning about if the helper armature will work)
    if not remove_bone_rotation and not fbx_rotate_bones:
        return
    
    def warn_constraints_helper(warning_str):
        option_names = []
        if remove_bone_rotation:
            option_names.append("Remove Rotation From Bones")
        if fbx_rotate_bones:
            option_names.append("Bake Z Forward")
        do_bone_warning(self, option_names, pbone.name, warning_str)
    
    if hasattr(constraint, 'target') and constraint.target != armature:
        warn_constraints_helper("Constraint targeting a different object! May not export correctly.")
    
    if constraint.type == 'COPY_ROTATION':
        if constraint.target_space == 'WORLD' and constraint.owner_space == 'WORLD':
            if constraint.target != armature:
                warn_constraints_helper("World-space COPY ROTATION constraint to another object! May not export correctly, consider pose-space instead.")
        elif constraint.target_space == 'WORLD' or constraint.owner_space == 'WORLD':
            warn_constraints_helper("COPY ROTATION constraint with one space as world-space! May not export correctly, consider pose-space instead.")
    
    if constraint.type == 'COPY_TRANSFORMS':
        if constraint.target_space == 'WORLD' and constraint.owner_space == 'WORLD':
            if constraint.target != armature:
                warn_constraints_helper("World-space COPY TRANSFORMS constraint to another object! May not export correctly, consider pose-space instead.")
        elif constraint.target_space == 'WORLD' or constraint.owner_space == 'WORLD':
            warn_constraints_helper("COPY TRANSFORMS constraint with one space as world-space! May not export correctly, consider pose-space instead.")
    
    if constraint.type == 'TRANSFORM' and (constraint.target_space == 'WORLD' or constraint.owner_space == 'WORLD'):
        if constraint.target_space == 'WORLD' and constraint.owner_space == 'WORLD':
            if constraint.target != armature:
                warn_constraints_helper("World-space TRANSFORM constraint to another object! May not export correctly, consider pose-space instead.")
        elif constraint.target_space == 'WORLD' or constraint.owner_space == 'WORLD':
            warn_constraints_helper("TRANSFORM constraint with one space as world-space! May not export correctly, consider pose-space instead.")
    
    if constraint.type == 'LIMIT_ROTATION' and (constraint.owner_space == 'WORLD'):
        warn_constraints_helper("World-space LIMIT ROTATION constraint! May not export correctly, consider pose-space instead.")


def init_helper_armatures(self, context, armatures, helper_armatures, remove_scale_from_bones, flat_bone_hierarchy, flat_bone_hierarchy_root, remove_bone_rotation, fbx_rotate_bones):
    """
    Perform modifications to bones in armature, and constrain it to a "helper armature" to preserve animations
    * remove_scale_from_bones - constrain bones from ever changing scale during animation
    * flat_bone_hierarchy - collapse hierarchy to make all bones parented to a given root bone
    * flat_bone_hierarchy_root - root bone for flat_bone_hierarchy
    * remove_bone_rotation - disconnect all bones, and make them use 0,0,0 rotation
    * fbx_rotate_bones - disconnect all bones, and rotate them -90 degrees in X to match FBX/Maya coordinate system. Applies after remove_bone_rotation
    """
    
    for i, armature in enumerate(armatures):
        # helper_armatures - additional duplicate of the original duplicate armature
        # armature - deform bones modified to be disconnected, not inherit scale, and be constrained to corresponding bones in helper_armatures
        #   will have hierarchy changed if flat_bone_hierarchy is True
        helper_armature = helper_armatures[i]
        
        # Select armature and helper armature
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = armature
        armature.select_set(state=True)
        helper_armature.select_set(state=True)
        
        # --------------------------------------------
        # Edit Bone changes
        # --------------------------------------------
        def rotate_edit_bone(ebone, is_helper_armature):
            if remove_bone_rotation:
                if fbx_rotate_bones and is_helper_armature:
                    # Zero rotationis harder with the helper armature when fbx_rotate_bones is active:
                    # * helper armature is rotated by an active constraint, not its own transform, so we can't calculate its final world transform
                    # * ebone.matrix is armature space, but we need it to line up with the regular armature in world space
                    ebone.matrix = Matrix.LocRotScale(ebone.matrix.to_translation(), Matrix.Rotation(radians(90.0), 3, 'X'), ebone.matrix.to_scale())
                else:
                    ebone.matrix = Matrix.LocRotScale(ebone.matrix.to_translation(), Matrix.Identity(3), ebone.matrix.to_scale())
            
            elif fbx_rotate_bones:
                # rotation matrix 90 degrees around local x axis
                # also need to manually fix the roll
                x, y, z = ebone.matrix.to_3x3().col
                R = (Matrix.Translation(ebone.head) @
                    Matrix.Rotation(radians(90), 4, x) @
                    Matrix.Translation(-ebone.head)
                    )
                ebone.transform(R)
                ebone.align_roll(-y)
        
        # switch to Edit Mode
        try:
            bpy.ops.object.mode_set(mode='EDIT')
        except:
            pass
        
        # If rotating bones, we need to disconnect all bones first
        if remove_bone_rotation or fbx_rotate_bones:
            for ebone in armature.data.edit_bones:
                ebone.use_connect = False
                ebone.inherit_scale = 'NONE'
        
        # Process bones
        for i, ebone in enumerate(armature.data.edit_bones):
            # armature bone
            ebone.use_connect = False
            ebone.inherit_scale = 'NONE'
            
            if flat_bone_hierarchy:
                if flat_bone_hierarchy_root == "":
                    ebone.parent = None # Remove parent
                else:
                    ebone.parent = armature.data.edit_bones[flat_bone_hierarchy_root] # Set user specified parent
            
            rotate_edit_bone(ebone, False)
            
            # helper armature bone
            if remove_bone_rotation or fbx_rotate_bones:
                helper_ebone = helper_armature.data.edit_bones[i]
                # Create duplicate child bone
                new_helper_ebone = helper_armature.data.edit_bones.new(helper_ebone.name + "_helperarmature_dupe")
                new_helper_ebone.use_connect = False
                new_helper_ebone.inherit_scale = 'FULL'
                new_helper_ebone.head = helper_ebone.head
                new_helper_ebone.tail = helper_ebone.tail
                new_helper_ebone.roll = helper_ebone.roll
                new_helper_ebone.matrix = helper_ebone.matrix
                new_helper_ebone.parent = helper_ebone
                
                # Apply same transformations as the non-helper armature bones
                rotate_edit_bone(new_helper_ebone, True)
        
        # if we created new bones, update the scene
        #if remove_bone_rotation or fbx_rotate_bones:
        #    context.view_layer.update()
        
        # switch back to Object Mode
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        
        # --------------------------------------------
        # Pose Bone changes
        # --------------------------------------------
        # armature deform bones - delete all constraints, constrain to helper armature
        for pbone in armature.pose.bones:
            # delete all constraints
            for constraint in pbone.constraints:
                warn_incompatible_constraints(self, context, armature, pbone, constraint, remove_bone_rotation, fbx_rotate_bones)
                pbone.constraints.remove(constraint)
            
            # constrain to helper_armature bone
            # (necessary to split channels to account for different scale)
            target_pbone_name = pbone.name
            if remove_bone_rotation or fbx_rotate_bones:
                target_pbone_name += "_helperarmature_dupe"
            new_constraint = pbone.constraints.new('COPY_SCALE') # constraint must be pose space
            new_constraint.target = helper_armature
            new_constraint.subtarget = target_pbone_name
            new_constraint.target_space = 'POSE'
            new_constraint.owner_space = 'POSE'
            new_constraint = pbone.constraints.new('COPY_ROTATION') # constraint must be world space
            new_constraint.target = helper_armature
            new_constraint.subtarget = target_pbone_name
            new_constraint.target_space = 'WORLD'
            new_constraint.owner_space = 'WORLD'
            new_constraint = pbone.constraints.new('COPY_LOCATION') # constraint must be world space
            new_constraint.target = helper_armature
            new_constraint.subtarget = target_pbone_name
            new_constraint.target_space = 'WORLD'
            new_constraint.owner_space = 'WORLD'
            
            # constrain scale
            if remove_scale_from_bones:
                new_constraint = pbone.constraints.new('LIMIT_SCALE')
                new_constraint.use_min_x = True
                new_constraint.min_x = 1.0
                new_constraint.use_min_y = True
                new_constraint.min_y = 1.0
                new_constraint.use_min_z = True
                new_constraint.min_z = 1.0
                new_constraint.use_max_x = True
                new_constraint.max_x = 1.0
                new_constraint.use_max_y = True
                new_constraint.max_y = 1.0
                new_constraint.use_max_z = True
                new_constraint.max_z = 1.0
    
    context.view_layer.update()


def do_fbx_export(self, context, filepath, keywords):
    """
    Perform an FBX export using PROTO modification of Blender's included FBX exporter
    """
    keywords["filepath"] = filepath
    proto_export_fbx_bin.save(self, context, **keywords)


def cleanup_scene(context, unit_scale, bake_z_forward, saved_unit_settings, original_objects, duplicate_objects, renamed_objects, scale_changed_actions, original_action_frame_ranges, fcurve_changed_actions, actions_original_fcurves, helper_armatures, helper_empties):
    """
    Delete duplicate objects, revert unit scale changes to scene and actions, undo name changes
    (technically 'duplicate_objects' can include new objects that aren't really duplicates, but they are treated the same)
    """
    
    # Delete duplicate objects
    for ob in duplicate_objects:
        bpy.data.objects.remove(ob, do_unlink=True)
    for armature in helper_armatures:
        bpy.data.objects.remove(armature, do_unlink=True)
    for helper_empty in helper_empties:
        bpy.data.objects.remove(helper_empty)
    
    # revert animation curves scaling
    if unit_scale != 1.0:
        for action in scale_changed_actions:
            unscale_action(action, unit_scale)
    # DEPRECATED
    #if bake_z_forward:
    #    unrotate_action(action)
    
    # revert adjusted action frame ranges
    for action in original_action_frame_ranges:
        original_use_frame_range, original_frame_range = original_action_frame_ranges[action]
        action.use_frame_range = original_use_frame_range
        if action.use_frame_range:
            action.frame_range = original_frame_range
    
    # Undo object name changes
    for ob, original_name in renamed_objects.items():
        ob.name = original_name
    
    # Reset scene scale
    # start by restoring the unit system value, since changing it will unexpectedly reset others to default values
    context.scene.unit_settings.system = saved_unit_settings['system']
    for prop_name in saved_unit_settings:
        if prop_name != 'system':
            value = saved_unit_settings[prop_name]
            try:# if Unit System is None, the attributes may be locked
                setattr(context.scene.unit_settings, prop_name, value)
            except:
                pass


# rotate JUST root object curves -90 in x, to account for FBX file forward
# swizzle y and z location keyframes
def DEPRECATED_fbx_rotate_action(action):
    if bpy.app.version < (4, 4, 0):
        # Pre-Action-Slots version
        old_z_keyframe_points = list()
        old_y_keyframe_points = list()
        for fcurve in action.fcurves:
            print(fcurve.data_path)
            if 'location' == fcurve.data_path and fcurve.array_index == 1: # y
                old_y_keyframe_points = fcurve.keyframe_points
            if 'location' == fcurve.data_path and fcurve.array_index == 2: # z
                old_z_keyframe_points = fcurve.keyframe_points
        for fcurve in action.fcurves:
            if 'location' == fcurve.data_path and fcurve.array_index == 1: # y
                for i, point in enumerate(fcurve.keyframe_points):
                    z_point = old_z_keyframe_points[i]
                    point.co[1] = z_point.co[1]
                    point.handle_left[1] = z_point.handle_left[1]
                    point.handle_right[1] = z_point.handle_right[1]
            if 'location' == fcurve.data_path and fcurve.array_index == 2: # z
                for i, point in enumerate(fcurve.keyframe_points):
                    # Invert, and flip handles relative to key
                    y_point = old_y_keyframe_points[i]
                    point.co[1] = -1.0 * y_point.co[1]
                    point.handle_left[1] = y_point.co[1] - ((y_point.handle_left[1] - y_point.co[1]))
                    point.handle_right[1] = y_point.co[1] - ((y_point.handle_right[1] - y_point.co[1]))
    else:
        # Action-Slots version
        for layer in action.layers:
            for strip in layer.strips:
                # NOTE: we *could* only scale the slot that matches the armature, but maybe there are
                # cases where the other slots' animations matter for the armature's final pose?
                for slot in action.slots:
                    channelbag = strip.channelbag(slot)
                    if channelbag != None:
                        for fcurve in channelbag.fcurves:
                            if 'location' == fcurve.data_path and fcurve.array_index == 1: # y
                                old_y_keyframe_points = fcurve.keyframe_points
                            if 'location' == fcurve.data_path and fcurve.array_index == 2: # z
                                old_z_keyframe_points = fcurve.keyframe_points
                        for fcurve in channelbag.fcurves:
                            if 'location' == fcurve.data_path and fcurve.array_index == 1: # y
                                for i, point in enumerate(fcurve.keyframe_points):
                                    z_point = old_z_keyframe_points[i]
                                    point.co[1] = z_point.co[1]
                                    point.handle_left[1] = z_point.handle_left[1]
                                    point.handle_right[1] = z_point.handle_right[1]
                            if 'location' == fcurve.data_path and fcurve.array_index == 2: # z
                                for i, point in enumerate(fcurve.keyframe_points):
                                    # Invert, and flip handles relative to key
                                    y_point = old_y_keyframe_points[i]
                                    point.co[1] = -1.0 * y_point.co[1]
                                    point.handle_left[1] = y_point.co[1] - ((y_point.handle_left[1] - y_point.co[1]))
                                    point.handle_right[1] = y_point.co[1] - ((y_point.handle_right[1] - y_point.co[1]))


def DEPRECATED_unrotate_action(action):
    if bpy.app.version < (4, 4, 0):
        # Pre-Action-Slots version
        old_z_keyframe_points = list()
        old_y_keyframe_points = list()
        for fcurve in action.fcurves:
            if 'location' == fcurve.data_path and fcurve.array_index == 1: # y
                old_y_keyframe_points = fcurve.keyframe_points
            if 'location' == fcurve.data_path and fcurve.array_index == 2: # z
                old_z_keyframe_points = fcurve.keyframe_points
        for fcurve in action.fcurves:
            if 'location' == fcurve.data_path and fcurve.array_index == 2: # z
                for i, point in enumerate(fcurve.keyframe_points):
                    y_point = old_y_keyframe_points[i]
                    point.co[1] = y_point.co[1]
                    point.handle_left[1] = y_point.handle_left[1]
                    point.handle_right[1] = y_point.handle_right[1]
            if 'location' == fcurve.data_path and fcurve.array_index == 1: # y
                for i, point in enumerate(fcurve.keyframe_points):
                    # Invert, and flip handles relative to key
                    z_point = old_z_keyframe_points[i]
                    point.co[1] = -1.0 * z_point.co[1]
                    point.handle_left[1] = z_point.co[1] - ((z_point.handle_left[1] - z_point.co[1]))
                    point.handle_right[1] = z_point.co[1] - ((z_point.handle_right[1] - z_point.co[1]))
    else:
        # Action-Slots version
        for layer in action.layers:
            for strip in layer.strips:
                # NOTE: we *could* only scale the slot that matches the armature, but maybe there are
                # cases where the other slots' animations matter for the armature's final pose?
                for slot in action.slots:
                    channelbag = strip.channelbag(slot)
                    if channelbag != None:
                        for fcurve in channelbag.fcurves:
                            if 'location' == fcurve.data_path and fcurve.array_index == 1: # y
                                old_y_keyframe_points = fcurve.keyframe_points
                            if 'location' == fcurve.data_path and fcurve.array_index == 2: # z
                                old_z_keyframe_points = fcurve.keyframe_points
                        for fcurve in channelbag.fcurves:
                            if 'location' == fcurve.data_path and fcurve.array_index == 2: # z
                                for i, point in enumerate(fcurve.keyframe_points):
                                    y_point = old_y_keyframe_points[i]
                                    point.co[1] = y_point.co[1]
                                    point.handle_left[1] = y_point.handle_left[1]
                                    point.handle_right[1] = y_point.handle_right[1]
                            if 'location' == fcurve.data_path and fcurve.array_index == 1: # y
                                for i, point in enumerate(fcurve.keyframe_points):
                                    # Invert, and flip handles relative to key
                                    z_point = old_z_keyframe_points[i]
                                    point.co[1] = -1.0 * z_point.co[1]
                                    point.handle_left[1] = z_point.co[1] - ((z_point.handle_left[1] - z_point.co[1]))
                                    point.handle_right[1] = z_point.co[1] - ((z_point.handle_right[1] - z_point.co[1]))



