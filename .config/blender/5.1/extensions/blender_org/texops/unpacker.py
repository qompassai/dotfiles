"""
Unpacker Module for TexOps
Unpack RGBA texture channels into separate grayscale images or reconstruct resolution-packed images
"""

import bpy
import numpy as np
import os

from . import core


# ============================================================================
# Unpacking Mode Definitions
# ============================================================================

UNPACKING_MODES = [
    ('CHANNEL_SPLIT', "Channel Split", "Split RGBA into separate grayscale images"),
    ('BIT_UNPACK', "Bit Unpack", "Unpack bit-packed textures from RGBA channels"),
    ('RESOLUTION_UNPACK', "Resolution Unpack", "Reconstruct image from resolution-packed RGBA"),
]


# ============================================================================
# Bit Unpacking - Matching bit_packer.py
# ============================================================================

BIT_MODE_DEPTH = {'8BIT': 8, '16BIT': 16, '32BIT': 32}

# Reduction mode info matching resolution_packer.py
REDUCTION_MODES = {
    '1/2': {'grid': 2, 'quadrants': 4, 'bits': {'8BIT': 8, '16BIT': 16, '32BIT': 32}},
    '1/4': {'grid': 4, 'quadrants': 16, 'bits': {'8BIT': 2, '16BIT': 4, '32BIT': 8}},
    '1/8': {'grid': 8, 'quadrants': 64, 'bits': {'8BIT': 0, '16BIT': 1, '32BIT': 2}},
}


def generate_bit_partitions(total_bits, num_textures):
    """Generate all valid ways to partition total_bits into num_textures parts."""
    if num_textures == 0:
        return [[]]
    if num_textures == 1:
        return [[total_bits]]
    
    partitions = []
    
    def partition(remaining_bits, parts_left, min_bits, current):
        if parts_left == 0:
            if remaining_bits == 0:
                partitions.append(current[:])
            return
        max_bits = remaining_bits - (parts_left - 1)
        for bits in range(max_bits, min_bits - 1, -1):
            current.append(bits)
            partition(remaining_bits - bits, parts_left - 1, 1, current)
            current.pop()
    
    partition(total_bits, num_textures, 1, [])
    return partitions


def format_bit_layout(bits):
    """Format bit layout as string."""
    if not bits:
        return ""
    parts = []
    current_val = bits[0]
    count = 1
    for i in range(1, len(bits)):
        if bits[i] == current_val:
            count += 1
        else:
            parts.append(f"{current_val} x{count}" if count > 1 else str(current_val))
            current_val = bits[i]
            count = 1
    parts.append(f"{current_val} x{count}" if count > 1 else str(current_val))
    return ' | '.join(parts)


def get_channel_bit_layout(props, channel):
    """Get the actual bit layout list for a channel."""
    tex_count = int(getattr(props, f'tex_count_{channel}', '0'))
    if tex_count == 0:
        return []
    layout_idx = int(getattr(props, f'bit_layout_{channel}', '0'))
    total_bits = BIT_MODE_DEPTH[props.bit_mode]
    partitions = generate_bit_partitions(total_bits, tex_count)
    if 0 <= layout_idx < len(partitions):
        return partitions[layout_idx]
    return []


# ============================================================================
# Core Unpacking Functions
# ============================================================================

def unpack_rgba_channels(image):
    """Unpack RGBA image into 4 separate grayscale images."""
    pixels, w, h = core.read_pixels(image)
    result = {}
    for i, channel in enumerate(['R', 'G', 'B', 'A']):
        gray = pixels[:, :, i]
        result[channel] = np.stack([gray, gray, gray, np.ones_like(gray)], axis=-1).astype(np.float32)
    return result


