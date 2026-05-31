"""
MSDF Texture Generator Module for TexOps
Generates Multi-channel Signed Distance Fields from Blender Curve objects
Based on Chlumsky's MSDF algorithm (github.com/Chlumsky/msdfgen)

Implements the paper: "Shape Decomposition for Multi-channel Distance Fields"
by Viktor Chlumsky, Czech Technical University in Prague, 2015
"""

import bpy
import numpy as np
import math
import os

from . import core


# ============================================================================
# Edge Color Constants (Section 3.2.2 - Median of Three Model)
# ============================================================================

COLOR_RED = 0b001
COLOR_GREEN = 0b010
COLOR_BLUE = 0b100
COLOR_CYAN = 0b110      # G + B
COLOR_MAGENTA = 0b101   # R + B
COLOR_YELLOW = 0b011    # R + G
COLOR_WHITE = 0b111     # R + G + B


# ============================================================================
# Vector Math Utilities
# ============================================================================

def vec2_dot(a, b):
    return a[0] * b[0] + a[1] * b[1]

def vec2_cross(a, b):
    """2D cross product (returns scalar) - Equation 2.15"""
    return a[0] * b[1] - a[1] * b[0]

def vec2_length(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1])

def vec2_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])

def vec2_add(a, b):
    return (a[0] + b[0], a[1] + b[1])

def vec2_scale(v, s):
    return (v[0] * s, v[1] * s)

def vec2_lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

def vec2_normalize(v):
    l = vec2_length(v)
    return (v[0] / l, v[1] / l) if l > 1e-12 else (0.0, 0.0)


# ============================================================================
# Segment Class - Represents a line segment with distance computations
# ============================================================================

class Segment:
    """
    A line segment from p0 to p1, belonging to an edge with a specific color.
    Implements distance computations from Sections 2.3-2.5 of the paper.
    """
    __slots__ = ['p0', 'p1', 'color', 'direction', 'length']
    
    def __init__(self, p0, p1, color=COLOR_WHITE):
        self.p0 = p0
        self.p1 = p1
        self.color = color
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        self.length = math.sqrt(dx*dx + dy*dy)
        self.direction = (dx / self.length, dy / self.length) if self.length > 1e-12 else (1.0, 0.0)
    
    def signed_distance(self, px, py):
        """
        Compute signed TRUE distance from point to segment (Section 2.3).
        Returns (distance, orthogonality, t) where t is parameter on segment.
        """
        p0x, p0y = self.p0
        p1x, p1y = self.p1
        
        dx = p1x - p0x
        dy = p1y - p0y
        
        # Vector from p0 to query point
        apx = px - p0x
        apy = py - p0y
        
        # Parameter t on segment (Equation 2.28)
        len_sq = dx*dx + dy*dy
        if len_sq < 1e-20:
            # Degenerate segment
            dist = math.sqrt(apx*apx + apy*apy)
            return (dist, 0.0, 0.0)
        
        t = (apx * dx + apy * dy) / len_sq
        t_clamped = max(0.0, min(1.0, t))
        
        # Closest point on segment
        closest_x = p0x + t_clamped * dx
        closest_y = p0y + t_clamped * dy
        
        # Distance to closest point
        diff_x = px - closest_x
        diff_y = py - closest_y
        dist = math.sqrt(diff_x*diff_x + diff_y*diff_y)
        
        # Sign from cross product (which side of line)
        cross = dx * apy - dy * apx
        sign = 1.0 if cross >= 0 else -1.0
        
        # Orthogonality (Section 2.4, Equation 2.43)
        # How perpendicular is the direction from closest point to query point
        if dist > 1e-12:
            ortho = abs(cross) / (self.length * dist)
        else:
            ortho = 0.0
        
        return (sign * dist, ortho, t_clamped)
    
    def pseudo_distance(self, px, py):
        """
        Compute signed PSEUDO-distance from point to infinite line (Section 2.5).
        This is the perpendicular distance, ignoring segment endpoints.
        """
        p0x, p0y = self.p0
        dx = self.p1[0] - p0x
        dy = self.p1[1] - p0y
        
        # Vector from p0 to query point
        apx = px - p0x
        apy = py - p0y
        
        # Signed perpendicular distance = cross product / length
        cross = dx * apy - dy * apx
        return cross / self.length if self.length > 1e-12 else 0.0


