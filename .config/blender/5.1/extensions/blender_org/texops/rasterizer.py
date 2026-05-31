"""
Rasterizer Module for TexOps
Renders Blender Curve objects to raster images
"""

import bpy
import numpy as np
import math
import os

from . import core


# ============================================================================
# Vector Math
# ============================================================================

def vec2_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])

def vec2_length(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1])

def vec2_lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ============================================================================
# Curve Subdivision
# ============================================================================

def subdivide_cubic(p0, p1, p2, p3, tolerance=0.01):
    """Subdivide a cubic Bezier curve into line segments."""
    d1 = point_line_distance(p1, p0, p3)
    d2 = point_line_distance(p2, p0, p3)
    
    if d1 < tolerance and d2 < tolerance:
        return [(p0, p3)]
    
    # De Casteljau subdivision
    q0 = vec2_lerp(p0, p1, 0.5)
    q1 = vec2_lerp(p1, p2, 0.5)
    q2 = vec2_lerp(p2, p3, 0.5)
    r0 = vec2_lerp(q0, q1, 0.5)
    r1 = vec2_lerp(q1, q2, 0.5)
    s = vec2_lerp(r0, r1, 0.5)
    
    return subdivide_cubic(p0, q0, r0, s, tolerance) + subdivide_cubic(s, r1, q2, p3, tolerance)


def point_line_distance(p, a, b):
    """Calculate perpendicular distance from point to line segment."""
    ab = vec2_sub(b, a)
    ab_len = vec2_length(ab)
    if ab_len < 1e-12:
        return vec2_length(vec2_sub(p, a))
    return abs(ab[0] * (a[1] - p[1]) - ab[1] * (a[0] - p[0])) / ab_len


# ============================================================================
# Color Extraction
# ============================================================================

def get_curve_color(curve_obj):
    """Extract color from curve object's material or fallback to white."""
    curve_data = curve_obj.data
    
    # 1. Try material nodes (Diffuse, Principled, Emission)
    if curve_data.materials:
        mat = curve_data.materials[0]
        if mat:
            if mat.use_nodes and mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == 'BSDF_DIFFUSE':
                        return tuple(node.inputs['Color'].default_value[:3])
                    elif node.type == 'BSDF_PRINCIPLED':
                        return tuple(node.inputs['Base Color'].default_value[:3])
                    elif node.type == 'EMISSION':
                        return tuple(node.inputs['Color'].default_value[:3])
            else:
                return tuple(mat.diffuse_color[:3])
    
    # 2. Object viewport color
    if hasattr(curve_obj, 'color'):
        col = curve_obj.color[:3]
        if col != (1.0, 1.0, 1.0):
            return tuple(col)
    
    return (1.0, 1.0, 1.0)


# ============================================================================
# Shape Extraction from Blender Curves
# ============================================================================

def extract_segments_from_curve(curve_obj, subdivision_tolerance=0.01):
    """Extract line segments and colors from a Blender curve object."""
    if curve_obj.type != 'CURVE':
        return [], (0, 0, 1, 1), (1.0, 1.0, 1.0)
    
    curve_data = curve_obj.data
    matrix = curve_obj.matrix_world
    segments = []
    curve_color = get_curve_color(curve_obj)
    
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
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
                
                # Update bounds
                for pt in [start, ctrl1, ctrl2, end]:
                    min_x, min_y = min(min_x, pt[0]), min(min_y, pt[1])
                    max_x, max_y = max(max_x, pt[0]), max(max_y, pt[1])
                
                if vec2_length(vec2_sub(end, start)) < 1e-9:
                    continue
                
                # Check if curve is nearly straight
                d1 = point_line_distance(ctrl1, start, end)
                d2 = point_line_distance(ctrl2, start, end)
                
                if d1 < subdivision_tolerance and d2 < subdivision_tolerance:
                    segments.append((start, end))
                else:
                    segments.extend(subdivide_cubic(start, ctrl1, ctrl2, end, subdivision_tolerance))
        
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
                    segments.append((start, end))
    
    if min_x == float('inf'):
        return [], (0, 0, 1, 1), (1.0, 1.0, 1.0)
    
    return segments, (min_x, min_y, max_x, max_y), curve_color


# ============================================================================
# Rasterization
# ============================================================================

