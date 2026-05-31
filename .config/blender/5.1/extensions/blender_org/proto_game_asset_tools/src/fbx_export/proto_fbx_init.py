# SPDX-FileCopyrightText: 2011-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later
#
# Modified by PROTOWLF 2026
#
# PROTO FBX Export Wrapper
# Wraps additional features around Blender's default FBX Exporter


# import, reload if already imported
if "proto_fbx_utils" not in locals():
    from . import proto_fbx_utils
    #print("PROTO Tools - proto_fbx_init: Importing")
else:
    import importlib
    proto_fbx_utils = importlib.reload(proto_fbx_utils)
    #print("PROTO Tools - proto_fbx_init: Reloading Scripts") 

from .proto_fbx_utils import (
    select_objects_for_export,
    get_export_objects,
    get_actions_for_armature,
    find_slot_in_action_for_armature,
    duplicate_export_objects,
    transform_export_objects,
    apply_min_two_frames_to_actions,
    do_fbx_export,
    cleanup_scene,
    init_helper_armatures,
    get_action_filepath,
    create_dummy_shapekey_meshes,
    get_meshes_for_armatures,
    get_shapekey_objects_to_duplicate_from_armature_meshes,
    refresh_action_filter
)


import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
    IntProperty,
    CollectionProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    orientation_helper,
    path_reference_mode,
    axis_conversion,
    poll_file_object_drop,
)
import time
import math
import os


addon_package_name = __package__
addon_package_name = addon_package_name.removesuffix(".src.fbx_export")


class ProtoExportFBX_ExportListEntry(bpy.types.PropertyGroup):
    name: StringProperty(default="")
    rename_name: StringProperty(default="")


# --------------------------------------------------------------------------
# ProtoExportFBX - Action Filter classes
# Note that ProtoToolsQuickExportProperties contains properties just like
# these, but the exporter itself stores this separately
# --------------------------------------------------------------------------
class ProtoExportFBX_RefreshActionList(bpy.types.Operator):
    """Refresh the list of Actions"""
    bl_idname = "proto_export_scene.refresh_actionlist"
    bl_label = "Refresh Action list"
    
    def execute(self, context):
        proto_exportfbx = context.scene.proto_exportfbx
        refresh_action_filter(proto_exportfbx.action_filter)
        return {'FINISHED'}


class ProtoExportFBX_ActionFilterEntry(bpy.types.PropertyGroup):
    action: bpy.props.PointerProperty(type=bpy.types.Action)
    keep: bpy.props.BoolProperty(name="Include in exports")


def on_use_action_filter_changed(self, context):
    proto_exportfbx = context.scene.proto_exportfbx
    if self.use_action_filter is True:
        refresh_action_filter(proto_exportfbx.action_filter)


class ProtoExportFBX_ActionFilterProperties(bpy.types.PropertyGroup):
    def copy_from(self, old):
        self.action_filter = old.action_filter
        self.action_filter_index = old.action_filter_index
    
    action_filter: CollectionProperty(
        name="Action Filter",
        description="Select Actions considered for export",
        type=ProtoExportFBX_ActionFilterEntry,
    )
    
    action_filter_index: IntProperty(
        name="Action Index",
        description="Index of currently selected Action in the Action Filter list",
        default=0
    )
    
    

