"""
Map Converter Module for TexOps
Convert and derive PBR texture maps from height and normal maps
Supports: Height→Normal, Height→AO, Height→Cavity, Height→Slope,
          Normal→AO, Normal→Curvature, Normal→Cavity, Normal→Height,
          Normal+AO→Bent Normal
"""

import bpy
import numpy as np
import os

from . import core


# ============================================================================
# Conversion Mode Definitions
# ============================================================================

CONVERSION_MODES = [
    ('HEIGHT_TO_NORMAL', "Height → Normal", "Generate normal map from height map"),
    ('HEIGHT_TO_AO', "Height → AO", "Generate ambient occlusion from height map"),
    ('HEIGHT_TO_CAVITY', "Height → Cavity", "Extract fine detail cavity from height map"),
    ('HEIGHT_TO_SLOPE', "Height → Slope", "Generate slope mask (white=steep, black=flat)"),
    ('NORMAL_TO_AO', "Normal → AO", "Approximate ambient occlusion from normal map"),
    ('NORMAL_TO_CURVATURE', "Normal → Curvature", "Extract curvature from normal map"),
    ('NORMAL_TO_CAVITY', "Normal → Cavity", "Extract cavity from normal map"),
    ('NORMAL_TO_HEIGHT', "Normal → Height", "Integrate normal map to height"),
    ('BENT_NORMAL', "Normal + AO → Bent Normal", "Combine normal and AO into bent normal"),
    ('NORMAL_DX_TO_GL', "Normal DX → GL", "Convert DirectX normal to OpenGL (flip Y)"),
    ('NORMAL_GL_TO_DX', "Normal GL → DX", "Convert OpenGL normal to DirectX (flip Y)"),
    ('NORMAL_XY_TO_XYZ', "Normal XY → XYZ", "Derive Z channel from XY normal map"),
]

# Modes that require a height map input
HEIGHT_INPUT_MODES = {'HEIGHT_TO_NORMAL', 'HEIGHT_TO_AO', 'HEIGHT_TO_CAVITY', 'HEIGHT_TO_SLOPE'}

# Modes that require a normal map input
NORMAL_INPUT_MODES = {'NORMAL_TO_AO', 'NORMAL_TO_CURVATURE', 'NORMAL_TO_CAVITY', 'NORMAL_TO_HEIGHT', 
                      'BENT_NORMAL', 'NORMAL_DX_TO_GL', 'NORMAL_GL_TO_DX', 'NORMAL_XY_TO_XYZ'}

# Modes that require AO input (secondary)
AO_INPUT_MODES = {'BENT_NORMAL'}

# Modes that output normal maps (need GL/DX option)
NORMAL_OUTPUT_MODES = {'HEIGHT_TO_NORMAL', 'BENT_NORMAL', 'NORMAL_XY_TO_XYZ'}

# All modes that output RGB normal maps (for color mode selection)
RGB_OUTPUT_MODES = {'HEIGHT_TO_NORMAL', 'BENT_NORMAL', 'NORMAL_XY_TO_XYZ', 
                    'NORMAL_DX_TO_GL', 'NORMAL_GL_TO_DX'}

# Default suffixes per mode
MODE_SUFFIXES = {
    'HEIGHT_TO_NORMAL': "_Normal",
    'HEIGHT_TO_AO': "_AO",
    'HEIGHT_TO_CAVITY': "_Cavity",
    'HEIGHT_TO_SLOPE': "_Slope",
    'NORMAL_TO_AO': "_AO",
    'NORMAL_TO_CURVATURE': "_Curvature",
    'NORMAL_TO_CAVITY': "_Cavity",
    'NORMAL_TO_HEIGHT': "_Height",
    'BENT_NORMAL': "_BentNormal",
    'NORMAL_DX_TO_GL': "_GL",
    'NORMAL_GL_TO_DX': "_DX",
    'NORMAL_XY_TO_XYZ': "_XYZ",
}


def update_suffix_for_mode(self, context):
    """Update suffix when mode changes."""
    suffix = MODE_SUFFIXES.get(self.mode, "")
    # Add GL/DX suffix for normal output modes
    if self.mode in NORMAL_OUTPUT_MODES:
        suffix += "_GL" if self.normal_format == 'GL' else "_DX"
    self.output_suffix = suffix


def update_suffix_for_format(self, context):
    """Update suffix when normal format changes."""
    if self.mode in NORMAL_OUTPUT_MODES:
        base_suffix = MODE_SUFFIXES.get(self.mode, "")
        self.output_suffix = base_suffix + ("_GL" if self.normal_format == 'GL' else "_DX")


# ============================================================================
# Core Conversion Functions
# ============================================================================