def unpack_bits_from_channel(packed_channel, bits_layout, bit_mode):
    """Unpack a single channel containing bit-packed data."""
    total_bits = BIT_MODE_DEPTH[bit_mode]
    if bit_mode == '8BIT':
        packed_int = (packed_channel * 255.0).astype(np.uint32)
    elif bit_mode == '16BIT':
        packed_int = (packed_channel * 65535.0).astype(np.uint32)
    else:
        packed_int = (packed_channel * 4294967295.0).astype(np.uint64)
    
    results = []
    bit_offset = 0
    for bits in bits_layout:
        mask = (1 << bits) - 1
        extracted = (packed_int >> bit_offset) & mask
        max_val = (1 << bits) - 1
        normalized = extracted.astype(np.float32) / max_val if max_val > 0 else extracted.astype(np.float32)
        results.append(normalized)
        bit_offset += bits
    return results


def unpack_bit_packed(image, channel_layouts, bit_mode):
    """Unpack bit-packed textures from all RGBA channels."""
    pixels, w, h = core.read_pixels(image)
    result = {}
    for ch_idx, (channel, bits_layout) in enumerate(zip('RGBA', channel_layouts)):
        if not bits_layout:
            continue
        channel_data = pixels[:, :, ch_idx]
        unpacked_list = unpack_bits_from_channel(channel_data, bits_layout, bit_mode)
        for tex_idx, tex_data in enumerate(unpacked_list):
            key = f"{channel}{tex_idx}"
            rgba = np.stack([tex_data, tex_data, tex_data, np.ones_like(tex_data)], axis=-1).astype(np.float32)
            result[key] = rgba
    return result


def unpack_resolution_packed(image, bit_mode, reduction_mode):
    """Reconstruct full resolution image from resolution-packed RGBA."""
    pixels, w, h = core.read_pixels(image)
    mode_info = REDUCTION_MODES[reduction_mode]
    grid_size = mode_info['grid']
    bits_per_quadrant = mode_info['bits'][bit_mode]
    quadrants_per_channel = (grid_size * grid_size) // 4
    
    # Use bit_mode to determine scale factor (how the data was packed)
    if bit_mode == '8BIT':
        scale_factor = 255.0
    elif bit_mode == '16BIT':
        scale_factor = 65535.0
    else:  # 32BIT
        scale_factor = 4294967295.0
    
    # For 1/2 mode (no bit packing), each channel stores a full quadrant
    if quadrants_per_channel == 1:
        all_quadrants = [pixels[:, :, ch_idx] for ch_idx in range(4)]
    else:
        # For 1/4 and 1/8 modes, we need bit unpacking
        all_quadrants = []
        for ch_idx in range(4):
            channel_data = pixels[:, :, ch_idx]
            unpacked = unpack_quadrants_from_channel_scaled(
                channel_data, quadrants_per_channel, bits_per_quadrant, scale_factor
            )
            all_quadrants.extend(unpacked)
    
    full_h, full_w = h * grid_size, w * grid_size
    reconstructed = np.zeros((full_h, full_w), dtype=np.float32)
    quad_idx = 0
    for row in range(grid_size):
        for col in range(grid_size):
            y_start, y_end = row * h, (row + 1) * h
            x_start, x_end = col * w, (col + 1) * w
            reconstructed[y_start:y_end, x_start:x_end] = all_quadrants[quad_idx]
            quad_idx += 1
    
    return np.stack([reconstructed, reconstructed, reconstructed, np.ones_like(reconstructed)], axis=-1).astype(np.float32)


def unpack_quadrants_from_channel_scaled(packed_channel, num_quadrants, bits_per_quadrant, scale_factor):
    """Unpack multiple quadrants from a single channel using explicit scale factor."""
    packed_int = (packed_channel * scale_factor + 0.5).astype(np.uint64 if scale_factor > 65535 else np.uint32)
    
    results = []
    bit_offset = 0
    for _ in range(num_quadrants):
        mask = (1 << bits_per_quadrant) - 1
        extracted = (packed_int >> bit_offset) & mask
        max_val = (1 << bits_per_quadrant) - 1
        normalized = extracted.astype(np.float32) / max_val if max_val > 0 else extracted.astype(np.float32)
        results.append(normalized)
        bit_offset += bits_per_quadrant
    return results


