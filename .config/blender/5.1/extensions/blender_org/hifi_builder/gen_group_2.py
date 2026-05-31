import bpy, math
from .utils import PREVIEW_PREFIX, to_internal, apply_transform, apply_boolean, cleanup_previews

def gen_dome_2_shell(props, sc):
    cleanup_previews()
    radius = to_internal(props.dome_2_radius_ft, sc)
    thickness = to_internal(props.dome_2_thickness_ft, sc)
    target_h = to_internal(props.dome_2_height_ft, sc)
    cut_z = to_internal(props.dome_2_cut_z_ft, sc) 
    z_scale = target_h / max(radius, 0.001)
    inner_r = max(radius - thickness, 0.001)
    segs = props.dome_segments
    rings = props.dome_rings

    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=segs, ring_count=rings, location=(0,0,0))
    outer = bpy.context.active_object
    outer.scale[2] = z_scale
    apply_transform(outer)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=inner_r, segments=segs, ring_count=rings, location=(0,0,0))
    inner = bpy.context.active_object
    inner.scale[2] = z_scale
    apply_transform(inner)
    
    apply_boolean(outer, inner, 'DIFFERENCE')
    try:
        bpy.data.objects.remove(inner, do_unlink=True)
    except:
        pass

    cutter_size = radius * 4.0
    cutter_h = radius * 2.0
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0, cut_z - (cutter_h/2.0)))
    cutter = bpy.context.active_object
    cutter.scale = (cutter_size, cutter_size, cutter_h)
    apply_transform(cutter)
    
    apply_boolean(outer, cutter, 'DIFFERENCE')
    try:
        bpy.data.objects.remove(cutter, do_unlink=True)
    except:
        pass

    outer.name = PREVIEW_PREFIX + "DOME_2"
    params = {"type":"DOME_2", "radius":props.dome_2_radius_ft, "height":props.dome_2_height_ft, "thickness":props.dome_2_thickness_ft, "cut_z":props.dome_2_cut_z_ft, "unit":props.unit_type}
    return outer, params

def gen_stairs(props, sc):
    cleanup_previews()
    steps = props.stairs_steps
    step_h = to_internal(props.stairs_step_height_ft, sc)
    step_d = to_internal(props.stairs_step_depth_ft, sc)
    width = to_internal(props.stairs_width_ft, sc)
    t_thick = to_internal(props.stairs_tread_thick_ft, sc)
    
    rail_h = to_internal(props.stairs_rail_height_ft, sc)
    rail_t = to_internal(props.stairs_rail_thick_ft, sc)
    interval = props.stairs_stick_interval
    
    objs = []
    for i in range(steps):
        hx = (step_d * i) + step_d/2.0
        if t_thick > 0.001:
            hz = (step_h * i) + step_h - (t_thick/2.0)
            bpy.ops.mesh.primitive_cube_add(size=1, location=(hx, 0, hz))
            o = bpy.context.active_object
            o.scale = (step_d, width, t_thick)
        else:
            hz = (step_h * i) + step_h/2.0
            bpy.ops.mesh.primitive_cube_add(size=1, location=(hx, 0, hz))
            o = bpy.context.active_object
            o.scale = (step_d, width, step_h)
        apply_transform(o)
        o.name = PREVIEW_PREFIX + f"STAIR_{i}"
        objs.append(o)
        
    if rail_h > 0.001:
        run = steps * step_d
        rise = steps * step_h
        length = math.sqrt(run**2 + rise**2)
        angle = math.atan2(rise, run)
        cx = run / 2.0
        cz = (rise / 2.0) + rail_h
        
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, -width/2.0 + rail_t/2.0, cz))
        l_rail = bpy.context.active_object
        l_rail.scale = (length, rail_t, rail_t)
        l_rail.rotation_euler.y = -angle
        apply_transform(l_rail)
        l_rail.name = PREVIEW_PREFIX + "STAIR_RAIL_L"
        objs.append(l_rail)
        
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, width/2.0 - rail_t/2.0, cz))
        r_rail = bpy.context.active_object
        r_rail.scale = (length, rail_t, rail_t)
        r_rail.rotation_euler.y = -angle
        apply_transform(r_rail)
        r_rail.name = PREVIEW_PREFIX + "STAIR_RAIL_R"
        objs.append(r_rail)

        if interval > 0:
            for i in range(steps):
                if i % interval == 0:
                    hx = (step_d * i) + step_d/2.0
                    step_top_z = (step_h * i) + step_h
                    stick_z = step_top_z + (rail_h / 2.0)
                    
                    bpy.ops.mesh.primitive_cube_add(size=1, location=(hx, -width/2.0 + rail_t/2.0, stick_z))
                    ls = bpy.context.active_object
                    ls.scale = (rail_t, rail_t, rail_h)
                    apply_transform(ls)
                    ls.name = PREVIEW_PREFIX + f"STICK_L_{i}"
                    objs.append(ls)
                    
                    bpy.ops.mesh.primitive_cube_add(size=1, location=(hx, width/2.0 - rail_t/2.0, stick_z))
                    rs = bpy.context.active_object
                    rs.scale = (rail_t, rail_t, rail_h)
                    apply_transform(rs)
                    rs.name = PREVIEW_PREFIX + f"STICK_R_{i}"
                    objs.append(rs)

    params = {"type":"STAIRS", "steps":props.stairs_steps, "step_h":props.stairs_step_height_ft, "step_d":props.stairs_step_depth_ft, "width":props.stairs_width_ft, "unit":props.unit_type}
    return objs, params

