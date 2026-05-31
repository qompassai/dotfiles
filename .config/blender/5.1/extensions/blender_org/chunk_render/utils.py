import bpy
import math
import re
import gpu
import blf
from bpy.app.handlers import persistent
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from .tile_common import cr_cell_rect

_cr_shader_cache = None
_cr_draw_handler = None
_cr_overlay_suspend_depth = 0
_cr_overlay_sync_retries = 0
_LABEL_THRESHOLD = 400
_cr_custom_indices_cache: tuple = ("", 0, [])  # (text, total, result)


def cr_get_addon_preferences(context=None):
    try:
        prefs_owner = context if context is not None else bpy.context
        prefs = getattr(prefs_owner, "preferences", None)
        if prefs is None:
            return None
        addon = prefs.addons.get(__package__)
        return addon.preferences if addon else None
    except Exception:
        return None


def cr_debug_enabled(context=None):
    prefs = cr_get_addon_preferences(context)
    return bool(getattr(prefs, "debug_logging", False)) if prefs else False


def cr_log(message):
    print(message)


def cr_log_debug(message, context=None):
    if cr_debug_enabled(context):
        print(message)


def _cr_any_overlay_enabled():
    try:
        for scene in bpy.data.scenes:
            ps = getattr(scene, "chunk_render_settings", None)
            if ps is not None and getattr(ps, "CR_overlay_enabled", False):
                return True
    except Exception:
        return False
    return False


def cr_register_draw_handler():
    global _cr_draw_handler
    if _cr_draw_handler is not None:
        return
    try:
        _cr_draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            cr_draw_callback, (), 'WINDOW', 'POST_PIXEL'
        )
    except Exception as e:
        _cr_draw_handler = None
        cr_log_debug(f"[Chunk Render][DEBUG] Failed to register overlay draw handler: {e}")


def cr_unregister_draw_handler():
    global _cr_draw_handler
    if _cr_draw_handler is None:
        return
    try:
        bpy.types.SpaceView3D.draw_handler_remove(_cr_draw_handler, 'WINDOW')
    except Exception as e:
        cr_log_debug(f"[Chunk Render][DEBUG] Failed to unregister overlay draw handler: {e}")
    finally:
        _cr_draw_handler = None


def cr_sync_draw_handler():
    if _cr_any_overlay_enabled():
        cr_register_draw_handler()
    else:
        cr_unregister_draw_handler()


def cr_suspend_overlay_draw():
    global _cr_overlay_suspend_depth
    _cr_overlay_suspend_depth += 1


def cr_resume_overlay_draw():
    global _cr_overlay_suspend_depth
    _cr_overlay_suspend_depth = max(0, _cr_overlay_suspend_depth - 1)


def cr_refresh_overlay():
    cr_sync_draw_handler()
    cr_tag_view3d_redraw()


def _cr_overlay_sync_timer():
    global _cr_overlay_sync_retries
    try:
        cr_refresh_overlay()
    except Exception as e:
        cr_log_debug(f"[Chunk Render][DEBUG] Delayed overlay sync failed: {e}")
    if _cr_any_overlay_enabled() or _cr_overlay_sync_retries <= 0:
        _cr_overlay_sync_retries = 0
        return None
    _cr_overlay_sync_retries -= 1
    return 0.2


def cr_schedule_overlay_sync(first_interval=0.05, retries=3):
    global _cr_overlay_sync_retries
    _cr_overlay_sync_retries = max(_cr_overlay_sync_retries, max(0, int(retries)))
    try:
        if not bpy.app.timers.is_registered(_cr_overlay_sync_timer):
            bpy.app.timers.register(_cr_overlay_sync_timer, first_interval=max(0.0, float(first_interval)))
    except Exception as e:
        cr_log_debug(f"[Chunk Render][DEBUG] Failed to schedule overlay sync: {e}")


def cr_sync_level_grid_settings(scene=None):
    scenes = [scene] if scene is not None else getattr(bpy.data, "scenes", [])
    for scn in scenes:
        ps = getattr(scn, "chunk_render_settings", None)
        if ps is None:
            continue
        sync_level_grid = getattr(ps, "sync_level_grid", None)
        if callable(sync_level_grid):
            try:
                _ = sync_level_grid()
            except Exception as e:
                cr_log_debug(f"[Chunk Render][DEBUG] Failed to sync level grid settings: {e}")


