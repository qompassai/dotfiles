"""
Resolution Packer Module for TexOps
Split a single image into quadrants and pack into RGBA channels at reduced resolution.
Supports multiple reduction modes with bit packing for higher compression.

Reduction modes by bit depth:
- 8-bit:  1/2 (8-bit), 1/4 (2-bit)
- 16-bit: 1/2 (16-bit), 1/4 (4-bit), 1/8 (1-bit)
- 32-bit: 1/2 (32-bit), 1/4 (8-bit), 1/8 (2-bit)
"""

import bpy
import numpy as np
import os

from . import core


# ============================================================================
# Constants
# ============================================================================

# Reduction mode info: (grid_size, quadrants_per_channel, bits_per_quadrant by bit_mode)
REDUCTION_MODES = {
    '1/2': {'grid': 2, 'quadrants': 4, 'bits': {'8BIT': 8, '16BIT': 16, '32BIT': 32}},
    '1/4': {'grid': 4, 'quadrants': 16, 'bits': {'8BIT': 2, '16BIT': 4, '32BIT': 8}},
    '1/8': {'grid': 8, 'quadrants': 64, 'bits': {'8BIT': 0, '16BIT': 1, '32BIT': 2}},
}

BIT_MODE_DEPTH = {'8BIT': 8, '16BIT': 16, '32BIT': 32}


# ============================================================================
# Core Functions
# ============================================================================

def get_available_reduction_modes(bit_mode):
    """Get reduction modes available for the given bit mode."""
    modes = []
    for mode_name, mode_info in REDUCTION_MODES.items():
        bits = mode_info['bits'].get(bit_mode, 0)
        if bits >= 1:
            modes.append(mode_name)
    return modes


def get_reduction_info(bit_mode, reduction_mode):
    """Get grid size and bits per quadrant for given settings."""
    mode_info = REDUCTION_MODES.get(reduction_mode, REDUCTION_MODES['1/2'])
    grid = mode_info['grid']
    bits = mode_info['bits'].get(bit_mode, 8)
    return grid, bits


def split_into_quadrants(image_data, grid_size):
    """Split image into grid_size × grid_size quadrants."""
    if image_data.ndim == 3:
        image_data = image_data[:, :, 0]
    
    h, w = image_data.shape
    qh, qw = h // grid_size, w // grid_size
    
    quadrants = []
    for row in range(grid_size):
        for col in range(grid_size):
            y_start, y_end = row * qh, (row + 1) * qh
            x_start, x_end = col * qw, (col + 1) * qw
            quadrants.append(image_data[y_start:y_end, x_start:x_end])
    
    return quadrants, qh, qw


def pack_quadrants_to_channel(quadrants, bits_per_quadrant, dither_mode):
    """Pack multiple quadrants into a single channel using bit packing."""
    height, width = quadrants[0].shape
    result = np.zeros((height, width), dtype=np.uint32)
    bit_offset = 0
    
    for quad in quadrants:
        # Apply dithering if needed
        quad = core.apply_dither(quad.astype(np.float32), bits_per_quadrant, dither_mode, height, width)
        quantized = core.quantize(quad, bits_per_quadrant)
        result |= (quantized << bit_offset)
        bit_offset += bits_per_quadrant
    
    # Normalize to 0-1 range based on total bits used
    total_bits = bit_offset
    max_val = (1 << total_bits) - 1
    return result.astype(np.float32) / max_val


def pack_image(image_data, bit_mode, reduction_mode, dither_mode):
    """
    Pack image into RGBA using specified reduction mode.
    
    Returns (packed_rgba, output_width, output_height, bits_per_quadrant)
    """
    grid_size, bits_per_quadrant = get_reduction_info(bit_mode, reduction_mode)
    quadrants, qh, qw = split_into_quadrants(image_data, grid_size)
    
    total_quadrants = grid_size * grid_size
    quadrants_per_channel = total_quadrants // 4
    
    output = np.zeros((qh, qw, 4), dtype=np.float32)
    
    for ch in range(4):
        start_idx = ch * quadrants_per_channel
        end_idx = start_idx + quadrants_per_channel
        channel_quadrants = quadrants[start_idx:end_idx]
        
        if quadrants_per_channel == 1:
            # 1/2 mode: single quadrant per channel, no bit packing
            quad = channel_quadrants[0].astype(np.float32)
            output[:, :, ch] = np.clip(quad, 0, 1)
        else:
            # 1/4 or 1/8 mode: multiple quadrants bit-packed
            output[:, :, ch] = pack_quadrants_to_channel(
                channel_quadrants, bits_per_quadrant, dither_mode
            )
    
    return output, qw, qh, bits_per_quadrant