def height_to_normal(height, strength=1.0):
    """
    Generate normal map from height map using Sobel operator.
    
    Args:
        height: (H, W) grayscale height data
        strength: Normal map intensity multiplier (unbounded)
    
    Returns:
        (H, W, 4) RGBA normal map (OpenGL convention: Y+ up)
    """
    # Sobel kernels for gradient (Scharr for better rotational symmetry)
    sobel_x = np.array([[-3,  0,  3],
                        [-10, 0, 10],
                        [-3,  0,  3]], dtype=np.float32) / 32.0
    sobel_y = np.array([[-3, -10, -3],
                        [ 0,   0,  0],
                        [ 3,  10,  3]], dtype=np.float32) / 32.0
    
    # Pad for convolution (wrap for tileable textures)
    padded = np.pad(height, 1, mode='wrap')
    
    h, w = height.shape
    dx = np.zeros_like(height)
    dy = np.zeros_like(height)
    
    # Convolve
    for i in range(3):
        for j in range(3):
            dx += sobel_x[i, j] * padded[i:i+h, j:j+w]
            dy += sobel_y[i, j] * padded[i:i+h, j:j+w]
    
    # Apply strength (scale gradients, not final normal)
    dx *= strength
    dy *= strength
    
    # Construct normal vectors: Normal = normalize(-dx, -dy, 1)
    nx = -dx
    ny = -dy
    nz = np.ones_like(height)
    
    # Normalize
    length = np.sqrt(nx*nx + ny*ny + nz*nz)
    nx /= length
    ny /= length
    nz /= length
    
    # Pack to 0-1 range (tangent space normal map convention)
    r = nx * 0.5 + 0.5
    g = ny * 0.5 + 0.5
    b = nz * 0.5 + 0.5
    a = np.ones_like(height)
    
    return np.stack([r, g, b, a], axis=-1).astype(np.float32)


def height_to_ao(height, radius=8, intensity=1.0):
    """
    Generate ambient occlusion from height map.
    Uses horizon-based ambient occlusion approximation with smooth sampling.
    
    Args:
        height: (H, W) grayscale height data
        radius: Sample radius in pixels
        intensity: AO intensity multiplier
    
    Returns:
        (H, W, 4) RGBA with AO in RGB channels
    """
    h, w = height.shape
    ao = np.zeros_like(height)
    
    # More directions for smoother result
    num_dirs = 16
    angles = np.linspace(0, 2 * np.pi, num_dirs, endpoint=False)
    
    # Precompute height scale factor (normalize based on radius)
    height_scale = radius * 0.5
    
    for angle in angles:
        dx = np.cos(angle)
        dy = np.sin(angle)
        
        max_horizon = np.zeros_like(height)
        
        # Sample along ray with sub-pixel interpolation
        num_steps = radius * 2
        for step in range(1, num_steps + 1):
            t = step / num_steps * radius
            
            # Bilinear sample offset
            ox = dx * t
            oy = dy * t
            
            # Integer and fractional parts
            ox_i, ox_f = int(np.floor(ox)), ox % 1.0
            oy_i, oy_f = int(np.floor(oy)), oy % 1.0
            
            # Bilinear interpolation using rolls
            s00 = np.roll(np.roll(height, -oy_i, axis=0), -ox_i, axis=1)
            s10 = np.roll(np.roll(height, -oy_i, axis=0), -ox_i-1, axis=1)
            s01 = np.roll(np.roll(height, -oy_i-1, axis=0), -ox_i, axis=1)
            s11 = np.roll(np.roll(height, -oy_i-1, axis=0), -ox_i-1, axis=1)
            
            sampled = (s00 * (1-ox_f) * (1-oy_f) + 
                      s10 * ox_f * (1-oy_f) +
                      s01 * (1-ox_f) * oy_f +
                      s11 * ox_f * oy_f)
            
            # Calculate horizon angle: atan2(height_diff, distance)
            height_diff = (sampled - height) * height_scale
            horizon = height_diff / (t + 0.001)
            
            max_horizon = np.maximum(max_horizon, horizon)
        
        # Convert horizon to occlusion (higher horizon = more occluded)
        ao += np.clip(max_horizon, 0, 1)
    
    # Normalize
    ao = ao / num_dirs
    
    # Apply intensity and invert (1 = unoccluded, 0 = fully occluded)
    ao = 1.0 - ao * intensity
    ao = np.clip(ao, 0.0, 1.0)
    
    # Light blur to reduce any remaining banding
    ao = _gaussian_blur(ao, sigma=1.0)
    
    return np.stack([ao, ao, ao, np.ones_like(ao)], axis=-1).astype(np.float32)


def _gaussian_blur(data, sigma=1.0):
    """Simple gaussian blur for smoothing."""
    kernel_size = int(sigma * 3) * 2 + 1
    radius = kernel_size // 2
    
    # Create 1D gaussian kernel
    x = np.arange(-radius, radius + 1)
    kernel_1d = np.exp(-x**2 / (2 * sigma**2))
    kernel_1d /= kernel_1d.sum()
    
    # Separable blur (horizontal then vertical)
    padded = np.pad(data, radius, mode='edge')
    h, w = data.shape
    
    # Horizontal pass
    temp = np.zeros_like(data)
    for i, k in enumerate(kernel_1d):
        temp += k * padded[radius:radius+h, i:i+w]
    
    # Vertical pass
    padded = np.pad(temp, radius, mode='edge')
    result = np.zeros_like(data)
    for i, k in enumerate(kernel_1d):
        result += k * padded[i:i+h, radius:radius+w]
    
    return result


