"""
Bit Packer Module for TexOps
Pack multiple textures into RGBA channels using bit subdivision
"""

import bpy
import numpy as np
import os

from . import core


# ============================================================================
# Bit Packing Functions
# ============================================================================

def pack_bits(values, bit_layouts):
    """Pack multiple quantized values into a single float channel."""
    result = np.zeros_like(values[0], dtype=np.uint32)
    bit_offset = 0
    for val, bits in zip(values, bit_layouts):
        result |= (val << bit_offset)
        bit_offset += bits
    return result.astype(np.float32) / 255.0


def pack_channel(tex_data_list, bits_layout, width, height, dither_mode, is_alpha=False):
    """Pack textures into a single channel."""
    tex_data = []
    for i, b in enumerate(bits_layout):
        if i < len(tex_data_list) and tex_data_list[i] is not None:
            tex = tex_data_list[i]
            if tex.shape != (height, width):
                tex = core.resize_bilinear(tex, height, width)
        else:
            default = 1.0 if is_alpha else 0.0
            tex = np.full((height, width), default, dtype=np.float32)
        
        tex = core.apply_dither(np.clip(tex, 0, 1), b, dither_mode, height, width)
        tex_data.append(core.quantize(np.clip(tex, 0, 1), b))
    
    return pack_bits(tex_data, bits_layout)


def pack_textures_flexible(channel_configs, tex_data_dict, width, height, dither_mode):
    """Pack textures with per-channel configuration."""
    output = np.zeros((height, width, 4), dtype=np.float32)
    
    for ch_idx, (channel, bits_layout) in enumerate(zip('RGBA', channel_configs)):
        if not bits_layout:  # Empty layout
            output[:, :, ch_idx] = 1.0 if channel == 'A' else 0.0
            continue
        
        tex_list = tex_data_dict.get(channel, [])
        is_alpha = (channel == 'A')
        output[:, :, ch_idx] = pack_channel(tex_list, bits_layout, width, height, dither_mode, is_alpha)
    
    return output


def determine_color_mode(channel_configs):
    """
    Determine output color mode based on which channels have data.
    
    Args:
        channel_configs: List of 4 bit layouts [R, G, B, A]
    
    Returns:
        'BW' if only R, 'RGB' if R/G/B but no A, 'RGBA' if A is used
    """
    r_used = bool(channel_configs[0])
    g_used = bool(channel_configs[1])
    b_used = bool(channel_configs[2])
    a_used = bool(channel_configs[3])
    
    if a_used:
        return 'RGBA'
    elif g_used or b_used:
        return 'RGB'
    elif r_used:
        return 'BW'
    else:
        return 'RGBA'  # Default fallback


# ============================================================================
# Bit Layout Generation
# ============================================================================

def generate_bit_partitions(total_bits, num_textures):
    """
    Generate all valid ways to partition total_bits into num_textures parts.
    Each part must be >= 1 bit.
    Returns list of tuples representing bit allocations in descending order.
    """
    if num_textures == 0:
        return [[]]
    if num_textures == 1:
        return [[total_bits]]
    
    partitions = []
    
    def partition_recursive(remaining_bits, remaining_textures, current, min_bits):
        if remaining_textures == 0:
            if remaining_bits == 0:
                partitions.append(current[:])
            return
        
        if remaining_textures == 1:
            if remaining_bits >= 1 and remaining_bits <= min_bits:
                partitions.append(current + [remaining_bits])
            return
        
        # Try allocating bits in descending order to avoid duplicates
        # Start from min_bits down to ensure we can allocate at least 1 bit to remaining textures
        max_allocate = min(min_bits, remaining_bits - remaining_textures + 1)
        
        for bits in range(max_allocate, 0, -1):
            partition_recursive(remaining_bits - bits, remaining_textures - 1, current + [bits], bits)
    
    partition_recursive(total_bits, num_textures, [], total_bits)
    
    # Results are already in descending order per position due to recursion order
    return partitions


def get_symmetrical_counts(total_bits):
    """
    Get valid symmetrical texture counts for batch mode.
    Only returns counts that evenly divide total_bits (e.g., 8-bit: 1,2,4,8).
    """
    counts = []
    for count in range(1, total_bits + 1):
        if total_bits % count == 0:
            counts.append(count)
    return counts