@persistent
def cr_overlay_load_post(_dummy):
    cr_log_debug("[Chunk Render][DEBUG] load_post received, scheduling overlay sync")
    cr_sync_level_grid_settings()
    cr_schedule_overlay_sync(first_interval=0.05, retries=5)


def cr_register_overlay_lifecycle():
    handlers = bpy.app.handlers.load_post
    if cr_overlay_load_post not in handlers:
        handlers.append(cr_overlay_load_post)
    cr_sync_level_grid_settings()
    cr_schedule_overlay_sync(first_interval=0.05, retries=5)


def cr_unregister_overlay_lifecycle():
    handlers = getattr(bpy.app.handlers, "load_post", None)
    if handlers is not None and cr_overlay_load_post in handlers:
        handlers.remove(cr_overlay_load_post)
    try:
        if bpy.app.timers.is_registered(_cr_overlay_sync_timer):
            bpy.app.timers.unregister(_cr_overlay_sync_timer)
    except Exception as e:
        cr_log_debug(f"[Chunk Render][DEBUG] Failed to unregister overlay sync timer: {e}")


def get_cr_shader():
    global _cr_shader_cache
    if _cr_shader_cache is None:
        try:
            _cr_shader_cache = gpu.shader.from_builtin('UNIFORM_COLOR')
        except Exception:
            pass
    return _cr_shader_cache


def get_comp_tree(scene):
    tree = getattr(scene, "compositing_node_group", None)
    if tree is None:
        tree = getattr(scene, "node_tree", None)
    return tree

def cr_get_output_file_base_dir_value(node):
    val = getattr(node, "directory", None)
    if val is None:
        val = getattr(node, "base_path", None)
    return "" if val is None else str(val)


def cr_get_output_file_base_dir(node):
    base_path = cr_get_output_file_base_dir_value(node)
    if not base_path:
        return ""
    try:
        return bpy.path.abspath(base_path)
    except Exception as e:
        cr_log(f"[Chunk Render] abspath failed: {e}")
        return str(base_path)


def cr_set_output_file_base_dir(node, value):
    new_value = "" if value is None else str(value)
    if hasattr(node, "directory"):
        node.directory = new_value
    elif hasattr(node, "base_path"):
        node.base_path = new_value


def cr_get_output_file_name(node):
    val = getattr(node, "file_name", None)
    return "" if val is None else str(val)


def cr_set_output_file_name(node, value):
    if hasattr(node, "file_name"):
        node.file_name = "" if value is None else str(value)


def cr_get_output_file_items(node):
    fmt = str(getattr(getattr(node, "format", None), "file_format", "") or "")
    if fmt == 'OPEN_EXR_MULTILAYER':
        items = getattr(node, "layer_slots", None)
        if items is not None:
            return items
        items = getattr(node, "file_slots", None)
        if items is not None:
            return items
    else:
        items = getattr(node, "file_slots", None)
        if items is not None:
            return items
        items = getattr(node, "layer_slots", None)
        if items is not None:
            return items
    items = getattr(node, "file_output_items", None)
    return items if items is not None else []


def cr_output_file_item_supports_path(item):
    return hasattr(item, "path") or hasattr(item, "file_path")


def cr_get_output_file_item_path(item):
    if hasattr(item, "path"):
        return item.path
    if hasattr(item, "file_path"):
        return item.file_path
    return ""


def cr_set_output_file_item_path(item, value):
    if hasattr(item, "path"):
        item.path = value
    elif hasattr(item, "file_path"):
        item.file_path = value
    else:
        cr_log_debug(f"[Chunk Render][DEBUG] Skipped unsupported File Output slot type for path assignment: {type(item)}")


def cr_output_file_has_linked_slots(node):
    inputs = getattr(node, "inputs", None)
    if not inputs:
        return False
    return any(getattr(inp, "is_linked", False) for inp in inputs)


def cr_strip_chunk_suffix(path_str):
    result = re.sub(r'(?:\d+x\d+_\d+_\d+_)+$', '', str(path_str))
    return result.rstrip('_')


def cr_tag_view3d_redraw():
    try:
        wm = getattr(bpy.context, "window_manager", None)
        if wm is None:
            return
        for window in tuple(getattr(wm, "windows", ())):
            screen = getattr(window, "screen", None)
            if screen is None:
                continue
            for area in tuple(getattr(screen, "areas", ())):
                if getattr(area, "type", None) != 'VIEW_3D':
                    continue
                try:
                    area.tag_redraw()
                except Exception:
                    continue
    except Exception:
        return

