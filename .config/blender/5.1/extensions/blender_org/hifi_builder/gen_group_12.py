import bpy
from .utils import PREVIEW_PREFIX, apply_transform, cleanup_previews

def gen_procedural_cable(props, sc):
    cleanup_previews()
    
    length = props.cable_length_ft * sc
    droop = props.cable_droop_ft * sc
    thickness = props.cable_thickness_ft * sc
    
    curve_data = bpy.data.curves.new(PREVIEW_PREFIX + "CABLE_curve", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = props.cable_resolution
    curve_data.bevel_depth = thickness
    curve_data.bevel_resolution = 4
    curve_data.fill_mode = 'FULL'
    
    spline = curve_data.splines.new('NURBS')
    spline.points.add(2)
    
    spline.points[0].co = (0.0, 0.0, 0.0, 1.0)
    spline.points[1].co = (length / 2.0, 0.0, -droop, 1.0)
    spline.points[2].co = (length, 0.0, 0.0, 1.0)
    spline.use_endpoint_u = True
    
    obj = bpy.data.objects.new(PREVIEW_PREFIX + "CABLE", curve_data)
    bpy.context.collection.objects.link(obj)
    
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    apply_transform(obj)
    
    params = {"type": "CABLE", "unit": props.unit_type}
    return obj, params
