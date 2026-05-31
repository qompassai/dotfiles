# PROTO Tools Operators
# 2026 PROTOWLF, Licensed under GPL-3.0


# import, reload if already imported
if "proto_fbx_utils" not in locals():
    from .fbx_export import proto_fbx_utils
else:
    import importlib
    proto_fbx_utils = importlib.reload(proto_fbx_utils)
from .fbx_export.proto_fbx_utils import (
    get_actions_for_armature,
    action_has_slot_with_name,
    get_action_filepath,
    refresh_action_filter
)

if "protogat_utils" not in locals():
    from . import protogat_utils
else:
    import importlib
    protogat_utils = importlib.reload(protogat_utils)
from .protogat_utils import (
    get_current_quick_export_properties,
    get_current_multi_selected_batch_export_items,
    get_current_selected_batch_export_item,
    get_batch_export_properties_by_index
)

from .fbx_export.proto_fbx_init import ProtoExportFBX_ExportListEntry

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    EnumProperty,
    CollectionProperty,
    PointerProperty
)
import os
import math
import time
import textwrap


addon_package_name = __package__
addon_package_name = addon_package_name.removesuffix(".src")


def get_final_scene_conversion_options(context, export_properties):
    scene_rotation_mode = "None"
    
    if export_properties.scene_conversion_mode == "Unreal":
        bake_scale_mode = "Centimeters"
        bake_scale_custom = 1.0 # ignored outside bake_scale_mode "Custom"
        scene_rotation_mode = "None"
        armature_name = "Armature"
        skip_armature_object = False
    elif export_properties.scene_conversion_mode == "UnityGodot":
        bake_scale_mode = "Centimeters"
        bake_scale_custom = 1.0 # ignored outside bake_scale_mode "Custom"
        scene_rotation_mode = "BakeZForward"
        armature_name = ""
        skip_armature_object = True
    elif export_properties.scene_conversion_mode == "Custom":
        bake_scale_mode = export_properties.bake_scale_mode
        bake_scale_custom = export_properties.bake_scale_custom
        scene_rotation_mode = export_properties.scene_rotation_mode
        armature_name = export_properties.armature_name
        skip_armature_object = export_properties.skip_armature_object
    
    if scene_rotation_mode == 'BakeZForward':
        bake_z_forward = True
        use_space_transform = False
    else:
        bake_z_forward = False
        use_space_transform = True
    
    return bake_scale_mode, bake_scale_custom, armature_name, skip_armature_object, bake_z_forward, use_space_transform


def get_final_action_filter(context, export_properties):
    action_whitelist = []
    
    # Could call refresh_action_filter(), but let's keep exports as lightweight as possible
    
    if export_properties.use_action_filter:
        for entry in export_properties.action_filter:
            if entry.action is not None and entry.keep:
                dict = {}
                dict["name"] = entry.action.name
                dict["action_name"] = entry.action.name
                action_whitelist.append(dict)
    
    return action_whitelist


def get_export_properties_for_operator(context, batch_export_item_index):
    if batch_export_item_index == -1:
        return context.scene.proto_quickexport.export_selected_properties
    return get_batch_export_properties_by_index(context, batch_export_item_index)


class ProtoTools_QuickExportSetOptionsPreset(bpy.types.Operator):
    """Set Export Options to preset settings"""
    bl_idname = "prototools.quick_export_set_options_preset"
    bl_label = "Options Presets"
    
    preset: EnumProperty(
        name="Options Preset",
        items=(('Unreal', "Unreal", ""),
               ('Unity', "Unity", ""),
               ('Godot', "Godot", ""),
               ),
    )
    
    def execute(self, context):
        export_properties = get_current_quick_export_properties(context)
        if self.preset == 'Unreal':
            export_properties.scene_conversion_mode = "Unreal"
            #export_properties.bake_scale_mode = 'Centimeters'
            #export_properties.bake_scale_custom = 1.0
            #export_properties.scene_rotation_mode = 'None'
            #export_properties.armature_name = 'Armature'
            #export_properties.skip_armature_object = False
            export_properties.apply_modifiers = False
            #export_properties.action_name_style = Action
            #export_properties.action_name_sharedname = ""
            export_properties.animation_force_dummy_mesh = False
            export_properties.min_two_frames = True
            export_properties.remove_scale_from_bones = False
            export_properties.remove_bone_rotation = False
            export_properties.flat_bone_hierarchy = False
            export_properties.flat_bone_hierarchy_root = ""
            export_properties.bake_anim_simplify_factor = 0.1
            export_properties.dont_simplify_root_bone = True
            export_properties.export_shapekey_animation = True
            export_properties.shapekey_export_mode = 'ArmatureCustomProps'
            export_properties.armature_shapekey_scale = 1.0
            #export_properties.export_zeroed_shapekeys = False
            #export_properties.export_custom_property_animation = False
            #export_properties.export_zeroed_custom_properties = False
            #export_properties.export_non_deform_custom_properties = False
            #export_properties.export_armature_object_custom_properties = False
            #export_properties.export_armature_data_custom_properties = False
        elif self.preset == 'Unity':
            export_properties.scene_conversion_mode = "UnityGodot"
            #export_properties.bake_scale_mode = 'Centimeters'
            #export_properties.bake_scale_custom = 1.0
            #export_properties.scene_rotation_mode = 'BakeZForward'
            #export_properties.armature_name = ''
            #export_properties.skip_armature_object = True
            export_properties.apply_modifiers = False
            #export_properties.action_name_style = Action
            #export_properties.action_name_sharedname = ""
            export_properties.animation_force_dummy_mesh = True
            export_properties.min_two_frames = True
            export_properties.remove_scale_from_bones = False
            export_properties.remove_bone_rotation = False
            export_properties.flat_bone_hierarchy = False
            export_properties.flat_bone_hierarchy_root = ""
            export_properties.bake_anim_simplify_factor = 0.1
            export_properties.dont_simplify_root_bone = True
            export_properties.export_shapekey_animation = True
            export_properties.shapekey_export_mode = 'ArmatureDummyMesh'
            export_properties.armature_shapekey_scale = 1.0
            #export_properties.export_zeroed_shapekeys = False
            #export_properties.export_custom_property_animation = False
            #export_properties.export_zeroed_custom_properties = False
            #export_properties.export_non_deform_custom_properties = False
            #export_properties.export_armature_object_custom_properties = False
            #export_properties.export_armature_data_custom_properties = False
        elif self.preset == 'Godot':
            export_properties.scene_conversion_mode = "UnityGodot"
            #export_properties.bake_scale_mode = 'Centimeters'
            #export_properties.scene_rotation_mode = 'BakeZForward'
            #export_properties.bake_scale_custom = 1.0
            #export_properties.armature_name = ''
            #export_properties.skip_armature_object = True
            export_properties.apply_modifiers = False
            #export_properties.action_name_style = Action
            #export_properties.action_name_sharedname = ""
            export_properties.animation_force_dummy_mesh = False
            export_properties.min_two_frames = True
            export_properties.remove_scale_from_bones = False
            export_properties.remove_bone_rotation = False
            export_properties.flat_bone_hierarchy = False
            export_properties.flat_bone_hierarchy_root = ""
            export_properties.bake_anim_simplify_factor = 0.1
            export_properties.dont_simplify_root_bone = True
            export_properties.export_shapekey_animation = True
            export_properties.shapekey_export_mode = 'ArmatureDummyMesh'
            export_properties.armature_shapekey_scale = 1.0
            #export_properties.export_zeroed_shapekeys = False
            #export_properties.export_custom_property_animation = False
            #export_properties.export_zeroed_custom_properties = False
            #export_properties.export_non_deform_custom_properties = False
            #export_properties.export_armature_object_custom_properties = False
            #export_properties.export_armature_data_custom_properties = False
        
        # Property window won't update immediately because of the invoke popup. Force an update
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event=event, title="Set all options to preset '" + self.preset + "'?")