def get_format_items_for_bit_mode(self, context):
    """Get valid file formats based on bit mode."""
    props = context.scene.texops_bit_packer
    bit_mode = props.bit_mode
    
    if bit_mode == '8BIT':
        # All formats except EXR
        return [
            ('PNG', "PNG", "8-bit PNG"),
            ('TARGA', "TGA", "8-bit Targa"),
            ('TIFF', "TIFF", "8-bit TIFF"),
        ]
    elif bit_mode == '16BIT':
        # All formats
        return [
            ('PNG', "PNG", "16-bit PNG"),
            ('TARGA', "TGA", "16-bit Targa"),
            ('TIFF', "TIFF", "16-bit TIFF"),
            ('OPEN_EXR', "EXR", "16-bit OpenEXR"),
        ]
    else:  # 32BIT
        # EXR only
        return [
            ('OPEN_EXR', "EXR", "32-bit OpenEXR (float)"),
        ]


def get_bit_mode_max(bit_mode):
    """Get the bit depth for the selected mode."""
    return {'8BIT': 8, '16BIT': 16, '32BIT': 32}[bit_mode]


def update_format_for_bit_mode(self, context):
    """Update file format when bit mode changes to ensure compatibility."""
    props = context.scene.texops_bit_packer
    
    # Set default format based on bit mode
    if props.bit_mode == '8BIT':
        if props.file_format not in ('PNG', 'TARGA', 'TIFF'):
            props.file_format = 'PNG'
    elif props.bit_mode == '16BIT':
        if props.file_format not in ('PNG', 'TARGA', 'TIFF', 'OPEN_EXR'):
            props.file_format = 'PNG'
    else:  # 32BIT
        props.file_format = 'OPEN_EXR'
    
    # Also reset channels when mode changes
    update_bit_mode(props, context)


def format_bit_layout(bits):
    """Format bit layout as string: [4,4,2,2] -> '4 x2 | 2 x2' (bit depth x count). Omit x1."""
    if not bits:
        return ""
    
    # Group consecutive identical values and format as "bit_depth x count"
    parts = []
    current_val = bits[0]
    count = 1
    
    for i in range(1, len(bits)):
        if bits[i] == current_val:
            count += 1
        else:
            # Add the previous group as "bit x count" (omit x1)
            if count == 1:
                parts.append(str(current_val))
            else:
                parts.append(f"{current_val} x{count}")
            current_val = bits[i]
            count = 1
    
    # Add the last group
    if count == 1:
        parts.append(str(current_val))
    else:
        parts.append(f"{current_val} x{count}")
    
    return ' | '.join(parts)


def get_batch_textures_per_channel_items(self, context):
    """Generate texture per channel options for batch mode - symmetrical layouts only."""
    props = context.scene.texops_bit_packer
    total_bits = get_bit_mode_max(props.bit_mode)
    
    # Only allow symmetrical counts (evenly divide total bits)
    symmetrical_counts = get_symmetrical_counts(total_bits)
    
    items = []
    for count in symmetrical_counts:
        bits_per_tex = total_bits // count
        # Symmetrical layout: all textures get same bit depth
        layout_str = f"{bits_per_tex} x{count}" if count > 1 else str(bits_per_tex)
        items.append((str(count), f"{count} ({layout_str})", f"{count} textures per channel, {bits_per_tex} bits each"))
    
    return items if items else [('1', '1', 'One texture')]


def get_texture_count_items(self, context):
    """Generate texture count dropdown based on bit mode."""
    props = context.scene.texops_bit_packer
    max_textures = get_bit_mode_max(props.bit_mode)
    return [(str(i), str(i), f"{i} textures") for i in range(max_textures + 1)]


def get_bit_layout_items_r(self, context):
    """Generate bit layout for R channel."""
    return get_bit_layout_items_for_channel(context, 'r')

def get_bit_layout_items_g(self, context):
    """Generate bit layout for G channel."""
    return get_bit_layout_items_for_channel(context, 'g')

def get_bit_layout_items_b(self, context):
    """Generate bit layout for B channel."""
    return get_bit_layout_items_for_channel(context, 'b')

def get_bit_layout_items_a(self, context):
    """Generate bit layout for A channel."""
    return get_bit_layout_items_for_channel(context, 'a')

