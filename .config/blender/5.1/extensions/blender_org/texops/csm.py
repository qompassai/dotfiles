"""
ARCSM Texture Generator Module for TexOps
Generates height maps to Anisotropic Relaxed Cone Step Mapping format
"""

import bpy
import numpy as np
import math
import os

from . import core


# ============================================================================
# Core ARCSM Functions
# ============================================================================

def compute_cone_ratios(height_map, search_radius, num_sectors, use_relaxed=True, 
                       use_robust=True, progress_callback=None):
    """Compute Cone Step Mapping ratios for specified number of sectors."""
    map_height, map_width = height_map.shape
    
    tex_scale = 1.0 / max(map_width, map_height)
    sector_angle = 2.0 * math.pi / num_sectors if num_sectors > 0 else 2.0 * math.pi
    
    cone_ratios = np.ones((num_sectors, map_height, map_width), dtype=np.float32)
    
    # Assign offsets to sectors
    sector_offsets = [[] for _ in range(num_sectors)]
    
    for dy in range(-search_radius, search_radius + 1):
        for dx in range(-search_radius, search_radius + 1):
            if dx == 0 and dy == 0:
                continue
            
            dist_pixels = math.sqrt(dx * dx + dy * dy)
            if dist_pixels > search_radius:
                continue
            
            dist_tex = dist_pixels * tex_scale
            angle = math.atan2(dy, dx)
            
            # Assign to appropriate sector
            for sector in range(num_sectors):
                sector_center = -math.pi + (sector + 0.5) * sector_angle
                angle_diff = angle - sector_center
                
                while angle_diff > math.pi:
                    angle_diff -= 2 * math.pi
                while angle_diff < -math.pi:
                    angle_diff += 2 * math.pi
                
                if abs(angle_diff) <= sector_angle / 2:
                    sector_offsets[sector].append((dx, dy, dist_tex, dist_pixels))
                    break
    
    if progress_callback:
        progress_callback(10)
    
    # Compute cone ratios for each sector
    for sector in range(num_sectors):
        offsets = sector_offsets[sector]
        
        for dx, dy, dist_tex, dist_pixels in offsets:
            if dy >= 0:
                src_y = slice(0, map_height - dy) if dy > 0 else slice(None)
                dst_y = slice(dy, map_height) if dy > 0 else slice(None)
            else:
                src_y = slice(-dy, map_height)
                dst_y = slice(0, map_height + dy)
            
            if dx >= 0:
                src_x = slice(0, map_width - dx) if dx > 0 else slice(None)
                dst_x = slice(dx, map_width) if dx > 0 else slice(None)
            else:
                src_x = slice(-dx, map_width)
                dst_x = slice(0, map_width + dx)
            
            src_depths = height_map[src_y, src_x]
            dst_depths = height_map[dst_y, dst_x]
            
            if use_relaxed:
                max_depth = dst_depths.copy()
                num_samples = max(2, int(dist_pixels / 2))
                
                for sample in range(1, num_samples):
                    t = sample / num_samples
                    inter_dx = int(round(dx * t))
                    inter_dy = int(round(dy * t))
                    
                    if inter_dx == 0 and inter_dy == 0:
                        continue
                    
                    if inter_dy >= 0:
                        int_src_y = slice(0, map_height - inter_dy) if inter_dy > 0 else slice(None)
                        int_dst_y = slice(inter_dy, map_height) if inter_dy > 0 else slice(None)
                    else:
                        int_src_y = slice(-inter_dy, map_height)
                        int_dst_y = slice(0, map_height + inter_dy)
                    
                    if inter_dx >= 0:
                        int_src_x = slice(0, map_width - inter_dx) if inter_dx > 0 else slice(None)
                        int_dst_x = slice(inter_dx, map_width) if inter_dx > 0 else slice(None)
                    else:
                        int_src_x = slice(-inter_dx, map_width)
                        int_dst_x = slice(0, map_width + inter_dx)
                    
                    inter_depths = height_map[int_dst_y, int_dst_x]
                    
                    min_h = min(max_depth.shape[0], inter_depths.shape[0])
                    min_w = min(max_depth.shape[1], inter_depths.shape[1])
                    
                    max_depth[:min_h, :min_w] = np.maximum(
                        max_depth[:min_h, :min_w],
                        inter_depths[:min_h, :min_w]
                    )
                
                depth_diff = max_depth - src_depths[:max_depth.shape[0], :max_depth.shape[1]]
            else:
                depth_diff = dst_depths - src_depths
            
            with np.errstate(divide='ignore', invalid='ignore'):
                ratios = np.where(depth_diff > 0.0001, dist_tex / depth_diff, 1.0)
            ratios = np.clip(ratios, 0.0, 1.0)
            
            current = cone_ratios[sector, src_y, src_x]
            if use_relaxed and ratios.shape != current.shape:
                min_h = min(ratios.shape[0], current.shape[0])
                min_w = min(ratios.shape[1], current.shape[1])
                cone_ratios[sector, src_y, src_x][:min_h, :min_w] = np.minimum(
                    current[:min_h, :min_w], ratios[:min_h, :min_w]
                )
            else:
                cone_ratios[sector, src_y, src_x] = np.minimum(current, ratios)
        
        if progress_callback:
            progress_callback(10 + int(70 * (sector + 1) / num_sectors))
    
    return cone_ratios


