# PROTO Tools UI Panels
# 2026 PROTOWLF, Licensed under GPL-3.0

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
    IntProperty,
    CollectionProperty,
    PointerProperty,
)
from .fbx_export import proto_fbx_utils




def on_use_action_filter_changed(self, context):
    if self.use_action_filter is True:
        proto_fbx_utils.refresh_action_filter(self.action_filter)


def on_batch_export_item_mode_changed(self, context):
    if self.batch_export_item_mode == "ModelAndAnimations":
        self.export_properties.export_mode = "Combined"
    else:
        self.export_properties.export_mode = "Separate"


class ActionExport(bpy.types.PropertyGroup):
    def copy_from(self, old):
        self.action = old.action
        self.export_filepath = old.export_filepath
    
    action: PointerProperty(type=bpy.types.Action)
    export_filepath: StringProperty()


class QuickExportActionFilterEntry(bpy.types.PropertyGroup):
    def copy_from(self, old):
        self.action = old.action
        self.keep = old.keep
    
    action: bpy.props.PointerProperty(type=bpy.types.Action)
    keep: bpy.props.BoolProperty(name="Include in exports")


# Single Object chosen to be part of a single batch Export Item
class ExportItemObjectPointer(bpy.types.PropertyGroup):
    
    def copy_from(self, old):
        self.pointer = old.pointer
        self.rename_name = old.rename_name
    
    pointer: bpy.props.PointerProperty(
        name="Object",
        type=bpy.types.Object,
        #poll=export_object_filter,
    )
    
    rename_name: StringProperty(
        name="Rename",
        description="(optional) Rename Object to this name when exported (ignored if blank).\n\nTIP: if the mesh animated in Blender is not the same one exported to game engines, Shape Key animation may break due to non-matching Mesh names. Use this to keep a matching name",
        default=""
    )