def get_bit_layout_items_for_channel(context, channel):
    """Generate bit layout combinations based on texture count for specific channel."""
    props = context.scene.texops_bit_packer
    
    tex_count_prop = f'tex_count_{channel}'
    tex_count_str = getattr(props, tex_count_prop, '0')
    tex_count = int(tex_count_str)
    
    if tex_count == 0:
        return [('0', 'N/A', 'No textures')]
    
    total_bits = get_bit_mode_max(props.bit_mode)
    partitions = generate_bit_partitions(total_bits, tex_count)
    
    items = []
    for i, partition in enumerate(partitions):
        layout_str = format_bit_layout(partition)
        items.append((str(i), layout_str, f"{tex_count} textures using {layout_str} bits"))
    
    return items if items else [('0', 'N/A', 'No valid layouts')]


def update_bit_mode(self, context):
    """Reset all channels when bit mode changes."""
    props = context.scene.texops_bit_packer
    for ch in 'rgba':
        setattr(props, f'tex_count_{ch}', '0')
        setattr(props, f'bit_layout_{ch}', '0')


def update_tex_count(self, context):
    """Reset bit layout when texture count changes."""
    props = context.scene.texops_bit_packer
    channel = self.path_from_id().split('.')[-1].split('_')[-1]
    setattr(props, f'bit_layout_{channel}', '0')


def get_channel_bit_layout(props, channel):
    """
    Get the actual bit layout list for a channel.
    Returns empty list if no textures selected.
    """
    tex_count = int(getattr(props, f'tex_count_{channel}', '0'))
    if tex_count == 0:
        return []
    
    layout_idx = int(getattr(props, f'bit_layout_{channel}', '0'))
    total_bits = get_bit_mode_max(props.bit_mode)
    partitions = generate_bit_partitions(total_bits, tex_count)
    
    if 0 <= layout_idx < len(partitions):
        return partitions[layout_idx]
    return []


# ============================================================================
# Properties
# ============================================================================

_aspect = core.AspectRatioHelper()


class BitPackerInput_Properties(bpy.types.PropertyGroup):
    image: bpy.props.StringProperty(name="Image", default="")
    channel: bpy.props.EnumProperty(name="Channel", items=core.CHANNEL_ITEMS_WITH_CONSTANTS, default='GRAY')


def _create_bitpacker_props():
    annotations = {
        'bit_mode': bpy.props.EnumProperty(
            name="Bit Mode",
            items=[
                ('8BIT', "8-bit", "Pack into 8 bits per channel"),
                ('16BIT', "16-bit", "Pack into 16 bits per channel"),
                ('32BIT', "32-bit", "Pack into 32 bits per channel"),
            ],
            default='8BIT',
            update=update_format_for_bit_mode
        ),
        
        'input_mode': bpy.props.EnumProperty(
            name="Mode", items=[('SINGLE', "Single", ""), ('BATCH', "Batch", "")], default='SINGLE'
        ),
        'input_folder': bpy.props.StringProperty(name="Input Folder", default="//", subtype='DIR_PATH'),
        
        'batch_textures_per_channel': bpy.props.EnumProperty(
            name="Textures Per Channel",
            items=get_batch_textures_per_channel_items,
            default=0
        ),
        
        'dither_mode': bpy.props.EnumProperty(
            name="Dithering",
            items=[
                ('NONE', "None", "No dithering"),
                ('ORDERED', "Ordered", "Bayer matrix (deterministic, tileable)"),
                ('NOISE', "Noise", "Random noise"),
                ('BLUE', "Blue Noise", "Blue noise (best quality)"),
            ],
            default='ORDERED'
        ),
        
        'file_format': bpy.props.EnumProperty(
            name="Format",
            items=get_format_items_for_bit_mode,
            default=0
        ),
        
        'output_name': bpy.props.StringProperty(name="Output Name", default="Packed"),
        'output_suffix': bpy.props.StringProperty(name="Suffix", default="_BitPacked"),
        'output_folder': bpy.props.StringProperty(name="Output Folder", default="//", subtype='DIR_PATH'),
        'output_width': bpy.props.IntProperty(name="Width", default=0, min=0, max=16384,
                                               update=lambda s, c: _aspect.update_width(s)),
        'output_height': bpy.props.IntProperty(name="Height", default=0, min=0, max=16384,
                                                update=lambda s, c: _aspect.update_height(s)),
        'lock_aspect': bpy.props.BoolProperty(name="Lock Aspect", default=True,
                                               update=lambda s, c: _aspect.update_lock(s)),
    }
    
    # Per-channel texture count and bit layout selection
    annotations['tex_count_r'] = bpy.props.EnumProperty(
        name="R Texture Count",
        items=get_texture_count_items,
        update=update_tex_count
    )
    annotations['bit_layout_r'] = bpy.props.EnumProperty(
        name="R Bit Layout",
        items=get_bit_layout_items_r
    )
    
    annotations['tex_count_g'] = bpy.props.EnumProperty(
        name="G Texture Count",
        items=get_texture_count_items,
        update=update_tex_count
    )
    annotations['bit_layout_g'] = bpy.props.EnumProperty(
        name="G Bit Layout",
        items=get_bit_layout_items_g
    )
    
    annotations['tex_count_b'] = bpy.props.EnumProperty(
        name="B Texture Count",
        items=get_texture_count_items,
        update=update_tex_count
    )
    annotations['bit_layout_b'] = bpy.props.EnumProperty(
        name="B Bit Layout",
        items=get_bit_layout_items_b
    )
    
    annotations['tex_count_a'] = bpy.props.EnumProperty(
        name="A Texture Count",
        items=get_texture_count_items,
        update=update_tex_count
    )
    annotations['bit_layout_a'] = bpy.props.EnumProperty(
        name="A Bit Layout",
        items=get_bit_layout_items_a
    )
    
    # 32 texture slots per channel × 4 channels = 128 max slots
    for ch in 'rgba':
        for i in range(32):
            annotations[f'tex_{ch}_{i}'] = bpy.props.PointerProperty(type=BitPackerInput_Properties)
    
    return annotations