# ============================================================================
# Property Callbacks
# ============================================================================

def get_texture_count_items(self, context):
    """Generate texture count dropdown based on bit mode."""
    props = context.scene.texops_unpacker
    max_textures = BIT_MODE_DEPTH.get(props.bit_mode, 8)
    return [(str(i), str(i), f"{i} textures") for i in range(max_textures + 1)]


def get_bit_layout_items_for_channel(context, channel):
    """Generate bit layout combinations based on texture count for specific channel."""
    props = context.scene.texops_unpacker
    tex_count_str = getattr(props, f'tex_count_{channel}', '0')
    tex_count = int(tex_count_str)
    if tex_count == 0:
        return [('0', 'N/A', 'No textures')]
    total_bits = BIT_MODE_DEPTH[props.bit_mode]
    partitions = generate_bit_partitions(total_bits, tex_count)
    items = []
    for i, partition in enumerate(partitions):
        layout_str = format_bit_layout(partition)
        items.append((str(i), layout_str, f"{tex_count} textures using {layout_str} bits"))
    return items if items else [('0', 'N/A', 'No valid layouts')]


def get_bit_layout_items_r(self, context):
    return get_bit_layout_items_for_channel(context, 'r')

def get_bit_layout_items_g(self, context):
    return get_bit_layout_items_for_channel(context, 'g')

def get_bit_layout_items_b(self, context):
    return get_bit_layout_items_for_channel(context, 'b')

def get_bit_layout_items_a(self, context):
    return get_bit_layout_items_for_channel(context, 'a')


def update_bit_mode(self, context):
    """Reset all channels when bit mode changes."""
    props = context.scene.texops_unpacker
    for ch in 'rgba':
        setattr(props, f'tex_count_{ch}', '0')
        setattr(props, f'bit_layout_{ch}', '0')


def update_tex_count(self, context):
    """Reset bit layout when texture count changes."""
    pass


def get_reduction_mode_items(self, context):
    """Get available reduction modes based on bit mode."""
    props = context.scene.texops_unpacker
    bit_mode = props.bit_mode
    items = []
    for mode_name, mode_info in REDUCTION_MODES.items():
        bits = mode_info['bits'].get(bit_mode, 0)
        if bits >= 1:
            grid = mode_info['grid']
            items.append((mode_name, mode_name, f"{grid}x{grid} grid, {bits} bits per quadrant"))
    return items if items else [('1/2', '1/2', 'Default')]


# ============================================================================
# Properties
# ============================================================================

get_depth_items = core.make_depth_items_callback("texops_unpacker")
_aspect = core.AspectRatioHelper()