# Properties for A single Quick Export item
class ProtoToolsQuickExport_SingleExportProperties(bpy.types.PropertyGroup):
    
    def copy_from(self, old):
        self.copy_output_settings(old)
        self.copy_options(old)
    
    def copy_output_settings(self, old):
        self.export_mode = old.export_mode
        self.model_path = old.model_path
        self.anim_folder_path = old.anim_folder_path
        self.all_anims_path = old.all_anims_path
        self.one_file_per_action = old.one_file_per_action
    
    def copy_options(self, old):
        self.scene_conversion_mode = old.scene_conversion_mode
        self.bake_scale_mode = old.bake_scale_mode
        self.bake_scale_custom = old.bake_scale_custom
        self.scene_rotation_mode = old.scene_rotation_mode
        self.armature_name = old.armature_name
        self.skip_armature_object = old.skip_armature_object
        self.move_to_origin = old.move_to_origin
        self.apply_modifiers = old.apply_modifiers
        self.action_name_style = old.action_name_style
        self.action_name_sharedname = old.action_name_sharedname
        self.animation_force_dummy_mesh = old.animation_force_dummy_mesh
        self.use_action_filter = old.use_action_filter
        
        self.action_filter.clear()
        for other_entry in old.action_filter:
            self.action_filter.add()
            self.action_filter[len(self.action_filter)-1].copy_from(other_entry)
        
        self.action_filter_index = old.action_filter_index
        self.min_two_frames = old.min_two_frames
        self.remove_scale_from_bones = old.remove_scale_from_bones
        self.remove_bone_rotation = old.remove_bone_rotation
        self.flat_bone_hierarchy = old.flat_bone_hierarchy
        self.flat_bone_hierarchy_root = old.flat_bone_hierarchy_root
        self.bake_anim_simplify_factor = old.bake_anim_simplify_factor
        self.dont_simplify_root_bone = old.dont_simplify_root_bone
        self.export_shapekey_animation = old.export_shapekey_animation
        self.shapekey_export_mode = old.shapekey_export_mode
        self.armature_shapekey_scale = old.armature_shapekey_scale
        self.export_zeroed_shapekeys = old.export_zeroed_shapekeys
        self.export_custom_property_animation = old.export_custom_property_animation
        self.export_zeroed_custom_properties = old.export_zeroed_custom_properties
        self.export_non_deform_custom_properties = old.export_non_deform_custom_properties
        self.export_armature_object_custom_properties = old.export_armature_object_custom_properties
        self.export_armature_data_custom_properties = old.export_armature_data_custom_properties
    
    
    # ----------------------------------------------
    # OUTPUT SETTINGS
    # ----------------------------------------------
    
    export_mode: EnumProperty(
        name="Mode",
        description="Export Mode",
        options=set(),
        items=(('Combined', "Model + Animations (1 File)", "Export Mesh, Armature, and Animations all in one FBX file"),
               ('Separate', "Separate Animations", "Export Mesh and Armature in one file, and Animations in separate files"),
               ),
        default='Combined',
    )
    
    batch_export_item_index: IntProperty(
        name="Batch Export Item Index",
        description="(internal) if these properties are associated with a Batch Export Item, the index for that item. If -1, not Batch Export Item properties",
        default=-1,
        options={'HIDDEN'}
    )
    
    model_path: StringProperty(
		name="Path",
        description="Where to save the exported Model FBX",
        options=set(),
		subtype="FILE_PATH",
		default="/",
	)
    
    anim_folder_path: StringProperty(
		name="Folder",
        description="Folder to save the exported Anim FBX file in. The exported file(s) will be named after Action name(s)",
        options=set(),
		subtype="DIR_PATH",
		default="/",
	)
    
    all_anims_path: StringProperty(
		name="Path",
        description="Where save the exported Animation FBX file",
        options=set(),
		subtype="FILE_PATH",
		default="/",
	)
    
    one_file_per_action: BoolProperty(
		name="1 File Per Action",
        description="When exporting all Actions, save each action to its own FBX file. Each file will be named after the Action's name",
        options=set(),
		default=True,
	)
    
    
    # ----------------------------------------------
    # OPTIONS
    # ----------------------------------------------
    
    scene_conversion_mode: EnumProperty(
        name="Scene Conversion",
        description="How to scale/rotate the exported scene, and how to export the Armature object",
        options=set(),
        items=(('Unreal', "Unreal", "Convert scene for Unreal Engine.\n* Scaled to centimeters\n* Armature object is exported but renamed to 'Armature', which causes Unreal to exclude it from the imported Skeleton."),
               ('UnityGodot', "Unity, Godot", "Convert scene for Unity and Godot Engine.\n* Scaled to centimers, rotated to Z-forward.\n* Armature object removed from export.\n\nNOTE: Unity and Godot use meters, but this conversion avoids these engines applying 100x scale to imported objects"),
               ('Custom', "Custom", "Set scene conversion options to manually"),
               ),
        default='UnityGodot',
    )
    
    bake_scale_mode: EnumProperty(
        name="Scene Scale",
        description="Bake in a conversion from Blender's default units (meters) to a different length unit. Use this when exporting for apps that don't handle unit conversions well on-import",
        options=set(),
        items=(('None', "None", "Do not bake a unit conversion"),
               ('Centimeters', "Centimeters (Unreal, Unity, Godot)", "Bake a unit conversion to centimeters.\n\nRecommended for: Unreal, Unity, Godot\nNOTE: Unity and Godot use meters, but expect cenimters in FBX, or they will apply 100x scale to imported objects"),
               ('Inches', "Inches (Source)", "Bake a unit conversion to inches.\n\nRecommended for: Source, Source 2"),
               ('Custom', "Custom", "Bake a custom conversion. Enter a multiplier to apply to meters (e.g. 100 for centimeters, 39.37 for inches)"),
               ),
        default='Centimeters',
    )
    
    bake_scale_custom: FloatProperty(
        name="Custom Scale",
        description="A custom unit conversion. Enter a multiplier to apply to meters (e.g. 100 for centimeters, 39.37 for inches)",
        options=set(),
        min=0.0001, max=10000.0,
        soft_min=0.0001, soft_max=10000.0,
        default=1.0,
    )
    
    scene_rotation_mode: EnumProperty(
        name="Scene Rotation",
        description="How to export rotation in the scene, to target different game engines",
        items=(('None', "None", "Do not bake any rotation into the scene, and export with default options\n\nRecommended for: Unreal (if *not* using 'Skip Armature Object')"),
               ('BakeZForward', "Z Forward (Unity, Godot)", "Bake-in rotation to make the scene Z-forward, Y-Up, X-Left, matching Maya's coordinate system.\n\nRecommended for: Unity, Godot"),
               ),
        default='None',
    )
    
    armature_name: StringProperty(
        name="Rename Armature",
        description="Blender exports the Armature object itself as node above the root bone. You may rename it, or leave blank to use the existing name.\n\nTIP: Unreal will import this node as a bone in the skeleton, but will strip it out if it is named 'Armature'; if you set this to 'Armature', this will cause Unreal to use the first bone as the root when imported",
        options=set(),
        default="Armature",
    )
    
    skip_armature_object: BoolProperty(
        name="Skip Armature Object",
        description="By default, Blender exports the Armature object itself above the root bone. This is generally not desireable. If True, this option will remove it from the export.\n\nRecommended for: Unity, Godot.\n\nNOTE: If used without Scene Rotation 'Z Forward', may result in a rotated export.\n\nNOTE: Not recommended for Unreal, instead rename the Armature to 'Armature' to cause Unreal to remove it on-import",
        default=False,
    )
    
    move_to_origin: BoolProperty(
        name="Move To Origin",
        description="Move Object(s) to world origin before exporting, removing world offset from exported Model.\n\nNOTE: parented Objects are moved together. If you have multiple un-parented Objects in export, ensure that they have the same origin",
        default=False,
    )
    
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers to mesh objects (except Armature ones) - WARNING: prevents exporting shape keys.\n\nNOTE: Only affects model exports -- animation exports will never apply modifiers",
        options=set(),
        default=False
    )
    
    action_name_style: EnumProperty(
		name="Action File Names",
        description="When exporting Actions as FBX animations, the format to use for their file names",
        options=set(),
		items=(('Action', "Action", "Actions FBX files are saved as just their name:\nActionName.fbx"),
               ('Name_Action', "Name_Action", "Actions FBX files are saved with a shared name with _ActionName:\nSharedName_ActionName.fbx"),
               ('Name-Action', "Name-Action", "Actions FBX files are saved with a shared name with -ActionName:\nSharedName-ActionName.fbx"),
               ('Name@Action', "Name@Action", "Actions FBX files are saved with a shared name with @ActionName:\nSharedName@ActionName.fbx"),
               ),
        default='Action',
	)
    
    action_name_sharedname: StringProperty(
		name="Shared Name",
        description="When exporting Actions as FBX animations, shared name that will be combined with the Action Name to make a file name",
        options=set(),
		default=""
	)
    
    animation_force_dummy_mesh: BoolProperty(
        name="Anims Dummy Mesh (Unity)",
        description="If true, animation FBX files will always have a dummy Mesh inserted.\n\nThis is a workaround for Unity's FBX importer; when FBX files only contain animation, Unity's importer requires its 'Preserve Hierarchy' option to be enabled, or else it will import incorrectly. By inserting a dummy Mesh, animation FBX files will import correctly in Unity by-default.\n\nRecommended for: Unity",
        default=False
    )
    
    use_action_filter: BoolProperty(
        name="Enable Action Filter",
        description="Limit which Actions are considered for export",
        default=False,
        update=on_use_action_filter_changed,
    )
    
    action_filter: CollectionProperty(
        name="Action Filter",
        description="Select Actions considered for export",
        type=QuickExportActionFilterEntry,
    )
    
    action_filter_index: IntProperty(
        name="Action Index",
        description="Index of currently selected Action in the Action Filter list",
        default=0
    )
    
    min_two_frames: BoolProperty(
        name="Minimum 2 Frames",
        description="When exporting Actions, force frame range to be at least 2 frames long.\n\nAvoids a Blender FBX export bug where no keys are exported for 1 frame animations. Recommended to always leave this enabled",
        options=set(),
        default=True,
    )
    
    remove_scale_from_bones: BoolProperty(
        name="Remove Scale from Bones",
        description="When exporting armatures and actions, remove all scaling from bones.\n\nTIP: if you see innacurate animations after export, it is often the result of scaled bones. This option can be used to work around rigs that producing scaled bones",
        options=set(),
        default=False,
    )
    
    remove_bone_rotation: BoolProperty(
        name="Remove Rotation from Bones",
        description="Remove all bone rotation from bind pose, making each bone have (0,0,0) rotation (in Blender's coordinate system)",
        default=False,
    )
    
    flat_bone_hierarchy: BoolProperty(
        name="Flat Bone Hierarchy",
        description="When exporting armatures and actions, set all bones' parents to the given root bone.\n\nTIP: Useful if you want to do squash/stretch bone scaling in a game engine. A flat hierarchy avoids distorted transforms resulting from scaled bone chains, but is not recommended under normal circumstances",
        options=set(),
        default=False,
    )
    
    flat_bone_hierarchy_root: StringProperty(
        name="Root Bone Name",
        description="When using Flat Bone Hierarchy, name of the bone to treat as the root.\nLeave blank to make all bones have no parent (making the Armature itself the root)",
        options=set(),
        default="",
    )
    
    bake_anim_simplify_factor: FloatProperty(
        name="Simplify",
        description="How much to compress animation data (0.0 = best accuracy, largest file size. Higher numbers = less accuracy, smaller file size).\nGenerally leave at default of 0.1. Try setting to 0.0 if you see innacuracy in exported animation.\n\n(NOTE: innacurate animation is often the result of scaled bones, not the Simplify setting)",
        options=set(),
        min=0.0, max=100.0,
        soft_min=0.0, soft_max=10.0,
        default=0.1,
    )
    
    dont_simplify_root_bone: BoolProperty(
		name="Don't Simplify Root Bone",
        description="Forces root bone location animation to skip simplification. Hack to help some FBX importers get the right frame count and framerate by having a track with keys on every frame.\n\nSpecifically works around an importer bug with Unreal Engine",
        options=set(),
		default=True,
	)
    
    
    export_shapekey_animation: BoolProperty(
		name="Shape Key Animation",
        description="Export animation of Shape Keys",
        options=set(),
		default=True,
	)
    
    shapekey_export_mode: EnumProperty(
        name="Shape Key Anim Mode",
        items=(('ArmatureCustomProps', "Custom Props (Unreal)", "When exporting an Armature with animation, Shape Key animation of deformed Meshes is detected and converted to Custom Property curves on the Armature root bone.\n\nRecommended for: Unreal.\nNote: Unity can import these curves, but will not automatically apply them to Blendshape animation"),
               ('ArmatureDummyMesh', "Dummy Mesh (Unity, Godot)", "When exporting an Armature with animation, Shape Key animation of deformed Meshes is detected and converted to Shape Key curves on a dummy mesh. Allows for real FBX blendshape curves while keeping filesize down.\n\nRecommended for: Unity, Godot"),
               ),
        options=set(),
        default='ArmatureCustomProps',
    )
    
    armature_shapekey_scale: FloatProperty(
		name="Shape Key Custom Prop Scale",
        description="Multiplier applied to Shape Key curves exported as Custom Property curves.\n\nCan be used to compensate for importers that expect values of 0-100 instead of 0-1\n\nOnly used when 'Shape Key Anim Mode' is set to 'Custom Properties'",
        options=set(),
		default=1.0,
	)
    
    export_zeroed_shapekeys: BoolProperty(
		name="Zeroed Shape Keys",
        description="When True, export Shape Key animation even if a Shape Key is zero for the entire Action. Otherwise, skip these Shape Keys",
        options=set(),
		default=False,
	)
    
    
    export_custom_property_animation: BoolProperty(
		name="Custom Property Animation",
        description="Export animation of the Armature's (and Bones') Custom Properties.\n\nNOTE: game engine FBX importers may not import custom property curves by default, and may have optional settings to do-so",
        options=set(),
		default=False,
	)
    
    export_zeroed_custom_properties: BoolProperty(
		name="Zeroed Properties",
        description="When True, export Custom Property animation even if the property is zero for the entire Action. Otherwise, skip these properties",
        options=set(),
		default=False,
	)
    
    export_non_deform_custom_properties: BoolProperty(
		name="Non-Deform Bones",
        description="When True, export animation of Custom Properties on non-deform bones (even if those bones are not exported)",
        options=set(),
		default=False,
	)
    
    export_armature_object_custom_properties: BoolProperty(
		name="Armature Object",
        description="When True, export animation of Custom Properties on the Armature Object itself.\n\nI.E. properties defined in the 'Object' panel",
        options=set(),
		default=False,
	)
    
    export_armature_data_custom_properties: BoolProperty(
		name="Armature Data",
        description="When True, export animation of Custom Properties on the Armature Data.\n\nI.E. properties defined in the 'Data' panel",
        options=set(),
		default=False,
	)