def apply_robust_correction(cone_ratios):
    """
    Apply robust correction: replace each cone ratio with min of 3x3 neighborhood.
    This prevents bilinear interpolation artifacts (Section 4 of Robust CSM paper).
    """
    num_sectors, map_height, map_width = cone_ratios.shape
    corrected = np.zeros_like(cone_ratios)
    
    for sector in range(num_sectors):
        for i in range(map_height):
            for j in range(map_width):
                min_val = 1.0
                for di in range(-1, 2):
                    for dj in range(-1, 2):
                        ni, nj = i + di, j + dj
                        if 0 <= ni < map_height and 0 <= nj < map_width:
                            min_val = min(min_val, cone_ratios[sector, ni, nj])
                corrected[sector, i, j] = min_val
    
    return corrected


def generate_arcsm_texture(height_map, search_radius, num_sectors, pack_height,
                          height_channel, use_relaxed=True, use_robust=True, progress_callback=None):
    """Generate the final CSM/ARCSM texture."""
    map_height, map_width = height_map.shape
    
    # Compute cone ratios
    cone_ratios = compute_cone_ratios(
        height_map, search_radius, num_sectors, use_relaxed, use_robust, progress_callback
    )
    
    # Apply robust correction if enabled
    if use_robust:
        if progress_callback:
            progress_callback(80)
        cone_ratios = apply_robust_correction(cone_ratios)
    
    if progress_callback:
        progress_callback(85)
    
    # Determine output channels based on whether we're packing height
    if pack_height:
        num_channels = num_sectors + 1
    else:
        num_channels = num_sectors
    
    num_channels = min(4, num_channels)  # Cap at 4 (RGBA)
    
    # Pack into output texture
    output = np.zeros((map_height, map_width, num_channels), dtype=np.float32)
    
    # Determine channel packing order
    if pack_height and height_channel == 'FIRST':
        # Height first, then cone ratios
        output[:, :, 0] = height_map
        for sector in range(min(num_sectors, num_channels - 1)):
            output[:, :, sector + 1] = cone_ratios[sector]
    elif pack_height and height_channel == 'LAST':
        # Cone ratios first, then height in last channel
        for sector in range(min(num_sectors, num_channels - 1)):
            output[:, :, sector] = cone_ratios[sector]
        output[:, :, num_channels - 1] = height_map
    else:
        # No height packing, just cone ratios
        for sector in range(num_channels):
            output[:, :, sector] = cone_ratios[sector]
    
    if progress_callback:
        progress_callback(90)
    
    return output


