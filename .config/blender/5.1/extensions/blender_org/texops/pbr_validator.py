"""
PBR Validator Module for TexOps
Validate and correct PBR textures to ensure physically accurate ranges
"""

import bpy
import numpy as np
import os

from . import core


# ============================================================================
# PBR Validation Ranges (Linear)
# ============================================================================

# Albedo ranges (Linear 0.0-1.0)
ALBEDO_DIELECTRIC_MIN_STRICT = 0.032   # 50 sRGB
ALBEDO_DIELECTRIC_MIN_TOLERANT = 0.013  # 30 sRGB
ALBEDO_DIELECTRIC_MAX = 0.871          # 240 sRGB
ALBEDO_METAL_MIN = 0.456               # 180 sRGB
ALBEDO_METAL_MAX = 1.0                 # 255 sRGB

# Metallic ranges (should be binary 0 or 1, with exceptions for transitions)
METALLIC_THRESHOLD = 0.1
METALLIC_TRANSITION_THRESHOLD = 0.05

# Roughness ranges (avoid pure extremes)
ROUGHNESS_MIN = 0.02
ROUGHNESS_MAX = 0.98


# ============================================================================
# Utility Functions
# ============================================================================

def smoothstep(edge0, edge1, x):
    """Smooth Hermite interpolation between 0 and 1."""
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def calculate_luminance(rgb):
    """Calculate perceptual luminance from RGB."""
    return 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]


def detect_metallic_transitions(metallic):
    """
    Detect areas with metallic gradients (transitions between materials).
    These are physically valid for coatings, dust, thin films, etc.
    """
    gy, gx = np.gradient(metallic)
    gradient = np.sqrt(gx**2 + gy**2)
    return (gradient > METALLIC_TRANSITION_THRESHOLD).astype(np.float32)


# ============================================================================
# Validation Functions
# ============================================================================

def validate_metallic(metallic, threshold=METALLIC_THRESHOLD, check_transitions=True):
    """Check metallic values - should be 0 or 1 (binary), except in transition areas."""
    invalid = (metallic > threshold) & (metallic < (1.0 - threshold))
    
    if check_transitions:
        transitions = detect_metallic_transitions(metallic)
        invalid = invalid & (transitions < 0.5)
    
    return invalid.astype(np.float32)


def validate_metallic_gradient(metallic, threshold=METALLIC_THRESHOLD, check_transitions=True):
    """Calculate how far metallic values are from valid binary values."""
    # Distance from nearest valid value (0 or 1), normalized so 0.5 maps to 1.0
    gradient = np.minimum(metallic, 1.0 - metallic) * 2.0
    
    # Zero out values within threshold
    gradient = np.where((metallic < threshold) | (metallic > (1.0 - threshold)), 0.0, gradient)
    
    if check_transitions:
        transitions = detect_metallic_transitions(metallic)
        gradient = np.where(transitions > 0.5, 0.0, gradient)
    
    return gradient.astype(np.float32)


def validate_roughness(roughness):
    """Check roughness values - should avoid pure 0 or 1."""
    return ((roughness < ROUGHNESS_MIN) | (roughness > ROUGHNESS_MAX)).astype(np.float32)


def validate_roughness_gradient(roughness):
    """Calculate how far roughness values are from valid range."""
    gradient = np.zeros_like(roughness)
    gradient = np.where(roughness < ROUGHNESS_MIN, 
                       (ROUGHNESS_MIN - roughness) / ROUGHNESS_MIN, gradient)
    gradient = np.where(roughness > ROUGHNESS_MAX,
                       (roughness - ROUGHNESS_MAX) / (1.0 - ROUGHNESS_MAX), gradient)
    return gradient.astype(np.float32)


def validate_albedo(albedo_rgb, metallic, use_strict=True):
    """Check albedo values against metallic-dependent ranges."""
    luminance = calculate_luminance(albedo_rgb)
    dielectric_min = ALBEDO_DIELECTRIC_MIN_STRICT if use_strict else ALBEDO_DIELECTRIC_MIN_TOLERANT
    
    # Interpolate valid range based on metallic
    valid_min = dielectric_min + metallic * (ALBEDO_METAL_MIN - dielectric_min)
    valid_max = ALBEDO_DIELECTRIC_MAX + metallic * (ALBEDO_METAL_MAX - ALBEDO_DIELECTRIC_MAX)
    
    return ((luminance < valid_min) | (luminance > valid_max)).astype(np.float32)


