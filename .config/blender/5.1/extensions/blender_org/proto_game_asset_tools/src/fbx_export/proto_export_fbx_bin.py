# SPDX-FileCopyrightText: 2013 Campbell Barton
# SPDX-FileCopyrightText: 2014 Bastien Montagne
#
# SPDX-License-Identifier: GPL-2.0-or-later
#
# Partial modification of export_fbx_bin.py from Blender 5.0, modified by PROTOWLF 2026
# * Mostly only a modification of fbx_animations_do()

import datetime
import math
import numpy as np
import os
import time

from collections import namedtuple
from itertools import zip_longest
from functools import cache

if "bpy" in locals():
    import importlib
    if "encode_bin" in locals():
        importlib.reload(encode_bin)
    if "data_types" in locals():
        importlib.reload(data_types)
    if "fbx_utils" in locals():
        importlib.reload(fbx_utils)

import bpy
import bpy_extras
from bpy_extras import node_shader_utils
from bpy.app.translations import pgettext_tip as tip_
from mathutils import Vector, Matrix
from bpy.types import Object, Bone, PoseBone

# Import default FBX export scripts included with blender
from io_scene_fbx import encode_bin, data_types, fbx_utils, export_fbx_bin

from io_scene_fbx.fbx_utils import (
    # Constants.
    FBX_VERSION, FBX_HEADER_VERSION, FBX_SCENEINFO_VERSION, FBX_TEMPLATES_VERSION,
    FBX_MODELS_VERSION,
    FBX_GEOMETRY_VERSION, FBX_GEOMETRY_NORMAL_VERSION, FBX_GEOMETRY_BINORMAL_VERSION, FBX_GEOMETRY_TANGENT_VERSION,
    FBX_GEOMETRY_SMOOTHING_VERSION, FBX_GEOMETRY_CREASE_VERSION, FBX_GEOMETRY_VCOLOR_VERSION, FBX_GEOMETRY_UV_VERSION,
    FBX_GEOMETRY_MATERIAL_VERSION, FBX_GEOMETRY_LAYER_VERSION,
    FBX_GEOMETRY_SHAPE_VERSION, FBX_DEFORMER_SHAPE_VERSION, FBX_DEFORMER_SHAPECHANNEL_VERSION,
    FBX_POSE_BIND_VERSION, FBX_DEFORMER_SKIN_VERSION, FBX_DEFORMER_CLUSTER_VERSION,
    FBX_MATERIAL_VERSION, FBX_TEXTURE_VERSION,
    FBX_ANIM_KEY_VERSION,
    FBX_ANIM_PROPSGROUP_NAME,
    FBX_KTIME,
    BLENDER_OTHER_OBJECT_TYPES, BLENDER_OBJECT_TYPES_MESHLIKE,
    FBX_LIGHT_TYPES, FBX_LIGHT_DECAY_TYPES,
    RIGHT_HAND_AXES, FBX_FRAMERATES,
    # Miscellaneous utils.
    PerfMon,
    units_blender_to_fbx_factor, units_convertor, units_convertor_iter,
    matrix4_to_array, similar_values, shape_difference_exclude_similar, astype_view_signedness, fast_first_axis_unique,
    fast_first_axis_flat,
    # Attribute helpers.
    MESH_ATTRIBUTE_CORNER_EDGE, MESH_ATTRIBUTE_SHARP_EDGE, MESH_ATTRIBUTE_EDGE_VERTS, MESH_ATTRIBUTE_CORNER_VERT,
    MESH_ATTRIBUTE_SHARP_FACE, MESH_ATTRIBUTE_POSITION, MESH_ATTRIBUTE_MATERIAL_INDEX,
    # Mesh transform helpers.
    vcos_transformed, nors_transformed,
    # UUID from key.
    get_fbx_uuid_from_key,
    # Key generators.
    get_blenderID_key, get_blenderID_name,
    get_blender_mesh_shape_key, get_blender_mesh_shape_channel_key,
    get_blender_empty_key, get_blender_bone_key,
    get_blender_bindpose_key, get_blender_armature_skin_key, get_blender_bone_cluster_key,
    get_blender_anim_id_base, get_blender_anim_stack_key, get_blender_anim_layer_key,
    get_blender_anim_curve_node_key, get_blender_anim_curve_key,
    get_blender_nodetexture_key,
    # FBX element data.
    elem_empty,
    elem_data_single_char, elem_data_single_int16, elem_data_single_int32, elem_data_single_int64,
    elem_data_single_float32, elem_data_single_float64,
    elem_data_single_bytes, elem_data_single_string, elem_data_single_string_unicode,
    elem_data_single_bool_array, elem_data_single_int32_array, elem_data_single_int64_array,
    elem_data_single_float32_array, elem_data_single_float64_array, elem_data_vec_float64,
    # FBX element properties.
    elem_properties, elem_props_set, elem_props_compound,
    # FBX element properties handling templates.
    elem_props_template_init, elem_props_template_set, elem_props_template_finalize,
    # Templates.
    FBXTemplate, fbx_templates_generate,
    # Animation.
    AnimationCurveNodeWrapper,
    # Objects.
    ObjectWrapper, fbx_name_class, ensure_object_not_in_edit_mode,
    # Top level.
    FBXExportSettingsMedia, FBXExportSettings, FBXExportData,
)

# Units convertors!
convert_sec_to_ktime = units_convertor("second", "ktime")
convert_sec_to_ktime_iter = units_convertor_iter("second", "ktime")

convert_mm_to_inch = units_convertor("millimeter", "inch")

convert_rad_to_deg = units_convertor("radian", "degree")
convert_rad_to_deg_iter = units_convertor_iter("radian", "degree")

# PROTOWLF addition
# Helper container for PROTOWLF settings
ProtoFBXExportSettings = namedtuple("ProtoFBXExportSettings", (
    "export_mesh_shapekey_animation", "export_armature_shapekey_animation",
    "export_zeroed_shapekeys", "armature_shapekey_scale",
    "export_custom_property_animation", "export_zeroed_custom_properties",
    "export_non_deform_custom_properties", "export_armature_object_custom_properties",
    "export_armature_data_custom_properties", "dont_simplify_root_bone",
    "bake_anim_use_action_filter", "bake_anim_action_filter",
    "skip_meshes_if_no_shapekey_animation", "helper_armatures",
    "skip_armature_object"
))
class ProtoFBXExportData:
    has_shapekey_animation = False


# PROTOWLF addition
def all_equal(list):
    iterator = iter(list)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == x for x in iterator)
    

# PROTOWLF addition
# Get first bone (presumably the root) with use_deform
# If root does not have use_deform, will keep looking for a bone that does
# If no use_deform bones are found, root will be returned
def get_root_deform_pose_bone(armature):
    if len(armature.pose.bones) == 0:
        return None
    
    for pbone in armature.pose.bones:
        bone = armature.data.bones[pbone.name]
        if bone.use_deform:
            return pbone
    
    # if we get here, we didn't find any deforming pose bones
    return armature.pose.bones[0]


# PROTOWLF addition
def get_meshes_with_shapekeys_for_armature(armature):
    # Get all deformed meshes with shape key information
    shapekey_objects = []
    for ob in bpy.context.view_layer.objects:
        if ob.type == 'MESH' and ob.data.shape_keys != None:
            #print("Object " + ob.name + " has shapekeys")
            #print("armature.name: " + armature.name)
            if ob.parent == armature: # Get this mesh if its parent is the armature
                #print("Object " + ob.name + " considered for shapekey anim export")
                shapekey_objects.append(ob)
            else: # Or if it uses the armature with a modifier
                for modifier in ob.modifiers:
                    if modifier.type == 'ARMATURE' and modifier.object.name == armature.name:
                        #print("Object " + ob.name + " considered for shapekey anim export")
                        shapekey_objects.append(ob)
    
    return shapekey_objects


# PROTOWLF addition -- validate_actions from 4.2 export_fbx_bin.py (add-on supports 4.2)
# Function re-written. Old version rejected slots if they had any invalid keys (led to false negatives)
# New version accepts slots if they have at least 1 valid key
def validate_actions(act, path_resolve):
    valid_action = False
    for fcurve in action.fcurves:
        data_path = fc.data_path
        if fc.array_index:
            data_path = data_path + "[%d]" % fc.array_index
        try:
            path_resolve(data_path)
            valid_slot = True
            break
        except ValueError:
            ...
    if valid_action:
        return True
    
    return False # Invalid.


# PROTOWLF modification -- find_validate_action_slot moved from nested function def to here
# Function re-written. Old version rejected slots if they had any invalid keys (led to false negatives)
# New version accepts slots if they have at least 1 valid key
def find_validate_action_slot(action, path_resolve): #-> bpy.types.ActionSlot | None: annotation removed for 4.2 support
    #print("Validating action '" + act.name + "'")
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                #print("testing channelbag...")
                if not channelbag.fcurves:
                    # Do not export empty Channelbags.
                    #print("empty channelbag")
                    continue
                valid_slot = False
                for fc in channelbag.fcurves:
                    data_path = fc.data_path
                    if fc.array_index:
                        data_path = data_path + "[%d]" % fc.array_index
                    try:
                        path_resolve(data_path)
                        valid_slot = True
                        break
                    except ValueError:
                        ...
                if valid_slot:
                    #print("returning channelbag.slot: " + channelbag.slot.name_display)
                    return channelbag.slot
    
    #print("return None")
    return None  # Found nothing to return.


# PROTOWLF modification -- restore_object defs moved from nested function def to here
# Function unchanged
def restore_object(ob_to, ob_from):
    # Restore org state of object (ugh :/ ).
    props = (
        'location', 'rotation_quaternion', 'rotation_axis_angle', 'rotation_euler', 'rotation_mode', 'scale',
        'delta_location', 'delta_rotation_euler', 'delta_rotation_quaternion', 'delta_scale',
        'lock_location', 'lock_rotation', 'lock_rotation_w', 'lock_rotations_4d', 'lock_scale',
        'tag', 'track_axis', 'up_axis', 'active_material', 'active_material_index',
        'matrix_parent_inverse', 'empty_display_type', 'empty_display_size', 'empty_image_offset', 'pass_index',
        'color', 'hide_viewport', 'hide_select', 'hide_render', 'instance_type',
        'use_instance_vertices_rotation', 'use_instance_faces_scale', 'instance_faces_scale',
        'display_type', 'show_bounds', 'display_bounds_type', 'show_name', 'show_axis', 'show_texture_space',
        'show_wire', 'show_all_edges', 'show_transparent', 'show_in_front',
        'show_only_shape_key', 'use_shape_key_edit_mode', 'active_shape_key_index',
    )
    for p in props:
        if not ob_to.is_property_readonly(p):
            setattr(ob_to, p, getattr(ob_from, p))