def resize_if_needed(arcsm_data, props):
    """Resize ARCSM result if custom dimensions specified."""
    out_h, out_w = arcsm_data.shape[:2]
    target_w = props.output_width if props.output_width > 0 else out_w
    target_h = props.output_height if props.output_height > 0 else out_h
    
    if (target_w, target_h) != (out_w, out_h):
        return core.resize_bilinear(arcsm_data, target_h, target_w), target_w, target_h
    return arcsm_data, out_w, out_h


# ============================================================================
# Properties
# ============================================================================

get_depth_items = core.make_depth_items_callback("texops_arcsm_props")
_aspect = core.AspectRatioHelper()


class ARCSM_Properties(bpy.types.PropertyGroup):
    input_mode: bpy.props.EnumProperty(
        name="Mode",
        items=[
            ('SINGLE', "Single", "Process single image"),
            ('BATCH', "Batch", "Process folder of images"),
        ],
        default='SINGLE'
    )
    
    input_image: bpy.props.StringProperty(name="Image", default="")
    input_channel: bpy.props.EnumProperty(name="Channel", items=core.CHANNEL_ITEMS, default='GRAY')
    input_folder: bpy.props.StringProperty(name="Folder", default="//", subtype='DIR_PATH')
    
    search_radius: bpy.props.IntProperty(
        name="Search Radius", default=32, min=8, max=128
    )
    
    # Anisotropic sectors
    def update_num_sectors(self, context):
        """Disable pack_height when 4 sectors selected"""
        if int(self.num_sectors) == 4:
            self.pack_height = False
    
    num_sectors: bpy.props.EnumProperty(
        name="Anisotropic",
        items=[
            ('1', "1 (R)", "Isotropic - 1 cone for all directions"),
            ('2', "2 (RG)", "2 directional cones (180° each)"),
            ('3', "3 (RGB)", "3 directional cones (120° each)"),
            ('4', "4 (RGBA)", "4 directional cones (90° each)"),
        ],
        default='3',
        description="Number of directional cone sectors",
        update=update_num_sectors
    )
    
    pack_height: bpy.props.BoolProperty(
        name="Pack Height",
        default=False,
        description="Pack height map into available channel (disabled for 4 sectors)"
    )
    
    height_channel: bpy.props.EnumProperty(
        name="Height Channel",
        items=[
            ('FIRST', "First", "Pack height in first channel (R)"),
            ('LAST', "Last", "Pack height in last available channel"),
        ],
        default='FIRST',
        description="Which channel to pack the height map into"
    )
    
    # Method toggles
    use_relaxed: bpy.props.BoolProperty(
        name="Relaxed",
        default=True,
        description="Use relaxed cone stepping (wider cones, requires refinement)"
    )
    
    use_robust: bpy.props.BoolProperty(
        name="Robust",
        default=True,
        description="Apply robust correction to prevent bilinear interpolation artifacts"
    )
    
    output_name: bpy.props.StringProperty(name="Output Name", default="CSM")
    output_suffix: bpy.props.StringProperty(
        name="Suffix", default="_CSM",
        description="Suffix added to output filename"
    )
    output_folder: bpy.props.StringProperty(name="Output Folder", default="//", subtype='DIR_PATH')
    output_width: bpy.props.IntProperty(
        name="Width", default=0, min=0, max=16384,
        description="Output width (0 = same as input)",
        update=lambda s, c: _aspect.update_width(s)
    )
    output_height: bpy.props.IntProperty(
        name="Height", default=0, min=0, max=16384,
        description="Output height (0 = same as input)",
        update=lambda s, c: _aspect.update_height(s)
    )
    lock_aspect: bpy.props.BoolProperty(
        name="Lock Aspect", default=True,
        update=lambda s, c: _aspect.update_lock(s)
    )
    
    file_format: bpy.props.EnumProperty(
        name="Format",
        items=core.get_format_items,
        update=core.update_depth_for_format
    )
    color_depth: bpy.props.EnumProperty(name="Depth", items=get_depth_items)