def resize_if_needed(packed, props):
    """Resize packed result if custom dimensions specified."""
    out_h, out_w = packed.shape[:2]
    target_w = props.output_width if props.output_width > 0 else out_w
    target_h = props.output_height if props.output_height > 0 else out_h
    
    if (target_w, target_h) != (out_w, out_h):
        return core.resize_bilinear(packed, target_h, target_w), target_w, target_h
    return packed, out_w, out_h


# ============================================================================
# Property Helpers
# ============================================================================

def get_reduction_mode_items(self, context):
    """Get available reduction modes for current bit mode."""
    props = context.scene.texops_resolution_packer
    bit_mode = props.bit_mode
    
    items = []
    for mode_name in ['1/2', '1/4', '1/8']:
        mode_info = REDUCTION_MODES[mode_name]
        bits = mode_info['bits'].get(bit_mode, 0)
        if bits >= 1:
            items.append((mode_name, mode_name, f"{mode_name} resolution, {bits}-bit per quadrant"))
    
    return items if items else [('1/2', '1/2', 'Half resolution')]


def get_format_items_for_bit_mode(self, context):
    """Get valid file formats based on bit mode."""
    props = context.scene.texops_resolution_packer
    bit_mode = props.bit_mode
    
    if bit_mode == '8BIT':
        return [
            ('PNG', "PNG", "8-bit PNG"),
            ('TARGA', "TGA", "8-bit Targa"),
            ('TIFF', "TIFF", "8-bit TIFF"),
        ]
    elif bit_mode == '16BIT':
        return [
            ('PNG', "PNG", "16-bit PNG"),
            ('TIFF', "TIFF", "16-bit TIFF"),
            ('OPEN_EXR', "EXR", "16-bit OpenEXR"),
        ]
    else:  # 32BIT
        return [
            ('OPEN_EXR', "EXR", "32-bit OpenEXR"),
        ]


def update_format_for_bit_mode(self, context):
    """Update file format when bit mode changes."""
    props = context.scene.texops_resolution_packer
    
    if props.bit_mode == '8BIT':
        if props.file_format not in ('PNG', 'TARGA', 'TIFF'):
            props.file_format = 'PNG'
    elif props.bit_mode == '16BIT':
        if props.file_format not in ('PNG', 'TIFF', 'OPEN_EXR'):
            props.file_format = 'PNG'
    else:  # 32BIT
        props.file_format = 'OPEN_EXR'


def get_color_depth_for_bit_mode(bit_mode, file_format):
    """Get appropriate color depth string for saving."""
    if file_format == 'OPEN_EXR':
        return '32' if bit_mode == '32BIT' else '16'
    elif bit_mode == '8BIT':
        return '8'
    else:
        return '16'


# ============================================================================
# Properties
# ============================================================================

_aspect = core.AspectRatioHelper()