# PROTOWLF addition - populate animdata_customproperties with data for anim curve for custom property from armature, armature object data, or armature pose bones
def process_custom_property(animdata_customproperties, ob_obj, key, propertyowner, customproperty, force_keying, force_sek, add_dummy_prop=False, dummy_prop_owner=None):
    # Only float, int, bool allowed
    if not (isinstance(propertyowner[customproperty], float) or isinstance(propertyowner[customproperty], int) or isinstance(propertyowner[customproperty], bool)):
        return
    
    #print("- adding custom property: " + customproperty)
    if customproperty in animdata_customproperties:
        # NOTE: would be nice to give a warning to users, but exporting multiple actions at once causes this to get tripped which is not the user's fault
        #print("WARNING: duplicate custom property name '" + customproperty + "'! Can only export custom properties with unique names. Ignoring.")
        ...
    else:
        # All-zero keys get exported unless BOTH force_keying and force_startend_keying are False!
        acnode = AnimationCurveNodeWrapper(key, 'SHAPE_KEY', force_keying, force_sek, (0.0,))
        acnode.add_group(key, customproperty, customproperty, (customproperty,))
        animdata_customproperties[customproperty]=(customproperty, propertyowner, ob_obj, acnode)
    
    if add_dummy_prop:
        # Make a dummy custom property (most likely on the armature's root bone, but not necessarily)
        if customproperty not in dummy_prop_owner:
            dummy_prop_owner[customproperty] = 0.0