# ============================================================================
# Bezier Curve Subdivision (Section 2.1, 2.3.2)
# ============================================================================

def point_line_distance(p, a, b):
    """Perpendicular distance from point to line through a and b."""
    ab = vec2_sub(b, a)
    ab_len = vec2_length(ab)
    if ab_len < 1e-12:
        return vec2_length(vec2_sub(p, a))
    return abs(vec2_cross(ab, vec2_sub(p, a))) / ab_len


def subdivide_cubic(p0, p1, p2, p3, tolerance=0.1):
    """
    Recursively subdivide cubic Bezier into line segments (Section 2.3.2).
    Uses de Casteljau algorithm.
    """
    # Check if curve is flat enough
    d1 = point_line_distance(p1, p0, p3)
    d2 = point_line_distance(p2, p0, p3)
    
    if d1 < tolerance and d2 < tolerance:
        return [(p0, p3)]
    
    # de Casteljau subdivision at t=0.5
    q0 = vec2_lerp(p0, p1, 0.5)
    q1 = vec2_lerp(p1, p2, 0.5)
    q2 = vec2_lerp(p2, p3, 0.5)
    r0 = vec2_lerp(q0, q1, 0.5)
    r1 = vec2_lerp(q1, q2, 0.5)
    s = vec2_lerp(r0, r1, 0.5)
    
    # Recurse on both halves
    left = subdivide_cubic(p0, q0, r0, s, tolerance)
    right = subdivide_cubic(s, r1, q2, p3, tolerance)
    
    return left + right


# ============================================================================
# Edge Coloring (Section 4.4.1, Algorithm 6)
# ============================================================================

def edge_coloring_simple(contours, angle_threshold_deg=3.0):
    """
    Assign colors to edges following Algorithm 6 from the paper.
    
    Rules (Section 4.4.1):
    - Every edge must have at least two channels on (yellow, magenta, cyan, or white)
    - Adjacent edges at corners must share EXACTLY one channel
    
    Algorithm 6:
    - Single edge contour: use WHITE
    - Otherwise: start with MAGENTA, then alternate YELLOW ↔ CYAN
    """
    for contour in contours:
        edges = contour['edges']
        n_edges = len(edges)
        
        if n_edges == 0:
            continue
        
        if n_edges == 1:
            # Single edge (smooth closed curve) - use white
            edges[0]['color'] = COLOR_WHITE
            continue
        
        # Algorithm 6: Start with magenta, alternate yellow/cyan
        current = COLOR_MAGENTA
        for i, edge in enumerate(edges):
            edge['color'] = current
            # Determine next color
            if current == COLOR_YELLOW:
                current = COLOR_CYAN
            else:
                current = COLOR_YELLOW


# ============================================================================
# Shape Extraction from Blender Curves (Section 4.1)
# ============================================================================

def extract_shape_from_curve(curve_obj, subdivision_tolerance=0.01):
    """
    Extract contours with edges from a Blender curve object.
    
    Structure (Figure 4.2):
    - Shape contains Contours
    - Contour contains Edges (separated at corners)
    - Edge contains Segments (line segments from Bezier subdivision)
    """
    if curve_obj.type != 'CURVE':
        return [], (0, 0, 1, 1)
    
    curve_data = curve_obj.data
    matrix = curve_obj.matrix_world
    contours = []
    
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    for spline in curve_data.splines:
        contour = {'edges': []}
        
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
                
                # Update bounds
                for pt in [start, ctrl1, ctrl2, end]:
                    min_x, min_y = min(min_x, pt[0]), min(min_y, pt[1])
                    max_x, max_y = max(max_x, pt[0]), max(max_y, pt[1])
                
                if vec2_length(vec2_sub(end, start)) < 1e-9:
                    continue
                
                # Subdivide cubic Bezier into line segments
                d1 = point_line_distance(ctrl1, start, end)
                d2 = point_line_distance(ctrl2, start, end)
                
                if d1 < subdivision_tolerance and d2 < subdivision_tolerance:
                    line_segs = [(start, end)]
                else:
                    line_segs = subdivide_cubic(start, ctrl1, ctrl2, end, subdivision_tolerance)
                
                if line_segs:
                    first_seg = line_segs[0]
                    last_seg = line_segs[-1]
                    contour['edges'].append({
                        'segments': line_segs,
                        'start_dir': vec2_normalize(vec2_sub(first_seg[1], first_seg[0])),
                        'end_dir': vec2_normalize(vec2_sub(last_seg[1], last_seg[0])),
                        'color': COLOR_WHITE
                    })
        
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
                
                if vec2_length(vec2_sub(end, start)) > 1e-9:
                    direction = vec2_normalize(vec2_sub(end, start))
                    contour['edges'].append({
                        'segments': [(start, end)],
                        'start_dir': direction,
                        'end_dir': direction,
                        'color': COLOR_WHITE
                    })
        
        if contour['edges']:
            contours.append(contour)
    
    if min_x == float('inf'):
        return [], (0, 0, 1, 1)
    
    return contours, (min_x, min_y, max_x, max_y)