class ResolutionPacker_Properties(bpy.types.PropertyGroup):
    bit_mode: bpy.props.EnumProperty(
        name="Bit Mode",
        items=[
            ('8BIT', "8-bit", "8 bits per channel"),
            ('16BIT', "16-bit", "16 bits per channel"),
            ('32BIT', "32-bit", "32 bits per channel (EXR)"),
        ],
        default='8BIT',
        update=update_format_for_bit_mode
    )
    
    reduction_mode: bpy.props.EnumProperty(
        name="Reduction",
        items=get_reduction_mode_items,
        default=0
    )
    
    input_mode: bpy.props.EnumProperty(
        name="Mode",
        items=[('SINGLE', "Single", "Pack single image"),
               ('BATCH', "Batch", "Pack all images from folder")],
        default='SINGLE'
    )
    
    input_image: bpy.props.StringProperty(name="Input Image", default="")
    input_channel: bpy.props.EnumProperty(name="Channel", items=core.CHANNEL_ITEMS, default='GRAY')
    input_folder: bpy.props.StringProperty(name="Input Folder", default="//", subtype='DIR_PATH')
    
    dither_mode: bpy.props.EnumProperty(
        name="Dithering",
        items=[
            ('NONE', "None", "No dithering"),
            ('ORDERED', "Ordered", "Bayer matrix (deterministic, tileable)"),
            ('NOISE', "Noise", "Random noise"),
            ('BLUE', "Blue Noise", "Blue noise (best quality)"),
        ],
        default='ORDERED'
    )
    
    output_name: bpy.props.StringProperty(name="Output Name", default="Packed")
    output_suffix: bpy.props.StringProperty(name="Suffix", default="_ResPacked",
                                            description="Suffix added to output filename")
    output_folder: bpy.props.StringProperty(name="Output Folder", default="//", subtype='DIR_PATH')
    output_width: bpy.props.IntProperty(
        name="Width", default=0, min=0, max=16384,
        description="Output width (0 = auto)",
        update=lambda s, c: _aspect.update_width(s)
    )
    output_height: bpy.props.IntProperty(
        name="Height", default=0, min=0, max=16384,
        description="Output height (0 = auto)",
        update=lambda s, c: _aspect.update_height(s)
    )
    lock_aspect: bpy.props.BoolProperty(
        name="Lock Aspect", default=True,
        update=lambda s, c: _aspect.update_lock(s)
    )
    file_format: bpy.props.EnumProperty(
        name="Format",
        items=get_format_items_for_bit_mode,
        default=0
    )


# ============================================================================
# Operators
# ============================================================================

class TEXOPS_OT_ResolutionPacker_LoadImage(core.LoadImageOperatorBase):
    bl_idname = "texops.resolution_load_image"
    bl_label = "Load Image"
    image_property = "input_image"
    
    def get_props(self, context):
        return context.scene.texops_resolution_packer


class TEXOPS_OT_ResolutionPacker_Preview(bpy.types.Operator):
    """Preview the selected input image"""
    bl_idname = "texops.resolution_preview"
    bl_label = "Preview Input"
    bl_options = {'INTERNAL'}
    
    def execute(self, context):
        props = context.scene.texops_resolution_packer
        if props.input_image:
            img = bpy.data.images.get(props.input_image)
            if img:
                core.set_image_editor_image(context, img)
        return {'FINISHED'}


class TEXOPS_OT_ResolutionPacker_Pack(core.BatchConfirmMixin, bpy.types.Operator):
    """Pack image quadrants into RGBA texture at reduced resolution"""
    bl_idname = "texops.resolution_pack"
    bl_label = "Pack"
    bl_options = {'REGISTER'}
    
    def get_props(self, context):
        return context.scene.texops_resolution_packer
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_resolution_packer
        if props.input_mode == 'BATCH':
            return self.execute_batch(context, props)
        return self.execute_single(context, props)
    
    def execute_single(self, context, props):
        img, result = core.get_input_image(props, self)
        if not img:
            return result
        
        width, height = img.size
        grid_size, _ = get_reduction_info(props.bit_mode, props.reduction_mode)
        
        if width % grid_size != 0 or height % grid_size != 0:
            self.report({'WARNING'}, f"Dimensions ({width}x{height}) not divisible by {grid_size}, cropping")
        
        data = core.extract_channel(img, props.input_channel, (height, width), 0.0)
        packed, out_w, out_h, bits = pack_image(data, props.bit_mode, props.reduction_mode, props.dither_mode)
        packed, out_w, out_h = resize_if_needed(packed, props)
        
        output_name = (props.output_name if props.output_name else img.name.rsplit('.', 1)[0]) + props.output_suffix
        use_float = props.bit_mode != '8BIT'
        output_img = core.create_image(output_name, packed, 'Non-Color', float_buffer=use_float)
        
        color_depth = get_color_depth_for_bit_mode(props.bit_mode, props.file_format)
        filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
        core.save_image(output_img, filepath, props.file_format, 'RGBA', color_depth, compression=0)
        core.set_image_editor_image(context, output_img)
        
        self.report({'INFO'}, f"Packed {width}x{height} -> {out_w}x{out_h} ({bits}-bit per quadrant)")
        return {'FINISHED'}
    
    def execute_batch(self, context, props):
        image_files = core.get_images_from_folder(props.input_folder)
        if not image_files:
            self.report({'ERROR'}, "No images found in folder")
            return {'CANCELLED'}
        
        suffix = props.output_suffix
        success = 0
        grid_size, bits = get_reduction_info(props.bit_mode, props.reduction_mode)
        color_depth = get_color_depth_for_bit_mode(props.bit_mode, props.file_format)
        use_float = props.bit_mode != '8BIT'
        
        with core.progress(context.window_manager) as update:
            for i, filepath in enumerate(image_files):
                update(int(100 * i / len(image_files)))
                
                img = core.load_image(filepath)
                if not img:
                    continue
                
                width, height = img.size
                data = core.extract_channel(img, props.input_channel, (height, width), 0.0)
                packed, _, _, _ = pack_image(data, props.bit_mode, props.reduction_mode, props.dither_mode)
                packed, _, _ = resize_if_needed(packed, props)
                
                base_name = os.path.splitext(os.path.basename(filepath))[0]
                output_name = base_name + suffix
                output_img = core.create_image(output_name, packed, 'Non-Color', float_buffer=use_float)
                out_path = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                core.save_image(output_img, out_path, props.file_format, 'RGBA', color_depth, compression=0)
                success += 1
        
        self.report({'INFO'}, f"Packed {success}/{len(image_files)} images ({bits}-bit per quadrant)")
        return {'FINISHED'}