def fbx_animations_do(scene_data, proto_settings, proto_data, ref_id, f_start, f_end, start_zero, objects=None, force_keep=False):
    """
    Generate animation data (a single AnimStack) from objects, for a given frame range.
    """
    bake_step = scene_data.settings.bake_anim_step
    simplify_fac = scene_data.settings.bake_anim_simplify_factor
    scene = scene_data.scene
    depsgraph = scene_data.depsgraph
    force_keying = scene_data.settings.bake_anim_use_all_bones
    force_sek = scene_data.settings.bake_anim_force_startend_keying
    gscale = scene_data.settings.global_scale
    
    if objects is not None:
        # Add bones and duplis!
        for ob_obj in tuple(objects):
            if not ob_obj.is_object:
                continue
            if ob_obj.type == 'ARMATURE':
                objects |= {bo_obj for bo_obj in ob_obj.bones if bo_obj in scene_data.objects}
            for dp_obj in ob_obj.dupli_list_gen(depsgraph):
                if dp_obj in scene_data.objects:
                    objects.add(dp_obj)
    else:
        objects = scene_data.objects

    back_currframe = scene.frame_current
    animdata_ob = {}
    p_rots = {}
    
    # PROTOWLF additions
    animdata_customproperties = {}
    animdata_childshapekeyproperties = {}
    
    for ob_obj in objects:
        if ob_obj.parented_to_armature:
            continue
        ACNW = AnimationCurveNodeWrapper
        loc, rot, scale, _m, _mr = ob_obj.fbx_object_tx(scene_data)
        rot_deg = tuple(export_fbx_bin.convert_rad_to_deg_iter(rot))
        force_key = (simplify_fac == 0.0) or (ob_obj.is_bone and force_keying)
        animdata_ob[ob_obj] = (ACNW(ob_obj.key, 'LCL_TRANSLATION', force_key, force_sek, loc),
                               ACNW(ob_obj.key, 'LCL_ROTATION', force_key, force_sek, rot_deg),
                               ACNW(ob_obj.key, 'LCL_SCALING', force_key, force_sek, scale))
        p_rots[ob_obj] = rot
        
        # PROTOWLF addition - custom properties, shapekeys on deformed meshes
        # We can only successfully export an anim curve if a corresponding custom property really exists on the exported object
        # If property is not on a deforming pose bone, it is added to 'dummy_prop_owner', which is ideally the root bone of the armature. We do this because:
        # * The armature object itself is imported into Unreal as the root bone, but will be stripped-out if it is named 'Armature'
        # * This causes Unreal to fail to import properties on the armature object, so we have to use a bone instead
        # * Depending on export settings, non-deform bones may not be exported, so we prefer a bone with use_deform
        if ob_obj.type == 'ARMATURE':
            ob_name = ob_obj.name
            armature = ob_obj.bdata
            
            # We create dummy custom properties to allow curve data to be exported
            # We ideally put this data on the root bone of the armature, but in the
            # rare case that an armature has no bones, we put it on the armature object
            dummy_prop_owner = ob_obj.bdata
            dummy_prop_key = ob_obj.key
            if len(ob_obj.bdata.pose.bones) > 0:
                pbone_root = get_root_deform_pose_bone(armature)
                bone_root = armature.data.bones[pbone_root.name]
                dummy_prop_owner = pbone_root
                dummy_prop_key = get_blenderID_key((armature, bone_root))
            
            # -----------------------------------------------
            # Custom Properties from Armature
            # -----------------------------------------------
            if proto_settings.export_custom_property_animation:
                
                # -----------------------------------------------
                # Get custom properites of all pose bones
                # -----------------------------------------------
                for pbone in ob_obj.bdata.pose.bones:
                    for customproperty in pbone.keys(): # custom properties from Pose Bone Properties panel
                        armature = ob_obj.bdata
                        bone = armature.data.bones[pbone.name]
                        
                        if bone.use_deform:
                            # Deform Bone
                            key = get_blenderID_key((armature, bone))
                            process_custom_property(animdata_customproperties, ob_obj, key, pbone, customproperty, force_keying, force_sek)
                        elif proto_settings.export_non_deform_custom_properties:
                            # Non-Deform Bone, use dummy prop on root bone
                            process_custom_property(animdata_customproperties, ob_obj, dummy_prop_key, pbone, customproperty, force_keying, force_sek, True, dummy_prop_owner)
                
                # -----------------------------------------------
                # Get custom properties of Armature Object
                # -----------------------------------------------
                if proto_settings.export_armature_object_custom_properties:
                    for customproperty in ob_obj.bdata.keys(): # custom properties from Object Properties panel
                        process_custom_property(animdata_customproperties, ob_obj, dummy_prop_key, ob_obj.bdata, customproperty, force_keying, force_sek, True, dummy_prop_owner)
                
                # -----------------------------------------------
                # custom properties from Amature Data
                # -----------------------------------------------
                if proto_settings.export_armature_data_custom_properties:
                    for customproperty in ob_obj.bdata.data.keys(): 
                        process_custom_property(animdata_customproperties, ob_obj, dummy_prop_key, ob_obj.bdata.data, customproperty, force_keying, force_sek, True, dummy_prop_owner)
            
            # -----------------------------------------------
            # Shapekeys from meshes deformed by Armature
            # -----------------------------------------------
            if proto_settings.export_armature_shapekey_animation:
                shapekey_objects = get_meshes_with_shapekeys_for_armature(ob_obj.bdata)
                for mesh in shapekey_objects:
                    # ignore this object if it is already part of the export
                    if mesh in objects:
                        continue
                    # Ignore absolute shape keys (the blender mesh export won't export these)
                    if not mesh.data.shape_keys.use_relative:
                        continue
                    
                    for shape in mesh.data.shape_keys.key_blocks[1:]: # skip the first shapekey (the basis)
                        # NOTE: Will only export correctly if a custom property of this name really exists on the object
                        # We can make one and don't need to clean it up after (the exported armature is a duplicate that is deleted after export!)
                        
                        # Use dummy prop on root bone
                        if shape.name not in dummy_prop_owner:
                            dummy_prop_owner[shape.name] = 0.0
                        
                        if shape.name in animdata_childshapekeyproperties:
                            # do nothing. Not a warning, because you might have multiple meshes with the same shapekeys on them, in which case you probably expect them to function as one shapekey in a game engine
                            ...
                        else:
                            # All-zero keys get exported unless BOTH force_keying and force_startend_keying are False!
                            acnode = AnimationCurveNodeWrapper(dummy_prop_key, 'SHAPE_KEY', force_keying, force_sek, (0.0,))
                            acnode.add_group(dummy_prop_key, shape.name, shape.name, (shape.name,))
                            #print("- adding child shapekey property: " + shape.name + " from mesh: " + mesh.name)
                            animdata_childshapekeyproperties[shape.name]=(shape.name, mesh, ob_obj, acnode)
            
    force_key = (simplify_fac == 0.0) #PROTOWLF note: existing code, used to be used by shapekeys, but this is poorly designed
    animdata_shapes = {}
    
    # -----------------------------------------------
    # Shapekeys from meshes in the export
    # * this is the old way, not a PROTOWLF addition
    # * updated to obey proto_settings.export_mesh_shapekey_animation
    # * (below, updated to obey proto_settings.export_zeroed_shapekeys)
    # -----------------------------------------------
    if proto_settings.export_mesh_shapekey_animation:
        for me, (me_key, _shapes_key, shapes) in scene_data.data_deformers_shape.items():
            # Ignore absolute shape keys for now!
            if not me.shape_keys.use_relative:
                continue
            if bpy.app.version >= (5, 1, 0): # shapes.items changed in 5.1
                for shape, (channel_key, geom_key, _shape_verts_co, _shape_verts_nors, _shape_verts_idx) in shapes.items():
                    acnode = AnimationCurveNodeWrapper(channel_key, 'SHAPE_KEY', force_key, force_sek, (0.0,))
                    # Sooooo happy to have to twist again like a mad snake... Yes, we need to write those curves twice. :/
                    acnode.add_group(me_key, shape.name, shape.name, (shape.name,))
                    animdata_shapes[channel_key] = (acnode, me, shape)
            else: # Pre-5.1 version
                for shape, (channel_key, geom_key, _shape_verts_co, _shape_verts_idx) in shapes.items():
                    acnode = AnimationCurveNodeWrapper(channel_key, 'SHAPE_KEY', force_key, force_sek, (0.0,))
                    # Sooooo happy to have to twist again like a mad snake... Yes, we need to write those curves twice. :/
                    acnode.add_group(me_key, shape.name, shape.name, (shape.name,))
                    animdata_shapes[channel_key] = (acnode, me, shape)

    animdata_cameras = {}
    for cam_obj, cam_key in scene_data.data_cameras.items():
        cam = cam_obj.bdata.data
        acnode_lens = AnimationCurveNodeWrapper(cam_key, 'CAMERA_FOCAL', force_key, force_sek, (cam.lens,))
        acnode_focus_distance = AnimationCurveNodeWrapper(cam_key, 'CAMERA_FOCUS_DISTANCE', force_key,
                                                          force_sek, (cam.dof.focus_distance,))
        animdata_cameras[cam_key] = (acnode_lens, acnode_focus_distance, cam)

    # Get all parent bdata of animated dupli instances, so that we can quickly identify which instances in
    # `depsgraph.object_instances` are animated and need their ObjectWrappers' matrices updated each frame.
    dupli_parent_bdata = {dup.get_parent().bdata for dup in animdata_ob if dup.is_dupli}
    has_animated_duplis = bool(dupli_parent_bdata)

    # Initialize keyframe times array. Each AnimationCurveNodeWrapper will share the same instance.
    # `np.arange` excludes the `stop` argument like when using `range`, so we use np.nextafter to get the next
    # representable value after f_end and use that as the `stop` argument instead.
    currframes = np.arange(f_start, np.nextafter(f_end, np.inf), step=bake_step)

    # Convert from Blender time to FBX time.
    fps = scene.render.fps / scene.render.fps_base
    real_currframes = currframes - f_start if start_zero else currframes
    real_currframes = (real_currframes / fps * FBX_KTIME).astype(np.int64)

    # Generator that yields the animated values of each frame in order.
    def frame_values_gen():
        # Precalculate integer frames and subframes.
        int_currframes = currframes.astype(int)
        subframes = currframes - int_currframes

        # Create simpler iterables that return only the values we care about.
        animdata_shapes_only = [shape for _anim_shape, _me, shape in animdata_shapes.values()]
        animdata_cameras_only = [camera for _anim_camera_lens, _anim_camera_focus_distance, camera
                                 in animdata_cameras.values()]
        # Previous frame's rotation for each object in animdata_ob, this will be updated each frame.
        animdata_ob_p_rots = p_rots.values()

        # Iterate through each frame and yield the values for that frame.
        # Iterating .data, the memoryview of an array, is faster than iterating the array directly.
        for int_currframe, subframe in zip(int_currframes.data, subframes.data):
            scene.frame_set(int_currframe, subframe=subframe)

            if has_animated_duplis:
                # Changing the scene's frame invalidates existing dupli instances. To get the updated matrices of duplis
                # for this frame, we must get the duplis from the depsgraph again.
                for dup in depsgraph.object_instances:
                    if (parent := dup.parent) and parent.original in dupli_parent_bdata:
                        # ObjectWrapper caches its instances. Attempting to create a new instance updates the existing
                        # ObjectWrapper instance with the current frame's matrix and then returns the existing instance.
                        ObjectWrapper(dup)
            next_p_rots = []
            for ob_obj, p_rot in zip(animdata_ob, animdata_ob_p_rots):
                # We compute baked loc/rot/scale for all objects (rot being euler-compat with previous value!).
                loc, rot, scale, _m, _mr = ob_obj.fbx_object_tx(scene_data, rot_euler_compat=p_rot)
                next_p_rots.append(rot)
                yield from loc
                yield from rot
                yield from scale
            animdata_ob_p_rots = next_p_rots
            for shape in animdata_shapes_only:
                yield shape.value
            for camera in animdata_cameras_only:
                yield camera.lens
                yield camera.dof.focus_distance
            # PROTOWLF addition - get value of custom properties at this time
            for customproperty in animdata_customproperties:
                custompropertyname, propertyowner, ob_obj, acnode = animdata_customproperties[customproperty]
                yield propertyowner[customproperty] # value of custom property at this time
            # PROTOWLF addition - get value of child shapekey properties at this time
            for customproperty in animdata_childshapekeyproperties:
                shapekeyname, meshowner, ob_obj, acnode = animdata_childshapekeyproperties[customproperty]
                yield meshowner.data.shape_keys.key_blocks[shapekeyname].value # value of shapekey at this time
                

    # Providing `count` to np.fromiter pre-allocates the array, avoiding extra memory allocations while iterating.
    num_ob_values = len(animdata_ob) * 9  # Location, rotation and scale, each of which have x, y, and z components
    num_shape_values = len(animdata_shapes)  # Only 1 value per shape key
    num_camera_values = len(animdata_cameras) * 2  # Focal length (`.lens`) and focus distance
    num_customproperty_values = len(animdata_customproperties) # PROTOWLF addition
    num_childshapekeyproperty_values = len(animdata_childshapekeyproperties) # PROTOWLF addition
    num_values_per_frame = num_ob_values + num_shape_values + num_camera_values + num_customproperty_values + num_childshapekeyproperty_values # PROTOWLF addition - num_customproperty_values, num_childshapekeyproperty_values
    num_frames = len(real_currframes)
    all_values_flat = np.fromiter(frame_values_gen(), dtype=float, count=num_frames * num_values_per_frame)

    # Restore the scene's current frame.
    scene.frame_set(back_currframe, subframe=0.0)

    # View such that each column is all values for a single frame and each row is all values for a single curve.
    all_values = all_values_flat.reshape(num_frames, num_values_per_frame).T
    # Split into views of the arrays for each curve type.
    split_at = [num_ob_values, num_shape_values, num_camera_values, num_customproperty_values, num_childshapekeyproperty_values] # PROTOWLF addition - num_customproperty_values, num_childshapekeyproperty_values
    # For unequal sized splits, np.split takes indices to split at, which can be acquired through a cumulative sum
    # across the list.
    # The last value isn't needed, because the last split is assumed to go to the end of the array.
    split_at = np.cumsum(split_at[:-1])
    
    # PROTOWLF addition - all_customproperty_values, all_childshapekeyproperty_values
    all_ob_values, all_shape_key_values, all_camera_values, all_customproperty_values, all_childshapekeyproperty_values = np.split(all_values, split_at)

    all_anims = []
    
    root_bone_loc_index = -1

    # Set location/rotation/scale curves.
    # Split into equal sized views of the arrays for each object.
    split_into = len(animdata_ob)
    per_ob_values = np.split(all_ob_values, split_into) if split_into > 0 else ()
    for anims, ob_values in zip(animdata_ob.values(), per_ob_values):
        # Split again into equal sized views of the location, rotation and scaling arrays.
        loc_xyz, rot_xyz, sca_xyz = np.split(ob_values, 3)
        # In-place convert from Blender rotation to FBX rotation.
        np.rad2deg(rot_xyz, out=rot_xyz)

        anim_loc, anim_rot, anim_scale = anims
        anim_loc.set_keyframes(real_currframes, loc_xyz)
        anim_rot.set_keyframes(real_currframes, rot_xyz)
        anim_scale.set_keyframes(real_currframes, sca_xyz)
        all_anims.extend(anims)
    
    if len(all_anims) > 4:
        root_bone_loc_index = 4
    elif len(all_anims) > 0:
        root_bone_loc_index = 0
    
    # Set camera curves.
    # Split into equal sized views of the arrays for each camera.
    split_into = len(animdata_cameras)
    per_camera_values = np.split(all_camera_values, split_into) if split_into > 0 else ()
    zipped = zip(animdata_cameras.values(), per_camera_values)
    for (anim_camera_lens, anim_camera_focus_distance, _camera), (lens_values, focus_distance_values) in zipped:
        # In-place convert from Blender focus distance to FBX.
        focus_distance_values *= (1000 * gscale)
        anim_camera_lens.set_keyframes(real_currframes, lens_values)
        anim_camera_focus_distance.set_keyframes(real_currframes, focus_distance_values)
        all_anims.append(anim_camera_lens)
        all_anims.append(anim_camera_focus_distance)
    
    simplified_anims_count = len(all_anims)
    
    # Set shape key curves.
    # There's only one array per shape key, so there's no need to split `all_shape_key_values`.
    for (anim_shape, _me, _shape), shape_key_values in zip(animdata_shapes.values(), all_shape_key_values):
        # PROTOWLF addition - Skip if all zero?
        if not proto_settings.export_zeroed_shapekeys and len(shape_key_values) > 0 and shape_key_values[0] == 0 and all_equal(shape_key_values):
            continue
        
        # In-place convert from Blender Shape Key Value to FBX Deform Percent.
        shape_key_values *= 100.0
        
        anim_shape.set_keyframes(real_currframes, shape_key_values)
        #print("-------------------")
        #print("shapekey: " + _shape.name)
        #for value in shape_key_values[0:10]:
        #    print(str(value))
        #print("-------------------")
        all_anims.append(anim_shape)
        proto_data.has_shapekey_animation = True # PROTOWLF addition
    
    # PROTOWLF addition - set custom properties
    for (customproperty, propertyowner, ob_obj, acnode), customproperty_values in zip(animdata_customproperties.values(), all_customproperty_values):
        # Skip if all zero?
        if not proto_settings.export_zeroed_custom_properties and len(customproperty_values) > 0 and customproperty_values[0] == 0 and all_equal(customproperty_values):
            continue
        
        acnode.set_keyframes(real_currframes, customproperty_values)
        #print("-------------------")
        #print("customproperty: " + customproperty)
        #for value in customproperty_values:
        #    print(str(value))
        #print("-------------------")
        all_anims.append(acnode)
    
    # PROTOWLF addition - set child shapekey properties
    for (shapekeyname, meshowner, ob_obj, acnode), childshapekeyproperty_values in zip(animdata_childshapekeyproperties.values(), all_childshapekeyproperty_values):
        # Skip if all zero?
        if not proto_settings.export_zeroed_shapekeys and len(childshapekeyproperty_values) > 0 and childshapekeyproperty_values[0] == 0 and all_equal(childshapekeyproperty_values):
            continue
        
        # Unlike mesh shape keys, do NOT convert from 0-1 to FBX Deform Percent (0-100)
        # UE4 / UE5 will not import this correctly at 0-100!
        # Instead users have a scale option in case other importers behave differently
        childshapekeyproperty_values *= proto_settings.armature_shapekey_scale
        
        acnode.set_keyframes(real_currframes, childshapekeyproperty_values)
        #print("-------------------")
        #print("child shapekey: " + shapekeyname)
        #for value in childshapekeyproperty_values:
        #    print(str(value))
        #print("-------------------")
        all_anims.append(acnode)
    
    animations = {}

    # And now, produce final data (usable by FBX export code)
    for i, anim in enumerate(all_anims):
        # PROTOWLF addition - UE4 / UE5 importer has a bug where it gets the wrong frame count / fps
        # if an anim doesn't have enough keyframes on any bone tracks (just start+end is not enough)
        # To work around this, do not simplify the root bone (increases file size a little, but reasonable)
        # NOTE: Unreal will strip out the Armature if it's named 'Armature', so we don't do this on
        # that bone track.
        if i != root_bone_loc_index or not proto_settings.dont_simplify_root_bone:
            anim.simplify(simplify_fac, bake_step, force_keep)
        
        if not anim:
            continue
        for obj_key, group_key, group, fbx_group, fbx_gname in anim.get_final_data(scene, ref_id, force_keep):
            #print("===================")
            #print("obj_key: " + obj_key)
            #print("group_key: " + group_key)
            #print("fbx_group: " + fbx_group)
            #print("fbx_gname: " + fbx_gname)
            #print(group)
            #print("===================")
            anim_data = animations.setdefault(obj_key, ("dummy_unused_key", {}))
            anim_data[1][fbx_group] = (group_key, group, fbx_gname)

    astack_key = get_blender_anim_stack_key(scene, ref_id)
    alayer_key = get_blender_anim_layer_key(scene, ref_id)
    
    name = get_blenderID_name(ref_id) if ref_id else scene.name
    #print("animation name pre: " + name)
    if proto_settings.skip_armature_object:
        name_split = name.split("|")
        if len(name_split) > 1:
            name = name_split[1]
            for substr in name_split[2:]:
                name += "|" + substr
    #print("animation name: " + name)
    name = name.encode()
    
    
    if start_zero:
        f_end -= f_start
        f_start = 0.0
    
    return (astack_key, animations, alayer_key, name, f_start, f_end) if animations else None