class ProtoTools_QuickExportMeshAndAnimations(bpy.types.Operator):
    """Export selected meshes (and up to 1 Armature) as an FBX mesh, with all of its animations (if any)\n\nMust include an Armature in order for this mesh to be animated"""
    bl_idname = "prototools.quick_export_mesh_and_animations"
    bl_label = "Quick Export Mesh and Animations"
    
    # Proto Addition
    export_name: StringProperty(
        name="Export Name",
        description="Name to identify this export, displayed in warnings. Internal, not set by users",
        options={'HIDDEN'},
        default="",
    )
    
    batch_export_item_index: IntProperty(default=-1)
    
    # (optional) list of object names to export, overrides other methods of object selection
    # may contain a name to be renamed-to
    export_object_list: CollectionProperty(
        type=ProtoExportFBX_ExportListEntry,
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        export_properties = get_export_properties_for_operator(context, self.batch_export_item_index)
        
        # Validate filepath (with file name)
        if export_properties.model_path == "" or export_properties.model_path == "/":
            self.report({'ERROR'}, "Invalid File Path - Set a path above.")
            return {'CANCELLED'}
        if export_properties.model_path[-1] == '/' or export_properties.model_path[-1] == '\\':
            self.report({'ERROR'}, "Invalid File Path - Must specify a file name.")
            return {'CANCELLED'}
        
        # Get final export objects (either selection, or optional overriden export list from batch export)
        # Convert self.export_object_list to final_export_object_list
        final_export_objects = context.selected_objects
        final_export_object_list = []
        if len(self.export_object_list) > 0:
            # use export list instead of current selection
            final_export_objects.clear()
            for entry in self.export_object_list:
                final_export_objects.append(bpy.data.objects[entry.name])
                # Can't pass CollectionProperty through operator, must convert to a plain list(dict())
                final_entry = dict()
                final_entry["name"] = entry.name
                final_entry["rename_name"] = entry.rename_name
                final_export_object_list.append(final_entry)
        
        # Must have objects selected
        if final_export_objects == None or len(final_export_objects) == 0:
            self.report({'ERROR'}, "Invalid Selection - No Objects selected.")
            return {'CANCELLED'}
        
        # Must have at least 1 mesh selected, maximum 1 armature
        found_mesh = False
        num_armatures = 0
        armature = None
        for ob in final_export_objects:
            if ob.type == "MESH":
                found_mesh = True
            elif ob.type == "ARMATURE":
                num_armatures += 1
                armature = ob
        if found_mesh == False:
            self.report({'ERROR'}, "Invalid Selection - No Meshes selected.")
            return {'CANCELLED'}
        if num_armatures > 1:
            self.report({'ERROR'}, "Invalid Selection - Multiple Armatures selected, maximum 1 Armature allowed.")
            return {'CANCELLED'}
        
        # Make sure armature has bones (if we're exporting one)
        if armature != None and (armature.pose == None or len(armature.pose.bones) == 0):
            self.report({'ERROR'}, "Invalid Armature - Must have at least 1 bone.")
            return {'CANCELLED'}
        
        self.original_mode = context.mode
        result = set()
        try:
            # Switch to Object Mode
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except:
                pass
            
            bake_scale_mode, bake_scale_custom, armature_name, skip_armature_object, bake_z_forward, use_space_transform = get_final_scene_conversion_options(context, export_properties)
            action_whitelist = get_final_action_filter(context, export_properties)
            
            result = bpy.ops.proto_export_scene.fbx(
                filepath = export_properties.model_path,
                export_name = self.export_name,
                # Include
                use_selection = True,
                use_visible = True,
                use_active_collection = False,
                collection = "",
                object_types = {'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'},
                use_custom_props = True,
                export_object_list = final_export_object_list,
                # Conversion
                bake_scale_mode = bake_scale_mode,
                bake_scale_custom = bake_scale_custom,
                armature_name = armature_name,
                skip_armature_object = skip_armature_object,
                bake_z_forward = bake_z_forward,
                use_space_transform = use_space_transform,
                move_to_origin = export_properties.move_to_origin,
                # Geometry
                use_mesh_modifiers = export_properties.apply_modifiers,
                # Bake Animations
                bake_anim = True,
                animation_export_mode = 'MultipleActions',
                one_file_per_action = False,
                action_whitelist = action_whitelist,
                # Proto Options
                min_two_frames = export_properties.min_two_frames,
                remove_scale_from_bones = export_properties.remove_scale_from_bones,
                remove_bone_rotation = export_properties.remove_bone_rotation,
                flat_bone_hierarchy = export_properties.flat_bone_hierarchy,
                flat_bone_hierarchy_root = export_properties.flat_bone_hierarchy_root,
                bake_anim_simplify_factor = export_properties.bake_anim_simplify_factor,
                export_shapekey_animation = export_properties.export_shapekey_animation,
                shapekey_export_mode = 'Mesh', # when exporting mesh + anims together, always makes sense to export shapekeys using the mesh
                export_zeroed_shapekeys = export_properties.export_zeroed_shapekeys,
                armature_shapekey_scale = export_properties.armature_shapekey_scale,
                export_custom_property_animation = export_properties.export_custom_property_animation,
                export_zeroed_custom_properties = export_properties.export_zeroed_custom_properties,
                export_non_deform_custom_properties = export_properties.export_non_deform_custom_properties,
                export_armature_object_custom_properties = export_properties.export_armature_object_custom_properties,
                export_armature_data_custom_properties = export_properties.export_armature_data_custom_properties,
                dont_simplify_root_bone = export_properties.dont_simplify_root_bone,
                #action_name_style = export_properties.action_name_style, # ignored when not one_file_per_action
                #action_name_sharedname = export_properties.action_name_sharedname, # ignored when not one_file_per_action
                animation_force_dummy_mesh = export_properties.animation_force_dummy_mesh
            )
        finally:
            # Restore previous mode
            try:
                bpy.ops.object.mode_set(mode=self.original_mode)
            except:
                pass
        
        if 'FINISHED' in result:
            self.report({'INFO'}, "Model exported successfully")
        return {'FINISHED'}


class ProtoTools_QuickExportMesh(bpy.types.Operator):
    """Export selected meshes (and up to 1 Armature) as an FBX mesh.\n\nMust include an Armature in order for this mesh to be animated"""
    bl_idname = "prototools.quick_export_mesh"
    bl_label = "Quick Export Mesh"
    
    # Proto Addition
    export_name: StringProperty(
        name="Export Name",
        description="Name to identify this export, displayed in warnings. Internal, not set by users",
        options={'HIDDEN'},
        default="",
    )
    
    batch_export_item_index: IntProperty(default=-1)
    
    # (optional) list of object names to export, overrides other methods of object selection
    # may contain a name to be renamed-to
    export_object_list: CollectionProperty(
        type=ProtoExportFBX_ExportListEntry,
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        export_properties = get_export_properties_for_operator(context, self.batch_export_item_index)
        
        # Validate filepath (with file name)
        if export_properties.model_path == "" or export_properties.model_path == "/":
            self.report({'ERROR'}, "Invalid File Path - Set a path above.")
            return {'CANCELLED'}
        if export_properties.model_path[-1] == '/' or export_properties.model_path[-1] == '\\':
            self.report({'ERROR'}, "Invalid File Path - Must specify a file name.")
            return {'CANCELLED'}
        
        # Get final export objects (either selection, or optional overriden export list from batch export)
        # Convert self.export_object_list to final_export_object_list
        final_export_objects = context.selected_objects
        final_export_object_list = []
        if len(self.export_object_list) > 0:
            # use export list instead of current selection
            final_export_objects.clear()
            for entry in self.export_object_list:
                final_export_objects.append(bpy.data.objects[entry.name])
                # Can't pass CollectionProperty through operator, must convert to a plain list(dict())
                final_entry = dict()
                final_entry["name"] = entry.name
                final_entry["rename_name"] = entry.rename_name
                final_export_object_list.append(final_entry)
            
        # Must have objects selected
        if final_export_objects == None or len(final_export_objects) == 0:
            self.report({'ERROR'}, "Invalid Selection - No Objects selected.")
            return {'CANCELLED'}
        
        # Must have at least 1 mesh selected, maximum 1 armature
        found_mesh = False
        num_armatures = 0
        armature = None
        for ob in final_export_objects:
            if ob.type == "MESH":
                found_mesh = True
            elif ob.type == "ARMATURE":
                num_armatures += 1
                armature = ob
        if found_mesh == False:
            self.report({'ERROR'}, "Invalid Selection - No Meshes selected.")
            return {'CANCELLED'}
        if num_armatures > 1:
            self.report({'ERROR'}, "Invalid Selection - Multiple Armatures selected, maximum 1 Armature allowed.")
            return {'CANCELLED'}
        
        # Make sure armature has bones (if we're exporting one)
        if armature != None and (armature.pose == None or len(armature.pose.bones) == 0):
            self.report({'ERROR'}, "Invalid Armature - Must have at least 1 bone.")
            return {'CANCELLED'}
        
        self.original_mode = context.mode
        self.original_pose_position = None
        if armature != None:
            self.original_pose_position = armature.data.pose_position
        
        result = set()
        try:
            # Switch to Object Mode
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except:
                pass
            
            # Switch armature to rest pose
            if armature != None:
                armature.data.pose_position = "REST"
            
            bake_scale_mode, bake_scale_custom, armature_name, skip_armature_object, bake_z_forward, use_space_transform = get_final_scene_conversion_options(context, export_properties)
            
            result = bpy.ops.proto_export_scene.fbx(
                filepath = export_properties.model_path,
                export_name = self.export_name,
                # Include
                use_selection = True,
                use_visible = True,
                use_active_collection = False,
                collection = "",
                object_types = {'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'},
                use_custom_props = True,
                export_object_list = final_export_object_list,
                # Conversion
                bake_scale_mode = bake_scale_mode,
                bake_scale_custom = bake_scale_custom,
                armature_name = armature_name,
                skip_armature_object = skip_armature_object,
                bake_z_forward = bake_z_forward,
                use_space_transform = use_space_transform,
                move_to_origin = export_properties.move_to_origin,
                # Geometry
                use_mesh_modifiers = export_properties.apply_modifiers,
                # Bake Animations
                bake_anim = False,
                # Proto Options
                min_two_frames = False,
                remove_scale_from_bones = export_properties.remove_scale_from_bones,
                remove_bone_rotation = export_properties.remove_bone_rotation,
                flat_bone_hierarchy = export_properties.flat_bone_hierarchy,
                flat_bone_hierarchy_root = export_properties.flat_bone_hierarchy_root,
                bake_anim_simplify_factor = export_properties.bake_anim_simplify_factor,
                export_shapekey_animation = export_properties.export_shapekey_animation,
                shapekey_export_mode = export_properties.shapekey_export_mode,
                export_zeroed_shapekeys = export_properties.export_zeroed_shapekeys,
                armature_shapekey_scale = export_properties.armature_shapekey_scale,
                export_custom_property_animation = export_properties.export_custom_property_animation,
                export_zeroed_custom_properties = export_properties.export_zeroed_custom_properties,
                export_non_deform_custom_properties = export_properties.export_non_deform_custom_properties,
                export_armature_object_custom_properties = export_properties.export_armature_object_custom_properties,
                export_armature_data_custom_properties = export_properties.export_armature_data_custom_properties,
                dont_simplify_root_bone = export_properties.dont_simplify_root_bone
            )
        finally:
            # Restore previous mode
            try:
                bpy.ops.object.mode_set(mode=self.original_mode)
            except:
                pass
            
            # Restore previous armature pose position
            if armature != None:
                armature.data.pose_position = self.original_pose_position
        
        if 'FINISHED' in result:
            self.report({'INFO'}, "Model exported successfully")
        return {'FINISHED'}


class ProtoTools_QuickExportCurAction(bpy.types.Operator):
    """Export current Action on selected Armature as an FBX animation.\nDo not select the bound Mesh, unless the Mesh has Shape Key animation\nNOTE: will export the Action's frame range, not the current Timeline"""
    bl_idname = "prototools.quick_export_curaction"
    bl_label = "Quick Export Current Action"
    
    # Proto Addition
    export_name: StringProperty(
        name="Export Name",
        description="Name to identify this export, displayed in warnings. Internal, not set by users",
        options={'HIDDEN'},
        default="",
    )
    
    batch_export_item_index: IntProperty(default=-1)
    
    # (optional) list of object names to export, overrides other methods of object selection
    # may contain a name to be renamed-to
    export_object_list: CollectionProperty(
        type=ProtoExportFBX_ExportListEntry,
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        settings = bpy.context.preferences.addons[addon_package_name].preferences
        export_properties = get_export_properties_for_operator(context, self.batch_export_item_index)
        
        # Validate filepath
        if export_properties.anim_folder_path == "" or export_properties.anim_folder_path == "/":
            self.report({'ERROR'}, "Invalid File Path - Set a path above.")
            return {'CANCELLED'}
        
        # Should be a path to a folder
        if export_properties.anim_folder_path[-1] != '/' and export_properties.anim_folder_path[-1] != '\\':
            self.report({'ERROR'}, "Invalid File Path - Must specify a folder name.")
            return {'CANCELLED'}
        
        # Get final export objects (either selection, or optional overriden export list from batch export)
        # Convert self.export_object_list to final_export_object_list
        final_export_objects = context.selected_objects
        final_export_object_list = []
        if len(self.export_object_list) > 0:
            # use export list instead of current selection
            final_export_objects.clear()
            for entry in self.export_object_list:
                final_export_objects.append(bpy.data.objects[entry.name])
                # Can't pass CollectionProperty through operator, must convert to a plain list(dict())
                final_entry = dict()
                final_entry["name"] = entry.name
                final_entry["rename_name"] = entry.rename_name
                final_export_object_list.append(final_entry)
        
        # Must have objects selected
        if final_export_objects == None or len(final_export_objects) == 0:
            self.report({'ERROR'}, "Invalid Selection - No Objects selected.")
            return {'CANCELLED'}
        
        # Cannot select multiple objects
        if len(final_export_objects) > 1:
            self.report({'ERROR'}, "Invalid Selection - Must only select 1 Armature.")
            return {'CANCELLED'}
        
        # Must have exactly 1 armature selected
        armature = None
        for ob in final_export_objects:
            if ob.type == 'ARMATURE':
                if armature != None:
                    self.report({'ERROR'}, "Multiple Armatures selected - Must select exactly 1 Armature.")
                    return {'CANCELLED'}
                armature = ob
        if armature == None:
            self.report({'ERROR'}, "No Armature selected - Must select exactly 1 Armature.")
            return {'CANCELLED'}
        
        # Make sure armature has bones
        if armature.pose == None or len(armature.pose.bones) == 0:
            self.report({'ERROR'}, "Invalid Armature - Must have at least 1 bone.")
            return {'CANCELLED'}
        
        # Must have an active action
        if armature.animation_data == None or armature.animation_data.action == None:
            self.report({'ERROR'}, "Invalid Action - No active Action on selected Armature.")
            return {'CANCELLED'}
        action = armature.animation_data.action
        
        # Action (may) need armature name slot
        if bpy.app.version >= (4, 4, 0):
            if settings.action_slot_behavior == 'ARMATURE_NAME':
                current_slot = context.active_object.animation_data.action_slot
                if current_slot == None:
                    self.report({'ERROR'}, "Invalid Action Slot - No active Slot on selected Armature.\nCheck the Quick Action Select panel.")
                    return {'CANCELLED'}
                elif current_slot.name_display != context.active_object.name:
                    self.report({'ERROR'}, "Invalid Action Slot - active Slot on selected Armature does not match Armature name.\nCheck the Quick Action Select panel.")
                    return {'CANCELLED'}
            else:
                current_slot = context.active_object.animation_data.action_slot
                if current_slot == None:
                    self.report({'ERROR'}, "Invalid Action Slot - No active Slot on selected Armature.")
                    return {'CANCELLED'}
        
        # Make sure flat bone hierarchy specifies a valid bone
        if export_properties.flat_bone_hierarchy and export_properties.flat_bone_hierarchy_root != "":
            if not export_properties.flat_bone_hierarchy_root in armature.data.bones:
                self.report({'ERROR'}, "Flat Bone Hierarchy mode - specified root bone '" + export_properties.flat_bone_hierarchy_root + "' not found in the armature.")
                return {'CANCELLED'}
        
        # Cache selection at start of export
        self.original_selected_objects = bpy.context.selected_objects
        self.original_active_selection = bpy.context.view_layer.objects.active
        
        action_name = armature.animation_data.action.name
        final_file_path = get_action_filepath(context, export_properties.anim_folder_path, action_name, export_properties.action_name_style, export_properties.action_name_sharedname)
        
        self.original_frame_start = bpy.context.scene.frame_start
        self.original_frame_end = bpy.context.scene.frame_end
        self.original_mode = context.mode
        result = set()
        
        try:
            # Switch to Object Mode
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except:
                pass
            
            # Set timeline to the action's frame range
            frame_start, frame_end = armature.animation_data.action.frame_range
            bpy.context.scene.frame_start = math.floor(frame_start)
            bpy.context.scene.frame_end = math.floor(frame_end)
            
            # if using min_two_frames, adjust timeline if necessary
            if bpy.context.scene.frame_start == bpy.context.scene.frame_end and export_properties.min_two_frames == True:
                bpy.context.scene.frame_end += 1
            
            bake_scale_mode, bake_scale_custom, armature_name, skip_armature_object, bake_z_forward, use_space_transform = get_final_scene_conversion_options(context, export_properties)
            
            # Do the export
            result = bpy.ops.proto_export_scene.fbx(
                filepath = final_file_path,
                export_name = self.export_name,
                # Include
                use_selection = True,
                use_visible = True,
                use_active_collection = False,
                collection = "",
                object_types = {'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'},
                use_custom_props = True, # Export curve data (e.g. shapekey animation)
                export_object_list = final_export_object_list,
                # Conversion
                bake_scale_mode = bake_scale_mode,
                bake_scale_custom = bake_scale_custom,
                armature_name = armature_name,
                skip_armature_object = skip_armature_object,
                bake_z_forward = bake_z_forward,
                use_space_transform = use_space_transform,
                move_to_origin = export_properties.move_to_origin,
                # Geometry
                use_mesh_modifiers = export_properties.apply_modifiers,
                # Bake Animations
                bake_anim = True,
                animation_export_mode = 'CurrentAction',
                one_file_per_action = False,
                # Proto Options
                min_two_frames = False, # Already handled it, so don't let PROTO exporter do this!
                remove_scale_from_bones = export_properties.remove_scale_from_bones,
                remove_bone_rotation = export_properties.remove_bone_rotation,
                flat_bone_hierarchy = export_properties.flat_bone_hierarchy,
                flat_bone_hierarchy_root = export_properties.flat_bone_hierarchy_root,
                bake_anim_simplify_factor = export_properties.bake_anim_simplify_factor,
                export_shapekey_animation = export_properties.export_shapekey_animation,
                shapekey_export_mode = export_properties.shapekey_export_mode,
                export_zeroed_shapekeys = export_properties.export_zeroed_shapekeys,
                armature_shapekey_scale = export_properties.armature_shapekey_scale,
                export_custom_property_animation = export_properties.export_custom_property_animation,
                export_zeroed_custom_properties = export_properties.export_zeroed_custom_properties,
                export_non_deform_custom_properties = export_properties.export_non_deform_custom_properties,
                export_armature_object_custom_properties = export_properties.export_armature_object_custom_properties,
                export_armature_data_custom_properties = export_properties.export_armature_data_custom_properties,
                dont_simplify_root_bone = export_properties.dont_simplify_root_bone,
                #action_name_style = export_properties.action_name_style, # ignored when not one_file_per_action
                #action_name_sharedname = export_properties.action_name_sharedname, # ignored when not one_file_per_action
                animation_force_dummy_mesh = export_properties.animation_force_dummy_mesh
            )
            
        finally:
            # Reset the original timeline frame range
            bpy.context.scene.frame_start = self.original_frame_start
            bpy.context.scene.frame_end = self.original_frame_end
            
            # Re-select objects from the start of the export
            bpy.ops.object.select_all(action='DESELECT')
            for ob in self.original_selected_objects:
                ob.select_set(state=True)
            bpy.context.view_layer.objects.active = self.original_active_selection
            
            # Restore previous mode
            try:
                bpy.ops.object.mode_set(mode=self.original_mode)
            except:
                pass
        
        if 'FINISHED' in result:
            self.report({'INFO'}, "Animation exported successfully")
        return {'FINISHED'}


def cache_pose(armature):
    saved_pose = {}
    for pose_bone in armature.pose.bones:
        saved_pose[pose_bone.name] = pose_bone.location.copy(), pose_bone.scale.copy(), pose_bone.rotation_mode, pose_bone.rotation_quaternion.copy(), pose_bone.rotation_euler.copy()
    return saved_pose


def restore_pose(armature, saved_pose):
    for pose_bone in armature.pose.bones:
        location, scale, rotation_mode, rotation_quaternion, rotation_euler = saved_pose[pose_bone.name]
        pose_bone.location = location
        pose_bone.scale = scale
        pose_bone.rotation_mode = rotation_mode
        pose_bone.rotation_quaternion = rotation_quaternion
        pose_bone.rotation_euler = rotation_euler


class ProtoTools_QuickExportAllActions(bpy.types.Operator):
    """Export all Actions on selected Armature as FBX animations.\nDo not select the bound Mesh, unless the Mesh has Shape Key animation"""
    bl_idname = "prototools.quick_export_allactions"
    bl_label = "Quick Export All Actions"
    
    # Proto Addition
    export_name: StringProperty(
        name="Export Name",
        description="Name to identify this export, displayed in warnings. Internal, not set by users",
        options={'HIDDEN'},
        default="",
    )
    
    batch_export_item_index: IntProperty(default=-1)
    
    # (optional) list of object names to export, overrides other methods of object selection
    # may contain a name to be renamed-to
    export_object_list: CollectionProperty(
        type=ProtoExportFBX_ExportListEntry,
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        settings = bpy.context.preferences.addons[addon_package_name].preferences
        export_properties = get_export_properties_for_operator(context, self.batch_export_item_index)
        
        # We use a different path property with one_file_per_action
        filepath = export_properties.all_anims_path
        filepath_folder = export_properties.anim_folder_path
        
        # Validate file / folder
        if export_properties.one_file_per_action:
            if filepath_folder == "" or filepath_folder == "/":
                self.report({'ERROR'}, "Invalid File Path - Set a path above.")
                return {'CANCELLED'}
            
            # Should be a path to a folder
            if filepath_folder[-1] != '/' and filepath_folder[-1] != '\\':
                self.report({'ERROR'}, "Invalid File Path - With 1 File Per Action, must specify a folder name.")
                return {'CANCELLED'}
        else:
            if filepath == "" or filepath == "/":
                self.report({'ERROR'}, "Invalid File Path - Set a path above.")
                return {'CANCELLED'}
            
            # Should be a path to a file
            if filepath[-1] == '/' or filepath[-1] == '\\':
                self.report({'ERROR'}, "Invalid File Path - Must specify a file name.")
                return {'CANCELLED'}
        
        # Get final export objects (either selection, or optional overriden export list from batch export)
        # Convert self.export_object_list to final_export_object_list
        final_export_objects = context.selected_objects
        final_export_object_list = []
        if len(self.export_object_list) > 0:
            # use export list instead of current selection
            final_export_objects.clear()
            for entry in self.export_object_list:
                final_export_objects.append(bpy.data.objects[entry.name])
                # Can't pass CollectionProperty through operator, must convert to a plain list(dict())
                final_entry = dict()
                final_entry["name"] = entry.name
                final_entry["rename_name"] = entry.rename_name
                final_export_object_list.append(final_entry)
        
        # Must have objects selected
        if final_export_objects == None or len(final_export_objects) == 0:
            self.report({'ERROR'}, "Invalid Selection - No Objects selected.")
            return {'CANCELLED'}
        
        # Cannot select multiple objects
        if len(final_export_objects) > 1:
            self.report({'ERROR'}, "Invalid Selection - Must only select 1 Armature.")
            return {'CANCELLED'}
        
        # Must have exactly 1 armature selected
        armature = None
        for ob in final_export_objects:
            if ob.type == 'ARMATURE':
                if armature != None:
                    self.report({'ERROR'}, "Multiple Armatures selected - Must select exactly 1 Armature.")
                    return {'CANCELLED'}
                armature = ob
        if armature == None:
            self.report({'ERROR'}, "No Armature selected - Must select exactly 1 Armature.")
            return {'CANCELLED'}
        
        # Make sure armature has bones
        if armature.pose == None or len(armature.pose.bones) == 0:
            self.report({'ERROR'}, "Invalid Armature - Must have at least 1 bone.")
            return {'CANCELLED'}
        
        # NOTE: for do_armature_slot_name_filter, if this is NOT one file per action, we don't have a way to
        # limit which actions will get exported by the default FBX exporter, so we don't filter by slot name
        actions = get_actions_for_armature(armature, armature.name, do_armature_slot_name_filter=export_properties.one_file_per_action)
        
        # Make sure we have any actions
        if len(actions) == 0:
            if bpy.app.version >= (4, 4, 0) and settings.action_slot_behavior == 'ARMATURE_NAME' and export_properties.one_file_per_action:
                # Determine if there are any valid actions when NOT filtering by slot name
                no_filter_actions = get_actions_for_armature(armature, armature.name, do_armature_slot_name_filter=False)
                if len(no_filter_actions) > 0:
                    self.report({'ERROR'}, "No Valid Actions - found no actions to export for the selected Armature.\nDo your Actions have Slots matching the name of your Armature? Check the Quick Action Select panel.")
                else:
                    self.report({'ERROR'}, "No Valid Actions - found no actions to export for the selected Armature.")
            else:
                self.report({'ERROR'}, "No Valid Actions - found no actions to export for the selected Armature.")
            return {'CANCELLED'}
        
        # Make sure flat bone hierarchy specifies a valid bone
        if export_properties.flat_bone_hierarchy and export_properties.flat_bone_hierarchy_root != "":
            if not export_properties.flat_bone_hierarchy_root in armature.data.bones:
                self.report({'ERROR'}, "Flat Bone Hierarchy mode - specified root bone '" + export_properties.flat_bone_hierarchy_root + "' not found in the armature.")
                return {'CANCELLED'}
        
        # Cache information to reset later
        self.original_active_action = armature.animation_data.action
        self.original_object_mode = bpy.context.object.mode
        self.original_pose = cache_pose(armature)
        self.original_frame_start = bpy.context.scene.frame_start
        self.original_frame_end = bpy.context.scene.frame_end
        self.original_selected_objects = bpy.context.selected_objects
        self.original_active_selection = bpy.context.view_layer.objects.active
        self.original_mode = context.mode
        result = set()
        
        # Run the export(s)
        try:
            # Switch to Object Mode
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except:
                pass
            
            bake_scale_mode, bake_scale_custom, armature_name, skip_armature_object, bake_z_forward, use_space_transform = get_final_scene_conversion_options(context, export_properties)
            action_whitelist = get_final_action_filter(context, export_properties)
            
            # Run one export in one_file_per_action mode
            result = bpy.ops.proto_export_scene.fbx(
                filepath = filepath_folder if export_properties.one_file_per_action else filepath, # NOTE: in one_file_per_action mode, pass in folder path. Otherwise, file path
                export_name = self.export_name,
                # Include
                use_selection = True,
                use_visible = True,
                use_active_collection = False,
                collection = "",
                object_types = {'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'},
                use_custom_props = True, # Export curve data (e.g. shapekey animation)
                export_object_list = final_export_object_list,
                # Conversion
                bake_scale_mode = bake_scale_mode,
                bake_scale_custom = bake_scale_custom,
                armature_name = armature_name,
                skip_armature_object = skip_armature_object,
                bake_z_forward = bake_z_forward,
                use_space_transform = use_space_transform,
                move_to_origin = export_properties.move_to_origin,
                # Geometry
                use_mesh_modifiers = export_properties.apply_modifiers,
                # Bake Animations
                bake_anim = True,
                animation_export_mode = 'MultipleActions',
                one_file_per_action = export_properties.one_file_per_action,
                action_whitelist = action_whitelist,
                # Proto Options
                min_two_frames = export_properties.min_two_frames,
                remove_scale_from_bones = export_properties.remove_scale_from_bones,
                remove_bone_rotation = export_properties.remove_bone_rotation,
                flat_bone_hierarchy = export_properties.flat_bone_hierarchy,
                flat_bone_hierarchy_root = export_properties.flat_bone_hierarchy_root,
                bake_anim_simplify_factor = export_properties.bake_anim_simplify_factor,
                export_shapekey_animation = export_properties.export_shapekey_animation,
                shapekey_export_mode = export_properties.shapekey_export_mode,
                export_zeroed_shapekeys = export_properties.export_zeroed_shapekeys,
                armature_shapekey_scale = export_properties.armature_shapekey_scale,
                export_custom_property_animation = export_properties.export_custom_property_animation,
                export_zeroed_custom_properties = export_properties.export_zeroed_custom_properties,
                export_non_deform_custom_properties = export_properties.export_non_deform_custom_properties,
                export_armature_object_custom_properties = export_properties.export_armature_object_custom_properties,
                export_armature_data_custom_properties = export_properties.export_armature_data_custom_properties,
                dont_simplify_root_bone = export_properties.dont_simplify_root_bone,
                action_name_style = export_properties.action_name_style,
                action_name_sharedname = export_properties.action_name_sharedname,
                animation_force_dummy_mesh = export_properties.animation_force_dummy_mesh
            )
            
        finally:
            # Reset the original active action
            armature.animation_data.action = self.original_active_action
            
            # Reset the original pose
            #bpy.ops.object.mode_set(mode='POSE')
            #armature.pose = self.original_pose
            #bpy.ops.object.mode_set(self.original_object_mode)
            restore_pose(armature, self.original_pose)
            
            # Reset the original timeline frame range
            bpy.context.scene.frame_start = self.original_frame_start
            bpy.context.scene.frame_end = self.original_frame_end
            
            # Re-select objects from the start of the export
            bpy.ops.object.select_all(action='DESELECT')
            for ob in self.original_selected_objects:
                ob.select_set(state=True)
            bpy.context.view_layer.objects.active = self.original_active_selection
            
            # Restore previous mode
            try:
                bpy.ops.object.mode_set(mode=self.original_mode)
            except:
                pass
            
        
        if 'FINISHED' in result:
            self.report({'INFO'}, "Animations exported successfully")
        return {'FINISHED'}


class ProtoTools_QuickExportActionList_Refresh(bpy.types.Operator):
    """Refresh the list of Actions"""
    bl_idname = "prototools.refresh_quick_export_actionlist"
    bl_label = "Refresh Action list"
    
    def execute(self, context):
        export_properties = get_current_quick_export_properties(context)
        refresh_action_filter(export_properties.action_filter)
        return {'FINISHED'}


class ProtoTools_QuickExportActionList_SetAll(bpy.types.Operator):
    """Set all Actions enabled/disabled for export"""
    bl_idname = "prototools.set_all_quick_export_actionlist"
    bl_label = ""
    
    enable : BoolProperty()
    
    @classmethod
    def description(cls, context, properties):
        if properties.enable:
            return "Enable All"
        else:
            return "Disable All"
    
    def execute(self, context):
        export_properties = get_current_quick_export_properties(context)
        
        refresh_action_filter(export_properties.action_filter)
        
        for entry in export_properties.action_filter:
            entry.keep = self.enable
        
        return {'FINISHED'}


class ProtoTools_MakeAnimData(bpy.types.Operator):
    """Create Anim Data for an Object"""
    bl_idname = "prototools.makeanimdata"
    bl_label = "Create Anim Data"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.active_object != None and context.active_object.animation_data == None:
            return True
    
    def execute(self, context):
        ob = context.active_object
        if ob.animation_data == None:
            ob.animation_data_create()
        
        return {'FINISHED'}


class ProtoTools_NewAction(bpy.types.Operator):
    """Create New Action"""
    bl_idname = "prototools.actionnew"
    bl_label = "New Action"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            return True
    
    def execute(self, context):
        ob = context.active_object
        new_action = None
        
        duplicate_action = False
        if ob.animation_data != None and ob.animation_data.action != None:
            # if the object already has an action assigned, duplicate it
            new_action = ob.animation_data.action.copy()
            duplicate_action = True
        else:
            # if not, create a new action
            new_action_name = "Action"
            new_action = bpy.data.actions.new(new_action_name)
            if ob.animation_data == None:
                ob.animation_data_create()
        
        # Set fake user on the new action (convenience to avoid accidentally losing actions)
        new_action.use_fake_user = True
        
        ob.animation_data.action = new_action
        
        if bpy.app.version >= (4, 4, 0):
            # Blender 4.4 and up
            if not duplicate_action:
                # Create an Action Slot with the name of the Object, and assign it
                new_slot = new_action.slots.new(ob.id_type, ob.name)
                ob.animation_data.action_slot = new_slot
        
        return {'FINISHED'}


class ProtoTools_UnlinkAction(bpy.types.Operator):
    """Unlink this action from the active action slot"""
    bl_idname = "prototools.actionunlink"
    bl_label = "Unlink Action"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            return True
    
    def execute(self, context):
        ob = context.active_object
        if ob.animation_data != None and ob.animation_data.action != None:
            ob.animation_data.action = None
        
        return {'FINISHED'}
        

class ProtoTools_DeleteAction(bpy.types.Operator):
    """Delete this Action from the Blender file - WARNING: this will permanently delete the Action!"""
    bl_idname = "prototools.actiondelete"
    bl_label = "Delete Action"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            return True
    
    def execute(self, context):
        ob = context.active_object
        if ob.animation_data != None and ob.animation_data.action != None:
            action = ob.animation_data.action
            bpy.data.actions.remove(action, do_unlink = True)
        
        return {'FINISHED'}
        
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, title="Delete Action?")


class ProtoTools_DeleteActionSlot(bpy.types.Operator):
    """Delete this Action Slot from the Blender file - WARNING: this will permanently delete the Slot!"""
    bl_idname = "prototools.action_slot_delete"
    bl_label = "Delete Action Slot"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            return True
    
    def execute(self, context):
        ob = context.active_object
        if ob.animation_data != None and ob.animation_data.action != None and ob.animation_data.action_slot != None :
            action = ob.animation_data.action
            current_slot = ob.animation_data.action_slot
            action.slots.remove(current_slot)
        
        return {'FINISHED'}
        
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, title="Delete Action Slot?")


class ProtoTools_UpdateLegacySlot(bpy.types.Operator):
    """Migrate the animation data currently in Slot 'Legacy Slot' to an Action Slot named after this Object"""
    bl_idname = "prototools.update_legacy_slot"
    bl_label = "Migrate Legacy Slot"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            return True
    
    def execute(self, context):
        ob = context.active_object
        if ob.animation_data != None and ob.animation_data.action != None:
            action = ob.animation_data.action
            desired_name = ob.name
            
            # Rename conflicting slot name (if it exists)
            for slot in action.slots:
                if slot.name_display == desired_name:
                    slot.name_display = desired_name + "_old"
                    break;
                    
            # Rename Legacy Slot to desired name
            for slot in action.slots:
                if slot.name_display == "Legacy Slot":
                    slot.name_display = desired_name
                    
                    # Select the newly renamed slot
                    ob.animation_data.action_slot = slot
                    break
            
            
        return {'FINISHED'}


class ProtoTools_DeleteLegacySlot(bpy.types.Operator):
    """Delete animation Slot 'Legacy Slot'. WARNING: This Slot may contain animation data authored in a previous version of Blender"""
    bl_idname = "prototools.delete_legacy_slot"
    bl_label = "Delete Legacy Slot"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            return True
    
    def execute(self, context):
        ob = context.active_object
        if ob.animation_data != None and ob.animation_data.action != None:
            action = ob.animation_data.action
            
            # Delete Legacy Slot to desired name
            for slot in action.slots:
                if slot.name_display == "Legacy Slot":
                    action.slots.remove(slot)
                    break
            
        return {'FINISHED'}


class ProtoTools_DeleteMeshAnimationData(bpy.types.Operator):
    """Delete Mesh animation data (will not delete any actions or keyframes)\n\nFor game assets, animation data should be on an Armature, not Mesh. Mesh animation data can result in erroneous animations exported with FBX files"""
    bl_idname = "prototools.delete_mesh_animation_data"
    bl_label = "Delete Mesh Animation Data"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.active_object != None and context.active_object.type == 'MESH':
            return True
    
    def execute(self, context):
        ob = context.active_object
        if ob.animation_data != None:
            ob.animation_data_clear()
        return {'FINISHED'}


class ProtoTools_SwitchToObjectNameSlot(bpy.types.Operator):
    """Switch to Action Slot with the same name as this Object"""
    bl_idname = "prototools.switch_to_object_name_slot"
    bl_label = "Switch To Object Name Slot"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            return True
    
    def execute(self, context):
        ob = context.active_object
        if ob.animation_data != None and ob.animation_data.action != None:
            action = ob.animation_data.action
            desired_name = ob.name
            
            # Switch to slot with desired name
            for slot in action.slots:
                if slot.name_display == desired_name:
                    ob.animation_data.action_slot = slot
                    break
            
        return {'FINISHED'}


class ProtoTools_CreateObjectNameSlot(bpy.types.Operator):
    """Create a new Action Slot named after this Object"""
    bl_idname = "prototools.create_object_name_slot"
    bl_label = "Create Object Name Slot"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            return True
    
    def execute(self, context):
        ob = context.active_object
        if ob.animation_data != None and ob.animation_data.action != None:
            action = ob.animation_data.action
            desired_name = ob.name
            
            # Rename conflicting slot name (if it exists)
            for slot in action.slots:
                if slot.name_display == desired_name:
                    slot.name_display = desired_name + "_old"
                    break;
                    
            # Deselect current slot
            ob.animation_data.action_slot = None
            
            # Create new slot with desired name
            new_slot = action.slots.new(ob.id_type, ob.name)
            ob.animation_data.action_slot = new_slot
            
        return {'FINISHED'}


class ProtoTools_RenameCurrentSlotToObjectName(bpy.types.Operator):
    """Rename the current Action Slot to the Object's name"""
    bl_idname = "prototools.rename_current_slot_to_object_name"
    bl_label = "Rename Current Slot To Object Name"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            return True
    
    def execute(self, context):
        ob = context.active_object
        if ob.animation_data != None and ob.animation_data.action != None and ob.animation_data.action_slot != None:
            action = ob.animation_data.action
            desired_name = ob.name
            
            # Rename conflicting slot name (if it exists)
            for slot in action.slots:
                if slot.name_display == desired_name:
                    slot.name_display = desired_name + "_old"
                    break;
            
            # Rename current slot
            ob.animation_data.action_slot.name_display = desired_name
            
        return {'FINISHED'}


class ProtoTools_TimelineToAction(bpy.types.Operator):
    """Set the Scene Timeline to match the start and end of the current Action"""
    bl_idname = "prototools.timelinetoaction"
    bl_label = "Set Timeline"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            return True
    
    def execute(self, context):
        proto_actionselect = context.scene.proto_actionselect
        ob = context.active_object
        if ob.animation_data != None and ob.animation_data.action != None:
            action = ob.animation_data.action
            frame_start, frame_end = action.frame_range
            if proto_actionselect.set_timeline_ignore_zero == True and frame_start < 1 and frame_end >= 2:
                frame_start = 1
            bpy.context.scene.frame_start = math.floor(frame_start)
            bpy.context.scene.frame_end = math.floor(frame_end)
        
        return {'FINISHED'}


class ProtoTools_Copy_QuickExport_Options(bpy.types.Operator):
    """Copy Export Options"""
    bl_idname = "prototools.copy_quickexport_options"
    bl_label = "Copy"
    
    batch_export_item_index: IntProperty(default=-1)
    
    def draw(self, context):
        layout = self.layout
        current_export_properties = get_export_properties_for_operator(context, self.batch_export_item_index)
        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text="Copied")

    def execute(self, context):
        current_export_properties = get_export_properties_for_operator(context, self.batch_export_item_index)
        
        proto_quickexport = context.scene.proto_quickexport
        proto_quickexport.clipboard_export_properties.copy_options(current_export_properties)
        proto_quickexport.clipboard_export_properties_copied = True
        
        self.report({'INFO'}, "Copied Export Options")
        
        return {"FINISHED"}

    #def invoke(self, context, event):
    #    return context.window_manager.invoke_popup(self, width=100)


class ProtoTools_Paste_QuickExport_Options(bpy.types.Operator):
    """Paste Export Options"""
    bl_idname = "prototools.paste_quickexport_options"
    bl_label = "Paste"
    
    batch_export_item_index: IntProperty(default=-1, options={'HIDDEN'},)
    
    @classmethod
    def poll(cls, context):
        proto_quickexport = context.scene.proto_quickexport
        return proto_quickexport.clipboard_export_properties_copied
    
    def execute(self, context):
        current_export_properties = get_export_properties_for_operator(context, self.batch_export_item_index)
        
        proto_quickexport = context.scene.proto_quickexport
        current_export_properties.copy_options(proto_quickexport.clipboard_export_properties)
        
        self.report({'INFO'}, "Pasted Export Options")
        
        return {"FINISHED"}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, title="Paste Export Options?")