# --------------------------------------------------------------------------
# ProtoExportFBX
# --------------------------------------------------------------------------
class ProtoExportFBX_ActionWhitelistEntry(bpy.types.PropertyGroup):
    action_name: bpy.props.StringProperty(default="")


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ProtoExportFBX(bpy.types.Operator, ExportHelper):
    """Open FBX file exporter dialogue"""
    bl_idname = "proto_export_scene.fbx"
    bl_label = "PROTO Export FBX"
    bl_options = {'UNDO', 'PRESET'}

    filename_ext = ".fbx"
    filter_glob: StringProperty(default="*.fbx", options={'HIDDEN'})
    
    # Proto Addition - (optional) list of object names to export, overrides other methods of object selection
    # may contain a name to be renamed-to
    export_object_list: CollectionProperty(
        type=ProtoExportFBX_ExportListEntry,
        options={'HIDDEN'},
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    use_selection: BoolProperty(
        name="Selected Objects",
        description="Export selected and visible objects only",
        default=True,
    )
    use_visible: BoolProperty(
        name='Visible Objects',
        description='Export visible objects only',
        default=True
    )
    use_active_collection: BoolProperty(
        name="Active Collection",
        description="Export only objects from the active collection (and its children)",
        default=False,
    )
    collection: StringProperty(
        name="Source Collection",
        description="Export only objects from this collection (and its children)",
        default="",
    )
    global_scale: FloatProperty(
        name="Scale",
        description="Scale all data (Some importers do not support scaled armatures!)",
        min=0.001, max=1000.0,
        soft_min=0.01, soft_max=1000.0,
        default=1.0,
    )
    apply_unit_scale: BoolProperty(
        name="Apply Unit",
        description="Take into account current Blender units settings (if unset, raw Blender Units values are used as-is)",
        default=True,
    )
    apply_scale_options: EnumProperty(
        items=(('FBX_SCALE_NONE', "All Local",
                "Apply custom scaling and units scaling to each object transformation, FBX scale remains at 1.0"),
               ('FBX_SCALE_UNITS', "FBX Units Scale",
                "Apply custom scaling to each object transformation, and units scaling to FBX scale"),
               ('FBX_SCALE_CUSTOM', "FBX Custom Scale",
                "Apply custom scaling to FBX scale, and units scaling to each object transformation"),
               ('FBX_SCALE_ALL', "FBX All",
                "Apply custom scaling and units scaling to FBX scale"),
               ),
        name="Apply Scalings",
        description="How to apply custom and units scalings in generated FBX file "
        "(Blender uses FBX scale to detect units on import, "
        "but many other applications do not handle the same way)",
    )

    use_space_transform: BoolProperty(
        name="Use Space Transform",
        description="Apply global space transform to the object rotations. When disabled "
        "only the axis space is written to the file and all object transforms are left as-is",
        default=True,
    )
    bake_space_transform: BoolProperty(
        name="Apply Transform",
        description="Bake space transform into object data, avoids getting unwanted rotations to objects when "
        "target space is not aligned with Blender's space "
        "(WARNING! experimental option, use at own risk, known to be broken with armatures/animations)",
        default=False,
    )
    
    object_types: EnumProperty(
        name="Object Types",
        options={'ENUM_FLAG'},
        items=(('EMPTY', "Empty", ""),
               ('CAMERA', "Camera", ""),
               ('LIGHT', "Lamp", ""),
               ('ARMATURE', "Armature", "WARNING: not supported in dupli/group instances"),
               ('MESH', "Mesh", ""),
               ('OTHER', "Other", "Other geometry types, like curve, metaball, etc. (converted to meshes)"),
               ),
        description="Which kind of object to export",
        default={'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'},
    )

    use_mesh_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers to mesh objects (except Armature ones) - "
        "WARNING: prevents exporting shape keys",
        default=True,
    )
    use_mesh_modifiers_render: BoolProperty(
        name="Use Modifiers Render Setting",
        description="Use render settings when applying modifiers to mesh objects (DISABLED in Blender 2.8)",
        default=True,
    )
    mesh_smooth_type: EnumProperty(
        name="Smoothing",
        items=(('OFF', "Normals Only", "Export only normals instead of writing edge or face smoothing data"),
               ('FACE', "Face", "Write face smoothing"),
               ('EDGE', "Edge", "Write edge smoothing"),
               ),
        description="Export smoothing information "
        "(prefer 'Normals Only' option if your target importer understand split normals)",
        default='FACE',
    )
    colors_type: EnumProperty(
        name="Vertex Colors",
        items=(('NONE', "None", "Do not export color attributes"),
               ('SRGB', "sRGB", "Export colors in sRGB color space"),
               ('LINEAR', "Linear", "Export colors in linear color space"),
               ),
        description="Export vertex color attributes",
        default='SRGB',
    )
    prioritize_active_color: BoolProperty(
        name="Prioritize Active Color",
        description="Make sure active color will be exported first. Could be important "
        "since some other software can discard other color attributes besides the first one",
        default=False,
    )
    use_subsurf: BoolProperty(
        name="Export Subdivision Surface",
        description="Export the last Catmull-Rom subdivision modifier as FBX subdivision "
        "(does not apply the modifier even if 'Apply Modifiers' is enabled)",
        default=False,
    )
    use_mesh_edges: BoolProperty(
        name="Loose Edges",
        description="Export loose edges (as two-vertices polygons)",
        default=False,
    )
    use_tspace: BoolProperty(
        name="Tangent Space",
        description="Add binormal and tangent vectors, together with normal they form the tangent space "
        "(will only work correctly with tris/quads only meshes!)",
        default=False,
    )
    use_triangles: BoolProperty(
        name="Triangulate Faces",
        description="Convert all faces to triangles",
        default=False,
    )
    use_custom_props: BoolProperty(
        name="Custom Properties",
        description="Export custom properties",
        default=False,
    )
    add_leaf_bones: BoolProperty(
        name="Add Leaf Bones",
        description="Append a final bone to the end of each chain to specify last bone length "
        "(use this when you intend to edit the armature from exported data)",
        default=False  # False for commit!
    )
    primary_bone_axis: EnumProperty(
        name="Primary Bone Axis",
        items=(('X', "X Axis", ""),
               ('Y', "Y Axis", ""),
               ('Z', "Z Axis", ""),
               ('-X', "-X Axis", ""),
               ('-Y', "-Y Axis", ""),
               ('-Z', "-Z Axis", ""),
               ),
        default='Y',
    )
    secondary_bone_axis: EnumProperty(
        name="Secondary Bone Axis",
        items=(('X', "X Axis", ""),
               ('Y', "Y Axis", ""),
               ('Z', "Z Axis", ""),
               ('-X', "-X Axis", ""),
               ('-Y', "-Y Axis", ""),
               ('-Z', "-Z Axis", ""),
               ),
        default='X',
    )
    use_armature_deform_only: BoolProperty(
        name="Only Deform Bones",
        description="Only write deforming bones (and non-deforming ones when they have deforming children)",
        default=True,
    )
    armature_nodetype: EnumProperty(
        name="Armature FBXNode Type",
        items=(('NULL', "Null", "'Null' FBX node, similar to Blender's Empty (default)"),
               ('ROOT', "Root", "'Root' FBX node, supposed to be the root of chains of bones..."),
               ('LIMBNODE', "LimbNode", "'LimbNode' FBX node, a regular joint between two bones..."),
               ),
        description="FBX type of node (object) used to represent Blender's armatures "
        "(use the Null type unless you experience issues with the other app, "
        "as other choices may not import back perfectly into Blender...)",
        default='NULL',
    )
    bake_anim: BoolProperty(
        name="Baked Animation",
        description="Export baked keyframe animation",
        default=False,
    )
    bake_anim_use_all_bones: BoolProperty(
        name="Key All Bones",
        description="Force exporting at least one key of animation for all bones "
        "(needed with some target applications, like UE4)",
        default=True,
    )
    #bake_anim_use_nla_strips: BoolProperty(
    #    name="NLA Strips",
    #    description="Export each non-muted NLA strip as a separated FBX's AnimStack, if any, "
    #    "instead of global scene animation. NOTE: if this is true, and no actions are pushed down into the NLA stack, then no animations will be exported in the FBX file!",
    #    default=False,
    #)
    #bake_anim_use_all_actions: BoolProperty(
    #    name="All Actions",
    #    description="Export each action as a separated FBX's AnimStack, instead of global scene animation "
    #    "(note that animated objects will get all actions compatible with them, "
    #    "others will get no animation at all)",
    #    default=True,
    #)
    bake_anim_force_startend_keying: BoolProperty(
        name="Force Start/End Keying",
        description="Always add a keyframe at start and end of actions for animated channels",
        default=True,
    )
    bake_anim_step: FloatProperty(
        name="Sampling Rate",
        description="How often to evaluate animated values (in frames)",
        min=0.01, max=100.0,
        soft_min=0.1, soft_max=10.0,
        default=1.0,
    )
    bake_anim_simplify_factor: FloatProperty(
        name="Simplify",
        description="How much to compress animation data (0.0 = best accuracy, largest file size. Higher numbers = less accuracy, smaller file size).\nGenerally leave at default of 0.1. Try setting to 0.0 if you see innacuracy in exported animation.\n\n(NOTE: innacurate animation is often the result of scaled bones, not the Simplify setting)",
        min=0.0, max=100.0,
        soft_min=0.0, soft_max=10.0,
        default=0.1,
    )
    path_mode: path_reference_mode
    embed_textures: BoolProperty(
        name="Embed Textures",
        description="Embed textures in FBX binary file (only for \"Copy\" path mode!)",
        default=False,
    )
    
    # Proto: BATCH MODE NOT SUPPORTED
    # batch_mode: EnumProperty(
    #     name="Batch Mode",
    #     items=(('OFF', "Off", "Active scene to file"),
    #            ('SCENE', "Scene", "Each scene as a file"),
    #            ('COLLECTION', "Collection",
    #             "Each collection (data-block ones) as a file, does not include content of children collections"),
    #            ('SCENE_COLLECTION', "Scene Collections",
    #             "Each collection (including master, non-data-block ones) of each scene as a file, "
    #             "including content from children collections"),
    #            ('ACTIVE_SCENE_COLLECTION', "Active Scene Collections",
    #             "Each collection (including master, non-data-block one) of the active scene as a file, "
    #             "including content from children collections"),
    #            ),
    # )
    #use_batch_own_dir: BoolProperty(
    #    name="Batch Own Dir",
    #    description="Create a dir for each exported file",
    #    default=True,
    #)
    use_metadata: BoolProperty(
        name="Use Metadata",
        default=True,
        options={'HIDDEN'},
    )
    
    # Proto Addition
    export_name: StringProperty(
        name="Export Name",
        description="Name to identify this export, displayed in warnings. Internal, not set by users",
        options={'HIDDEN'},
        default="",
    )
    
    # Proto Addition
    bake_scale_mode: EnumProperty(
        name="Scene Scale",
        description="Bake in a conversion from Blender's default units (meters) to a different length unit. Use this when exporting for engines that don't handle unit conversions well on import",
        items=(('None', "None", "Do not bake a unit conversion"),
               ('Centimeters', "Centimeters (Unreal, Unity, Godot)", "Bake a unit conversion to centimeters.\n\nRecommended for: Unreal, Unity, Godot\nNOTE: Unity and Godot use meters, but expect cenimters in FBX, or they will apply 100x scale to imported objects"),
               ('Inches', "Inches (Source)", "Bake a unit conversion to inches.\n\nRecommended for: Source, Source 2"),
               ('Custom', "Custom", "Bake a custom conversion. Enter a multiplier to apply to meters (e.g. 100 for centimeters, 39.37 for inches)"),
               ),
        default='Centimeters',
    )
    
    # Proto Addition
    bake_scale_custom: FloatProperty(
        name="Custom Scale",
        description="A custom unit conversion. Enter a multiplier to apply to meters (e.g. 100 for centimeters, 39.37 for inches)",
        min=0.0001, max=10000.0,
        soft_min=0.0001, soft_max=10000.0,
        default=1.0,
    )
    
    # PROTOWLF addition
    bake_z_forward: BoolProperty(
        name="Bake Z Forward",
        description="Bake in rotation to make the scene Z-forward, Y-Up, X-Left, matching Maya's coordinate system. Avoids issues with importers (e.g. Unity, Godot) applying 90 degree rotations to objects and bones.\n\nRecommended for: Unity, Godot",
        default=True,
    )
    
    # PROTOWLF addition
    remove_bone_rotation: BoolProperty(
        name="Remove Rotation from Bones",
        description="Remove all bone rotation from bind pose, making each bone have (0,0,0) rotation (in Blender's coordinate system)",
        default=False,
    )
    
    # Proto Addition
    armature_name: StringProperty(
        name="Rename Root",
        description="Blender exports the Armature object itself as node above the root bone. You may rename it, or leave blank to use the existing name.\n\nTIP: Unreal will import this node as a bone in the skeleton, but will strip it out if it is named 'Armature'; if you set this to 'Armature', this will cause Unreal to use the first bone as the root when imported",
        default="",
    )
    
    # Proto Addition
    skip_armature_object: BoolProperty(
        name="Skip Armature Object",
        description="By default, Blender exports the Armature object itself above the root bone. This is generally not desireable. If True, this option will remove it from the export.\n\nRecommended for: Unity, Godot.\n\nNOTE: If used without 'Bake Z Forward', may result in a rotated export.\n\nNOTE: Not recommended for Unreal, instead rename the Armature to 'Armature' to cause Unreal to remove it on-import",
        default=True,
    )
    
    # PROTOWLF addition
    move_to_origin: BoolProperty(
        name="Move To Origin",
        description="Move Object(s) to world origin before exporting, removing world offset from exported Model.\n\nNOTE: parented Objects are moved together. If you have multiple un-parented Objects in export, ensure that they have the same origin",
        default=False,
    )
    
    # Proto Addition
    min_two_frames: BoolProperty(
        name="Minimum 2 Frames",
        description="When exporting Actions, force frame range to be at least 2 frames long.\nFixes import issue with Unreal, where it cannot import 1 frame animations",
        default=False,
    )
    
    # Proto Addition
    remove_scale_from_bones: BoolProperty(
        name="Remove Scale from Bones",
        description="When exporting armatures and actions, remove all scaling from bones.\n\nTIP: if you see innacurate animations after export, it is often the result of scaled bones. This option can be used to work around rigs that producing scaled bones",
        default=False,
    )
    
    # Proto Addition
    flat_bone_hierarchy: BoolProperty(
        name="Flat Bone Hierarchy",
        description="When exporting armatures and actions, set all bones' parents to the given root bone.\n\nTIP: Useful if you want to do squash/stretch bone scaling in a game engine. A flat hierarchy avoids distorted transforms resulting from scaled bone chains, but is not recommended under normal circumstances",
        default=False,
    )
    
    # Proto Addition
    flat_bone_hierarchy_root: StringProperty(
        name="Root Bone Name",
        description="When using Flat Bone Hierarchy, name of the bone to treat as the root.\nLeave blank to make all bones have no parent (making the Armature itself the root)",
        default="",
    )
    
    # Poto Addition
    # How to export animations
    animation_export_mode: EnumProperty(
        name="Animation Mode",
        items=(('Scene', "Scene", "Export the current timeline"),
               ('CurrentAction', "Current Action (Armature)", "(Requires Armature) Export the Armature's current active Action as 1 animation"),
               ('MultipleActions', "Multiple Actions (Armature)", "(Requires Armature) Export multiple Actions from the Armature as animations"),
               ('NLAStrips', "All NLA Strips", "Export all NLA Strips from the Scene as animations"),
               ),
        default='Scene',
    )
    
    # Proto Addition
    one_file_per_action: BoolProperty(
		name="1 File Per Action",
        description="Save each Action to its own FBX animation file. Each file will be named after the Action's name",
		default=True,
	)
    
    # Proto Addition
    action_name_style: EnumProperty(
		name="Action File Names",
        description="When exporting 1 File Per Action, the format to use for their file names",
		items=(('Action', "Action", "Actions FBX files are saved as just their name:\nActionName.fbx"),
               ('Name_Action', "Name_Action", "Actions FBX files are saved with a shared name with _ActionName:\nSharedName_ActionName.fbx"),
               ('Name-Action', "Name-Action", "Actions FBX files are saved with a shared name with -ActionName:\nSharedName-ActionName.fbx"),
               ('Name@Action', "Name@Action", "Actions FBX files are saved with a shared name with @ActionName:\nSharedName@ActionName.fbx"),
               ),
        default='Action',
	)
    
    # Proto Addition
    action_name_sharedname: StringProperty(
		name="Shared Name",
        description="When exporting 1 File Per Action, shared name that will be combined with the Action Name to make a file name",
		default=""
	)
    
    # Proto Addition
    animation_force_dummy_mesh: BoolProperty(
        name="Anims Dummy Mesh (Unity)",
        description="If true, animation FBX files will always have a dummy Mesh inserted.\n\nThis is a workaround for Unity's FBX importer; when FBX files only contain animation, Unity's importer requires its 'Preserve Hierarchy' option to be enabled, or else it will import incorrectly. By inserting a dummy Mesh, animation FBX files will import correctly in Unity by-default.\n\nRecommended for: Unity",
        default=False
    )
    
    # Proto Addition
    # Not exposed to UI, used for other export UIs to send action whitelist (overrides use_action_filter)
    action_whitelist: CollectionProperty(
        name="Action Whitelist",
        type=ProtoExportFBX_ActionWhitelistEntry
    )
    
    # Proto Addition
    # List users set in manual export UI. action_filter stored in bpy.types.Scene.action_filter
    use_action_filter: BoolProperty(
        name="Enable Action Filter",
        description="Limit which Actions are considered for export",
        default=False,
        update=on_use_action_filter_changed,
    )
    
    # Proto Addition
    export_shapekey_animation: BoolProperty(
		name="Shape Key Animation",
        description="Export animation of Shape Keys",
		default=True,
	)
    
    # Proto Addition
    shapekey_export_mode: EnumProperty(
        name="Shape Key Anim Mode",
        items=(('ArmatureCustomProps', "Armature, Custom Props", "Export just Armature, Shape Key animation of deformed Meshes is detected and converted to Custom Property curves on the Armature root bone.\n\nRecommended for: Unreal.\nNote: Unity can import these curves, but will not automatically apply them to Blendshape animation"),
               ('ArmatureDummyMesh', "Armature, Dummy Mesh", "Export just Armature, Shape Key animation of deformed Meshes is detected and converted to Shape Key curves on a dummy mesh. Allows for real FBX blendshape curves while keeping filesize down.\n\nRecommended for: Unity, Godot.\nNote: If you wish to export a Mesh in the same FBX as its animations, do not use this option, use 'Mesh' instead"),
               ('Mesh', "Mesh", "(Default Blender exporter behavior) Export Armature and Mesh(es), Shape Key animation is detected on Mesh(es) and exported\n\nRecommended for: Any engine, when exporting Mesh and animations in one FBX file"),
               ),
        default='Mesh',
    )
    
    # Proto Addition
    export_zeroed_shapekeys: BoolProperty(
		name="Include Zeroed Shape Keys",
        description="When True, export Shape Key animation even if a Shape Key is zero for the entire animation. Otherwise, skip these Shape Keys",
		default=False,
	)
    
    # Proto Addition
    armature_shapekey_scale: FloatProperty(
		name="Armature Shape Key Scale",
        description="When using 'From Armature as Props' Shape Key animation export, scale applied to exported curves.\n\nCan be used to compensate for importers that expect values of 0-100 instead of 0-1",
		default=1.0,
	)
    
    # Proto Addition
    export_custom_property_animation: BoolProperty(
		name="Export Custom Prop Animation",
        description="Export animation of the Armature's Custom Properties as curve data",
		default=False,
	)
    
    # Proto Addition
    export_zeroed_custom_properties: BoolProperty(
		name="Include Zeroed Properties",
        description="When True, export Custom Property animation even if the property is zero for the entire animation. Otherwise, skip these properties",
		default=False,
	)
    
    # Proto Addition
    export_non_deform_custom_properties: BoolProperty(
		name="Include Non-Deform Bones",
        description="When True, export animation of Custom Properties on non-deforming bones (even if those bones are not exported)",
		default=False,
	)
    
    # Proto Addition
    export_armature_object_custom_properties: BoolProperty(
		name="Include Armature Object",
        description="When True, export animation of Custom Properties on the Armature Object itself.\n\nI.E. properties defined in the 'Object' panel",
		default=False,
	)
    
    # Proto Addition
    export_armature_data_custom_properties: BoolProperty(
		name="Include Armature Data",
        description="When True, export animation of Custom Properties on the Armature Data.\n\nI.E. properties defined in the 'Data' panel",
		default=False,
	)
    
    
    # Proto Addition
    dont_simplify_root_bone: BoolProperty(
		name="Don't Simplify Root Bone",
        description="Forces root bone location animation to skip simplification. Hack to help some FBX importers get the right frame count and framerate by having a track with keys on every frame.\n\nSpecifically works around an importer bug with Unreal Engine",
		default=True,
	)
    
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        # Are we inside the File browser
        is_file_browser = context.space_data.type == 'FILE_BROWSER'

        export_main(layout, self, is_file_browser)
        export_panel_conversions(layout, self)
        export_panel_include(layout, self, is_file_browser)
        export_panel_transform(layout, self)
        export_panel_geometry(layout, self)
        export_panel_armature(layout, self)
        export_panel_animation(context, layout, self)

    @property
    def check_extension(self):
        return True #self.batch_mode == 'OFF'

    def execute(self, context):
        from mathutils import Matrix
        settings = bpy.context.preferences.addons[addon_package_name].preferences
        
        print("\nPROTO FBX Exporter - beginnning export")
        start_time = time.time()
        
        # Verify filepath
        # * In one_file_per_action mode, turn it into a folder path
        if not self.filepath:
            raise Exception("filepath not set")
        
        # Validate filepath
        if self.filepath == "" or self.filepath == "/":
            self.report({'ERROR'}, "Invalid File Path")
            return {'CANCELLED'}
        
        if self.animation_export_mode == 'MultipleActions' and self.one_file_per_action:
            # We need a path that ends in a slash
            head, tail = os.path.split(self.filepath)
            if head == '':
                self.report({'ERROR'}, "Invalid Folder Path (One File Per Action mode) - Must specify a folder path")
                return {'CANCELLED'}
            self.filepath = head + "\\"
        else:
            # We need a file name
            if self.filepath[-1] == '/' or self.filepath[-1] == '\\':
                self.report({'ERROR'}, "Invalid File Path - Must specify a file name")
                return {'CANCELLED'}
            
            # Add .fbx suffix if missing
            split_filepath = self.filepath.split(".")
            if split_filepath[-1] != "fbx":
                self.filepath += ".fbx"
        
        # Global Matrix
        if self.use_space_transform:
            global_matrix = axis_conversion(to_forward=self.axis_forward, to_up=self.axis_up,).to_4x4()
        else:
            global_matrix = Matrix()
        
        keywords = self.as_keywords(ignore=("check_existing",
                                            "filter_glob",
                                            "ui_tab",
                                            ))

        keywords["global_matrix"] = global_matrix
        
        # Determine unit scale for export
        self.final_unit_scale = 1.0
        if keywords["bake_scale_mode"] == "Centimeters":
            self.final_unit_scale = 100.0
        if keywords["bake_scale_mode"] == "Inches":
            self.final_unit_scale = 39.37
        if keywords["bake_scale_mode"] == "Custom":
            self.final_unit_scale = keywords["bake_scale_custom"]
        
        # Cache selection at start of export
        self.original_selected_objects = bpy.context.selected_objects
        self.original_active_selection = bpy.context.view_layer.objects.active
        
        # Cache auto-keying state, disable
        self.original_keyframe_insert_auto = bpy.context.scene.tool_settings.use_keyframe_insert_auto
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
        
        self.saved_unit_settings = {}
        self.original_export_objects = [] # original objects in the scene to be exported
        self.final_export_objects = [] # list of (possibly duplicate or spawned) objects that will be sent to the export operator
        self.objects_to_duplicate = [] # list of original objects in the scene that need to be duplicated
        self.duplicate_objects = [] # duplicates created (ALL, including armatures)
        self.renamed_objects = {} # dictionary of renamed objects to original names
        self.scale_changed_actions = []
        self.fcurve_changed_actions = []
        self.actions_original_fcurves = []
        self.original_action_frame_ranges = {}
        self.original_armatures = []
        self.armatures = [] # stores duplicate armatures used in the export process
        self.armature_original_names = []
        self.actions = []
        self.helper_armatures = [] # extra armature duplicates that do not have transforms applied, that the final exported armature is contrained to
        self.helper_empties = [] # empty that helper_armatures are constrained to
        self.actions_skipped_missing_slot = []
        self.any_meshes_in_original_objects = False
        self.warnings = []
        try:
            #start_time = time.time()
            
            # switch to Object Mode
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except:
                pass
    
            
            # Get objects for export
            self.original_export_objects = get_export_objects(context, keywords["use_selection"], keywords["use_visible"], keywords["use_active_collection"], keywords["collection"], keywords["export_object_list"])
            
            # Verify objects are valid, get armatures, meshes
            if not self.original_export_objects:
                self.report({'ERROR'}, "no valid exportable objects found")
                return {'CANCELLED'}
            else:
                num_armatures = 0
                for ob in self.original_export_objects:
                    if ob.type == 'ARMATURE':
                        self.original_armatures.append(ob)
                        num_armatures += 1
                    if ob.type == 'MESH':
                        self.any_meshes_in_original_objects = True
                if num_armatures > 1:
                    self.report({'ERROR'}, "Multiple Armatures in export! Only 1 armatures is supported.")
                    return {'CANCELLED'}
            
            
            # store current scene unit settings
            for prop_name in dir(context.scene.unit_settings):
                if not (prop_name in ['bl_rna', 'rna_type'] or prop_name.startswith('__')):
                    self.saved_unit_settings[prop_name] = getattr(context.scene.unit_settings, prop_name)
            
            # -----------------------------------------------
            # Duplicate objects
            # * Including handling non-export dupes, and shapekey dummy objects
            # -----------------------------------------------
            export_objects_to_duplicate = self.original_export_objects
            export_objects_to_shapekey_dummy = []
            non_export_objects_to_duplicate = []
            if keywords["bake_anim"] and len(self.original_armatures) > 0 and (keywords["export_shapekey_animation"] or keywords["animation_force_dummy_mesh"]):
                armature_meshes = get_meshes_for_armatures(context, self.original_armatures) # Expensive operation (iterates all objects), minimize calls to it
                if len(armature_meshes) > 0:
                    if keywords["export_shapekey_animation"]:
                        shapekey_objects = get_shapekey_objects_to_duplicate_from_armature_meshes(context, armature_meshes, self.original_export_objects)
                        if keywords["shapekey_export_mode"] == 'ArmatureCustomProps':
                            non_export_objects_to_duplicate = shapekey_objects
                        elif keywords["shapekey_export_mode"] == 'ArmatureDummyMesh':
                            export_objects_to_shapekey_dummy = shapekey_objects
                    
                    # Should we force inclusion of a dummy mesh?
                    # (it's okay to treat this the same as a "shapekey" dummy even if it doesn't have shape keys)
                    if keywords["animation_force_dummy_mesh"] and len(export_objects_to_shapekey_dummy) == 0 and not self.any_meshes_in_original_objects:
                        # Just pick the first one (only need 1)
                        export_objects_to_shapekey_dummy.append(armature_meshes[0])
            
            self.objects_to_duplicate = list(self.original_export_objects + export_objects_to_shapekey_dummy + non_export_objects_to_duplicate)
            self.duplicate_objects, self.renamed_objects, self.armatures, self.armature_original_names, self.final_export_objects = duplicate_export_objects(self, context, export_objects_to_duplicate, export_objects_to_shapekey_dummy, non_export_objects_to_duplicate, keywords["armature_name"], keywords["export_object_list"])
            #print("Duplicated objects:")
            #for ob in self.duplicate_objects:
            #    print(ob.name)
            
            
            # -----------------------------------------------
            # Warn user if a mesh has animation data (only warn if exported with an armature)
            # -----------------------------------------------
            # Commented out, decided not to warn about this
            #if len(self.armatures) > 0:
            #    for ob in self.duplicate_objects:
            #        if ob.type == 'MESH' and ob.animation_data != None:
            #            self.warnings.append("Mesh '" + ob.name + "' has animation data! Can cause erroneous animations in FBX export, deleting Mesh animation data is recommended. Select Mesh and see Quick Action Select panel")
            
            
            # -----------------------------------------------
            # Get actions for this export
            # -----------------------------------------------
            if len(self.armatures) > 0 and keywords["bake_anim"] == True:
                if keywords["animation_export_mode"] == 'CurrentAction':
                    # We are only baking the current action
                    if self.armatures[0].animation_data == None:
                        self.report({'ERROR'}, "Tried to bake current action, but selected armature did not have animation data!")
                        return {'CANCELLED'}
                    if self.armatures[0].animation_data.action == None:
                        self.report({'ERROR'}, "Tried to bake current action, but selected armature did not have an active action!")
                        return {'CANCELLED'}
                    self.actions.append(self.armatures[0].animation_data.action)
                else:
                    # Bake all actions
                    filter_names = keywords["animation_export_mode"] == 'MultipleActions'
                    
                    # Action Whitelist / Filter
                    # * action_whitelist (sent by other Export UIs) takes top priority
                    # * if no action_whitelist, consider use_action_filter (manual export window)
                    # * NOTE: if action_whitelist is empty, it is ignored by get_actions_for_armature()
                    final_action_names_whitelist = list()
                    if len(keywords["action_whitelist"]) > 0:
                        # action whitelist passed from other export UIs
                        for entry in keywords["action_whitelist"]:
                            final_action_names_whitelist.append(entry.action_name)
                    else:
                        # no action_whitelist, consider use_action_filter
                        proto_exportfbx = context.scene.proto_exportfbx
                        if self.use_action_filter and len(proto_exportfbx.action_filter) > 0:
                            for entry in proto_exportfbx.action_filter:
                                if entry.action != None and entry.keep:
                                    final_action_names_whitelist.append(entry.action.name)
                    
                    self.actions = get_actions_for_armature(self.armatures[0], self.armature_original_names[0], do_armature_slot_name_filter=filter_names, action_names_whitelist=final_action_names_whitelist)
            
            elif len(self.armatures) > 0:
                # Not exporting actions, but it's possible we have a currently active action that could affect the export objects
                if self.armatures[0].animation_data != None and self.armatures[0].animation_data.action != None:
                    self.actions.append(self.armatures[0].animation_data.action)
            
                
            
            
            # -----------------------------------------------
            # Transform scene (baked-in unit scaling, rotation)
            # -----------------------------------------------
            if self.final_unit_scale != 1.0 or keywords["bake_z_forward"]:
                transform_export_objects(self, context, self.final_unit_scale, keywords["bake_z_forward"], self.remove_bone_rotation, keywords["move_to_origin"], keywords["skip_armature_object"], self.duplicate_objects, self.armatures, self.actions, self.helper_armatures, self.helper_empties, self.scale_changed_actions)
            
            
            # -----------------------------------------------
            # Initialize helper armatures (if we have any)
            # -----------------------------------------------
            if len(self.helper_armatures) > 0:
                # verify flat_bone_hierarchy_root
                if self.flat_bone_hierarchy and self.flat_bone_hierarchy_root != "":
                    if not self.flat_bone_hierarchy_root in self.armatures[0].data.bones:
                        self.report({'ERROR'}, "Running with Flat Bone Hierarchy, but specified Root Bone was not found in the armature!")
                        return {'CANCELLED'}
                
                init_helper_armatures(self, context, self.armatures, self.helper_armatures, self.remove_scale_from_bones, self.flat_bone_hierarchy, self.flat_bone_hierarchy_root, self.remove_bone_rotation, self.bake_z_forward)
            
            
            # -----------------------------------------------
            # Select Objects for export
            # -----------------------------------------------
            select_objects_for_export(context, self.final_export_objects)
            #print("final_export_objects:")
            #for ob in self.final_export_objects:
            #    print(ob.name)
            
            #end_time = time.time()
            #print("PROTO FBX Exporter - DEBUG TIMER - Scene Preparation took: ", end_time-start_time)
            #start_time = time.time()
            
            
            # -----------------------------------------------
            # Perform Export(s)
            # -----------------------------------------------
            if keywords["bake_anim"] == True and keywords["animation_export_mode"] == 'MultipleActions' and keywords["one_file_per_action"]:
                if len(self.actions) == 0:
                    self.report({'ERROR'}, "Running in one_file_per_action mode, but no action were found!")
                    return {'CANCELLED'}
                
                # We must have exactly 1 armature as part of this export
                if len(self.armatures) == 0:
                    self.report({'ERROR'}, "Running in one_file_per_action mode, but no armatures were present in exported objects!")
                    return {'CANCELLED'}
                if len(self.armatures) > 1:
                    self.report({'ERROR'}, "Running in one_file_per_action mode, but more than 1 armature was present in exported objects! Only 1 is supported.")
                    return {'CANCELLED'}
                
                # if using min_two_frames, we have to iterate actions and adjust their manual frame range
                # Assume 1 armature exported at a time
                if self.min_two_frames == True and len(self.armatures) > 0 and len(self.actions) > 0:
                    if len(self.armatures) > 1:
                        self.report({'ERROR'}, "Running with min_two_frames enabled, but more than 1 armature was present in exported objects! Only 1 is supported.")
                        return {'CANCELLED'}
                    apply_min_two_frames_to_actions(self.armatures[0], self.actions, self.original_action_frame_ranges)
                
                print("PROTO FBX Exporter - Beginning one-file-per-action exports")
                file_folder = self.filepath
                for action in self.actions:
                    
                    # Trigger FBX export for this action
                    # In One File Per Action mode, self.filepath should always be a folder path here
                    export_filepath = get_action_filepath(context, file_folder, action.name, keywords["action_name_style"], keywords["action_name_sharedname"])
                    self.filepath = export_filepath
                    
                    # Export "all actions" but filtered to current action
                    # This causes the Take to have a better name in the export (instead of just "Scene")
                    keywords["bake_anim_use_nla_strips"] = False
                    keywords["bake_anim_use_all_actions"] = True
                    keywords["bake_anim_use_action_filter"] = True
                    keywords["bake_anim_action_filter"] = [action]
                    
                    keywords["export_mesh_shapekey_animation"] = keywords["bake_anim"] and keywords["export_shapekey_animation"] and (keywords["shapekey_export_mode"] == 'ArmatureDummyMesh' or keywords["shapekey_export_mode"] == 'Mesh')
                    keywords["skip_meshes_if_no_shapekey_animation"] = (not self.any_meshes_in_original_objects and not keywords["animation_force_dummy_mesh"]) and keywords["export_mesh_shapekey_animation"] and keywords["shapekey_export_mode"] == 'ArmatureDummyMesh'
                    keywords["export_armature_shapekey_animation"] = keywords["bake_anim"] and keywords["export_shapekey_animation"] and keywords["shapekey_export_mode"] == 'ArmatureCustomProps'
                    if len(self.helper_armatures) > 0:
                        keywords["helper_armatures"] = {}
                        for i, helper_armature in enumerate(self.helper_armatures):
                            keywords["helper_armatures"][self.armatures[i]] = helper_armature
                    do_fbx_export(self, context, self.filepath, keywords)
                
            else:
                # if using min_two_frames, we have to iterate actions and adjust their manual frame range
                # Assume 1 armature exported at a time
                if self.min_two_frames == True and len(self.armatures) > 0 and len(self.actions) > 0:
                    if len(self.armatures) > 1:
                        self.report({'ERROR'}, "Running with min_two_frames enabled, but more than 1 armature was present in exported objects! Only 1 is supported.")
                        return {'CANCELLED'}
                    apply_min_two_frames_to_actions(self.armatures[0], self.actions, self.original_action_frame_ranges)
                
                # Trigger FBX export of selected objects
                if keywords["animation_export_mode"] == 'Scene':
                    keywords["bake_anim_use_nla_strips"] = False
                    keywords["bake_anim_use_all_actions"] = False
                elif keywords["animation_export_mode"] == 'CurrentAction':
                    # Export "all actions" but filtered to current action
                    # This causes the Take to have a better name in the export (instead of just "Scene")
                    keywords["bake_anim_use_nla_strips"] = False
                    if len(self.armatures) > 0 and self.armatures[0].animation_data != None and self.armatures[0].animation_data.action != None:
                        keywords["bake_anim_use_all_actions"] = True
                        keywords["bake_anim_use_action_filter"] = True
                        keywords["bake_anim_action_filter"] = [self.armatures[0].animation_data.action]
                elif keywords["animation_export_mode"] == 'MultipleActions':
                    keywords["bake_anim_use_nla_strips"] = False
                    keywords["bake_anim_use_all_actions"] = True
                    keywords["bake_anim_use_action_filter"] = True
                    keywords["bake_anim_action_filter"] = self.actions
                elif keywords["animation_export_mode"] == 'NLAStrips':
                    keywords["bake_anim_use_nla_strips"] = True
                    keywords["bake_anim_use_all_actions"] = False
                    
                keywords["export_mesh_shapekey_animation"] = keywords["bake_anim"] and keywords["export_shapekey_animation"] and (keywords["shapekey_export_mode"] == 'ArmatureDummyMesh' or keywords["shapekey_export_mode"] == 'Mesh')
                keywords["skip_meshes_if_no_shapekey_animation"] = (not self.any_meshes_in_original_objects and not keywords["animation_force_dummy_mesh"]) and keywords["export_mesh_shapekey_animation"] and keywords["shapekey_export_mode"] == 'ArmatureDummyMesh'
                keywords["export_armature_shapekey_animation"] = keywords["bake_anim"] and keywords["export_shapekey_animation"] and keywords["shapekey_export_mode"] == 'ArmatureCustomProps'
                if len(self.helper_armatures) > 0:
                        keywords["helper_armatures"] = {}
                        for i, helper_armature in enumerate(self.helper_armatures):
                            keywords["helper_armatures"][self.armatures[i]] = helper_armature
                
                do_fbx_export(self, context, self.filepath, keywords)
            #end_time = time.time()
            #print("PROTO FBX Exporter - DEBUG TIMER - internal export took: ", end_time-start_time)
            
        finally:
            # Clean up duplicates and modifications to scene
            cleanup_scene(context, self.final_unit_scale, keywords["bake_z_forward"], self.saved_unit_settings, self.objects_to_duplicate, self.duplicate_objects, self.renamed_objects, self.scale_changed_actions, self.original_action_frame_ranges, self.fcurve_changed_actions, self.actions_original_fcurves, self.helper_armatures, self.helper_empties)
            
            # Re-select objects from the start of the export
            bpy.ops.object.select_all(action='DESELECT')
            for ob in self.original_selected_objects:
                ob.select_set(state=True)
            bpy.context.view_layer.objects.active = self.original_active_selection
        
        # restore auto-keying state
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = self.original_keyframe_insert_auto
        
        # Warn users if any meshes had shapekeys, and we exported with modifiers applied
        if self.use_mesh_modifiers:
            found_shapekeys_with_mods = False
            for ob in self.original_export_objects:
                if ob.type == 'MESH' and ob.data.shape_keys != None:
                    found_non_arm_mod = False
                    for modifier in ob.modifiers:
                        if modifier.type != "ARMATURE":
                            found_non_arm_mod = True
                    if found_non_arm_mod:
                        found_shapekeys_with_mods = True
                        break
            if found_shapekeys_with_mods:
                self.warnings.append("Shapekeys may not have exported! Applying Modifiers prevents shapekey export")
        
        # Warn users if we skipped any actions due to not having a valid slot
        if bpy.app.version >= (4, 4, 0) and len(self.actions_skipped_missing_slot) > 0:
            msg = ""
            if settings.action_slot_behavior == 'ARMATURE_NAME':
                msg = "The following actions did not have a slot matching the name of the exported armature and were skipped:\n"
            else:
                msg = "The following actions could not auto-select a valid action slot and were skipped:\n"
            for action_name in self.actions_skipped_missing_slot:
                msg = msg + "- " + action_name + "\n"
            self.warnings.append(msg)
        
        # Display warnings
        if len(self.warnings) > 0:
            final_str = ""
            final_str += self.warnings[0]
            for warning in self.warnings[1:]:
                final_str += "\n" + warning
            
            # Display popup to user
            warnings_title = "Warnings"
            if self.export_name != "":
                warnings_title = self.export_name + " - Warnings"
            bpy.ops.prototools.infopopup('INVOKE_DEFAULT', title=warnings_title, text=final_str, icon='ERROR')
            
            # Multi-entry version
            #warning_entries = []
            #entry = dict()
            #entry["name"] = "First Entry"
            #entry["header"] = "Export Warnings"
            #entry["text"] = final_str
            #entry["icon"] = "ERROR"
            #warning_entries.append(entry)
            #bpy.ops.prototools.infopopuparray('INVOKE_DEFAULT', title="Warnings", entries=warning_entries)
            
            # Print warnings to console
            print("\n-------------------------------\nPROTO FBX Exporter - Warnings:\n-------------------------------\n" + final_str)
        
        print("\nPROTO FBX Exporter - export successful")
        print('export finished in %.4f sec.' % (time.time() - start_time))
        return {'FINISHED'}