def extract_shape_from_curves(curves, subdivision_tolerance=0.01):
    """Extract combined shape from multiple curve objects."""
    all_contours = []
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    for curve_obj in curves:
        contours, bounds = extract_shape_from_curve(curve_obj, subdivision_tolerance)
        if contours:
            all_contours.extend(contours)
            min_x = min(min_x, bounds[0])
            min_y = min(min_y, bounds[1])
            max_x = max(max_x, bounds[2])
            max_y = max(max_y, bounds[3])
    
    if min_x == float('inf'):
        return [], (0, 0, 1, 1)
    
    return all_contours, (min_x, min_y, max_x, max_y)


def import_svg_curves(context, svg_path):
    """Import SVG file and return curve objects."""
    try:
        bpy.ops.import_curve.svg(filepath=svg_path)
    except Exception:
        return []
    curves = [obj for obj in context.selected_objects if obj.type == 'CURVE']
    curves.sort(key=lambda c: c.location.z)
    return curves


# ============================================================================
# Build Segment List with Colors
# ============================================================================

def build_segments(contours):
    """Build list of Segment objects with colors from edges."""
    segments = []
    for contour in contours:
        for edge in contour['edges']:
            color = edge['color']
            for p0, p1 in edge['segments']:
                segments.append(Segment(p0, p1, color))
    return segments


# ============================================================================
# Winding Number Computation (inside/outside test)
# ============================================================================

def compute_winding_number_scalar(contours, px, py):
    """Compute winding number for a single point (Section 2.4)."""
    crossings = 0
    
    for contour in contours:
        for edge in contour['edges']:
            for p0, p1 in edge['segments']:
                y0, y1 = p0[1], p1[1]
                x0, x1 = p0[0], p1[0]
                
                # Check if horizontal ray from (px, py) crosses this segment
                if (y0 <= py < y1) or (y1 <= py < y0):
                    # Compute x-intersection
                    t = (py - y0) / (y1 - y0 + 1e-20)
                    x_intersect = x0 + t * (x1 - x0)
                    if x_intersect > px:
                        crossings += 1
    
    return (crossings % 2) == 1  # Odd = inside


def compute_winding_number_batch(contours, points_x, points_y):
    """Compute winding number for arrays of points."""
    crossings = np.zeros(points_x.shape, dtype=np.int32)
    
    for contour in contours:
        for edge in contour['edges']:
            for p0, p1 in edge['segments']:
                y0, y1 = p0[1], p1[1]
                x0, x1 = p0[0], p1[0]
                
                may_cross = ((y0 <= points_y) & (points_y < y1)) | ((y1 <= points_y) & (points_y < y0))
                if not np.any(may_cross):
                    continue
                
                with np.errstate(divide='ignore', invalid='ignore'):
                    t = np.where(may_cross, (points_y - y0) / (y1 - y0 + 1e-20), 0)
                    x_intersect = x0 + t * (x1 - x0)
                
                crossings += (may_cross & (x_intersect > points_x)).astype(np.int32)
    
    return (crossings % 2) == 1


# ============================================================================
# MSDF Distance Computation (Algorithm 7 from the paper)
# ============================================================================

