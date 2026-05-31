import bpy
from bpy.props import BoolProperty, FloatProperty, FloatVectorProperty, IntProperty
from bpy.types import PropertyGroup, Panel, Operator

def get_fcurves_compatible(context):
    obj = context.active_object
    if not obj or not obj.animation_data or not obj.animation_data.action:
        return []
    action = obj.animation_data.action
    fcurves_col = []
    if hasattr(action, "fcurves"):
        fcurves_col = action.fcurves
    else:
        try:
            from bpy_extras import anim_utils
            slot = obj.animation_data.action_slot
            if slot:
                bag = anim_utils.action_get_channelbag_for_slot(action, slot)
                if bag:
                    fcurves_col = bag.fcurves
        except Exception:
            pass
    return fcurves_col

def apply_easing_to_selected(context, side, value):
    fcurves_col = get_fcurves_compatible(context)
    if not fcurves_col:
        return

    modified = False
    for fcurve in fcurves_col:
        kfs = fcurve.keyframe_points
        if not any(kf.select_control_point for kf in kfs):
            continue

        for i, kf in enumerate(kfs):
            if kf.select_control_point:
                
                if side in {'LEFT', 'BOTH'} and i > 0:
                    prev_kf = kfs[i-1]
                    
                    was_linear = (kf.handle_left_type == 'VECTOR' or prev_kf.interpolation in {'LINEAR', 'CONSTANT'})
                    
                    center = kf.co
                    handle = kf.handle_left
                    curr_dx = center[0] - handle[0]
                    curr_dy = center[1] - handle[1]
                    original_slope = curr_dy / curr_dx if curr_dx > 0.0001 else 0.0
                    
                    # 强制改为贝塞尔，确保滑块拖动能直观看到效果
                    if prev_kf.interpolation != 'BEZIER':
                        prev_kf.interpolation = 'BEZIER'
                    if kf.handle_left_type != 'FREE':
                        kf.handle_left_type = 'FREE'
                        
                    dist_x = max(0.001, center[0] - prev_kf.co[0])
                    target_dx = dist_x * (value / 100.0)
                    target_dx = max(0.001, target_dx)
                    
                    if was_linear:
                        slope = 0.0
                    else:
                        slope = original_slope
                    
                    new_dy = target_dx * slope
                    kf.handle_left = (center[0] - target_dx, center[1] - new_dy)
                    modified = True

                if side in {'RIGHT', 'BOTH'} and i < len(kfs) - 1:
                    next_kf = kfs[i+1]
                    
                    was_linear = (kf.handle_right_type == 'VECTOR' or kf.interpolation in {'LINEAR', 'CONSTANT'})
                    
                    center = kf.co
                    handle = kf.handle_right
                    curr_dx = handle[0] - center[0]
                    curr_dy = handle[1] - center[1]
                    original_slope = curr_dy / curr_dx if curr_dx > 0.0001 else 0.0
                    
                    # 强制改为贝塞尔，确保滑块拖动能直观看到效果
                    if kf.interpolation != 'BEZIER':
                        kf.interpolation = 'BEZIER'
                    if kf.handle_right_type != 'FREE':
                        kf.handle_right_type = 'FREE'
                        
                    dist_x = max(0.001, next_kf.co[0] - center[0])
                    target_dx = dist_x * (value / 100.0)
                    target_dx = max(0.001, target_dx)
                    
                    if was_linear:
                        slope = 0.0
                    else:
                        slope = original_slope
                    
                    new_dy = target_dx * slope
                    kf.handle_right = (center[0] + target_dx, center[1] + new_dy)
                    modified = True
                    
        if modified:
            fcurve.update()

    if modified:
        for area in context.screen.areas:
            if area.type == 'GRAPH_EDITOR':
                area.tag_redraw()

def update_ease_in(self, context):
    apply_easing_to_selected(context, 'LEFT', self.ease_in)

def update_ease_out(self, context):
    apply_easing_to_selected(context, 'RIGHT', self.ease_out)

def update_ease_both(self, context):
    apply_easing_to_selected(context, 'BOTH', self.ease_both)

def update_speed_curve_toggle(self, context):
    from . import draw_handler
    if self.is_enabled:
        draw_handler.register_draw_handler()
    else:
        draw_handler.unregister_draw_handler()
    if context.area:
        context.area.tag_redraw()