def export_main(layout, operator, is_file_browser):
    row = layout.row(align=True)
    row.prop(operator, "path_mode")
    sub = row.row(align=True)
    sub.enabled = (operator.path_mode == 'COPY')
    sub.prop(operator, "embed_textures", text="", icon='PACKAGE' if operator.embed_textures else 'UGLYPACKAGE')
    # PROTO: BATCH MODE NOT SUPPORTED
    #if is_file_browser:
    #    row = layout.row(align=True)
    #    row.prop(operator, "batch_mode")
    #    sub = row.row(align=True)
    #    sub.prop(operator, "use_batch_own_dir", text="", icon='NEWFOLDER')


def export_panel_conversions(layout, operator):
    header, body = layout.panel("FBX_export_proto", default_closed=False)
    header.label(text="Conversions")
    if body:
        body.prop(operator, "bake_scale_mode")
        if operator.bake_scale_mode == "Custom":
            body.prop(operator, "bake_scale_custom")
        body.prop(operator, "bake_z_forward")
        body.prop(operator, "skip_armature_object")
        if operator.skip_armature_object == False:
            body.prop(operator, "armature_name")
        body.prop(operator, "move_to_origin")
        body.separator()
        body.prop(operator, "remove_scale_from_bones")
        body.prop(operator, "remove_bone_rotation")
        body.prop(operator, "flat_bone_hierarchy")


