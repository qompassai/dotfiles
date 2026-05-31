"""
Channel Packer Module for TexOps
Pack different channels from multiple textures into a single RGBA texture
"""

import bpy
import numpy as np
import os

from . import core


# ============================================================================
# Core Functions
# ============================================================================

def pack_channels(channel_data, output_size):
    """Pack 4 channels into RGBA texture."""
    height, width = output_size
    channels = []
    
    for i, (data, default_val) in enumerate(zip(channel_data, [0.0, 0.0, 0.0, 1.0])):
        if data is None:
            ch = np.full((height, width), default_val, dtype=np.float32)
        elif data.shape != (height, width):
            ch = core.resize_bilinear(data, height, width)
        else:
            ch = data
        channels.append(ch)
    
    return np.clip(np.stack(channels, axis=-1), 0.0, 1.0).astype(np.float32)


def pack_from_files(file_dict, output_size, default_channel='GRAY'):
    """
    Pack channels from file dictionary.
    
    Args:
        file_dict: Dict mapping '_R', '_G', '_B', '_A' to filepaths
        output_size: (height, width) tuple
        default_channel: Channel to use when loading images without suffix
    
    Returns:
        (packed_data, color_mode) tuple
    """
    channel_data = []
    channels_used = {'R': False, 'G': False, 'B': False, 'A': False}
    height, width = output_size
    
    for suffix, ch_name in [('_R', 'R'), ('_G', 'G'), ('_B', 'B'), ('_A', 'A')]:
        filepath = file_dict.get(suffix)
        if filepath:
            img = core.load_image(filepath)
            if img:
                data = core.extract_channel(img, default_channel, (height, width), 
                                           1.0 if suffix == '_A' else 0.0)
                channel_data.append(data)
                channels_used[ch_name] = True
            else:
                channel_data.append(None)
        else:
            channel_data.append(None)
    
    color_mode = determine_color_mode_from_usage(channels_used)
    return pack_channels(channel_data, output_size), color_mode


def determine_color_mode_from_usage(channels_used):
    """
    Determine output color mode based on which channels have data.
    
    Args:
        channels_used: Dict {'R': bool, 'G': bool, 'B': bool, 'A': bool}
    
    Returns:
        'BW' if only R, 'RGB' if R/G/B but no A, 'RGBA' if A is used
    """
    if channels_used['A']:
        return 'RGBA'
    elif channels_used['G'] or channels_used['B']:
        return 'RGB'
    elif channels_used['R']:
        return 'BW'
    else:
        return 'RGBA'  # Default fallback


def determine_color_mode_from_inputs(inputs):
    """
    Determine color mode from single-mode inputs dict.
    
    Args:
        inputs: Dict {'R': (image_name, channel), 'G': ..., 'B': ..., 'A': ...}
    
    Returns:
        'BW', 'RGB', or 'RGBA'
    """
    def has_data(img_name, channel):
        # Has data if image is set OR channel is WHITE/BLACK constant
        return bool(img_name) or channel in ['WHITE', 'BLACK']
    
    channels_used = {
        'R': has_data(*inputs['R']),
        'G': has_data(*inputs['G']),
        'B': has_data(*inputs['B']),
        'A': has_data(*inputs['A']),
    }
    
    return determine_color_mode_from_usage(channels_used)


# ============================================================================
# Properties
# ============================================================================

_aspect = core.AspectRatioHelper()
get_depth_items = core.make_depth_items_callback("texops_channel_packer")


class ChannelInput_Properties(bpy.types.PropertyGroup):
    image: bpy.props.StringProperty(name="Image", default="")
    channel: bpy.props.EnumProperty(name="Channel", items=core.CHANNEL_ITEMS_WITH_CONSTANTS, default='R')