def height_to_cavity(height, radius=2, intensity=1.0):
    """
    Extract high-frequency cavity detail from height map.
    Detects small crevices that AO might miss.
    
    Args:
        height: (H, W) grayscale height data
        radius: Blur radius for high-pass filter
        intensity: Cavity intensity multiplier
    
    Returns:
        (H, W, 4) RGBA with cavity in RGB channels
    """
    # Simple box blur for low-frequency
    kernel_size = radius * 2 + 1
    padded = np.pad(height, radius, mode='edge')
    
    h, w = height.shape
    blurred = np.zeros_like(height)
    
    # Box blur
    for i in range(kernel_size):
        for j in range(kernel_size):
            blurred += padded[i:i+h, j:j+w]
    blurred /= (kernel_size * kernel_size)
    
    # High-pass: original - blurred
    cavity = blurred - height
    
    # Remap: negative values = cavities (darker)
    cavity = cavity * intensity + 0.5
    cavity = np.clip(cavity, 0.0, 1.0)
    
    return np.stack([cavity, cavity, cavity, np.ones_like(cavity)], axis=-1).astype(np.float32)


def height_to_slope(height, intensity=1.0):
    """
    Generate slope/gradient mask from height map.
    White = steep areas, Black = flat areas.
    
    Useful for procedural texturing masks:
    - Snow accumulation (flat areas)
    - Moss/lichen growth (flat areas)  
    - Edge wear/erosion (steep areas)
    - Dirt accumulation (flat areas)
    
    Args:
        height: (H, W) grayscale height data
        intensity: Slope intensity multiplier
    
    Returns:
        (H, W, 4) RGBA with slope in RGB channels
    """
    # Use Scharr operator for better quality gradients
    scharr_x = np.array([[-3,  0,  3],
                         [-10, 0, 10],
                         [-3,  0,  3]], dtype=np.float32) / 32.0
    scharr_y = np.array([[-3, -10, -3],
                         [ 0,   0,  0],
                         [ 3,  10,  3]], dtype=np.float32) / 32.0
    
    padded = np.pad(height, 1, mode='wrap')
    
    h, w = height.shape
    dx = np.zeros_like(height)
    dy = np.zeros_like(height)
    
    for i in range(3):
        for j in range(3):
            dx += scharr_x[i, j] * padded[i:i+h, j:j+w]
            dy += scharr_y[i, j] * padded[i:i+h, j:j+w]
    
    # Gradient magnitude
    slope = np.sqrt(dx*dx + dy*dy)
    
    # Apply intensity and normalize
    slope = slope * intensity
    
    # Smooth to reduce banding
    slope = _gaussian_blur(slope, sigma=0.75)
    slope = np.clip(slope, 0.0, 1.0)
    
    return np.stack([slope, slope, slope, np.ones_like(slope)], axis=-1).astype(np.float32)


def normal_to_ao(normal_data, radius=8, intensity=1.0):
    """
    Approximate ambient occlusion from normal map.
    Based on normal direction variance in local neighborhood.
    
    Args:
        normal_data: (H, W, 4) RGBA normal map
        radius: Sample radius
        intensity: AO intensity multiplier
    
    Returns:
        (H, W, 4) RGBA with AO in RGB channels
    """
    # Unpack normals from 0-1 to -1 to 1
    nx = normal_data[:, :, 0] * 2.0 - 1.0
    ny = normal_data[:, :, 1] * 2.0 - 1.0
    nz = normal_data[:, :, 2] * 2.0 - 1.0
    
    h, w = nx.shape
    ao = np.ones((h, w), dtype=np.float32)
    
    # Pad for sampling
    nx_pad = np.pad(nx, radius, mode='edge')
    ny_pad = np.pad(ny, radius, mode='edge')
    nz_pad = np.pad(nz, radius, mode='edge')
    
    # Sample directions
    num_samples = 8
    angles = np.linspace(0, 2 * np.pi, num_samples, endpoint=False)
    
    for angle in angles:
        dx = int(round(np.cos(angle) * radius))
        dy = int(round(np.sin(angle) * radius))
        
        # Sample neighbor normals
        snx = nx_pad[radius+dy:radius+dy+h, radius+dx:radius+dx+w]
        sny = ny_pad[radius+dy:radius+dy+h, radius+dx:radius+dx+w]
        snz = nz_pad[radius+dy:radius+dy+h, radius+dx:radius+dx+w]
        
        # Dot product with center normal (how aligned are they?)
        dot = nx * snx + ny * sny + nz * snz
        
        # Lower dot = more occlusion potential
        ao -= (1.0 - np.clip(dot, 0, 1)) / num_samples
    
    ao = 1.0 - (1.0 - ao) * intensity
    ao = np.clip(ao, 0.0, 1.0)
    
    return np.stack([ao, ao, ao, np.ones_like(ao)], axis=-1).astype(np.float32)