# ============================================================================
# Operators
# ============================================================================

class TEXOPS_OT_ARCSM_LoadImage(core.LoadImageOperatorBase):
    """Load image file"""
    bl_idname = "texops.arcsm_load_image"
    bl_label = "Load Image"
    
    def get_props(self, context):
        return context.scene.texops_arcsm_props


class TEXOPS_OT_ARCSM_PreviewInput(core.ShowImageOperatorBase):
    """Preview the selected input image"""
    bl_idname = "texops.arcsm_preview_input"
    bl_label = "Preview Input"
    
    def get_props(self, context):
        return context.scene.texops_arcsm_props


class TEXOPS_OT_ARCSM_Generate(core.BatchConfirmMixin, bpy.types.Operator):
    """Generate height map to CSM/ARCSM texture"""
    bl_idname = "texops.arcsm_generate"
    bl_label = "Generate CSM"
    bl_options = {'REGISTER'}
    
    def get_props(self, context):
        return context.scene.texops_arcsm_props
    
    @core.with_error_handling
    def execute(self, context):
        props = context.scene.texops_arcsm_props
        
        if props.input_mode == 'SINGLE':
            return self.process_single(context, props)
        else:
            return self.process_batch(context, props)
    
    def process_single(self, context, props):
        input_img, result = core.get_input_image(props, self)
        if not input_img:
            return result
        
        with core.progress(context.window_manager) as update:
            update(5)
            output_img = self.generate_image(props, input_img, update)
        
        if output_img:
            core.set_image_editor_image(context, output_img)
        
        return {'FINISHED'}
    
    def process_batch(self, context, props):
        files = core.get_images_from_folder(props.input_folder)
        if not files:
            self.report({'ERROR'}, "No images found in folder")
            return {'CANCELLED'}
        
        success_count = 0
        last_output = None
        
        with core.progress(context.window_manager) as update:
            for i, filepath in enumerate(files):
                update(int(100 * i / len(files)))
                
                img = core.load_image(filepath)
                if not img:
                    continue
                
                output_img = self.generate_image(props, img, is_batch=True)
                if output_img:
                    success_count += 1
                    last_output = output_img
        
        if last_output:
            core.set_image_editor_image(context, last_output)
        
        self.report({'INFO'}, f"Generated {success_count}/{len(files)} images")
        return {'FINISHED'}
    
    def generate_image(self, props, input_img, progress_update=None, is_batch=False):
        """Generate CSM texture from input image. Returns output image or None."""
        def update_progress(value):
            if progress_update and not is_batch:
                progress_update(value)
        
        update_progress(10)
        
        # Read as grayscale from selected channel
        height_map, width, height = core.read_pixels_grayscale(input_img, props.input_channel)
        
        # Get parameters
        num_sectors = int(props.num_sectors)
        pack_height = props.pack_height and num_sectors < 4
        
        # Generate CSM/ARCSM data
        arcsm_data = generate_arcsm_texture(
            height_map, props.search_radius, num_sectors, pack_height,
            props.height_channel, props.use_relaxed, props.use_robust, update_progress
        )
        
        update_progress(90)
        
        # Resize if needed
        arcsm_data, out_w, out_h = resize_if_needed(arcsm_data, props)
        
        # Determine channel format for saving
        num_channels = arcsm_data.shape[2]
        if num_channels == 1:
            channel_format = 'BW'
        elif num_channels == 3:
            channel_format = 'RGB'
        else:
            channel_format = 'RGBA'
        
        # Pad to 4 channels if needed for proper saving
        if num_channels < 4:
            padded = np.zeros((arcsm_data.shape[0], arcsm_data.shape[1], 4), dtype=np.float32)
            padded[:, :, :num_channels] = arcsm_data
            padded[:, :, 3] = 1.0
            arcsm_data = padded
        
        # Generate output name
        if props.input_mode == 'SINGLE' and props.output_name:
            output_name = props.output_name + props.output_suffix
        else:
            base_name = os.path.splitext(input_img.name)[0]
            output_name = base_name + props.output_suffix
        
        output_img = core.create_image(output_name, arcsm_data, 'Non-Color')
        
        output_path = core.generate_output_path(
            output_name, "", props.output_folder, props.file_format
        )
        
        core.save_image(
            output_img, output_path, props.file_format, channel_format, props.color_depth
        )
        
        if not is_batch:
            self.report({'INFO'}, f"Saved: {output_path}")
        
        return output_img