class BitPacker_Properties(bpy.types.PropertyGroup):
    __annotations__ = _create_bitpacker_props()


def get_tex_prop(props, channel, index):
    return getattr(props, f"tex_{channel.lower()}_{index}", None)


# ============================================================================
# Operators
# ============================================================================

class TEXOPS_OT_BitPacker_LoadImage(core.LoadImageOperatorBase):
    bl_idname = "texops.bitpack_load_image"
    bl_label = "Load Image"
    
    channel: bpy.props.StringProperty()
    index: bpy.props.IntProperty()
    
    def get_props(self, context):
        return context.scene.texops_bit_packer
    
    def execute(self, context):
        try:
            img = bpy.data.images.load(self.filepath, check_existing=True)
            props = self.get_props(context)
            tex_prop = get_tex_prop(props, self.channel, self.index)
            if tex_prop:
                tex_prop.image = img.name
            core.set_image_editor_image(context, img)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed: {str(e)}")
            return {'CANCELLED'}


class TEXOPS_OT_BitPacker_Preview(bpy.types.Operator):
    """Preview the selected input image"""
    bl_idname = "texops.bitpack_preview"
    bl_label = "Preview Input"
    bl_options = {'INTERNAL'}
    
    channel: bpy.props.StringProperty()
    index: bpy.props.IntProperty()
    
    def execute(self, context):
        props = context.scene.texops_bit_packer
        tex_prop = get_tex_prop(props, self.channel, self.index)
        if not tex_prop or not tex_prop.image:
            return {'CANCELLED'}
        
        img = bpy.data.images.get(tex_prop.image)
        if img:
            core.set_image_editor_image(context, img)
        return {'FINISHED'}