def cr_get_camera_frame_2d(context, region, region_data):
    scene = context.scene
    cam = scene.camera
    if cam is None:
        return None
    frame = cam.data.view_frame(scene=scene)
    mat = cam.matrix_world
    coords_2d = []
    for v in frame:
        co = mat @ v
        screen = view3d_utils.location_3d_to_region_2d(region, region_data, co)
        if screen is None:
            return None
        coords_2d.append(screen)
    xs = [c.x for c in coords_2d]
    ys = [c.y for c in coords_2d]
    return min(xs), max(xs), min(ys), max(ys)

def cr_draw_grid_lines(left, right, bottom, top, cols, rows, color):
    width = right - left
    height = top - bottom
    if width <= 0 or height <= 0:
        return
    coords = []
    for i in range(1, cols):
        x = left + width * (i / cols)
        coords.extend([(x, bottom), (x, top)])
    for j in range(1, rows):
        y = bottom + height * (j / rows)
        coords.extend([(left, y), (right, y)])
    if not coords:
        return
    shader = get_cr_shader()
    if not shader: return
    batch = batch_for_shader(shader, 'LINES', {"pos": coords})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def cr_draw_selected_tiles(left, right, bottom, top, cols, rows, indices, color, line_width=1.0):
    width = right - left
    height = top - bottom
    if width <= 0 or height <= 0:
        return
    coords = []
    for idx in indices:
        rect = cr_cell_rect(left, right, bottom, top, cols, rows, idx)
        if rect is None:
            continue
        x1, x2, y1, y2 = rect
        coords.extend([(x1, y1), (x2, y1), (x2, y1), (x2, y2), (x2, y2), (x1, y2), (x1, y2), (x1, y1)])
    if not coords:
        return
    shader = get_cr_shader()
    if not shader: return
    batch = batch_for_shader(shader, 'LINES', {"pos": coords})
    set_line_width = getattr(gpu.state, "line_width_set", None)
    if callable(set_line_width):
        _ = set_line_width(max(line_width, 1.0))
    try:
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)
    finally:
        if callable(set_line_width):
            _ = set_line_width(1.0)


