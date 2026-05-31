import bpy, math
from .utils import PREVIEW_PREFIX, to_internal, apply_transform, apply_boolean, cleanup_previews

def gen_circular_wall(props, sc):
    cleanup_previews()
    R = to_internal(props.cwall_radius_ft, sc)
    H = to_internal(props.cwall_height_ft, sc)
    T = to_internal(props.cwall_thickness_ft, sc)
    res = props.cwall_resolution
    
    outer_r = max(R + T/2.0, 0.001)
    inner_r = max(R - T/2.0, 0.001)

    bpy.ops.mesh.primitive_cylinder_add(radius=outer_r, depth=H, vertices=res, location=(0, 0, H/2.0))
    outer = bpy.context.active_object
    outer.name = PREVIEW_PREFIX + "CIRCULAR_WALL_OUTER"
    apply_transform(outer)

    bpy.ops.mesh.primitive_cylinder_add(radius=inner_r, depth=H + 0.02, vertices=res, location=(0, 0, H/2.0))
    inner = bpy.context.active_object
    inner.name = PREVIEW_PREFIX + "CIRCULAR_WALL_INNER"
    apply_transform(inner)

    apply_boolean(outer, inner, 'DIFFERENCE')
    try:
        bpy.data.objects.remove(inner, do_unlink=True)
    except:
        pass

    outer.name = PREVIEW_PREFIX + "CIRCULAR_WALL"
    apply_transform(outer)
    params = {"type":"CIRCULAR_WALL", "radius":props.cwall_radius_ft, "unit":props.unit_type}
    return outer, params

def gen_moon(props, sc):
    cleanup_previews()
    r_out = to_internal(props.moon_radius_ft, sc)
    r_in = to_internal(props.moon_cutter_radius_ft, sc)
    offset = to_internal(props.moon_offset_ft, sc)
    thick = props.moon_thickness_scale
    segs = props.moon_segments
    rings = props.moon_rings
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r_out, segments=segs, ring_count=rings, location=(0,0,r_out))
    moon = bpy.context.active_object
    moon.scale[1] = thick
    apply_transform(moon)
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r_in, segments=segs, ring_count=rings, location=(offset, 0, r_out))
    cutter = bpy.context.active_object
    cutter.scale[1] = thick * 1.5 
    apply_transform(cutter)
    
    apply_boolean(moon, cutter, 'DIFFERENCE')
    try:
        bpy.data.objects.remove(cutter, do_unlink=True)
    except:
        pass
    
    moon.name = PREVIEW_PREFIX + "MOON"
    params = {"type":"MOON", "radius":props.moon_radius_ft, "unit":props.unit_type}
    return moon, params

def gen_star(props, sc):
    cleanup_previews()
    points = props.star_points
    r_out = to_internal(props.star_outer_radius_ft, sc)
    r_in = to_internal(props.star_inner_radius_ft, sc)
    depth = to_internal(props.star_depth_ft, sc)
    
    verts = []
    faces = []
    
    z_top = depth / 2.0
    z_bot = -depth / 2.0
    verts.append((0, 0, z_top)) 
    verts.append((0, 0, z_bot)) 
    
    angle_step = math.pi / points
    for i in range(points * 2):
        angle = i * angle_step + (math.pi / 2) 
        r = r_out if i % 2 == 0 else r_in
        verts.append((r * math.cos(angle), r * math.sin(angle), 0))
    
    for i in range(points * 2):
        v_curr = 2 + i
        v_next = 2 + ((i + 1) % (points * 2))
        faces.append((0, v_curr, v_next))
        faces.append((1, v_next, v_curr))
        
    mesh = bpy.data.meshes.new(PREVIEW_PREFIX + "STAR_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    obj = bpy.data.objects.new(PREVIEW_PREFIX + "STAR", mesh)
    bpy.context.collection.objects.link(obj)
    
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    obj.rotation_euler.x = math.radians(90)
    obj.location.z = r_out
    apply_transform(obj)
    
    params = {"type":"STAR", "points":props.star_points, "unit":props.unit_type}
    return obj, params
