bl_info = {
    "name": "VectArt Import & Preview",
    "author": "Dimona Patrick",
    "version": (1, 0, 4),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > VectArt Import",
    "description": "Import and preview vector files with layer management and SVG editor connection",
    "category": "Import-Export",
}

import bpy
import os
import math
import time
import platform
import subprocess
import shutil
import sys
import tempfile
from bpy_extras.io_utils import ImportHelper
from bpy.props import (StringProperty, 
                      BoolProperty,
                      EnumProperty, 
                      FloatProperty, 
                      IntProperty,
                      CollectionProperty,
                      PointerProperty)
from bpy.types import (Operator,
                      Panel,
                      PropertyGroup,
                      UIList,
                      AddonPreferences,
                      Object,Menu)
from bpy.utils import previews
from mathutils import Vector
from bpy.app.handlers import persistent



if "preview_collections" not in globals():
    preview_collections = {}

_vectart_session = {}

def get_preview_items(self, context):
    """Get preview items for SVG files"""
    pcoll = preview_collections.get("vectart_previews")
    if pcoll is None:
        return []
    return pcoll.enum_items if hasattr(pcoll, "enum_items") else []

def generate_previews():
    """Generate preview icons for SVG files"""
    # Clear existing previews
    if "vectart_previews" in preview_collections:
        preview_collections["vectart_previews"].close()
        del preview_collections["vectart_previews"]
    
    pcoll = bpy.utils.previews.new()
    preview_collections["vectart_previews"] = pcoll
    enum_items = []
    
    try:
        if not bpy.context or not bpy.context.scene:
            return enum_items
            
        props = bpy.context.scene.vectart_library_props
        base_path = get_base_path()
        
        if not props.current_folder or not base_path:
            return enum_items
            
        folder_path = normalize_path(os.path.join(base_path, props.current_folder))
        if not os.path.exists(folder_path):
            return enum_items
            
        for i, file in enumerate(sorted(os.listdir(folder_path))):
            if not file.lower().endswith('.svg'):
                continue
                
            filepath = normalize_path(os.path.join(folder_path, file))
            try:
                icon = pcoll.load(filepath, filepath, 'IMAGE')
                enum_items.append((filepath, os.path.splitext(file)[0], "", icon.icon_id, i))
            except Exception as e:
                print(f"Error loading preview for {file}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error generating previews: {str(e)}")
        return enum_items
    
    pcoll.enum_items = enum_items
    return enum_items

@persistent
def load_handler(dummy):
    """Handler for file load"""
    # Generate previews
    generate_previews()
    
    try:
        # Initialize live update
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    override = {'window': window, 'screen': window.screen, 'area': area}
                    bpy.ops.object.live_update(override)
        
        # Initialize vertex colors
        for obj in bpy.data.objects:
            if obj.get("is_vectart"):
                if obj.type == 'CURVE' and obj.data.vertex_colors.active is None:
                    obj.data.vertex_colors.new(name="Col")
    except Exception as e:
        print(f"VectArt load handler error: {str(e)}")

def find_svg_editor_path(editor_type):
    """Find path to SVG editor based on platform and editor type"""
    system = platform.system()
    
    # Default paths by platform and editor type
    paths = {
        'Windows': {
            'ILLUSTRATOR': [
                "C:\\Program Files\\Adobe\\Adobe Illustrator 2023\\Support Files\\Contents\\Windows\\Illustrator.exe",
                "C:\\Program Files\\Adobe\\Adobe Illustrator 2022\\Support Files\\Contents\\Windows\\Illustrator.exe"
            ],
            'AFFINITY': [
                "C:\\Program Files\\Affinity\\Designer\\Designer.exe"
            ],
            'INKSCAPE': [
                "C:\\Program Files\\Inkscape\\inkscape.exe",
                "C:\\Program Files\\Inkscape\\bin\\inkscape.exe"
            ]
        },
        'Darwin': {  # macOS
            'ILLUSTRATOR': [
                "/Applications/Adobe Illustrator.app/Contents/MacOS/Adobe Illustrator"
            ],
            'AFFINITY': [
                "/Applications/Affinity Designer.app/Contents/MacOS/Affinity Designer"
            ],
            'INKSCAPE': [
                "/Applications/Inkscape.app/Contents/MacOS/Inkscape"
            ]
        },
        'Linux': {
            'INKSCAPE': [
                "/usr/bin/inkscape"
            ]
        }
    }
    
    # Check if system is supported
    if system not in paths:
        return ""
        
    # Check if editor type is available for this system
    if editor_type not in paths[system]:
        return ""
        
    # Try each possible path
    for path in paths[system][editor_type]:
        if os.path.exists(path):
            return path
            
    # Try to find in PATH
    if editor_type == 'INKSCAPE':
        inkscape_path = shutil.which('inkscape')
        if inkscape_path:
            return inkscape_path
            
    return ""

def update_editor_path(self, context):
    """Update editor path when type changes"""
    if self.svg_editor_type != 'CUSTOM':
        path = find_svg_editor_path(self.svg_editor_type)
        if path:
            self.svg_editor_path = path

def auto_assign_layer(context, curve_obj):
    """Automatically assign a curve to the appropriate layer based on z-position"""
    props = context.scene.vectart_props
    
    # Create default layer if none exist
    if len(props.layers) == 0:
        bpy.ops.object.add_layer()
    
    # Get curve's z position
    z_pos = curve_obj.location.z
    
    # Find the closest layer based on z position
    closest_layer_idx = 0
    smallest_diff = float('inf')
    
    for idx, layer in enumerate(props.layers):
        layer_z = props.get_layer_offset(idx)
        diff = abs(z_pos - layer_z)
        
        if diff < smallest_diff:
            smallest_diff = diff
            closest_layer_idx = idx
    
    # Assign the curve to the closest layer
    curve_obj["vectart_layer"] = closest_layer_idx
    # Add a custom property to mark this as a vectart curve
    curve_obj["is_vectart"] = True
    return closest_layer_idx

@persistent
def scene_update_handler(scene):
    """Handle scene updates"""
    try:
        # Check if we need to update
        if not scene.vectart_props.live_update_enabled:
            return
            
        update_settings = scene.vectart_update_settings
        if not update_settings.is_updating:
            return
            
        current_time = time.time()
        if current_time - update_settings.last_update < update_settings.update_delay:
            return
            
        # Update all vectart objects
        for obj in scene.objects:
            if obj.get("is_vectart"):
                update_vectart_object(obj, scene)
                
        update_settings.is_updating = False
        update_settings.last_update = current_time
        
    except Exception as e:
        print(f"Scene update error: {str(e)}")

def update_vectart_object(obj, scene):
    """Update individual vectart object"""
    try:
        props = scene.vectart_props
        layer_idx = obj.get("vectart_layer", 0)
        
        if layer_idx >= len(props.layers):
            return
            
        layer = props.layers[layer_idx]
        if not layer.active:
            return
            
        # Update object properties
        if obj.type == 'CURVE':
            obj.data.extrude = layer.settings.extrude_height
            obj.data.bevel_depth = props.bevel_depth
            obj.data.bevel_resolution = props.bevel_resolution
            obj.data.offset = props.curve_offset
            
            # Update splines
            for spline in obj.data.splines:
                spline.use_cyclic_u = props.use_cyclic
                
        # Update transforms
        obj.location.z = props.get_layer_offset(layer_idx)
        obj.scale = Vector((layer.settings.scale,) * 3)
        
    except Exception as e:
        print(f"Object update error: {str(e)}")

def get_layer_curves(layer_idx):
    """Get all curves assigned to a specific layer"""
    curves = []
    try:
        for obj in bpy.data.objects:
            if (obj.type == 'CURVE' and 
                "is_vectart" in obj and 
                "vectart_layer" in obj and 
                obj["vectart_layer"] == layer_idx):
                curves.append(obj)
    except Exception as e:
        print(f"Error getting layer curves: {str(e)}")
    return curves