def fbx_animations(scene_data, proto_settings, proto_data):
    """
    Generate global animation data from objects.
    """
    scene = scene_data.scene
    animations = []
    animated = set()
    frame_start = 1e100
    frame_end = -1e100

    def add_anim(animations, animated, anim):
        nonlocal frame_start, frame_end
        if anim is not None:
            animations.append(anim)
            f_start, f_end = anim[4:6]
            if f_start < frame_start:
                frame_start = f_start
            if f_end > frame_end:
                frame_end = f_end

            _astack_key, astack, _alayer_key, _name, _fstart, _fend = anim
            for elem_key, (alayer_key, acurvenodes) in astack.items():
                for fbx_prop, (acurvenode_key, acurves, acurvenode_name) in acurvenodes.items():
                    animated.add((elem_key, fbx_prop))

    # Per-NLA strip animstacks.
    if scene_data.settings.bake_anim_use_nla_strips:
        strips = []
        ob_actions = []
        for ob_obj in scene_data.objects:
            # NLA tracks only for objects, not bones!
            if not ob_obj.is_object:
                continue
            ob = ob_obj.bdata  # Back to real Blender Object.
            if not ob.animation_data:
                continue

            # Some actions are read-only, one cause is being in NLA tweakmode
            restore_use_tweak_mode = ob.animation_data.use_tweak_mode
            if ob.animation_data.is_property_readonly('action'):
                ob.animation_data.use_tweak_mode = False

            # We have to remove active action from objects, it overwrites strips actions otherwise...
            ob_actions.append((ob, ob.animation_data.action, restore_use_tweak_mode))
            ob.animation_data.action = None
            for track in ob.animation_data.nla_tracks:
                if track.mute:
                    continue
                for strip in track.strips:
                    if strip.mute:
                        continue
                    strips.append(strip)
                    strip.mute = True

        for strip in strips:
            strip.mute = False
            add_anim(animations, animated,
                     fbx_animations_do(scene_data, proto_settings, proto_data, strip, strip.frame_start, strip.frame_end, True, force_keep=True))
            strip.mute = True
            scene.frame_set(scene.frame_current, subframe=0.0)

        for strip in strips:
            strip.mute = False

        for ob, ob_act, restore_use_tweak_mode in ob_actions:
            ob.animation_data.action = ob_act
            ob.animation_data.use_tweak_mode = restore_use_tweak_mode

    # All actions.
    if scene_data.settings.bake_anim_use_all_actions:
        
        # PROTOWLF modification -- find_validate_action_slot and restore_object defs moved outside this function
        
        for ob_obj in scene_data.objects:
            # Actions only for objects, not bones!
            if not ob_obj.is_object:
                continue
            
            ob = ob_obj.bdata  # Back to real Blender Object.

            if not ob.animation_data:
                continue  # Do not export animations for objects that are absolutely not animated, see T44386.
            
            if ob.animation_data.is_property_readonly('action'):
                continue  # Cannot re-assign 'active action' to this object (usually related to NLA usage, see T48089).
            
            # We can't play with animdata and actions and get back to org state easily.
            # So we have to add a temp copy of the object to the scene, animate it, and remove it... :/
            ob_copy = ob.copy()
            # Great, have to handle bones as well if needed...
            pbones_matrices = [pbo.matrix_basis.copy() for pbo in ob.pose.bones] if ob.type == 'ARMATURE' else ...
            
            org_act = ob.animation_data.action
            if bpy.app.version >= (4, 4, 0): # PROTOWLF addition - support versions before action slots
                org_act_slot = ob.animation_data.action_slot
            path_resolve = ob.path_resolve
            
            for act in bpy.data.actions:
                # PROTOWLF addition
                if proto_settings.bake_anim_use_action_filter and act not in proto_settings.bake_anim_action_filter:
                    #print("Skipping action '" + act.name + "', not in action filter")
                    continue
                
                # PROTOWLF addition - support versions before action slots
                if bpy.app.version >= (4, 4, 0):
                    # For now, *all* paths in the action must be valid for the object, to validate the action.
                    # Unless that action was already assigned to the object!
                    if act == org_act:
                        act_slot = org_act_slot
                    else:
                        act_slot = find_validate_action_slot(act, path_resolve)
                    if not act_slot:
                        #print("Skipping action '" + act.name + "', could not find valid slot")
                        continue
                
                # Set the action. PROTOWLF addition: also set on helper armature if necessary
                ob.animation_data.action = act
                if ob in proto_settings.helper_armatures:
                    proto_settings.helper_armatures[ob].animation_data.action = act
                if bpy.app.version >= (4, 4, 0): # PROTOWLF addition - support versions before action slots
                    #print("setting action slot: " + act_slot.name_display)
                    ob.animation_data.action_slot = act_slot
                    if ob in proto_settings.helper_armatures:
                        proto_settings.helper_armatures[ob].animation_data.action_slot = act_slot
                
                frame_start, frame_end = act.frame_range  # sic!
                add_anim(animations, animated,
                         fbx_animations_do(scene_data, proto_settings, proto_data, (ob, act), frame_start, frame_end, True,
                                           objects={ob_obj}, force_keep=True))
                
                # Reset the action. PROTOWLF addition: also reset on helper armature if necessary
                # Ugly! :/
                if pbones_matrices is not ...:
                    for pbo, mat in zip(ob.pose.bones, pbones_matrices):
                        pbo.matrix_basis = mat.copy()
                ob.animation_data.action = org_act
                if ob in proto_settings.helper_armatures:
                    proto_settings.helper_armatures[ob].animation_data.action = org_act
                if bpy.app.version >= (4, 4, 0): # PROTOWLF addition - support versions before action slots
                    if org_act:
                        ob.animation_data.action_slot = org_act_slot
                        if ob in proto_settings.helper_armatures:
                            proto_settings.helper_armatures[ob].animation_data.action_slot = org_act_slot
                restore_object(ob, ob_copy)
                scene.frame_set(scene.frame_current, subframe=0.0)

            if pbones_matrices is not ...:
                for pbo, mat in zip(ob.pose.bones, pbones_matrices):
                    pbo.matrix_basis = mat.copy()
            ob.animation_data.action = org_act
            if bpy.app.version >= (4, 4, 0): # PROTOWLF addition - support versions before action slots
                if org_act:
                    ob.animation_data.action_slot = org_act_slot

            bpy.data.objects.remove(ob_copy)
            scene.frame_set(scene.frame_current, subframe=0.0)

    # Global (containing everything) animstack, only if not exporting NLA strips and/or all actions.
    # PROTOWLF addition - this one did not set force_keep and I have no idea why...
    if not scene_data.settings.bake_anim_use_nla_strips and not scene_data.settings.bake_anim_use_all_actions:
        add_anim(animations, animated, fbx_animations_do(scene_data, proto_settings, proto_data, None, scene.frame_start, scene.frame_end, False, force_keep=True))

    # Be sure to update all matrices back to org state!
    scene.frame_set(scene.frame_current, subframe=0.0)

    return animations, animated, frame_start, frame_end