class Unpacker_Properties(bpy.types.PropertyGroup):
    mode: bpy.props.EnumProperty(name="Mode", items=UNPACKING_MODES, default='CHANNEL_SPLIT')
    
    bit_mode: bpy.props.EnumProperty(
        name="Bit Mode",
        items=[('8BIT', "8-bit", ""), ('16BIT', "16-bit", ""), ('32BIT', "32-bit", "")],
        default='8BIT', update=update_bit_mode
    )
    reduction_mode: bpy.props.EnumProperty(name="Reduction", items=get_reduction_mode_items, default=0)
    
    input_mode: bpy.props.EnumProperty(
        name="Mode", items=[('SINGLE', "Single", ""), ('BATCH', "Batch", "")], default='SINGLE'
    )
    input_folder: bpy.props.StringProperty(name="Input Folder", default="//", subtype='DIR_PATH')
    input_image: bpy.props.StringProperty(name="Input Image", default="")
    
    unpack_r: bpy.props.BoolProperty(name="R", default=True)
    unpack_g: bpy.props.BoolProperty(name="G", default=True)
    unpack_b: bpy.props.BoolProperty(name="B", default=True)
    unpack_a: bpy.props.BoolProperty(name="A", default=True)
    
    tex_count_r: bpy.props.EnumProperty(name="R Count", items=get_texture_count_items, update=update_tex_count)
    tex_count_g: bpy.props.EnumProperty(name="G Count", items=get_texture_count_items, update=update_tex_count)
    tex_count_b: bpy.props.EnumProperty(name="B Count", items=get_texture_count_items, update=update_tex_count)
    tex_count_a: bpy.props.EnumProperty(name="A Count", items=get_texture_count_items, update=update_tex_count)
    
    bit_layout_r: bpy.props.EnumProperty(name="R Layout", items=get_bit_layout_items_r)
    bit_layout_g: bpy.props.EnumProperty(name="G Layout", items=get_bit_layout_items_g)
    bit_layout_b: bpy.props.EnumProperty(name="B Layout", items=get_bit_layout_items_b)
    bit_layout_a: bpy.props.EnumProperty(name="A Layout", items=get_bit_layout_items_a)
    
    suffix_r: bpy.props.StringProperty(name="R Suffix", default="_R")
    suffix_g: bpy.props.StringProperty(name="G Suffix", default="_G")
    suffix_b: bpy.props.StringProperty(name="B Suffix", default="_B")
    suffix_a: bpy.props.StringProperty(name="A Suffix", default="_A")
    
    suffix_r0: bpy.props.StringProperty(default="_R1")
    suffix_r1: bpy.props.StringProperty(default="_R2")
    suffix_r2: bpy.props.StringProperty(default="_R3")
    suffix_r3: bpy.props.StringProperty(default="_R4")
    suffix_r4: bpy.props.StringProperty(default="_R5")
    suffix_r5: bpy.props.StringProperty(default="_R6")
    suffix_r6: bpy.props.StringProperty(default="_R7")
    suffix_r7: bpy.props.StringProperty(default="_R8")
    
    suffix_g0: bpy.props.StringProperty(default="_G1")
    suffix_g1: bpy.props.StringProperty(default="_G2")
    suffix_g2: bpy.props.StringProperty(default="_G3")
    suffix_g3: bpy.props.StringProperty(default="_G4")
    suffix_g4: bpy.props.StringProperty(default="_G5")
    suffix_g5: bpy.props.StringProperty(default="_G6")
    suffix_g6: bpy.props.StringProperty(default="_G7")
    suffix_g7: bpy.props.StringProperty(default="_G8")
    
    suffix_b0: bpy.props.StringProperty(default="_B1")
    suffix_b1: bpy.props.StringProperty(default="_B2")
    suffix_b2: bpy.props.StringProperty(default="_B3")
    suffix_b3: bpy.props.StringProperty(default="_B4")
    suffix_b4: bpy.props.StringProperty(default="_B5")
    suffix_b5: bpy.props.StringProperty(default="_B6")
    suffix_b6: bpy.props.StringProperty(default="_B7")
    suffix_b7: bpy.props.StringProperty(default="_B8")
    
    suffix_a0: bpy.props.StringProperty(default="_A1")
    suffix_a1: bpy.props.StringProperty(default="_A2")
    suffix_a2: bpy.props.StringProperty(default="_A3")
    suffix_a3: bpy.props.StringProperty(default="_A4")
    suffix_a4: bpy.props.StringProperty(default="_A5")
    suffix_a5: bpy.props.StringProperty(default="_A6")
    suffix_a6: bpy.props.StringProperty(default="_A7")
    suffix_a7: bpy.props.StringProperty(default="_A8")
    
    output_name: bpy.props.StringProperty(name="Output Name", default="")
    output_suffix: bpy.props.StringProperty(name="Suffix", default="_Unpacked")
    output_folder: bpy.props.StringProperty(name="Output Folder", default="//", subtype='DIR_PATH')
    output_width: bpy.props.IntProperty(name="Width", default=0, min=0, max=16384, update=lambda s, c: _aspect.update_width(s))
    output_height: bpy.props.IntProperty(name="Height", default=0, min=0, max=16384, update=lambda s, c: _aspect.update_height(s))
    lock_aspect: bpy.props.BoolProperty(name="Lock Aspect", default=True, update=lambda s, c: _aspect.update_lock(s))
    file_format: bpy.props.EnumProperty(name="Format", items=core.get_format_items, update=core.update_depth_for_format)
    color_depth: bpy.props.EnumProperty(name="Depth", items=get_depth_items)