def normal_to_curvature(normal_data, intensity=1.0):
    """
    Extract curvature from normal map.
    Convex areas = bright, Concave areas = dark, Flat = 0.5 gray.
    
    Args:
        normal_data: (H, W, 4) RGBA normal map
        intensity: Curvature intensity multiplier
    
    Returns:
        (H, W, 4) RGBA with curvature in RGB channels
    """
    # Unpack normals
    nx = normal_data[:, :, 0] * 2.0 - 1.0
    ny = normal_data[:, :, 1] * 2.0 - 1.0
    
    # Curvature = divergence of normal field
    # Approximate with finite differences
    dnx_dx = np.gradient(nx, axis=1)
    dny_dy = np.gradient(ny, axis=0)
    
    curvature = (dnx_dx + dny_dy) * 0.5
    
    # Remap to 0-1 (0.5 = flat)
    curvature = curvature * intensity + 0.5
    curvature = np.clip(curvature, 0.0, 1.0)
    
    return np.stack([curvature, curvature, curvature, np.ones_like(curvature)], axis=-1).astype(np.float32)


def normal_to_cavity(normal_data, intensity=1.0):
    """
    Extract cavity from normal map (concave areas only).
    
    Args:
        normal_data: (H, W, 4) RGBA normal map
        intensity: Cavity intensity multiplier
    
    Returns:
        (H, W, 4) RGBA with cavity in RGB channels
    """
    # Get full curvature first
    nx = normal_data[:, :, 0] * 2.0 - 1.0
    ny = normal_data[:, :, 1] * 2.0 - 1.0
    
    dnx_dx = np.gradient(nx, axis=1)
    dny_dy = np.gradient(ny, axis=0)
    
    curvature = dnx_dx + dny_dy
    
    # Keep only concave (negative curvature) as cavity
    cavity = np.maximum(-curvature, 0) * intensity
    cavity = 1.0 - np.clip(cavity, 0.0, 1.0)
    
    return np.stack([cavity, cavity, cavity, np.ones_like(cavity)], axis=-1).astype(np.float32)


def normal_to_height(normal_data, iterations=256):
    """
    Integrate normal map to reconstruct height map.
    Uses Frankot-Chellappa FFT-based integration for robust results.
    
    Args:
        normal_data: (H, W, 4) RGBA normal map
        iterations: Ignored (kept for API compatibility), FFT method is direct
    
    Returns:
        (H, W, 4) RGBA with height in RGB channels
    """
    # Unpack normals from 0-1 to -1 to 1
    nx = normal_data[:, :, 0] * 2.0 - 1.0
    ny = normal_data[:, :, 1] * 2.0 - 1.0
    nz = normal_data[:, :, 2] * 2.0 - 1.0
    
    # Avoid division by zero
    nz = np.maximum(np.abs(nz), 0.001) * np.sign(nz + 0.001)
    
    # Gradient from normal: dz/dx = -nx/nz, dz/dy = -ny/nz
    p = -nx / nz  # dz/dx
    q = -ny / nz  # dz/dy
    
    h, w = nx.shape
    
    # Frankot-Chellappa integration via FFT
    # Create frequency grids
    fy = np.fft.fftfreq(h).reshape(-1, 1)
    fx = np.fft.fftfreq(w).reshape(1, -1)
    
    # FFT of gradients
    P = np.fft.fft2(p)
    Q = np.fft.fft2(q)
    
    # Integrate in frequency domain
    # Z = (-j*fx*P - j*fy*Q) / (fx^2 + fy^2)
    # Avoid division by zero at DC
    denom = (fx**2 + fy**2)
    denom[0, 0] = 1.0  # Prevent div by zero
    
    # Frequency domain integration
    Z = (-1j * fx * P - 1j * fy * Q) / denom
    Z[0, 0] = 0  # Zero mean (DC component)
    
    # Inverse FFT to get height
    height = np.real(np.fft.ifft2(Z))
    
    # Normalize to 0-1 range
    height = height - height.min()
    max_val = height.max()
    if max_val > 1e-6:
        height = height / max_val
    
    height = height.astype(np.float32)
    
    return np.stack([height, height, height, np.ones_like(height)], axis=-1).astype(np.float32)