# Properties a single batch Export Item
class ProtoToolsQuickExport_ExportItemProperties(bpy.types.PropertyGroup):

    def copy_from(self, old):
        self.multi_selected = old.multi_selected
        self.name = old.name
        self.batch_export_item_mode = old.batch_export_item_mode
        self.export_objects.clear()
        for other_export_object in old.export_objects:
            self.export_objects.add()
            self.export_objects[len(self.export_objects)-1].copy_from(other_export_object)
        self.export_objects_index = old.export_objects_index
        self.export_properties.copy_from(old.export_properties)
    
    # Selection (for multi-selection in Export Item list)
    multi_selected: BoolProperty(
        name="Select for Export",
        description="Check multiple Export Items to export multiple at once",
        options=set(),
        default=False
    )
    
    name: StringProperty(
        name="Name",
        default="Untitled Export",
        options=set(),
    )
    
    batch_export_item_mode: EnumProperty(
        name="Export Mode",
        description="How this Export Item exports",
        options=set(),
        items=(('ModelAndAnimations', "Model + Animations (1 File)", "Export Mesh, Armature, and Animations all in 1 file"),
               ('Model', "Model", "Export Mesh and Armature in 1 file"),
               ('Animations', "Animations", "Export Animations, in 1 file or 1 file-per-action"),
               ),
        default='ModelAndAnimations',
        update=on_batch_export_item_mode_changed
    )
    
    export_objects: CollectionProperty(
        name="Export Objects",
        description="Objects that will be included in this export.\n\nA maximum of 1 Armature is allowed",
        options=set(),
        type=ExportItemObjectPointer
    )
    
    export_objects_index: IntProperty(
        name="Export Object",
        options=set(),
        default=0,
    )
    
    export_properties: PointerProperty(
        name="Export Properties",
        type=ProtoToolsQuickExport_SingleExportProperties,
        options=set(),
    )


