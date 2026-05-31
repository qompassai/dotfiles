import bpy, math
from .utils import PREVIEW_PREFIX, to_internal, apply_transform, apply_boolean, cleanup_previews

def gen_door_frame_flat(props, sc):
    cleanup_previews()
    w = to_internal(props.door_f_width_ft, sc)
    h = to_internal(props.door_f_height_ft, sc)
    depth = to_internal(props.door_f_depth_ft, sc)
    frame_thick = to_internal(props.door_f_frame_thick_ft, sc)
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, h/2.0))
    frame = bpy.context.active_object
    frame.scale = (w, depth, h)
    apply_transform(frame)
    
    cut_w = max(w - (2 * frame_thick), 0.001)
    cut_h = max(h - frame_thick, 0.001)
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, (cut_h + 0.5)/2.0 - 0.5))
    cutter = bpy.context.active_object
    cutter.scale = (cut_w, depth + 2.0, cut_h + 0.5)
    apply_transform(cutter)
    
    apply_boolean(frame, cutter, 'DIFFERENCE')
    try:
        bpy.data.objects.remove(cutter, do_unlink=True)
    except:
        pass
    
    frame.name = PREVIEW_PREFIX + "DOOR_FLAT"
    params = {"type":"DOOR_FLAT", "width": props.door_f_width_ft, "height": props.door_f_height_ft, "frame_thick": props.door_f_frame_thick_ft, "unit":props.unit_type}
    return frame, params

def gen_balcony(props, sc):
    cleanup_previews()
    w = to_internal(props.bal_width_ft, sc)
    d = to_internal(props.bal_depth_ft, sc)
    h = to_internal(props.bal_height_ft, sc)
    thick = to_internal(props.bal_thickness_ft, sc)
    rail_h = to_internal(props.bal_rail_height_ft, sc)
    rail_t = to_internal(props.bal_rail_thick_ft, sc)
    back_wall = props.bal_rail_back
    
    objs = []
    bpy.ops.mesh.primitive_cube_add(size=1, location=(d/2.0, 0, h + thick/2.0))
    slab = bpy.context.active_object
    slab.scale = (d, w, thick)
    apply_transform(slab)
    slab.name = PREVIEW_PREFIX + "BALCONY_SLAB"
    objs.append(slab)
    
    if rail_h > 0.001:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(d - rail_t/2.0, 0, h + thick + rail_h/2.0))
        f_rail = bpy.context.active_object
        f_rail.scale = (rail_t, w, rail_h)
        apply_transform(f_rail)
        f_rail.name = PREVIEW_PREFIX + "BALCONY_RAIL_F"
        objs.append(f_rail)
        
        bpy.ops.mesh.primitive_cube_add(size=1, location=(d/2.0, -w/2.0 + rail_t/2.0, h + thick + rail_h/2.0))
        l_rail = bpy.context.active_object
        l_rail.scale = (d, rail_t, rail_h)
        apply_transform(l_rail)
        l_rail.name = PREVIEW_PREFIX + "BALCONY_RAIL_L"
        objs.append(l_rail)
        
        bpy.ops.mesh.primitive_cube_add(size=1, location=(d/2.0, w/2.0 - rail_t/2.0, h + thick + rail_h/2.0))
        r_rail = bpy.context.active_object
        r_rail.scale = (d, rail_t, rail_h)
        apply_transform(r_rail)
        r_rail.name = PREVIEW_PREFIX + "BALCONY_RAIL_R"
        objs.append(r_rail)
        
        if back_wall:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(rail_t/2.0, 0, h + thick + rail_h/2.0))
            b_rail = bpy.context.active_object
            b_rail.scale = (rail_t, w, rail_h)
            apply_transform(b_rail)
            b_rail.name = PREVIEW_PREFIX + "BALCONY_RAIL_B"
            objs.append(b_rail)
            
    params = {"type":"BALCONY", "width":props.bal_width_ft, "unit":props.unit_type}
    return objs, params

def gen_fence(props, sc):
    cleanup_previews()
    length = to_internal(props.fence_length_ft, sc)
    height = to_internal(props.fence_height_ft, sc)
    posts = props.fence_posts
    shape = props.fence_shape
    res = props.fence_resolution
    spacing = length / max(posts-1,1)
    
    objs = []
    post_thick = to_internal(0.3, sc)
    if props.unit_type == 'METERS': post_thick = 0.1
    
    for i in range(posts):
        px = i * spacing
        if shape == 'ROUND':
            bpy.ops.mesh.primitive_cylinder_add(radius=post_thick/2, depth=height, vertices=res, location=(px, 0, height/2.0))
            p = bpy.context.active_object
        else:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(px, 0, height/2.0))
            p = bpy.context.active_object
            p.scale = (post_thick, post_thick, height)
            apply_transform(p)
            
        p.name = PREVIEW_PREFIX + f"FENCE_POST_{i}"
        if shape == 'ROUND':
            apply_transform(p)
        objs.append(p)
        
    params = {"type":"FENCE", "length":props.fence_length_ft, "unit":props.unit_type}
    return objs, params

def gen_circular_floor(props, sc):
    cleanup_previews()
    R = to_internal(props.cfloor_radius_ft, sc)
    thickness = to_internal(props.cfloor_thickness_ft, sc)
    res = props.cfloor_resolution
    
    bpy.ops.mesh.primitive_cylinder_add(radius=R, depth=thickness, vertices=res, location=(0,0,thickness/2.0))
    o = bpy.context.active_object
    o.name = PREVIEW_PREFIX + "CIRCULAR_FLOOR"
    apply_transform(o)
    params = {"type":"CIRCULAR_FLOOR", "radius":props.cfloor_radius_ft, "unit":props.unit_type}
    return o, params

def gen_circular_ceiling(props, sc):
    cleanup_previews()
    R = to_internal(props.cceiling_radius_ft, sc)
    thickness = to_internal(props.cceiling_thickness_ft, sc)
    h = to_internal(props.cceiling_height_ft, sc)
    res = props.cceiling_resolution
    
    bpy.ops.mesh.primitive_cylinder_add(radius=R, depth=thickness, vertices=res, location=(0,0, h + thickness/2.0))
    o = bpy.context.active_object
    o.name = PREVIEW_PREFIX + "CIRCULAR_CEILING"
    apply_transform(o)
    params = {"type":"CIRCULAR_CEILING", "radius":props.cceiling_radius_ft, "unit":props.unit_type}
    return o, params