def create_bent_normal(normal_data, ao_data, intensity=1.0):
    """
    Combine normal map and AO into bent normal.
    Bent normals point toward unoccluded directions.
    
    Args:
        normal_data: (H, W, 4) RGBA normal map
        ao_data: (H, W) or (H, W, 4) ambient occlusion
        intensity: Blend intensity
    
    Returns:
        (H, W, 4) RGBA bent normal map
    """
    # Unpack normal
    nx = normal_data[:, :, 0] * 2.0 - 1.0
    ny = normal_data[:, :, 1] * 2.0 - 1.0
    nz = normal_data[:, :, 2] * 2.0 - 1.0
    
    # Get AO as single channel
    if len(ao_data.shape) == 3:
        ao = ao_data[:, :, 0]
    else:
        ao = ao_data
    
    # Bend normal toward up (0,0,1) based on occlusion
    # More occluded = bend more toward open sky
    bend_factor = (1.0 - ao) * intensity
    
    # Lerp toward up vector
    bent_nx = nx * (1.0 - bend_factor)
    bent_ny = ny * (1.0 - bend_factor)
    bent_nz = nz * (1.0 - bend_factor) + bend_factor
    
    # Renormalize
    length = np.sqrt(bent_nx**2 + bent_ny**2 + bent_nz**2)
    length = np.maximum(length, 0.001)
    bent_nx /= length
    bent_ny /= length
    bent_nz /= length
    
    # Pack back to 0-1
    r = bent_nx * 0.5 + 0.5
    g = bent_ny * 0.5 + 0.5
    b = bent_nz * 0.5 + 0.5
    
    return np.stack([r, g, b, np.ones_like(r)], axis=-1).astype(np.float32)


def normal_flip_y(normal_data):
    """
    Flip Y channel of normal map (converts between DirectX and OpenGL conventions).
    DirectX: Y+ points down (into surface)
    OpenGL: Y+ points up (out of surface)
    
    Args:
        normal_data: (H, W, 4) RGBA normal map
    
    Returns:
        (H, W, 4) RGBA normal map with flipped Y
    """
    result = normal_data.copy()
    # Flip Y: invert around 0.5 (the neutral value)
    result[:, :, 1] = 1.0 - result[:, :, 1]
    return result


def normal_xy_to_xyz(normal_data):
    """
    Derive Z channel from XY normal map.
    Uses the unit normal constraint: x² + y² + z² = 1, so z = sqrt(1 - x² - y²)
    
    Args:
        normal_data: (H, W, 4) RGBA normal map (may have incorrect/missing Z)
    
    Returns:
        (H, W, 4) RGBA normal map with derived Z
    """
    # Unpack X and Y from 0-1 to -1 to 1
    nx = normal_data[:, :, 0] * 2.0 - 1.0
    ny = normal_data[:, :, 1] * 2.0 - 1.0
    
    # Derive Z from unit normal constraint
    # z = sqrt(1 - x² - y²)
    # Clamp the value under sqrt to avoid negative numbers from precision issues
    nz_squared = 1.0 - nx*nx - ny*ny
    nz_squared = np.maximum(nz_squared, 0.0)
    nz = np.sqrt(nz_squared)
    
    # Pack back to 0-1
    r = normal_data[:, :, 0]  # Keep original X
    g = normal_data[:, :, 1]  # Keep original Y
    b = nz * 0.5 + 0.5        # Derived Z
    a = np.ones_like(r)
    
    return np.stack([r, g, b, a], axis=-1).astype(np.float32)


# ============================================================================
# Properties
# ============================================================================

get_depth_items = core.make_depth_items_callback("texops_map_converter")
_aspect = core.AspectRatioHelper()


class MapConverter_Properties(bpy.types.PropertyGroup):
    # Input mode
    input_mode: bpy.props.EnumProperty(
        name="Mode",
        items=[('SINGLE', "Single", "Convert single image"),
               ('BATCH', "Batch", "Convert all images from folder")],
        default='SINGLE'
    )
    input_folder: bpy.props.StringProperty(name="Input Folder", default="//", subtype='DIR_PATH')
    
    # Conversion mode
    mode: bpy.props.EnumProperty(
        name="Mode",
        items=CONVERSION_MODES,
        default='HEIGHT_TO_NORMAL',
        update=update_suffix_for_mode
    )
    
    # Input images
    height_image: bpy.props.StringProperty(name="Height Map", default="")
    height_channel: bpy.props.EnumProperty(name="Channel", items=core.CHANNEL_ITEMS, default='R')
    
    normal_image: bpy.props.StringProperty(name="Normal Map", default="")
    
    ao_image: bpy.props.StringProperty(name="AO Map", default="")
    ao_channel: bpy.props.EnumProperty(name="Channel", items=core.CHANNEL_ITEMS, default='R')
    
    # Conversion parameters
    strength: bpy.props.FloatProperty(
        name="Strength", default=1.0, soft_min=-10.0, soft_max=10.0,
        description="Conversion intensity/strength (negative inverts direction)"
    )
    radius: bpy.props.IntProperty(
        name="Radius", default=64, min=1, soft_max=128,
        description="Sample radius for AO/Cavity calculations"
    )
    iterations: bpy.props.IntProperty(
        name="Iterations", default=256, min=1, soft_min=16, soft_max=1024,
        description="Solver iterations for Normal→Height"
    )
    normal_format: bpy.props.EnumProperty(
        name="Normal Format",
        items=[('GL', "OpenGL", "Y+ up (OpenGL, Blender, Unity)"),
               ('DX', "DirectX", "Y+ down (DirectX, Unreal)")],
        default='GL',
        description="Output normal map format",
        update=update_suffix_for_format
    )
    
    # Output settings
    output_name: bpy.props.StringProperty(name="Output Name", default="Converted")
    output_suffix: bpy.props.StringProperty(name="Suffix", default="_Normal_GL",
                                            description="Suffix added to output filename")
    output_folder: bpy.props.StringProperty(name="Output Folder", default="//", subtype='DIR_PATH')
    output_width: bpy.props.IntProperty(
        name="Width", default=0, min=0, soft_max=16384,
        description="Output width (0 = same as input)",
        update=lambda s, c: _aspect.update_width(s)
    )
    output_height: bpy.props.IntProperty(
        name="Height", default=0, min=0, soft_max=16384,
        description="Output height (0 = same as input)",
        update=lambda s, c: _aspect.update_height(s)
    )
    lock_aspect: bpy.props.BoolProperty(
        name="Lock Aspect", default=True,
        update=lambda s, c: _aspect.update_lock(s)
    )
    file_format: bpy.props.EnumProperty(
        name="Format", items=core.get_format_items,
        update=core.update_depth_for_format
    )
    color_depth: bpy.props.EnumProperty(name="Depth", items=get_depth_items)


