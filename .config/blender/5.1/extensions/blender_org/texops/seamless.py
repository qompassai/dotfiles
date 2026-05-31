"""
Seamless Texture Generator Module for TexOps
Convert non-tiling textures into seamless/tileable textures
Uses edge-blend approach that preserves texture center
"""

import bpy
import numpy as np
import os

from . import core


# ============================================================================
# Core Seamless Functions
# ============================================================================

def pre_average(image_data, intensity=20, radius=10):
    """
    Pre-average dark and light areas to reduce visible seams from uneven lighting.
    
    This applies local contrast normalization - it evens out brightness variations
    across the image so that when edges are blended, there's less mismatch.
    
    Args:
        image_data: (H, W, 4) RGBA image as float32 [0-1]
        intensity: Strength of averaging (0-100, 0=disabled)
        radius: Size of local averaging window (1-20)
    
    Returns:
        (H, W, 4) pre-averaged RGBA image
    """
    if intensity <= 0:
        return image_data
    
    h, w, c = image_data.shape
    result = image_data.copy()
    
    # Clamp parameters
    intensity = np.clip(intensity, 0, 100) / 100.0
    radius = max(1, min(radius, 20))
    
    # Box blur kernel size
    kernel_size = radius * 2 + 1
    
    for ch in range(3):  # RGB only, not alpha
        channel = image_data[:, :, ch]
        
        # Pad with reflected values - need radius+1 for cumsum indexing
        padded = np.pad(channel, radius + 1, mode='reflect')
        
        # Cumulative sum for fast box blur (integral image)
        cum = np.cumsum(np.cumsum(padded, axis=0), axis=1)
        
        # Box blur using integral image
        # For output pixel (y,x), sum the kernel_size x kernel_size region
        local_mean = (
            cum[kernel_size:kernel_size + h, kernel_size:kernel_size + w] - 
            cum[:h, kernel_size:kernel_size + w] - 
            cum[kernel_size:kernel_size + h, :w] + 
            cum[:h, :w]
        ) / (kernel_size * kernel_size)
        
        # Global mean
        global_mean = np.mean(channel)
        
        # Blend towards normalized: push local variations toward global mean
        # deviation = how far pixel is from local average
        # normalized = global_mean + deviation (same relative contrast, but centered on global mean)
        deviation = channel - local_mean
        normalized = global_mean + deviation
        
        # Blend between original and normalized based on intensity
        result[:, :, ch] = channel * (1.0 - intensity) + normalized * intensity
    
    result[:, :, :3] = np.clip(result[:, :, :3], 0.0, 1.0)
    return result.astype(np.float32)


def create_edge_blend_mask_1d(size, blend_pixels):
    """
    Create a 1D blend mask: 1.0 at edges, 0.0 in center region.
    """
    blend_pixels = max(blend_pixels, 1)
    idx = np.arange(size, dtype=np.float32)
    dist_from_edge = np.minimum(idx, (size - 1) - idx)
    mask = np.clip(dist_from_edge / blend_pixels, 0.0, 1.0)
    mask = mask * mask * (3.0 - 2.0 * mask)  # smoothstep
    return 1.0 - mask


def make_seamless(image_data, overlap=0.25):
    """
    Make texture seamless using smooth edge blending.
    
    Two-pass approach that blends only at edges:
    1. Horizontal pass: blend left/right edges with 50% horizontally-shifted content
    2. Vertical pass: blend top/bottom edges with 50% vertically-shifted content
    
    Args:
        image_data: (H, W, 4) RGBA image as float32 [0-1]
        overlap: Fraction of each edge used for blending
    
    Returns:
        (H, W, 4) seamless RGBA image
    """
    h, w, c = image_data.shape
    half_h, half_w = h // 2, w // 2
    
    blend_h = max(int(h * overlap), 1)
    blend_w = max(int(w * overlap), 1)
    
    # Pass 1: Horizontal
    h_offset = np.roll(image_data, half_w, axis=1)
    h_mask = create_edge_blend_mask_1d(w, blend_w)[np.newaxis, :, np.newaxis]
    h_seamless = image_data * (1.0 - h_mask) + h_offset * h_mask
    
    # Pass 2: Vertical
    v_offset = np.roll(h_seamless, half_h, axis=0)
    v_mask = create_edge_blend_mask_1d(h, blend_h)[:, np.newaxis, np.newaxis]
    result = h_seamless * (1.0 - v_mask) + v_offset * v_mask
    
    return result.astype(np.float32)