def gen_ramp(props, sc):
    cleanup_previews()
    w = to_internal(props.ramp_width_ft, sc)
    l = to_internal(props.ramp_length_ft, sc)
    h = to_internal(props.ramp_height_ft, sc)
    
    verts = [
        (0, -w/2.0, 0),
        (0, w/2.0, 0),
        (l, -w/2.0, 0),
        (l, w/2.0, 0),
        (l, -w/2.0, h),
        (l, w/2.0, h)
    ]
    faces = [
        (0, 1, 3, 2),
        (2, 3, 5, 4),
        (0, 2, 4),
        (1, 5, 3),
        (0, 1, 5, 4)
    ]
    
    mesh = bpy.data.meshes.new(PREVIEW_PREFIX + "RAMP_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    obj = bpy.data.objects.new(PREVIEW_PREFIX + "RAMP", mesh)
    bpy.context.collection.objects.link(obj)
    
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    apply_transform(obj)
    
    params = {"type":"RAMP", "width":props.ramp_width_ft, "length":props.ramp_length_ft, "height":props.ramp_height_ft, "unit":props.unit_type}
    return obj, params

def gen_window_frame_flat(props, sc):
    cleanup_previews()
    w = to_internal(props.win_f_width_ft, sc)
    h = to_internal(props.win_f_height_ft, sc)
    depth = to_internal(props.win_f_depth_ft, sc)
    frame_thick = to_internal(props.win_f_frame_thick_ft, sc)
    base_z = to_internal(props.win_f_base_z_ft, sc)
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, base_z + h/2.0))
    frame = bpy.context.active_object
    frame.scale = (w, depth, h)
    apply_transform(frame)
    
    cut_w = max(w - (2 * frame_thick), 0.001)
    cut_h = max(h - (2 * frame_thick), 0.001)
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, base_z + h/2.0))
    cutter = bpy.context.active_object
    cutter.scale = (cut_w, depth + 2.0, cut_h)
    apply_transform(cutter)
    
    apply_boolean(frame, cutter, 'DIFFERENCE')
    try:
        bpy.data.objects.remove(cutter, do_unlink=True)
    except:
        pass
    
    frame.name = PREVIEW_PREFIX + "WINDOW_FLAT"
    params = {"type":"WINDOW_FLAT", "width": props.win_f_width_ft, "height": props.win_f_height_ft, "depth": props.win_f_depth_ft, "frame_thick": props.win_f_frame_thick_ft, "base_z":props.win_f_base_z_ft, "unit":props.unit_type}
    return frame, params

def gen_window_frame_circular(props, sc):
    cleanup_previews()
    w = to_internal(props.win_c_wall_width_ft, sc)
    h = to_internal(props.win_c_wall_height_ft, sc)
    depth = to_internal(props.win_c_wall_depth_ft, sc)
    res = props.win_c_resolution
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, h/2.0))
    frame = bpy.context.active_object
    frame.name = PREVIEW_PREFIX + "WINDOW_CIRCULAR"
    frame.scale = (w, depth, h)
    apply_transform(frame)

    hr = to_internal(props.win_c_hollow_radius_ft, sc)
    base_z = to_internal(props.win_c_hollow_base_z_ft, sc)
    offset_x = to_internal(props.win_c_hollow_offset_x_ft, sc)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=hr, depth=depth + 2.0, vertices=res, location=(offset_x, 0, base_z))
    cutter = bpy.context.active_object
    cutter.rotation_euler.x = math.radians(90)
    apply_transform(cutter)

    apply_boolean(frame, cutter, 'DIFFERENCE')
    try:
        bpy.data.objects.remove(cutter, do_unlink=True)
    except:
        pass

    params = {"type":"WINDOW_CIRCULAR", "wall_w":props.win_c_wall_width_ft, "wall_h":props.win_c_wall_height_ft, "hole_r":props.win_c_hollow_radius_ft, "unit":props.unit_type}
    return frame, params