def rasterize_segments(segments, bounds, width, height, line_width, margin=0, 
                       fill=False, antialiasing=True, curve_colors=None, progress_callback=None):
    """Rasterize line segments to an image array with colors."""
    min_x, min_y, max_x, max_y = bounds
    shape_width, shape_height = max_x - min_x, max_y - min_y
    
    if shape_width < 1e-9 or shape_height < 1e-9:
        return np.zeros((height, width, 3), dtype=np.float32), np.zeros((height, width), dtype=np.float32)
    
    # Calculate scaling and offset
    usable_width, usable_height = width - 2 * margin, height - 2 * margin
    scale = min(usable_width / shape_width, usable_height / shape_height)
    offset_x = margin + (usable_width - shape_width * scale) / 2 - min_x * scale
    offset_y = margin + (usable_height - shape_height * scale) / 2 - min_y * scale
    
    if progress_callback:
        progress_callback(20)
    
    # Create coordinate grids
    px_grid, py_grid = np.meshgrid(
        np.arange(width, dtype=np.float32),
        np.arange(height, dtype=np.float32)
    )
    
    if curve_colors is None:
        curve_colors = [(1.0, 1.0, 1.0)] * len(segments)
    
    # Get the curve's color (all segments have same color for a single curve)
    r, g, b = curve_colors[0] if curve_colors else (1.0, 1.0, 1.0)
    
    # Initialize alpha mask
    alpha_mask = np.zeros((height, width), dtype=np.float32)
    
    # Fill interior FIRST if requested
    if fill and segments:
        interior = compute_interior(segments, scale, offset_x, offset_y, px_grid, py_grid)
        alpha_mask = interior.copy()
    
    if progress_callback:
        progress_callback(40)
    
    # Draw strokes (combine with fill using max for coverage)
    scaled_line_width = max(1.0, line_width * scale)
    half_width = scaled_line_width / 2
    
    for p0, p1 in segments:
        x0, y0 = p0[0] * scale + offset_x, p0[1] * scale + offset_y
        x1, y1 = p1[0] * scale + offset_x, p1[1] * scale + offset_y
        
        dx, dy = x1 - x0, y1 - y0
        len_sq = dx * dx + dy * dy
        if len_sq < 1e-20:
            continue
        
        # Project pixels onto segment
        t = np.clip(((px_grid - x0) * dx + (py_grid - y0) * dy) / len_sq, 0.0, 1.0)
        dist = np.sqrt((px_grid - (x0 + t * dx)) ** 2 + (py_grid - (y0 + t * dy)) ** 2)
        
        if antialiasing:
            contribution = np.clip(1.0 - (dist - half_width) / half_width, 0.0, 1.0)
        else:
            contribution = (dist <= half_width).astype(np.float32)
        
        alpha_mask = np.maximum(alpha_mask, contribution)
    
    if progress_callback:
        progress_callback(95)
    
    # Create constant color RGB output
    output_rgb = np.zeros((height, width, 3), dtype=np.float32)
    output_rgb[:, :, 0] = r
    output_rgb[:, :, 1] = g
    output_rgb[:, :, 2] = b
    
    return output_rgb, alpha_mask


def compute_interior(segments, scale, offset_x, offset_y, px_grid, py_grid):
    """Compute interior fill using winding number."""
    crossings = np.zeros(px_grid.shape, dtype=np.int32)
    
    for p0, p1 in segments:
        x0, y0 = p0[0] * scale + offset_x, p0[1] * scale + offset_y
        x1, y1 = p1[0] * scale + offset_x, p1[1] * scale + offset_y
        
        may_cross = ((y0 <= py_grid) & (py_grid < y1)) | ((y1 <= py_grid) & (py_grid < y0))
        if not np.any(may_cross):
            continue
        
        with np.errstate(divide='ignore', invalid='ignore'):
            t = np.where(may_cross, (py_grid - y0) / (y1 - y0 + 1e-20), 0)
            x_intersect = x0 + t * (x1 - x0)
        
        crossings += (may_cross & (x_intersect > px_grid)).astype(np.int32)
    
    return ((crossings % 2) == 1).astype(np.float32)