class ChannelPacker_Properties(bpy.types.PropertyGroup):
    input_mode: bpy.props.EnumProperty(
        name="Mode",
        items=[('SINGLE', "Single", "Pack single set of channels"),
               ('BATCH', "Batch", "Pack from folder (looks for _R/_G/_B/_A suffixes)")],
        default='SINGLE'
    )
    input_folder: bpy.props.StringProperty(name="Input Folder", default="//", subtype='DIR_PATH')
    
    channel_r: bpy.props.PointerProperty(type=ChannelInput_Properties)
    channel_g: bpy.props.PointerProperty(type=ChannelInput_Properties)
    channel_b: bpy.props.PointerProperty(type=ChannelInput_Properties)
    channel_a: bpy.props.PointerProperty(type=ChannelInput_Properties)
    
    output_name: bpy.props.StringProperty(name="Output Name", default="Result")
    output_suffix: bpy.props.StringProperty(name="Suffix", default="_Packed",
                                            description="Suffix added to output filename")
    output_folder: bpy.props.StringProperty(name="Output Folder", default="//", subtype='DIR_PATH')
    output_width: bpy.props.IntProperty(name="Width", default=0, min=0, max=16384,
                                         update=lambda s, c: _aspect.update_width(s))
    output_height: bpy.props.IntProperty(name="Height", default=0, min=0, max=16384,
                                          update=lambda s, c: _aspect.update_height(s))
    lock_aspect: bpy.props.BoolProperty(name="Lock Aspect", default=True,
                                         update=lambda s, c: _aspect.update_lock(s))
    file_format: bpy.props.EnumProperty(name="Format", items=core.get_format_items,
                                         update=core.update_depth_for_format)
    color_depth: bpy.props.EnumProperty(name="Depth", items=get_depth_items)


# ============================================================================
# Operators
# ============================================================================

class TEXOPS_OT_ChannelPacker_LoadImage(core.LoadImageOperatorBase):
    bl_idname = "texops.channel_load_image"
    bl_label = "Load Image"
    
    channel: bpy.props.StringProperty()
    
    def get_props(self, context):
        return context.scene.texops_channel_packer
    
    def execute(self, context):
        try:
            img = bpy.data.images.load(self.filepath, check_existing=True)
            props = self.get_props(context)
            ch_props = getattr(props, f"channel_{self.channel.lower()}", None)
            if ch_props:
                ch_props.image = img.name
            core.set_image_editor_image(context, img)
            self.report({'INFO'}, f"Loaded: {img.name}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load: {str(e)}")
            return {'CANCELLED'}


class TEXOPS_OT_ChannelPacker_Preview(bpy.types.Operator):
    """Preview the selected input image"""
    bl_idname = "texops.channel_preview"
    bl_label = "Preview Input"
    bl_options = {'INTERNAL'}
    
    channel: bpy.props.StringProperty()
    
    def execute(self, context):
        props = context.scene.texops_channel_packer
        ch_props = getattr(props, f"channel_{self.channel.lower()}", None)
        if not ch_props or not ch_props.image:
            return {'CANCELLED'}
        
        img = bpy.data.images.get(ch_props.image)
        if img:
            core.set_image_editor_image(context, img)
        return {'FINISHED'}


