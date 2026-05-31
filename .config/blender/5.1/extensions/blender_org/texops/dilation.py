"""
Dilation Module for TexOps
Expands RGB colors into transparent (alpha) regions
"""

import bpy
import numpy as np
import os

from . import core


# ============================================================================
# Core Dilation
# ============================================================================

def get_neighbor_offsets(style):
    """Get neighbor offsets based on dilation style."""
    if style == 'DIAMOND':
        return [(-1, 0), (1, 0), (0, -1), (0, 1)]
    return [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def dilate_texture(pixels, alpha_threshold=0.0, max_iterations=0, 
                   edge_offset=0, style='SQUARE', fill_alpha=True,
                   progress_callback=None):
    """Dilate RGB colors into transparent areas."""
    h, w = pixels.shape[:2]
    output = pixels.copy()
    
    base_mask = (output[:, :, 3] > alpha_threshold).astype(np.float32)
    if edge_offset != 0:
        base_mask = core.erode_dilate_mask(base_mask, edge_offset)
    
    filled = base_mask.copy()
    if progress_callback:
        progress_callback(10)
    
    if np.all(filled > 0) or not np.any(filled > 0):
        return output
    
    rgb = output[:, :, :3].copy()
    rgb[filled == 0] = 0
    
    offsets = get_neighbor_offsets(style)
    max_iter = max_iterations if max_iterations > 0 else max(w, h)
    
    for iteration in range(max_iter):
        if np.sum(filled == 0) == 0:
            break
        
        filled_pad = np.pad(filled, 1, mode='constant', constant_values=0)
        rgb_pad = np.pad(rgb, ((1, 1), (1, 1), (0, 0)), mode='constant', constant_values=0)
        
        neighbor_count = np.zeros((h, w), dtype=np.float32)
        neighbor_rgb = np.zeros((h, w, 3), dtype=np.float32)
        
        for dy, dx in offsets:
            n_filled = filled_pad[1+dy:h+1+dy, 1+dx:w+1+dx]
            n_rgb = rgb_pad[1+dy:h+1+dy, 1+dx:w+1+dx]
            neighbor_count += n_filled
            neighbor_rgb += n_rgb * n_filled[:, :, np.newaxis]
        
        to_fill = (filled == 0) & (neighbor_count > 0)
        if not np.any(to_fill):
            break
        
        with np.errstate(divide='ignore', invalid='ignore'):
            avg_rgb = np.nan_to_num(neighbor_rgb / neighbor_count[:, :, np.newaxis])
        
        rgb[to_fill] = avg_rgb[to_fill]
        output[to_fill, :3] = avg_rgb[to_fill]
        if fill_alpha:
            output[to_fill, 3] = 1.0
        filled[to_fill] = 1.0
        
        if progress_callback and iteration % 5 == 0:
            progress_callback(10 + int(80 * np.sum(filled) / (h * w)))
    
    return output


def generate_mask_preview(pixels, alpha_threshold, edge_offset):
    """Generate black/white mask preview."""
    h, w = pixels.shape[:2]
    mask = (pixels[:, :, 3] > alpha_threshold).astype(np.float32)
    if edge_offset != 0:
        mask = core.erode_dilate_mask(mask, edge_offset)
    
    output = np.zeros((h, w, 4), dtype=np.float32)
    output[:, :, :3] = mask[:, :, np.newaxis]
    output[:, :, 3] = 1.0
    return output


def process_single_image(input_img, props, progress_callback=None):
    """Process a single image with dilation."""
    pixels, w, h = core.read_pixels(input_img)
    
    fill_alpha = props.alpha_mode in ['FILL', 'REMOVE']
    dilated = dilate_texture(
        pixels, props.alpha_threshold, props.max_distance,
        props.edge_offset, props.style, fill_alpha, progress_callback
    )
    
    if props.alpha_mode == 'REMOVE':
        dilated[:, :, 3] = 1.0
    
    out_w, out_h = core.calculate_output_dimensions(props, w, h)
    if (out_w, out_h) != (w, h):
        dilated = core.resize_bilinear(dilated, out_h, out_w)
    
    return dilated


# ============================================================================
# Properties
# ============================================================================

_aspect = core.AspectRatioHelper()
get_depth_items = core.make_depth_items_callback("texops_dilation_props")


class Dilation_Properties(bpy.types.PropertyGroup):
    input_mode: bpy.props.EnumProperty(
        name="Mode",
        items=[('SINGLE', "Single", ""), ('BATCH', "Batch", "")],
        default='SINGLE'
    )
    input_image: bpy.props.StringProperty(name="Input Image", default="")
    input_folder: bpy.props.StringProperty(name="Input Folder", default="//", subtype='DIR_PATH')
    
    alpha_threshold: bpy.props.FloatProperty(name="Alpha Threshold", default=0.0, min=0.0, max=1.0)
    edge_offset: bpy.props.IntProperty(name="Edge Offset", default=0, min=-64, max=64)
    max_distance: bpy.props.IntProperty(name="Max Distance", default=0, min=0, max=1024)
    style: bpy.props.EnumProperty(
        name="Style",
        items=[('SQUARE', "Square", "8-connected"), ('DIAMOND', "Diamond", "4-connected")],
        default='SQUARE'
    )
    alpha_mode: bpy.props.EnumProperty(
        name="Alpha Mode",
        items=[('FILL', "Fill Alpha", ""), ('KEEP', "Keep Alpha", ""), ('REMOVE', "Remove Alpha", "")],
        default='FILL'
    )
    
    output_name: bpy.props.StringProperty(name="Output Name", default="")
    output_suffix: bpy.props.StringProperty(name="Suffix", default="_Dilated",
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

class TEXOPS_OT_Dilation_LoadImage(core.LoadImageOperatorBase):
    bl_idname = "texops.dilation_load_image"
    bl_label = "Load Image"
    def get_props(self, context):
        return context.scene.texops_dilation_props


class TEXOPS_OT_Dilation_ShowInput(core.ShowImageOperatorBase):
    bl_idname = "texops.dilation_show_input"
    bl_label = "Show Input"
    def get_props(self, context):
        return context.scene.texops_dilation_props


class TEXOPS_OT_Dilation_Generate(core.BatchConfirmMixin, bpy.types.Operator):
    """Dilate RGB colors into transparent areas"""
    bl_idname = "texops.dilation_generate"
    bl_label = "Dilate"
    bl_options = {'REGISTER', 'UNDO'}
    
    def get_props(self, context):
        return context.scene.texops_dilation_props
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_dilation_props
        if props.input_mode == 'BATCH':
            return self.execute_batch(context, props)
        return self.execute_single(context, props)
    
    def execute_single(self, context, props):
        input_img, error = core.get_input_image(props, self)
        if error:
            return error
        
        with core.progress(context.window_manager) as update:
            dilated = process_single_image(input_img, props, update)
            output_name = (props.output_name if props.output_name else input_img.name.rsplit('.', 1)[0]) + props.output_suffix
            output_img = core.create_image(output_name, dilated, input_img.colorspace_settings.name)
            filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
            
            # REMOVE mode discards alpha, otherwise preserve it
            color_mode = 'RGB' if props.alpha_mode == 'REMOVE' else 'RGBA'
            core.save_image(output_img, filepath, props.file_format, color_mode, props.color_depth)
            core.set_image_editor_image(context, output_img)
        
        self.report({'INFO'}, f"Saved: {filepath}")
        return {'FINISHED'}
    
    def execute_batch(self, context, props):
        files = core.get_images_from_folder(props.input_folder)
        if not files:
            self.report({'ERROR'}, "No images found in folder")
            return {'CANCELLED'}
        
        # REMOVE mode discards alpha, otherwise preserve it
        color_mode = 'RGB' if props.alpha_mode == 'REMOVE' else 'RGBA'
        
        success = 0
        with core.progress(context.window_manager) as update:
            for i, filepath in enumerate(files):
                update(int(100 * i / len(files)))
                input_img = core.load_image(filepath)
                if not input_img:
                    continue
                
                dilated = process_single_image(input_img, props)
                base_name = os.path.splitext(os.path.basename(filepath))[0]
                output_name = base_name + props.output_suffix
                output_img = core.create_image(output_name, dilated, input_img.colorspace_settings.name)
                out_path = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                core.save_image(output_img, out_path, props.file_format, color_mode, props.color_depth)
                success += 1
        
        self.report({'INFO'}, f"Processed {success}/{len(files)} images")
        return {'FINISHED'}


class TEXOPS_OT_Dilation_PreviewMask(bpy.types.Operator):
    """Preview the alpha mask"""
    bl_idname = "texops.dilation_preview_mask"
    bl_label = "Preview Mask"
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_dilation_props
        input_img, error = core.get_input_image(props, self)
        if error:
            return error
        
        pixels, w, h = core.read_pixels(input_img)
        preview_data = generate_mask_preview(pixels, props.alpha_threshold, props.edge_offset)
        preview = core.create_image("_Dilation_Mask_Preview", preview_data, 'Non-Color')
        core.set_image_editor_image(context, preview)
        return {'FINISHED'}


# ============================================================================
# UI Panel
# ============================================================================

class TEXOPS_PT_Dilation(bpy.types.Panel):
    bl_label = "Dilation"
    bl_idname = "TEXOPS_PT_dilation"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'TexOps'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.texops_dilation_props
        
        box = layout.box()
        box.label(text="Input:", icon='IMAGE_DATA')
        core.draw_batch_input_section(
            box, props, "texops.dilation_load_image", "texops.dilation_show_input",
            lambda f: len(core.get_images_from_folder(f)), "images"
        )
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Dilation Settings:", icon='FULLSCREEN_ENTER')
        box.prop(props, "alpha_threshold", slider=True)
        box.prop(props, "edge_offset")
        box.prop(props, "max_distance")
        box.prop(props, "style")
        box.prop(props, "alpha_mode")
        if props.input_mode == 'SINGLE':
            row = box.row()
            row.enabled = bool(props.input_image)
            row.operator("texops.dilation_preview_mask", icon='HIDE_OFF')
        
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
        
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        row.operator("texops.dilation_generate", icon='EXPORT')


# ============================================================================
# Registration
# ============================================================================

classes = (
    Dilation_Properties,
    TEXOPS_OT_Dilation_LoadImage,
    TEXOPS_OT_Dilation_ShowInput,
    TEXOPS_OT_Dilation_Generate,
    TEXOPS_OT_Dilation_PreviewMask,
    TEXOPS_PT_Dilation,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_dilation_props = bpy.props.PointerProperty(type=Dilation_Properties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.texops_dilation_props