def find_closest_segment(segments, px, py, channel_mask):
    """
    Find the closest segment for a specific channel (Algorithm 7, lines 4-11).
    
    Uses TRUE distance to find closest, with orthogonality as tiebreaker (Section 2.4).
    Returns the closest Segment object, or None if no segments match the channel.
    """
    closest_seg = None
    closest_dist = float('inf')
    closest_ortho = -1.0
    
    for seg in segments:
        # Only consider segments with this channel (Algorithm 7, lines 6-11)
        if not (seg.color & channel_mask):
            continue
        
        dist, ortho, t = seg.signed_distance(px, py)
        abs_dist = abs(dist)
        
        # Compare using distance, with orthogonality as tiebreaker (Section 2.4)
        if abs_dist < closest_dist - 1e-9:
            closest_dist = abs_dist
            closest_ortho = ortho
            closest_seg = seg
        elif abs(abs_dist - closest_dist) < 1e-9 and ortho > closest_ortho:
            # Equal distance - use orthogonality tiebreaker
            closest_ortho = ortho
            closest_seg = seg
    
    return closest_seg


def compute_msdf_pixel(segments, contours, px, py):
    """
    Compute MSDF values for a single pixel (Algorithm 7 from the paper).
    
    Key insight: Use TRUE distance to find closest edge per channel,
    then output PSEUDO-distance from that edge.
    """
    # Find closest segment for each channel
    r_seg = find_closest_segment(segments, px, py, COLOR_RED)
    g_seg = find_closest_segment(segments, px, py, COLOR_GREEN)
    b_seg = find_closest_segment(segments, px, py, COLOR_BLUE)
    
    # Compute pseudo-distance from closest segments (Algorithm 7, lines 12-14)
    r_dist = r_seg.pseudo_distance(px, py) if r_seg else 1e10
    g_dist = g_seg.pseudo_distance(px, py) if g_seg else 1e10
    b_dist = b_seg.pseudo_distance(px, py) if b_seg else 1e10
    
    # Determine inside/outside using winding number
    inside = compute_winding_number_scalar(contours, px, py)
    
    # Apply sign: positive inside, negative outside
    if inside:
        r_dist = abs(r_dist)
        g_dist = abs(g_dist)
        b_dist = abs(b_dist)
    else:
        r_dist = -abs(r_dist)
        g_dist = -abs(g_dist)
        b_dist = -abs(b_dist)
    
    return r_dist, g_dist, b_dist


# ============================================================================
# Vectorized MSDF Computation (optimized batch version of Algorithm 7)
# ============================================================================

def compute_msdf_batch(segments, contours, points_x, points_y):
    """
    Vectorized implementation of Algorithm 7 for efficiency.
    """
    height, width = points_x.shape
    
    # Initialize distance arrays
    r_dist = np.full((height, width), 1e10, dtype=np.float32)
    g_dist = np.full((height, width), 1e10, dtype=np.float32)
    b_dist = np.full((height, width), 1e10, dtype=np.float32)
    
    # Track closest segment info for each channel
    r_closest_dist = np.full((height, width), 1e10, dtype=np.float32)
    g_closest_dist = np.full((height, width), 1e10, dtype=np.float32)
    b_closest_dist = np.full((height, width), 1e10, dtype=np.float32)
    
    r_ortho = np.full((height, width), -1.0, dtype=np.float32)
    g_ortho = np.full((height, width), -1.0, dtype=np.float32)
    b_ortho = np.full((height, width), -1.0, dtype=np.float32)
    
    for seg in segments:
        p0x, p0y = seg.p0
        p1x, p1y = seg.p1
        dx = p1x - p0x
        dy = p1y - p0y
        len_sq = dx*dx + dy*dy
        
        if len_sq < 1e-20:
            continue
        
        seg_len = math.sqrt(len_sq)
        
        # Vectors from p0 to query points
        apx = points_x - p0x
        apy = points_y - p0y
        
        # Parameter t on segment (clamped for TRUE distance)
        t = np.clip((apx * dx + apy * dy) / len_sq, 0.0, 1.0)
        
        # Closest point on segment
        closest_x = p0x + t * dx
        closest_y = p0y + t * dy
        
        # TRUE distance (to segment)
        diff_x = points_x - closest_x
        diff_y = points_y - closest_y
        true_dist = np.sqrt(diff_x*diff_x + diff_y*diff_y)
        
        # Cross product for sign and orthogonality
        cross = dx * apy - dy * apx
        
        # Orthogonality (Section 2.4)
        with np.errstate(divide='ignore', invalid='ignore'):
            ortho = np.where(true_dist > 1e-12, np.abs(cross) / (seg_len * true_dist), 0.0)
        
        # PSEUDO-distance (perpendicular to infinite line)
        pseudo_dist = cross / seg_len
        
        # Update each channel if this segment is closer
        # Using distance as primary, orthogonality as tiebreaker
        
        if seg.color & COLOR_RED:
            better = (true_dist < r_closest_dist - 1e-9) | \
                    ((np.abs(true_dist - r_closest_dist) < 1e-9) & (ortho > r_ortho))
            r_closest_dist = np.where(better, true_dist, r_closest_dist)
            r_ortho = np.where(better, ortho, r_ortho)
            r_dist = np.where(better, pseudo_dist, r_dist)
        
        if seg.color & COLOR_GREEN:
            better = (true_dist < g_closest_dist - 1e-9) | \
                    ((np.abs(true_dist - g_closest_dist) < 1e-9) & (ortho > g_ortho))
            g_closest_dist = np.where(better, true_dist, g_closest_dist)
            g_ortho = np.where(better, ortho, g_ortho)
            g_dist = np.where(better, pseudo_dist, g_dist)
        
        if seg.color & COLOR_BLUE:
            better = (true_dist < b_closest_dist - 1e-9) | \
                    ((np.abs(true_dist - b_closest_dist) < 1e-9) & (ortho > b_ortho))
            b_closest_dist = np.where(better, true_dist, b_closest_dist)
            b_ortho = np.where(better, ortho, b_ortho)
            b_dist = np.where(better, pseudo_dist, b_dist)
    
    # Apply sign based on winding number
    inside = compute_winding_number_batch(contours, points_x, points_y)
    
    r_dist = np.where(inside, np.abs(r_dist), -np.abs(r_dist))
    g_dist = np.where(inside, np.abs(g_dist), -np.abs(g_dist))
    b_dist = np.where(inside, np.abs(b_dist), -np.abs(b_dist))
    
    return r_dist, g_dist, b_dist


