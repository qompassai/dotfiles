"""
Image Tools Module for TexOps
Basic image operations: invert, grayscale, clear, flip, rotate, resize, crop, offset, scale
"""

import bpy
import numpy as np
import os

from . import core


# ============================================================================
# Helper Functions
# ============================================================================

def get_active_image(context):
    """Get the active image from the Image Editor."""
    space = context.space_data
    return space.image if space and space.type == 'IMAGE_EDITOR' else None


def get_source_image(context):
    """Get the source image, handling RGBA Preview."""
    image = get_active_image(context)
    if not image:
        return None, False
    
    if image.name == "_RGBA_Preview":
        props = getattr(context.scene, 'texops_rgba_props', None)
        if props and props.source_image:
            source = bpy.data.images.get(props.source_image)
            if source:
                return source, True
    
    return image, False


def refresh_rgba_preview(context, source_image):
    """Regenerate RGBA preview after modifying source image."""
    props = getattr(context.scene, 'texops_rgba_props', None)
    if not props or (props.show_r and props.show_g and props.show_b and props.show_a):
        return
    try:
        from . import rgba_toggles
        rgba_toggles.update_preview(context)
    except Exception:
        pass


def image_to_numpy(image):
    """Convert Blender image to numpy array."""
    w, h = image.size
    pixels = np.empty(w * h * image.channels, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    return pixels.reshape((h, w, image.channels)), w, h


def numpy_to_image(image, pixels):
    """Write numpy array back to Blender image."""
    image.pixels.foreach_set(pixels.ravel())
    image.update()


def is_valid_input_folder(folder_path):
    """Check if folder path is valid for batch processing (not root)."""
    if not folder_path:
        return False
    abs_path = bpy.path.abspath(folder_path)
    # Reject root paths
    if abs_path in ('/', '//', '\\', ''):
        return False
    if len(abs_path) <= 3 and ':' in abs_path:  # Windows root like C:\
        return False
    return os.path.isdir(abs_path)


# ============================================================================
# Undo System
# ============================================================================

_undo_stack = {}
_redo_stack = {}
MAX_UNDO = 20


def store_undo(image, name):
    """Store image state for undo."""
    key = image.name
    pixels = np.empty(image.size[0] * image.size[1] * image.channels, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    
    stack = _undo_stack.setdefault(key, [])
    stack.append({'name': name, 'pixels': pixels.copy(), 'size': tuple(image.size)})
    _redo_stack[key] = []
    
    if len(stack) > MAX_UNDO:
        stack.pop(0)


def _swap_state(image, from_stack, to_stack):
    """Swap image state between stacks. Returns operation name or None."""
    key = image.name
    if key not in from_stack or not from_stack[key]:
        return None
    
    # Save current state
    current = np.empty(image.size[0] * image.size[1] * image.channels, dtype=np.float32)
    image.pixels.foreach_get(current)
    
    state = from_stack[key].pop()
    to_stack.setdefault(key, []).append({
        'name': state['name'],
        'pixels': current.copy(),
        'size': tuple(image.size)
    })
    
    # Restore
    if tuple(image.size) != state['size']:
        image.scale(*state['size'])
    image.pixels.foreach_set(state['pixels'])
    image.update()
    return state['name']


def pop_undo(image):
    return _swap_state(image, _undo_stack, _redo_stack)


def pop_redo(image):
    return _swap_state(image, _redo_stack, _undo_stack)


def get_undo_count(image):
    return len(_undo_stack.get(image.name, []))


def get_redo_count(image):
    return len(_redo_stack.get(image.name, []))


# ============================================================================
# Properties
# ============================================================================

_updating_aspect = False


def update_resize_width(self, context):
    global _updating_aspect
    if _updating_aspect or not self.resize_lock_aspect:
        return
    source_image, _ = get_source_image(context)
    if not source_image or source_image.size[0] == 0:
        return
    _updating_aspect = True
    self.resize_height = max(1, int(self.resize_width * source_image.size[1] / source_image.size[0]))
    _updating_aspect = False


def update_resize_height(self, context):
    global _updating_aspect
    if _updating_aspect or not self.resize_lock_aspect:
        return
    source_image, _ = get_source_image(context)
    if not source_image or source_image.size[1] == 0:
        return
    _updating_aspect = True
    self.resize_width = max(1, int(self.resize_height * source_image.size[0] / source_image.size[1]))
    _updating_aspect = False


class ImageTools_Properties(bpy.types.PropertyGroup):
    # Mode
    input_mode: bpy.props.EnumProperty(
        name="Mode",
        items=[('CURRENT', "Current", "Edit current image"),
               ('BATCH', "Batch", "Process folder of images")],
        default='CURRENT'
    )
    input_folder: bpy.props.StringProperty(name="Input Folder", default="", subtype='DIR_PATH')
    output_folder: bpy.props.StringProperty(name="Output Folder", default="", subtype='DIR_PATH')
    
    # Resize
    resize_width: bpy.props.IntProperty(name="Width", default=1024, min=1, max=16384, update=update_resize_width)
    resize_height: bpy.props.IntProperty(name="Height", default=1024, min=1, max=16384, update=update_resize_height)
    resize_lock_aspect: bpy.props.BoolProperty(name="Lock Aspect", default=True)
    resize_method: bpy.props.EnumProperty(
        name="Method",
        items=[('NEAREST', "Nearest", ""), ('BILINEAR', "Bilinear", ""), ('BICUBIC', "Bicubic", "")],
        default='BILINEAR'
    )
    
    # Crop
    crop_left: bpy.props.IntProperty(name="Left", default=0, min=0)
    crop_right: bpy.props.IntProperty(name="Right", default=0, min=0)
    crop_top: bpy.props.IntProperty(name="Top", default=0, min=0)
    crop_bottom: bpy.props.IntProperty(name="Bottom", default=0, min=0)
    
    # Offset/Scale
    offset_x: bpy.props.IntProperty(name="X", default=0)
    offset_y: bpy.props.IntProperty(name="Y", default=0)
    scale_percent: bpy.props.FloatProperty(name="Scale %", default=100.0, min=1.0, max=1000.0)


# ============================================================================
# Base Operator
# ============================================================================

class ImageToolOperator(core.BatchConfirmMixin, bpy.types.Operator):
    """Base class for image tool operators."""
    
    def apply_operation(self, pixels, w, h, props):
        return pixels
    
    def get_operation_name(self):
        return "Operation"
    
    def get_props(self, context):
        return context.scene.texops_imagetools_props
    
    def get_image(self, context):
        source_image, is_preview = get_source_image(context)
        if not source_image:
            self.report({'ERROR'}, "No active image")
        return source_image, is_preview
    
    def finish(self, context, source_image, is_preview, message):
        if is_preview:
            refresh_rgba_preview(context, source_image)
        self.report({'INFO'}, message)
        return {'FINISHED'}
    
    def execute(self, context):
        props = self.get_props(context)
        if props.input_mode == 'BATCH':
            return self.execute_batch(context, props)
        return self.execute_single(context, props)
    
    def execute_single(self, context, props):
        source_image, is_preview = self.get_image(context)
        if not source_image:
            return {'CANCELLED'}
        
        store_undo(source_image, self.get_operation_name())
        pixels, w, h = image_to_numpy(source_image)
        pixels = self.apply_operation(pixels, w, h, props)
        
        new_h, new_w = pixels.shape[:2]
        if (new_w, new_h) != (w, h):
            source_image.scale(new_w, new_h)
        
        numpy_to_image(source_image, pixels)
        return self.finish(context, source_image, is_preview, self.get_operation_name())
    
    def execute_batch(self, context, props):
        if not is_valid_input_folder(props.input_folder):
            self.report({'ERROR'}, "Invalid input folder")
            return {'CANCELLED'}
        
        image_files = core.get_images_from_folder(props.input_folder)
        if not image_files:
            self.report({'ERROR'}, "No images found in folder")
            return {'CANCELLED'}
        
        folder = bpy.path.abspath(props.input_folder)
        output_folder = bpy.path.abspath(props.output_folder) if props.output_folder else folder
        os.makedirs(output_folder, exist_ok=True)
        
        success = 0
        for filepath in image_files:
            try:
                img = bpy.data.images.load(filepath, check_existing=False)
                pixels, w, h = image_to_numpy(img)
                pixels = self.apply_operation(pixels, w, h, props)
                
                new_h, new_w = pixels.shape[:2]
                if (new_w, new_h) != (w, h):
                    img.scale(new_w, new_h)
                numpy_to_image(img, pixels)
                
                out_path = os.path.join(output_folder, os.path.basename(filepath))
                img.filepath_raw = out_path
                img.save()
                bpy.data.images.remove(img)
                success += 1
            except Exception as e:
                print(f"Failed to process {filepath}: {e}")
        
        self.report({'INFO'}, f"{self.get_operation_name()}: {success}/{len(image_files)} images")
        return {'FINISHED'}


# ============================================================================
# Undo/Redo Operators
# ============================================================================

class TEXOPS_OT_ImageTools_Undo(bpy.types.Operator):
    bl_idname = "texops.imagetools_undo"
    bl_label = "Undo"
    
    def execute(self, context):
        source_image, is_preview = get_source_image(context)
        if not source_image:
            return {'CANCELLED'}
        name = pop_undo(source_image)
        if name:
            if is_preview:
                refresh_rgba_preview(context, source_image)
            self.report({'INFO'}, f"Undone: {name}")
            return {'FINISHED'}
        self.report({'WARNING'}, "Nothing to undo")
        return {'CANCELLED'}


class TEXOPS_OT_ImageTools_Redo(bpy.types.Operator):
    bl_idname = "texops.imagetools_redo"
    bl_label = "Redo"
    
    def execute(self, context):
        source_image, is_preview = get_source_image(context)
        if not source_image:
            return {'CANCELLED'}
        name = pop_redo(source_image)
        if name:
            if is_preview:
                refresh_rgba_preview(context, source_image)
            self.report({'INFO'}, f"Redone: {name}")
            return {'FINISHED'}
        self.report({'WARNING'}, "Nothing to redo")
        return {'CANCELLED'}


# ============================================================================
# Invert Operators
# ============================================================================

class TEXOPS_OT_InvertRGB(ImageToolOperator):
    bl_idname = "texops.invert_rgb"
    bl_label = "Invert RGB"
    
    def get_operation_name(self):
        return "Invert RGB"
    
    def apply_operation(self, pixels, w, h, props):
        pixels = pixels.copy()
        pixels[:, :, :3] = 1.0 - pixels[:, :, :3]
        return pixels


class TEXOPS_OT_InvertRGBA(ImageToolOperator):
    bl_idname = "texops.invert_rgba"
    bl_label = "Invert RGBA"
    
    def get_operation_name(self):
        return "Invert RGBA"
    
    def apply_operation(self, pixels, w, h, props):
        return 1.0 - pixels


class TEXOPS_OT_InvertChannel(ImageToolOperator):
    bl_idname = "texops.invert_channel"
    bl_label = "Invert Channel"
    
    channel: bpy.props.IntProperty(default=0)
    
    def get_operation_name(self):
        return f"Invert {'RGBA'[self.channel]}"
    
    def apply_operation(self, pixels, w, h, props):
        pixels = pixels.copy()
        pixels[:, :, self.channel] = 1.0 - pixels[:, :, self.channel]
        return pixels
    
    def execute_single(self, context, props):
        source_image, _ = self.get_image(context)
        if not source_image:
            return {'CANCELLED'}
        if self.channel == 3 and source_image.channels < 4:
            self.report({'WARNING'}, "Image has no alpha channel")
            return {'CANCELLED'}
        return super().execute_single(context, props)


# ============================================================================
# Clear / Grayscale Operators
# ============================================================================

class TEXOPS_OT_ClearChannel(ImageToolOperator):
    bl_idname = "texops.clear_channel"
    bl_label = "Clear Channel"
    
    channel: bpy.props.IntProperty(default=0)
    
    def get_operation_name(self):
        return f"Clear {'RGBA'[self.channel]}"
    
    def apply_operation(self, pixels, w, h, props):
        pixels = pixels.copy()
        pixels[:, :, self.channel] = 1.0 if self.channel == 3 else 0.0
        return pixels
    
    def execute_single(self, context, props):
        source_image, _ = self.get_image(context)
        if not source_image:
            return {'CANCELLED'}
        if self.channel == 3 and source_image.channels < 4:
            self.report({'WARNING'}, "Image has no alpha channel")
            return {'CANCELLED'}
        return super().execute_single(context, props)


class TEXOPS_OT_MakeGrayscale(ImageToolOperator):
    bl_idname = "texops.make_grayscale"
    bl_label = "Make Grayscale"
    
    def get_operation_name(self):
        return "Grayscale"
    
    def apply_operation(self, pixels, w, h, props):
        pixels = pixels.copy()
        gray = pixels[:, :, 0] * 0.2126 + pixels[:, :, 1] * 0.7152 + pixels[:, :, 2] * 0.0722
        pixels[:, :, 0] = pixels[:, :, 1] = pixels[:, :, 2] = gray
        return pixels


# ============================================================================
# Flip/Mirror Operators
# ============================================================================

class TEXOPS_OT_FlipH(ImageToolOperator):
    bl_idname = "texops.flip_h"
    bl_label = "Flip Horizontal"
    
    def get_operation_name(self):
        return "Flip H"
    
    def apply_operation(self, pixels, w, h, props):
        return np.flip(pixels, axis=1)


class TEXOPS_OT_FlipV(ImageToolOperator):
    bl_idname = "texops.flip_v"
    bl_label = "Flip Vertical"
    
    def get_operation_name(self):
        return "Flip V"
    
    def apply_operation(self, pixels, w, h, props):
        return np.flip(pixels, axis=0)


class TEXOPS_OT_Mirror(ImageToolOperator):
    bl_idname = "texops.mirror"
    bl_label = "Mirror"
    
    direction: bpy.props.StringProperty(default='LR')
    
    _labels = {'LR': 'Mirror L->R', 'RL': 'Mirror R->L', 'TB': 'Mirror T->B', 'BT': 'Mirror B->T'}
    
    def get_operation_name(self):
        return self._labels.get(self.direction, "Mirror")
    
    def apply_operation(self, pixels, w, h, props):
        pixels = pixels.copy()
        d = self.direction
        if d in ('LR', 'RL'):
            mid = w // 2
            if d == 'LR':
                # Copy left half to right half (flipped)
                right_size = w - mid
                pixels[:, mid:, :] = np.flip(pixels[:, :right_size, :], axis=1)
            else:
                # Copy right half to left half (flipped)
                pixels[:, :mid, :] = np.flip(pixels[:, w - mid:, :], axis=1)
        else:
            mid = h // 2
            if d == 'TB':
                # Copy bottom half to top half (flipped)
                pixels[:mid, :, :] = np.flip(pixels[h - mid:, :, :], axis=0)
            else:
                # Copy top half to bottom half (flipped)
                bottom_size = h - mid
                pixels[mid:, :, :] = np.flip(pixels[:bottom_size, :, :], axis=0)
        return pixels


# ============================================================================
# Rotate Operators
# ============================================================================

class TEXOPS_OT_Rotate(ImageToolOperator):
    bl_idname = "texops.rotate"
    bl_label = "Rotate"
    
    angle: bpy.props.IntProperty(default=90)
    
    def get_operation_name(self):
        return f"Rotate {self.angle}"
    
    def apply_operation(self, pixels, w, h, props):
        k = {90: -1, -90: 1, 180: 2}.get(self.angle, 2)
        return np.rot90(pixels, k=k)


# ============================================================================
# Transform Operators
# ============================================================================

def resize_pixels(pixels, new_w, new_h, method):
    """Resize pixels using specified method."""
    old_h, old_w, ch = pixels.shape
    
    if method == 'NEAREST':
        row_idx = np.clip((np.arange(new_h) * old_h / new_h).astype(int), 0, old_h - 1)
        col_idx = np.clip((np.arange(new_w) * old_w / new_w).astype(int), 0, old_w - 1)
        return pixels[row_idx[:, np.newaxis], col_idx, :].astype(np.float32)
    
    elif method == 'BILINEAR':
        y = np.arange(new_h) * (old_h - 1) / max(new_h - 1, 1)
        x = np.arange(new_w) * (old_w - 1) / max(new_w - 1, 1)
        y0, x0 = np.floor(y).astype(int), np.floor(x).astype(int)
        y1, x1 = np.clip(y0 + 1, 0, old_h - 1), np.clip(x0 + 1, 0, old_w - 1)
        y0, x0 = np.clip(y0, 0, old_h - 1), np.clip(x0, 0, old_w - 1)
        fy, fx = (y - y0).reshape(-1, 1, 1), (x - x0).reshape(1, -1, 1)
        return (pixels[y0][:, x0] * (1-fx) * (1-fy) + 
                pixels[y0][:, x1] * fx * (1-fy) + 
                pixels[y1][:, x0] * (1-fx) * fy + 
                pixels[y1][:, x1] * fx * fy).astype(np.float32)
    
    else:  # BICUBIC
        def cubic_weight(t):
            t = np.abs(t)
            r = np.zeros_like(t)
            m1, m2 = t <= 1, (t > 1) & (t <= 2)
            r[m1] = 1.5 * t[m1]**3 - 2.5 * t[m1]**2 + 1
            r[m2] = -0.5 * t[m2]**3 + 2.5 * t[m2]**2 - 4 * t[m2] + 2
            return r
        
        y = np.arange(new_h) * (old_h - 1) / max(new_h - 1, 1)
        x = np.arange(new_w) * (old_w - 1) / max(new_w - 1, 1)
        y0, x0 = np.floor(y).astype(int), np.floor(x).astype(int)
        fy, fx = y - y0, x - x0
        
        output = np.zeros((new_h, new_w, ch), dtype=np.float32)
        for j in range(-1, 3):
            wy = cubic_weight(j - fy)
            py = np.clip(y0 + j, 0, old_h - 1)
            for i in range(-1, 3):
                wx = cubic_weight(i - fx)
                px = np.clip(x0 + i, 0, old_w - 1)
                weight = (wy[:, np.newaxis] * wx[np.newaxis, :])[:, :, np.newaxis]
                output += pixels[py][:, px] * weight
        return np.clip(output, 0.0, 1.0).astype(np.float32)


class TEXOPS_OT_Resize(ImageToolOperator):
    bl_idname = "texops.resize"
    bl_label = "Resize"
    
    def get_operation_name(self):
        return "Resize"
    
    def apply_operation(self, pixels, w, h, props):
        return resize_pixels(pixels, props.resize_width, props.resize_height, props.resize_method)


class TEXOPS_OT_GetImageSize(bpy.types.Operator):
    bl_idname = "texops.get_image_size"
    bl_label = "Get Size"
    bl_options = {'INTERNAL'}
    
    def execute(self, context):
        global _updating_aspect
        source_image, _ = get_source_image(context)
        if not source_image:
            return {'CANCELLED'}
        props = context.scene.texops_imagetools_props
        _updating_aspect = True
        props.resize_width, props.resize_height = source_image.size
        _updating_aspect = False
        return {'FINISHED'}


class TEXOPS_OT_Crop(ImageToolOperator):
    bl_idname = "texops.crop"
    bl_label = "Crop"
    
    def get_operation_name(self):
        return "Crop"
    
    def apply_operation(self, pixels, w, h, props):
        left, right, top, bottom = props.crop_left, props.crop_right, props.crop_top, props.crop_bottom
        end_y = h - top if top else h
        end_x = w - right if right else w
        return pixels[bottom:end_y, left:end_x, :].copy()
    
    def _validate_crop(self, props, w=None, h=None):
        left, right, top, bottom = props.crop_left, props.crop_right, props.crop_top, props.crop_bottom
        if left == 0 and right == 0 and top == 0 and bottom == 0:
            return "No crop specified"
        if w and h:
            if w - left - right <= 0 or h - top - bottom <= 0:
                return "Crop values too large"
        return None
    
    def execute_single(self, context, props):
        source_image, _ = self.get_image(context)
        if not source_image:
            return {'CANCELLED'}
        
        error = self._validate_crop(props, source_image.size[0], source_image.size[1])
        if error:
            self.report({'WARNING' if 'No crop' in error else 'ERROR'}, error)
            return {'CANCELLED'}
        return super().execute_single(context, props)
    
    def execute_batch(self, context, props):
        error = self._validate_crop(props)
        if error:
            self.report({'WARNING'}, error)
            return {'CANCELLED'}
        return super().execute_batch(context, props)


class TEXOPS_OT_Offset(ImageToolOperator):
    bl_idname = "texops.offset"
    bl_label = "Offset"
    
    def get_operation_name(self):
        return "Offset"
    
    def apply_operation(self, pixels, w, h, props):
        return np.roll(np.roll(pixels, props.offset_x, axis=1), props.offset_y, axis=0)
    
    def _check_offset(self, props):
        if props.offset_x == 0 and props.offset_y == 0:
            self.report({'WARNING'}, "No offset specified")
            return False
        return True
    
    def execute_single(self, context, props):
        return super().execute_single(context, props) if self._check_offset(props) else {'CANCELLED'}
    
    def execute_batch(self, context, props):
        return super().execute_batch(context, props) if self._check_offset(props) else {'CANCELLED'}


class TEXOPS_OT_Scale(ImageToolOperator):
    bl_idname = "texops.scale"
    bl_label = "Scale"
    
    def get_operation_name(self):
        return "Scale (tile)"
    
    def apply_operation(self, pixels, w, h, props):
        scale = props.scale_percent / 100.0
        tile_w, tile_h = max(1, int(w * scale)), max(1, int(h * scale))
        
        row_idx = np.clip((np.arange(tile_h) * h / tile_h).astype(int), 0, h - 1)
        col_idx = np.clip((np.arange(tile_w) * w / tile_w).astype(int), 0, w - 1)
        tile = pixels[row_idx[:, np.newaxis], col_idx, :]
        
        output = np.zeros_like(pixels)
        for y in range(0, h, tile_h):
            for x in range(0, w, tile_w):
                y_end, x_end = min(y + tile_h, h), min(x + tile_w, w)
                output[y:y_end, x:x_end, :] = tile[:y_end-y, :x_end-x, :]
        return output
    
    def _check_scale(self, props):
        if props.scale_percent == 100.0:
            self.report({'WARNING'}, "Scale is 100%")
            return False
        return True
    
    def execute_single(self, context, props):
        return super().execute_single(context, props) if self._check_scale(props) else {'CANCELLED'}
    
    def execute_batch(self, context, props):
        return super().execute_batch(context, props) if self._check_scale(props) else {'CANCELLED'}


# ============================================================================
# UI Panel
# ============================================================================

class TEXOPS_PT_ImageTools(bpy.types.Panel):
    bl_label = "Image Tools"
    bl_idname = "TEXOPS_PT_imagetools"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'TexOps'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.texops_imagetools_props
        source_image, _ = get_source_image(context)
        is_batch = props.input_mode == 'BATCH'
        
        # Mode toggle
        layout.row().prop(props, "input_mode", expand=True)
        
        # Batch input folder
        if is_batch:
            box = layout.box()
            box.label(text="Input Folder:", icon='IMPORT')
            box.prop(props, "input_folder", text="")
            valid = is_valid_input_folder(props.input_folder)
            if valid:
                count = len(core.get_images_from_folder(props.input_folder))
                box.label(text=f"{count} images", icon='INFO' if count else 'ERROR')
            else:
                box.label(text="Set a valid folder path", icon='ERROR')
            layout.separator()
        
        # Undo/Redo (current mode only)
        if not is_batch and source_image:
            row = layout.row(align=True)
            undo_count, redo_count = get_undo_count(source_image), get_redo_count(source_image)
            sub = row.row(align=True)
            sub.enabled = undo_count > 0
            sub.operator("texops.imagetools_undo", text=f"Undo ({undo_count})", icon='LOOP_BACK')
            sub = row.row(align=True)
            sub.enabled = redo_count > 0
            sub.operator("texops.imagetools_redo", text=f"Redo ({redo_count})", icon='LOOP_FORWARDS')
            layout.separator()
        
        # Invert
        box = layout.box()
        box.label(text="Invert:", icon='MODIFIER')
        row = box.row(align=True)
        row.operator("texops.invert_rgb", text="RGB")
        row.operator("texops.invert_rgba", text="RGBA")
        row = box.row(align=True)
        for i, ch in enumerate("RGBA"):
            row.operator("texops.invert_channel", text=ch).channel = i
        
        layout.separator()
        
        # Clear
        box = layout.box()
        box.label(text="Clear:", icon='X')
        row = box.row(align=True)
        for i, ch in enumerate("RGBA"):
            row.operator("texops.clear_channel", text=ch).channel = i
        box.operator("texops.make_grayscale", text="Grayscale")
        
        layout.separator()
        
        # Flip/Mirror
        box = layout.box()
        box.label(text="Flip / Mirror:", icon='MOD_MIRROR')
        row = box.row(align=True)
        row.operator("texops.flip_h", text="Flip H")
        row.operator("texops.flip_v", text="Flip V")
        row = box.row(align=True)
        for d, label in (('LR', "L"), ('RL', "R"), ('TB', "T"), ('BT', "B")):
            row.operator("texops.mirror", text=label).direction = d
        
        layout.separator()
        
        # Rotate
        box = layout.box()
        box.label(text="Rotate:", icon='FILE_REFRESH')
        row = box.row(align=True)
        for angle, label in ((-90, "-90"), (180, "180"), (90, "+90")):
            row.operator("texops.rotate", text=label).angle = angle
        
        layout.separator()
        
        # Resize
        box = layout.box()
        box.label(text="Resize:", icon='FULLSCREEN_ENTER')
        if not is_batch and source_image:
            box.label(text=f"Current: {source_image.size[0]} x {source_image.size[1]}")
        row = box.row(align=True)
        row.prop(props, "resize_lock_aspect", text="", icon='LOCKED' if props.resize_lock_aspect else 'UNLOCKED', toggle=True)
        row.prop(props, "resize_width")
        row.prop(props, "resize_height")
        box.prop(props, "resize_method", text="")
        row = box.row(align=True)
        if not is_batch:
            row.operator("texops.get_image_size", text="Get Size")
        row.operator("texops.resize", text="Resize")
        
        layout.separator()
        
        # Crop
        box = layout.box()
        box.label(text="Crop:", icon='SELECT_SUBTRACT')
        row = box.row(align=True)
        row.prop(props, "crop_left", text="L")
        row.prop(props, "crop_right", text="R")
        row = box.row(align=True)
        row.prop(props, "crop_top", text="T")
        row.prop(props, "crop_bottom", text="B")
        box.operator("texops.crop", text="Apply Crop")
        
        layout.separator()
        
        # Offset
        box = layout.box()
        box.label(text="Offset (wrap):", icon='VIEW_PAN')
        row = box.row(align=True)
        row.prop(props, "offset_x")
        row.prop(props, "offset_y")
        box.operator("texops.offset", text="Apply Offset")
        
        layout.separator()
        
        # Scale
        box = layout.box()
        box.label(text="Scale (tile):", icon='TEXTURE')
        row = box.row(align=True)
        row.prop(props, "scale_percent", text="%")
        row.operator("texops.scale", text="Scale")
        
        # Batch output folder
        if is_batch:
            layout.separator()
            box = layout.box()
            box.label(text="Output Folder:", icon='EXPORT')
            box.prop(props, "output_folder", text="")


# ============================================================================
# Registration
# ============================================================================

classes = (
    ImageTools_Properties,
    TEXOPS_OT_ImageTools_Undo,
    TEXOPS_OT_ImageTools_Redo,
    TEXOPS_OT_InvertRGB,
    TEXOPS_OT_InvertRGBA,
    TEXOPS_OT_InvertChannel,
    TEXOPS_OT_MakeGrayscale,
    TEXOPS_OT_ClearChannel,
    TEXOPS_OT_FlipH,
    TEXOPS_OT_FlipV,
    TEXOPS_OT_Mirror,
    TEXOPS_OT_Rotate,
    TEXOPS_OT_Resize,
    TEXOPS_OT_GetImageSize,
    TEXOPS_OT_Crop,
    TEXOPS_OT_Offset,
    TEXOPS_OT_Scale,
    TEXOPS_PT_ImageTools,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_imagetools_props = bpy.props.PointerProperty(type=ImageTools_Properties)


def unregister():
    global _undo_stack, _redo_stack
    _undo_stack = {}
    _redo_stack = {}
    del bpy.types.Scene.texops_imagetools_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)