def update_layer_settings(self, context):
    """Update settings for curves in the layer"""
    if not context.scene.vectart_props.live_update_enabled:
        return
        
    try:
        props = context.scene.vectart_props
        layer_idx = -1
        
        # Find the layer index for this settings object
        for idx, layer in enumerate(props.layers):
            if layer.settings == self:
                layer_idx = idx
                break
                
        if layer_idx == -1:
            return
            
        # Get curves in this layer
        curves = get_layer_curves(layer_idx)
        for curve in curves:
            if curve.type == 'CURVE':
                # Apply existing settings
                curve.scale = Vector((self.scale,) * 3)
                curve.data.extrude = self.extrude_height
                curve.location.z = props.get_layer_offset(layer_idx)
                
                # Apply curve properties
                curve.data.bevel_depth = props.bevel_depth
                curve.data.bevel_resolution = props.bevel_resolution
                for spline in curve.data.splines:
                    spline.use_cyclic_u = props.use_cyclic
                
    except Exception as e:
        print(f"Error updating layer settings: {str(e)}")

def update_curve_properties(self, context):
    """Update all curve properties when global settings change"""
    if not context.scene.vectart_props.live_update_enabled:
        return
        
    try:
        for layer in context.scene.vectart_props.layers:
            if layer.active:
                layer_curves = get_layer_curves(context.scene.vectart_props.layers.find(layer.name))
                for curve in layer_curves:
                    if curve.type == 'CURVE':
                        # Apply bevel settings
                        curve.data.bevel_depth = self.bevel_depth
                        curve.data.bevel_resolution = self.bevel_resolution
                        
                        # Apply cyclic setting
                        for spline in curve.data.splines:
                            spline.use_cyclic_u = self.use_cyclic
                            
    except Exception as e:
        print(f"Error updating curve properties: {str(e)}")

def update_layer_visibility(self, context):
    """Update curve visibility when layer visibility changes"""
    try:
        layer_idx = context.scene.vectart_props.active_layer_index
        layer_curves = get_layer_curves(layer_idx)
        
        for curve in layer_curves:
            curve.hide_viewport = not self.active
            curve.hide_render = not self.active
            
    except Exception as e:
        print(f"Error updating visibility: {str(e)}")

def get_layer_offset(self, layer_index):
    """Calculate the total offset for a given layer"""
    try:
        # Start with base offset
        total_offset = self.base_z_offset
        
        # Add spacing for each layer up to this one
        total_offset += layer_index * self.layer_spacing
        
        # Add individual layer offsets up to this index
        for i in range(layer_index + 1):  # Include current layer
            if i < len(self.layers):
                layer = self.layers[i]
                if layer.active:
                    total_offset += layer.settings.z_offset
                    
        return total_offset
        
    except Exception as e:
        print(f"Error calculating layer offset: {str(e)}")
        return 0.0


def update_all_layers(self, context):
    """Update all layers when global settings change"""
    if not context.scene.vectart_props.live_update_enabled:
        return
        
    try:
        for idx, layer in enumerate(context.scene.vectart_props.layers):
            if layer.active:  # Only update active layers
                layer_curves = get_layer_curves(idx)
                for curve in layer_curves:
                    if curve.type == 'CURVE':
                        # Calculate and apply new z position
                        new_z = self.get_layer_offset(idx)
                        curve.location.z = new_z
                    
    except Exception as e:
        print(f"Error updating layers: {str(e)}")

def update_z_offset(self, context):
    """Update z positions when z_offset changes"""
    if not context.scene.vectart_props.live_update_enabled:
        return
        
    try:
        props = context.scene.vectart_props
        layer_idx = -1
        
        # Find the layer index for this settings object
        for idx, layer in enumerate(props.layers):
            if layer.settings == self:
                layer_idx = idx
                break
                
        if layer_idx == -1:
            return
            
        # Update all curves in this layer and layers above it
        for idx in range(layer_idx, len(props.layers)):
            curves = get_layer_curves(idx)
            for curve in curves:
                if curve.type == 'CURVE':
                    curve.location.z = get_layer_offset(props, idx)  
                    
    except Exception as e:
        print(f"Error updating z offset: {str(e)}")

def update_layer_selection(self, context):
    """Update selection when active layer changes"""
    if hasattr(context, 'scene'):  # Check if context is valid
        bpy.ops.object.select_layer(layer_index=self.active_layer_index)

def get_objects_bounding_box(objects):
    """Calculate the bounding box for a list of objects"""
    min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
    max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
    
    for obj in objects:
        # Get world matrix
        matrix = obj.matrix_world
        
        # Get bounding box corners in world space
        for corner in obj.bound_box:
            world_corner = matrix @ Vector(corner)
            
            # Update min/max
            min_x = min(min_x, world_corner.x)
            min_y = min(min_y, world_corner.y)
            min_z = min(min_z, world_corner.z)
            max_x = max(max_x, world_corner.x)
            max_y = max(max_y, world_corner.y)
            max_z = max(max_z, world_corner.z)
    
    # Calculate dimensions and center
    dimensions = Vector((max_x - min_x, max_y - min_y, max_z - min_z))
    center = Vector(((min_x + max_x)/2, (min_y + max_y)/2, (min_z + max_z)/2))
    
    return {
        'center': center,
        'dimensions': dimensions,
        'min': Vector((min_x, min_y, min_z)),
        'max': Vector((max_x, max_y, max_z))
    }

def get_addon_prefs():
    """Get addon preferences"""
    return bpy.context.preferences.addons[__package__].preferences

def normalize_path(path):
    """Normalize path for cross-platform compatibility"""
    if path:
        return os.path.normpath(path)
    return path

_base_path_warned = False

def get_base_path():
    """Get base path from preferences or scene"""
    global _base_path_warned
    try:
        prefs = get_addon_prefs()
        if prefs and prefs.base_path and os.path.exists(prefs.base_path):
            _base_path_warned = False
            return normalize_path(os.path.abspath(prefs.base_path))
            
        scene = bpy.context.scene
        if (hasattr(scene, 'vectart_library_props') and 
            hasattr(scene.vectart_library_props, "base_path") and
            scene.vectart_library_props.base_path and 
            os.path.exists(scene.vectart_library_props.base_path)):
            _base_path_warned = False
            return normalize_path(os.path.abspath(scene.vectart_library_props.base_path))
            
    except Exception as e:
        print(f"Error getting base path: {str(e)}")
        
    # Show user-friendly message only once per session
    if not _base_path_warned:
        print("VectArt: Please set the library path in the add-on preferences (Edit > Preferences > Add-ons > VectArt Import & Preview).")
        _base_path_warned = True
        
    return ""

def get_subfolders(self, context):
    """Get list of subfolders in the library path"""
    items = []
    
    try:
        path = get_base_path()
        if path and os.path.exists(path):
            folders = [f for f in os.listdir(path) 
                      if os.path.isdir(os.path.join(path, f))]
            items = [(f, f, "") for f in sorted(folders)]
    except Exception as e:
        print(f"Error loading folders: {str(e)}")
    
    return items if items else [("", "No folders found", "")]

# Preferences
class VectartAddonPreferences(AddonPreferences):
    bl_idname = __package__

    base_path: StringProperty(
        name="Library Path",
        subtype='DIR_PATH',
        default="",
        description="Base path for SVG library"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "base_path")

# Property Groups
class VectartUpdateSettings(PropertyGroup):
    is_updating: BoolProperty(default=False)
    last_update: FloatProperty(default=0.0)
    update_delay: FloatProperty(default=0.1, min=0.01)