# ============================================================================
# UI Panel
# ============================================================================

class TEXOPS_PT_ARCSM(bpy.types.Panel):
    """CSM/ARCSM Generator Panel"""
    bl_label = "CSM Generator"
    bl_idname = "TEXOPS_PT_arcsm"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'TexOps'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.texops_arcsm_props
        
        box = layout.box()
        box.label(text="Input:", icon='IMAGE_DATA')
        row = box.row()
        row.prop(props, "input_mode", expand=True)
        
        if props.input_mode == 'SINGLE':
            row = box.row(align=True)
            row.prop_search(props, "input_image", bpy.data, "images", text="")
            row.operator("texops.arcsm_load_image", text="", icon='FILEBROWSER')
            sub = row.row()
            sub.scale_x = 0.55
            sub.prop(props, "input_channel", text="")
            sub = row.row(align=True)
            sub.enabled = bool(props.input_image)
            sub.operator("texops.arcsm_preview_input", text="", icon='HIDE_OFF')
        else:
            box.prop(props, "input_folder", text="")
            files = core.get_images_from_folder(props.input_folder)
            box.label(text=f"{len(files)} images found" if files else "No images found", 
                      icon='INFO' if files else 'ERROR')
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Settings:", icon='SETTINGS')
        box.prop(props, "search_radius")
        
        row = box.row(align=True)
        row.label(text="Anisotropic:")
        row.prop(props, "num_sectors", text="")
        
        # Method toggles
        row = box.row(align=True)
        row.prop(props, "use_relaxed", toggle=True)
        row.prop(props, "use_robust", toggle=True)
        
        # Pack height option (disabled for 4 sectors)
        num_sectors = int(props.num_sectors)
        row = box.row(align=True)
        row.enabled = num_sectors < 4
        row.prop(props, "pack_height")
        
        # Height channel position (only if pack_height is enabled)
        if props.pack_height and num_sectors < 4:
            row.prop(props, "height_channel", expand=True)
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Output:", icon='FILE_IMAGE')
        if props.input_mode == 'SINGLE':
            box.prop(props, "output_name")
        box.prop(props, "output_suffix")
        box.prop(props, "output_folder", text="")
        
        row = box.row(align=True)
        row.prop(props, "lock_aspect", text="", icon='LOCKED' if props.lock_aspect else 'UNLOCKED')
        row.prop(props, "output_width", text="Width")
        row.prop(props, "output_height", text="Height")
        
        row = box.row(align=True)
        row.prop(props, "file_format", text="")
        row.prop(props, "color_depth", text="")
        
        layout.separator()
        
        row = layout.row()
        row.scale_y = 1.5
        text = "Generate Batch" if props.input_mode == 'BATCH' else "Generate CSM"
        row.operator("texops.arcsm_generate", text=text, icon='EXPORT')


# ============================================================================
# Registration
# ============================================================================

classes = (
    ARCSM_Properties,
    TEXOPS_OT_ARCSM_LoadImage,
    TEXOPS_OT_ARCSM_PreviewInput,
    TEXOPS_OT_ARCSM_Generate,
    TEXOPS_PT_ARCSM,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texops_arcsm_props = bpy.props.PointerProperty(type=ARCSM_Properties)


def unregister():
    del bpy.types.Scene.texops_arcsm_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)