def export_panel_include(layout, operator, is_file_browser):
    header, body = layout.panel("FBX_export_include", default_closed=False)
    header.label(text="Include")
    if body:
        sublayout = body.column(heading="Limit to")
        #sublayout.enabled = (operator.batch_mode == 'OFF')
        if is_file_browser:
            sublayout.prop(operator, "use_selection")
            sublayout.prop(operator, "use_visible")
            sublayout.prop(operator, "use_active_collection")

        body.column().prop(operator, "object_types")
        body.prop(operator, "use_custom_props")


def export_panel_transform(layout, operator):
    header, body = layout.panel("FBX_export_transform", default_closed=True)
    header.label(text="Transform")
    if body:
        body.prop(operator, "global_scale")
        body.prop(operator, "apply_scale_options")

        body.prop(operator, "axis_forward")
        body.prop(operator, "axis_up")

        body.prop(operator, "apply_unit_scale")
        body.prop(operator, "use_space_transform")
        row = body.row()
        row.prop(operator, "bake_space_transform")
        row.label(text="", icon='ERROR')
        
        
def export_panel_geometry(layout, operator):
    header, body = layout.panel("FBX_export_geometry", default_closed=True)
    header.label(text="Geometry")
    if body:
        body.prop(operator, "mesh_smooth_type")
        body.prop(operator, "use_subsurf")
        body.prop(operator, "use_mesh_modifiers")
        #sub = body.row()
        # sub.enabled = operator.use_mesh_modifiers and False  # disabled in 2.8...
        #sub.prop(operator, "use_mesh_modifiers_render")
        body.prop(operator, "use_mesh_edges")
        body.prop(operator, "use_triangles")
        sub = body.row()
        # ~ sub.enabled = operator.mesh_smooth_type in {'OFF'}
        sub.prop(operator, "use_tspace")
        body.prop(operator, "colors_type")
        body.prop(operator, "prioritize_active_color")