# ============================================================================
# Operators
# ============================================================================

class TEXOPS_OT_Unpacker_LoadImage(core.LoadImageOperatorBase):
    bl_idname = "texops.unpacker_load_image"
    bl_label = "Load Image"
    def get_props(self, context):
        return context.scene.texops_unpacker


class TEXOPS_OT_Unpacker_ShowImage(core.ShowImageOperatorBase):
    bl_idname = "texops.unpacker_show_image"
    bl_label = "Show Image"
    def get_props(self, context):
        return context.scene.texops_unpacker


class TEXOPS_OT_Unpacker_Unpack(core.BatchConfirmMixin, bpy.types.Operator):
    """Unpack textures based on selected mode"""
    bl_idname = "texops.unpacker_unpack"
    bl_label = "Unpack"
    bl_options = {'REGISTER', 'UNDO'}
    
    def get_props(self, context):
        return context.scene.texops_unpacker
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_unpacker
        if props.input_mode == 'BATCH':
            return self.execute_batch(context, props)
        
        input_img, error = core.get_input_image(props, self)
        if error:
            return error
        
        width, height = input_img.size
        target_w = props.output_width if props.output_width > 0 else width
        target_h = props.output_height if props.output_height > 0 else height
        
        if props.mode == 'CHANNEL_SPLIT':
            return self.execute_channel_split(context, props, input_img, width, height, target_w, target_h)
        elif props.mode == 'RESOLUTION_UNPACK':
            return self.execute_resolution_unpack(context, props, input_img, width, height, target_w, target_h)
        elif props.mode == 'BIT_UNPACK':
            return self.execute_bit_unpack(context, props, input_img, width, height, target_w, target_h)
        return {'CANCELLED'}
    
    def execute_channel_split(self, context, props, input_img, width, height, target_w, target_h):
        channels = unpack_rgba_channels(input_img)
        base_name = props.input_image.rsplit('.', 1)[0]
        enabled = {'R': props.unpack_r, 'G': props.unpack_g, 'B': props.unpack_b, 'A': props.unpack_a}
        suffixes = {'R': props.suffix_r, 'G': props.suffix_g, 'B': props.suffix_b, 'A': props.suffix_a}
        
        output_images = []
        for ch in 'RGBA':
            if not enabled[ch]:
                continue
            result = channels[ch]
            if (target_w, target_h) != (width, height):
                result = core.resize_bilinear(result, target_h, target_w)
            output_name = base_name + suffixes[ch]
            output_img = core.create_image(output_name, result, 'Non-Color')
            filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
            core.save_image(output_img, filepath, props.file_format, 'BW', props.color_depth)
            output_images.append(output_img)
        
        if output_images:
            core.set_image_editor_image(context, output_images[-1])
            self.report({'INFO'}, f"Unpacked {len(output_images)} channel(s) ({target_w}x{target_h})")
        return {'FINISHED'}
    
    def execute_resolution_unpack(self, context, props, input_img, width, height, target_w, target_h):
        mode_info = REDUCTION_MODES[props.reduction_mode]
        grid_size = mode_info['grid']
        auto_w, auto_h = width * grid_size, height * grid_size
        
        result = unpack_resolution_packed(input_img, props.bit_mode, props.reduction_mode)
        
        final_w = target_w if props.output_width > 0 else auto_w
        final_h = target_h if props.output_height > 0 else auto_h
        if (final_w, final_h) != (auto_w, auto_h):
            result = core.resize_bilinear(result, final_h, final_w)
        
        base_name = props.input_image.rsplit('.', 1)[0]
        output_name = (props.output_name if props.output_name else base_name) + props.output_suffix
        output_img = core.create_image(output_name, result, 'Non-Color')
        filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
        core.save_image(output_img, filepath, props.file_format, 'BW', props.color_depth)
        
        core.set_image_editor_image(context, output_img)
        self.report({'INFO'}, f"Unpacked {width}x{height} -> {final_w}x{final_h}")
        return {'FINISHED'}
    
    def execute_bit_unpack(self, context, props, input_img, width, height, target_w, target_h):
        channel_layouts = [
            get_channel_bit_layout(props, 'r'),
            get_channel_bit_layout(props, 'g'),
            get_channel_bit_layout(props, 'b'),
            get_channel_bit_layout(props, 'a'),
        ]
        if not any(channel_layouts):
            self.report({'ERROR'}, "No textures configured for unpacking")
            return {'CANCELLED'}
        
        unpacked_dict = unpack_bit_packed(input_img, channel_layouts, props.bit_mode)
        base_name = props.input_image.rsplit('.', 1)[0]
        output_images = []
        
        for ch_idx, (channel, bits_layout) in enumerate(zip('RGBA', channel_layouts)):
            if not bits_layout:
                continue
            for i in range(len(bits_layout)):
                key = f"{channel}{i}"
                if key not in unpacked_dict:
                    continue
                result = unpacked_dict[key]
                if (target_w, target_h) != (width, height):
                    result = core.resize_bilinear(result, target_h, target_w)
                suffix = getattr(props, f'suffix_{channel.lower()}{i}', f"_{channel}{i+1}")
                output_name = base_name + suffix
                output_img = core.create_image(output_name, result, 'Non-Color')
                filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                core.save_image(output_img, filepath, props.file_format, 'BW', props.color_depth)
                output_images.append(output_img)
        
        if output_images:
            core.set_image_editor_image(context, output_images[-1])
            self.report({'INFO'}, f"Unpacked {len(output_images)} texture(s) ({target_w}x{target_h})")
        return {'FINISHED'}
    
    def execute_batch(self, context, props):
        image_files = core.get_images_from_folder(props.input_folder)
        if not image_files:
            self.report({'ERROR'}, "No images found in folder")
            return {'CANCELLED'}
        
        if props.mode == 'CHANNEL_SPLIT':
            if not any([props.unpack_r, props.unpack_g, props.unpack_b, props.unpack_a]):
                self.report({'ERROR'}, "No channels selected")
                return {'CANCELLED'}
        elif props.mode == 'BIT_UNPACK':
            channel_layouts = [get_channel_bit_layout(props, ch) for ch in 'rgba']
            if not any(channel_layouts):
                self.report({'ERROR'}, "No textures configured")
                return {'CANCELLED'}
        
        target_w = props.output_width if props.output_width > 0 else 0
        target_h = props.output_height if props.output_height > 0 else 0
        success = 0
        last_output = None
        
        with core.progress(context.window_manager) as update:
            for i, filepath in enumerate(image_files):
                update(int(100 * i / len(image_files)))
                try:
                    img = core.load_image(filepath)
                    if not img:
                        continue
                    width, height = img.size
                    base_name = os.path.splitext(os.path.basename(filepath))[0]
                    final_target_w = target_w if target_w > 0 else width
                    final_target_h = target_h if target_h > 0 else height
                    
                    if props.mode == 'CHANNEL_SPLIT':
                        channels = unpack_rgba_channels(img)
                        enabled = {'R': props.unpack_r, 'G': props.unpack_g, 'B': props.unpack_b, 'A': props.unpack_a}
                        suffixes = {'R': props.suffix_r, 'G': props.suffix_g, 'B': props.suffix_b, 'A': props.suffix_a}
                        for ch in 'RGBA':
                            if not enabled[ch]:
                                continue
                            result = channels[ch]
                            if (final_target_w, final_target_h) != (width, height):
                                result = core.resize_bilinear(result, final_target_h, final_target_w)
                            output_name = base_name + suffixes[ch]
                            output_img = core.create_image(output_name, result, 'Non-Color')
                            out_path = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                            core.save_image(output_img, out_path, props.file_format, 'BW', props.color_depth)
                            last_output = output_img
                    
                    elif props.mode == 'RESOLUTION_UNPACK':
                        mode_info = REDUCTION_MODES[props.reduction_mode]
                        grid_size = mode_info['grid']
                        auto_w, auto_h = width * grid_size, height * grid_size
                        result = unpack_resolution_packed(img, props.bit_mode, props.reduction_mode)
                        final_w = target_w if target_w > 0 else auto_w
                        final_h = target_h if target_h > 0 else auto_h
                        if (final_w, final_h) != (auto_w, auto_h):
                            result = core.resize_bilinear(result, final_h, final_w)
                        output_name = base_name + props.output_suffix
                        output_img = core.create_image(output_name, result, 'Non-Color')
                        out_path = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                        core.save_image(output_img, out_path, props.file_format, 'BW', props.color_depth)
                        last_output = output_img
                    
                    elif props.mode == 'BIT_UNPACK':
                        channel_layouts = [get_channel_bit_layout(props, ch) for ch in 'rgba']
                        unpacked_dict = unpack_bit_packed(img, channel_layouts, props.bit_mode)
                        for ch_idx, (channel, bits_layout) in enumerate(zip('RGBA', channel_layouts)):
                            if not bits_layout:
                                continue
                            for j in range(len(bits_layout)):
                                key = f"{channel}{j}"
                                if key not in unpacked_dict:
                                    continue
                                result = unpacked_dict[key]
                                if (final_target_w, final_target_h) != (width, height):
                                    result = core.resize_bilinear(result, final_target_h, final_target_w)
                                suffix = getattr(props, f'suffix_{channel.lower()}{j}', f"_{channel}{j+1}")
                                output_name = base_name + suffix
                                output_img = core.create_image(output_name, result, 'Non-Color')
                                out_path = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                                core.save_image(output_img, out_path, props.file_format, 'BW', props.color_depth)
                                last_output = output_img
                    success += 1
                except Exception:
                    continue
        
        if last_output:
            core.set_image_editor_image(context, last_output)
        self.report({'INFO'}, f"Unpacked {success}/{len(image_files)} images")
        return {'FINISHED'}


