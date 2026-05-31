import bpy
from .utils import APPLY_LOCK

def inspector_prop_update(self, context):
    if APPLY_LOCK["locked"]: return

def props_update_handler(self, context):
    try:
        from .preview_logic import update_preview
        update_preview(context.scene)
    except: pass

def update_anim_frames(self, context):
    target = round(self.anim_frames / 8.0) * 8
    if target < 16:
        target = 16
    if self.anim_frames != target:
        self["anim_frames"] = target
    try:
        from .hifi_auto_anim import trigger_deep_wipe
        trigger_deep_wipe()
    except Exception as e: 
        pass

class HiFiSelectedProps(bpy.types.PropertyGroup):
    sel_loc_x: bpy.props.FloatProperty(name="Loc X", default=0.0, update=inspector_prop_update)
    sel_loc_y: bpy.props.FloatProperty(name="Loc Y", default=0.0, update=inspector_prop_update)
    sel_loc_z: bpy.props.FloatProperty(name="Loc Z", default=0.0, update=inspector_prop_update)
    sel_rot_x_deg: bpy.props.FloatProperty(name="Rot X", default=0.0, update=inspector_prop_update)
    sel_rot_y_deg: bpy.props.FloatProperty(name="Rot Y", default=0.0, update=inspector_prop_update)
    sel_rot_z_deg: bpy.props.FloatProperty(name="Rot Z", default=0.0, update=inspector_prop_update)
    sel_scale_x: bpy.props.FloatProperty(name="Scale X", default=1.0, update=inspector_prop_update)
    sel_scale_y: bpy.props.FloatProperty(name="Scale Y", default=1.0, update=inspector_prop_update)
    sel_scale_z: bpy.props.FloatProperty(name="Scale Z", default=1.0, update=inspector_prop_update)
    
    apply_loc_x: bpy.props.BoolProperty(name="Apply X", default=True)
    apply_loc_y: bpy.props.BoolProperty(name="Apply Y", default=True)
    apply_loc_z: bpy.props.BoolProperty(name="Apply Z", default=True)
    apply_rot_x: bpy.props.BoolProperty(name="Apply X", default=True)
    apply_rot_y: bpy.props.BoolProperty(name="Apply Y", default=True)
    apply_rot_z: bpy.props.BoolProperty(name="Apply Z", default=True)
    apply_scale_x: bpy.props.BoolProperty(name="Apply X", default=True)
    apply_scale_y: bpy.props.BoolProperty(name="Apply Y", default=True)
    apply_scale_z: bpy.props.BoolProperty(name="Apply Z", default=True)