class ProtoTools_InfoPopup(bpy.types.Operator):
    """Pop up a dialog with information. No functionality, the only interaction the user has is closing it"""
    bl_idname = "prototools.infopopup"
    bl_label = "Info"
    
    title : StringProperty(default="Info")
    text : StringProperty(default="")
    icon : StringProperty(default='INFO')
    
    def draw(self, context):
        layout = self.layout
        
        # Display multi-line text
        text_lines = self.text.split('\n')
        for line in text_lines:
            did_icon = False
            # text wrap
            wrapper = textwrap.TextWrapper(width=160)
            final_lines = wrapper.wrap(text=line)
            for final_line in final_lines:
                if did_icon:
                    layout.label(text=final_line)
                else:
                    layout.label(text=final_line, icon=self.icon)
                    did_icon = True
        
        props = layout.template_popup_confirm("", text="", cancel_text="OK")

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=900, title=self.title)


class ProtoTools_InfoPopupArray_Entry(bpy.types.PropertyGroup):
    header: StringProperty(default="")
    text: StringProperty(default="")
    icon : StringProperty(default='INFO')


class ProtoTools_InfoPopupArray(bpy.types.Operator):
    """Pop up a dialog with information, with arrays of headers/lines. No functionality, the only interaction the user has is closing it"""
    bl_idname = "prototools.infopopuparray"
    bl_label = "Info"
    
    title : StringProperty(default="Info")
    
    # NOTE: you can pass lists of dictionaries into this property when invoking the operator
    # E.G.: entries=[{"name":"MyEntry", "header":"Header Name", "text":"text content", "icon":"ERROR"}]
    entries : CollectionProperty(
        type=ProtoTools_InfoPopupArray_Entry,
    )
    
    def draw(self, context):
        layout = self.layout
        
        for entry in self.entries:
            # Header
            layout.label(text=entry.header)
            
            # Content
            # Display multi-line text
            text_lines = entry.text.split('\n')
            for line in text_lines:
                did_icon = False
                # text wrap
                wrapper = textwrap.TextWrapper(width=160)
                final_lines = wrapper.wrap(text=line)
                for final_line in final_lines:
                    if did_icon:
                        layout.label(text=final_line)
                    else:
                        layout.label(text=final_line, icon=entry.icon)
                        did_icon = True
        
        props = layout.template_popup_confirm("", text="", cancel_text="OK")

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=900, title=self.title)