class VectartLayerSettings(PropertyGroup):
    scale: FloatProperty(
        name="Scale",
        default=1.0,
        min=0.001,
        max=100.0,
        update=lambda self, context: update_layer_settings(self, context)
    )
    z_offset: FloatProperty(
        name="Z Offset",
        default=0.0,
        description="Fine-tune the vertical position of this layer",
        update=lambda self, context: update_z_offset(self, context)
    )
    extrude_height: FloatProperty(
        name="Extrude Height",
        default=0.01,
        min=0.0,
        update=lambda self, context: update_layer_settings(self, context)
    )

class VectartLayerItem(PropertyGroup):
    name: StringProperty(
        name="Name",
        default="Layer"
    )
    active: BoolProperty(
        name="Active",
        default=True,
        update=lambda self, context: update_layer_visibility(self, context)
    )
    settings: PointerProperty(type=VectartLayerSettings)

class VectartFolderItem(PropertyGroup):
    name: StringProperty()

class VectartLibraryProperties(PropertyGroup):
    current_folder: EnumProperty(
        name="Current Folder",
        items=get_subfolders,
        description="Select SVG folder"
    ) 
    preview_index: EnumProperty(
        items=get_preview_items,
        name="Preview Index"
    )

class VectartProperties(PropertyGroup):
    layers: CollectionProperty(type=VectartLayerItem)
    active_layer_index: IntProperty()
    update=update_layer_selection
    
    base_z_offset: FloatProperty(
        name="Base Height",
        default=0.0,
        update=lambda self, context: update_all_layers(self, context)
    )
    layer_spacing: FloatProperty(
        name="Layer Gap",
        default=0.01,
        min=0.0,
        update=lambda self, context: update_all_layers(self, context)
    )
    scale_factor: FloatProperty(
        name="Scale Factor",
        default=10.0,
        min=0.01,
        max=100.0,
        update=lambda self, context: update_all_layers(self, context)
    )
    
    # Live update
    live_update_enabled: BoolProperty(
        name="Live Update",
        description="Update curves immediately when settings change",
        default=True
    )
    bevel_depth: FloatProperty(
        name="Bevel Depth",
        default=0.0002,
        update=update_curve_properties

    )
    bevel_resolution: IntProperty(
        name="Bevel Resolution",
        default=4,
        update=update_curve_properties

    )
    use_cyclic: BoolProperty(
        name="Use Cyclic",
        default=True,
        update=update_curve_properties
    )


    empty_name: StringProperty(
        name="Name",
        default="VectArt_Group"
    )
    
    empty_type: EnumProperty(
        name="Empty Type",
        items=[
            ('PLAIN_AXES', "Plain Axes", "Plain Axes"),
            ('ARROWS', "Arrows", "Arrows"),
            ('SINGLE_ARROW', "Single Arrow", "Single Arrow"),
            ('CIRCLE', "Circle", "Circle"),
            ('CUBE', "Cube", "Cube"),
            ('SPHERE', "Sphere", "Sphere"),
        ],
        default='CUBE'
    )

    svg_editor_type: EnumProperty(
        name="Editor Type",
        items=[
            ('ILLUSTRATOR', "Adobe Illustrator", "Adobe Illustrator"),
            ('AFFINITY', "Affinity Designer", "Affinity Designer"),
            ('INKSCAPE', "Inkscape", "Inkscape"),
            ('CUSTOM', "Custom", "Custom SVG editor"),
        ],
        default='INKSCAPE',
        update=update_editor_path
    )
    svg_editor_path: StringProperty(
        name="Editor Path",
        subtype='FILE_PATH',
        description="Path to SVG editor executable"
    )
    auto_update_svg: BoolProperty(
        name="Auto Update",
        description="Automatically update SVG in Blender when saved externally",
        default=True
    )
    show_global_help: BoolProperty(
        name="Show Help",
        description="Show help for global settings abbreviations",
        default=False
    )
    
    def get_layer_offset(self, layer_index):
        """Calculate the total offset for a given layer"""
        base_offset = self.base_z_offset
        layer_offset = layer_index * self.layer_spacing
        
        # Add individual layer offsets up to this index
        for i in range(layer_index):
            if i < len(self.layers):
                layer = self.layers[i]
                if layer.active:
                    layer_offset += layer.settings.z_offset
        
        return base_offset + layer_offset

# Operators
class VECTART_OT_ImportSVG(Operator):
    bl_idname = "object.import_svg"
    bl_label = "Import SVG"
    bl_description = "Import SVG file"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        subtype='FILE_PATH',
        default=""
    )
    filter_glob: StringProperty(default="*.svg", options={'HIDDEN'})

    def get_curve_bounds(self, curve):
        """Get bounding box dimensions for a curve"""
        matrix = curve.matrix_world
        bbox_corners = [matrix @ Vector(corner) for corner in curve.bound_box]

        min_x = min(corner.x for corner in bbox_corners)
        max_x = max(corner.x for corner in bbox_corners)
        min_y = min(corner.y for corner in bbox_corners)
        max_y = max(corner.y for corner in bbox_corners)

        width = max_x - min_x
        height = max_y - min_y
        area = width * height

        return {
            'width': width,
            'height': height,
            'area': area,
            'center': Vector(((min_x + max_x)/2, (min_y + max_y)/2, 0))
        }

    def auto_assign_layer(context, curve_obj):
        try:
            props = context.scene.vectart_props
            
            # Create default layer if none exist
            if len(props.layers) == 0:
                result = bpy.ops.vectart.add_layer()
                if result != {'FINISHED'}:
                    raise Exception("Failed to create default layer")
            
            # Get curve's z position
            z_pos = curve_obj.location.z
            
            # Find closest layer
            closest_layer_idx = 0
            smallest_diff = float('inf')
            
            for idx, layer in enumerate(props.layers):
                layer_z = props.get_layer_offset(idx)
                diff = abs(z_pos - layer_z)
                
                if diff < smallest_diff:
                    smallest_diff = diff
                    closest_layer_idx = idx
            
            # Assign to layer
            curve_obj["vectart_layer"] = closest_layer_idx
            curve_obj["is_vectart"] = True
            
            # Apply layer settings
            layer = props.layers[closest_layer_idx]
            curve_obj.data.extrude = layer.settings.extrude_height
            curve_obj.scale = Vector((layer.settings.scale,) * 3)
            curve_obj.location.z = props.get_layer_offset(closest_layer_idx)
            
            return closest_layer_idx
            
        except Exception as e:
            print(f"Error assigning layer: {str(e)}")
            return -1

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}
    
        try:
            # Import SVG
            bpy.ops.import_curve.svg(filepath=self.filepath)
            
            # Get imported curves
            imported_curves = [obj for obj in context.selected_objects if obj.type == 'CURVE']
            
            if not imported_curves:
                self.report({'WARNING'}, "No curves imported")
                return {'CANCELLED'}
            
            props = context.scene.vectart_props
            
            # Apply settings to imported curves
            for curve in imported_curves:
                # Apply bevel settings
                curve.data.bevel_depth = props.bevel_depth
                curve.data.bevel_resolution = props.bevel_resolution
                
                # Apply cyclic setting
                for spline in curve.data.splines:
                    spline.use_cyclic_u = props.use_cyclic
            
            # Process imported curves
            self.auto_assign_layer(context, imported_curves)
            
            self.report({'INFO'}, f"Successfully imported {len(imported_curves)} curves")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error importing SVG: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
class VECTART_OT_LiveUpdate(Operator):
    bl_idname = "object.live_update"
    bl_label = "Live Update"
    bl_description = "Toggle live update mode"
    
    def execute(self, context):
        props = context.scene.vectart_props
        props.live_update_enabled = not props.live_update_enabled
        return {'FINISHED'} 
   
