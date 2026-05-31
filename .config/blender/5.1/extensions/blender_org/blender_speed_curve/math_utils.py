import bpy

def get_speed(fcurve, frame, delta=0.02):
    """
    计算 F-Curve 在特定帧的瞬时速度（变化率）。
    由于 Blender F-Curve 里的 Newton-Raphson 解算器精度有极限，
    太小的 delta 会产生高频噪音，所以使用 0.02。
    """
    if fcurve is None:
        return 0.0
    
    val_plus = fcurve.evaluate(frame + delta)
    val_minus = fcurve.evaluate(frame - delta)
    
    speed = (val_plus - val_minus) / (2.0 * delta)
    return speed

def smooth_speed_samples(samples, step, iterations=4):
    """一维高斯平滑滤波，剔除底层的微积分跳跃噪音"""
    if len(samples) < 3:
        return samples
    
    result = list(samples)
    for _ in range(iterations):
        new_result = [result[0]]
        for i in range(1, len(result) - 1):
            t_curr, v_curr = result[i]
            t_prev, v_prev = result[i-1]
            t_next, v_next = result[i+1]
            
            dt_prev = t_curr - t_prev
            dt_next = t_next - t_curr
            
            # 判断是否是连续段（排除关键帧前后的极小间距点，从而保护直角跳变的边缘锐度）
            is_continuous = abs(dt_prev - step) < (step * 0.1) and abs(dt_next - step) < (step * 0.1)
            
            if is_continuous:
                smoothed_v = (v_prev + 2.0 * v_curr + v_next) / 4.0
                new_result.append((t_curr, smoothed_v))
            else:
                new_result.append((t_curr, v_curr))
                
        new_result.append(result[-1])
        result = new_result
        
    return result

def sample_fcurve_speed(fcurve, start_frame, end_frame, step=0.01):
    """
    在指定帧范围内采样曲线的速度。
    """
    samples = []
    if fcurve is None:
        return samples
        
    times = set()
    frame = float(start_frame)
    while frame <= end_frame:
        times.add(round(frame, 3))
        frame += step
    times.add(round(float(end_frame), 3))
    
    # 强制在关键帧前后加入微小偏移点
    # 因为 delta=0.02，使用 offset=0.025 确保采样的上下界不会越过关键帧！
    for kf in fcurve.keyframe_points:
        t = kf.co[0]
        if start_frame - 1 <= t <= end_frame + 1:
            times.add(round(t - 0.025, 4))
            times.add(round(t + 0.025, 4))
            
    sorted_times = sorted(list(times))
    
    for t in sorted_times:
        if t < start_frame or t > end_frame:
            continue
        speed = get_speed(fcurve, t)
        samples.append((t, speed))
         
    # 最后对样本进行高斯滤波，滤除所有计算底噪，保持极限平滑
    samples = smooth_speed_samples(samples, step)
    return samples