def cr_draw_bleed_rects(frame_left, frame_right, frame_bottom, frame_top, inner_left, inner_right, inner_bottom, inner_top, cols, rows, bleed_px, resx, resy, color):
    inner_w = inner_right - inner_left
    inner_h = inner_top - inner_bottom
    frame_w = frame_right - frame_left
    frame_h = frame_top - frame_bottom
    if inner_w <= 0 or inner_h <= 0 or frame_w <= 0 or frame_h <= 0:
        return
    if resx <= 0 or resy <= 0:
        return
    bleed_frac_x = bleed_px / resx
    bleed_frac_y = bleed_px / resy
    bleed_screen_x = frame_w * bleed_frac_x
    bleed_screen_y = frame_h * bleed_frac_y
    cell_w = inner_w / cols
    cell_h = inner_h / rows
    
    def _add_dashed_line(p1, p2, target_coords, dash=6, gap=4):
        dx, dy = p2[0]-p1[0], p2[1]-p1[1]
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < 1: return
        ux, uy = dx/dist, dy/dist
        curr = 0
        while curr < dist:
            end = min(curr + dash, dist)
            target_coords.append((p1[0] + ux * curr, p1[1] + uy * curr))
            target_coords.append((p1[0] + ux * end, p1[1] + uy * end))
            curr += dash + gap

    coords_line = []
    coords_fill = []
    
    total_tx1, total_tx2 = inner_left, inner_right
    total_ty1, total_ty2 = inner_top, inner_bottom
    total_bx1, total_bx2 = max(frame_left, total_tx1 - bleed_screen_x), min(frame_right, total_tx2 + bleed_screen_x)
    total_by1, total_by2 = min(frame_top, total_ty1 + bleed_screen_y), max(frame_bottom, total_ty2 - bleed_screen_y)

    xs = [total_bx1, total_tx1]
    for c in range(1, cols):
        pos = total_tx1 + c * cell_w
        xs.append(pos - bleed_screen_x)
        xs.append(pos + bleed_screen_x)
    xs.append(total_tx2)
    xs.append(total_bx2)
    
    ys = [total_by2, total_ty2]
    for r in range(1, rows):
        pos = total_ty2 + r * cell_h
        ys.append(pos - bleed_screen_y)
        ys.append(pos + bleed_screen_y)
    ys.append(total_ty1)
    ys.append(total_by1)

    core_x = {i for i in range(1, 2 * cols, 2)}
    core_y = {j for j in range(1, 2 * rows, 2)}
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            if i in core_x and j in core_y:
                continue
            x1, x2 = xs[i], xs[i+1]
            y1, y2 = ys[j], ys[j+1]
            if x2 > x1 and y2 > y1:
                coords_fill.extend([(x1, y1), (x2, y1), (x2, y2), (x1, y1), (x2, y2), (x1, y2)])

    h_segments = set()
    v_segments = set()

    def _find_idx(val, seq):
        for idx, s_val in enumerate(seq):
            if abs(s_val - val) < 0.2:
                return idx  # 0.2 pixel tolerance
        return -1

    for r in range(rows):
        for c in range(cols):
            tx1, tx2 = inner_left + c * cell_w, inner_left + (c + 1) * cell_w
            ty1, ty2 = inner_top - r * cell_h, inner_top - (r + 1) * cell_h
            bx1, bx2 = max(frame_left, tx1 - bleed_screen_x), min(frame_right, tx2 + bleed_screen_x)
            by1, by1_top = min(frame_top, ty1 + bleed_screen_y), max(frame_bottom, ty2 - bleed_screen_y)
            by1, by2 = by1_top, by1  # normalize so y1 < y2 for later calculations
            if by1 > by2:
                by1, by2 = by2, by1
            
            ix1, ix2 = _find_idx(bx1, xs), _find_idx(bx2, xs)
            jy1, jy2 = _find_idx(by1, ys), _find_idx(by2, ys)
            
            if ix1 != -1 and ix2 != -1 and jy1 != -1 and jy2 != -1:
                for i in range(ix1, ix2):
                    h_segments.add((jy1, i))
                    h_segments.add((jy2, i))
                for j in range(jy1, jy2):
                    v_segments.add((ix1, j))
                    v_segments.add((ix2, j))

    for j, i in h_segments:
        _add_dashed_line((xs[i], ys[j]), (xs[i+1], ys[j]), coords_line)
    for i, j in v_segments:
        _add_dashed_line((xs[i], ys[j]), (xs[i], ys[j+1]), coords_line)

    if coords_fill:
        shader_f = get_cr_shader()
        if shader_f:
            batch_f = batch_for_shader(shader_f, 'TRIS', {"pos": coords_fill})
            gpu.state.blend_set('ALPHA')
            try:
                shader_f.bind()
                shader_f.uniform_float("color", (color[0], color[1], color[2], 0.15))
                batch_f.draw(shader_f)
            finally:
                gpu.state.blend_set('NONE')

    if coords_line:
        shader_l = get_cr_shader()
        if shader_l:
            batch_l = batch_for_shader(shader_l, 'LINES', {"pos": coords_line})
            shader_l.bind()
            shader_l.uniform_float("color", color)
            batch_l.draw(shader_l)


def _cr_draw_outlined_text(font_id, text, x, y, text_color=(1.0, 1.0, 1.0, 1.0), outline_color=(0.0, 0.0, 0.0, 1.0), offset=1.0, rotation=0.0):
    rotation_flag = getattr(blf, "ROTATION", getattr(blf, "BLF_ROTATION", None))
    use_rotation = abs(rotation) > 1e-6 and rotation_flag is not None
    if use_rotation:
        blf.enable(font_id, rotation_flag)
        blf.rotation(font_id, rotation)
    try:
        for dx, dy in ((-offset, 0.0), (offset, 0.0), (0.0, -offset), (0.0, offset)):
            blf.color(font_id, outline_color[0], outline_color[1], outline_color[2], outline_color[3])
            blf.position(font_id, x + dx, y + dy, 0)
            blf.draw(font_id, text)
        blf.color(font_id, text_color[0], text_color[1], text_color[2], text_color[3])
        blf.position(font_id, x, y, 0)
        blf.draw(font_id, text)
    finally:
        if use_rotation:
            blf.rotation(font_id, 0.0)
            blf.disable(font_id, rotation_flag)


