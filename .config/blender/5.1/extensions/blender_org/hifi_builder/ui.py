import bpy

class HIFI_PT_main(bpy.types.Panel):
    bl_label = "HiFi Engine v4.5.8"
    bl_idname = "HIFI_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HiFi Builder'
    bl_order = 0
    
    def draw(self, context):
        props = context.scene.hifi_props
        layout = self.layout
        
        box = layout.box()
        box.label(text="Global Environment Setup", icon='WORLD')
        row = box.row(align=True)
        row.label(text="Unit Settings:", icon='PREFERENCES')
        row.prop(props, "unit_type", text="")
        
        sollumz_installed = any("sollumz" in k.lower() for k in context.preferences.addons.keys())
        box = layout.box()
        box.label(text="GTA V Integration", icon='MOD_ARMATURE')
        row = box.row()
        row.enabled = sollumz_installed
        row.prop(props, "use_sollumz", text="Enable Sollumz Output")

class HIFI_PT_generator(bpy.types.Panel):
    bl_label = "Mesh Generator"
    bl_idname = "HIFI_PT_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HiFi Builder'
    bl_order = 1
    
    def draw(self, context):
        props = context.scene.hifi_props
        layout = self.layout
        
        box = layout.box()
        box.label(text="Select Prop to Generate:", icon='MESH_DATA')
        box.prop(props, "generator_type", text="")
        
        if props.generator_type != 'NONE':
            param_box = layout.box()
            param_box.label(text="Generation Parameters:", icon='TOOL_SETTINGS')
            col = param_box.column(align=True)
            g = props.generator_type
            def d(pname): col.prop(props, pname)
            
            if g == 'WALL':
                d("wall_length_ft"); d("wall_height_ft"); d("wall_thickness_ft")
            elif g == 'FLOOR':
                d("floor_length_ft"); d("floor_width_ft"); d("floor_thickness_ft")
            elif g == 'CEILING':
                d("ceiling_length_ft"); d("ceiling_width_ft"); d("ceiling_height_ft"); d("ceiling_thickness_ft")
            elif g == 'PILLAR':
                d("pillar_height_ft"); d("pillar_radius_ft"); d("pillar_shape")
                if props.pillar_shape == 'ROUND': d("pillar_resolution")
            elif g == 'DOME_1':
                d("dome_1_radius_ft"); d("dome_1_height_ft"); d("dome_1_thickness_ft"); d("dome_1_cut_z_ft")
                d("dome_segments"); d("dome_rings")
            elif g == 'DOME_2':
                d("dome_2_radius_ft"); d("dome_2_height_ft"); d("dome_2_thickness_ft"); d("dome_2_cut_z_ft")
                d("dome_segments"); d("dome_rings")
            elif g == 'STAIRS':
                d("stairs_steps"); d("stairs_step_height_ft"); d("stairs_step_depth_ft"); d("stairs_width_ft")
                d("stairs_tread_thick_ft"); d("stairs_rail_height_ft"); d("stairs_rail_thick_ft"); d("stairs_stick_interval")
            elif g == 'RAMP':
                d("ramp_width_ft"); d("ramp_length_ft"); d("ramp_height_ft")
            elif g == 'WINDOW_FLAT':
                d("win_f_width_ft"); d("win_f_height_ft"); d("win_f_depth_ft"); d("win_f_frame_thick_ft"); d("win_f_base_z_ft")
            elif g == 'WINDOW_CIRCULAR':
                d("win_c_wall_width_ft"); d("win_c_wall_height_ft"); d("win_c_wall_depth_ft")
                d("win_c_hollow_radius_ft"); d("win_c_hollow_base_z_ft"); d("win_c_hollow_offset_x_ft"); d("win_c_resolution")
            elif g == 'PIPE':
                d("pipe_radius_ft"); d("pipe_length_ft"); d("pipe_thickness_ft"); d("pipe_resolution")
            elif g in ['PIPE_L', 'PIPE_U', 'PIPE_45']:
                d("pipe_bend_radius_ft"); d("pipe_radius_ft"); d("pipe_thickness_ft"); d("pipe_resolution")
            elif g == 'DOOR_FLAT':
                d("door_f_width_ft"); d("door_f_height_ft"); d("door_f_depth_ft"); d("door_f_frame_thick_ft")
            elif g == 'BALCONY':
                d("bal_width_ft"); d("bal_depth_ft"); d("bal_height_ft"); d("bal_thickness_ft")
                d("bal_rail_height_ft"); d("bal_rail_thick_ft"); d("bal_rail_back")
            elif g == 'FENCE':
                d("fence_length_ft"); d("fence_height_ft"); d("fence_posts"); d("fence_shape")
                if props.fence_shape == 'ROUND': d("fence_resolution")
            elif g == 'CIRCULAR_FLOOR':
                d("cfloor_radius_ft"); d("cfloor_thickness_ft"); d("cfloor_resolution")
            elif g == 'CIRCULAR_CEILING':
                d("cceiling_radius_ft"); d("cceiling_thickness_ft"); d("cceiling_height_ft"); d("cceiling_resolution")
            elif g == 'CIRCULAR_WALL':
                d("cwall_radius_ft"); d("cwall_height_ft"); d("cwall_thickness_ft"); d("cwall_resolution")
            elif g == 'MOON':
                d("moon_radius_ft"); d("moon_cutter_radius_ft"); d("moon_offset_ft")
                d("moon_thickness_scale"); d("moon_segments"); d("moon_rings")
            elif g == 'STAR':
                d("star_points"); d("star_outer_radius_ft"); d("star_inner_radius_ft"); d("star_depth_ft")
            elif g == 'CABLE':
                d("cable_length_ft"); d("cable_droop_ft"); d("cable_thickness_ft"); d("cable_resolution")
            elif g == 'CEILING_FAN':
                d("fan_show_base"); d("fan_show_blades")
            elif g in ['GTA_STATUE', 'TOILET', 'OFFICE_SINKS', 'OFFICE_SHOWER', 'BILLBOARD']:
                col.label(text="Global transforms apply directly to this prop.", icon='INFO')

        layout.separator()
        row = layout.row(align=True)
        row.operator("hifi.clear_previews", text="Clear Preview", icon="TRASH")
        row.operator("hifi.generate", text="Generate Mesh", icon="OBJECT_DATA")