# Properties for All Quick Export features
class ProtoToolsQuickExport_Properties(bpy.types.PropertyGroup):

    def copy_from(self, old):
        self.quick_export_mode = old.quick_export_mode
        self.export_selected_properties.copy_from(old.export_selected_properties)
        self.clipboard_export_properties.copy_from(old.clipboard_export_properties)
        self.clipboard_export_properties_copied = old.clipboard_export_properties_copied
        self.batch_export_items.clear()
        for other_batch_export_item in old.batch_export_items:
            self.batch_export_items.add()
            self.batch_export_items[len(self.batch_export_items)-1].copy_from(other_batch_export_item)
        self.batch_export_items_index = old.batch_export_items_index
    
    
    quick_export_mode: EnumProperty(
        name="Quick Export Mode",
        description="Select whether to do single exports of selected objects, or pre-defined batch exports",
        options=set(),
        items=(('ExportSelected', "Export Selected", "Export current selection with 1 set of options"),
               ('BatchExport', "Batch Export", "Pre-define multiple exports, export multiple in one click"),
               ),
        default='ExportSelected',
    )
    
    export_selected_properties: PointerProperty(
        name="Export-Selected Properties",
        type=ProtoToolsQuickExport_SingleExportProperties,
        options=set(),
    )
    
    clipboard_export_properties: PointerProperty(
        name="Export-Selected Properties",
        description="Export Options that the user has copied to later paste",
        type=ProtoToolsQuickExport_SingleExportProperties,
        options={'HIDDEN'},
    )
    
    clipboard_export_properties_copied: BoolProperty(
        name="Are Export Properties Copied",
        description="Tracks if any export properties have been copied. Resets on file load",
        options={'HIDDEN', 'SKIP_SAVE'},
        default=False,
    )
    
    batch_export_items: CollectionProperty(
        name="Batch Export Items",
        description="List of Batch Export Items defined by user in the UI",
        type=ProtoToolsQuickExport_ExportItemProperties,
        options=set(),
    )
    
    batch_export_items_index: IntProperty(
        name="Batch Export Item",
        options=set(),
        default=0
    )