def validate_albedo_gradient(albedo_rgb, metallic, use_strict=True):
    """Calculate how far albedo values are from valid range."""
    luminance = calculate_luminance(albedo_rgb)
    dielectric_min = ALBEDO_DIELECTRIC_MIN_STRICT if use_strict else ALBEDO_DIELECTRIC_MIN_TOLERANT
    
    valid_min = dielectric_min + metallic * (ALBEDO_METAL_MIN - dielectric_min)
    valid_max = ALBEDO_DIELECTRIC_MAX + metallic * (ALBEDO_METAL_MAX - ALBEDO_DIELECTRIC_MAX)
    
    gradient = np.zeros_like(luminance)
    gradient = np.where(luminance < valid_min,
                       (valid_min - luminance) / np.maximum(valid_min, 1e-6), gradient)
    gradient = np.where(luminance > valid_max,
                       (luminance - valid_max) / np.maximum(1.0 - valid_max, 1e-6), gradient)
    return gradient.astype(np.float32)


def create_validation_map(albedo_rgb, packed_rgba, packed_channels,
                          check_albedo=True, check_metallic=True, check_roughness=True,
                          use_strict=True, allow_transitions=True, use_gradient=False):
    """
    Create validation map highlighting invalid areas.
    Returns (H, W, 4) RGBA: Red=Albedo, Green=Metallic, Blue=Roughness issues.
    """
    height, width = albedo_rgb.shape[:2]
    validation = np.zeros((height, width, 4), dtype=np.float32)
    validation[:, :, 3] = 1.0
    
    metallic = packed_rgba[:, :, packed_channels.get('metallic', 0)]
    roughness = packed_rgba[:, :, packed_channels.get('roughness', 1)]
    
    if check_albedo:
        func = validate_albedo_gradient if use_gradient else validate_albedo
        validation[:, :, 0] = func(albedo_rgb, metallic, use_strict)
    
    if check_metallic:
        func = validate_metallic_gradient if use_gradient else validate_metallic
        validation[:, :, 1] = func(metallic, check_transitions=allow_transitions)
    
    if check_roughness:
        func = validate_roughness_gradient if use_gradient else validate_roughness
        validation[:, :, 2] = func(roughness)
    
    return validation


# ============================================================================
# Correction Functions
# ============================================================================

def correct_metallic(metallic, threshold=METALLIC_THRESHOLD, transition=0.05, preserve_transitions=True):
    """Correct metallic to binary 0 or 1 with smooth transition."""
    corrected = np.where(
        metallic < 0.5,
        smoothstep(threshold, threshold - transition, metallic),
        1.0 - smoothstep(1.0 - threshold, 1.0 - threshold + transition, metallic)
    )
    
    if preserve_transitions:
        transitions = detect_metallic_transitions(metallic)
        corrected = np.where(transitions > 0.5, metallic, corrected)
    
    return corrected.astype(np.float32)


def correct_roughness(roughness, margin=0.02):
    """Correct roughness to avoid pure extremes with smooth clamping."""
    corrected = np.clip(roughness, margin, 1.0 - margin)
    transition = margin * 2
    
    # Smooth lower edge
    mask_low = roughness < (margin + transition)
    corrected = np.where(mask_low,
                        margin + smoothstep(0, margin + transition, roughness) * transition,
                        corrected)
    
    # Smooth upper edge
    mask_high = roughness > (1.0 - margin - transition)
    corrected = np.where(mask_high,
                        (1.0 - margin) - smoothstep(1.0 - margin - transition, 1.0, roughness) * transition,
                        corrected)
    
    return corrected.astype(np.float32)


