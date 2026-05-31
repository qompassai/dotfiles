"""
RGBA Channel Toggles Module for TexOps
Adds R G B A toggle buttons to the Image Editor tool header
Allows disabling individual channels while viewing others
Shift+click to isolate a channel (displays as grayscale)
"""

import bpy
import numpy as np

from . import core


# ============================================================================
# Properties
# ============================================================================

class RGBA_Properties(bpy.types.PropertyGroup):
    show_r: bpy.props.BoolProperty(name="R", description="Show Red channel", default=True)
    show_g: bpy.props.BoolProperty(name="G", description="Show Green channel", default=True)
    show_b: bpy.props.BoolProperty(name="B", description="Show Blue channel", default=True)
    show_a: bpy.props.BoolProperty(name="A", description="Show Alpha channel", default=True)
    show_transparent: bpy.props.BoolProperty(
        name="Show Transparency",
        description="Display alpha as transparency (checkerboard) or opaque",
        default=True
    )
    isolated_channel: bpy.props.StringProperty(name="Isolated", default="")
    source_image: bpy.props.StringProperty(name="Source Image", default="")
    source_image_hash: bpy.props.IntProperty(name="Source Hash", default=0)


# ============================================================================
# Preview Generation
# ============================================================================

PREVIEW_NAME = "_RGBA_Preview"
CHANNEL_PROPS = {'R': 'show_r', 'G': 'show_g', 'B': 'show_b', 'A': 'show_a'}