class HiFiProperties(bpy.types.PropertyGroup):
    unit_type: bpy.props.EnumProperty(
        name="Unit System",
        items=[('METERS','Meters',''),('FEET','Feet',''),('INCHES','Inches',''),('CENTIMETERS','Centimeters',''),('MILLIMETERS','Millimeters','')],
        default='METERS', update=props_update_handler
    )

    use_sollumz: bpy.props.BoolProperty(
        name="Enable Sollumz Integration", 
        default=False
    )

    anim_axis: bpy.props.EnumProperty(
        name="Rotation Axis",
        items=[('X','X Axis',''),('Y','Y Axis',''),('Z','Z Axis','')],
        default='Z', update=props_update_handler
    )
    
    anim_reverse: bpy.props.BoolProperty(
        name="Reverse Direction", 
        default=False, 
        update=props_update_handler
    )

    anim_frames: bpy.props.IntProperty(
        name="Total Frames", 
        default=240, 
        min=16,
        update=update_anim_frames
    )

    generator_type: bpy.props.EnumProperty(
        name="Generator Model",
        items=[
            ('WALL','Wall',''),('FLOOR','Floor',''),('CEILING','Ceiling',''),('PILLAR','Pillar',''),
            ('DOME_1','Dome 1 (Hemisphere)',''),('DOME_2','Dome 2 (Open Bottom)',''),('STAIRS','Stairs',''),('RAMP','Ramp Generator',''),
            ('WINDOW_CIRCULAR','Window Circular',''),('WINDOW_FLAT','Window Flat',''),
            ('PIPE','Circular Pipe (Straight)',''),('PIPE_L','Circular Pipe (L-Shape)',''),('PIPE_U','Circular Pipe (U-Shape)',''),('PIPE_45','Circular Pipe (45° Curve)',''),
            ('DOOR_FLAT','Door Flat',''),('BALCONY','Balcony',''),
            ('FENCE','Fence',''),('CIRCULAR_FLOOR','Circular Floor',''),('CIRCULAR_CEILING','Circular Ceiling',''),
            ('CIRCULAR_WALL','Circular Wall',''),
            ('MOON','Crescent Moon',''),('STAR','3D Star',''),
            ('CABLE','Procedural Hanging Cable',''),
            ('GTA_STATUE','GTA 5 Base Character Statue',''),
            ('CEILING_FAN','Ceiling Fan (Multi-Part)',''),
            ('TOILET','HiFi Toilet Prop',''),
            ('OFFICE_SINKS','HiFi Office Sinks',''),
            ('OFFICE_SHOWER','HiFi Office Shower',''),
            ('BILLBOARD','HiFi Billboard',''),
            ('NONE','None',''),
        ],
        default='NONE', update=props_update_handler
    )

    fan_show_base: bpy.props.BoolProperty(name="Generate Fan Base", default=True, update=props_update_handler)
    fan_show_blades: bpy.props.BoolProperty(name="Generate Fan Blades", default=True, update=props_update_handler)
    wall_length_ft: bpy.props.FloatProperty(name='Length', default=10.0, update=props_update_handler)
    wall_height_ft: bpy.props.FloatProperty(name='Height', default=1.0, update=props_update_handler)
    wall_thickness_ft: bpy.props.FloatProperty(name='Thickness', default=0.2, update=props_update_handler)
    floor_length_ft: bpy.props.FloatProperty(name='Length', default=10.0, update=props_update_handler)
    floor_width_ft: bpy.props.FloatProperty(name='Width', default=5.0, update=props_update_handler)
    floor_thickness_ft: bpy.props.FloatProperty(name='Thickness', default=0.1, update=props_update_handler)
    ceiling_length_ft: bpy.props.FloatProperty(name='Length', default=10.0, update=props_update_handler)
    ceiling_width_ft: bpy.props.FloatProperty(name='Width', default=5.0, update=props_update_handler)
    ceiling_height_ft: bpy.props.FloatProperty(name='Height', default=3.0, update=props_update_handler)
    ceiling_thickness_ft: bpy.props.FloatProperty(name='Thickness', default=0.1, update=props_update_handler)
    pillar_height_ft: bpy.props.FloatProperty(name='Height', default=2.0, update=props_update_handler)
    pillar_radius_ft: bpy.props.FloatProperty(name='Radius', default=0.2, update=props_update_handler)
    pillar_shape: bpy.props.EnumProperty(name='Shape', items=[('ROUND','Round',''),('SQUARE','Square','')], default='ROUND', update=props_update_handler)
    pillar_resolution: bpy.props.IntProperty(name='Resolution', default=32, min=3, update=props_update_handler)
    dome_1_radius_ft: bpy.props.FloatProperty(name='Radius', default=2.0, update=props_update_handler)
    dome_1_height_ft: bpy.props.FloatProperty(name='Height', default=1.5, update=props_update_handler)
    dome_1_thickness_ft: bpy.props.FloatProperty(name='Thickness', default=0.05, update=props_update_handler)
    dome_1_cut_z_ft: bpy.props.FloatProperty(name='Cut Start Z', default=0.0, update=props_update_handler)
    dome_2_radius_ft: bpy.props.FloatProperty(name='Radius', default=1.5, update=props_update_handler)
    dome_2_height_ft: bpy.props.FloatProperty(name='Height', default=1.5, update=props_update_handler)
    dome_2_thickness_ft: bpy.props.FloatProperty(name='Thickness', default=0.05, update=props_update_handler)
    dome_2_cut_z_ft: bpy.props.FloatProperty(name='Cut Bottom Z', default=0.0, update=props_update_handler)
    dome_segments: bpy.props.IntProperty(name='Segments', default=32, min=3, update=props_update_handler)
    dome_rings: bpy.props.IntProperty(name='Rings', default=16, min=2, update=props_update_handler)
    stairs_steps: bpy.props.IntProperty(name='Steps', default=8, min=1, update=props_update_handler)
    stairs_step_height_ft: bpy.props.FloatProperty(name='Step Height', default=0.15, update=props_update_handler)
    stairs_step_depth_ft: bpy.props.FloatProperty(name='Step Depth', default=0.25, update=props_update_handler)
    stairs_width_ft: bpy.props.FloatProperty(name='Width', default=1.2, update=props_update_handler)
    stairs_tread_thick_ft: bpy.props.FloatProperty(name='Tread Thickness', default=0.0, min=0.0, update=props_update_handler)
    stairs_rail_height_ft: bpy.props.FloatProperty(name='Handrail Height', default=0.9, min=0.0, update=props_update_handler)
    stairs_rail_thick_ft: bpy.props.FloatProperty(name='Handrail Thickness', default=0.05, min=0.0, update=props_update_handler)
    stairs_stick_interval: bpy.props.IntProperty(name='Stick Interval', default=1, min=0, update=props_update_handler)
    ramp_width_ft: bpy.props.FloatProperty(name='Width', default=3.0, update=props_update_handler)
    ramp_length_ft: bpy.props.FloatProperty(name='Length', default=6.0, update=props_update_handler)
    ramp_height_ft: bpy.props.FloatProperty(name='Height', default=2.0, update=props_update_handler)
    win_f_width_ft: bpy.props.FloatProperty(name='Width', default=2.0, update=props_update_handler)
    win_f_height_ft: bpy.props.FloatProperty(name='Height', default=1.5, update=props_update_handler)
    win_f_depth_ft: bpy.props.FloatProperty(name='Depth', default=0.2, update=props_update_handler)
    win_f_frame_thick_ft: bpy.props.FloatProperty(name='Frame Thickness', default=0.1, update=props_update_handler)
    win_f_base_z_ft: bpy.props.FloatProperty(name='Base Z Offset', default=1.0, update=props_update_handler)
    win_c_wall_width_ft: bpy.props.FloatProperty(name='Wall Width', default=3.0, update=props_update_handler)
    win_c_wall_height_ft: bpy.props.FloatProperty(name='Wall Height', default=3.0, update=props_update_handler)
    win_c_wall_depth_ft: bpy.props.FloatProperty(name='Wall Depth', default=0.2, update=props_update_handler)
    win_c_hollow_radius_ft: bpy.props.FloatProperty(name='Hole Radius', default=0.8, update=props_update_handler)
    win_c_hollow_base_z_ft: bpy.props.FloatProperty(name='Hole Base Z', default=1.5, update=props_update_handler)
    win_c_hollow_offset_x_ft: bpy.props.FloatProperty(name='Hole Offset X', default=0.0, update=props_update_handler)
    win_c_resolution: bpy.props.IntProperty(name='Resolution', default=32, min=3, update=props_update_handler)
    pipe_radius_ft: bpy.props.FloatProperty(name='Outer Radius', default=1.0, update=props_update_handler)
    pipe_length_ft: bpy.props.FloatProperty(name='Length', default=5.0, update=props_update_handler)
    pipe_thickness_ft: bpy.props.FloatProperty(name='Wall Thickness', default=0.1, update=props_update_handler)
    pipe_bend_radius_ft: bpy.props.FloatProperty(name='Bend Radius', default=2.0, update=props_update_handler)
    pipe_resolution: bpy.props.IntProperty(name='Resolution', default=32, min=3, update=props_update_handler)
    door_f_width_ft: bpy.props.FloatProperty(name='Width', default=1.5, update=props_update_handler)
    door_f_height_ft: bpy.props.FloatProperty(name='Height', default=2.1, update=props_update_handler)
    door_f_depth_ft: bpy.props.FloatProperty(name='Depth', default=0.2, update=props_update_handler)
    door_f_frame_thick_ft: bpy.props.FloatProperty(name='Frame Thickness', default=0.1, update=props_update_handler)
    bal_width_ft: bpy.props.FloatProperty(name='Width', default=2.0, update=props_update_handler)
    bal_depth_ft: bpy.props.FloatProperty(name='Depth', default=1.0, update=props_update_handler)
    bal_height_ft: bpy.props.FloatProperty(name='Height', default=3.0, update=props_update_handler)
    bal_thickness_ft: bpy.props.FloatProperty(name='Slab Thickness', default=0.1, update=props_update_handler)
    bal_rail_height_ft: bpy.props.FloatProperty(name='Wall Height', default=1.0, update=props_update_handler)
    bal_rail_thick_ft: bpy.props.FloatProperty(name='Wall Thickness', default=0.1, update=props_update_handler)
    bal_rail_back: bpy.props.BoolProperty(name='Include Back Wall', default=False, update=props_update_handler)
    fence_length_ft: bpy.props.FloatProperty(name='Length', default=3.0, update=props_update_handler)
    fence_height_ft: bpy.props.FloatProperty(name='Height', default=1.0, update=props_update_handler)
    fence_posts: bpy.props.IntProperty(name='Posts', default=9, min=2, update=props_update_handler)
    fence_shape: bpy.props.EnumProperty(name='Shape', items=[('ROUND','Round',''),('SQUARE','Square','')], default='SQUARE', update=props_update_handler)
    fence_resolution: bpy.props.IntProperty(name='Resolution', default=16, min=3, update=props_update_handler)
    cfloor_radius_ft: bpy.props.FloatProperty(name='Radius', default=2.0, update=props_update_handler)
    cfloor_thickness_ft: bpy.props.FloatProperty(name='Thickness', default=0.1, update=props_update_handler)
    cfloor_resolution: bpy.props.IntProperty(name='Resolution', default=32, min=3, update=props_update_handler)
    cceiling_radius_ft: bpy.props.FloatProperty(name='Radius', default=2.0, update=props_update_handler)
    cceiling_thickness_ft: bpy.props.FloatProperty(name='Thickness', default=0.1, update=props_update_handler)
    cceiling_height_ft: bpy.props.FloatProperty(name='Height', default=3.0, update=props_update_handler)
    cceiling_resolution: bpy.props.IntProperty(name='Resolution', default=32, min=3, update=props_update_handler)
    cwall_radius_ft: bpy.props.FloatProperty(name='Radius', default=2.0, update=props_update_handler)
    cwall_height_ft: bpy.props.FloatProperty(name='Height', default=2.0, update=props_update_handler)
    cwall_thickness_ft: bpy.props.FloatProperty(name='Thickness', default=0.1, update=props_update_handler)
    cwall_resolution: bpy.props.IntProperty(name='Resolution', default=32, min=3, update=props_update_handler)
    moon_radius_ft: bpy.props.FloatProperty(name='Outer Radius', default=2.0, update=props_update_handler)
    moon_cutter_radius_ft: bpy.props.FloatProperty(name='Inner Radius', default=1.8, update=props_update_handler)
    moon_offset_ft: bpy.props.FloatProperty(name='Crescent Offset', default=0.5, update=props_update_handler)
    moon_thickness_scale: bpy.props.FloatProperty(name='Thickness Scale', default=0.2, update=props_update_handler)
    moon_segments: bpy.props.IntProperty(name='Segments', default=32, min=3, update=props_update_handler)
    moon_rings: bpy.props.IntProperty(name='Rings', default=16, min=3, update=props_update_handler)
    star_points: bpy.props.IntProperty(name='Points', default=5, min=3, max=50, update=props_update_handler)
    star_outer_radius_ft: bpy.props.FloatProperty(name='Outer Radius', default=2.0, update=props_update_handler)
    star_inner_radius_ft: bpy.props.FloatProperty(name='Inner Radius', default=0.8, update=props_update_handler)
    star_depth_ft: bpy.props.FloatProperty(name='Depth', default=0.5, update=props_update_handler)
    cable_length_ft: bpy.props.FloatProperty(name='Length', default=10.0, update=props_update_handler)
    cable_droop_ft: bpy.props.FloatProperty(name='Droop', default=2.0, update=props_update_handler)
    cable_thickness_ft: bpy.props.FloatProperty(name='Thickness', default=0.05, update=props_update_handler)
    cable_resolution: bpy.props.IntProperty(name='Resolution', default=32, min=4, update=props_update_handler)