def export_panel_armature(layout, operator):
    header, body = layout.panel("FBX_export_armature", default_closed=True)
    header.label(text="Armature")
    if body:
        body.prop(operator, "primary_bone_axis")
        body.prop(operator, "secondary_bone_axis")
        body.prop(operator, "armature_nodetype")
        body.prop(operator, "use_armature_deform_only")
        body.prop(operator, "add_leaf_bones")


def export_panel_animation(context, layout, operator):
    header, body = layout.panel("FBX_export_bake_animation", default_closed=True)
    header.use_property_split = False
    header.prop(operator, "bake_anim", text="")
    header.label(text="Animation")
    if body:
        body.enabled = operator.bake_anim
        #body.prop(operator, "bake_anim_use_nla_strips")
        #body.prop(operator, "bake_anim_use_all_actions")
        body.prop(operator, "animation_export_mode")
        if operator.animation_export_mode == 'MultipleActions':
            body.prop(operator, "one_file_per_action")
            if operator.one_file_per_action:
                body.prop(operator, "action_name_style")
                body.prop(operator, "action_name_sharedname")
        body.prop(operator, "animation_force_dummy_mesh")
        
        # action_filter
        if operator.animation_export_mode == 'MultipleActions':
            col = body.column()
            col.use_property_split = False
            top_row = col.row()
            top_row.label(text="", icon="ACTION")
            top_row.prop(operator, "use_action_filter")
            if operator.use_action_filter == True:
                proto_exportfbx = context.scene.proto_exportfbx
                row = col.row()
                row.template_list(
                    "PROTOTOOLS_UL_Export_Quick_Options_ActionList",
                    "proto_quick_export_action_list",
                    proto_exportfbx,
                    "action_filter",
                    proto_exportfbx,
                    "action_filter_index",
                    rows=4
                )
                
                side_bar = row.column(align=True)
                op = side_bar.operator("proto_export_scene.refresh_actionlist", icon="FILE_REFRESH", text="")
        
        export_panel_animation_shapekeys(body, operator)
        export_panel_animation_customproperties(body, operator)
        export_panel_animation_advanced(body, operator)