class TEXOPS_OT_ChannelPacker_Pack(core.BatchConfirmMixin, bpy.types.Operator):
    """Pack selected channels into RGBA texture"""
    bl_idname = "texops.channel_pack"
    bl_label = "Pack to Texture"
    bl_options = {'REGISTER'}
    
    def get_props(self, context):
        return context.scene.texops_channel_packer
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_channel_packer
        if props.input_mode == 'BATCH':
            return self.execute_batch(context, props)
        return self.execute_single(context, props)
    
    def execute_single(self, context, props):
        inputs = {
            'R': (props.channel_r.image, props.channel_r.channel),
            'G': (props.channel_g.image, props.channel_g.channel),
            'B': (props.channel_b.image, props.channel_b.channel),
            'A': (props.channel_a.image, props.channel_a.channel),
        }
        
        images = {name: (bpy.data.images.get(img) if img else None, ch) 
                  for name, (img, ch) in inputs.items()}
        
        # Determine output size
        if props.output_width > 0 and props.output_height > 0:
            width, height = props.output_width, props.output_height
        else:
            width, height = 1024, 1024
            for img, _ in images.values():
                if img:
                    width, height = img.size
                    break
        
        has_input = any(img for img, _ in images.values()) or \
                    any(ch in ['WHITE', 'BLACK'] for _, ch in images.values())
        
        if not has_input:
            self.report({'ERROR'}, "No valid source images selected")
            return {'CANCELLED'}
        
        channel_data = []
        for name in ['R', 'G', 'B', 'A']:
            img, ch_type = images[name]
            default_val = 1.0 if name == 'A' else 0.0
            ch_data = core.extract_channel(img, ch_type, (height, width), default_val)
            channel_data.append(ch_data)
        
        packed = pack_channels(channel_data, (height, width))
        output_name = props.output_name + (props.output_suffix if props.output_suffix else "")
        output_img = core.create_image(output_name, packed, 'Non-Color')
        
        # Determine color mode based on channels used
        color_mode = determine_color_mode_from_inputs(inputs)
        
        filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
        core.save_image(output_img, filepath, props.file_format, color_mode, props.color_depth)
        core.set_image_editor_image(context, output_img)
        
        self.report({'INFO'}, f"Saved: {filepath}")
        return {'FINISHED'}
    
    def execute_batch(self, context, props):
        base_images = core.get_base_images_from_folder(props.input_folder)
        if not base_images:
            self.report({'ERROR'}, "No images found in folder")
            return {'CANCELLED'}
        
        suffix = props.output_suffix
        success = 0
        
        with core.progress(context.window_manager) as update:
            for i, (base_name, file_dict, default_file) in enumerate(base_images):
                update(int(100 * i / len(base_images)))
                
                # Skip if no channel files found
                if not file_dict and not default_file:
                    continue
                
                # Determine size from first available image
                width, height = props.output_width, props.output_height
                if width == 0 or height == 0:
                    sample_file = default_file or next(iter(file_dict.values()), None)
                    if sample_file:
                        sample_img = core.load_image(sample_file)
                        if sample_img:
                            width, height = sample_img.size
                    if width == 0 or height == 0:
                        width, height = 1024, 1024
                
                packed, color_mode = pack_from_files(file_dict, (height, width))
                output_name = base_name + suffix
                output_img = core.create_image(output_name, packed, 'Non-Color')
                out_path = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                core.save_image(output_img, out_path, props.file_format, color_mode, props.color_depth)
                success += 1
        
        self.report({'INFO'}, f"Packed {success} texture sets")
        return {'FINISHED'}


# ============================================================================
# UI Panel
# ============================================================================

class TEXOPS_PT_ChannelPacker(bpy.types.Panel):
    bl_label = "Channel Packer"
    bl_idname = "TEXOPS_PT_channel_packer"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'TexOps'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.texops_channel_packer
        
        box = layout.box()
        box.label(text="Input:", icon='NODE_COMPOSITING')
        row = box.row()
        row.prop(props, "input_mode", expand=True)
        
        if props.input_mode == 'SINGLE':
            for ch_name, ch_props in [('R', props.channel_r), ('G', props.channel_g),
                                       ('B', props.channel_b), ('A', props.channel_a)]:
                row = box.row(align=True)
                # Channel label
                sub = row.row()
                sub.scale_x = 0.4
                sub.label(text=ch_name)
                # Image search
                row.prop_search(ch_props, "image", bpy.data, "images", text="")
                # Load button
                op = row.operator("texops.channel_load_image", text="", icon='FILEBROWSER')
                op.channel = ch_name
                # Channel dropdown (narrow)
                sub = row.row()
                sub.scale_x = 0.55
                sub.prop(ch_props, "channel", text="")
                # Preview button
                sub = row.row(align=True)
                sub.enabled = bool(ch_props.image)
                op = sub.operator("texops.channel_preview", text="", icon='HIDE_OFF')
                op.channel = ch_name
        else:
            box.prop(props, "input_folder", text="")
            base_images = core.get_base_images_from_folder(props.input_folder)
            box.label(text=f"{len(base_images)} texture sets" if base_images else "No texture sets found",
                     icon='INFO' if base_images else 'ERROR')
        
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
        row.prop(props, "color_depth", text="")
        
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        row.operator("texops.channel_pack", icon='EXPORT')


# ============================================================================
# Registration
# ============================================================================

classes = (
    ChannelInput_Properties,
    ChannelPacker_Properties,
    TEXOPS_OT_ChannelPacker_LoadImage,
    TEXOPS_OT_ChannelPacker_Preview,
    TEXOPS_OT_ChannelPacker_Pack,
    TEXOPS_PT_ChannelPacker,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_channel_packer = bpy.props.PointerProperty(type=ChannelPacker_Properties)

def unregister():
    del bpy.types.Scene.texops_channel_packer
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)