def create_tiled_preview(image_data, tile_count=2):
    """
    Create a tiled preview of the texture to visually check for seams.
    
    Args:
        image_data: (H, W, 4) RGBA image
        tile_count: Number of tiles in each direction (2 = 2x2 grid)
    
    Returns:
        (H*tile_count, W*tile_count, 4) tiled preview image
    """
    h, w, c = image_data.shape
    out_h = h * tile_count
    out_w = w * tile_count
    
    # Use np.tile for efficient tiling
    output = np.tile(image_data, (tile_count, tile_count, 1))
    
    return output.astype(np.float32)


def detect_color_mode(image_data):
    """
    Detect appropriate color mode from image data.
    
    Args:
        image_data: (H, W, 4) RGBA image
    
    Returns:
        'BW' if grayscale, 'RGB' if no alpha variation, 'RGBA' if alpha varies
    """
    # Check if alpha channel varies (not all 1.0 or all same value)
    alpha = image_data[:, :, 3]
    alpha_varies = np.ptp(alpha) > 0.01  # ptp = max - min
    
    # Check if grayscale (R ≈ G ≈ B)
    r, g, b = image_data[:, :, 0], image_data[:, :, 1], image_data[:, :, 2]
    is_grayscale = (np.allclose(r, g, atol=0.01) and np.allclose(g, b, atol=0.01))
    
    if alpha_varies:
        return 'RGBA'
    elif is_grayscale:
        return 'BW'
    else:
        return 'RGB'


# ============================================================================
# Properties
# ============================================================================

get_depth_items = core.make_depth_items_callback("texops_seamless")
_aspect = core.AspectRatioHelper()


class Seamless_Properties(bpy.types.PropertyGroup):
    # Input mode
    input_mode: bpy.props.EnumProperty(
        name="Input Mode",
        items=[('SINGLE', "Single", "Process single image"),
               ('BATCH', "Batch", "Process all images from folder")],
        default='SINGLE'
    )
    input_image: bpy.props.StringProperty(name="Input Image", default="")
    input_folder: bpy.props.StringProperty(name="Input Folder", default="//", subtype='DIR_PATH')
    
    # Algorithm parameters
    overlap: bpy.props.FloatProperty(
        name="Blend Zone",
        description="Size of edge blend zone as fraction of image (higher = smoother but more center content affected)",
        default=0.25,
        min=0.05,
        max=0.5,
        subtype='FACTOR'
    )
    
    # Pre-averaging settings
    pre_average_intensity: bpy.props.IntProperty(
        name="Intensity",
        description="Strength of brightness normalization (0 = disabled)",
        default=0,
        min=0,
        max=100,
        subtype='PERCENTAGE'
    )
    pre_average_radius: bpy.props.IntProperty(
        name="Radius",
        description="Size of local averaging window",
        default=10,
        min=1,
        max=20
    )
    
    # Output settings
    output_name: bpy.props.StringProperty(name="Output Name", default="")
    output_suffix: bpy.props.StringProperty(name="Suffix", default="_Seamless",
                                            description="Suffix added to output filename")
    output_folder: bpy.props.StringProperty(
        name="Output Folder",
        default="//",
        subtype='DIR_PATH'
    )
    output_width: bpy.props.IntProperty(
        name="Width",
        default=0,
        min=0,
        description="Output width (0 = same as input)",
        update=lambda s, c: _aspect.update_width(s)
    )
    output_height: bpy.props.IntProperty(
        name="Height",
        default=0,
        min=0,
        description="Output height (0 = same as input)",
        update=lambda s, c: _aspect.update_height(s)
    )
    lock_aspect: bpy.props.BoolProperty(
        name="Lock Aspect Ratio",
        default=True,
        update=lambda s, c: _aspect.update_lock(s)
    )
    file_format: bpy.props.EnumProperty(
        name="Format",
        items=core.get_format_items,
        update=core.update_depth_for_format
    )
    color_depth: bpy.props.EnumProperty(
        name="Depth",
        items=get_depth_items
    )


# ============================================================================
# Operators
# ============================================================================