def correct_albedo(albedo_rgb, metallic, use_strict=True, transition=0.05):
    """Correct albedo values to valid ranges with smooth clamping."""
    luminance = calculate_luminance(albedo_rgb)
    dielectric_min = ALBEDO_DIELECTRIC_MIN_STRICT if use_strict else ALBEDO_DIELECTRIC_MIN_TOLERANT
    
    target_min = dielectric_min + metallic * (ALBEDO_METAL_MIN - dielectric_min)
    target_max = ALBEDO_DIELECTRIC_MAX + metallic * (ALBEDO_METAL_MAX - ALBEDO_DIELECTRIC_MAX)
    
    correction = np.ones_like(luminance)
    
    # Too dark
    mask_dark = luminance < target_min
    correction = np.where(mask_dark,
                         target_min / np.maximum(luminance, 1e-6) * 
                         smoothstep(target_min - transition, target_min, luminance),
                         correction)
    
    # Too bright
    mask_bright = luminance > target_max
    correction = np.where(mask_bright,
                         target_max / np.maximum(luminance, 1e-6) *
                         (1.0 - smoothstep(target_max, target_max + transition, luminance - target_max)),
                         correction)
    
    return np.clip(albedo_rgb * correction[:, :, np.newaxis], 0.0, 1.0).astype(np.float32)


# ============================================================================
# Properties
# ============================================================================

get_depth_items = core.make_depth_items_callback("texops_pbr_validator")

CHANNEL_ITEMS = [('R', "R", "Red"), ('G', "G", "Green"), ('B', "B", "Blue"), ('A', "A", "Alpha")]


class PBRValidator_Properties(bpy.types.PropertyGroup):
    # Input
    albedo_image: bpy.props.StringProperty(name="Albedo", default="")
    packed_image: bpy.props.StringProperty(name="Packed", default="")
    
    # Channel mapping
    roughness_channel: bpy.props.EnumProperty(name="Roughness", items=CHANNEL_ITEMS, default='G')
    metallic_channel: bpy.props.EnumProperty(name="Metallic", items=CHANNEL_ITEMS, default='B')
    
    # Validation options
    check_albedo: bpy.props.BoolProperty(name="Albedo", default=True)
    check_metallic: bpy.props.BoolProperty(name="Metallic", default=True)
    check_roughness: bpy.props.BoolProperty(name="Roughness", default=True)
    use_strict_albedo: bpy.props.BoolProperty(
        name="Strict Albedo Range", default=True,
        description="Use strict range (50-240 sRGB) vs tolerant (30-240 sRGB)"
    )
    allow_metallic_transitions: bpy.props.BoolProperty(
        name="Allow Metallic Transitions", default=True,
        description="Allow gray metallic values in gradient areas (coatings, dust, weathering)"
    )
    use_gradient_validation: bpy.props.BoolProperty(
        name="Gradient Validation", default=False,
        description="Show how far off values are instead of binary mask"
    )
    
    # Output
    output_suffix: bpy.props.StringProperty(name="Suffix", default="_Corrected",
                                            description="Suffix added to corrected output filenames")
    output_folder: bpy.props.StringProperty(name="Output Folder", default="//", subtype='DIR_PATH')
    file_format: bpy.props.EnumProperty(name="Format", items=core.get_format_items,
                                         update=core.update_depth_for_format)
    color_depth: bpy.props.EnumProperty(name="Depth", items=get_depth_items)


# ============================================================================
# Operators
# ============================================================================

class TEXOPS_OT_PBRValidator_LoadAlbedo(core.LoadImageOperatorBase):
    bl_idname = "texops.pbr_load_albedo"
    bl_label = "Load Albedo"
    image_property = "albedo_image"
    def get_props(self, context):
        return context.scene.texops_pbr_validator


class TEXOPS_OT_PBRValidator_LoadPacked(core.LoadImageOperatorBase):
    bl_idname = "texops.pbr_load_packed"
    bl_label = "Load Packed"
    image_property = "packed_image"
    def get_props(self, context):
        return context.scene.texops_pbr_validator


class TEXOPS_OT_PBRValidator_Preview(bpy.types.Operator):
    """Preview selected image"""
    bl_idname = "texops.pbr_preview"
    bl_label = "Preview Image"
    bl_options = {'INTERNAL'}
    
    image_type: bpy.props.StringProperty()
    
    def execute(self, context):
        props = context.scene.texops_pbr_validator
        image_name = getattr(props, self.image_type, "")
        if image_name:
            img = bpy.data.images.get(image_name)
            if img:
                core.set_image_editor_image(context, img)
        return {'FINISHED'}