#export_shapekey_animation
def export_panel_animation_shapekeys(layout, operator):
    header, body = layout.panel("FBX_export_bake_animation_shapekeys", default_closed=True)
    header.use_property_split = False
    header.prop(operator, "export_shapekey_animation", text="")
    header.label(text="Shape Key Animation")
    if body:
        body.enabled = operator.export_shapekey_animation
        body.prop(operator, "shapekey_export_mode")
        
        col = body.column(heading="Include")
        col.prop(operator, "export_zeroed_shapekeys")
        
        sub = body.column()
        if operator.shapekey_export_mode == 'ArmatureCustomProps':
            sub.prop(operator, "armature_shapekey_scale")


def export_panel_animation_customproperties(layout, operator):
    header, body = layout.panel("FBX_export_bake_animation_customproperties", default_closed=True)
    header.use_property_split = False
    header.prop(operator, "export_custom_property_animation", text="")
    header.label(text="Custom Property Animation")
    if body:
        body.enabled = operator.export_custom_property_animation
        col = body.column(heading="Include")
        col.prop(operator, "export_zeroed_custom_properties")
        col.prop(operator, "export_non_deform_custom_properties")
        col.prop(operator, "export_armature_object_custom_properties")
        col.prop(operator, "export_armature_data_custom_properties")