# ============================================================================
# Collision Correction (Section 4.4.3)
# ============================================================================

def detect_and_correct_collisions(r_dist, g_dist, b_dist, threshold):
    """
    Detect and correct false edge collisions (Section 4.4.3).
    
    When 2+ channels have false edges at the same location, the median
    is always correct, so we use it to replace all channels there.
    
    This is a SAFETY NET for rare edge cases, not the primary mechanism.
    """
    height, width = r_dist.shape
    
    # Median is always the correct pseudo-distance (Section 4.4.2)
    median = np.median(np.stack([r_dist, g_dist, b_dist]), axis=0)
    
    # Detect false edges by large gradient jumps between adjacent pixels
    def detect_false_edges(dist):
        padded = np.pad(dist, 1, mode='edge')
        # Check all 4 neighbors
        jump_r = np.abs(padded[1:-1, 2:] - dist) > threshold
        jump_l = np.abs(padded[1:-1, :-2] - dist) > threshold
        jump_d = np.abs(padded[2:, 1:-1] - dist) > threshold
        jump_u = np.abs(padded[:-2, 1:-1] - dist) > threshold
        return jump_r | jump_l | jump_d | jump_u
    
    r_false = detect_false_edges(r_dist)
    g_false = detect_false_edges(g_dist)
    b_false = detect_false_edges(b_dist)
    
    # Collision: 2+ channels have false edges at same pixel
    false_count = r_false.astype(int) + g_false.astype(int) + b_false.astype(int)
    collision = false_count >= 2
    
    # Replace with median at collision points
    r_dist = np.where(collision, median, r_dist)
    g_dist = np.where(collision, median, g_dist)
    b_dist = np.where(collision, median, b_dist)
    
    return r_dist, g_dist, b_dist


# ============================================================================
# Main MSDF Generation Function
# ============================================================================