class TEXOPS_OT_Seamless_LoadImage(core.LoadImageOperatorBase):
    bl_idname = "texops.seamless_load_image"
    bl_label = "Load Image"
    image_property = "input_image"
    
    def get_props(self, context):
        return context.scene.texops_seamless


class TEXOPS_OT_Seamless_Preview(core.ShowImageOperatorBase):
    bl_idname = "texops.seamless_preview"
    bl_label = "Preview"
    image_property = "input_image"
    
    def get_props(self, context):
        return context.scene.texops_seamless


class TEXOPS_OT_Seamless_PreviewTile(bpy.types.Operator):
    """Create 2x2 tiled preview to check seamlessness"""
    bl_idname = "texops.seamless_preview_tile"
    bl_label = "Preview Tiling"
    bl_options = {'REGISTER'}
    
    @core.with_error_handling
    def execute(self, context):
        space = context.space_data
        if not space or space.type != 'IMAGE_EDITOR' or not space.image:
            self.report({'ERROR'}, "No image in editor")
            return {'CANCELLED'}
        
        img = space.image
        
        # Read image data
        image_data, width, height = core.read_pixels(img)
        
        # Create 2x2 tiled preview
        preview = create_tiled_preview(image_data, tile_count=2)
        
        # Determine colorspace from input
        colorspace = img.colorspace_settings.name
        
        # Create preview image
        preview_name = "_Seamless_TilePreview"
        preview_img = core.create_image(preview_name, preview, colorspace)
        core.set_image_editor_image(context, preview_img)
        
        out_h, out_w = preview.shape[:2]
        self.report({'INFO'}, f"Created 2x2 tile preview ({out_w}x{out_h})")
        return {'FINISHED'}


class TEXOPS_OT_Seamless_Generate(core.BatchConfirmMixin, bpy.types.Operator):
    """Generate seamless texture"""
    bl_idname = "texops.seamless_generate"
    bl_label = "Generate"
    bl_options = {'REGISTER'}
    
    def get_props(self, context):
        return context.scene.texops_seamless
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_seamless
        if props.input_mode == 'BATCH':
            return self.execute_batch(context, props)
        return self.execute_single(context, props)
    
    def process_image(self, image_data, props):
        """Apply seamless processing with optional pre-averaging."""
        # Apply pre-averaging if enabled
        if props.pre_average_intensity > 0:
            image_data = pre_average(
                image_data, 
                intensity=props.pre_average_intensity,
                radius=props.pre_average_radius
            )
        
        # Make seamless
        return make_seamless(image_data, props.overlap)
    
    def execute_single(self, context, props):
        if not props.input_image:
            self.report({'ERROR'}, "No input image selected")
            return {'CANCELLED'}
        
        img = bpy.data.images.get(props.input_image)
        if not img:
            self.report({'ERROR'}, "Input image not found")
            return {'CANCELLED'}
        
        # Read image data
        image_data, width, height = core.read_pixels(img)
        
        # Detect color mode from input
        color_mode = detect_color_mode(image_data)
        
        # Process
        result = self.process_image(image_data, props)
        
        # Resize if needed
        out_h, out_w = result.shape[:2]
        target_w = props.output_width if props.output_width > 0 else out_w
        target_h = props.output_height if props.output_height > 0 else out_h
        
        if (target_w, target_h) != (out_w, out_h):
            result = core.resize_bilinear(result, target_h, target_w)
            out_w, out_h = target_w, target_h
        
        # Determine colorspace from input
        colorspace = img.colorspace_settings.name
        
        # Create and save output
        output_name = (props.output_name if props.output_name else img.name.rsplit('.', 1)[0]) + props.output_suffix
        output_img = core.create_image(output_name, result, colorspace)
        filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
        core.save_image(output_img, filepath, props.file_format, color_mode, props.color_depth)
        core.set_image_editor_image(context, output_img)
        
        self.report({'INFO'}, f"Created {output_name} ({out_w}x{out_h})")
        return {'FINISHED'}
    
    def execute_batch(self, context, props):
        image_files = core.get_images_from_folder(props.input_folder)
        
        if not image_files:
            self.report({'ERROR'}, "No images found in folder")
            return {'CANCELLED'}
        
        success = 0
        last_output = None
        
        with core.progress(context.window_manager) as update:
            for i, filepath in enumerate(image_files):
                update(int(100 * i / len(image_files)))
                
                img = core.load_image(filepath)
                if not img:
                    continue
                
                # Read and process
                image_data, width, height = core.read_pixels(img)
                
                # Detect color mode from input
                color_mode = detect_color_mode(image_data)
                
                result = self.process_image(image_data, props)
                
                # Resize if needed
                out_h, out_w = result.shape[:2]
                target_w = props.output_width if props.output_width > 0 else out_w
                target_h = props.output_height if props.output_height > 0 else out_h
                
                if (target_w, target_h) != (out_w, out_h):
                    result = core.resize_bilinear(result, target_h, target_w)
                
                # Determine colorspace
                colorspace = img.colorspace_settings.name
                
                # Generate output
                base_name = os.path.splitext(os.path.basename(filepath))[0]
                output_name = base_name + props.output_suffix
                output_img = core.create_image(output_name, result, colorspace)
                out_path = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                core.save_image(output_img, out_path, props.file_format, color_mode, props.color_depth)
                last_output = output_img
                success += 1
        
        if last_output:
            core.set_image_editor_image(context, last_output)
        
        self.report({'INFO'}, f"Processed {success}/{len(image_files)} images")
        return {'FINISHED'}