def composite_layer(base_rgb, base_alpha, layer_rgb, layer_alpha):
    """Composite layer over base using standard alpha blending."""
    # Alpha compositing: result = layer + base * (1 - layer_alpha)
    out_alpha = layer_alpha + base_alpha * (1.0 - layer_alpha)
    
    # Avoid division by zero
    safe_alpha = np.maximum(out_alpha, 1e-10)
    
    out_rgb = np.zeros_like(base_rgb)
    for c in range(3):
        out_rgb[:, :, c] = (layer_rgb[:, :, c] * layer_alpha + 
                           base_rgb[:, :, c] * base_alpha * (1.0 - layer_alpha)) / safe_alpha
    
    # Where output alpha is zero, RGB doesn't matter
    out_rgb = np.where(out_alpha[:, :, np.newaxis] > 0, out_rgb, 0)
    
    return out_rgb, out_alpha


def composite_over_background(rgb, alpha, bg_color):
    """Composite RGB+Alpha over background color."""
    bg_r, bg_g, bg_b, bg_a = bg_color
    h, w = alpha.shape
    output = np.zeros((h, w, 4), dtype=np.float32)
    
    if bg_a > 0:
        # Composite over background
        output[:, :, 0] = bg_r * (1.0 - alpha) + rgb[:, :, 0] * alpha
        output[:, :, 1] = bg_g * (1.0 - alpha) + rgb[:, :, 1] * alpha
        output[:, :, 2] = bg_b * (1.0 - alpha) + rgb[:, :, 2] * alpha
        output[:, :, 3] = bg_a * (1.0 - alpha) + alpha
    else:
        # Transparent background - preserve alpha
        output[:, :, :3] = rgb
        output[:, :, 3] = alpha
    
    return output


def determine_raster_color_mode(output_rgba, props):
    """
    Determine appropriate color mode for rasterized output.
    
    Returns 'BW', 'RGB', or 'RGBA' based on content and settings.
    """
    # If background is transparent, need alpha channel
    if props.bg_color[3] == 0:
        # Check if alpha actually varies
        alpha = output_rgba[:, :, 3]
        if np.ptp(alpha) > 0.01:
            # Check if grayscale (force_bw or all colors same)
            if props.force_bw:
                return 'RGBA'  # Need alpha, but content is grayscale - still RGBA for transparency
            r, g, b = output_rgba[:, :, 0], output_rgba[:, :, 1], output_rgba[:, :, 2]
            if np.allclose(r, g, atol=0.01) and np.allclose(g, b, atol=0.01):
                return 'RGBA'  # Grayscale with alpha
            return 'RGBA'
    
    # Opaque background - no alpha needed
    if props.force_bw:
        return 'BW'
    
    # Check if output is grayscale
    r, g, b = output_rgba[:, :, 0], output_rgba[:, :, 1], output_rgba[:, :, 2]
    if np.allclose(r, g, atol=0.01) and np.allclose(g, b, atol=0.01):
        return 'BW'
    
    return 'RGB'


# ============================================================================
# Curve Collection and Sorting
# ============================================================================

def collect_curves_sorted(root_curve):
    """Collect a single curve (no children)."""
    return [root_curve] if root_curve.type == 'CURVE' else []


def collect_collection_curves_sorted(collection):
    """Collect curves from a collection, sorted by Z position."""
    curves = [obj for obj in collection.objects if obj.type == 'CURVE']
    curves.sort(key=lambda c: c.location.z)
    return curves


def collect_imported_curves_sorted(context):
    """Collect selected curves sorted by Z (for SVG imports)."""
    curves = [obj for obj in context.selected_objects if obj.type == 'CURVE']
    curves.sort(key=lambda c: c.location.z)
    return curves


def import_svg_and_get_curves(context, svg_path):
    """Import SVG file and return collected curves."""
    try:
        bpy.ops.import_curve.svg(filepath=svg_path)
    except Exception:
        return []
    return collect_imported_curves_sorted(context)


# ============================================================================
# Properties
# ============================================================================

_aspect = core.AspectRatioHelper()
get_depth_items = core.make_depth_items_callback("texops_rasterizer_props")