def get_pbr_images(props, operator):
    """Get and validate albedo/packed images. Returns (albedo_rgba, packed_rgba, w, h) or None."""
    if not props.albedo_image or not props.packed_image:
        operator.report({'ERROR'}, "Both albedo and packed images required")
        return None
    
    albedo_img = bpy.data.images.get(props.albedo_image)
    packed_img = bpy.data.images.get(props.packed_image)
    
    if not albedo_img or not packed_img:
        operator.report({'ERROR'}, "Images not found")
        return None
    
    albedo_rgba, aw, ah = core.read_pixels(albedo_img)
    packed_rgba, pw, ph = core.read_pixels(packed_img)
    
    if (aw, ah) != (pw, ph):
        operator.report({'ERROR'}, f"Image size mismatch: {aw}x{ah} vs {pw}x{ph}")
        return None
    
    return albedo_rgba, packed_rgba, aw, ah


def get_channel_map(props):
    """Get channel mapping dict from properties."""
    ch_map = {'R': 0, 'G': 1, 'B': 2, 'A': 3}
    return {
        'metallic': ch_map[props.metallic_channel],
        'roughness': ch_map[props.roughness_channel],
    }


class TEXOPS_OT_PBRValidator_Validate(bpy.types.Operator):
    """Create validation map showing invalid PBR areas"""
    bl_idname = "texops.pbr_validate"
    bl_label = "Validate"
    bl_options = {'REGISTER'}
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_pbr_validator
        
        result = get_pbr_images(props, self)
        if not result:
            return {'CANCELLED'}
        
        albedo_rgba, packed_rgba, w, h = result
        
        validation = create_validation_map(
            albedo_rgba[:, :, :3], packed_rgba, get_channel_map(props),
            props.check_albedo, props.check_metallic, props.check_roughness,
            props.use_strict_albedo, props.allow_metallic_transitions,
            props.use_gradient_validation
        )
        
        output_img = core.create_image("PBR_Validation", validation, 'Non-Color')
        core.set_image_editor_image(context, output_img)
        
        self.report({'INFO'}, "Validation map: Red=Albedo, Green=Metallic, Blue=Roughness")
        return {'FINISHED'}


class TEXOPS_OT_PBRValidator_Correct(bpy.types.Operator):
    """Correct PBR values to valid ranges"""
    bl_idname = "texops.pbr_correct"
    bl_label = "Correct"
    bl_options = {'REGISTER'}
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_pbr_validator
        
        result = get_pbr_images(props, self)
        if not result:
            return {'CANCELLED'}
        
        albedo_rgba, packed_rgba, w, h = result
        channels = get_channel_map(props)
        
        # Extract and correct channels
        metallic = packed_rgba[:, :, channels['metallic']].copy()
        roughness = packed_rgba[:, :, channels['roughness']].copy()
        albedo_rgb = albedo_rgba[:, :, :3].copy()
        
        if props.check_metallic:
            metallic = correct_metallic(metallic, preserve_transitions=props.allow_metallic_transitions)
        if props.check_roughness:
            roughness = correct_roughness(roughness)
        if props.check_albedo:
            albedo_rgb = correct_albedo(albedo_rgb, metallic, props.use_strict_albedo)
        
        # Create corrected images
        corrected_packed = packed_rgba.copy()
        corrected_packed[:, :, channels['metallic']] = metallic
        corrected_packed[:, :, channels['roughness']] = roughness
        
        corrected_albedo = albedo_rgba.copy()
        corrected_albedo[:, :, :3] = albedo_rgb
        
        # Save
        albedo_base = os.path.splitext(os.path.basename(props.albedo_image))[0]
        packed_base = os.path.splitext(os.path.basename(props.packed_image))[0]
        suffix = props.output_suffix
        
        # Check if albedo has meaningful alpha (not all 1.0)
        albedo_alpha = albedo_rgba[:, :, 3]
        albedo_has_alpha = np.ptp(albedo_alpha) > 0.01  # ptp = max - min
        albedo_color_mode = 'RGBA' if albedo_has_alpha else 'RGB'
        
        albedo_out = core.create_image(f"{albedo_base}{suffix}", corrected_albedo, 'sRGB')
        albedo_path = core.generate_output_path(f"{albedo_base}{suffix}", "", props.output_folder, props.file_format)
        core.save_image(albedo_out, albedo_path, props.file_format, albedo_color_mode, props.color_depth)
        
        packed_out = core.create_image(f"{packed_base}{suffix}", corrected_packed, 'Non-Color')
        packed_path = core.generate_output_path(f"{packed_base}{suffix}", "", props.output_folder, props.file_format)
        core.save_image(packed_out, packed_path, props.file_format, 'RGBA', props.color_depth)
        
        core.set_image_editor_image(context, albedo_out)
        self.report({'INFO'}, "Corrected textures saved")
        return {'FINISHED'}


