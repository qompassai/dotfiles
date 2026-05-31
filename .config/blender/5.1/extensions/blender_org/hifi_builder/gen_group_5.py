import bpy, math
from .utils import PREVIEW_PREFIX, to_internal, apply_transform, apply_boolean, cleanup_previews

def gen_pipe(props, sc):
    cleanup_previews()
    R = to_internal(props.pipe_radius_ft, sc)
    L = to_internal(props.pipe_length_ft, sc)
    T = to_internal(props.pipe_thickness_ft, sc)
    res = props.pipe_resolution
    
    outer_r = max(R, 0.001)
    inner_r = max(R - T, 0.001)

    bpy.ops.mesh.primitive_cylinder_add(radius=outer_r, depth=L, vertices=res, location=(0, 0, 0))
    pipe = bpy.context.active_object
    pipe.rotation_euler.y = math.radians(90)
    apply_transform(pipe)
    pipe.location.x = L / 2.0
    pipe.location.z = outer_r
    apply_transform(pipe)

    if T > 0 and inner_r > 0:
        bpy.ops.mesh.primitive_cylinder_add(radius=inner_r, depth=L + 2.0, vertices=res, location=(0, 0, 0))
        cutter = bpy.context.active_object
        cutter.rotation_euler.y = math.radians(90)
        apply_transform(cutter)
        cutter.location.x = L / 2.0
        cutter.location.z = outer_r
        apply_transform(cutter)
        
        apply_boolean(pipe, cutter, 'DIFFERENCE')
        try:
            bpy.data.objects.remove(cutter, do_unlink=True)
        except:
            pass

    pipe.name = PREVIEW_PREFIX + "PIPE"
    params = {"type":"PIPE", "radius":props.pipe_radius_ft, "length":props.pipe_length_ft, "thickness":props.pipe_thickness_ft, "unit":props.unit_type}
    return pipe, params

def build_curved_pipe(props, sc, angle_deg, name_prefix, param_type):
    cleanup_previews()
    major_r = to_internal(props.pipe_bend_radius_ft, sc)
    minor_r = to_internal(props.pipe_radius_ft, sc)
    thick = to_internal(props.pipe_thickness_ft, sc)
    res = props.pipe_resolution
    
    z_loc = minor_r
    
    bpy.ops.mesh.primitive_torus_add(major_segments=res*2, minor_segments=res, major_radius=major_r, minor_radius=minor_r, location=(0,0,z_loc))
    outer = bpy.context.active_object
    apply_transform(outer)
    
    if thick > 0 and minor_r - thick > 0.001:
        bpy.ops.mesh.primitive_torus_add(major_segments=res*2, minor_segments=res, major_radius=major_r, minor_radius=minor_r - thick, location=(0,0,z_loc))
        inner = bpy.context.active_object
        apply_transform(inner)
        apply_boolean(outer, inner, 'DIFFERENCE')
        try:
            bpy.data.objects.remove(inner, do_unlink=True)
        except:
            pass
            
    cutter_size = major_r * 4.0
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -cutter_size/2.0, z_loc))
    c1 = bpy.context.active_object
    c1.scale = (cutter_size, cutter_size, cutter_size)
    apply_transform(c1)
    apply_boolean(outer, c1, 'DIFFERENCE')
    try:
        bpy.data.objects.remove(c1, do_unlink=True)
    except:
        pass
    
    if angle_deg <= 90:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-cutter_size/2.0, 0, z_loc))
        c2 = bpy.context.active_object
        c2.scale = (cutter_size, cutter_size, cutter_size)
        apply_transform(c2)
        apply_boolean(outer, c2, 'DIFFERENCE')
        try:
            bpy.data.objects.remove(c2, do_unlink=True)
        except:
            pass
        
    if angle_deg == 45:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, cutter_size/2.0, z_loc))
        c3 = bpy.context.active_object
        c3.scale = (cutter_size, cutter_size, cutter_size)
        c3.location = (-cutter_size/2.0 * math.sin(math.radians(45)), cutter_size/2.0 * math.cos(math.radians(45)), z_loc)
        c3.rotation_euler.z = math.radians(45)
        apply_transform(c3)
        apply_boolean(outer, c3, 'DIFFERENCE')
        try:
            bpy.data.objects.remove(c3, do_unlink=True)
        except:
            pass

    outer.name = PREVIEW_PREFIX + name_prefix
    
    outer.location.x -= major_r
    apply_transform(outer)
    
    params = {"type":param_type, "radius":props.pipe_radius_ft, "bend_radius":props.pipe_bend_radius_ft, "thickness":props.pipe_thickness_ft, "unit":props.unit_type}
    return outer, params

def gen_pipe_l(props, sc):
    return build_curved_pipe(props, sc, 90, "PIPE_L", "PIPE_L")

def gen_pipe_u(props, sc):
    return build_curved_pipe(props, sc, 180, "PIPE_U", "PIPE_U")

def gen_pipe_45(props, sc):
    return build_curved_pipe(props, sc, 45, "PIPE_45", "PIPE_45")