def generate_msdf(contours, bounds, width, height, range_px, margin=0, invert=False, progress_callback=None):
    """
    Generate multi-channel signed distance field (complete implementation of Section 4.4).
    
    Args:
        contours: Shape contours with edges
        bounds: (min_x, min_y, max_x, max_y) bounding box
        width, height: Output dimensions in pixels
        range_px: Distance range in pixels (controls gradient width)
        margin: Pixel margin around shape
        invert: Swap inside/outside
        progress_callback: Optional progress update function
    
    Returns:
        Tuple of (r_channel, g_channel, b_channel) as float32 arrays [0-1]
    """
    min_x, min_y, max_x, max_y = bounds
    shape_width = max_x - min_x
    shape_height = max_y - min_y
    
    if shape_width < 1e-9 or shape_height < 1e-9:
        return tuple(np.full((height, width), 0.5, dtype=np.float32) for _ in range(3))
    
    # Compute transformation from pixel space to shape space
    usable_width = width - 2 * margin
    usable_height = height - 2 * margin
    scale = min(usable_width / shape_width, usable_height / shape_height)
    offset_x = margin + (usable_width - shape_width * scale) / 2 - min_x * scale
    offset_y = margin + (usable_height - shape_height * scale) / 2 - min_y * scale
    
    if progress_callback:
        progress_callback(10)
    
    # Step 1: Edge coloring (Section 4.4.1, Algorithm 6)
    edge_coloring_simple(contours)
    
    if progress_callback:
        progress_callback(15)
    
    # Build segment list with colors
    segments = build_segments(contours)
    if not segments:
        return tuple(np.full((height, width), 0.5, dtype=np.float32) for _ in range(3))
    
    if progress_callback:
        progress_callback(20)
    
    # Create coordinate grids (in shape space)
    px_grid, py_grid = np.meshgrid(
        np.arange(width, dtype=np.float32),
        np.arange(height, dtype=np.float32)
    )
    shape_x = (px_grid - offset_x) / scale
    shape_y = (py_grid - offset_y) / scale
    
    if progress_callback:
        progress_callback(25)
    
    # Step 2: Compute MSDF distances (Algorithm 7)
    r_dist, g_dist, b_dist = compute_msdf_batch(segments, contours, shape_x, shape_y)
    
    if progress_callback:
        progress_callback(70)
    
    # Handle invert
    if invert:
        r_dist = -r_dist
        g_dist = -g_dist
        b_dist = -b_dist
    
    # Convert to pixel units
    r_dist = r_dist * scale
    g_dist = g_dist * scale
    b_dist = b_dist * scale
    
    if progress_callback:
        progress_callback(80)
    
    # Step 3: Collision correction (Section 4.4.3)
    r_dist, g_dist, b_dist = detect_and_correct_collisions(
        r_dist, g_dist, b_dist, 
        threshold=range_px * 1.2
    )
    
    if progress_callback:
        progress_callback(90)
    
    # Normalize to [0, 1] range (Equation 4.1)
    r_channel = np.clip(0.5 + r_dist / (2 * range_px), 0, 1).astype(np.float32)
    g_channel = np.clip(0.5 + g_dist / (2 * range_px), 0, 1).astype(np.float32)
    b_channel = np.clip(0.5 + b_dist / (2 * range_px), 0, 1).astype(np.float32)
    
    if progress_callback:
        progress_callback(95)
    
    return r_channel, g_channel, b_channel


# ============================================================================
# Properties
# ============================================================================

_aspect = core.AspectRatioHelper()
get_depth_items = core.make_depth_items_callback("texops_msdf_props")