class HIFI_PT_transform(bpy.types.Panel):
    bl_label = "Global Transform"
    bl_idname = "HIFI_PT_transform"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HiFi Builder'
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        preview_obj = None
        for obj in context.scene.objects:
            if obj.name.startswith("hifi_prev_"):
                preview_obj = obj
                break
                
        if preview_obj:
            box = layout.box()
            box.label(text="Live Generation Placement:", icon='EMPTY_ARROWS')
            col = box.column(align=True)
            
            col.label(text="Location:", icon='CON_LOCLIKE')
            r = col.row(align=True); r.prop(preview_obj, "location", index=0, text="X"); r.prop(preview_obj, "location", index=1, text="Y"); r.prop(preview_obj, "location", index=2, text="Z")
            
            col.label(text="Rotation (Degrees):", icon='CON_ROTLIKE')
            r = col.row(align=True); r.prop(preview_obj, "rotation_euler", index=0, text="X"); r.prop(preview_obj, "rotation_euler", index=1, text="Y"); r.prop(preview_obj, "rotation_euler", index=2, text="Z")
            
            col.label(text="Scale:", icon='CON_SIZELIKE')
            r = col.row(align=True); r.prop(preview_obj, "scale", index=0, text="X"); r.prop(preview_obj, "scale", index=1, text="Y"); r.prop(preview_obj, "scale", index=2, text="Z")
        else:
            layout.label(text="Select a prop in Mesh Generator to access live Transforms", icon='INFO')