def fbx_data_from_scene(scene, depsgraph, settings, proto_settings, proto_data):
    """
    Do some pre-processing over scene's data...
    """
    objtypes = settings.object_types
    dp_objtypes = objtypes - {'ARMATURE'}  # Armatures are not supported as dupli instances currently...
    perfmon = PerfMon()
    perfmon.level_up()

    # ##### Gathering data...

    perfmon.step("FBX export prepare: Wrapping Objects...")

    # This is rather simple for now, maybe we could end generating templates with most-used values
    # instead of default ones?
    objects = {}  # Because we do not have any ordered set...
    for ob in settings.context_objects:
        if ob.type not in objtypes:
            continue
        ob_obj = ObjectWrapper(ob)
        objects[ob_obj] = None
        # Duplis...
        for dp_obj in ob_obj.dupli_list_gen(depsgraph):
            if dp_obj.type not in dp_objtypes:
                continue
            objects[dp_obj] = None

    perfmon.step("FBX export prepare: Wrapping Data (lamps, cameras, empties)...")

    data_lights = {ob_obj.bdata.data: get_blenderID_key(ob_obj.bdata.data)
                   for ob_obj in objects if ob_obj.type == 'LIGHT'}
    # Unfortunately, FBX camera data contains object-level data (like position, orientation, etc.)...
    data_cameras = {ob_obj: get_blenderID_key(ob_obj.bdata.data)
                    for ob_obj in objects if ob_obj.type == 'CAMERA'}
    # Yep! Contains nothing, but needed!
    data_empties = {ob_obj: get_blender_empty_key(ob_obj.bdata)
                    for ob_obj in objects if ob_obj.type == 'EMPTY'}

    perfmon.step("FBX export prepare: Wrapping Meshes...")

    data_meshes = {}
    for ob_obj in objects:
        if ob_obj.type not in BLENDER_OBJECT_TYPES_MESHLIKE:
            continue
        ob = ob_obj.bdata
        org_ob_obj = None

        # Do not want to systematically recreate a new mesh for dupliobject instances, kind of break purpose of those.
        if ob_obj.is_dupli:
            org_ob_obj = ObjectWrapper(ob)  # We get the "real" object wrapper from that dupli instance.
            if org_ob_obj in data_meshes:
                data_meshes[ob_obj] = data_meshes[org_ob_obj]
                continue

        # There are 4 different cases for what we need to do with the original data of each Object:
        # 1) The original data can be used without changes.
        # 2) A copy of the original data needs to be made.
        #  - If an export option modifies the data, e.g. Triangulate Faces is enabled.
        #  - If the Object has Object-linked materials. This is because our current mapping of materials to FBX requires
        #    that multiple Objects sharing a single mesh must have the same materials.
        # 3) The Object needs to be converted to a mesh.
        #  - All mesh-like Objects that are not meshes need to be converted to a mesh in order to be exported.
        # 4) The Object needs to be evaluated and then converted to a mesh.
        #  - Whenever use_mesh_modifiers is enabled and either there are modifiers to apply or the Object needs to be
        #    converted to a mesh.
        # If multiple cases apply to an Object, then only the last applicable case is relevant.
        do_copy = any(ms.link == 'OBJECT' for ms in ob.material_slots) or settings.use_triangles
        do_convert = ob.type in BLENDER_OTHER_OBJECT_TYPES
        do_evaluate = do_convert and settings.use_mesh_modifiers

        # If the Object is a mesh, and we're applying modifiers, check if there are actually any modifiers to apply.
        # If there are then the mesh will need to be evaluated, and we may need to make some temporary changes to the
        # modifiers or scene before the mesh is evaluated.
        backup_pose_positions = []
        tmp_mods = []
        if ob.type == 'MESH' and settings.use_mesh_modifiers:
            # No need to create a new mesh in this case, if no modifier is active!
            last_subsurf = None
            for mod in ob.modifiers:
                # For meshes, when armature export is enabled, disable Armature modifiers here!
                # XXX Temp hacks here since currently we only have access to a viewport depsgraph...
                #
                # NOTE: We put armature to the rest pose instead of disabling it so we still
                # have vertex groups in the evaluated mesh.
                if mod.type == 'ARMATURE' and 'ARMATURE' in settings.object_types:
                    object = mod.object
                    if object and object.type == 'ARMATURE':
                        armature = object.data
                        # If armature is already in REST position, there's nothing to back-up
                        # This cuts down on export time dramatically, if all armatures are already in REST position
                        # by not triggering dependency graph update
                        if armature.pose_position != 'REST':
                            backup_pose_positions.append((armature, armature.pose_position))
                            armature.pose_position = 'REST'
                elif mod.show_render or mod.show_viewport:
                    # If exporting with subsurf collect the last Catmull-Clark subsurf modifier
                    # and disable it. We can use the original data as long as this is the first
                    # found applicable subsurf modifier.
                    if settings.use_subsurf and mod.type == 'SUBSURF' and mod.subdivision_type == 'CATMULL_CLARK':
                        if last_subsurf:
                            do_evaluate = True
                        last_subsurf = mod
                    else:
                        do_evaluate = True
            if settings.use_subsurf and last_subsurf:
                # XXX: When exporting with subsurf information temporarily disable
                # the last subsurf modifier.
                tmp_mods.append((last_subsurf, last_subsurf.show_render, last_subsurf.show_viewport))
                last_subsurf.show_render = False
                last_subsurf.show_viewport = False

        if do_evaluate:
            # If modifiers has been altered need to update dependency graph.
            if backup_pose_positions or tmp_mods:
                depsgraph.update()
            ob_to_convert = ob.evaluated_get(depsgraph)
            # NOTE: The dependency graph might be re-evaluating multiple times, which could
            # potentially free the mesh created early on. So we put those meshes to bmain and
            # free them afterwards. Not ideal but ensures correct ownership.
            # This also converts non-mesh Objects to Mesh data.
            tmp_me = bpy.data.meshes.new_from_object(
                ob_to_convert, preserve_all_data_layers=True, depsgraph=depsgraph)

            # Usually the materials of the evaluated Object converted to a Mesh will be the same as the original
            # Object, but modifiers, such as Geometry Nodes, can change the materials.
            orig_mats = [slot.material for slot in ob.material_slots]
            eval_mats = list(tmp_me.materials)
            if orig_mats != eval_mats:
                # An object-linked material slot replaces the material on the data at the slot's index. If applying
                # modifiers changes the materials on the data, the object-linked material slot will replace the new
                # material at the same index as before.
                for i, slot in zip(range(len(eval_mats)), ob.material_slots):
                    if slot.link == 'OBJECT':
                        eval_mats[i] = slot.material
                # Override the default behavior of getting materials from `ob_obj.bdata.material_slots`.
                ob_obj.override_materials = tuple(eval_mats)
        elif do_convert:
            tmp_me = bpy.data.meshes.new_from_object(ob, preserve_all_data_layers=True, depsgraph=depsgraph)
        elif do_copy:
            # bpy.data.meshes.new_from_object removes shape keys (see #104714), so create a copy of the mesh instead.
            tmp_me = ob.data.copy()
        else:
            tmp_me = None

        if tmp_me is None:
            # Use the original data of this Object.
            data_meshes[ob_obj] = (get_blenderID_key(ob.data), ob.data, False)
        else:
            # Triangulate the mesh if requested
            if settings.use_triangles:
                import bmesh
                bm = bmesh.new()
                bm.from_mesh(tmp_me)
                bmesh.ops.triangulate(bm, faces=bm.faces)
                bm.to_mesh(tmp_me)
                bm.free()
            # A temporary mesh was created for this Object, which should be deleted once the export is complete.
            data_meshes[ob_obj] = (get_blenderID_key(tmp_me), tmp_me, True)

        # Change armatures back.
        for armature, pose_position in backup_pose_positions:
            #print((armature, pose_position)) PROTOWLF addition - commenting out, seems like an oversight
            armature.pose_position = pose_position
            # Update now, so we don't leave modified state after last object was exported.
        # Re-enable temporary disabled modifiers.
        for mod, show_render, show_viewport in tmp_mods:
            mod.show_render = show_render
            mod.show_viewport = show_viewport
        if backup_pose_positions or tmp_mods:
            depsgraph.update()

        # In case "real" source object of that dupli did not yet still existed in data_meshes, create it now!
        if org_ob_obj is not None:
            data_meshes[org_ob_obj] = data_meshes[ob_obj]

    perfmon.step("FBX export prepare: Wrapping ShapeKeys...")

    # ShapeKeys.
    data_deformers_shape = {}
    geom_mat_co = settings.global_matrix if settings.bake_space_transform else None
    co_bl_dtype = np.single
    co_fbx_dtype = np.float64
    idx_fbx_dtype = np.int32
    if bpy.app.version >= (5, 1, 0):
        normal_bl_dtype = np.single
        normal_fbx_dtype = np.float64
        geom_mat_no = Matrix(settings.global_matrix_inv_transposed) if settings.bake_space_transform else None
        if geom_mat_no is not None:
            # Remove translation & scaling!
            geom_mat_no.translation = Vector()
            geom_mat_no.normalize()
    
    def empty_verts_fallbacks():
        if bpy.app.version >= (5, 1, 0):
            """Create fallback arrays for when there are no verts"""
            # FBX does not like empty shapes (makes Unity crash e.g.).
            # To prevent this, we add a vertex that does nothing, but it keeps the shape key intact
            single_vert_co = np.zeros((1, 3), dtype=co_fbx_dtype)
            single_vert_nor = np.zeros((1, 3), dtype=co_fbx_dtype)
            single_vert_idx = np.zeros(1, dtype=idx_fbx_dtype)
            return single_vert_co, single_vert_nor, single_vert_idx
        else:
            """Create fallback arrays for when there are no verts"""
            # FBX does not like empty shapes (makes Unity crash e.g.).
            # To prevent this, we add a vertex that does nothing, but it keeps the shape key intact
            single_vert_co = np.zeros((1, 3), dtype=co_fbx_dtype)
            single_vert_idx = np.zeros(1, dtype=idx_fbx_dtype)
            return single_vert_co, single_vert_idx

    for me_key, me, _free in data_meshes.values():
        if not (me.shape_keys and len(me.shape_keys.key_blocks) > 1):  # We do not want basis-only relative skeys...
            continue
        if me in data_deformers_shape:
            continue

        shapes_key = get_blender_mesh_shape_key(me)

        sk_base = me.shape_keys.key_blocks[0]

        # Get and cache only the cos that we need
        @cache
        def sk_cos(shape_key):
            if shape_key == sk_base:
                _cos = MESH_ATTRIBUTE_POSITION.to_ndarray(me.attributes)
            else:
                _cos = np.empty(len(me.vertices) * 3, dtype=co_bl_dtype)
                shape_key.points.foreach_get("co", _cos)
            return vcos_transformed(_cos, geom_mat_co, co_fbx_dtype)
        
        # Get and cache only the cos that we need (5.1 version)
        @cache
        def sk_cos_nors(shape_key):
            if shape_key == sk_base:
                _cos = MESH_ATTRIBUTE_POSITION.to_ndarray(me.attributes)
            else:
                _cos = np.empty(len(me.vertices) * 3, dtype=co_bl_dtype)
                shape_key.points.foreach_get("co", _cos)
            _nors = np.array(shape_key.normals_vertex_get(), dtype=normal_bl_dtype)
            return (
                vcos_transformed(_cos, geom_mat_co, co_fbx_dtype),
                nors_transformed(_nors, geom_mat_no, normal_fbx_dtype)
            )
        
        if bpy.app.version >= (5, 1, 0):
            for shape in me.shape_keys.key_blocks[1:]:
                # Only write vertices really different from base coordinates!
                relative_key = shape.relative_key
                if shape == relative_key:
                    # Shape is its own relative key, so it does nothing
                    shape_verts_co, shape_verts_nors, shape_verts_idx = empty_verts_fallbacks()
                else:
                    sv_cos_nors = sk_cos_nors(shape)
                    ref_cos_nors = sk_cos_nors(shape.relative_key)
    
                    # Exclude cos similar to ref_cos and get the indices of the cos that remain
                    shape_verts_co, shape_verts_nors, shape_verts_idx = shape_difference_exclude_similar(
                        sv_cos_nors, ref_cos_nors)
    
                    if not shape_verts_co.size:
                        shape_verts_co, shape_verts_nors, shape_verts_idx = empty_verts_fallbacks()
                    else:
                        # Ensure the indices are of the correct type
                        shape_verts_idx = astype_view_signedness(shape_verts_idx, idx_fbx_dtype)
    
                channel_key, geom_key = get_blender_mesh_shape_channel_key(me, shape)
                data = (channel_key, geom_key, shape_verts_co, shape_verts_nors, shape_verts_idx)
                data_deformers_shape.setdefault(me, (me_key, shapes_key, {}))[2][shape] = data
        else:
            for shape in me.shape_keys.key_blocks[1:]:
                # Only write vertices really different from base coordinates!
                relative_key = shape.relative_key
                if shape == relative_key:
                    # Shape is its own relative key, so it does nothing
                    shape_verts_co, shape_verts_idx = empty_verts_fallbacks()
                else:
                    sv_cos = sk_cos(shape)
                    ref_cos = sk_cos(shape.relative_key)
    
                    # Exclude cos similar to ref_cos and get the indices of the cos that remain
                    shape_verts_co, shape_verts_idx = shape_difference_exclude_similar(sv_cos, ref_cos)
    
                    if not shape_verts_co.size:
                        shape_verts_co, shape_verts_idx = empty_verts_fallbacks()
                    else:
                        # Ensure the indices are of the correct type
                        shape_verts_idx = astype_view_signedness(shape_verts_idx, idx_fbx_dtype)
    
                channel_key, geom_key = get_blender_mesh_shape_channel_key(me, shape)
                data = (channel_key, geom_key, shape_verts_co, shape_verts_idx)
                data_deformers_shape.setdefault(me, (me_key, shapes_key, {}))[2][shape] = data

        del sk_cos
        del sk_cos_nors

    perfmon.step("FBX export prepare: Wrapping Armatures...")

    # Armatures!
    data_deformers_skin = {}
    data_bones = {}
    arm_parents = set()
    for ob_obj in tuple(objects):
        if not (ob_obj.is_object and ob_obj.type in {'ARMATURE'}):
            continue
        export_fbx_bin.fbx_skeleton_from_armature(scene, settings, ob_obj, objects, data_meshes,
                                   data_bones, data_deformers_skin, data_empties, arm_parents)
    
    # Generate leaf bones
    data_leaf_bones = []
    if settings.add_leaf_bones:
        data_leaf_bones = fbx_generate_leaf_bones(settings, data_bones)

    perfmon.step("FBX export prepare: Wrapping World...")

    # Some world settings are embedded in FBX materials...
    if scene.world:
        data_world = {scene.world: get_blenderID_key(scene.world)}
    else:
        data_world = {}

    perfmon.step("FBX export prepare: Wrapping Materials...")

    # TODO: Check all the material stuff works even when they are linked to Objects
    #       (we can then have the same mesh used with different materials...).
    #       *Should* work, as FBX always links its materials to Models (i.e. objects).
    #       XXX However, material indices would probably break...
    data_materials = {}
    for ob_obj in objects:
        # If obj is not a valid object for materials, wrapper will just return an empty tuple...
        for ma in ob_obj.materials:
            if ma is None:
                continue  # Empty slots!
            # Note theoretically, FBX supports any kind of materials, even GLSL shaders etc.
            # However, I doubt anything else than Lambert/Phong is really portable!
            # Note we want to keep a 'dummy' empty material even when we can't really support it, see T41396.
            ma_data = data_materials.setdefault(ma, (get_blenderID_key(ma), []))
            ma_data[1].append(ob_obj)

    perfmon.step("FBX export prepare: Wrapping Textures...")

    # Note FBX textures also hold their mapping info.
    # TODO: Support layers?
    data_textures = {}
    # FbxVideo also used to store static images...
    data_videos = {}
    # For now, do not use world textures, don't think they can be linked to anything FBX wise...
    for ma in data_materials.keys():
        # Note: with nodal shaders, we'll could be generating much more textures, but that's kind of unavoidable,
        #       given that textures actually do not exist anymore in material context in Blender...
        ma_wrap = node_shader_utils.PrincipledBSDFWrapper(ma, is_readonly=True)
        for sock_name, fbx_name in export_fbx_bin.PRINCIPLED_TEXTURE_SOCKETS_TO_FBX:
            tex = getattr(ma_wrap, sock_name)
            if tex is None or tex.image is None:
                continue
            blender_tex_key = (ma, sock_name)
            data_textures[blender_tex_key] = (get_blender_nodetexture_key(*blender_tex_key), fbx_name)

            img = tex.image
            vid_data = data_videos.setdefault(img, (get_blenderID_key(img), []))
            vid_data[1].append(blender_tex_key)

    perfmon.step("FBX export prepare: Wrapping Animations...")

    # Animation...
    animations = ()
    animated = set()
    frame_start = scene.frame_start
    frame_end = scene.frame_end
    if settings.bake_anim:
        # From objects & bones only for a start.
        # Kind of hack, we need a temp scene_data for object's space handling to bake animations...
        tmp_scdata = FBXExportData(
            None, None, None,
            settings, scene, depsgraph, objects, None, None, 0.0, 0.0,
            data_empties, data_lights, data_cameras, data_meshes, None,
            data_bones, data_leaf_bones, data_deformers_skin, data_deformers_shape,
            data_world, data_materials, data_textures, data_videos,
        )
        animations, animated, frame_start, frame_end = fbx_animations(tmp_scdata, proto_settings, proto_data)
    
    
    # PROTOWLF addition - Remove meshes from export
    if proto_settings.skip_meshes_if_no_shapekey_animation:
        # Remove meshes from export if we are not exporting any shapekey animation
        # NOTE: must be real shapekey animation, not shapekeys as custom properties
        #
        # The reason we remove meshes (rather than filter them before running the export)
        # is because to filter them we'd have to crawl every frame of every animation,
        # which we definitely do not want to do. We want to lean on the anim crawling that
        # the export process already does. Therefore, we strip out meshes here
        if not proto_data.has_shapekey_animation:
            #print("Removing meshes from export")
            # for each mesh, remove entry in objects
            for ob_obj, me in data_meshes.items():
                del objects[ob_obj]
            # nuke meshes, data_deformers_skin, materials, and textures
            data_meshes.clear()
            data_materials.clear()
            data_textures.clear()
            data_deformers_skin.clear()
    
    # ##### Creation of templates...

    perfmon.step("FBX export prepare: Generating templates...")

    templates = {}
    templates[b"GlobalSettings"] = export_fbx_bin.fbx_template_def_globalsettings(scene, settings, nbr_users=1)

    if data_empties:
        templates[b"Null"] = export_fbx_bin.fbx_template_def_null(scene, settings, nbr_users=len(data_empties))

    if data_lights:
        templates[b"Light"] = export_fbx_bin.fbx_template_def_light(scene, settings, nbr_users=len(data_lights))

    if data_cameras:
        templates[b"Camera"] = export_fbx_bin.fbx_template_def_camera(scene, settings, nbr_users=len(data_cameras))

    if data_bones:
        templates[b"Bone"] = export_fbx_bin.fbx_template_def_bone(scene, settings, nbr_users=len(data_bones))

    if data_meshes:
        nbr = len({me_key for me_key, _me, _free in data_meshes.values()})
        if data_deformers_shape:
            nbr += sum(len(shapes[2]) for shapes in data_deformers_shape.values())
        templates[b"Geometry"] = export_fbx_bin.fbx_template_def_geometry(scene, settings, nbr_users=nbr)

    if objects:
        templates[b"Model"] = export_fbx_bin.fbx_template_def_model(scene, settings, nbr_users=len(objects))

    if arm_parents:
        # Number of Pose|BindPose elements should be the same as number of meshes-parented-to-armatures
        templates[b"BindPose"] = export_fbx_bin.fbx_template_def_pose(scene, settings, nbr_users=len(arm_parents))

    if data_deformers_skin or data_deformers_shape:
        nbr = 0
        if data_deformers_skin:
            nbr += len(data_deformers_skin)
            nbr += sum(len(clusters) for def_me in data_deformers_skin.values() for a, b, clusters in def_me.values())
        if data_deformers_shape:
            nbr += len(data_deformers_shape)
            nbr += sum(len(shapes[2]) for shapes in data_deformers_shape.values())
        assert(nbr != 0)
        templates[b"Deformers"] = export_fbx_bin.fbx_template_def_deformer(scene, settings, nbr_users=nbr)

    # No world support in FBX...
    """
    if data_world:
        templates[b"World"] = fbx_template_def_world(scene, settings, nbr_users=len(data_world))
    """

    if data_materials:
        templates[b"Material"] = export_fbx_bin.fbx_template_def_material(scene, settings, nbr_users=len(data_materials))

    if data_textures:
        templates[b"TextureFile"] = export_fbx_bin.fbx_template_def_texture_file(scene, settings, nbr_users=len(data_textures))

    if data_videos:
        templates[b"Video"] = export_fbx_bin.fbx_template_def_video(scene, settings, nbr_users=len(data_videos))

    if animations:
        nbr_astacks = len(animations)
        nbr_acnodes = 0
        nbr_acurves = 0
        for _astack_key, astack, _al, _n, _fs, _fe in animations:
            for _alayer_key, alayer in astack.values():
                for _acnode_key, acnode, _acnode_name in alayer.values():
                    nbr_acnodes += 1
                    for _acurve_key, _dval, (keys, _values), acurve_valid in acnode.values():
                        if len(keys):
                            nbr_acurves += 1

        templates[b"AnimationStack"] = export_fbx_bin.fbx_template_def_animstack(scene, settings, nbr_users=nbr_astacks)
        # Would be nice to have one layer per animated object, but this seems tricky and not that well supported.
        # So for now, only one layer per anim stack.
        templates[b"AnimationLayer"] = export_fbx_bin.fbx_template_def_animlayer(scene, settings, nbr_users=nbr_astacks)
        templates[b"AnimationCurveNode"] = export_fbx_bin.fbx_template_def_animcurvenode(scene, settings, nbr_users=nbr_acnodes)
        templates[b"AnimationCurve"] = export_fbx_bin.fbx_template_def_animcurve(scene, settings, nbr_users=nbr_acurves)

    templates_users = sum(tmpl.nbr_users for tmpl in templates.values())

    # ##### Creation of connections...

    perfmon.step("FBX export prepare: Generating Connections...")

    connections = []

    # Objects (with classical parenting).
    for ob_obj in objects:
    
        # PROTOWLF addition - support skip_armature_object
        if proto_settings.skip_armature_object and ob_obj.type == "ARMATURE":
            continue
        
        # Bones are handled later.
        if not ob_obj.is_bone:
            par_obj = ob_obj.parent
            # Meshes parented to armature are handled separately, yet we want the 'no parent' connection (0).
            if par_obj and ob_obj.has_valid_parent(objects) and (par_obj, ob_obj) not in arm_parents:
                connections.append((b"OO", ob_obj.fbx_uuid, par_obj.fbx_uuid, None))
            else:
                connections.append((b"OO", ob_obj.fbx_uuid, 0, None))

    # Armature & Bone chains.
    for bo_obj in data_bones.keys():
        par_obj = bo_obj.parent
        if par_obj not in objects:
            continue
        
        # PROTOWLF addition - support skip_armature_object, root bones have to be connected to None
        if proto_settings.skip_armature_object and par_obj.type == "ARMATURE":
            connections.append((b"OO", bo_obj.fbx_uuid, 0, None))
            continue
        
        connections.append((b"OO", bo_obj.fbx_uuid, par_obj.fbx_uuid, None))

    # Object data.
    for ob_obj in objects:
        if ob_obj.is_bone:
            bo_data_key = data_bones[ob_obj]
            connections.append((b"OO", get_fbx_uuid_from_key(bo_data_key), ob_obj.fbx_uuid, None))
        else:
            if ob_obj.type == 'LIGHT':
                light_key = data_lights[ob_obj.bdata.data]
                connections.append((b"OO", get_fbx_uuid_from_key(light_key), ob_obj.fbx_uuid, None))
            elif ob_obj.type == 'CAMERA':
                cam_key = data_cameras[ob_obj]
                connections.append((b"OO", get_fbx_uuid_from_key(cam_key), ob_obj.fbx_uuid, None))
            elif ob_obj.type == 'EMPTY' or ob_obj.type == 'ARMATURE':
                print("connection.append EMPTY or ARMATURE: ")
                # PROTOWLF addition - support skip_armature_object
                if proto_settings.skip_armature_object and ob_obj.type == "ARMATURE":
                    continue
                
                empty_key = data_empties[ob_obj]
                #print("connection.append EMPTY or ARMATURE: ")
                connections.append((b"OO", get_fbx_uuid_from_key(empty_key), ob_obj.fbx_uuid, None))
            elif ob_obj.type in BLENDER_OBJECT_TYPES_MESHLIKE:
                mesh_key, _me, _free = data_meshes[ob_obj]
                #print("connection.append BLENDER_OBJECT_TYPES_MESHLIKE: mesh_key, " + ob_obj.name)
                connections.append((b"OO", get_fbx_uuid_from_key(mesh_key), ob_obj.fbx_uuid, None))

    # Leaf Bones
    for (_node_name, par_uuid, node_uuid, attr_uuid, _matrix, _hide, _size) in data_leaf_bones:
        connections.append((b"OO", node_uuid, par_uuid, None))
        connections.append((b"OO", attr_uuid, node_uuid, None))

    # 'Shape' deformers (shape keys, only for meshes currently)...
    for me_key, shapes_key, shapes in data_deformers_shape.values():
        # shape -> geometry
        connections.append((b"OO", get_fbx_uuid_from_key(shapes_key), get_fbx_uuid_from_key(me_key), None))
        if bpy.app.version >= (5, 1, 0):
            for channel_key, geom_key, _shape_verts_co, _shape_verts_nors, _shape_verts_idx in shapes.values():
                # shape channel -> shape
                connections.append((b"OO", get_fbx_uuid_from_key(channel_key), get_fbx_uuid_from_key(shapes_key), None))
                # geometry (keys) -> shape channel
                connections.append((b"OO", get_fbx_uuid_from_key(geom_key), get_fbx_uuid_from_key(channel_key), None))
        else:
            for channel_key, geom_key, _shape_verts_co, _shape_verts_idx in shapes.values():
                # shape channel -> shape
                connections.append((b"OO", get_fbx_uuid_from_key(channel_key), get_fbx_uuid_from_key(shapes_key), None))
                # geometry (keys) -> shape channel
                connections.append((b"OO", get_fbx_uuid_from_key(geom_key), get_fbx_uuid_from_key(channel_key), None))

    # 'Skin' deformers (armature-to-geometry, only for meshes currently)...
    for arm, deformed_meshes in data_deformers_skin.items():
        for me, (skin_key, ob_obj, clusters) in deformed_meshes.items():
            # skin -> geometry
            mesh_key, _me, _free = data_meshes[ob_obj]
            assert(me == _me)
            connections.append((b"OO", get_fbx_uuid_from_key(skin_key), get_fbx_uuid_from_key(mesh_key), None))
            for bo_obj, clstr_key in clusters.items():
                # cluster -> skin
                connections.append((b"OO", get_fbx_uuid_from_key(clstr_key), get_fbx_uuid_from_key(skin_key), None))
                # bone -> cluster
                connections.append((b"OO", bo_obj.fbx_uuid, get_fbx_uuid_from_key(clstr_key), None))
                

    # Materials
    mesh_material_indices = {}
    for ob_obj in objects:
        ob_mat_idx = 0
        me = None
        if ob_obj.type in BLENDER_OBJECT_TYPES_MESHLIKE:
            _mesh_key, me, _free = data_meshes[ob_obj]
        # NOTE: If a mesh has multiple material slots with the same material, they are combined into one
        # single connexion (slot).
        # Even if duplicate materials were exported without combining them into one slot, keeping duplicate
        # materials separated does not appear to be common behavior of external software when importing FBX.
        # Also, None (empty slots, no material) are always skipped/ignored.
        done_materials_for_object = {None}
        for ma in ob_obj.materials:
            if ma in done_materials_for_object:
                continue
            done_materials_for_object.add(ma)
            ma_key, _ob_objs = data_materials[ma]
            connections.append((b"OO", get_fbx_uuid_from_key(ma_key), ob_obj.fbx_uuid, None))
            # Get index of this material for this object (or dupliobject).
            # Material indices for mesh faces are determined by their order in 'ma to ob' connections.
            # Only materials for meshes currently...
            # Note in case of dupliobjects a same me/ma idx will be generated several times...
            # Should not be an issue in practice, and it's needed in case we export duplis but not the original!
            if ob_obj.type not in BLENDER_OBJECT_TYPES_MESHLIKE:
                continue
            if ma not in mesh_material_indices.setdefault(me, {}):
                mesh_material_indices[me][ma] = ob_mat_idx
            else:
                print("WARNING: Cannot register a valid material index for '{}' from '{}' mesh, '{}' object. "
                      "Most likely, different objects using the same mesh, but different material slots layouts."
                      "".format(ma.name, me.name, ob_obj.name))
            ob_mat_idx += 1

    # Textures
    for (ma, sock_name), (tex_key, fbx_prop) in data_textures.items():
        ma_key, _ob_objs = data_materials[ma]
        # texture -> material properties
        connections.append((b"OP", get_fbx_uuid_from_key(tex_key), get_fbx_uuid_from_key(ma_key), fbx_prop))

    # Images
    for vid, (vid_key, blender_tex_keys) in data_videos.items():
        for blender_tex_key in blender_tex_keys:
            tex_key, _fbx_prop = data_textures[blender_tex_key]
            connections.append((b"OO", get_fbx_uuid_from_key(vid_key), get_fbx_uuid_from_key(tex_key), None))

    # Animations
    for astack_key, astack, alayer_key, _name, _fstart, _fend in animations:
        # Animstack itself is linked nowhere!
        astack_id = get_fbx_uuid_from_key(astack_key)
        # For now, only one layer!
        alayer_id = get_fbx_uuid_from_key(alayer_key)
        connections.append((b"OO", alayer_id, astack_id, None))
        for elem_key, (alayer_key, acurvenodes) in astack.items():
            elem_id = get_fbx_uuid_from_key(elem_key)
            # Animlayer -> animstack.
            # alayer_id = get_fbx_uuid_from_key(alayer_key)
            # connections.append((b"OO", alayer_id, astack_id, None))
            for fbx_prop, (acurvenode_key, acurves, acurvenode_name) in acurvenodes.items():
                # Animcurvenode -> animalayer.
                acurvenode_id = get_fbx_uuid_from_key(acurvenode_key)
                connections.append((b"OO", acurvenode_id, alayer_id, None))
                # Animcurvenode -> object property.
                connections.append((b"OP", acurvenode_id, elem_id, fbx_prop.encode()))
                for fbx_item, (acurve_key, default_value, (keys, values), acurve_valid) in acurves.items():
                    if len(keys):
                        # Animcurve -> Animcurvenode.
                        connections.append((b"OP", get_fbx_uuid_from_key(acurve_key), acurvenode_id, fbx_item.encode()))

    perfmon.level_down()

    # ##### And pack all this!

    return FBXExportData(
        templates, templates_users, connections,
        settings, scene, depsgraph, objects, animations, animated, frame_start, frame_end,
        data_empties, data_lights, data_cameras, data_meshes, mesh_material_indices,
        data_bones, data_leaf_bones, data_deformers_skin, data_deformers_shape,
        data_world, data_materials, data_textures, data_videos,
    )