def cr_draw_grid_labels(left, right, bottom, top, cols, rows, color, res_x, res_y, only_indices=None):
    width = right - left
    height = top - bottom
    if width <= 0 or height <= 0:
        return
    cell_w = width / cols
    cell_h = height / rows
    px_w = res_x / cols
    px_h = res_y / rows
    fmt_w = f"{px_w:.1f}" if px_w % 1 != 0 else f"{int(px_w)}"
    fmt_h = f"{px_h:.1f}" if px_h % 1 != 0 else f"{int(px_h)}"
    size_text = f"{fmt_w} x {fmt_h}"
    font_id = 0
    blf.size(font_id, 18)
    
    only_set = set(only_indices) if only_indices is not None else None

    ref_size_w, ref_size_h = blf.dimensions(font_id, size_text)
    size_text_padding = 10.0
    size_text_rotation = -math.pi / 2 if ref_size_w > max(cell_w - size_text_padding, 1.0) else 0.0

    for r in range(rows):
        for c in range(cols):
            index = r * cols + c
            if only_set is not None and index not in only_set:
                continue
            cx = left + (c + 0.5) * cell_w
            cy = top - (r + 0.5) * cell_h

            text_idx = str(index)
            d_idx = blf.dimensions(font_id, text_idx)
            index_y = cy + (ref_size_h * 0.5 + 6.0 if size_text_rotation != 0.0 else 2.0)

            _cr_draw_outlined_text(
                font_id,
                text_idx,
                cx - d_idx[0] / 2,
                index_y,
                text_color=(1.0, 1.0, 1.0, 1.0),
                outline_color=(0.0, 0.0, 0.0, 1.0),
                offset=1.0,
            )

            if size_text_rotation != 0.0:
                size_text_x = cx - ref_size_h / 2
                size_text_y = cy - 2
            else:
                size_text_x = cx - ref_size_w / 2
                size_text_y = cy - ref_size_h - 2

            _cr_draw_outlined_text(
                font_id,
                size_text,
                size_text_x,
                size_text_y,
                text_color=(1.0, 1.0, 1.0, 1.0),
                outline_color=(0.0, 0.0, 0.0, 1.0),
                offset=1.0,
                rotation=size_text_rotation,
            )


def cr_parse_custom_indices(text, total):
    if total <= 0:
        return []
    try:
        raw_txt = str(text).replace("，", ",").replace("、", ",")
        parts = raw_txt.split(",")
        result = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if p.isdigit():
                val = int(p)
                if 0 <= val < total:
                    result.append(val)
        return sorted(list(set(result)))
    except Exception as e:
        cr_log(f"[Chunk Render] parse_custom_indices failed: {e}")
        return []

def cr_get_effective_resolution(rnd, use_render_border):
    perc = rnd.resolution_percentage / 100.0
    if not use_render_border:
        return int(rnd.resolution_x * perc), int(rnd.resolution_y * perc)
    bminx, bmaxx, bminy, bmaxy = get_border_range(rnd, True)
    return (
        round((bmaxx - bminx) * rnd.resolution_x * perc),
        round((bmaxy - bminy) * rnd.resolution_y * perc),
    )


def get_border_range(rnd, use_render_border):
    if not use_render_border:
        return (0.0, 1.0, 0.0, 1.0)
    try:
        minx, maxx = float(rnd.border_min_x), float(rnd.border_max_x)
        miny, maxy = float(rnd.border_min_y), float(rnd.border_max_y)
    except (TypeError, ValueError):
        return (0.0, 1.0, 0.0, 1.0)
    return _cr_normalize_border_range(minx, maxx, miny, maxy)


def get_border_range_from_values(minx, maxx, miny, maxy):
    try:
        minx_f = float(minx)
        maxx_f = float(maxx)
        miny_f = float(miny)
        maxy_f = float(maxy)
    except (TypeError, ValueError):
        return (0.0, 1.0, 0.0, 1.0)
    return _cr_normalize_border_range(minx_f, maxx_f, miny_f, maxy_f)


def _cr_normalize_border_range(minx, maxx, miny, maxy):
    bminx = max(0.0, min(minx, maxx))
    bmaxx = min(1.0, max(minx, maxx))
    bminy = max(0.0, min(miny, maxy))
    bmaxy = min(1.0, max(miny, maxy))
    if (bmaxx - bminx) <= 0.0 or (bmaxy - bminy) <= 0.0:
        return (0.0, 1.0, 0.0, 1.0)
    return (bminx, bmaxx, bminy, bmaxy)


