import bpy, math
from .utils import PREVIEW_PREFIX, to_internal, apply_transform, apply_boolean, cleanup_previews

def gen_wall(props, sc):
    cleanup_previews()
    length = to_internal(props.wall_length_ft, sc)
    height = to_internal(props.wall_height_ft, sc)
    thickness = to_internal(props.wall_thickness_ft, sc)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, height/2.0))
    obj = bpy.context.active_object
    obj.name = PREVIEW_PREFIX + "WALL"
    obj.scale = (length, thickness, height)
    apply_transform(obj)
    params = {"type":"WALL", "length":props.wall_length_ft, "height":props.wall_height_ft, "thickness":props.wall_thickness_ft, "unit":props.unit_type}
    return obj, params

def gen_floor(props, sc):
    cleanup_previews()
    lx = to_internal(props.floor_length_ft, sc)
    ly = to_internal(props.floor_width_ft, sc)
    thickness = to_internal(props.floor_thickness_ft, sc)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, thickness/2.0))
    obj = bpy.context.active_object
    obj.name = PREVIEW_PREFIX + "FLOOR"
    obj.scale = (lx, ly, thickness)
    apply_transform(obj)
    params = {"type":"FLOOR", "length":props.floor_length_ft, "width":props.floor_width_ft, "thickness":props.floor_thickness_ft, "unit":props.unit_type}
    return obj, params

def gen_ceiling(props, sc):
    cleanup_previews()
    lx = to_internal(props.ceiling_length_ft, sc)
    ly = to_internal(props.ceiling_width_ft, sc)
    thickness = to_internal(props.ceiling_thickness_ft, sc)
    h = to_internal(props.ceiling_height_ft, sc)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, h + thickness/2.0))
    obj = bpy.context.active_object
    obj.name = PREVIEW_PREFIX + "CEILING"
    obj.scale = (lx, ly, thickness)
    apply_transform(obj)
    params = {"type":"CEILING", "length":props.ceiling_length_ft, "width":props.ceiling_width_ft, "thickness":props.ceiling_thickness_ft, "height":props.ceiling_height_ft, "unit":props.unit_type}
    return obj, params

def gen_pillar(props, sc):
    cleanup_previews()
    h = to_internal(props.pillar_height_ft, sc)
    r = to_internal(props.pillar_radius_ft, sc)
    res = props.pillar_resolution
    if props.pillar_shape == 'ROUND':
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=res, location=(0, 0, h/2.0))
        obj = bpy.context.active_object
    else:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, h/2.0))
        obj = bpy.context.active_object
        obj.scale = (r*2, r*2, h)
        apply_transform(obj)
    obj.name = PREVIEW_PREFIX + "PILLAR"
    if props.pillar_shape == 'ROUND':
        apply_transform(obj)
    params = {"type":"PILLAR", "height":props.pillar_height_ft, "radius":props.pillar_radius_ft, "shape":props.pillar_shape, "resolution":props.pillar_resolution, "unit":props.unit_type}
    return obj, params

def gen_dome_1_shell(props, sc):
    cleanup_previews()
    radius = to_internal(props.dome_1_radius_ft, sc)
    thickness = to_internal(props.dome_1_thickness_ft, sc)
    target_h = to_internal(props.dome_1_height_ft, sc)
    cut_z = to_internal(props.dome_1_cut_z_ft, sc)
    z_scale = target_h / max(radius, 0.001)
    inner_r = max(radius - thickness, radius * 0.01)
    segs = props.dome_segments
    rings = props.dome_rings

    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=segs, ring_count=rings, location=(0,0,0))
    outer = bpy.context.active_object
    outer.name = PREVIEW_PREFIX + "DOME_1_OUTER"
    outer.scale[2] = z_scale
    apply_transform(outer)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=inner_r, segments=segs, ring_count=rings, location=(0,0,0))
    inner = bpy.context.active_object
    inner.name = PREVIEW_PREFIX + "DOME_1_INNER"
    inner.scale[2] = z_scale * (inner_r / max(radius, 0.001))
    apply_transform(inner)
    
    apply_boolean(outer, inner, 'DIFFERENCE')
    try:
        bpy.data.objects.remove(inner, do_unlink=True)
    except:
        pass

    cutter_size = radius * 3.0
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0, -cutter_size/2.0 + cut_z)) 
    cutter = bpy.context.active_object
    cutter.scale = (cutter_size, cutter_size, cutter_size)
    apply_transform(cutter)
    
    apply_boolean(outer, cutter, 'DIFFERENCE')
    try:
        bpy.data.objects.remove(cutter, do_unlink=True)
    except:
        pass

    outer.name = PREVIEW_PREFIX + "DOME_1"
    apply_transform(outer)
    params = {"type":"DOME_1", "radius":props.dome_1_radius_ft, "height":props.dome_1_height_ft, "thickness":props.dome_1_thickness_ft, "cut_z":props.dome_1_cut_z_ft, "unit":props.unit_type}
    return outer, params