def fbx_objects_elements(root, scene_data, proto_settings):
    """
    Data (objects, geometry, material, textures, armatures, etc.).
    """
    perfmon = PerfMon()
    perfmon.level_up()
    objects = elem_empty(root, b"Objects")

    perfmon.step("FBX export fetch empties (%d)..." % len(scene_data.data_empties))

    for empty in scene_data.data_empties:
        export_fbx_bin.fbx_data_empty_elements(objects, empty, scene_data)

    perfmon.step("FBX export fetch lamps (%d)..." % len(scene_data.data_lights))

    for lamp in scene_data.data_lights:
        export_fbx_bin.fbx_data_light_elements(objects, lamp, scene_data)

    perfmon.step("FBX export fetch cameras (%d)..." % len(scene_data.data_cameras))

    for cam in scene_data.data_cameras:
        export_fbx_bin.fbx_data_camera_elements(objects, cam, scene_data)

    perfmon.step("FBX export fetch meshes (%d)..."
                 % len({me_key for me_key, _me, _free in scene_data.data_meshes.values()}))

    done_meshes = set()
    for me_obj in scene_data.data_meshes:
        export_fbx_bin.fbx_data_mesh_elements(objects, me_obj, scene_data, done_meshes)
    del done_meshes

    perfmon.step("FBX export fetch objects (%d)..." % len(scene_data.objects))

    for ob_obj in scene_data.objects:
        if ob_obj.is_dupli:
            continue
        
        # PROTOWLF addition - Remove armature from export
        if proto_settings.skip_armature_object and ob_obj.type == "ARMATURE":
            continue
        
        export_fbx_bin.fbx_data_object_elements(objects, ob_obj, scene_data)
        for dp_obj in ob_obj.dupli_list_gen(scene_data.depsgraph):
            if dp_obj not in scene_data.objects:
                continue
            export_fbx_bin.fbx_data_object_elements(objects, dp_obj, scene_data)

    perfmon.step("FBX export fetch remaining...")

    for ob_obj in scene_data.objects:
        if not (ob_obj.is_object and ob_obj.type == 'ARMATURE'):
            continue
        export_fbx_bin.fbx_data_armature_elements(objects, ob_obj, scene_data)

    if scene_data.data_leaf_bones:
        export_fbx_bin.fbx_data_leaf_bone_elements(objects, scene_data)

    for ma in scene_data.data_materials:
        export_fbx_bin.fbx_data_material_elements(objects, ma, scene_data)

    for blender_tex_key in scene_data.data_textures:
        export_fbx_bin.fbx_data_texture_file_elements(objects, blender_tex_key, scene_data)

    for vid in scene_data.data_videos:
        export_fbx_bin.fbx_data_video_elements(objects, vid, scene_data)

    perfmon.step("FBX export fetch animations...")
    start_time = time.process_time()

    export_fbx_bin.fbx_data_animation_elements(objects, scene_data)

    perfmon.level_down()