class VECTART_OT_ImportLibrarySVG(Operator):
    bl_idname = "object.import_library_svg"
    bl_label = "Import SVG"
    bl_description = "Import selected SVG from library and split to layers"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.vectart_library_props
        vectart_props = context.scene.vectart_props  
        if not props.preview_index:
            self.report({'ERROR'}, "No SVG file selected")
            return {'CANCELLED'}
            
        try:
            # Get list of existing objects before import
            existing_objects = set(bpy.data.objects[:])
            
            # Import SVG using the selected file path
            result = bpy.ops.import_curve.svg(filepath=props.preview_index)
            
            if result != {'FINISHED'}:
                self.report({'ERROR'}, "Failed to import SVG file")
                return {'CANCELLED'}
            
            # Find newly created objects by comparing with previous list
            new_objects = set(bpy.data.objects[:]) - existing_objects
            imported_curves = [obj for obj in new_objects if obj.type == 'CURVE']
            
            if not imported_curves:
                self.report({'WARNING'}, "No curves were imported from the SVG file")
                return {'CANCELLED'}
            
            # Deselect everything first
            bpy.ops.object.select_all(action='DESELECT')
            
            # Select and scale imported curves using scale_factor
            for curve in imported_curves:
                curve.select_set(True)
                # Ensure curve is visible and selectable
                curve.hide_viewport = False
                curve.hide_set(False)
                
                # Apply scale factor from properties
                curve.scale = Vector((vectart_props.scale_factor,) * 3)
                
                # Apply bevel and extrude settings immediately
                curve.data.bevel_depth = vectart_props.bevel_depth
                curve.data.bevel_resolution = vectart_props.bevel_resolution
                
                # Apply cyclic setting to all splines
                for spline in curve.data.splines:
                    spline.use_cyclic_u = vectart_props.use_cyclic
            
            # Set active object
            if imported_curves:
                context.view_layer.objects.active = imported_curves[0]
            
            # Apply scale to make it permanent
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            
            # Now execute split to layers
            bpy.ops.object.split_to_layers()
            
            # Update viewport
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
            
            # Focus view on imported objects
            bpy.ops.object.focus_selected()
            
            self.report({'INFO'}, f"Successfully imported and split {len(imported_curves)} curves")
            return {'FINISHED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Error importing SVG: {str(e)}")
            return {'CANCELLED'}

class VECTART_OT_RefreshLibrary(Operator):
    bl_idname = "object.refresh_library"
    bl_label = "Refresh Library"
    bl_description = "Refresh SVG preview library"
    
    def cleanup_previews(self):
        """Properly cleanup preview collections"""
        if "vectart_previews" in preview_collections:
            preview_collections["vectart_previews"].close()
            del preview_collections["vectart_previews"]

    def execute(self, context):
        try:
            # Cleanup existing previews
            self.cleanup_previews()
            
            # Generate new previews
            generate_previews()
            
            self.report({'INFO'}, "Library refreshed successfully")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error refreshing library: {str(e)}")
            return {'CANCELLED'}

# Layer Management Operators
class VECTART_OT_AddLayer(Operator):
    bl_idname = "object.add_layer"
    bl_label = "Add Layer"
    bl_description = "Add a new layer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.vectart_props
        layer = props.layers.add()
        layer.name = f"Layer {len(props.layers)}"
        props.active_layer_index = len(props.layers) - 1
        return {'FINISHED'}

class VECTART_OT_RemoveLayer(Operator):
    bl_idname = "object.remove_layer"
    bl_label = "Remove Layer"
    bl_description = "Remove selected layer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.vectart_props
        if props.active_layer_index >= 0 and len(props.layers) > 0:
            # Remove all curves in this layer
            curves = get_layer_curves(props.active_layer_index)
            for curve in curves:
                bpy.data.objects.remove(curve, do_unlink=True)
                
            props.layers.remove(props.active_layer_index)
            props.active_layer_index = min(props.active_layer_index, len(props.layers) - 1)
        return {'FINISHED'}

class VECTART_OT_MoveLayers(Operator):
    bl_idname = "object.move_layers"
    bl_label = "Move Layer"
    bl_description = "Move layer up or down"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        items=[
            ('UP', "Up", "Move layer up"),
            ('DOWN', "Down", "Move layer down")
        ]
    )

    def execute(self, context):
        props = context.scene.vectart_props
        index = props.active_layer_index

        if self.direction == 'UP' and index > 0:
            props.layers.move(index, index - 1)
            props.active_layer_index -= 1
        elif self.direction == 'DOWN' and index < len(props.layers) - 1:
            props.layers.move(index, index + 1)
            props.active_layer_index += 1

        return {'FINISHED'}

class VECTART_OT_ClearLayers(Operator):
    bl_idname = "object.clear_layers"
    bl_label = "Clear All layers"
    bl_description = "Remove all layers from layer list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        context.scene.vectart_props.layers.clear()
        return {'FINISHED'}

class VECTART_OT_ConvertAndClear(Operator):
    bl_idname = "object.convert_and_clear"
    bl_label = "Convert to Mesh"
    bl_description = "Convert curves in layers to mesh and clear layers"
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(
            self, 
            event,
            message="Convert curves to mesh and clear layers?"
        )
    
    def execute(self, context):
        try:
            props = context.scene.vectart_props
            
            # Get curves only from active layers
            layer_curves = []
            for layer_idx, layer in enumerate(props.layers):
                if layer.active:  
                    curves = get_layer_curves(layer_idx)
                    layer_curves.extend(curves)
            
            if not layer_curves:
                self.report({'WARNING'}, "No curves found in layers")
                return {'CANCELLED'}
            
            # Deselect all objects
            bpy.ops.object.select_all(action='DESELECT')
            
            # Select only curves from layers
            for curve in layer_curves:
                if curve.type == 'CURVE':  
                    curve.select_set(True)
                    curve.hide_viewport = False  
                    curve.hide_set(False)  
                
            # Set active object
            context.view_layer.objects.active = layer_curves[0]
            
            # Convert to mesh
            result = bpy.ops.object.convert(target='MESH', keep_original=False)
            
            if result != {'FINISHED'}:
                self.report({'ERROR'}, "Failed to convert curves to mesh")
                return {'CANCELLED'}
            
            # Clear all layers
            props.layers.clear()
            
            self.report({'INFO'}, f"Successfully converted {len(layer_curves)} curves to mesh and cleared layers")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error during conversion: {str(e)}")
            return {'CANCELLED'}

class VECTART_OT_SelectAllCurves(Operator):
    bl_idname = "object.select_all_curves"
    bl_label = "Select All Curves"
    bl_description = "Select all curves in the active collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Deselect all objects first
        bpy.ops.object.select_all(action='DESELECT')
        
        # Get active collection
        active_collection = context.view_layer.active_layer_collection.collection
        if not active_collection:
            self.report({'WARNING'}, "No active collection")
            return {'CANCELLED'}
            
        # Select all curves in the collection
        selected_count = 0
        for obj in active_collection.objects:
            if obj.type == 'CURVE':
                obj.select_set(True)
                selected_count += 1
                
        if selected_count > 0:
            # Set the last selected curve as active object
            context.view_layer.objects.active = obj
            self.report({'INFO'}, f"Selected {selected_count} curves")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No curves found in active collection")
            return {'CANCELLED'}