def _cr_get_cached_custom_indices(text, total):
    global _cr_custom_indices_cache
    cached_text, cached_total, cached_result = _cr_custom_indices_cache
    if cached_text != text or cached_total != total:
        cached_result = cr_parse_custom_indices(text, total)
        _cr_custom_indices_cache = (text, total, cached_result)
    return cached_result


def cr_draw_callback():
    if _cr_overlay_suspend_depth > 0:
        return

    try:
        context = bpy.context
        area = getattr(context, "area", None)
        region = getattr(context, "region", None)
        if area is None or getattr(area, "type", None) != 'VIEW_3D' or region is None or getattr(region, "type", None) != 'WINDOW':
            return

        region_data = getattr(context, "region_data", None)
        if region_data is None or getattr(region_data, "view_perspective", "") != 'CAMERA':
            return

        scene = getattr(context, "scene", None)
        if scene is None:
            return
        ps = getattr(scene, "chunk_render_settings", None)
        if ps is None or not getattr(ps, "CR_overlay_enabled", False):
            return

        cols = max(1, int(ps.CR_reg_columns))
        rows = max(1, int(ps.CR_reg_rows))
        total_tiles = cols * rows
        frame = cr_get_camera_frame_2d(context, region, region_data)
        if frame is None:
            return
        left, right, bottom, top = frame

        rnd = scene.render
        if ps.CR_renderGo:
            bminx, bmaxx, bminy, bmaxy = get_border_range_from_values(
                ps.CR_saved_border_min_x, ps.CR_saved_border_max_x,
                ps.CR_saved_border_min_y, ps.CR_saved_border_max_y,
            )
        else:
            active_use_border = ps.CR_use_render_border and rnd.use_border
            bminx, bmaxx, bminy, bmaxy = get_border_range(rnd, active_use_border)

        fw, fh = right - left, top - bottom
        il = left + fw * bminx
        ir = left + fw * bmaxx
        ib = bottom + fh * bminy
        it = bottom + fh * bmaxy
        color = (1.0, 0.6, 0.2, 0.8)
        perc = rnd.resolution_percentage / 100.0
        resx_sub = (rnd.resolution_x * perc) * (bmaxx - bminx)
        resy_sub = (rnd.resolution_y * perc) * (bmaxy - bminy)

        cr_draw_grid_lines(il, ir, ib, it, cols, rows, color)
        if total_tiles <= _LABEL_THRESHOLD:
            cr_draw_grid_labels(il, ir, ib, it, cols, rows, color, resx_sub, resy_sub)

        if ps.CR_select_mode == 'CUSTOM':
            indices = _cr_get_cached_custom_indices(ps.CR_custom_indices, total_tiles)
            if indices:
                highlight_color = (0.2, 1.0, 0.2, 1.0)
                cr_draw_selected_tiles(il, ir, ib, it, cols, rows, indices, highlight_color, line_width=3.0)
                if total_tiles <= _LABEL_THRESHOLD:
                    cr_draw_grid_labels(il, ir, ib, it, cols, rows, highlight_color, resx_sub, resy_sub, indices)

        if ps.CR_bleed_pixels > 0:
            cr_draw_bleed_rects(
                left,
                right,
                bottom,
                top,
                il,
                ir,
                ib,
                it,
                cols,
                rows,
                ps.CR_bleed_pixels,
                int(rnd.resolution_x * perc),
                int(rnd.resolution_y * perc),
                (1.0, 0.02, 0.15, 1.0),
            )

        if not ps.CR_renderGo or ps.CR_active_index == -1:
            return

        active_color = (0.2, 0.6, 1.0, 1.0)
        idx = ps.CR_active_index
        rect = cr_cell_rect(il, ir, ib, it, cols, rows, idx)
        if rect is not None:
            x1, x2, y2, y1 = rect
            fill_coords = [(x1, y1), (x2, y1), (x2, y2), (x1, y1), (x2, y2), (x1, y2)]
            shader = get_cr_shader()
            if shader:
                batch_f = batch_for_shader(shader, 'TRIS', {"pos": fill_coords})
                gpu.state.blend_set('ALPHA')
                try:
                    shader.bind()
                    shader.uniform_float("color", (0.2, 0.6, 1.0, 0.35))
                    batch_f.draw(shader)
                finally:
                    gpu.state.blend_set('NONE')
        cr_draw_selected_tiles(il, ir, ib, it, cols, rows, [idx], active_color)
    except Exception as e:
        cr_log_debug(f"[Chunk Render][DEBUG] Overlay draw skipped due to transient UI state: {e}")
        return
