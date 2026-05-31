import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from .math_utils import sample_fcurve_speed

_draw_handler = None

def get_shader():
    try:
        # Blender 4.0+ 和 3.x 后期推荐
        return gpu.shader.from_builtin('UNIFORM_COLOR')
    except Exception:
         # 兼容老版本
         return gpu.shader.from_builtin('2D_UNIFORM_COLOR')

def get_active_fcurves(context):
    """获取活动物体当前被选中的 F-Curve"""
    obj = context.active_object
    if not obj or not obj.animation_data or not obj.animation_data.action:
        return []
    
    action = obj.animation_data.action
    fcurves_col = []
    if hasattr(action, "fcurves"):
        # Blender 4.2及更早
        fcurves_col = action.fcurves
    else:
        # Blender 4.3+ / 5.0 Slotted Action
        try:
            from bpy_extras import anim_utils
            slot = obj.animation_data.action_slot
            if slot:
                bag = anim_utils.action_get_channelbag_for_slot(action, slot)
                if bag:
                    fcurves_col = bag.fcurves
        except Exception:
            pass
            
    return [fc for fc in fcurves_col if fc.select]

def draw_speed_curve():
    context = bpy.context
    if not context.area or context.area.type != 'GRAPH_EDITOR':
        return
        
    scene = getattr(context, 'scene', None)
    if not scene: return
    
    props = getattr(scene, "speed_curve_props", None)
    if not props or not props.is_enabled:
        return

    scale_y = props.scale_y
    color = props.line_color
    zero_color = (0.5, 0.5, 0.5, 0.5)

    curves = get_active_fcurves(context)
    if not curves:
        return

    region = context.region
    view2d = region.view2d
    if not view2d: return

    # 获取视图可见帧的范围，用于限制采样范围，提升性能
    try:
        # region_to_view 返回的是 (x, y) 的元组，左下角和右上角
        x_min, _ = view2d.region_to_view(0, 0)
        x_max, _ = view2d.region_to_view(region.width, region.height)
    except Exception:
        # 获取失败或在某些未就绪的地方，直接跳过
        return
    
    # 稍微向外扩展一点采样，避免边缘被切掉
    x_min -= 10
    x_max += 10
    
    shader = get_shader()
    shader.bind()
    
    # 开启 GPU 抗锯齿与混合
    try:
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(1.5)
    except Exception:
        pass
    
    # 1. 绘制速度 0 轴（基准线），直接在 VIEW 空间绘制
    batch_zero = batch_for_shader(shader, 'LINES', {"pos": [(x_min, 0.0), (x_max, 0.0)]})
    shader.uniform_float("color", zero_color)
    batch_zero.draw(shader)

    # 2. 绘制速度曲线
    shader.uniform_float("color", color)
    for fcurve in curves:
        # 开启终极重采样精度（0.01帧=每帧100个多边形线段），逼近 Blender 原生几何平滑极限
        samples = sample_fcurve_speed(fcurve, x_min, x_max, step=0.01)
        
        curve_verts = [(frame, speed * scale_y) for frame, speed in samples]
                 
        if len(curve_verts) > 1:
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": curve_verts})
            batch.draw(shader)
            
    try:
        gpu.state.blend_set('NONE')
    except Exception:
        pass

def register_draw_handler():
    global _draw_handler
    if _draw_handler is None:
        args = ()
        _draw_handler = bpy.types.SpaceGraphEditor.draw_handler_add(
            draw_speed_curve, args, 'WINDOW', 'POST_VIEW'
        )

def unregister_draw_handler():
    global _draw_handler
    if _draw_handler is not None:
        bpy.types.SpaceGraphEditor.draw_handler_remove(_draw_handler, 'WINDOW')
        _draw_handler = None