# ##### "Main" functions. #####

# This func can be called with just the filepath
def save_single(operator, scene, depsgraph, filepath="",
                global_matrix=Matrix(),
                apply_unit_scale=False,
                global_scale=1.0,
                apply_scale_options='FBX_SCALE_NONE',
                axis_up="Z",
                axis_forward="Y",
                context_objects=None,
                object_types=None,
                use_mesh_modifiers=True,
                use_mesh_modifiers_render=True,
                mesh_smooth_type='FACE',
                use_subsurf=False,
                use_armature_deform_only=False,
                bake_anim=True,
                bake_anim_use_all_bones=True,
                bake_anim_use_nla_strips=False,
                bake_anim_use_all_actions=False,
                bake_anim_use_action_filter=False,
                bake_anim_action_filter=[],
                bake_anim_step=1.0,
                bake_anim_simplify_factor=1.0,
                bake_anim_force_startend_keying=True,
                skip_meshes_if_no_shapekey_animation=False,
                add_leaf_bones=False,
                primary_bone_axis='Y',
                secondary_bone_axis='X',
                use_metadata=True,
                path_mode='AUTO',
                use_mesh_edges=True,
                use_tspace=True,
                use_triangles=False,
                embed_textures=False,
                use_custom_props=False,
                bake_space_transform=False,
                armature_nodetype='NULL',
                colors_type='SRGB',
                prioritize_active_color=False,
                export_mesh_shapekey_animation = False,
                export_armature_shapekey_animation = False,
                export_zeroed_shapekeys = False,
                armature_shapekey_scale = 1.0,
                export_custom_property_animation = False,
                export_zeroed_custom_properties = False,
                export_non_deform_custom_properties = False,
                export_armature_object_custom_properties = False,
                export_armature_data_custom_properties = False,
                dont_simplify_root_bone = False,
                helper_armatures = {}, # dictionary with export object as key, helper armature as value. Armatures that should be animated but not exported
                skip_armature_object = False,
                **kwargs
                ):
    
    # Clear cached ObjectWrappers (just in case...).
    ObjectWrapper.cache_clear()
    
    if object_types is None:
        object_types = {'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'}
    
    if 'OTHER' in object_types:
        object_types |= BLENDER_OTHER_OBJECT_TYPES
    
    # Default Blender unit is equivalent to meter, while FBX one is centimeter...
    unit_scale = units_blender_to_fbx_factor(scene) if apply_unit_scale else 100.0
    if apply_scale_options == 'FBX_SCALE_NONE':
        global_matrix = Matrix.Scale(unit_scale * global_scale, 4) @ global_matrix
        unit_scale = 1.0
    elif apply_scale_options == 'FBX_SCALE_UNITS':
        global_matrix = Matrix.Scale(global_scale, 4) @ global_matrix
    elif apply_scale_options == 'FBX_SCALE_CUSTOM':
        global_matrix = Matrix.Scale(unit_scale, 4) @ global_matrix
        unit_scale = global_scale
    else:  # if apply_scale_options == 'FBX_SCALE_ALL':
        unit_scale = global_scale * unit_scale
    
    global_scale = global_matrix.median_scale
    global_matrix_inv = global_matrix.inverted()
    # For transforming mesh normals.
    global_matrix_inv_transposed = global_matrix_inv.transposed()

    # Only embed textures in COPY mode!
    if embed_textures and path_mode != 'COPY':
        embed_textures = False

    # Calculate bone correction matrix
    bone_correction_matrix = None  # Default is None = no change
    bone_correction_matrix_inv = None
    if (primary_bone_axis, secondary_bone_axis) != ('Y', 'X'):
        from bpy_extras.io_utils import axis_conversion
        bone_correction_matrix = axis_conversion(from_forward=secondary_bone_axis,
                                                 from_up=primary_bone_axis,
                                                 to_forward='X',
                                                 to_up='Y',
                                                 ).to_4x4()
        bone_correction_matrix_inv = bone_correction_matrix.inverted()

    media_settings = FBXExportSettingsMedia(
        path_mode,
        os.path.dirname(bpy.data.filepath),  # base_src
        os.path.dirname(filepath),  # base_dst
        # Local dir where to put images (media), using FBX conventions.
        os.path.splitext(os.path.basename(filepath))[0] + ".fbm",  # subdir
        embed_textures,
        set(),  # copy_set
        set(),  # embedded_set
    )
    
    settings = FBXExportSettings(
        operator.report, (axis_up, axis_forward), global_matrix, global_scale, apply_unit_scale, unit_scale,
        bake_space_transform, global_matrix_inv, global_matrix_inv_transposed,
        context_objects, object_types, use_mesh_modifiers, use_mesh_modifiers_render,
        mesh_smooth_type, use_subsurf, use_mesh_edges, use_tspace, use_triangles,
        armature_nodetype, use_armature_deform_only,
        add_leaf_bones, bone_correction_matrix, bone_correction_matrix_inv,
        bake_anim, bake_anim_use_all_bones, bake_anim_use_nla_strips, bake_anim_use_all_actions,
        bake_anim_step, bake_anim_simplify_factor, bake_anim_force_startend_keying,
        False, media_settings, use_custom_props, colors_type, prioritize_active_color
    )
    
    proto_settings = ProtoFBXExportSettings( export_mesh_shapekey_animation, export_armature_shapekey_animation,
        export_zeroed_shapekeys, armature_shapekey_scale,
        export_custom_property_animation, export_zeroed_custom_properties,
        export_non_deform_custom_properties, export_armature_object_custom_properties,
        export_armature_data_custom_properties, dont_simplify_root_bone,
        bake_anim_use_action_filter, bake_anim_action_filter,
        skip_meshes_if_no_shapekey_animation, helper_armatures,
        skip_armature_object
    )
    
    proto_data = ProtoFBXExportData()
    
    import bpy_extras.io_utils
    
    print('\nFBX export starting... %r' % filepath)
    start_time = time.time()
    
    # Generate some data about exported scene...
    scene_data = fbx_data_from_scene(scene, depsgraph, settings, proto_settings, proto_data)
    
    # Enable multithreaded array compression in FBXElem and wait until all threads are done before exiting the context
    # manager.
    with encode_bin.FBXElem.enable_multithreading_cm():
        # Writing elements into an FBX hierarchy can now begin.
        root = elem_empty(None, b"")  # Root element has no id, as it is not saved per se!

        # Mostly FBXHeaderExtension and GlobalSettings.
        export_fbx_bin.fbx_header_elements(root, scene_data)

        # Documents and References are pretty much void currently.
        export_fbx_bin.fbx_documents_elements(root, scene_data)
        export_fbx_bin.fbx_references_elements(root, scene_data)

        # Templates definitions.
        export_fbx_bin.fbx_definitions_elements(root, scene_data)

        # Actual data.
        #export_fbx_bin.fbx_objects_elements(root, scene_data)
        fbx_objects_elements(root, scene_data, proto_settings)
        
        # How data are inter-connected.
        export_fbx_bin.fbx_connections_elements(root, scene_data)

        # Animation.
        export_fbx_bin.fbx_takes_elements(root, scene_data)

        # Cleanup!
        export_fbx_bin.fbx_scene_data_cleanup(scene_data)

    # And we are done, all multithreaded tasks are complete, and we can write the whole thing to file!
    encode_bin.write(filepath, root, FBX_VERSION)

    # Clear cached ObjectWrappers!
    ObjectWrapper.cache_clear()

    # copy all collected files, if we did not embed them.
    if not media_settings.embed_textures:
        bpy_extras.io_utils.path_reference_copy(media_settings.copy_set)

    print('export finished in %.4f sec.' % (time.time() - start_time))
    return {'FINISHED'}


