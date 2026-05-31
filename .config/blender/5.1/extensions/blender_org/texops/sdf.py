"""
SDF Texture Generator Module for TexOps
Generates a Signed Distance Field from a binary/grayscale image
"""

import bpy
import numpy as np
import os

from . import core


# ============================================================================
# Core SDF Functions
# ============================================================================

def compute_sdf_jfa(binary_mask, progress_callback=None):
    """Compute SDF using Jump Flooding Algorithm (JFA)."""
    height, width = binary_mask.shape
    edges = find_edges(binary_mask)
    
    if progress_callback:
        progress_callback(15)
    
    seed_coords = np.full((height, width, 2), -1, dtype=np.int32)
    edge_y, edge_x = np.where(edges)
    seed_coords[edge_y, edge_x, 0] = edge_x
    seed_coords[edge_y, edge_x, 1] = edge_y
    
    if progress_callback:
        progress_callback(20)
    
    max_dim = max(width, height)
    step = max(1, max_dim // 2)
    pass_count = 0
    total_passes = int(np.ceil(np.log2(max_dim))) + 2
    
    while step >= 1:
        seed_coords = jfa_pass(seed_coords, step, width, height)
        pass_count += 1
        if progress_callback:
            progress_callback(20 + int(60 * pass_count / total_passes))
        step //= 2
    
    seed_coords = jfa_pass(seed_coords, 2, width, height)
    seed_coords = jfa_pass(seed_coords, 1, width, height)
    
    if progress_callback:
        progress_callback(85)
    
    y_coords, x_coords = np.mgrid[0:height, 0:width]
    valid_mask = seed_coords[:, :, 0] >= 0
    
    dx = np.where(valid_mask, x_coords - seed_coords[:, :, 0], 0)
    dy = np.where(valid_mask, y_coords - seed_coords[:, :, 1], 0)
    
    distances = np.sqrt(dx.astype(np.float32)**2 + dy.astype(np.float32)**2)
    sdf = np.where(binary_mask, -distances, distances)
    
    max_dist = np.sqrt(width**2 + height**2)
    sdf = np.where(valid_mask, sdf, np.where(binary_mask, -max_dist, max_dist))
    
    return sdf


def find_edges(binary_mask):
    """Find edge pixels."""
    height, width = binary_mask.shape
    edges = np.zeros((height, width), dtype=bool)
    
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            shifted = np.roll(np.roll(binary_mask, dy, axis=0), dx, axis=1)
            edges |= (binary_mask != shifted)
    
    edges[0, :] = edges[-1, :] = edges[:, 0] = edges[:, -1] = True
    edges &= (binary_mask != np.roll(binary_mask, 1, axis=0)) | \
             (binary_mask != np.roll(binary_mask, -1, axis=0)) | \
             (binary_mask != np.roll(binary_mask, 1, axis=1)) | \
             (binary_mask != np.roll(binary_mask, -1, axis=1))
    return edges


def jfa_pass(seed_coords, step, width, height):
    """Single pass of Jump Flooding Algorithm."""
    h, w = seed_coords.shape[:2]
    new_seeds = seed_coords.copy()
    y_coords, x_coords = np.mgrid[0:h, 0:w]
    
    for dy in [-step, 0, step]:
        for dx in [-step, 0, step]:
            if dx == 0 and dy == 0:
                continue
            ny = np.clip(y_coords + dy, 0, h - 1)
            nx = np.clip(x_coords + dx, 0, w - 1)
            neighbor_seeds = seed_coords[ny, nx]
            
            current_valid = new_seeds[:, :, 0] >= 0
            neighbor_valid = neighbor_seeds[:, :, 0] >= 0
            
            curr_dx = x_coords - new_seeds[:, :, 0]
            curr_dy = y_coords - new_seeds[:, :, 1]
            curr_dist_sq = np.where(current_valid, curr_dx**2 + curr_dy**2, np.inf)
            
            neigh_dx = x_coords - neighbor_seeds[:, :, 0]
            neigh_dy = y_coords - neighbor_seeds[:, :, 1]
            neigh_dist_sq = np.where(neighbor_valid, neigh_dx**2 + neigh_dy**2, np.inf)
            
            update_mask = neigh_dist_sq < curr_dist_sq
            new_seeds[update_mask] = neighbor_seeds[update_mask]
    
    return new_seeds


def compute_edge_distance(width, height, bevel, margin=0):
    """Compute distance from image edge for each pixel."""
    y_coords, x_coords = np.mgrid[0:height, 0:width]
    cx, cy = (width - 1) / 2, (height - 1) / 2
    half_w, half_h = max(cx - margin, 1), max(cy - margin, 1)
    max_bevel = min(half_w, half_h)
    bevel_radius = bevel * max_bevel
    
    px, py = np.abs(x_coords - cx), np.abs(y_coords - cy)
    inner_w, inner_h = half_w - bevel_radius, half_h - bevel_radius
    
    if bevel_radius > 0:
        qx, qy = np.maximum(px - inner_w, 0), np.maximum(py - inner_h, 0)
        corner_dist = np.sqrt(qx**2 + qy**2) - bevel_radius
        edge_dist = np.maximum(px - half_w, py - half_h)
        in_corner = (px > inner_w) & (py > inner_h)
        sdf = np.where(in_corner, corner_dist, edge_dist)
    else:
        sdf = np.maximum(px - half_w, py - half_h)
    
    return (-sdf).astype(np.float32)


def smooth_min(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smooth_max(a, b, k):
    return -smooth_min(-a, -b, k) if k > 0 else np.maximum(a, b)


def apply_edge_falloff(output, edge_distance, falloff, invert_edge, blend_mode='MULTIPLY', smoothness=0.0):
    if falloff <= 0:
        return output
    
    edge_factor = np.clip(edge_distance / falloff, 0, 1)
    if invert_edge:
        edge_factor = 1.0 - edge_factor
    
    if blend_mode == 'MULTIPLY':
        result = output * edge_factor
    elif blend_mode == 'SMOOTH_MIN':
        result = smooth_min(output, edge_factor, smoothness / falloff)
    elif blend_mode == 'SMOOTH_MAX':
        result = smooth_max(output, edge_factor, smoothness / falloff)
    else:
        result = output
    
    return np.clip(result, 0, 1)


def image_to_binary_mask(image, threshold=0.5, invert=False, channel='GRAY'):
    """Convert Blender image to binary mask."""
    grayscale, width, height = core.read_pixels_grayscale(image, channel)
    binary = grayscale > threshold
    if invert:
        binary = ~binary
    return binary, width, height


def remap_sdf(sdf, inner_distance, outer_distance):
    """Remap SDF values to 0-1 range."""
    if inner_distance == 0 and outer_distance == 0:
        return np.where(sdf <= 0, 0.0, 1.0).astype(np.float32)
    
    total_distance = inner_distance + outer_distance
    if total_distance == 0:
        return np.full(sdf.shape, 0.5, dtype=np.float32)
    
    mid_point = inner_distance / total_distance
    inside = sdf < 0
    outside = sdf >= 0
    
    output = np.zeros_like(sdf, dtype=np.float32)
    if inner_distance > 0:
        inner_normalized = np.clip(-sdf[inside] / inner_distance, 0, 1)
        output[inside] = mid_point - inner_normalized * mid_point
    else:
        output[inside] = mid_point
    
    if outer_distance > 0:
        outer_normalized = np.clip(sdf[outside] / outer_distance, 0, 1)
        output[outside] = mid_point + outer_normalized * (1.0 - mid_point)
    else:
        output[outside] = mid_point
    
    return output


def generate_sdf_texture(binary_mask, inner_distance, outer_distance,
                         edge_mode='NONE', edge_bevel=0.0, edge_falloff=64.0,
                         edge_margin=0.0, edge_invert=0.0, edge_blend='MULTIPLY',
                         edge_smoothness=16.0, progress_callback=None):
    """Generate complete SDF texture from binary mask."""
    height, width = binary_mask.shape
    sdf = compute_sdf_jfa(binary_mask, progress_callback)
    output = remap_sdf(sdf, inner_distance, outer_distance)
    
    if edge_mode == 'EDGE':
        edge_distance = compute_edge_distance(width, height, edge_bevel, edge_margin)
        output = apply_edge_falloff(output, edge_distance, edge_falloff, 
                                   edge_invert, edge_blend, edge_smoothness)
    return output


def generate_edge_preview(width, height, bevel, falloff, margin, invert):
    """Generate edge preview visualization."""
    edge_distance = compute_edge_distance(width, height, bevel, margin)
    normalized = np.clip(edge_distance / falloff, 0, 1) if falloff > 0 else edge_distance / max(1, edge_distance.max())
    if invert:
        normalized = 1.0 - normalized
    
    preview = np.zeros((height, width, 4), dtype=np.float32)
    preview[:, :, :3] = normalized[:, :, np.newaxis]
    preview[:, :, 3] = 1.0
    
    if falloff > 0:
        falloff_contour = np.abs(edge_distance - falloff) < 1.5
        preview[falloff_contour, :3] = [1.0, 0.5, 0.0]
    edge_contour = np.abs(edge_distance) < 1.5
    preview[edge_contour, :3] = [0.0, 1.0, 0.5]
    return preview


def generate_threshold_preview(image, threshold, invert, channel='GRAY'):
    """Generate thresholded binary mask preview."""
    grayscale, width, height = core.read_pixels_grayscale(image, channel)
    binary = (grayscale > threshold).astype(np.float32)
    if invert:
        binary = 1.0 - binary
    preview = np.zeros((height, width, 4), dtype=np.float32)
    preview[:, :, :3] = binary[:, :, np.newaxis]
    preview[:, :, 3] = 1.0
    return preview, width, height


def process_single_image(input_img, props, progress_callback=None):
    """Process single image to generate SDF."""
    binary_mask, width, height = image_to_binary_mask(
        input_img, props.threshold, props.invert, props.input_channel
    )
    
    sdf_data = generate_sdf_texture(
        binary_mask, props.inner_distance, props.outer_distance,
        props.edge_mode, props.edge_bevel, props.edge_falloff,
        props.edge_margin, props.edge_invert, props.edge_blend,
        props.edge_smoothness, progress_callback
    )
    
    in_h, in_w = sdf_data.shape
    out_w, out_h = core.calculate_output_dimensions(props, in_w, in_h)
    if out_w != in_w or out_h != in_h:
        sdf_data = core.resize_bilinear(sdf_data, out_h, out_w)
    
    output_rgba = np.zeros((out_h, out_w, 4), dtype=np.float32)
    output_rgba[:, :, :3] = sdf_data[:, :, np.newaxis]
    output_rgba[:, :, 3] = 1.0
    return output_rgba


def extract_curve_segments(curves, tolerance=0.01):
    """Extract line segments from curves."""
    segments = []
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    for curve_obj in curves:
        if curve_obj.type != 'CURVE':
            continue
        
        curve_data = curve_obj.data
        matrix = curve_obj.matrix_world
        
        for spline in curve_data.splines:
            if spline.type == 'BEZIER':
                points = spline.bezier_points
                n_points = len(points)
                if n_points < 2:
                    continue
                
                for i in range(n_points):
                    if not spline.use_cyclic_u and i == n_points - 1:
                        break
                    
                    p0, p1 = points[i], points[(i + 1) % n_points]
                    co0 = matrix @ p0.co
                    handle_r0 = matrix @ p0.handle_right
                    handle_l1 = matrix @ p1.handle_left
                    co1 = matrix @ p1.co
                    
                    start = (co0.x, co0.y)
                    ctrl1 = (handle_r0.x, handle_r0.y)
                    ctrl2 = (handle_l1.x, handle_l1.y)
                    end = (co1.x, co1.y)
                    
                    for pt in [start, ctrl1, ctrl2, end]:
                        min_x, min_y = min(min_x, pt[0]), min(min_y, pt[1])
                        max_x, max_y = max(max_x, pt[0]), max(max_y, pt[1])
                    
                    dx, dy = end[0] - start[0], end[1] - start[1]
                    if dx*dx + dy*dy < 1e-18:
                        continue
                    
                    # Check if nearly straight
                    d1 = point_to_line_distance(ctrl1, start, end)
                    d2 = point_to_line_distance(ctrl2, start, end)
                    
                    if d1 < tolerance and d2 < tolerance:
                        segments.append((start, end))
                    else:
                        segments.extend(subdivide_bezier(start, ctrl1, ctrl2, end, tolerance))
            
            elif spline.type == 'POLY':
                points = spline.points
                n_points = len(points)
                if n_points < 2:
                    continue
                
                for i in range(n_points):
                    if not spline.use_cyclic_u and i == n_points - 1:
                        break
                    
                    co0 = matrix @ points[i].co
                    co1 = matrix @ points[(i + 1) % n_points].co
                    start, end = (co0.x, co0.y), (co1.x, co1.y)
                    
                    min_x, min_y = min(min_x, start[0], end[0]), min(min_y, start[1], end[1])
                    max_x, max_y = max(max_x, start[0], end[0]), max(max_y, start[1], end[1])
                    
                    dx, dy = end[0] - start[0], end[1] - start[1]
                    if dx*dx + dy*dy > 1e-18:
                        segments.append((start, end))
    
    if min_x == float('inf'):
        return [], (0, 0, 1, 1)
    
    return segments, (min_x, min_y, max_x, max_y)


def point_to_line_distance(p, a, b):
    """Perpendicular distance from point to line segment."""
    abx, aby = b[0] - a[0], b[1] - a[1]
    ab_len = np.sqrt(abx*abx + aby*aby)
    if ab_len < 1e-12:
        return np.sqrt((p[0]-a[0])**2 + (p[1]-a[1])**2)
    return abs(abx * (a[1] - p[1]) - aby * (a[0] - p[0])) / ab_len


def subdivide_bezier(p0, p1, p2, p3, tolerance=0.01):
    """Subdivide cubic bezier into line segments."""
    d1 = point_to_line_distance(p1, p0, p3)
    d2 = point_to_line_distance(p2, p0, p3)
    
    if d1 < tolerance and d2 < tolerance:
        return [(p0, p3)]
    
    # De Casteljau subdivision
    q0 = ((p0[0]+p1[0])/2, (p0[1]+p1[1])/2)
    q1 = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
    q2 = ((p2[0]+p3[0])/2, (p2[1]+p3[1])/2)
    r0 = ((q0[0]+q1[0])/2, (q0[1]+q1[1])/2)
    r1 = ((q1[0]+q2[0])/2, (q1[1]+q2[1])/2)
    s = ((r0[0]+r1[0])/2, (r0[1]+r1[1])/2)
    
    return subdivide_bezier(p0, q0, r0, s, tolerance) + subdivide_bezier(s, r1, q2, p3, tolerance)


def compute_curve_sdf(segments, bounds, width, height, margin=0):
    """Compute SDF from curve segments."""
    min_x, min_y, max_x, max_y = bounds
    shape_w, shape_h = max_x - min_x, max_y - min_y
    
    if shape_w < 1e-9 or shape_h < 1e-9:
        return np.zeros((height, width), dtype=np.float32)
    
    # Calculate scaling to fit in output with margin
    usable_w, usable_h = width - 2 * margin, height - 2 * margin
    scale = min(usable_w / shape_w, usable_h / shape_h)
    offset_x = margin + (usable_w - shape_w * scale) / 2 - min_x * scale
    offset_y = margin + (usable_h - shape_h * scale) / 2 - min_y * scale
    
    # Create pixel coordinate grids
    px, py = np.meshgrid(np.arange(width, dtype=np.float32),
                         np.arange(height, dtype=np.float32))
    
    # Initialize with large distance
    min_dist = np.full((height, width), 1e10, dtype=np.float32)
    
    # Compute winding number for inside/outside
    crossings = np.zeros((height, width), dtype=np.int32)
    
    for p0, p1 in segments:
        # Transform to pixel space
        x0, y0 = p0[0] * scale + offset_x, p0[1] * scale + offset_y
        x1, y1 = p1[0] * scale + offset_x, p1[1] * scale + offset_y
        
        dx, dy = x1 - x0, y1 - y0
        len_sq = dx*dx + dy*dy
        if len_sq < 1e-20:
            continue
        
        # Compute distance to segment
        apx, apy = px - x0, py - y0
        t = np.clip((apx * dx + apy * dy) / len_sq, 0.0, 1.0)
        diff_x, diff_y = px - (x0 + t * dx), py - (y0 + t * dy)
        dist = np.sqrt(diff_x*diff_x + diff_y*diff_y)
        
        min_dist = np.minimum(min_dist, dist)
        
        # Winding number contribution (ray casting)
        may_cross = ((y0 <= py) & (py < y1)) | ((y1 <= py) & (py < y0))
        if np.any(may_cross):
            with np.errstate(divide='ignore', invalid='ignore'):
                t_cross = np.where(may_cross, (py - y0) / (y1 - y0 + 1e-20), 0)
                x_intersect = x0 + t_cross * (x1 - x0)
            crossings += (may_cross & (x_intersect > px)).astype(np.int32)
    
    # Inside = odd crossings, outside = even
    inside = (crossings % 2) == 1
    sdf = np.where(inside, -min_dist, min_dist)
    
    return sdf


def import_svg_curves(context, svg_path):
    """Import SVG file and return curves."""
    try:
        bpy.ops.import_curve.svg(filepath=svg_path)
    except Exception:
        return []
    curves = [obj for obj in context.selected_objects if obj.type == 'CURVE']
    curves.sort(key=lambda c: c.location.z)
    return curves


def process_curve(curves, props, progress_callback=None):
    """Process curves to generate SDF."""
    if progress_callback:
        progress_callback(5)
    
    tolerance = 0.1 * (10 ** (-3 * props.curve_quality / 100))
    segments, bounds = extract_curve_segments(curves, tolerance)
    
    if not segments:
        return None
    
    if progress_callback:
        progress_callback(15)
    
    # Use output dimensions, default to 512 if not set
    out_w = props.output_width if props.output_width > 0 else 512
    out_h = props.output_height if props.output_height > 0 else 512
    
    # Compute SDF directly from curve segments
    sdf = compute_curve_sdf(segments, bounds, 
                            out_w, out_h, 
                            props.curve_margin)
    
    if props.invert:
        sdf = -sdf
    
    if progress_callback:
        progress_callback(70)
    
    # Remap to 0-1 range
    output = remap_sdf(sdf, props.inner_distance, props.outer_distance)
    
    # Apply edge behavior if enabled
    if props.edge_mode == 'EDGE':
        edge_distance = compute_edge_distance(out_w, out_h, 
                                              props.edge_bevel, props.edge_margin)
        output = apply_edge_falloff(output, edge_distance, props.edge_falloff,
                                   props.edge_invert, props.edge_blend, props.edge_smoothness)
    
    if progress_callback:
        progress_callback(85)
    
    output_rgba = np.zeros((out_h, out_w, 4), dtype=np.float32)
    output_rgba[:, :, :3] = output[:, :, np.newaxis]
    output_rgba[:, :, 3] = 1.0
    return output_rgba


# ============================================================================
# Properties
# ============================================================================

_aspect = core.AspectRatioHelper()
get_depth_items = core.make_depth_items_callback("texops_sdf_props")

SDF_PRESETS = {
    'SIGNED': (64.0, 64.0),
    'UNSIGNED': (128.0, 128.0),
    'INNER': (128.0, 0.0),
    'OUTER': (0.0, 128.0),
}


class SDF_Properties(bpy.types.PropertyGroup):
    input_mode: bpy.props.EnumProperty(
        name="Mode",
        items=[('SINGLE', "Single", ""), ('BATCH', "Batch", "")],
        default='SINGLE'
    )
    input_type: bpy.props.EnumProperty(
        name="Type",
        items=[('IMAGE', "Image", "Use image as input"),
               ('CURVE', "Curve", "Use single curve as input"),
               ('COLLECTION', "Collection", "Use collection of curves as input")],
        default='IMAGE'
    )
    input_image: bpy.props.StringProperty(name="Input Image", default="")
    input_curve: bpy.props.PointerProperty(
        name="Input Curve", type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'CURVE'
    )
    input_collection: bpy.props.PointerProperty(
        name="Input Collection", type=bpy.types.Collection
    )
    input_folder: bpy.props.StringProperty(name="Input Folder", default="//", subtype='DIR_PATH')
    input_channel: bpy.props.EnumProperty(name="Channel", items=core.CHANNEL_ITEMS, default='GRAY')
    
    threshold: bpy.props.FloatProperty(name="Threshold", default=0.5, min=0.0, max=1.0)
    invert: bpy.props.BoolProperty(name="Invert", default=False,
                                   description="Invert the input before generating SDF")
    
    inner_distance: bpy.props.FloatProperty(name="Inner Distance", default=64.0, min=0.0, max=1024.0)
    outer_distance: bpy.props.FloatProperty(name="Outer Distance", default=64.0, min=0.0, max=1024.0)
    
    edge_mode: bpy.props.EnumProperty(
        name="Edge Mode",
        items=[('NONE', "None", ""), ('EDGE', "Image Edge", "")],
        default='NONE'
    )
    edge_margin: bpy.props.FloatProperty(name="Margin", default=0.0, min=0.0, max=256.0)
    edge_bevel: bpy.props.FloatProperty(name="Bevel", default=0.0, min=0.0, max=1.0)
    edge_falloff: bpy.props.FloatProperty(name="Falloff", default=64.0, min=1.0, max=512.0)
    edge_invert: bpy.props.BoolProperty(name="Invert Edge", default=False,
                                        description="Invert the edge falloff")
    edge_blend: bpy.props.EnumProperty(
        name="Blend Mode",
        items=[('MULTIPLY', "Multiply", ""), ('SMOOTH_MIN', "Smooth Min", ""), ('SMOOTH_MAX', "Smooth Max", "")],
        default='MULTIPLY'
    )
    edge_smoothness: bpy.props.FloatProperty(name="Smoothness", default=16.0, min=0.0, max=128.0)
    
    # Curve settings
    curve_margin: bpy.props.IntProperty(
        name="Margin", default=16, min=0, max=128,
        description="Margin around curve"
    )
    curve_quality: bpy.props.FloatProperty(
        name="Quality", default=100.0, min=0.0, max=100.0, subtype='PERCENTAGE',
        description="Subdivision quality for curved segments"
    )
    
    output_name: bpy.props.StringProperty(name="Output Name", default="")
    output_suffix: bpy.props.StringProperty(name="Suffix", default="_SDF",
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

class TEXOPS_OT_SDF_LoadImage(core.LoadImageOperatorBase):
    bl_idname = "texops.sdf_load_image"
    bl_label = "Load Image"
    def get_props(self, context):
        return context.scene.texops_sdf_props


class TEXOPS_OT_SDF_ShowInput(core.ShowImageOperatorBase):
    bl_idname = "texops.sdf_show_input"
    bl_label = "Show"
    def get_props(self, context):
        return context.scene.texops_sdf_props


class TEXOPS_OT_SDF_Generate(core.BatchConfirmMixin, bpy.types.Operator):
    """Generate SDF from image or curve"""
    bl_idname = "texops.sdf_generate"
    bl_label = "Generate SDF"
    bl_options = {'REGISTER', 'UNDO'}
    
    def get_props(self, context):
        return context.scene.texops_sdf_props
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_sdf_props
        if props.input_mode == 'BATCH':
            return self.execute_batch(context, props)
        return self.execute_single(context, props)
    
    def execute_single(self, context, props):
        suffix = props.output_suffix
        
        if props.input_type == 'IMAGE':
            input_img, error = core.get_input_image(props, self)
            if error:
                return error
            
            with core.progress(context.window_manager) as update:
                update(5)
                output_rgba = process_single_image(input_img, props, update)
                update(95)
                
                base_name = props.output_name if props.output_name else input_img.name.rsplit('.', 1)[0]
                output_name = base_name + suffix
                output_img = core.create_image(output_name, output_rgba, 'Non-Color')
                filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                core.save_image(output_img, filepath, props.file_format, 'BW', props.color_depth)
                core.set_image_editor_image(context, output_img)
            
        elif props.input_type == 'CURVE':
            if not props.input_curve:
                self.report({'ERROR'}, "No curve selected")
                return {'CANCELLED'}
            
            curves = [props.input_curve]
            base_name = props.input_curve.name
            
            with core.progress(context.window_manager) as update:
                update(5)
                output_rgba = process_curve(curves, props, update)
                if output_rgba is None:
                    self.report({'ERROR'}, "Could not extract geometry from curve")
                    return {'CANCELLED'}
                update(95)
                
                base_name = props.output_name if props.output_name else base_name
                output_name = base_name + suffix
                output_img = core.create_image(output_name, output_rgba, 'Non-Color')
                filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                core.save_image(output_img, filepath, props.file_format, 'BW', props.color_depth)
                core.set_image_editor_image(context, output_img)
        
        else:  # COLLECTION
            if not props.input_collection:
                self.report({'ERROR'}, "No collection selected")
                return {'CANCELLED'}
            
            curves = [obj for obj in props.input_collection.objects if obj.type == 'CURVE']
            if not curves:
                self.report({'ERROR'}, "Collection has no curves")
                return {'CANCELLED'}
            
            base_name = props.input_collection.name
            
            with core.progress(context.window_manager) as update:
                update(5)
                output_rgba = process_curve(curves, props, update)
                if output_rgba is None:
                    self.report({'ERROR'}, "Could not extract geometry from curves")
                    return {'CANCELLED'}
                update(95)
                
                base_name = props.output_name if props.output_name else base_name
                output_name = base_name + suffix
                output_img = core.create_image(output_name, output_rgba, 'Non-Color')
                filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                core.save_image(output_img, filepath, props.file_format, 'BW', props.color_depth)
                core.set_image_editor_image(context, output_img)
        
        self.report({'INFO'}, f"Saved: {filepath}")
        return {'FINISHED'}
    
    def execute_batch(self, context, props):
        # Get both images and SVGs from folder
        image_files = core.get_images_from_folder(props.input_folder)
        svg_files = core.get_svgs_from_folder(props.input_folder)
        
        if not image_files and not svg_files:
            self.report({'ERROR'}, "No images or SVG files found in folder")
            return {'CANCELLED'}
        
        suffix = props.output_suffix
        success = 0
        total = len(image_files) + len(svg_files)
        
        with core.progress(context.window_manager) as update:
            # Process images
            for i, filepath in enumerate(image_files):
                update(int(100 * i / total))
                input_img = core.load_image(filepath)
                if not input_img:
                    continue
                
                output_rgba = process_single_image(input_img, props)
                base_name = os.path.splitext(os.path.basename(filepath))[0]
                output_name = base_name + suffix
                output_img = core.create_image(output_name, output_rgba, 'Non-Color')
                out_path = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                core.save_image(output_img, out_path, props.file_format, 'BW', props.color_depth)
                success += 1
            
            # Process SVGs
            for i, svg_path in enumerate(svg_files):
                update(int(100 * (len(image_files) + i) / total))
                
                curves = import_svg_curves(context, svg_path)
                if not curves:
                    continue
                
                output_rgba = process_curve(curves, props)
                if output_rgba is not None:
                    base_name = os.path.splitext(os.path.basename(svg_path))[0]
                    output_name = base_name + suffix
                    output_img = core.create_image(output_name, output_rgba, 'Non-Color')
                    out_path = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                    core.save_image(output_img, out_path, props.file_format, 'BW', props.color_depth)
                    success += 1
                
                # Clean up imported curves
                for curve in curves:
                    bpy.data.objects.remove(curve)
        
        self.report({'INFO'}, f"Processed {success}/{total} files")
        return {'FINISHED'}


class TEXOPS_OT_SDF_PreviewThreshold(bpy.types.Operator):
    """Preview threshold"""
    bl_idname = "texops.sdf_preview_threshold"
    bl_label = "Preview"
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_sdf_props
        input_img, error = core.get_input_image(props, self)
        if error:
            return error
        
        preview_data, w, h = generate_threshold_preview(
            input_img, props.threshold, props.invert, props.input_channel
        )
        preview = core.create_image("_SDF_Threshold_Preview", preview_data, 'Non-Color')
        core.set_image_editor_image(context, preview)
        return {'FINISHED'}


class TEXOPS_OT_SDF_PreviewEdge(bpy.types.Operator):
    """Preview edge"""
    bl_idname = "texops.sdf_preview_edge"
    bl_label = "Preview"
    
    def execute(self, context):
        props = context.scene.texops_sdf_props
        if props.input_image:
            input_img = bpy.data.images.get(props.input_image)
            w, h = input_img.size if input_img else (256, 256)
        else:
            w, h = 256, 256
        
        if max(w, h) > 512:
            scale = 512 / max(w, h)
            w, h = int(w * scale), int(h * scale)
        
        preview_data = generate_edge_preview(w, h, props.edge_bevel, props.edge_falloff,
                                             props.edge_margin, props.edge_invert)
        preview = core.create_image("_SDF_Edge_Preview", preview_data, 'Non-Color')
        core.set_image_editor_image(context, preview)
        return {'FINISHED'}


class TEXOPS_OT_SDF_Preset(bpy.types.Operator):
    """Apply SDF preset"""
    bl_idname = "texops.sdf_preset"
    bl_label = "Preset"
    
    preset: bpy.props.StringProperty()
    
    def execute(self, context):
        props = context.scene.texops_sdf_props
        if self.preset in SDF_PRESETS:
            props.inner_distance, props.outer_distance = SDF_PRESETS[self.preset]
        return {'FINISHED'}


# ============================================================================
# UI Panel
# ============================================================================

class TEXOPS_PT_SDF(bpy.types.Panel):
    bl_label = "SDF Generator"
    bl_idname = "TEXOPS_PT_sdf"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'TexOps'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.texops_sdf_props
        
        box = layout.box()
        box.label(text="Input:", icon='IMAGE_DATA')
        row = box.row()
        row.prop(props, "input_mode", expand=True)
        
        if props.input_mode == 'SINGLE':
            row = box.row()
            row.prop(props, "input_type", expand=True)
            
            if props.input_type == 'IMAGE':
                row = box.row(align=True)
                row.prop_search(props, "input_image", bpy.data, "images", text="")
                sub = row.row()
                sub.scale_x = 0.55
                sub.prop(props, "input_channel", text="")
                row.operator("texops.sdf_load_image", text="", icon='FILEBROWSER')
                sub = row.row(align=True)
                sub.enabled = bool(props.input_image)
                sub.operator("texops.sdf_show_input", text="", icon='HIDE_OFF')
                
                box.prop(props, "threshold", slider=True)
                row = box.row()
                row.prop(props, "invert", toggle=True)
                row = box.row()
                row.enabled = bool(props.input_image)
                row.operator("texops.sdf_preview_threshold", icon='HIDE_OFF')
            
            elif props.input_type == 'CURVE':
                box.prop(props, "input_curve", text="")
                
                box.separator()
                box.prop(props, "curve_margin")
                box.prop(props, "curve_quality", slider=True)
                row = box.row()
                row.prop(props, "invert", toggle=True)
            
            else:  # COLLECTION
                box.prop(props, "input_collection", text="")
                if props.input_collection:
                    curve_count = sum(1 for obj in props.input_collection.objects if obj.type == 'CURVE')
                    box.label(text=f"{curve_count} curves", icon='INFO' if curve_count else 'ERROR')
                
                box.separator()
                box.prop(props, "curve_margin")
                box.prop(props, "curve_quality", slider=True)
                row = box.row()
                row.prop(props, "invert", toggle=True)
        else:
            box.prop(props, "input_folder", text="")
            image_count = len(core.get_images_from_folder(props.input_folder))
            svg_count = len(core.get_svgs_from_folder(props.input_folder))
            total = image_count + svg_count
            box.label(text=f"{image_count} images, {svg_count} SVGs" if total else "No files found",
                     icon='INFO' if total else 'ERROR')
            
            box.separator()
            box.label(text="Image Settings:")
            row = box.row(align=True)
            row.label(text="Channel")
            sub = row.row()
            sub.scale_x = 0.55
            sub.prop(props, "input_channel", text="")
            box.prop(props, "threshold", slider=True)
            row = box.row()
            row.prop(props, "invert", toggle=True)
            
            box.separator()
            box.label(text="Curve Settings:")
            box.prop(props, "curve_margin")
            box.prop(props, "curve_quality", slider=True)
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Distance Range (px):", icon='ARROW_LEFTRIGHT')
        row = box.row(align=True)
        row.prop(props, "inner_distance", text="Inner")
        row.prop(props, "outer_distance", text="Outer")
        row = box.row(align=True)
        row.operator("texops.sdf_preset", text="Signed").preset = 'SIGNED'
        row.operator("texops.sdf_preset", text="Unsigned").preset = 'UNSIGNED'
        row = box.row(align=True)
        row.operator("texops.sdf_preset", text="Inner").preset = 'INNER'
        row.operator("texops.sdf_preset", text="Outer").preset = 'OUTER'
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Edge Behavior:", icon='MOD_EDGESPLIT')
        box.prop(props, "edge_mode", text="")
        if props.edge_mode != 'NONE':
            box.prop(props, "edge_margin")
            box.prop(props, "edge_bevel", slider=True)
            box.prop(props, "edge_falloff")
            row = box.row()
            row.prop(props, "edge_invert", toggle=True)
            box.separator()
            box.prop(props, "edge_blend")
            if props.edge_blend in ('SMOOTH_MIN', 'SMOOTH_MAX'):
                box.prop(props, "edge_smoothness")
            box.operator("texops.sdf_preview_edge", icon='HIDE_OFF')
        
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
        row.operator("texops.sdf_generate", icon='EXPORT')


# ============================================================================
# Registration
# ============================================================================

classes = (
    SDF_Properties,
    TEXOPS_OT_SDF_LoadImage,
    TEXOPS_OT_SDF_ShowInput,
    TEXOPS_OT_SDF_Generate,
    TEXOPS_OT_SDF_PreviewThreshold,
    TEXOPS_OT_SDF_PreviewEdge,
    TEXOPS_OT_SDF_Preset,
    TEXOPS_PT_SDF,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_sdf_props = bpy.props.PointerProperty(type=SDF_Properties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.texops_sdf_props