class VECTART_OT_CreateEmpty(Operator):
    bl_idname = "object.create_empty"
    bl_label = "Create Empty Parent"
    bl_description = "Create empty object at center of selected curves with bounding box size"
    bl_options = {'REGISTER', 'UNDO'}
    
    use_bounding_box: BoolProperty(
        name="Match Bounding Box",
        description="Set empty size to match the bounding box of selected objects",
        default=True
    )
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects and any(obj.type in {'CURVE', 'MESH'} for obj in context.selected_objects)
    
    def execute(self, context):
        try:
            props = context.scene.vectart_props
            
            # Store original selection and active object
            original_selection = context.selected_objects[:]
            original_active = context.view_layer.objects.active
            
            # Get selected curves and meshes
            selected_objects = [obj for obj in context.selected_objects if obj.type in {'CURVE', 'MESH'}]
            
            if not selected_objects:
                self.report({'WARNING'}, "No curves or meshes selected")
                return {'CANCELLED'}
            
            # Center pivots for each object
            for obj in selected_objects:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            
            # Calculate bounding box
            bbox = get_objects_bounding_box(selected_objects)
            center = bbox['center']
            dimensions = bbox['dimensions']
            max_dim = max(dimensions.x, dimensions.y, dimensions.z)
            
            # Deselect all and set 3D cursor to bounding box center
            bpy.ops.object.select_all(action='DESELECT')
            context.scene.cursor.location = center
            
            # Create empty at cursor
            bpy.ops.object.empty_add(type=props.empty_type, location=center)
            empty = context.active_object
            empty.name = props.empty_name
            empty["is_vectart_group"] = True
            
            # Set empty size and scale
            if self.use_bounding_box:
                if props.empty_type in {'CUBE', 'SPHERE'}:
                    # Scale matches bounding box dimensions
                    empty.scale = Vector((dimensions.x / 2, dimensions.y / 2, dimensions.z / 2))
                    empty.empty_display_size = 1.0  
                else:
                    empty.empty_display_size = max_dim / 2
            else:
                empty.empty_display_size = props.empty_size
            
            # Parent objects to empty without inverse
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected_objects:
                obj.select_set(True)
            empty.select_set(True)
            context.view_layer.objects.active = empty
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            
            # Restore original selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in original_selection:
                if obj:
                    obj.select_set(True)
            if original_active:
                context.view_layer.objects.active = original_active
            
            self.report({'INFO'}, f"Created precise empty for {len(selected_objects)} objects")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating empty: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "use_bounding_box")

class VECTART_OT_SelectLayerCurves(Operator):
    bl_idname = "object.select_layer_curves"
    bl_label = "Select Layer Curves"
    bl_description = "Select all curves in the active layer"
    
    def execute(self, context):
        props = context.scene.vectart_props
        layer_idx = props.active_layer_index
        
        if layer_idx < 0 or layer_idx >= len(props.layers):
            self.report({'ERROR'}, "No active layer")
            return {'CANCELLED'}
            
        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select curves in layer
        curves = get_layer_curves(layer_idx)
        for curve in curves:
            curve.select_set(True)
            
        if curves:
            context.view_layer.objects.active = curves[0]
            self.report({'INFO'}, f"Selected {len(curves)} curves")
        else:
            self.report({'INFO'}, "No curves in layer")
            
        return {'FINISHED'}

class VECTART_OT_AssignToLayer(Operator):
    bl_idname = "object.assign_to_layer"
    bl_label = "Assign to Layer"
    bl_description = "Assign selected curves to active layer"
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects and context.scene.vectart_props.layers

    def execute(self, context):
        props = context.scene.vectart_props
        layer_idx = props.active_layer_index
        
        if layer_idx < 0 or layer_idx >= len(props.layers):
            self.report({'ERROR'}, "Invalid layer")
            return {'CANCELLED'}
            
        selected_curves = [obj for obj in context.selected_objects if obj.type == 'CURVE']
        if not selected_curves:
            self.report({'WARNING'}, "No curves selected")
            return {'CANCELLED'}
            
        layer = props.layers[layer_idx]
        for curve in selected_curves:
            curve["is_vectart"] = True
            curve["vectart_layer"] = layer_idx
            curve.data.extrude = layer.settings.extrude_height
            curve.scale = Vector((layer.settings.scale,) * 3)
            curve.location.z = props.get_layer_offset(layer_idx)
            
        self.report({'INFO'}, f"Assigned {len(selected_curves)} curves to layer")
        return {'FINISHED'}

class VECTART_OT_DuplicateLayer(Operator):
    bl_idname = "object.duplicate_layer"
    bl_label = "Duplicate Layer"
    bl_description = "Duplicate active layer with its curves"
    
    def execute(self, context):
        props = context.scene.vectart_props
        src_idx = props.active_layer_index
        
        if src_idx < 0 or src_idx >= len(props.layers):
            self.report({'ERROR'}, "No active layer")
            return {'CANCELLED'}
            
        try:
            # Create new layer
            new_layer = props.layers.add()
            new_idx = len(props.layers) - 1
            
            # Copy settings
            src_layer = props.layers[src_idx]
            new_layer.name = f"{src_layer.name}_copy"
            new_layer.active = src_layer.active
            new_layer.settings.scale = src_layer.settings.scale
            new_layer.settings.z_offset = src_layer.settings.z_offset
            new_layer.settings.extrude_height = src_layer.settings.extrude_height
            
            # Duplicate curves
            curves = get_layer_curves(src_idx)
            for curve in curves:
                new_curve = curve.copy()
                new_curve.data = curve.data.copy()
                new_curve["vectart_layer"] = new_idx
                bpy.context.scene.collection.objects.link(new_curve)
            
            props.active_layer_index = new_idx
            self.report({'INFO'}, f"Layer duplicated with {len(curves)} curves")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error duplicating layer: {str(e)}")
            return {'CANCELLED'}

class VECTART_OT_SplitToLayers(Operator):
    bl_idname = "object.split_to_layers"
    bl_label = "Split to Layers"
    bl_description = "Create a new layer for each selected curve"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and any(obj.type == 'CURVE' for obj in context.selected_objects)

    def execute(self, context):
        props = context.scene.vectart_props
        
        # Get selected curves
        selected_curves = [obj for obj in context.selected_objects if obj.type == 'CURVE']
        
        if not selected_curves:
            self.report({'WARNING'}, "No curves selected")
            return {'CANCELLED'}
        
        try:
            # Create a new layer for each curve
            for curve in selected_curves:
                # Add new layer
                layer = props.layers.add()
                layer_idx = len(props.layers) - 1
                layer.name = f"Layer {layer_idx + 1} ({curve.name})"
                
                # Mark curve as vectart curve
                curve["is_vectart"] = True
                curve["vectart_layer"] = layer_idx
                
                # Apply layer settings while preserving bevel and cyclic
                bevel_depth = curve.data.bevel_depth
                bevel_resolution = curve.data.bevel_resolution
                
                # Apply new settings
                curve.data.extrude = layer.settings.extrude_height
                curve.scale = Vector((layer.settings.scale,) * 3)
                curve.location.z = props.get_layer_offset(layer_idx)
                
                # Restore bevel settings
                curve.data.bevel_depth = bevel_depth
                curve.data.bevel_resolution = bevel_resolution
            
            # Set active layer to last created layer
            props.active_layer_index = len(props.layers) - 1
            
            self.report({'INFO'}, f"Created {len(selected_curves)} new layers")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error splitting curves: {str(e)}")
            return {'CANCELLED'}    

class VECTART_OT_SelectLayer(Operator):
    bl_idname = "object.select_layer"
    bl_label = "Select Layer"
    bl_description = "Select all curves in this layer"
    bl_options = {'REGISTER', 'UNDO'}
    
    layer_index: IntProperty()
    
    def execute(self, context):
        props = context.scene.vectart_props
        
        try:
            # Deselect all objects first
            bpy.ops.object.select_all(action='DESELECT')
            
            # Get curves in this layer
            curves = get_layer_curves(self.layer_index)
            
            # Select curves and make them visible
            for curve in curves:
                curve.select_set(True)
                curve.hide_viewport = False
                curve.hide_set(False)
                
            # Set active object
            if curves:
                context.view_layer.objects.active = curves[0]
                
            # Set active layer index
            props.active_layer_index = self.layer_index
            
            self.report({'INFO'}, f"Selected {len(curves)} curves in layer {self.layer_index + 1}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error selecting layer: {str(e)}")
            return {'CANCELLED'}