def save(operator, context,
         filepath="",
         use_selection=False,
         use_visible=False,
         use_active_collection=False,
         collection="",
         batch_mode='OFF',
         use_batch_own_dir=False,
         **kwargs
         ):
    """
    This is a wrapper around save_single, which handles multi-scenes (or collections) cases, when batch-exporting
    a whole .blend file.
    """
    
    ret = {'FINISHED'}

    active_object = context.view_layer.objects.active

    org_mode = None
    if active_object and active_object.mode != 'OBJECT' and bpy.ops.object.mode_set.poll():
        org_mode = active_object.mode
        bpy.ops.object.mode_set(mode='OBJECT')

    if batch_mode == 'OFF':
        kwargs_mod = kwargs.copy()

        source_collection = None
        if use_active_collection:
            source_collection = context.view_layer.active_layer_collection.collection
        elif collection:
            local_collection = bpy.data.collections.get((collection, None))
            if local_collection:
                source_collection = local_collection
            else:
                operator.report({'ERROR'}, "Collection '%s' was not found" % collection)
                return {'CANCELLED'}

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

        # Sort exported objects by their names.
        ctx_objects = sorted(ctx_objects, key=lambda ob: ob.name)

        # Ensure no Objects are in Edit mode.
        # Copy to a tuple for safety, to avoid the risk of modifying ctx_objects while iterating.
        for obj in ctx_objects:
            if not ensure_object_not_in_edit_mode(context, obj):
                operator.report({'ERROR'}, "%s could not be set out of Edit Mode, so cannot be exported" % obj.name)
                return {'CANCELLED'}

        kwargs_mod["context_objects"] = ctx_objects
        depsgraph = context.evaluated_depsgraph_get()
        
        ret = save_single(operator, context.scene, depsgraph, filepath, **kwargs_mod)
    else:
        # XXX We need a way to generate a depsgraph for inactive view_layers first...
        # XXX Also, what to do in case of batch-exporting scenes, when there is more than one view layer?
        #     Scenes have no concept of 'active' view layer, that's on window level...
        fbxpath = filepath

        prefix = os.path.basename(fbxpath)
        if prefix:
            fbxpath = os.path.dirname(fbxpath)

        if batch_mode == 'COLLECTION':
            data_seq = tuple((coll, coll.name, 'objects') for coll in bpy.data.collections if coll.objects)
        elif batch_mode in {'SCENE_COLLECTION', 'ACTIVE_SCENE_COLLECTION'}:
            scenes = [context.scene] if batch_mode == 'ACTIVE_SCENE_COLLECTION' else bpy.data.scenes
            data_seq = []
            for scene in scenes:
                if not scene.objects:
                    continue
                # Needed to avoid having tens of 'Scene Collection' entries.
                todo_collections = [(scene.collection, "_".join((scene.name, scene.collection.name)))]
                while todo_collections:
                    coll, coll_name = todo_collections.pop()
                    todo_collections.extend(((c, c.name) for c in coll.children if c.all_objects))
                    data_seq.append((coll, coll_name, 'all_objects'))
        else:
            data_seq = tuple((scene, scene.name, 'objects') for scene in bpy.data.scenes if scene.objects)

        # Ensure no Objects are in Edit mode.
        for data, data_name, data_obj_propname in data_seq:
            # Copy to a tuple for safety, to avoid the risk of modifying the data prop while iterating it.
            for obj in tuple(getattr(data, data_obj_propname)):
                if not ensure_object_not_in_edit_mode(context, obj):
                    operator.report({'ERROR'},
                                    "%s in %s could not be set out of Edit Mode, so cannot be exported"
                                    % (obj.name, data_name))
                    return {'CANCELLED'}

        # call this function within a loop with BATCH_ENABLE == False

        new_fbxpath = fbxpath  # own dir option modifies, we need to keep an original
        for data, data_name, data_obj_propname in data_seq:  # scene or collection
            newname = "_".join((prefix, bpy.path.clean_name(data_name))) if prefix else bpy.path.clean_name(data_name)

            if use_batch_own_dir:
                new_fbxpath = os.path.join(fbxpath, newname)
                # path may already exist... and be a file.
                while os.path.isfile(new_fbxpath):
                    new_fbxpath = "_".join((new_fbxpath, "dir"))
                if not os.path.exists(new_fbxpath):
                    os.makedirs(new_fbxpath)

            filepath = os.path.join(new_fbxpath, newname + '.fbx')

            print('\nBatch exporting %s as...\n\t%r' % (data, filepath))

            if batch_mode in {'COLLECTION', 'SCENE_COLLECTION', 'ACTIVE_SCENE_COLLECTION'}:
                # Collection, so that objects update properly, add a dummy scene.
                scene = bpy.data.scenes.new(name="FBX_Temp")
                src_scenes = {}  # Count how much each 'source' scenes are used.
                for obj in getattr(data, data_obj_propname):
                    for src_sce in obj.users_scene:
                        src_scenes[src_sce] = src_scenes.setdefault(src_sce, 0) + 1
                    scene.collection.objects.link(obj)

                # Find the 'most used' source scene, and use its unit settings. This is somewhat weak, but should work
                # fine in most cases, and avoids stupid issues like T41931.
                best_src_scene = None
                best_src_scene_users = -1
                for sce, nbr_users in src_scenes.items():
                    if (nbr_users) > best_src_scene_users:
                        best_src_scene_users = nbr_users
                        best_src_scene = sce
                scene.unit_settings.system = best_src_scene.unit_settings.system
                scene.unit_settings.system_rotation = best_src_scene.unit_settings.system_rotation
                scene.unit_settings.scale_length = best_src_scene.unit_settings.scale_length

                # new scene [only one viewlayer to update]
                scene.view_layers[0].update()
                # TODO - BUMMER! Armatures not in the group wont animate the mesh
            else:
                scene = data

            kwargs_batch = kwargs.copy()
            kwargs_batch["context_objects"] = getattr(data, data_obj_propname)

            save_single(operator, scene, scene.view_layers[0].depsgraph, filepath, **kwargs_batch)

            if batch_mode in {'COLLECTION', 'SCENE_COLLECTION', 'ACTIVE_SCENE_COLLECTION'}:
                # Remove temp collection scene.
                bpy.data.scenes.remove(scene)

    if active_object and org_mode:
        context.view_layer.objects.active = active_object
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode=org_mode)

    return ret