# ============================================================================
# UI Panel
# ============================================================================

class TEXOPS_PT_ResolutionPacker(bpy.types.Panel):
    bl_label = "Resolution Packer"
    bl_idname = "TEXOPS_PT_resolution_packer"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'TexOps'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.texops_resolution_packer
        
        # Mode toggle
        row = layout.row()
        row.prop(props, "input_mode", expand=True)
        
        layout.separator()
        
        # Bit mode toggle
        row = layout.row()
        row.prop(props, "bit_mode", expand=True)
        
        # Reduction mode toggle
        row = layout.row()
        row.prop(props, "reduction_mode", expand=True)
        
        # Bit loss warning
        grid_size, bits = get_reduction_info(props.bit_mode, props.reduction_mode)
        if bits < 8:
            box = layout.box()
            levels = 1 << bits
            box.label(text=f"{bits}-bit precision ({levels} levels)", icon='INFO')
        
        layout.separator()
        
        # Input section
        box = layout.box()
        box.label(text="Input:", icon='IMAGE_DATA')
        
        if props.input_mode == 'SINGLE':
            row = box.row(align=True)
            row.prop_search(props, "input_image", bpy.data, "images", text="")
            row.operator("texops.resolution_load_image", text="", icon='FILEBROWSER')
            sub = row.row()
            sub.scale_x = 0.55
            sub.prop(props, "input_channel", text="")
            sub = row.row(align=True)
            sub.enabled = bool(props.input_image)
            sub.operator("texops.resolution_preview", text="", icon='HIDE_OFF')
            
            # Show resolution info
            if props.input_image:
                img = bpy.data.images.get(props.input_image)
                if img:
                    width, height = img.size
                    out_w = width // grid_size
                    out_h = height // grid_size
                    if props.output_width > 0:
                        out_w = props.output_width
                    if props.output_height > 0:
                        out_h = props.output_height
                    
                    info_row = box.row()
                    info_row.label(text=f"{width}x{height} -> {out_w}x{out_h}")
                    if width % grid_size != 0 or height % grid_size != 0:
                        info_row.label(text="", icon='ERROR')
        else:
            box.prop(props, "input_folder", text="")
            image_count = len(core.get_images_from_folder(props.input_folder))
            box.label(text=f"{image_count} images" if image_count else "No images found",
                     icon='INFO' if image_count else 'ERROR')
        
        layout.separator()
        
        # Output section
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
        row.prop(props, "dither_mode", text="")
        
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        row.operator("texops.resolution_pack", icon='EXPORT')


# ============================================================================
# Registration
# ============================================================================

classes = (
    ResolutionPacker_Properties,
    TEXOPS_OT_ResolutionPacker_LoadImage,
    TEXOPS_OT_ResolutionPacker_Preview,
    TEXOPS_OT_ResolutionPacker_Pack,
    TEXOPS_PT_ResolutionPacker,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_resolution_packer = bpy.props.PointerProperty(type=ResolutionPacker_Properties)

def unregister():
    del bpy.types.Scene.texops_resolution_packer
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)