class VECTART_OT_FocusSelected(Operator):
    bl_idname = "object.focus_selected"
    bl_label = "Focus Selected"
    bl_description = "Focus view on selected objects"
    
    center: BoolProperty(
        name="Center View",
        description="Center the view on selected objects",
        default=True
    )
    
    def execute(self, context):
        try:
            # Check if there are selected objects
            if not context.selected_objects:
                self.report({'WARNING'}, "No objects selected")
                return {'CANCELLED'}
            
            # Frame selected objects in all 3D viewports
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            override = {
                                'window': context.window,
                                'screen': context.screen,
                                'area': area,
                                'region': region,
                                'scene': context.scene,
                                'space_data': area.spaces.active
                            }
                            
                            with context.temp_override(**override):
                                # Frame selected objects
                                bpy.ops.view3d.view_selected(
                                    use_all_regions=False
                                )
                                
                                if self.center:
                                    # Optional: Center view on objects
                                    bpy.ops.view3d.view_center_cursor()
            
            self.report({'INFO'}, f"Focused on {len(context.selected_objects)} objects")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error focusing: {str(e)}")
            return {'CANCELLED'}

class VECTART_OT_EditSVG(Operator):
    bl_idname = "object.edit_svg"
    bl_label = "Edit Curves in SVG Editor"
    bl_description = "Export curves in selected collection as SVG, edit externally, and reimport with settings"

    def execute(self, context):
        import tempfile

        props = context.scene.vectart_props
        collection = context.view_layer.active_layer_collection.collection

        # Gather all curve objects in the selected collection
        curves = [obj for obj in collection.objects if obj.type == 'CURVE']
        if not curves:
            self.report({'ERROR'}, "No curves found in the selected collection")
            return {'CANCELLED'}

        # Store settings for each curve (layer, bevel, etc.)
        curve_settings = []
        for obj in curves:
            curve_settings.append({
                "name": obj.name,
                "vectart_layer": obj.get("vectart_layer"),
                "is_vectart": obj.get("is_vectart"),
                "bevel_depth": obj.data.bevel_depth,
                "bevel_resolution": obj.data.bevel_resolution,
                "extrude": obj.data.extrude,
                "scale": tuple(obj.scale),
                "location": tuple(obj.location),
            })

        # 3. Export curves as SVG to a temp file using Blender's built-in exporter
        temp_svg = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
        temp_svg.close()
        svg_path = temp_svg.name

        # Duplicate curves, set to 3D, apply transforms, export, then delete duplicates
        duplicates = []
        try:
            # Duplicate curves and link to collection
            for obj in curves:
                dup = obj.copy()
                dup.data = obj.data.copy()
                context.collection.objects.link(dup)
                # Set to 3D to allow transform apply
                dup.data.dimensions = '3D'
                duplicates.append(dup)

            # Select only duplicates
            bpy.ops.object.select_all(action='DESELECT')
            for dup in duplicates:
                dup.select_set(True)
            context.view_layer.objects.active = duplicates[0]

            # Apply all transforms (now allowed for all)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

            # Export
            bpy.ops.export_svg_format.svg(filepath=svg_path, check_existing=False)

        finally:
            # Clean up: delete duplicates
            bpy.ops.object.select_all(action='DESELECT')
            for dup in duplicates:
                dup.select_set(True)
            bpy.ops.object.delete()

        # 4. Launch external editor (cross-platform)
        editor_path = props.svg_editor_path
        if not editor_path:
            if props.svg_editor_type != 'CUSTOM':
                editor_path = find_svg_editor_path(props.svg_editor_type)
                props.svg_editor_path = editor_path
        if not editor_path:
            self.report({'ERROR'}, "SVG editor path not set or detected")
            return {'CANCELLED'}

        try:
            if sys.platform.startswith("win"):
                subprocess.Popen([editor_path, svg_path], shell=False)
            elif sys.platform == "darwin":
                if editor_path.endswith(".app"):
                    subprocess.Popen(["open", "-a", editor_path, svg_path])
                else:
                    subprocess.Popen([editor_path, svg_path])
            else:
                subprocess.Popen([editor_path, svg_path])
        except Exception as e:
            self.report({'ERROR'}, f"Error launching editor: {str(e)}")
            return {'CANCELLED'}

        # 5. Store SVG path and settings for reimport
        _vectart_session["svg_edit_path"] = svg_path
        _vectart_session["svg_edit_settings"] = curve_settings
        _vectart_session["svg_edit_count"] = len(curve_settings)
        _vectart_session["svg_edit_collection"] = collection.name

        self.report({'INFO'}, "Edit the SVG and save, then use 'Reimport Edited SVG' or Refresh button to update.")
        return {'FINISHED'}


class VECTART_OT_ReimportEditedSVG(Operator):
    bl_idname = "object.reimport_edited_svg"
    bl_label = "Reimport Edited SVG"
    bl_description = "Reimport the externally edited SVG and reapply previous settings"

    def execute(self, context):
        svg_path = _vectart_session.get("svg_edit_path")
        curve_settings = _vectart_session.get("svg_edit_settings")
        curve_count = _vectart_session.get("svg_edit_count")
        collection_name = _vectart_session.get("svg_edit_collection")

        if not svg_path or not curve_settings or not collection_name:
            self.report({'ERROR'}, "No SVG edit session found. Please use 'Edit SVG' first.")
            return {'CANCELLED'}

        # Remove old curves from the collection
        collection = bpy.data.collections.get(collection_name)
        if not collection:
            self.report({'ERROR'}, "Original collection not found.")
            return {'CANCELLED'}

        old_curves = [obj for obj in collection.objects if obj.type == 'CURVE']
        for obj in old_curves:
            bpy.data.objects.remove(obj, do_unlink=True)

        # Import edited SVG
        before_objs = set(bpy.data.objects)
        bpy.ops.import_curve.svg(filepath=svg_path)
        after_objs = set(bpy.data.objects)
        imported = [obj for obj in (after_objs - before_objs) if obj.type == 'CURVE']

        # Link imported curves to the original collection if needed
        for obj in imported:
            if obj.name not in collection.objects:
                collection.objects.link(obj)

        # Reapply settings and transforms by order
        for i, obj in enumerate(imported):
            if i < len(curve_settings):
                settings = curve_settings[i]
                obj["vectart_layer"] = settings["vectart_layer"]
                obj["is_vectart"] = settings["is_vectart"]
                obj.data.bevel_depth = settings["bevel_depth"]
                obj.data.bevel_resolution = settings["bevel_resolution"]
                obj.data.extrude = settings["extrude"]
                obj.scale = settings["scale"]
                obj.location = settings["location"]

        self.report({'INFO'}, f"Reimported and reapplied settings to {len(imported)} curves.")

        # Clean up session data
        _vectart_session.clear()

        return {'FINISHED'}


# UI Lists
class VECTART_UL_LayerList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            # Layer visibility toggle with better icon
            icon = 'HIDE_OFF' if item.active else 'HIDE_ON'
            row.prop(item, "active", text="", icon=icon, emboss=False)
            # Editable name field for renaming
            row.prop(item, "name", text="", emboss=True, icon='GREASEPENCIL')
            # Quick settings if layer is active with better layout
            if item.active:
                sub = row.row(align=True)
                sub.scale_x = 0.7
                sub.prop(item.settings, "extrude_height", text="")