class HIFI_PT_utils(bpy.types.Panel):
    bl_label = "Auto Create Animation GTA 5   🎬"
    bl_idname = "HIFI_PT_utils"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HiFi Builder'
    bl_order = 3
    
    def draw(self, context):
        props = context.scene.hifi_props
        layout = self.layout
        
        box = layout.box()
        box.label(text="Animation Settings:", icon='ANIM_DATA')
        box.prop(props, "anim_frames", text="Total Frames")
        
        row = box.row(align=True)
        row.prop(props, "anim_axis", expand=True)
        box.prop(props, "anim_reverse", text="Reverse Spin", icon='FILE_REFRESH')
        
        box.separator()
        box.label(text="3 Clicks Export Ready Process:", icon='EXPORT')
        box.operator("hifi.anim_step1_rig", text="Step 1: Rig & Animate Mesh", icon='PLAY')
        box.operator("hifi.anim_step2_clipdict", text="Step 2: Create Clip Dictionary", icon='RENDER_ANIMATION')
        box.operator("hifi.anim_step3_ytyp", text="Step 3: Create YTYP Archetype", icon='FILE_3D')
        
        layout.separator()
        tool_box = layout.box()
        tool_box.label(text="Export Utilities:", icon='TOOL_SETTINGS')
        tool_box.operator("hifi.game_export", text="Prepare For Export", icon='TRANSFORM_ORIGINS')
        row = tool_box.row(align=True)
        row.operator("hifi.join_cleanup", text="Join Selected", icon="AUTOMERGE_ON")
        row.operator("hifi.cleanup_orphans", text="Clean Memory", icon="BRUSH_DATA")

class HIFI_PT_inspector(bpy.types.Panel):
    bl_label = "Object Inspector"
    bl_idname = "HIFI_PT_inspector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HiFi Builder'
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        sel_props = context.scene.hifi_sel_props
        layout = self.layout
        obj = context.active_object
        
        if obj:
            box = layout.box()
            box.label(text=f"Target: {obj.name}", icon='VIEWZOOM')
            
            row = box.row(align=True)
            row.operator("hifi.load_selected_params", text="Load", icon='IMPORT')
            row.operator("hifi.apply_transform_to_selected", text="Apply", icon='EXPORT')
            row.operator("hifi.copy_transform", text="Copy To Clipboard", icon='COPYDOWN')
            
            box.separator()
            box.label(text="Live Location:", icon='CON_LOCLIKE')
            col = box.column(align=True)
            r = col.row(align=True); r.prop(obj, "lock_location", index=0, text=""); r.prop(obj, "location", index=0, text="X")
            r = col.row(align=True); r.prop(obj, "lock_location", index=1, text=""); r.prop(obj, "location", index=1, text="Y")
            r = col.row(align=True); r.prop(obj, "lock_location", index=2, text=""); r.prop(obj, "location", index=2, text="Z")
            
            box.label(text="Live Rotation:", icon='CON_ROTLIKE')
            col = box.column(align=True)
            r = col.row(align=True); r.prop(obj, "lock_rotation", index=0, text=""); r.prop(obj, "rotation_euler", index=0, text="X")
            r = col.row(align=True); r.prop(obj, "lock_rotation", index=1, text=""); r.prop(obj, "rotation_euler", index=1, text="Y")
            r = col.row(align=True); r.prop(obj, "lock_rotation", index=2, text=""); r.prop(obj, "rotation_euler", index=2, text="Z")
            
            box.label(text="Live Scale:", icon='CON_SIZELIKE')
            col = box.column(align=True)
            r = col.row(align=True); r.prop(obj, "lock_scale", index=0, text=""); r.prop(obj, "scale", index=0, text="X")
            r = col.row(align=True); r.prop(obj, "lock_scale", index=1, text=""); r.prop(obj, "scale", index=1, text="Y")
            r = col.row(align=True); r.prop(obj, "lock_scale", index=2, text=""); r.prop(obj, "scale", index=2, text="Z")
        else:
            layout.label(text="Select an object to inspect.", icon='INFO')