# ============================================================================
# Operators
# ============================================================================

class TEXOPS_OT_MapConverter_LoadHeight(core.LoadImageOperatorBase):
    bl_idname = "texops.mapconv_load_height"
    bl_label = "Load Height Map"
    image_property = "height_image"
    
    def get_props(self, context):
        return context.scene.texops_map_converter


class TEXOPS_OT_MapConverter_LoadNormal(core.LoadImageOperatorBase):
    bl_idname = "texops.mapconv_load_normal"
    bl_label = "Load Normal Map"
    image_property = "normal_image"
    
    def get_props(self, context):
        return context.scene.texops_map_converter


class TEXOPS_OT_MapConverter_LoadAO(core.LoadImageOperatorBase):
    bl_idname = "texops.mapconv_load_ao"
    bl_label = "Load AO Map"
    image_property = "ao_image"
    
    def get_props(self, context):
        return context.scene.texops_map_converter


class TEXOPS_OT_MapConverter_Preview(bpy.types.Operator):
    """Preview selected input image"""
    bl_idname = "texops.mapconv_preview"
    bl_label = "Preview"
    bl_options = {'INTERNAL'}
    
    image_prop: bpy.props.StringProperty()
    
    def execute(self, context):
        props = context.scene.texops_map_converter
        image_name = getattr(props, self.image_prop, "")
        if image_name:
            img = bpy.data.images.get(image_name)
            if img:
                core.set_image_editor_image(context, img)
        return {'FINISHED'}