# Library Panel with improved layout
class VECTART_PT_LibraryPanel(Panel):
    bl_label = "VectArt Library"
    bl_idname = "VECTART_PT_library"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VectArt'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.vectart_library_props
        base_path = get_base_path()
        
        # Show preferences button if path not set
        if not base_path:
            box = layout.box()
            col = box.column(align=True)
            col.label(text="Library path not set!", icon='ERROR')
            col.operator(
                "preferences.addon_show",
                text="Open Preferences",
                icon='PREFERENCES'
            ).module = __package__
            return
            
        # Show current path in a more compact way
        path_box = layout.box()
        row = path_box.row()
        row.label(text="Library Path:", icon='FILE_FOLDER')
        
        # Show path in a smaller font with ellipsis if too long
        path_text = base_path
        if len(path_text) > 30:
            path_text = "..." + path_text[-27:]
        path_box.label(text=path_text)
            
        # Folder selection 
        col = layout.column(align=True)
        col.separator(factor=0.5)
        
        box = col.box()
        box.label(text="SVG Collections", icon='OUTLINER_OB_GROUP_INSTANCE')
        
        row = box.row(align=True)
        row.scale_y = 1.2
        row.prop_menu_enum(props, "current_folder", 
                          text=props.current_folder or "Select Folder")
        
        # Manual refresh button 
        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator(
            "object.refresh_library", 
            text="Refresh Library",
            icon='FILE_REFRESH'
        )

# Preview Panel 
class VECTART_PT_PreviewPanel(Panel):
    bl_label = "SVG Preview"
    bl_idname = "VECTART_PT_preview"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VectArt'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.vectart_library_props
        vectart_props = context.scene.vectart_props
        base_path = get_base_path()  
        
        if not props.current_folder:
            col = layout.column(align=True)
            col.label(text="Select a folder to view SVGs", icon='INFO')
            col.separator()
            col.operator("object.refresh_library", text="Refresh Library", icon='FILE_REFRESH')
            return
            
        folder_path = os.path.join(base_path, props.current_folder) 
        if not os.path.exists(folder_path):
            col = layout.column(align=True)
            col.label(text="Selected folder not found", icon='ERROR')
            col.separator()
            col.operator("object.refresh_library", text="Refresh Library", icon='FILE_REFRESH')
            return

        # Display thumbnails in a grid 
        preview_box = layout.box()
        preview_box.label(text="Available SVGs:", icon='IMAGE_DATA')
        row = preview_box.row()
        row.template_icon_view(props, 
                             "preview_index", 
                             show_labels=True, 
                             scale=6, 
                             scale_popup=2)
        
        # Import settings in a more compact layout
        settings_box = layout.box()
        row = settings_box.row()
        row.label(text="Import Settings:", icon='SETTINGS')
        row.prop(vectart_props, "scale_factor", text="")

        # Import buttons 
        col = layout.column(align=True)
        col.separator(factor=0.5)
        
        # Button row 
        row = col.row(align=True)
        
        if props.preview_index:
            # Left button - Import Selected SVG
            sub_row = row.row(align=True)
            sub_row.scale_y = 1.5
            sub_row.operator("object.import_library_svg", 
                        text="Import Selected", 
                        icon='IMPORT')
            
            # Add a small separator
            row.separator(factor=0.5)
        
        # Right button - Import New SVG
        sub_row = row.row(align=True)
        sub_row.scale_y = 1.5
        sub_row.operator("object.import_svg", 
                      icon='FILEBROWSER', 
                      text="Import New")

# Layer Panel 
class VECTART_PT_LayerPanel(Panel):
    bl_label = "VectArt Layers"
    bl_idname = "VECTART_PT_layer_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VectArt"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.vectart_props  

        # Live update 
        row = layout.row(align=True)
        row.scale_y = 1.2
        row.prop(props, "live_update_enabled", text="Live Update", icon='AUTO', toggle=True)

        layout.separator(factor=0.7)

        # Layer list section
        box = layout.box()
        box.label(text="Layers", icon='OUTLINER_OB_LIGHTPROBE')

        # Layer list 
        row = box.row()
        list_col = row.column()
        list_col.template_list("VECTART_UL_LayerList", "", props, "layers",
                            props, "active_layer_index", 
                            rows=6,
                            type='DEFAULT')

        # Layer management buttons 
        button_col = row.column(align=True)
        button_col.scale_y = 1.1

        # Add/Remove
        add_remove = button_col.column(align=True)
        add_remove.operator("object.add_layer", icon='ADD', text="")
        add_remove.operator("object.remove_layer", icon='REMOVE', text="")

        button_col.separator(factor=1.0)

        # Move Up/Down
        move = button_col.column(align=True) 
        move.operator("object.move_layers", icon='TRIA_UP', text="").direction = 'UP'
        move.operator("object.move_layers", icon='TRIA_DOWN', text="").direction = 'DOWN'

        button_col.separator(factor=1.0)

        # Duplicate/Clear
        utils = button_col.column(align=True)
        utils.operator("object.duplicate_layer", icon='DUPLICATE', text="")
        utils.operator("object.clear_layers", icon='TRASH', text="")

        # Selection Tools 
        box = layout.box()
        row = box.row(align=True)

        row.operator("object.select_all_curves", 
                    icon='OUTLINER_OB_CURVE', 
                    text="Select")
        
        row.operator("object.split_to_layers", 
                    icon='OUTLINER_OB_MESH', 
                    text="Split")
        
        row.operator("object.focus_selected", 
                     icon='ZOOM_SELECTED', 
                     text="Focus")
        
        layout.separator(factor=0.5)
        
        # Convert and Clear button 
        row = layout.row()
        row.scale_y = 1.5
        row.operator("object.convert_and_clear", 
                    text="Convert to Mesh", 
                    icon='MESH_DATA')
        
        # Global settings 
        box = layout.box()
        row = box.row()
        row.label(text="Global Settings", icon='WORLD')
        row.prop(props, "show_global_help", text="", icon='QUESTION')

        split = box.split()

        # Left column
        col1 = split.column(align=True)
        col1.use_property_split = True
        col1.prop(props, "base_z_offset", text="BH")
        col1.prop(props, "layer_spacing", text="LG")

        # Right column  
        col2 = split.column(align=True)
        col2.use_property_split = True
        col2.prop(props, "bevel_depth", text="BD")
        col2.prop(props, "bevel_resolution", text="BR")
        col2.prop(props, "use_cyclic", text="UC")
        
# Layer Tools Panel 
class VECTART_PT_LayerTools(Panel):
    bl_label = "Layer Tools"
    bl_idname = "VECTART_PT_layer_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VectArt"
    bl_parent_id = "VECTART_PT_layer_panel"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.vectart_props

        # Active layer settings 
        if props.layers and len(props.layers) > 0:
            active_layer = props.layers[props.active_layer_index]
            box = layout.box()
            row = box.row()
            row.label(text=f"Layer Settings: {active_layer.name}", icon='OPTIONS')
            
            col = box.column(align=True)
            col.use_property_split = True
            col.prop(active_layer.settings, "scale", text="Scale")
            col.prop(active_layer.settings, "extrude_height", text="Extrude")
            col.prop(active_layer.settings, "z_offset", text="Z Offset")
            
            # Layer info 
            curves = get_layer_curves(props.active_layer_index)
            row = box.row()
            row.label(text=f"Curves: {len(curves)}", icon='CURVE_DATA')

        # Grouping Tools Box 
        box = layout.box()
        row = box.row()
        row.label(text="Grouping Tools", icon='EMPTY_AXIS')
        
        # Empty Settings 
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(props, "empty_type", text="")
        row.prop(props, "empty_name", text="")
        
        # Add size control 
        if context.active_object and context.active_object.type == 'EMPTY':
            col.prop(context.active_object, "empty_display_size", text="Size")
        else:
            col.label(text="Select an empty to adjust size", icon='INFO')
        
        # Create Empty Button 
        col = box.column(align=True)
        col.scale_y = 1.2
        col.operator("object.create_empty", 
                    icon='EMPTY_DATA', 
                    text="Create Empty Parent")

        # Layer operations 
        if len(props.layers) > 0:
            box = layout.box()
            row = box.row()
            row.label(text="Layer Operations", icon='TOOL_SETTINGS')
            
            row = box.row(align=True)
            row.scale_y = 1.2
            row.operator("object.select_layer_curves", icon='SELECT_SET')
            row.operator("object.assign_to_layer", icon='LAYER_ACTIVE')