operator_classes = (
    ProtoTools_QuickExportSetOptionsPreset,
    ProtoTools_QuickExportMeshAndAnimations,
    ProtoTools_QuickExportMesh,
    ProtoTools_QuickExportCurAction,
    ProtoTools_QuickExportAllActions,
    
    ProtoTools_QuickExportActionList_Refresh,
    ProtoTools_QuickExportActionList_SetAll,
    
    ProtoTools_MakeAnimData,
    ProtoTools_NewAction,
    ProtoTools_UnlinkAction,
    ProtoTools_DeleteAction,
    ProtoTools_DeleteActionSlot,
    
    ProtoTools_UpdateLegacySlot,
    ProtoTools_DeleteLegacySlot,
    ProtoTools_DeleteMeshAnimationData,
    ProtoTools_SwitchToObjectNameSlot,
    ProtoTools_CreateObjectNameSlot,
    ProtoTools_RenameCurrentSlotToObjectName,
    
    ProtoTools_TimelineToAction,
    
    ProtoTools_Copy_QuickExport_Options,
    ProtoTools_Paste_QuickExport_Options,
    
    ProtoTools_InfoPopup,
    ProtoTools_InfoPopupArray_Entry,
    ProtoTools_InfoPopupArray
)


def register():
    for operator in operator_classes:
        bpy.utils.register_class(operator)


def unregister():
    for operator in operator_classes:
        bpy.utils.unregister_class(operator)


# Attempt at making a filtered list of actions to select from, instead of template_ID
# Would be added to UI with:
#    action_selector = group.operator('prototools.choose_action', text="Test", icon='ACTION')
#
#class ProtoTools_ChooseAction(bpy.types.Operator):
#    bl_idname = "prototools.choose_action"
#    bl_label = "Choose Action"
#    bl_options = {'INTERNAL'}
#    bl_property = "enum"
#    
#    def get_enum_options(self, context):
#        actions = get_actions_for_armature(armature)
#        action_names = []
#        for action in actions:
#            action_names.append(action.name)
#        return action_names
#    
#    enum: EnumProperty(items=get_enum_options, name="Actions")
#    node_tree: StringProperty()
#    node: StringProperty()
#    
#    def execute(self, context):
#        tree = bpy.data.node_groups[self.node_tree]
#        node = tree.nodes[self.node]
#        node.item_set = true
#        node.set_item(self.enum)
#        return {"FINISHED"}
#    
#    def invoke(self, context, event):
#        context.window_manager.invoke_search_popup(self)
#        return {"FINISHED"}