def get_image_hash(image):
    """Generate hash to detect image changes. Samples pixels for generated images."""
    if not image:
        return 0
    w, h = image.size
    
    # Generated images need pixel sampling since is_dirty doesn't update reliably
    if image.source == 'GENERATED' or not image.filepath:
        pixel_count = len(image.pixels)
        if pixel_count > 16:
            # Sample first, last, and middle pixels
            mid = (pixel_count // 2) & ~3
            sample = (image.pixels[0], image.pixels[3], image.pixels[mid], image.pixels[-1])
            h = hash((w, h, sample))
            return (h % 2147483647) if h >= 0 else -((-h) % 2147483647)
    
    h = hash((w, h, image.is_dirty))
    return (h % 2147483647) if h >= 0 else -((-h) % 2147483647)


def get_or_create_preview(source_image):
    """Get or create preview image matching source dimensions and colorspace."""
    width, height = source_image.size
    preview = bpy.data.images.get(PREVIEW_NAME)
    
    if preview and (preview.size[0] != width or preview.size[1] != height):
        bpy.data.images.remove(preview)
        preview = None
    
    if not preview:
        preview = bpy.data.images.new(PREVIEW_NAME, width=width, height=height, alpha=True)
    
    preview.colorspace_settings.name = source_image.colorspace_settings.name
    return preview


def generate_preview(source_image, show_r, show_g, show_b, show_a, show_transparent):
    """Generate channel preview using optimized numpy operations."""
    pixels, width, height = core.read_pixels_cached(source_image)
    
    output = np.empty((height, width, 4), dtype=np.float32)
    enabled_rgb = (show_r, show_g, show_b)
    enabled_count = sum(enabled_rgb)
    
    # Single channel isolation - show as grayscale
    if enabled_count == 1 and not show_a:
        ch_idx = enabled_rgb.index(True)
        gray = pixels[:, :, ch_idx]
        output[:, :, 0] = output[:, :, 1] = output[:, :, 2] = gray
        output[:, :, 3] = 1.0
    
    # Alpha only - show as grayscale
    elif enabled_count == 0 and show_a:
        gray = pixels[:, :, 3] if pixels.shape[2] >= 4 else 1.0
        output[:, :, 0] = output[:, :, 1] = output[:, :, 2] = gray
        output[:, :, 3] = 1.0
    
    # Multiple channels - selective display
    else:
        channels = pixels.shape[2]
        output[:, :, 0] = pixels[:, :, 0] if show_r and channels >= 1 else 0.0
        output[:, :, 1] = pixels[:, :, 1] if show_g and channels >= 2 else 0.0
        output[:, :, 2] = pixels[:, :, 2] if show_b and channels >= 3 else 0.0
        output[:, :, 3] = pixels[:, :, 3] if (show_a and show_transparent and channels >= 4) else 1.0
    
    return output.ravel()


def update_preview(context, force_refresh=False):
    """Update the channel preview in the image editor."""
    space = context.space_data
    if not space or space.type != 'IMAGE_EDITOR' or not space.image:
        return
    
    props = context.scene.texops_rgba_props
    image = space.image
    
    # Get source image (not the preview)
    if image.name == PREVIEW_NAME:
        image = bpy.data.images.get(props.source_image)
        if not image:
            return
    else:
        props.source_image = image.name
    
    # Check if image data has changed
    if force_refresh:
        props.source_image_hash = 0
        core._cache.invalidate(image.name)
    else:
        current_hash = get_image_hash(image)
        if current_hash != props.source_image_hash:
            props.source_image_hash = current_hash
            core._cache.invalidate(image.name)
    
    # All channels enabled - show original
    if props.show_r and props.show_g and props.show_b and props.show_a:
        space.display_channels = 'COLOR_ALPHA' if props.show_transparent else 'COLOR'
        if space.image.name == PREVIEW_NAME:
            space.image = image
        return
    
    # Generate and display preview
    preview = get_or_create_preview(image)
    preview.pixels.foreach_set(generate_preview(
        image, props.show_r, props.show_g, props.show_b, props.show_a, props.show_transparent
    ))
    preview.update()
    
    space.display_channels = 'COLOR_ALPHA' if (props.show_transparent and props.show_a) else 'COLOR'
    space.image = preview


# ============================================================================
# Operators
# ============================================================================

class TEXOPS_OT_RGBA_ToggleChannel(bpy.types.Operator):
    """Toggle channel visibility. Shift+click to isolate"""
    bl_idname = "texops.rgba_toggle_channel"
    bl_label = "Toggle Channel"
    bl_options = {'INTERNAL'}
    
    channel: bpy.props.StringProperty()
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space and space.type == 'IMAGE_EDITOR' and space.image
    
    def invoke(self, context, event):
        props = context.scene.texops_rgba_props
        channel = self.channel
        
        if event.shift:
            if props.isolated_channel == channel:
                props.isolated_channel = ""
                props.show_r = props.show_g = props.show_b = props.show_a = True
            else:
                props.isolated_channel = channel
                for ch, prop in CHANNEL_PROPS.items():
                    setattr(props, prop, ch == channel)
        else:
            props.isolated_channel = ""
            setattr(props, CHANNEL_PROPS[channel], not getattr(props, CHANNEL_PROPS[channel]))
        
        update_preview(context, force_refresh=True)
        return {'FINISHED'}


class TEXOPS_OT_RGBA_ToggleTransparency(bpy.types.Operator):
    """Toggle alpha transparency display (checkerboard)"""
    bl_idname = "texops.rgba_toggle_transparency"
    bl_label = "Toggle Transparency Display"
    bl_options = {'INTERNAL'}
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space and space.type == 'IMAGE_EDITOR' and space.image
    
    def execute(self, context):
        props = context.scene.texops_rgba_props
        props.show_transparent = not props.show_transparent
        update_preview(context, force_refresh=True)
        return {'FINISHED'}


class TEXOPS_OT_RGBA_Reset(bpy.types.Operator):
    """Reset to show all channels"""
    bl_idname = "texops.rgba_reset"
    bl_label = "Reset Channels"
    bl_options = {'INTERNAL'}
    
    def execute(self, context):
        props = context.scene.texops_rgba_props
        space = context.space_data
        
        props.show_r = props.show_g = props.show_b = props.show_a = True
        props.isolated_channel = ""
        props.source_image_hash = 0
        
        source = bpy.data.images.get(props.source_image)
        if source and space and space.type == 'IMAGE_EDITOR':
            if space.image and space.image.name == PREVIEW_NAME:
                space.image = source
            space.display_channels = 'COLOR_ALPHA' if props.show_transparent else 'COLOR'
        
        core._cache.invalidate(props.source_image)
        return {'FINISHED'}


class TEXOPS_OT_RGBA_Refresh(bpy.types.Operator):
    """Force refresh the channel preview"""
    bl_idname = "texops.rgba_refresh"
    bl_label = "Refresh Preview"
    bl_options = {'INTERNAL'}
    
    def execute(self, context):
        context.scene.texops_rgba_props.source_image_hash = 0
        update_preview(context, force_refresh=True)
        return {'FINISHED'}


# ============================================================================
# UI Draw Function
# ============================================================================

def draw_rgba_toggles(self, context):
    space = context.space_data
    if not space or not space.image:
        return
    
    props = context.scene.texops_rgba_props
    row = self.layout.row(align=True)
    
    for channel, prop in CHANNEL_PROPS.items():
        enabled = getattr(props, prop)
        sub = row.row(align=True)
        sub.alert = not enabled
        sub.operator("texops.rgba_toggle_channel", text=channel, depress=enabled).channel = channel
    
    row.operator("texops.rgba_toggle_transparency", text="", icon='TEXTURE', depress=props.show_transparent)


# ============================================================================
# Handlers
# ============================================================================

@bpy.app.handlers.persistent
def on_image_change(dummy):
    """Invalidate cache when blend file changes."""
    core._cache.invalidate()


@bpy.app.handlers.persistent
def on_depsgraph_update(scene, depsgraph):
    """Detect when images are updated and refresh preview if needed."""
    if not scene or not hasattr(scene, 'texops_rgba_props'):
        return
    
    props = scene.texops_rgba_props
    if not props.source_image:
        return
    
    context = bpy.context
    if not context.space_data or context.space_data.type != 'IMAGE_EDITOR':
        return
    
    if not context.space_data.image or context.space_data.image.name != PREVIEW_NAME:
        return
    
    for update in depsgraph.updates:
        if isinstance(update.id, bpy.types.Image) and update.id.name == props.source_image:
            core._cache.invalidate(props.source_image)
            props.source_image_hash = 0
            break


# ============================================================================
# Registration
# ============================================================================

classes = (
    RGBA_Properties,
    TEXOPS_OT_RGBA_ToggleChannel,
    TEXOPS_OT_RGBA_ToggleTransparency,
    TEXOPS_OT_RGBA_Reset,
    TEXOPS_OT_RGBA_Refresh,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_rgba_props = bpy.props.PointerProperty(type=RGBA_Properties)
    bpy.types.IMAGE_HT_tool_header.append(draw_rgba_toggles)
    
    if on_image_change not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(on_image_change)
    
    if on_depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)


def unregister():
    if on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update)
    
    if on_image_change in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(on_image_change)
    
    bpy.types.IMAGE_HT_tool_header.remove(draw_rgba_toggles)
    del bpy.types.Scene.texops_rgba_props
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    preview = bpy.data.images.get(PREVIEW_NAME)
    if preview:
        bpy.data.images.remove(preview)