class VECTART_MT_SelectionMenu(Menu):
    bl_label = "VectArt Selection"
    bl_idname = "VECTART_MT_selection_menu"

    def draw(self, context):
        layout = self.layout
        
        # Curve Selection
        layout.label(text="Curve Selection", icon='CURVE_DATA')
        layout.operator(
            "object.select_all_curves", 
            text="Select All Curves in Collection", 
            icon='RESTRICT_SELECT_OFF'
        )
        layout.operator(
            "object.select_layer_curves", 
            text="Select Layer Curves", 
            icon='LAYER_ACTIVE'
        )
        
        layout.separator()

        layout.operator(
            "object.assign_to_layer", 
            icon='LAYER_ACTIVE'
        )

        layout.separator()

        layout.operator(
            "object.create_empty", 
                    icon='EMPTY_DATA', 
                    text="Create Empty Parent"
        )
        
        # Focus
        layout.operator(
            "object.focus_selected", 
            text="Focus Selected", 
            icon='ZOOM_SELECTED'
        )
        
class VECTART_PT_SVGEditorPanel(Panel):
    bl_label = "SVG Editor Link"
    bl_idname = "VECTART_PT_svg_editor"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VectArt'

    def draw(self, context):
        layout = self.layout
        props = context.scene.vectart_props

        box = layout.box()
        box.label(text="SVG Editor Connection", icon='GREASEPENCIL')

        # Use grid for editor type/path
        grid = box.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=False, align=True)
        grid.prop(props, "svg_editor_type", text="Editor")
        grid.prop(props, "svg_editor_path", text="Path")

        # Use grid for main actions
        grid2 = layout.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=False, align=True)

        grid2.operator("object.edit_svg", icon='OUTLINER_OB_GREASEPENCIL', text="Edit SVG")
        grid2.operator("object.reimport_edited_svg", icon='FILE_REFRESH', text="Refresh & Reimport")

class VECTART_PT_GlobalSettingsHelp(Panel):
    bl_label = "Global Settings Help"
    bl_idname = "VECTART_PT_global_settings_help"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VectArt"
    bl_parent_id = "VECTART_PT_layer_panel"

    @classmethod
    def poll(cls, context):
        # Only show if the toggle is active
        props = context.scene.vectart_props
        return getattr(props, "show_global_help", False)
    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Abbreviations:", icon='INFO')
        box.label(text="BH = Base Height")
        box.label(text="LG = Layer Gap")
        box.label(text="BD = Bevel Depth")
        box.label(text="BR = Bevel Resolution")
        box.label(text="UC = Use Cyclic")

def draw_selection_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.menu(VECTART_MT_SelectionMenu.bl_idname, icon='RESTRICT_SELECT_OFF')
    

def clear_previews():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

# Registration
classes = (
    VectartUpdateSettings,
    VectartAddonPreferences,
    VectartLayerSettings,
    VectartLayerItem,
    VectartFolderItem,
    VectartLibraryProperties,
    VectartProperties,
    VECTART_OT_ImportSVG,
    VECTART_OT_LiveUpdate,
    VECTART_OT_ImportLibrarySVG,
    VECTART_OT_RefreshLibrary,
    VECTART_OT_AddLayer,
    VECTART_OT_RemoveLayer,
    VECTART_OT_ClearLayers,
    VECTART_OT_ConvertAndClear,
    VECTART_OT_MoveLayers,
    VECTART_UL_LayerList,
    VECTART_PT_LibraryPanel,
    VECTART_PT_PreviewPanel,
    VECTART_PT_LayerPanel,
    VECTART_PT_GlobalSettingsHelp,
    VECTART_MT_SelectionMenu,
    VECTART_OT_SelectLayerCurves,
    VECTART_OT_SelectAllCurves,
    VECTART_OT_SelectLayer,
    VECTART_OT_FocusSelected,
    VECTART_OT_AssignToLayer,
    VECTART_OT_DuplicateLayer,
    VECTART_PT_LayerTools,
    VECTART_OT_SplitToLayers,
    VECTART_OT_CreateEmpty,
    VECTART_OT_EditSVG,
    VECTART_OT_ReimportEditedSVG,
    VECTART_PT_SVGEditorPanel
    
)

def register():
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_selection_menu)
    """Register all classes and properties"""
    # Register classes
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"Error registering {cls.__name__}: {str(e)}")
            raise

    # Register properties
    try:
        bpy.types.Scene.vectart_library_props = PointerProperty(type=VectartLibraryProperties)
        bpy.types.Scene.vectart_props = PointerProperty(type=VectartProperties)
        bpy.types.Scene.vectart_update_settings = PointerProperty(type=VectartUpdateSettings)
    except Exception as e:
        print(f"Error registering properties: {str(e)}")
        raise

    # Make sure update_curve_properties is available
    if "update_curve_properties" not in globals():
        globals()["update_curve_properties"] = update_curve_properties
    
    # Initialize preview collection
    try:
        pcoll = bpy.utils.previews.new()
        preview_collections["vectart_previews"] = pcoll
        pcoll.enum_items = []
    except Exception as e:
        print(f"Error initializing preview collection: {str(e)}")
        raise

    # Register handlers
    try:
        if load_handler not in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.append(load_handler)
    except Exception as e:
        print(f"Error registering handlers: {str(e)}")
        raise

    # Initialize operator states
    try:
        VECTART_OT_RefreshLibrary._is_auto_refresh = False
        VECTART_OT_RefreshLibrary._timer = None
    except Exception as e:
        print(f"Error initializing operator states: {str(e)}")
        raise

    print("VectArt Add-on successfully registered")


def unregister():
    """Unregister all classes and properties"""
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_selection_menu)
    # Remove handlers first
    try:
        if load_handler in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(load_handler)
    except Exception as e:
        print(f"Error removing handlers: {str(e)}")

    # Clear previews
    try:
        for pcoll in preview_collections.values():
            bpy.utils.previews.remove(pcoll)
        preview_collections.clear()
    except Exception as e:
        print(f"Error clearing previews: {str(e)}")

    # Stop auto-refresh if active
    try:
        if hasattr(VECTART_OT_RefreshLibrary, '_is_auto_refresh') and VECTART_OT_RefreshLibrary._is_auto_refresh:
            VECTART_OT_RefreshLibrary._is_auto_refresh = False
        if hasattr(VECTART_OT_RefreshLibrary, '_timer') and VECTART_OT_RefreshLibrary._timer:
            bpy.context.window_manager.event_timer_remove(VECTART_OT_RefreshLibrary._timer)
            VECTART_OT_RefreshLibrary._timer = None
    except Exception as e:
        print(f"Error stopping auto-refresh: {str(e)}")

    # Remove keymaps if any
    try:
        # Add keymap removal code here if you have any
        pass
    except Exception as e:
        print(f"Error removing keymaps: {str(e)}")

    # Remove properties
    try:
        del bpy.types.Scene.vectart_update_settings
        del bpy.types.Scene.vectart_library_props
        del bpy.types.Scene.vectart_props
    except Exception as e:
        print(f"Error removing properties: {str(e)}")

    # Unregister classes in reverse order
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"Error unregistering {cls.__name__}: {str(e)}")

    print("VectArt Add-on successfully unregistered")


if __name__ == "__main__":
    register()