class SpeedCurveProperties(PropertyGroup):
    is_enabled: BoolProperty(
        name="Enable Speed Curve",
        description="Draw speed curve in the background",
        default=False,
        update=update_speed_curve_toggle
    )
    scale_y: FloatProperty(
        name="Curve Amplitude",
        description="Scale the amplitude of the speed curve display",
        default=5.0,
        min=0.01,
        max=100.0,
        update=lambda self, context: context.area.tag_redraw() if context.area else None
    )
    line_color: FloatVectorProperty(
        name="Line Color",
        subtype='COLOR',
        default=(0.0, 1.0, 0.8, 1.0),
        size=4,
        min=0.0, max=1.0,
        update=lambda self, context: context.area.tag_redraw() if context.area else None
    )
    
    # 将滑块命名与功能严丝合缝匹配
    ease_in: IntProperty(
        name="Ease In",
        min=0, max=100, default=65, subtype='PERCENTAGE',
        update=update_ease_in
    )
    ease_out: IntProperty(
        name="Ease Out",
        min=0, max=100, default=88, subtype='PERCENTAGE',
        update=update_ease_out
    )
    ease_both: IntProperty(
        name="Ease Both",
        min=0, max=100, default=99, subtype='PERCENTAGE',
        update=update_ease_both
    )

class GRAPH_OT_set_interpolation(Operator):
    """Convert keyframe interpolation type and reset handles"""
    bl_idname = "graph.set_interpolation"
    bl_label = "Set Keyframe Interpolation"
    bl_options = {'REGISTER', 'UNDO'}
    
    interp_type: bpy.props.StringProperty()
    target_side: bpy.props.StringProperty(default='RIGHT')
    
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.animation_data
        
    def execute(self, context):
        fcurves_col = get_fcurves_compatible(context)
        modified = False
        
        for fcurve in fcurves_col:
            kfs = fcurve.keyframe_points
            for i, kf in enumerate(kfs):
                if kf.select_control_point:
                    # RIGHT side
                    if self.target_side in {'RIGHT', 'BOTH'}:
                        kf.interpolation = self.interp_type
                        if self.interp_type == 'BEZIER':
                            kf.handle_right_type = 'AUTO_CLAMPED'
                        elif self.interp_type == 'LINEAR':
                            kf.handle_right_type = 'VECTOR'
                        modified = True

                    # LEFT side
                    if self.target_side in {'LEFT', 'BOTH'}:
                        if i > 0:
                            kfs[i-1].interpolation = self.interp_type
                        if self.interp_type == 'BEZIER':
                            kf.handle_left_type = 'AUTO_CLAMPED'
                        elif self.interp_type == 'LINEAR':
                            kf.handle_left_type = 'VECTOR'
                        modified = True
                        
        if modified:
            for fcurve in fcurves_col:
                fcurve.update()
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    area.tag_redraw()
            
        return {'FINISHED'}

class GRAPH_PT_speed_curve_panel(Panel):
    bl_label = "Motion Style"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Motion'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.speed_curve_props
        
        row = layout.row()
        row.label(text="MOTION STYLE 1.0.2", icon='IPO_BEZIER')
        
        box = layout.box()
        col = box.column(align=True)
        col.scale_y = 1.3 
        
        self.draw_ae_row(col, props, "ease_in", 'LEFT') 
        self.draw_ae_row(col, props, "ease_out", 'RIGHT') 
        self.draw_ae_row(col, props, "ease_both", 'BOTH') 

        layout.separator()
        
        settings_box = layout.box()
        settings_box.prop(props, "is_enabled")
        if props.is_enabled:
            settings_box.prop(props, "scale_y")
            settings_box.prop(props, "line_color")
            
        layout.separator()
        row_author = layout.row()
        row_author.alignment = 'RIGHT'
        row_author.label(text="@WILLY_WORK")

    def draw_ae_row(self, layout, props, prop_name, target_side):
        split = layout.split(factor=0.1, align=True)
        
        # 左侧图标指示
        icon_text = " < " if target_side == 'LEFT' else (" > " if target_side == 'RIGHT' else " >< ")
        split.label(text=icon_text)
        
        # 滑块和右侧插值类型按键
        split2 = split.split(factor=0.7, align=True)
        split2.prop(props, prop_name, text="", slider=True)
        
        btn_row = split2.row(align=True)
        
        op_bezier = btn_row.operator(GRAPH_OT_set_interpolation.bl_idname, text="", icon='IPO_BEZIER')
        op_bezier.interp_type = 'BEZIER'
        op_bezier.target_side = target_side
        
        op_linear = btn_row.operator(GRAPH_OT_set_interpolation.bl_idname, text="", icon='IPO_LINEAR')
        op_linear.interp_type = 'LINEAR'
        op_linear.target_side = target_side
        
        op_const = btn_row.operator(GRAPH_OT_set_interpolation.bl_idname, text="", icon='IPO_CONSTANT')
        op_const.interp_type = 'CONSTANT'
        op_const.target_side = target_side