# ============================================================================
# UI Panel
# ============================================================================

class TEXOPS_PT_Unpacker(bpy.types.Panel):
    bl_label = "Unpacker"
    bl_idname = "TEXOPS_PT_unpacker"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'TexOps'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.texops_unpacker
        
        layout.prop(props, "mode")
        layout.separator()
        
        # Input section
        box = layout.box()
        box.label(text="Input:", icon='IMAGE_DATA')
        core.draw_batch_input_section(
            box, props, load_op="texops.unpacker_load_image",
            show_op="texops.unpacker_show_image",
            count_func=lambda folder: len(core.get_images_from_folder(folder))
        )
        
        # Channel Split settings
        if props.mode == 'CHANNEL_SPLIT':
            layout.separator()
            box = layout.box()
            box.label(text="Channels:", icon='PREFERENCES')
            row = box.row(align=True)
            row.prop(props, "unpack_r", text="R", toggle=True)
            row.prop(props, "unpack_g", text="G", toggle=True)
            row.prop(props, "unpack_b", text="B", toggle=True)
            row.prop(props, "unpack_a", text="A", toggle=True)
        
        # Bit Unpack settings - matching bit_packer.py UI
        if props.mode == 'BIT_UNPACK':
            layout.separator()
            
            # Bit mode toggle - 3 buttons in a row
            row = layout.row()
            row.prop(props, "bit_mode", expand=True)
            
            layout.separator()
            
            # Per-channel configuration
            for channel in 'RGBA':
                ch_lower = channel.lower()
                box = layout.box()
                
                # Channel header
                row = box.row()
                row.label(text=f"Channel {channel}:", icon='NODE_MATERIAL')
                
                # Texture count dropdown
                box.prop(props, f'tex_count_{ch_lower}', text="Textures")
                
                tex_count = int(getattr(props, f'tex_count_{ch_lower}', '0'))
                
                if tex_count > 0:
                    # Bit layout dropdown
                    box.prop(props, f'bit_layout_{ch_lower}', text="Layout")
                    
                    bits_layout = get_channel_bit_layout(props, ch_lower)
                    
                    if bits_layout:
                        box.separator()
                        
                        # Suffix fields for each texture
                        for i, bit_count in enumerate(bits_layout):
                            row = box.row(align=True)
                            sub = row.row()
                            sub.scale_x = 0.5
                            sub.label(text=f"{channel}{i+1} ({bit_count}-bit)")
                            suffix_prop = f'suffix_{ch_lower}{i}'
                            row.prop(props, suffix_prop, text="Suffix")
        
        # Resolution Unpack settings - matching resolution_packer.py UI
        if props.mode == 'RESOLUTION_UNPACK':
            layout.separator()
            
            # Bit mode toggle - 3 buttons in a row
            row = layout.row()
            row.prop(props, "bit_mode", expand=True)
            
            # Reduction mode toggle - 3 buttons in a row
            row = layout.row()
            row.prop(props, "reduction_mode", expand=True)
            
            # Show bit precision info
            mode_info = REDUCTION_MODES.get(props.reduction_mode, REDUCTION_MODES['1/2'])
            bits = mode_info['bits'].get(props.bit_mode, 8)
            if bits < 8:
                box = layout.box()
                levels = 1 << bits
                box.label(text=f"{bits}-bit precision ({levels} levels)", icon='INFO')
            
            # Show resolution info
            if props.input_mode == 'SINGLE' and props.input_image:
                img = bpy.data.images.get(props.input_image)
                if img:
                    width, height = img.size
                    grid_size = mode_info['grid']
                    auto_w, auto_h = width * grid_size, height * grid_size
                    out_w = props.output_width if props.output_width > 0 else auto_w
                    out_h = props.output_height if props.output_height > 0 else auto_h
                    box = layout.box()
                    box.label(text=f"{width}x{height} -> {out_w}x{out_h}", icon='INFO')
        
        # Output section
        layout.separator()
        out_box = layout.box()
        out_box.label(text="Output:", icon='FILE_IMAGE')
        
        if props.mode == 'CHANNEL_SPLIT':
            # Show suffix controls for channel split
            out_box.label(text="Channel Suffixes:")
            row = out_box.row(align=True)
            sub = row.row(align=True)
            sub.enabled = props.unpack_r
            sub.prop(props, "suffix_r", text="R")
            sub = row.row(align=True)
            sub.enabled = props.unpack_g
            sub.prop(props, "suffix_g", text="G")
            sub = row.row(align=True)
            sub.enabled = props.unpack_b
            sub.prop(props, "suffix_b", text="B")
            sub = row.row(align=True)
            sub.enabled = props.unpack_a
            sub.prop(props, "suffix_a", text="A")
        
        if props.mode == 'RESOLUTION_UNPACK':
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
        
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        row.operator("texops.unpacker_unpack", icon='EXPORT')


# ============================================================================
# Registration
# ============================================================================

classes = (
    Unpacker_Properties,
    TEXOPS_OT_Unpacker_LoadImage,
    TEXOPS_OT_Unpacker_ShowImage,
    TEXOPS_OT_Unpacker_Unpack,
    TEXOPS_PT_Unpacker,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_unpacker = bpy.props.PointerProperty(type=Unpacker_Properties)


def unregister():
    del bpy.types.Scene.texops_unpacker
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)