def export_panel_animation_advanced(layout, operator):
    header, body = layout.panel("FBX_export_bake_animation_advanced", default_closed=True)
    header.label(text="Advanced")
    if body:
        body.prop(operator, "bake_anim_use_all_bones")
        body.prop(operator, "bake_anim_force_startend_keying")
        body.prop(operator, "bake_anim_step")
        body.prop(operator, "bake_anim_simplify_factor")
        body.prop(operator, "dont_simplify_root_bone")


def menu_func_export(self, context):
    self.layout.operator(ProtoExportFBX.bl_idname, text="PROTO FBX (.fbx)")


def register():
    bpy.utils.register_class(ProtoExportFBX_ExportListEntry)
    bpy.utils.register_class(ProtoExportFBX_RefreshActionList)
    bpy.utils.register_class(ProtoExportFBX_ActionFilterEntry)
    bpy.utils.register_class(ProtoExportFBX_ActionFilterProperties)
    bpy.utils.register_class(ProtoExportFBX_ActionWhitelistEntry)
    bpy.utils.register_class(ProtoExportFBX)
    
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    
    bpy.types.Scene.proto_exportfbx = bpy.props.PointerProperty(type=ProtoExportFBX_ActionFilterProperties)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(ProtoExportFBX)
    bpy.utils.unregister_class(ProtoExportFBX_ActionWhitelistEntry)
    bpy.utils.unregister_class(ProtoExportFBX_ActionFilterProperties)
    bpy.utils.unregister_class(ProtoExportFBX_ActionFilterEntry)
    bpy.utils.unregister_class(ProtoExportFBX_RefreshActionList)
    bpy.utils.unregister_class(ProtoExportFBX_ExportListEntry)
    
    del bpy.types.Scene.proto_exportfbx


if __name__ == "__main__":
    register()