# Properties for Quick Action Select
class ProtoToolsActionSelectProperties(bpy.types.PropertyGroup):

    def copy_from(self, old):
        self.set_timeline_ignore_zero = old.set_timeline_ignore_zero
        self.dummy_action_use_frame_range = old.dummy_action_use_frame_range
        self.dummy_action_frame_start = old.dummy_action_frame_start
        self.dummy_action_frame_end = old.dummy_action_frame_end
    
    set_timeline_ignore_zero: BoolProperty(
		name="0->1",
        description="When true, Set Timeline will ignore a frame on frame zero, and set the start to frame one instead. Useful when previewing looping animations.\n\nNOTE: Quick Export functions will still export the full frame-range of the action",
        options=set(),
		default=True
	)
    
    dummy_action_use_frame_range: BoolProperty(
        name="Manual Frame Range",
        options=set(),
        default=False
    )
    
    dummy_action_frame_start: FloatProperty(
        name="Start",
        options=set(),
        default=0.0
    )
    
    dummy_action_frame_end: FloatProperty(
        name="End",
        options=set(),
        default=0.0
    )


def register():
    bpy.utils.register_class(ActionExport)
    bpy.utils.register_class(QuickExportActionFilterEntry)
    bpy.utils.register_class(ExportItemObjectPointer)
    bpy.utils.register_class(ProtoToolsQuickExport_SingleExportProperties)
    bpy.utils.register_class(ProtoToolsQuickExport_ExportItemProperties)
    bpy.utils.register_class(ProtoToolsQuickExport_Properties)
    bpy.utils.register_class(ProtoToolsActionSelectProperties)
    
    bpy.types.Scene.proto_quickexport = bpy.props.PointerProperty(type=ProtoToolsQuickExport_Properties)
    bpy.types.Scene.proto_actionselect = bpy.props.PointerProperty(type=ProtoToolsActionSelectProperties)


def unregister():
    bpy.utils.unregister_class(ProtoToolsActionSelectProperties)
    bpy.utils.unregister_class(ProtoToolsQuickExport_Properties)
    bpy.utils.unregister_class(ProtoToolsQuickExport_ExportItemProperties)
    bpy.utils.unregister_class(ProtoToolsQuickExport_SingleExportProperties)
    bpy.utils.unregister_class(ExportItemObjectPointer)
    bpy.utils.unregister_class(QuickExportActionFilterEntry)
    bpy.utils.unregister_class(ActionExport)
    
    del bpy.types.Scene.proto_actionselect
    del bpy.types.Scene.proto_quickexport


def on_save_pre():
    # Reset export properties copy tracker
    for scene in bpy.data.scenes:
        if hasattr(scene, "proto_quickexport"):
            scene.proto_quickexport.clipboard_export_properties_copied = False

