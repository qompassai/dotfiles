"""
Core Module for TexOps
Shared utilities: pixel I/O, properties, operators, UI helpers, batch processing
"""

import bpy
import numpy as np
import os
import traceback
from functools import wraps
from contextlib import contextmanager
from bpy_extras.io_utils import ImportHelper


# ============================================================================
# Channel Constants
# ============================================================================

CHANNEL_ITEMS = [
    ('R', "R", "Red channel"),
    ('G', "G", "Green channel"),
    ('B', "B", "Blue channel"),
    ('A', "A", "Alpha channel"),
    ('GRAY', "Gray", "Grayscale (luminance)"),
]

CHANNEL_ITEMS_WITH_CONSTANTS = CHANNEL_ITEMS + [
    ('WHITE', "1.0", "Constant white"),
    ('BLACK', "0.0", "Constant black"),
]

CHANNEL_MAP = {'R': 0, 'G': 1, 'B': 2, 'A': 3}

# Grayscale weights (Rec. 709)
GRAY_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


# ============================================================================
# Internal Pixel I/O
# ============================================================================

def _load_pixels_rgba(image):
    """Internal: Load image pixels as RGBA numpy array (H, W, 4)."""
    w, h = image.size
    channels = image.channels
    pixels = np.empty(w * h * channels, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape((h, w, channels))
    
    if channels < 4:
        rgba = np.ones((h, w, 4), dtype=np.float32)
        rgba[:, :, :channels] = pixels
        return rgba, w, h
    
    return pixels, w, h


def _to_grayscale(rgb):
    """Internal: Convert RGB(A) array to grayscale using Rec. 709 weights."""
    return rgb[:, :, 0] * GRAY_WEIGHTS[0] + rgb[:, :, 1] * GRAY_WEIGHTS[1] + rgb[:, :, 2] * GRAY_WEIGHTS[2]


# ============================================================================
# Pixel Cache (Singleton)
# ============================================================================

class PixelCache:
    """Cache source image pixels to avoid repeated reads."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = {}
        return cls._instance
    
    def get(self, image):
        """Get cached pixels or load from image. Returns (pixels, w, h)."""
        key = (image.name, image.size[0], image.size[1], image.is_dirty)
        
        if key in self._data:
            return self._data[key]
        
        # Clear old entries for this image
        self._data = {k: v for k, v in self._data.items() if k[0] != image.name}
        
        # Load and cache
        result = _load_pixels_rgba(image)
        self._data[key] = result
        return result
    
    def invalidate(self, image_name=None):
        """Clear cache. If image_name given, only clear that image."""
        if image_name:
            self._data = {k: v for k, v in self._data.items() if k[0] != image_name}
        else:
            self._data = {}


_cache = PixelCache()


# ============================================================================
# Fast Pixel I/O (Public API)
# ============================================================================

def read_pixels(image):
    """
    Read image pixels as RGBA numpy array.
    Returns (pixels, width, height) where pixels is (H, W, 4).
    """
    return _load_pixels_rgba(image)


def read_pixels_cached(image):
    """Read pixels with caching (use for repeated reads of same image)."""
    return _cache.get(image)


def read_pixels_grayscale(image, channel='GRAY'):
    """
    Read image as grayscale array.
    
    Args:
        image: Blender image
        channel: 'R', 'G', 'B', 'A', or 'GRAY' (luminance)
    
    Returns:
        (grayscale_array, width, height) where array is (H, W)
    """
    pixels, w, h = _load_pixels_rgba(image)
    
    if channel == 'GRAY':
        return _to_grayscale(pixels), w, h
    
    ch_idx = CHANNEL_MAP.get(channel, 0)
    return pixels[:, :, ch_idx], w, h


def create_image(name, pixels, colorspace='sRGB', float_buffer=False):
    """
    Create Blender image from numpy array.
    
    Args:
        name: Image name (existing image with same name will be replaced)
        pixels: (H, W, 4) numpy array
        colorspace: Colorspace name
        float_buffer: If True, create 32-bit float image (needed for 16-bit+ precision)
    
    Returns:
        Blender image
    """
    h, w = pixels.shape[:2]
    
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    
    img = bpy.data.images.new(name, width=w, height=h, alpha=True, float_buffer=float_buffer)
    img.colorspace_settings.name = colorspace
    img.pixels.foreach_set(pixels.ravel().astype(np.float32))
    img.update()
    
    return img


def extract_channel(image, channel_type, default_size, default_value=0.0):
    """
    Extract a single channel from an image.
    
    Args:
        image: Blender image or None
        channel_type: 'R', 'G', 'B', 'A', 'GRAY', 'WHITE', or 'BLACK'
        default_size: (height, width) tuple for output if no image
        default_value: Value to use when image is None (0.0 or 1.0)
    
    Returns:
        (H, W) numpy array of float32
    """
    height, width = default_size
    
    if channel_type == 'WHITE':
        return np.ones((height, width), dtype=np.float32)
    if channel_type == 'BLACK':
        return np.zeros((height, width), dtype=np.float32)
    if not image:
        return np.full((height, width), default_value, dtype=np.float32)
    
    pixels, w, h = _load_pixels_rgba(image)
    
    if channel_type == 'GRAY':
        return _to_grayscale(pixels)
    
    return pixels[:, :, CHANNEL_MAP.get(channel_type, 0)]


# ============================================================================
# Dithering and Quantization
# ============================================================================

BAYER_8x8 = np.array([
    [ 0, 32,  8, 40,  2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44,  4, 36, 14, 46,  6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [ 3, 35, 11, 43,  1, 33,  9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47,  7, 39, 13, 45,  5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21]
], dtype=np.float32) / 64.0 - 0.5


def apply_dither(data, bits, dither_mode, height, width):
    """
    Apply dithering before quantization to reduce banding.
    
    Args:
        data: (H, W) numpy array of float values
        bits: Target bit depth
        dither_mode: 'NONE', 'ORDERED', 'NOISE', or 'BLUE'
        height, width: Dimensions of data
    
    Returns:
        Dithered data array
    """
    if dither_mode == 'NONE' or bits >= 8:
        return data
    
    max_val = (1 << bits) - 1
    step = 1.0 / max_val
    
    if dither_mode == 'ORDERED':
        y_idx = np.arange(height) % 8
        x_idx = np.arange(width) % 8
        dither = BAYER_8x8[y_idx[:, np.newaxis], x_idx] * step
        return data + dither
    elif dither_mode == 'NOISE':
        noise = (np.random.random((height, width)).astype(np.float32) - 0.5) * step
        return data + noise
    elif dither_mode == 'BLUE':
        y, x = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')
        noise = np.mod(52.9829189 * np.mod(0.06711056 * x + 0.00583715 * y, 1.0), 1.0)
        return data + (noise.astype(np.float32) - 0.5) * step
    return data


def quantize(data, bits):
    """
    Quantize float data to N bits.
    
    Args:
        data: Numpy array of float values in 0-1 range
        bits: Target bit depth
    
    Returns:
        Quantized data as uint32 array
    """
    max_val = (1 << bits) - 1
    return np.round(np.clip(data, 0, 1) * max_val).astype(np.uint32)


# ============================================================================
# Progress Context Manager
# ============================================================================

@contextmanager
def progress(wm, start=0, end=100):
    """
    Context manager for progress bar.
    
    Usage:
        with core.progress(context.window_manager) as update:
            update(25)
            do_work()
            update(75)
    """
    wm.progress_begin(start, end)
    try:
        yield wm.progress_update
    finally:
        wm.progress_end()


# ============================================================================
# Error Handling Decorator
# ============================================================================

def with_error_handling(execute_func):
    """
    Decorator for operator execute methods that adds standard error handling.
    
    Usage:
        @core.with_error_handling
        def execute(self, context):
            # ... do work ...
            return {'FINISHED'}
    """
    @wraps(execute_func)
    def wrapper(self, context):
        try:
            return execute_func(self, context)
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            traceback.print_exc()
            return {'CANCELLED'}
    return wrapper


# ============================================================================
# File Format Helpers
# ============================================================================

FORMAT_EXTENSIONS = {
    'PNG': '.png',
    'JPEG': '.jpg',
    'TARGA': '.tga',
    'TIFF': '.tif',
    'OPEN_EXR': '.exr',
    'HDR': '.hdr',
    'BMP': '.bmp',
}

FORMAT_DEPTHS = {
    'PNG': ['8', '16'],
    'JPEG': ['8'],
    'TARGA': ['8'],
    'TIFF': ['8', '16'],
    'OPEN_EXR': ['16', '32'],
    'HDR': ['32'],
    'BMP': ['8'],
}


def get_format_items(self, context):
    """Standard format dropdown items."""
    return [
        ('PNG', "PNG", "PNG format"),
        ('JPEG', "JPEG", "JPEG format"),
        ('TARGA', "TGA", "Targa format"),
        ('TIFF', "TIFF", "TIFF format"),
        ('OPEN_EXR', "EXR", "OpenEXR format"),
    ]


def make_depth_items_callback(prop_group_name):
    """
    Create a callback for color depth items based on current format.
    
    Usage:
        get_depth_items = core.make_depth_items_callback("texops_my_props")
        
        class MyProps(PropertyGroup):
            color_depth: EnumProperty(items=get_depth_items)
    """
    def get_depth_items(self, context):
        props = getattr(context.scene, prop_group_name, None)
        if not props:
            return [('8', "8-bit", ""), ('16', "16-bit", "")]
        
        fmt = getattr(props, 'file_format', 'PNG')
        depths = FORMAT_DEPTHS.get(fmt, ['8', '16'])
        
        items = []
        if '8' in depths:
            items.append(('8', "8-bit", "8 bits per channel"))
        if '16' in depths:
            items.append(('16', "16-bit", "16 bits per channel"))
        if '32' in depths:
            items.append(('32', "32-bit", "32 bits per channel"))
        
        return items if items else [('8', "8-bit", "")]
    
    return get_depth_items


def update_depth_for_format(self, context):
    """Update color depth when format changes to ensure valid combination."""
    fmt = self.file_format
    depths = FORMAT_DEPTHS.get(fmt, ['8', '16'])
    
    if hasattr(self, 'color_depth') and self.color_depth not in depths:
        self.color_depth = depths[0]


# ============================================================================
# File I/O Helpers
# ============================================================================

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tga', '.bmp', '.tiff', '.tif', '.exr', '.hdr'}


def get_images_from_folder(folder_path):
    """Get list of image file paths from folder."""
    if not folder_path:
        return []
    
    folder = bpy.path.abspath(folder_path)
    if not os.path.isdir(folder):
        return []
    
    files = []
    for f in sorted(os.listdir(folder)):
        ext = os.path.splitext(f)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            files.append(os.path.join(folder, f))
    
    return files


def load_image(filepath):
    """Load image from filepath, returns Blender image or None."""
    try:
        img = bpy.data.images.load(filepath, check_existing=False)
        # Ensure the image uses float buffer for high bit-depth preservation
        # This is important for 16-bit images used in bit packing
        if not img.is_float:
            # Check if the source file might be high bit-depth
            ext = os.path.splitext(filepath)[1].lower()
            if ext in ('.exr', '.hdr'):
                # These formats require float
                pass  # Blender should handle automatically
            elif ext in ('.png', '.tiff', '.tif'):
                # PNG/TIFF can be 16-bit, reload with float if needed
                # Force reload the pixel data
                img.reload()
        return img
    except:
        return None


def generate_output_path(base_name, suffix, output_folder, file_format):
    """Generate full output file path."""
    ext = FORMAT_EXTENSIONS.get(file_format, '.png')
    filename = base_name + suffix + ext
    
    if output_folder:
        folder = bpy.path.abspath(output_folder)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, filename)
    
    return filename


def save_image(image, filepath, file_format, color_mode='RGBA', color_depth='8', compression=None):
    """
    Save Blender image to file.
    
    Args:
        image: Blender image
        filepath: Output path
        file_format: 'PNG', 'JPEG', 'TARGA', 'TIFF', 'OPEN_EXR', etc.
        color_mode: 'BW', 'RGB', or 'RGBA'
        color_depth: '8', '16', or '32'
        compression: 0-100 for PNG/TIFF, None for default. 0 = no compression.
    """
    scene = bpy.context.scene
    settings = scene.render.image_settings
    
    # Store original settings
    orig_format = settings.file_format
    orig_mode = settings.color_mode
    orig_depth = settings.color_depth
    orig_compression = settings.compression if hasattr(settings, 'compression') else 15
    orig_tiff_codec = settings.tiff_codec if hasattr(settings, 'tiff_codec') else 'DEFLATE'
    orig_exr_codec = settings.exr_codec if hasattr(settings, 'exr_codec') else 'ZIP'
    
    try:
        settings.file_format = file_format
        settings.color_mode = color_mode
        settings.color_depth = color_depth
        
        # Handle compression settings
        if file_format == 'PNG':
            if compression is not None:
                settings.compression = compression
        elif file_format == 'TIFF':
            if compression == 0:
                settings.tiff_codec = 'NONE'
            else:
                settings.tiff_codec = 'DEFLATE'
        elif file_format == 'OPEN_EXR':
            if compression == 0:
                settings.exr_codec = 'NONE'
            else:
                settings.exr_codec = 'ZIP'
        
        image.save_render(filepath, scene=scene)
    finally:
        # Restore original settings
        settings.file_format = orig_format
        settings.color_mode = orig_mode
        settings.color_depth = orig_depth
        if hasattr(settings, 'compression'):
            settings.compression = orig_compression
        if hasattr(settings, 'tiff_codec'):
            settings.tiff_codec = orig_tiff_codec
        if hasattr(settings, 'exr_codec'):
            settings.exr_codec = orig_exr_codec


def get_input_image(props, operator):
    """
    Get input image from props, with error reporting.
    
    Returns:
        (image, result) tuple. If image is None, result is the error return value.
    """
    if not props.input_image:
        operator.report({'ERROR'}, "No input image selected")
        return None, {'CANCELLED'}
    
    image = bpy.data.images.get(props.input_image)
    if not image:
        operator.report({'ERROR'}, f"Image not found: {props.input_image}")
        return None, {'CANCELLED'}
    
    return image, None


# ============================================================================
# Image Processing Helpers
# ============================================================================

def resize_bilinear(image_data, new_height, new_width):
    """
    Resize image using bilinear interpolation.
    
    Args:
        image_data: (H, W) or (H, W, C) numpy array
        new_height, new_width: Target dimensions
    
    Returns:
        Resized array
    """
    old_height, old_width = image_data.shape[:2]
    
    if old_height == new_height and old_width == new_width:
        return image_data
    
    # Create coordinate grids
    y = np.linspace(0, old_height - 1, new_height)
    x = np.linspace(0, old_width - 1, new_width)
    
    y0 = np.floor(y).astype(int)
    y1 = np.minimum(y0 + 1, old_height - 1)
    x0 = np.floor(x).astype(int)
    x1 = np.minimum(x0 + 1, old_width - 1)
    
    wy = y - y0
    wx = x - x0
    
    if image_data.ndim == 2:
        # Grayscale
        result = (
            image_data[y0][:, x0] * (1 - wy)[:, np.newaxis] * (1 - wx) +
            image_data[y1][:, x0] * wy[:, np.newaxis] * (1 - wx) +
            image_data[y0][:, x1] * (1 - wy)[:, np.newaxis] * wx +
            image_data[y1][:, x1] * wy[:, np.newaxis] * wx
        )
    else:
        # Color (H, W, C)
        result = np.zeros((new_height, new_width, image_data.shape[2]), dtype=image_data.dtype)
        for c in range(image_data.shape[2]):
            channel = image_data[:, :, c]
            result[:, :, c] = (
                channel[y0][:, x0] * (1 - wy)[:, np.newaxis] * (1 - wx) +
                channel[y1][:, x0] * wy[:, np.newaxis] * (1 - wx) +
                channel[y0][:, x1] * (1 - wy)[:, np.newaxis] * wx +
                channel[y1][:, x1] * wy[:, np.newaxis] * wx
            )
    
    return result.astype(np.float32)


# ============================================================================
# Aspect Ratio Helper
# ============================================================================

class AspectRatioHelper:
    """
    Helper for maintaining aspect ratio in width/height properties.
    
    Usage:
        _aspect = core.AspectRatioHelper()
        
        class MyProps(PropertyGroup):
            output_width: IntProperty(update=lambda s, c: _aspect.update_width(s))
            output_height: IntProperty(update=lambda s, c: _aspect.update_height(s))
            lock_aspect: BoolProperty(update=lambda s, c: _aspect.update_lock(s))
    """
    def __init__(self):
        self.ratio = 1.0
    
    def update_width(self, props):
        if props.lock_aspect and self.ratio > 0 and props.output_width > 0:
            new_height = int(props.output_width / self.ratio)
            if new_height != props.output_height and new_height > 0:
                props["output_height"] = max(1, new_height)
    
    def update_height(self, props):
        if props.lock_aspect and self.ratio > 0 and props.output_height > 0:
            new_width = int(props.output_height * self.ratio)
            if new_width != props.output_width and new_width > 0:
                props["output_width"] = max(1, new_width)
    
    def update_lock(self, props):
        if props.lock_aspect and props.output_height > 0 and props.output_width > 0:
            self.ratio = props.output_width / props.output_height


# ============================================================================
# Standard Load Image Operator Base
# ============================================================================

class LoadImageOperatorBase(bpy.types.Operator, ImportHelper):
    """
    Base class for image loading operators.
    
    Subclass and override:
        - bl_idname, bl_label
        - get_props(context): Return your module's property group
        - image_property: Name of the StringProperty to set
    """
    bl_options = {'REGISTER', 'UNDO'}
    
    filter_glob: bpy.props.StringProperty(
        default="*.png;*.jpg;*.jpeg;*.tga;*.bmp;*.tiff;*.tif;*.exr;*.hdr",
        options={'HIDDEN'}
    )
    
    image_property = "input_image"
    
    def get_props(self, context):
        raise NotImplementedError("Subclass must implement get_props()")
    
    def execute(self, context):
        try:
            img = bpy.data.images.load(self.filepath, check_existing=True)
            setattr(self.get_props(context), self.image_property, img.name)
            set_image_editor_image(context, img)
            self.report({'INFO'}, f"Loaded: {img.name}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load: {str(e)}")
            return {'CANCELLED'}


# ============================================================================
# Standard Show Image Operator Base
# ============================================================================

class ShowImageOperatorBase(bpy.types.Operator):
    """
    Base class for "show image in editor" operators.
    
    Subclass and override:
        - bl_idname, bl_label
        - get_props(context): Return your module's property group
        - image_property: Name of the StringProperty to read
    """
    bl_options = {'INTERNAL'}
    
    image_property = "input_image"
    
    def get_props(self, context):
        raise NotImplementedError("Subclass must implement get_props()")
    
    def execute(self, context):
        image_name = getattr(self.get_props(context), self.image_property, "")
        if image_name:
            img = bpy.data.images.get(image_name)
            if img:
                set_image_editor_image(context, img)
        return {'FINISHED'}


# ============================================================================
# Batch Overwrite Confirmation Mixin
# ============================================================================

class BatchConfirmMixin:
    """
    Mixin for operators that need confirmation before overwriting files in batch mode.
    
    Shows a confirmation dialog when output folder is empty or same as input folder.
    
    Usage:
        class MyOperator(BatchConfirmMixin, bpy.types.Operator):
            # Override these if your props use different names:
            input_folder_prop = "input_folder"
            output_folder_prop = "output_folder"
            
            def get_props(self, context):
                return context.scene.my_props
    """
    input_folder_prop = "input_folder"
    output_folder_prop = "output_folder"
    
    def get_props(self, context):
        raise NotImplementedError("Subclass must implement get_props()")
    
    def _will_overwrite(self, props):
        """Check if batch operation will overwrite original files."""
        output = getattr(props, self.output_folder_prop, "")
        if not output:
            return True
        input_folder = bpy.path.abspath(getattr(props, self.input_folder_prop, ""))
        output_folder = bpy.path.abspath(output)
        return os.path.normpath(input_folder) == os.path.normpath(output_folder)
    
    def _is_batch_mode(self, props):
        """Check if currently in batch mode."""
        return getattr(props, 'input_mode', 'SINGLE') == 'BATCH'
    
    def invoke(self, context, event):
        props = self.get_props(context)
        if self._is_batch_mode(props) and self._will_overwrite(props):
            return context.window_manager.invoke_props_dialog(self, width=300)
        return self.execute(context)
    
    def draw(self, context):
        """Draw confirmation dialog content."""
        layout = self.layout
        layout.label(text="This will overwrite original files!", icon='ERROR')
        layout.label(text="This cannot be undone.")
        layout.separator()


# ============================================================================
# UI Drawing Helpers
# ============================================================================

def set_image_editor_image(context, image):
    """Set the active image in the image editor."""
    for area in context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            area.spaces.active.image = image
            break


def calculate_output_dimensions(props, input_w, input_h):
    """Calculate output dimensions based on props (0 = same as input)."""
    if props.output_width > 0 and props.output_height > 0:
        return props.output_width, props.output_height
    elif props.output_width > 0:
        return props.output_width, int(input_h * props.output_width / input_w)
    elif props.output_height > 0:
        return int(input_w * props.output_height / input_h), props.output_height
    return input_w, input_h


def draw_output_section(layout, props):
    """
    Draw standardized output section in a panel.
    
    Expected properties: output_name, output_folder, lock_aspect,
                        output_width, output_height, file_format, color_depth
    """
    box = layout.box()
    box.label(text="Output:", icon='FILE_IMAGE')
    box.prop(props, "output_name")
    box.prop(props, "output_folder", text="")
    
    row = box.row(align=True)
    row.prop(props, "lock_aspect", text="", icon='LOCKED' if props.lock_aspect else 'UNLOCKED')
    row.prop(props, "output_width", text="Width")
    row.prop(props, "output_height", text="Height")
    
    row = box.row(align=True)
    row.prop(props, "file_format", text="")
    row.prop(props, "color_depth", text="")


def draw_input_image_row(layout, props, load_op, show_op, prop_name="input_image"):
    """Draw standardized input image row with search, load, and show buttons."""
    row = layout.row(align=True)
    row.prop_search(props, prop_name, bpy.data, "images", text="")
    row.operator(load_op, text="", icon='FILEBROWSER')
    sub = row.row(align=True)
    sub.enabled = bool(getattr(props, prop_name, ""))
    sub.operator(show_op, text="", icon='HIDE_OFF')


def draw_batch_input_section(layout, props, load_op=None, show_op=None,
                              count_func=None, count_label="images"):
    """
    Draw Single/Batch mode input section.
    
    Args:
        layout: Layout to draw in
        props: Property group with input_mode, input_image, input_folder
        load_op: Operator for loading single image
        show_op: Operator for showing single image
        count_func: Function to count files, receives folder path
        count_label: Label for count (e.g., "images", "SVGs")
    """
    row = layout.row()
    row.prop(props, "input_mode", expand=True)
    
    if props.input_mode == 'SINGLE':
        if load_op and show_op:
            draw_input_image_row(layout, props, load_op, show_op)
        else:
            layout.prop_search(props, "input_image", bpy.data, "images", text="")
    else:
        layout.prop(props, "input_folder", text="")
        if count_func:
            count = count_func(props.input_folder)
            layout.label(
                text=f"{count} {count_label} found" if count else f"No {count_label} found",
                icon='INFO' if count else 'ERROR'
            )


# ============================================================================
# Registration
# ============================================================================

def register():
    """Nothing to register - this is a utility module."""
    pass


def unregister():
    """Nothing to unregister - this is a utility module."""
    pass