class TEXOPS_OT_MapConverter_Convert(core.BatchConfirmMixin, bpy.types.Operator):
    """Convert/derive texture map"""
    bl_idname = "texops.mapconv_convert"
    bl_label = "Convert"
    bl_options = {'REGISTER'}
    
    def get_props(self, context):
        return context.scene.texops_map_converter
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_map_converter
        if props.input_mode == 'BATCH':
            return self.execute_batch(context, props)
        return self.execute_single(context, props)
    
    def get_primary_input_image(self, props, mode):
        """Get the primary input image name based on mode."""
        if mode in HEIGHT_INPUT_MODES:
            return props.height_image
        elif mode in NORMAL_INPUT_MODES:
            return props.normal_image
        return None
    
    def process_image(self, props, mode, height_data=None, normal_data=None, ao_data=None, width=0, height=0):
        """Process a single image through the selected conversion mode."""
        result = None
        suffix = ""
        colorspace = 'Non-Color'
        
        if mode == 'HEIGHT_TO_NORMAL':
            result = height_to_normal(height_data, props.strength)
            suffix = "_Normal"
        
        elif mode == 'HEIGHT_TO_AO':
            result = height_to_ao(height_data, props.radius, props.strength)
            suffix = "_AO"
        
        elif mode == 'HEIGHT_TO_CAVITY':
            result = height_to_cavity(height_data, props.radius, props.strength)
            suffix = "_Cavity"
        
        elif mode == 'HEIGHT_TO_SLOPE':
            result = height_to_slope(height_data, props.strength)
            suffix = "_Slope"
        
        elif mode == 'NORMAL_TO_AO':
            result = normal_to_ao(normal_data, props.radius, props.strength)
            suffix = "_AO"
        
        elif mode == 'NORMAL_TO_CURVATURE':
            result = normal_to_curvature(normal_data, props.strength)
            suffix = "_Curvature"
        
        elif mode == 'NORMAL_TO_CAVITY':
            result = normal_to_cavity(normal_data, props.strength)
            suffix = "_Cavity"
        
        elif mode == 'NORMAL_TO_HEIGHT':
            result = normal_to_height(normal_data, props.iterations)
            suffix = "_Height"
        
        elif mode == 'BENT_NORMAL':
            result = create_bent_normal(normal_data, ao_data, props.strength)
            suffix = "_BentNormal"
        
        elif mode == 'NORMAL_DX_TO_GL':
            result = normal_flip_y(normal_data)
            suffix = "_GL"
        
        elif mode == 'NORMAL_GL_TO_DX':
            result = normal_flip_y(normal_data)
            suffix = "_DX"
        
        elif mode == 'NORMAL_XY_TO_XYZ':
            result = normal_xy_to_xyz(normal_data)
            suffix = "_XYZ"
        
        # Apply GL/DX conversion for normal-outputting modes
        if result is not None and mode in NORMAL_OUTPUT_MODES:
            if props.normal_format == 'DX':
                result = normal_flip_y(result)
                suffix += "_DX"
            else:
                suffix += "_GL"
        
        return result, suffix, colorspace
    
    def execute_single(self, context, props):
        mode = props.mode
        height_data = None
        normal_data = None
        ao_data = None
        
        # Validate inputs based on mode
        if mode in HEIGHT_INPUT_MODES:
            if not props.height_image:
                self.report({'ERROR'}, "Height map required")
                return {'CANCELLED'}
            height_img = bpy.data.images.get(props.height_image)
            if not height_img:
                self.report({'ERROR'}, "Height map not found")
                return {'CANCELLED'}
            width, height = height_img.size
            height_data = core.extract_channel(height_img, props.height_channel, (height, width), 0.5)
        
        if mode in NORMAL_INPUT_MODES:
            if not props.normal_image:
                self.report({'ERROR'}, "Normal map required")
                return {'CANCELLED'}
            normal_img = bpy.data.images.get(props.normal_image)
            if not normal_img:
                self.report({'ERROR'}, "Normal map not found")
                return {'CANCELLED'}
            width, height = normal_img.size
            normal_data, _, _ = core.read_pixels(normal_img)
        
        if mode in AO_INPUT_MODES:
            if not props.ao_image:
                self.report({'ERROR'}, "AO map required")
                return {'CANCELLED'}
            ao_img = bpy.data.images.get(props.ao_image)
            if not ao_img:
                self.report({'ERROR'}, "AO map not found")
                return {'CANCELLED'}
            ao_data = core.extract_channel(ao_img, props.ao_channel, (height, width), 1.0)
        
        # Execute conversion
        result, _, colorspace = self.process_image(
            props, mode, height_data, normal_data, ao_data, width, height
        )
        
        if result is None:
            self.report({'ERROR'}, f"Unknown mode: {mode}")
            return {'CANCELLED'}
        
        # Resize if needed
        out_h, out_w = result.shape[:2]
        target_w = props.output_width if props.output_width > 0 else out_w
        target_h = props.output_height if props.output_height > 0 else out_h
        
        if (target_w, target_h) != (out_w, out_h):
            result = core.resize_bilinear(result, target_h, target_w)
            out_w, out_h = target_w, target_h
        
        # Create and save output
        primary_name = self.get_primary_input_image(props, mode) or "Output"
        output_name = (props.output_name if props.output_name else primary_name.rsplit('.', 1)[0]) + props.output_suffix
        output_img = core.create_image(output_name, result, colorspace)
        filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
        
        # Normal maps output as RGB, everything else as BW (single channel)
        color_mode = 'RGB' if mode in RGB_OUTPUT_MODES else 'BW'
        core.save_image(output_img, filepath, props.file_format, color_mode, props.color_depth)
        core.set_image_editor_image(context, output_img)
        
        self.report({'INFO'}, f"Created {output_name} ({out_w}x{out_h})")
        return {'FINISHED'}
    
    def execute_batch(self, context, props):
        mode = props.mode
        
        # Bent normal requires secondary input, not supported in batch
        if mode in AO_INPUT_MODES:
            self.report({'ERROR'}, "Bent Normal mode requires manual AO input, use Single mode")
            return {'CANCELLED'}
        
        image_files = core.get_images_from_folder(props.input_folder)
        
        if not image_files:
            self.report({'ERROR'}, "No images found in folder")
            return {'CANCELLED'}
        
        success = 0
        last_output = None
        
        with core.progress(context.window_manager) as update:
            for i, filepath in enumerate(image_files):
                update(int(100 * i / len(image_files)))
                
                # Load image
                try:
                    img = bpy.data.images.load(filepath, check_existing=True)
                except:
                    continue
                
                width, height = img.size
                height_data = None
                normal_data = None
                
                # Extract data based on mode
                if mode in HEIGHT_INPUT_MODES:
                    height_data = core.extract_channel(img, 'R', (height, width), 0.5)
                elif mode in NORMAL_INPUT_MODES:
                    normal_data, _, _ = core.read_pixels(img)
                
                # Process
                result, _, colorspace = self.process_image(
                    props, mode, height_data, normal_data, None, width, height
                )
                
                if result is None:
                    continue
                
                # Resize if needed
                out_h, out_w = result.shape[:2]
                target_w = props.output_width if props.output_width > 0 else out_w
                target_h = props.output_height if props.output_height > 0 else out_h
                
                if (target_w, target_h) != (out_w, out_h):
                    result = core.resize_bilinear(result, target_h, target_w)
                
                # Generate output
                base_name = os.path.splitext(os.path.basename(filepath))[0]
                output_name = base_name + props.output_suffix
                output_img = core.create_image(output_name, result, colorspace)
                out_path = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                
                # Normal maps output as RGB, everything else as BW (single channel)
                color_mode = 'RGB' if mode in RGB_OUTPUT_MODES else 'BW'
                core.save_image(output_img, out_path, props.file_format, color_mode, props.color_depth)
                last_output = output_img
                success += 1
        
        if last_output:
            core.set_image_editor_image(context, last_output)
        
        self.report({'INFO'}, f"Converted {success}/{len(image_files)} images")
        return {'FINISHED'}