class MSDF_Properties(bpy.types.PropertyGroup):
    input_mode: bpy.props.EnumProperty(
        name="Mode",
        items=[('SINGLE', "Single", "Process single curve/collection"),
               ('BATCH', "Batch", "Process SVG folder")],
        default='SINGLE'
    )
    input_type: bpy.props.EnumProperty(
        name="Type",
        items=[('CURVE', "Curve", "Single curve object"),
               ('COLLECTION', "Collection", "Collection of curves")],
        default='CURVE'
    )
    input_curve: bpy.props.PointerProperty(
        name="Input Curve", type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'CURVE'
    )
    input_collection: bpy.props.PointerProperty(
        name="Input Collection", type=bpy.types.Collection
    )
    input_folder: bpy.props.StringProperty(name="Input Folder", default="//", subtype='DIR_PATH')
    
    angle_threshold: bpy.props.FloatProperty(
        name="Corner Angle", default=3.0, min=0.1, max=90.0,
        description="Minimum angle in degrees to be considered a corner"
    )
    range_px: bpy.props.FloatProperty(
        name="Range", default=4.0, min=0.5, max=64.0,
        description="Distance range in pixels (controls gradient width)"
    )
    margin: bpy.props.IntProperty(
        name="Margin", default=4, min=0, max=64,
        description="Pixel margin around shape"
    )
    invert: bpy.props.BoolProperty(
        name="Invert", default=False,
        description="Swap inside/outside"
    )
    quality: bpy.props.FloatProperty(
        name="Quality", default=100.0, min=0.0, max=100.0, subtype='PERCENTAGE',
        description="Bezier subdivision quality (higher = more segments)"
    )
    
    output_name: bpy.props.StringProperty(name="Output Name", default="")
    output_suffix: bpy.props.StringProperty(
        name="Suffix", default="_MSDF",
        description="Suffix added to output filename"
    )
    output_folder: bpy.props.StringProperty(name="Output Folder", default="//", subtype='DIR_PATH')
    
    output_width: bpy.props.IntProperty(
        name="Width", default=64, min=8, max=4096,
        update=lambda s, c: _aspect.update_width(s)
    )
    output_height: bpy.props.IntProperty(
        name="Height", default=64, min=8, max=4096,
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

class TEXOPS_OT_MSDF_Generate(core.BatchConfirmMixin, bpy.types.Operator):
    """Generate MSDF from curve"""
    bl_idname = "texops.msdf_generate"
    bl_label = "Generate MSDF"
    bl_options = {'REGISTER', 'UNDO'}
    
    def get_props(self, context):
        return context.scene.texops_msdf_props
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_msdf_props
        if props.input_mode == 'BATCH':
            return self.execute_batch(context, props)
        return self.execute_single(context, props)
    
    def execute_single(self, context, props):
        suffix = props.output_suffix
        
        if props.input_type == 'CURVE':
            if not props.input_curve:
                self.report({'ERROR'}, "No input curve selected")
                return {'CANCELLED'}
            
            curve_obj = props.input_curve
            if curve_obj.type != 'CURVE':
                self.report({'ERROR'}, "Selected object is not a curve")
                return {'CANCELLED'}
            
            with core.progress(context.window_manager) as update:
                output_rgba = self.process_curve(curve_obj, props, update)
                if output_rgba is None:
                    self.report({'ERROR'}, "Could not extract shape from curve")
                    return {'CANCELLED'}
                
                base_name = props.output_name if props.output_name else curve_obj.name
                output_name = base_name + suffix
                output_img = core.create_image(output_name, output_rgba, 'Non-Color')
                filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                core.save_image(output_img, filepath, props.file_format, 'RGB', props.color_depth)
                core.set_image_editor_image(context, output_img)
        
        else:  # COLLECTION
            if not props.input_collection:
                self.report({'ERROR'}, "No collection selected")
                return {'CANCELLED'}
            
            curves = [obj for obj in props.input_collection.objects if obj.type == 'CURVE']
            if not curves:
                self.report({'ERROR'}, "Collection has no curves")
                return {'CANCELLED'}
            
            with core.progress(context.window_manager) as update:
                output_rgba = self.process_curves(curves, props, update)
                if output_rgba is None:
                    self.report({'ERROR'}, "Could not extract shape from curves")
                    return {'CANCELLED'}
                
                base_name = props.output_name if props.output_name else props.input_collection.name
                output_name = base_name + suffix
                output_img = core.create_image(output_name, output_rgba, 'Non-Color')
                filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                core.save_image(output_img, filepath, props.file_format, 'RGB', props.color_depth)
                core.set_image_editor_image(context, output_img)
        
        self.report({'INFO'}, f"Saved: {filepath}")
        return {'FINISHED'}
    
    def execute_batch(self, context, props):
        svg_files = core.get_svgs_from_folder(props.input_folder)
        if not svg_files:
            self.report({'ERROR'}, "No SVG files found in folder")
            return {'CANCELLED'}
        
        suffix = props.output_suffix
        success = 0
        
        with core.progress(context.window_manager) as update:
            for i, svg_path in enumerate(svg_files):
                update(int(100 * i / len(svg_files)))
                
                curves = import_svg_curves(context, svg_path)
                if not curves:
                    continue
                
                output_rgba = self.process_curves(curves, props)
                if output_rgba is not None:
                    base_name = os.path.splitext(os.path.basename(svg_path))[0]
                    output_name = base_name + suffix
                    
                    output_img = core.create_image(output_name, output_rgba, 'Non-Color')
                    out_path = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                    core.save_image(output_img, out_path, props.file_format, 'RGB', props.color_depth)
                    success += 1
                
                # Clean up imported curves
                for curve in curves:
                    bpy.data.objects.remove(curve)
        
        self.report({'INFO'}, f"Processed {success}/{len(svg_files)} SVG files")
        return {'FINISHED'}
    
    def process_curve(self, curve_obj, props, update=None):
        """Process a single curve object into MSDF."""
        if update:
            update(5)
        
        # Subdivision tolerance based on quality
        tolerance = 0.1 * (10 ** (-3 * props.quality / 100))
        contours, bounds = extract_shape_from_curve(curve_obj, subdivision_tolerance=tolerance)
        
        if not contours:
            return None
        
        r_channel, g_channel, b_channel = generate_msdf(
            contours, bounds,
            props.output_width, props.output_height,
            props.range_px, props.margin, props.invert,
            update
        )
        
        if update:
            update(96)
        
        out_h, out_w = r_channel.shape
        output_rgba = np.zeros((out_h, out_w, 4), dtype=np.float32)
        output_rgba[:, :, 0] = r_channel
        output_rgba[:, :, 1] = g_channel
        output_rgba[:, :, 2] = b_channel
        output_rgba[:, :, 3] = 1.0
        
        return output_rgba
    
    def process_curves(self, curves, props, update=None):
        """Process multiple curves into a single MSDF."""
        if update:
            update(5)
        
        tolerance = 0.1 * (10 ** (-3 * props.quality / 100))
        contours, bounds = extract_shape_from_curves(curves, subdivision_tolerance=tolerance)
        
        if not contours:
            return None
        
        r_channel, g_channel, b_channel = generate_msdf(
            contours, bounds,
            props.output_width, props.output_height,
            props.range_px, props.margin, props.invert,
            update
        )
        
        if update:
            update(96)
        
        out_h, out_w = r_channel.shape
        output_rgba = np.zeros((out_h, out_w, 4), dtype=np.float32)
        output_rgba[:, :, 0] = r_channel
        output_rgba[:, :, 1] = g_channel
        output_rgba[:, :, 2] = b_channel
        output_rgba[:, :, 3] = 1.0
        
        return output_rgba


# ============================================================================
# UI Panel
# ============================================================================

class TEXOPS_PT_MSDF(bpy.types.Panel):
    bl_label = "MSDF Generator"
    bl_idname = "TEXOPS_PT_msdf"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'TexOps'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.texops_msdf_props
        
        # Input section
        box = layout.box()
        box.label(text="Input:", icon='CURVE_DATA')
        row = box.row()
        row.prop(props, "input_mode", expand=True)
        
        if props.input_mode == 'SINGLE':
            row = box.row()
            row.prop(props, "input_type", expand=True)
            
            if props.input_type == 'CURVE':
                box.prop(props, "input_curve", text="")
            else:
                box.prop(props, "input_collection", text="")
                if props.input_collection:
                    curve_count = sum(1 for obj in props.input_collection.objects if obj.type == 'CURVE')
                    box.label(text=f"{curve_count} curves", icon='INFO' if curve_count else 'ERROR')
        else:
            box.prop(props, "input_folder", text="")
            svg_count = len(core.get_svgs_from_folder(props.input_folder))
            box.label(
                text=f"{svg_count} SVG files" if svg_count else "No SVG files found",
                icon='INFO' if svg_count else 'ERROR'
            )
        
        layout.separator()
        
        # MSDF Settings
        box = layout.box()
        box.label(text="MSDF Settings:", icon='NODE_TEXTURE')
        box.prop(props, "range_px")
        box.prop(props, "margin")
        box.prop(props, "angle_threshold")
        row = box.row()
        row.prop(props, "invert", toggle=True)
        box.prop(props, "quality", slider=True)
        
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
        
        # Generate button
        row = layout.row()
        row.scale_y = 1.5
        row.operator("texops.msdf_generate", icon='EXPORT')


# ============================================================================
# Registration
# ============================================================================

classes = (
    MSDF_Properties,
    TEXOPS_OT_MSDF_Generate,
    TEXOPS_PT_MSDF,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_msdf_props = bpy.props.PointerProperty(type=MSDF_Properties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.texops_msdf_props