# ============================================================================
# UI Panel
# ============================================================================

class TEXOPS_PT_PBRValidator(bpy.types.Panel):
    bl_label = "PBR Validator"
    bl_idname = "TEXOPS_PT_pbr_validator"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'TexOps'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.texops_pbr_validator
        
        # Input section
        box = layout.box()
        box.label(text="Input:", icon='IMAGE_DATA')
        
        # Albedo row
        row = box.row(align=True)
        sub = row.row()
        sub.scale_x = 0.6
        sub.label(text="Albedo")
        row.prop_search(props, "albedo_image", bpy.data, "images", text="")
        row.operator("texops.pbr_load_albedo", text="", icon='FILEBROWSER')
        sub = row.row(align=True)
        sub.enabled = bool(props.albedo_image)
        sub.operator("texops.pbr_preview", text="", icon='HIDE_OFF').image_type = "albedo_image"
        
        # Packed row
        row = box.row(align=True)
        sub = row.row()
        sub.scale_x = 0.6
        sub.label(text="Packed")
        row.prop_search(props, "packed_image", bpy.data, "images", text="")
        row.operator("texops.pbr_load_packed", text="", icon='FILEBROWSER')
        sub = row.row(align=True)
        sub.enabled = bool(props.packed_image)
        sub.operator("texops.pbr_preview", text="", icon='HIDE_OFF').image_type = "packed_image"
        
        # Channel mapping
        row = box.row(align=True)
        row.label(text="Roughness")
        sub = row.row()
        sub.scale_x = 0.55
        sub.prop(props, "roughness_channel", text="")
        row.separator()
        row.label(text="Metallic")
        sub = row.row()
        sub.scale_x = 0.55
        sub.prop(props, "metallic_channel", text="")
        
        layout.separator()
        
        # Validation section
        box = layout.box()
        box.label(text="Validation:", icon='CHECKMARK')
        
        # Check toggles row
        row = box.row(align=True)
        row.prop(props, "check_albedo", toggle=True)
        row.prop(props, "check_metallic", toggle=True)
        row.prop(props, "check_roughness", toggle=True)
        
        # Options
        col = box.column(align=True)
        row = col.row(align=True)
        sub = row.row(align=True)
        sub.enabled = props.check_albedo
        sub.prop(props, "use_strict_albedo", text="Strict", toggle=True)
        sub = row.row(align=True)
        sub.enabled = props.check_metallic
        sub.prop(props, "allow_metallic_transitions", text="Transitions", toggle=True)
        sub = row.row(align=True)
        sub.prop(props, "use_gradient_validation", text="Gradient", toggle=True)
        
        layout.separator()
        
        # Output section
        box = layout.box()
        box.label(text="Output:", icon='EXPORT')
        box.prop(props, "output_suffix")
        box.prop(props, "output_folder", text="")
        row = box.row(align=True)
        row.prop(props, "file_format", text="")
        row.prop(props, "color_depth", text="")
        
        layout.separator()
        
        # Action buttons
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("texops.pbr_validate", icon='VIEWZOOM')
        row.operator("texops.pbr_correct", icon='CHECKMARK')


# ============================================================================
# Registration
# ============================================================================

classes = (
    PBRValidator_Properties,
    TEXOPS_OT_PBRValidator_LoadAlbedo,
    TEXOPS_OT_PBRValidator_LoadPacked,
    TEXOPS_OT_PBRValidator_Preview,
    TEXOPS_OT_PBRValidator_Validate,
    TEXOPS_OT_PBRValidator_Correct,
    TEXOPS_PT_PBRValidator,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_pbr_validator = bpy.props.PointerProperty(type=PBRValidator_Properties)

def unregister():
    del bpy.types.Scene.texops_pbr_validator
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)