# ============================================================================
# UI Panel
# ============================================================================

class TEXOPS_PT_MapConverter(bpy.types.Panel):
    bl_label = "Map Converter"
    bl_idname = "TEXOPS_PT_map_converter"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'TexOps'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.texops_map_converter
        
        # Conversion mode selection
        layout.prop(props, "mode")
        
        layout.separator()
        
        # Input section
        box = layout.box()
        box.label(text="Input:", icon='IMAGE_DATA')
        
        mode = props.mode
        
        # Single/Batch toggle (hide for modes requiring multiple inputs)
        if mode not in AO_INPUT_MODES:
            row = box.row()
            row.prop(props, "input_mode", expand=True)
        
        if props.input_mode == 'SINGLE' or mode in AO_INPUT_MODES:
            # Height input (for height-based modes)
            if mode in HEIGHT_INPUT_MODES:
                row = box.row(align=True)
                row.prop_search(props, "height_image", bpy.data, "images", text="Height")
                row.operator("texops.mapconv_load_height", text="", icon='FILEBROWSER')
                sub = row.row()
                sub.scale_x = 0.55
                sub.prop(props, "height_channel", text="")
                op = row.operator("texops.mapconv_preview", text="", icon='HIDE_OFF')
                op.image_prop = "height_image"
            
            # Normal input (for normal-based modes)
            if mode in NORMAL_INPUT_MODES:
                row = box.row(align=True)
                row.prop_search(props, "normal_image", bpy.data, "images", text="Normal")
                row.operator("texops.mapconv_load_normal", text="", icon='FILEBROWSER')
                op = row.operator("texops.mapconv_preview", text="", icon='HIDE_OFF')
                op.image_prop = "normal_image"
            
            # AO input (for bent normal)
            if mode in AO_INPUT_MODES:
                row = box.row(align=True)
                row.prop_search(props, "ao_image", bpy.data, "images", text="AO")
                row.operator("texops.mapconv_load_ao", text="", icon='FILEBROWSER')
                sub = row.row()
                sub.scale_x = 0.55
                sub.prop(props, "ao_channel", text="")
                op = row.operator("texops.mapconv_preview", text="", icon='HIDE_OFF')
                op.image_prop = "ao_image"
        else:
            # Batch mode
            box.prop(props, "input_folder", text="")
            image_count = len(core.get_images_from_folder(props.input_folder))
            box.label(
                text=f"{image_count} images" if image_count else "No images found",
                icon='INFO' if image_count else 'ERROR'
            )
        
        # Parameters section (only show if mode has parameters)
        # Modes that use strength
        strength_modes = {'HEIGHT_TO_NORMAL', 'HEIGHT_TO_SLOPE', 'NORMAL_TO_CURVATURE', 
                          'NORMAL_TO_CAVITY', 'BENT_NORMAL', 'HEIGHT_TO_AO', 
                          'HEIGHT_TO_CAVITY', 'NORMAL_TO_AO'}
        
        # Modes that use radius
        radius_modes = {'HEIGHT_TO_AO', 'HEIGHT_TO_CAVITY', 'NORMAL_TO_AO'}
        
        has_params = mode in strength_modes or mode in radius_modes or mode in NORMAL_OUTPUT_MODES
        
        if has_params:
            layout.separator()
            box = layout.box()
            box.label(text="Parameters:", icon='PREFERENCES')
            if mode in strength_modes:
                box.prop(props, "strength")
            if mode in radius_modes:
                box.prop(props, "radius")
            if mode in NORMAL_OUTPUT_MODES:
                box.prop(props, "normal_format", text="Output")
        
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
        
        # Convert button
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        row.operator("texops.mapconv_convert", icon='FILE_REFRESH')


# ============================================================================
# Registration
# ============================================================================

classes = (
    MapConverter_Properties,
    TEXOPS_OT_MapConverter_LoadHeight,
    TEXOPS_OT_MapConverter_LoadNormal,
    TEXOPS_OT_MapConverter_LoadAO,
    TEXOPS_OT_MapConverter_Preview,
    TEXOPS_OT_MapConverter_Convert,
    TEXOPS_PT_MapConverter,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_map_converter = bpy.props.PointerProperty(type=MapConverter_Properties)


def unregister():
    del bpy.types.Scene.texops_map_converter
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)