class Rasterizer_Properties(bpy.types.PropertyGroup):
    # Input
    input_mode: bpy.props.EnumProperty(
        name="Mode",
        items=[('SINGLE', "Single", "Process single curve/group/SVG"),
               ('BATCH', "Batch", "Process SVG folder")],
        default='SINGLE'
    )
    input_type: bpy.props.EnumProperty(
        name="Type",
        items=[('CURVE', "Curve", "Single curve object"),
               ('COLLECTION', "Collection", "Collection of curves (e.g. imported SVG)")],
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
    
    # Rasterization settings
    line_width: bpy.props.FloatProperty(
        name="Line Width", default=2.0, min=0.0,
        description="Width of the rendered line in pixels"
    )
    margin: bpy.props.IntProperty(
        name="Margin", default=16, min=0, max=128,
        description="Margin around the shape in pixels"
    )
    fill: bpy.props.BoolProperty(
        name="Fill", default=False,
        description="Fill the interior of closed curves"
    )
    antialiasing: bpy.props.BoolProperty(
        name="AA", default=True,
        description="Smooth edges with antialiasing"
    )
    force_bw: bpy.props.BoolProperty(
        name="BW", default=False,
        description="Force all curves to white (useful for SDF input)"
    )
    quality: bpy.props.FloatProperty(
        name="Quality", default=100.0, min=0.0, max=100.0, subtype='PERCENTAGE',
        description="Subdivision quality for curved segments"
    )
    
    # Background
    bg_color: bpy.props.FloatVectorProperty(
        name="Background", subtype='COLOR_GAMMA', size=4,
        min=0.0, max=1.0, default=(0.0, 0.0, 0.0, 0.0),
        description="Background color (alpha 0 = transparent)"
    )
    
    # Output
    output_name: bpy.props.StringProperty(name="Output Name", default="")
    output_suffix: bpy.props.StringProperty(name="Suffix", default="_Rasterized",
                                            description="Suffix added to output filename")
    output_folder: bpy.props.StringProperty(name="Output Folder", default="//", subtype='DIR_PATH')
    output_width: bpy.props.IntProperty(
        name="Width", default=512, min=8, max=4096,
        update=lambda s, c: _aspect.update_width(s)
    )
    output_height: bpy.props.IntProperty(
        name="Height", default=512, min=8, max=4096,
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

class TEXOPS_OT_Rasterizer_Generate(core.BatchConfirmMixin, bpy.types.Operator):
    """Rasterize curve to image"""
    bl_idname = "texops.rasterizer_generate"
    bl_label = "Rasterize Curve"
    bl_options = {'REGISTER', 'UNDO'}
    
    def get_props(self, context):
        return context.scene.texops_rasterizer_props
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_rasterizer_props
        if props.input_mode == 'BATCH':
            return self.execute_batch(context, props)
        return self.execute_single(context, props)
    
    def execute_single(self, context, props):
        curves = []
        base_name = "Output"
        
        if props.input_type == 'CURVE':
            if not props.input_curve:
                self.report({'ERROR'}, "No input curve selected")
                return {'CANCELLED'}
            if props.input_curve.type != 'CURVE':
                self.report({'ERROR'}, "Selected object is not a curve")
                return {'CANCELLED'}
            curves = collect_curves_sorted(props.input_curve)
            base_name = props.input_curve.name
            
        elif props.input_type == 'COLLECTION':
            if not props.input_collection:
                self.report({'ERROR'}, "No collection selected")
                return {'CANCELLED'}
            curves = collect_collection_curves_sorted(props.input_collection)
            base_name = props.input_collection.name
            if not curves:
                self.report({'ERROR'}, "Collection has no curves")
                return {'CANCELLED'}
        
        with core.progress(context.window_manager) as update:
            output_rgba = self.rasterize_curves(curves, props, update)
            
            if output_rgba is None:
                self.report({'ERROR'}, "Could not extract geometry from curve(s)")
                return {'CANCELLED'}
            
            output_name = (props.output_name if props.output_name else base_name) + props.output_suffix
            output_img = core.create_image(output_name, output_rgba, 'Non-Color')
            filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
            color_mode = determine_raster_color_mode(output_rgba, props)
            core.save_image(output_img, filepath, props.file_format, color_mode, props.color_depth)
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
                
                curves = import_svg_and_get_curves(context, svg_path)
                if not curves:
                    continue
                
                output_rgba = self.rasterize_curves(curves, props)
                if output_rgba is not None:
                    base_name = os.path.splitext(os.path.basename(svg_path))[0]
                    output_name = base_name + suffix
                    output_img = core.create_image(output_name, output_rgba, 'Non-Color')
                    filepath = core.generate_output_path(output_name, "", props.output_folder, props.file_format)
                    color_mode = determine_raster_color_mode(output_rgba, props)
                    core.save_image(output_img, filepath, props.file_format, color_mode, props.color_depth)
                    success += 1
                
                # Clean up imported curves
                for curve in curves:
                    bpy.data.objects.remove(curve)
        
        self.report({'INFO'}, f"Processed {success}/{len(svg_files)} SVG files")
        return {'FINISHED'}
    
    def rasterize_curves(self, curves, props, update=None):
        """Rasterize multiple curves into single image with proper layering."""
        if update:
            update(5)
        
        tolerance = 0.1 * (10 ** (-3 * props.quality / 100))
        width, height = props.output_width, props.output_height
        
        # First pass: calculate combined bounds from all curves
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        curve_data = []  # Store (curve, segments, color) for each curve
        for curve in curves:
            segments, bounds, color = extract_segments_from_curve(curve, tolerance)
            if segments:
                # Override color if force_bw is enabled
                if props.force_bw:
                    color = (1.0, 1.0, 1.0)
                curve_data.append((curve, segments, color))
                min_x, min_y = min(min_x, bounds[0]), min(min_y, bounds[1])
                max_x, max_y = max(max_x, bounds[2]), max(max_y, bounds[3])
        
        if not curve_data:
            return None
        
        combined_bounds = (min_x, min_y, max_x, max_y)
        
        if update:
            update(10)
        
        # Initialize output with zeros (transparent)
        result_rgb = np.zeros((height, width, 3), dtype=np.float32)
        result_alpha = np.zeros((height, width), dtype=np.float32)
        
        # Process each curve back-to-front (already sorted by Z)
        total_curves = len(curve_data)
        for idx, (curve, segments, color) in enumerate(curve_data):
            colors = [color] * len(segments)
            
            # Rasterize this curve
            curve_rgb, curve_alpha = rasterize_segments(
                segments, combined_bounds,
                width, height,
                props.line_width / 100.0, props.margin,
                props.fill, props.antialiasing, colors, None
            )
            
            # Composite this curve over the accumulated result
            result_rgb, result_alpha = composite_layer(
                result_rgb, result_alpha,
                curve_rgb, curve_alpha
            )
            
            if update:
                progress = 10 + int(80 * (idx + 1) / total_curves)
                update(progress)
        
        if update:
            update(95)
        
        # Finally composite over background
        return composite_over_background(result_rgb, result_alpha, props.bg_color)


# ============================================================================
# UI Panel
# ============================================================================

class TEXOPS_PT_Rasterizer(bpy.types.Panel):
    bl_label = "Rasterizer"
    bl_idname = "TEXOPS_PT_rasterizer"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'TexOps'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.texops_rasterizer_props
        
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
            elif props.input_type == 'COLLECTION':
                box.prop(props, "input_collection", text="")
                if props.input_collection:
                    curve_count = sum(1 for obj in props.input_collection.objects if obj.type == 'CURVE')
                    box.label(text=f"{curve_count} curves", 
                             icon='INFO' if curve_count else 'ERROR')
        else:
            box.prop(props, "input_folder", text="")
            svg_count = len(core.get_svgs_from_folder(props.input_folder))
            box.label(text=f"{svg_count} SVG files" if svg_count else "No SVG files found",
                     icon='INFO' if svg_count else 'ERROR')
        
        layout.separator()
        
        # Rasterization settings
        box = layout.box()
        box.label(text="Rasterization:", icon='BRUSHES_ALL')
        box.prop(props, "line_width")
        box.prop(props, "margin")
        row = box.row(align=True)
        row.prop(props, "fill", toggle=True)
        row.prop(props, "antialiasing", toggle=True)
        row.prop(props, "force_bw", toggle=True)
        box.prop(props, "quality", slider=True)
        row = box.row(align=True)
        row.label(text="BG:")
        row.prop(props, "bg_color", text="")
        
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
        row.operator("texops.rasterizer_generate", icon='EXPORT')


# ============================================================================
# Registration
# ============================================================================

classes = (
    Rasterizer_Properties,
    TEXOPS_OT_Rasterizer_Generate,
    TEXOPS_PT_Rasterizer,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_rasterizer_props = bpy.props.PointerProperty(type=Rasterizer_Properties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.texops_rasterizer_props