class TEXOPS_OT_BitPacker_Pack(core.BatchConfirmMixin, bpy.types.Operator):
    """Pack textures using bit subdivision"""
    bl_idname = "texops.bitpack_pack"
    bl_label = "Pack Textures"
    bl_options = {'REGISTER'}
    
    def get_props(self, context):
        return context.scene.texops_bit_packer
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_bit_packer
        if props.input_mode == 'BATCH':
            return self.execute_batch(context, props)
        return self.execute_single(context, props)
    
    def execute_single(self, context, props):
        # Get bit layouts for each channel
        channel_configs = []
        tex_data_dict = {}
        first_img = None
        
        for channel in 'RGBA':
            bits_layout = get_channel_bit_layout(props, channel.lower())
            channel_configs.append(bits_layout)
            
            tex_list = []
            for i in range(len(bits_layout)):
                tex_prop = get_tex_prop(props, channel, i)
                if tex_prop and tex_prop.image:
                    img = bpy.data.images.get(tex_prop.image)
                    if img:
                        if not first_img:
                            first_img = img
                        data = core.extract_channel(img, tex_prop.channel, (1024, 1024))
                        tex_list.append(data)
                    else:
                        tex_list.append(None)
                else:
                    tex_list.append(None)
            
            tex_data_dict[channel] = tex_list
        
        # Check if any input
        has_input = any(
            any(t is not None for t in tex_list) 
            for tex_list in tex_data_dict.values()
        )
        if not has_input:
            self.report({'ERROR'}, "No input images selected")
            return {'CANCELLED'}
        
        width, height = props.output_width, props.output_height
        if width == 0 or height == 0:
            width, height = first_img.size if first_img else (1024, 1024)
        
        packed = pack_textures_flexible(channel_configs, tex_data_dict, width, height, props.dither_mode)
        output_name = props.output_name + props.output_suffix
        use_float = props.bit_mode != '8BIT'
        output_img = core.create_image(output_name, packed, 'Non-Color', float_buffer=use_float)
        
        # Use selected format and determine bit depth
        file_format = props.file_format
        if file_format == 'OPEN_EXR':
            color_depth = '32' if props.bit_mode == '32BIT' else '16'
        else:
            color_depth = '16' if props.bit_mode in ('16BIT', '32BIT') else '8'
        
        # Determine color mode based on channels used
        color_mode = determine_color_mode(channel_configs)
        
        filepath = core.generate_output_path(output_name, "", props.output_folder, file_format)
        core.save_image(output_img, filepath, file_format, color_mode, color_depth, compression=0)
        core.set_image_editor_image(context, output_img)
        
        self.report({'INFO'}, f"Saved: {filepath}")
        return {'FINISHED'}
    
    def execute_batch(self, context, props):
        files = core.get_images_from_folder(props.input_folder)
        if not files:
            self.report({'ERROR'}, "No images found in folder")
            return {'CANCELLED'}
        
        # Get textures per channel from batch setting
        tex_per_channel = int(props.batch_textures_per_channel)
        total_bits = get_bit_mode_max(props.bit_mode)
        
        # Symmetrical layout: all textures get equal bits
        bits_per_tex = total_bits // tex_per_channel
        bits_layout = [bits_per_tex] * tex_per_channel
        
        total_slots = tex_per_channel * 4  # Same layout for all 4 channels
        
        # Load images
        tex_data_all = []
        first_size = None
        for filepath in files[:total_slots]:
            img = core.load_image(filepath)
            if img:
                if not first_size:
                    first_size = img.size
                data = core.extract_channel(img, 'GRAY', first_size or (1024, 1024))
                tex_data_all.append(data)
        
        if not tex_data_all:
            self.report({'ERROR'}, "Failed to load any images")
            return {'CANCELLED'}
        
        # Distribute evenly across all 4 channels
        channel_configs = [bits_layout] * 4
        tex_data_dict = {}
        idx = 0
        
        for channel in 'RGBA':
            tex_data_dict[channel] = tex_data_all[idx:idx + tex_per_channel]
            idx += tex_per_channel
        
        width, height = props.output_width, props.output_height
        if width == 0 or height == 0:
            width, height = first_size or (1024, 1024)
        
        packed = pack_textures_flexible(channel_configs, tex_data_dict, width, height, props.dither_mode)
        output_name = props.output_name + props.output_suffix
        use_float = props.bit_mode != '8BIT'
        output_img = core.create_image(output_name, packed, 'Non-Color', float_buffer=use_float)
        
        file_format = props.file_format
        if file_format == 'OPEN_EXR':
            color_depth = '32' if props.bit_mode == '32BIT' else '16'
        else:
            color_depth = '16' if props.bit_mode in ('16BIT', '32BIT') else '8'
        
        filepath = core.generate_output_path(output_name, "", props.output_folder, file_format)
        core.save_image(output_img, filepath, file_format, 'RGBA', color_depth, compression=0)
        core.set_image_editor_image(context, output_img)
        
        loaded = len(tex_data_all)
        self.report({'INFO'}, f"Packed {loaded}/{len(files)} images ({tex_per_channel} per channel, {bits_per_tex}-bit each)")
        return {'FINISHED'}