# ============================================================================
# UI Panel
# ============================================================================

class TEXOPS_PT_Seamless(bpy.types.Panel):
    bl_label = "Seamless Generator"
    bl_idname = "TEXOPS_PT_seamless"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'TexOps'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.texops_seamless
        
        # Input section
        box = layout.box()
        box.label(text="Input:", icon='IMAGE_DATA')
        
        row = box.row()
        row.prop(props, "input_mode", expand=True)
        
        if props.input_mode == 'SINGLE':
            row = box.row(align=True)
            row.prop_search(props, "input_image", bpy.data, "images", text="")
            row.operator("texops.seamless_load_image", text="", icon='FILEBROWSER')
            sub = row.row(align=True)
            sub.enabled = bool(props.input_image)
            sub.operator("texops.seamless_preview", text="", icon='HIDE_OFF')
        else:
            box.prop(props, "input_folder", text="")
            image_count = len(core.get_images_from_folder(props.input_folder))
            box.label(
                text=f"{image_count} images" if image_count else "No images found",
                icon='INFO' if image_count else 'ERROR'
            )
        
        # Parameters section
        layout.separator()
        box = layout.box()
        box.label(text="Parameters:", icon='PREFERENCES')
        
        box.prop(props, "overlap", slider=True)
        
        # Pre-averaging subsection
        box.label(text="Pre-Averaging:")
        row = box.row(align=True)
        row.prop(props, "pre_average_intensity", text="Intensity")
        sub = row.row(align=True)
        sub.enabled = props.pre_average_intensity > 0
        sub.prop(props, "pre_average_radius", text="Radius")
        
        # Output section
        layout.separator()
        out_box = layout.box()
        out_box.label(text="Output:", icon='FILE_IMAGE')
        if props.input_mode == 'SINGLE':
            out_box.prop(props, "output_name")
        out_box.prop(props, "output_suffix")
        out_box.prop(props, "output_folder", text="")
        
        row = out_box.row(align=True)
        row.prop(props, "lock_aspect", text="", icon='LOCKED' if props.lock_aspect else 'UNLOCKED')
        row.prop(props, "output_width", text="Width")
        row.prop(props, "output_height", text="Height")
        
        row = out_box.row(align=True)
        row.prop(props, "file_format", text="")
        row.prop(props, "color_depth", text="")
        
        # Generate button
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        row.operator("texops.seamless_generate", icon='MOD_UVPROJECT')
    
        # Preview tiling button
        row = layout.row()
        row.scale_y = 1.5
        row.operator("texops.seamless_preview_tile", text="Preview Tiling", icon='HIDE_OFF')


# ============================================================================
# Registration
# ============================================================================

classes = (
    Seamless_Properties,
    TEXOPS_OT_Seamless_LoadImage,
    TEXOPS_OT_Seamless_Preview,
    TEXOPS_OT_Seamless_PreviewTile,
    TEXOPS_OT_Seamless_Generate,
    TEXOPS_PT_Seamless,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_seamless = bpy.props.PointerProperty(type=Seamless_Properties)


def unregister():
    del bpy.types.Scene.texops_seamless
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)