# ============================================================================
# UI Panel
# ============================================================================

class TEXOPS_PT_BitPacker(bpy.types.Panel):
    bl_label = "Bit Packer"
    bl_idname = "TEXOPS_PT_bit_packer"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'TexOps'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.texops_bit_packer
        
        # Mode toggle
        row = layout.row()
        row.prop(props, "input_mode", expand=True)
        
        layout.separator()
        
        # Bit mode toggle
        row = layout.row()
        row.prop(props, "bit_mode", expand=True)
        
        layout.separator()
        
        if props.input_mode == 'SINGLE':
            self.draw_single_mode(layout, props)
        else:
            self.draw_batch_mode(layout, props)
        
        layout.separator()
        
        # Output
        box = layout.box()
        box.label(text="Output:", icon='FILE_IMAGE')
        box.prop(props, "output_name")
        box.prop(props, "output_suffix")
        box.prop(props, "output_folder", text="")
        row = box.row(align=True)
        row.prop(props, "lock_aspect", text="", icon='LOCKED' if props.lock_aspect else 'UNLOCKED')
        row.prop(props, "output_width", text="Width")
        row.prop(props, "output_height", text="Height")
        box.prop(props, "file_format")
        box.prop(props, "dither_mode")
        
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        row.operator("texops.bitpack_pack", icon='EXPORT')
    
    def draw_single_mode(self, layout, props):
        """Draw per-channel configuration for single mode."""
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
                
                # Get the actual bit layout
                bits_layout = get_channel_bit_layout(props, ch_lower)
                
                if bits_layout:
                    box.separator()
                    
                    # Texture slots
                    for i, bit_count in enumerate(bits_layout):
                        tex_prop = get_tex_prop(props, channel, i)
                        if tex_prop:
                            row = box.row(align=True)
                            
                            # Label: "R1 (4-bit)"
                            sub = row.row()
                            sub.scale_x = 0.7
                            sub.label(text=f"{channel}{i+1} ({bit_count}-bit)")
                            
                            # Image search
                            row.prop_search(tex_prop, "image", bpy.data, "images", text="")
                            
                            # Load button
                            op = row.operator("texops.bitpack_load_image", text="", icon='FILEBROWSER')
                            op.channel = channel
                            op.index = i
                            
                            # Channel dropdown
                            sub = row.row()
                            sub.scale_x = 0.55
                            sub.prop(tex_prop, "channel", text="")
                            
                            # Preview button
                            sub = row.row(align=True)
                            sub.enabled = bool(tex_prop.image)
                            op = sub.operator("texops.bitpack_preview", text="", icon='HIDE_OFF')
                            op.channel = channel
                            op.index = i
    
    def draw_batch_mode(self, layout, props):
        """Draw batch mode with simple per-channel configuration."""
        box = layout.box()
        box.label(text="Batch Input:", icon='FILE_FOLDER')
        box.prop(props, "input_folder", text="")
        
        files = core.get_images_from_folder(props.input_folder)
        
        row = box.row(align=True)
        row.label(text="Textures Per Channel:")
        sub = row.row()
        sub.scale_x = 0.5
        sub.prop(props, "batch_textures_per_channel", text="")
        
        tex_per_channel = int(props.batch_textures_per_channel) if props.batch_textures_per_channel else 1
        total_bits = get_bit_mode_max(props.bit_mode)
        bits_per_tex = total_bits // tex_per_channel
        total_slots = tex_per_channel * 4
        
        box.separator()
        box.label(
            text=f"{len(files)} images found, need {total_slots} ({tex_per_channel} × 4 channels, {bits_per_tex}-bit each)",
            icon='CHECKMARK' if len(files) >= total_slots else 'ERROR'
        )


# ============================================================================
# Registration
# ============================================================================

classes = (
    BitPackerInput_Properties,
    BitPacker_Properties,
    TEXOPS_OT_BitPacker_LoadImage,
    TEXOPS_OT_BitPacker_Preview,
    TEXOPS_OT_BitPacker_Pack,
    TEXOPS_PT_BitPacker,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_bit_packer = bpy.props.PointerProperty(type=BitPacker_Properties)

def unregister():
    del bpy.types.Scene.texops_bit_packer
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)