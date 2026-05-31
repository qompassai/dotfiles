# SPDX-License-Identifier: GPL-2.0-or-later
#
# Multi Files Bookmark
#
# Blender keeps one active .blend data-base per process. This add-on stays
# inside the current Blender window and switches projects with open_mainfile().
# Before switching away, it writes a copy of the current project to Blender's
# user cache directory. Switching back opens that cache copy, so unsaved edits
# survive without touching the original .blend file.

bl_info = {
    "name": "Multi Files Bookmark",
    "author": "61+",
    "version": (0, 6, 5),
    "blender": (5, 0, 0),
    "location": "3D View > Floating Top Tab Bar",
    "description": "Manage blend project as bookmarks in one Blender window",
    "category": "System",
}

import json
import math
import os
import hashlib
import tempfile
import time
import uuid

import blf
import bpy
import gpu
import mathutils
from bpy_extras import view3d_utils
from bpy.app.handlers import persistent
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from gpu_extras.batch import batch_for_shader


ADDON_ID = "multi_blender_bookmark"
ADDON_MODULE = __package__
CACHE_FOLDER_NAME = "Blender Bookmark"
DEFAULT_CACHE_DIR = os.path.join(tempfile.gettempdir(), CACHE_FOLDER_NAME)
REGISTRY_PATH = os.path.join(DEFAULT_CACHE_DIR, "multi_blender_bookmark.json")
LEGACY_REGISTRY_PATH = os.path.join(tempfile.gettempdir(), "multi_blender_bookmark.json")
LAST_CLOSED_PATH = os.path.join(DEFAULT_CACHE_DIR, "multi_blender_bookmark_last_closed.json")
OVERLAY_STATE_PATH = os.path.join(DEFAULT_CACHE_DIR, "multi_blender_bookmark_overlay_state.json")

MAX_BOOKMARK_LABEL_CHARS = 12
OVERLAY_MARGIN = 14
OVERLAY_TOP_OFFSET = 70
TAB_WIDTH = 190
TAB_HEIGHT = 40
THUMB_TAB_WIDTH = 204
THUMB_TAB_HEIGHT = 126
THUMBNAIL_WIDTH = 150
THUMBNAIL_HEIGHT = 70
THUMBNAIL_BACKGROUND = (1.0, 1.0, 1.0, 1.0)
TAB_GAP = 8
NEW_BUTTON_WIDTH = 88
ICON_BUTTON_SIZE = 44
VIEW_TOGGLE_WIDTH = 88
CONTROL_GAP = 10
TAB_GROUP_GAP = 12
DOCK_PADDING_Y = 7

# Icon proportions are based on Microsoft Fluent UI System Icons (MIT):
# https://github.com/microsoft/fluentui-system-icons
# Referenced glyph families: Add, Document Add, Bookmark, Dismiss.
# The glyphs are redrawn below with Blender GPU primitives so the add-on stays
# a single self-contained Python file and does not depend on Blender's icon set.
ICON_REFERENCE = "Microsoft Fluent UI System Icons"

ADD_BUTTON_BLUE = (0.033104766570885055, 0.14126329114027164, 0.7758222183174236, 1.0)  # sRGB #3369e4
ADD_BUTTON_BLUE_HOVER = (0.07323895587840543, 0.2232279573168085, 1.0, 1.0)  # sRGB #4c82ff

addon_keymaps = []
_overlay_draw_handler = None
_overlay_router_running = False
_overlay_hitboxes = []
_overlay_hitboxes_by_area = {}
_overlay_dock_rects_by_area = {}
_overlay_last_region_size = (0, 0)
_overlay_mouse_abs = (-100000, -100000)
_overlay_absorb_leftmouse_release = False
_overlay_area_states = {}
_overlay_area_previous_modes = {}
_overlay_default_state = "NAMES"
_overlay_saved_area_states = []
_overlay_visibility_initialized = False
_overlay_view_mode_state = "NAMES"
_original_draw_xform_template = None
_thumbnail_textures = {}
_sdf_round_rect_shader = None
_sdf_line_shader = None
_sdf_shader_warning_printed = False

SHORTCUT_DEFAULTS = {
    "shortcut_restore_closed": "CTRL T",
    "shortcut_close": "CTRL W",
    "shortcut_next": "CTRL TAB",
    "shortcut_prev": "CTRL SHIFT TAB",
    "shortcut_toggle_bar": "CTRL SHIFT ACCENT_GRAVE",
}

SHORTCUT_TARGETS = (
    "shortcut_close",
    "shortcut_restore_closed",
    "shortcut_next",
    "shortcut_prev",
)
SHORTCUT_TARGET_LABELS = {
    "shortcut_restore_closed": "Reopen Closed",
    "shortcut_close": "Close Selected",
    "shortcut_next": "Switch to Next",
    "shortcut_prev": "Switch to Previous",
    "shortcut_toggle_bar": "Toggle Bar",
}
DOCK_SHORTCUT_OPERATOR_ID = "wm.mbb_dock_shortcut"
TOGGLE_BAR_SHORTCUT_OPERATOR_ID = "wm.mbb_toggle_area_tab_bar"
KEYMAP_NAME = "Window"
KEYMAP_SPACE_TYPE = "EMPTY"

OVERLAY_STATES = {"HIDDEN", "NAMES", "THUMBNAILS"}
VISIBLE_OVERLAY_STATES = {"NAMES", "THUMBNAILS"}


_selected_bookmark_indices = set()
_selection_anchor_index = -1
_last_closed_tabs = []
_closed_tab_history = []
_startup_session_initialized = False


def _now():
    return time.time()


def _clear_thumbnail_texture(filepath):
    path = bpy.path.abspath(filepath) if filepath else ""
    cached = _thumbnail_textures.pop(path, None)
    if cached is not None:
        try:
            bpy.data.images.remove(cached[1])
        except Exception:
            pass


def _title_from_path(filepath):
    if filepath:
        title = os.path.basename(bpy.path.abspath(filepath)) or "Untitled"
        if title.lower().endswith(".blend"):
            title = title[:-6]
        return title or "Untitled"
    return "Untitled"


def _display_title(title):
    title = title or "Untitled"
    if title.lower().endswith(".blend"):
        title = title[:-6]
    if len(title) > MAX_BOOKMARK_LABEL_CHARS:
        return title[:MAX_BOOKMARK_LABEL_CHARS] + "..."
    return title


def _format_shortcut_display(shortcut_str):
    if not shortcut_str or shortcut_str == "NONE":
        return "None"
    parts = shortcut_str.replace("+", " ").split()
    key_map = {
        "ACCENT_GRAVE": "~",
        "SPACE": "Space",
        "BACK_SLASH": "\\",
        "SLASH": "/",
        "COMMA": ",",
        "PERIOD": ".",
        "SEMI_COLON": ";",
        "QUOTE": "'",
        "LEFT_BRACKET": "[",
        "RIGHT_BRACKET": "]",
        "MINUS": "-",
        "EQUAL": "=",
        "BACKSPACE": "Backspace",
        "BACK_SPACE": "Backspace",
        "TAB": "Tab",
        "RET": "Enter",
        "RETURN": "Enter",
        "ESC": "Esc",
        "DEL": "Delete",
        "HOME": "Home",
        "END": "End",
        "PAGE_UP": "PageUp",
        "PAGE_DOWN": "PageDown",
        "NUMPAD_SLASH": "Num/",
        "NUMPAD_ASTERIX": "Num*",
        "NUMPAD_MINUS": "Num-",
        "NUMPAD_PLUS": "Num+",
        "NUMPAD_PERIOD": "Num.",
        "NUMPAD_0": "Num0",
        "NUMPAD_1": "Num1",
        "NUMPAD_2": "Num2",
        "NUMPAD_3": "Num3",
        "NUMPAD_4": "Num4",
        "NUMPAD_5": "Num5",
        "NUMPAD_6": "Num6",
        "NUMPAD_7": "Num7",
        "NUMPAD_8": "Num8",
        "NUMPAD_9": "Num9",
    }
    display_parts = []
    for part in parts:
        if part == "ALT":
            display_parts.append("Alt")
        elif part == "CTRL":
            display_parts.append("Ctrl")
        elif part == "SHIFT":
            display_parts.append("Shift")
        elif part == "OSKEY":
            display_parts.append("Cmd" if os.name == "posix" else "Win")
        elif part in key_map:
            display_parts.append(key_map[part])
        elif len(part) == 1:
            display_parts.append(part.upper())
        elif part.startswith("F") and part[1:].isdigit():
            display_parts.append(part)
        else:
            display_parts.append(part.replace("_", " ").title())
    return "+".join(display_parts)


def _normalize_shortcut(shortcut):
    parts = shortcut.replace("+", " ").split() if shortcut else []
    if not parts:
        return ""
    order = {"CTRL": 0, "SHIFT": 1, "ALT": 2, "OSKEY": 3}
    modifiers = sorted([part.upper() for part in parts[:-1]], key=lambda part: order.get(part, 99))
    key = parts[-1].upper()
    return " ".join(modifiers + [key])


def _shortcut_parts(shortcut):
    normalized = _normalize_shortcut(shortcut)
    if not normalized or normalized == "NONE":
        return "", set()
    parts = normalized.split()
    return parts[-1], set(parts[:-1])


def _keymap_item_for_target(target, keyconfig=None):
    if target not in SHORTCUT_TARGET_LABELS:
        return None, None, None
    wm = getattr(bpy.context, "window_manager", None)
    keyconfigs = getattr(wm, "keyconfigs", None)
    candidates = []
    if keyconfig is not None:
        candidates.append(keyconfig)
    elif keyconfigs is not None:
        candidates.extend(kc for kc in (getattr(keyconfigs, "user", None), getattr(keyconfigs, "addon", None)) if kc)
    for kc in candidates:
        km = kc.keymaps.get(KEYMAP_NAME)
        if km is None:
            continue
        for kmi in km.keymap_items:
            if target == "shortcut_toggle_bar":
                if kmi.idname == TOGGLE_BAR_SHORTCUT_OPERATOR_ID:
                    return kc, km, kmi
                continue
            if kmi.idname != DOCK_SHORTCUT_OPERATOR_ID:
                continue
            if getattr(getattr(kmi, "properties", None), "target", "") == target:
                return kc, km, kmi
    return None, None, None


def _current_blend_filepath():
    try:
        return getattr(bpy.data, "filepath", "") or ""
    except (AttributeError, ReferenceError, RuntimeError):
        return ""


def _window_manager_from_context(context=None):
    try:
        context = context or bpy.context
        return getattr(context, "window_manager", None)
    except (AttributeError, ReferenceError, RuntimeError):
        return None


def _cache_dir():
    prefs = _addon_preferences()
    if prefs and hasattr(prefs, "cache_directory") and prefs.cache_directory:
        path = bpy.path.abspath(prefs.cache_directory)
        try:
            os.makedirs(path, exist_ok=True)
            return path
        except OSError:
            pass
    # Keep all generated .blend caches and viewport previews in one clear
    # folder under %TEMP%, so Windows' temp root does not become cluttered.
    path = DEFAULT_CACHE_DIR
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        path = os.path.join(bpy.app.tempdir or tempfile.gettempdir(), CACHE_FOLDER_NAME)
        os.makedirs(path, exist_ok=True)
    return path


def _cache_path_for(filepath):
    # Intentionally use the original file name only. If another project has the
    # same file name, it overwrites the same cache file as requested.
    name = os.path.basename(bpy.path.abspath(filepath)) or "untitled.blend"
    if not name.lower().endswith(".blend"):
        name += ".blend"
    return os.path.join(_cache_dir(), name)


def _safe_filename_part(value):
    return "".join(char if char not in '<>:"/\\|?*' else "_" for char in str(value)) or "untitled"


def _new_tab_id():
    return uuid.uuid4().hex


def _stable_tab_id_for_paths(filepath="", cache_filepath=""):
    payload = "|".join((bpy.path.abspath(filepath or ""), bpy.path.abspath(cache_filepath or "")))
    return hashlib.sha1(payload.encode("utf-8", errors="ignore")).hexdigest()[:24]


def _is_untitled_path(filepath):
    name = os.path.basename(bpy.path.abspath(filepath or "")).lower()
    if not name:
        return False
    if name == "untitled.blend":
        return True
    if not name.endswith(".blend"):
        return False
    stem = name[:-6]
    return bool(stem.startswith("untitled ") or stem.startswith("untitled_"))


def _is_untitled_tab(tab):
    filepath = str(tab.get("filepath", "")) if isinstance(tab, dict) else getattr(tab, "filepath", "")
    cache_filepath = str(tab.get("cache_filepath", "")) if isinstance(tab, dict) else getattr(tab, "cache_filepath", "")
    title = str(tab.get("title", "")) if isinstance(tab, dict) else getattr(tab, "title", "")
    return _is_untitled_path(filepath) or _is_untitled_path(cache_filepath) or (title or "").lower().startswith("untitled")


def _tab_id_for_thumbnail(filepath):
    tab = _find_tab_by_any_path(filepath)
    if tab and tab.get("tab_id"):
        return tab["tab_id"]
    return ""


def _thumbnail_path_for(filepath, tab_id=""):
    if tab_id:
        return os.path.join(_cache_dir(), "preview_" + _safe_filename_part(tab_id) + ".png")
    resolved_tab_id = _tab_id_for_thumbnail(filepath)
    if resolved_tab_id:
        return os.path.join(_cache_dir(), "preview_" + _safe_filename_part(resolved_tab_id) + ".png")
    name = os.path.basename(bpy.path.abspath(filepath)) or "untitled.blend"
    if name.lower().endswith(".blend"):
        name = name[:-6]
    safe_name = _safe_filename_part(name)
    return os.path.join(_cache_dir(), safe_name + ".preview.png")


def _candidate_thumbnail_paths(tab):
    paths = []
    placeholder = bool(tab.get("thumbnail_placeholder", False)) if isinstance(tab, dict) else bool(getattr(tab, "thumbnail_placeholder", False))
    if placeholder:
        return []
    explicit = str(tab.get("thumbnail_filepath", "")) if isinstance(tab, dict) else getattr(tab, "thumbnail_filepath", "")
    if explicit:
        paths.append(bpy.path.abspath(explicit))
    tab_id = str(tab.get("tab_id", "")) if isinstance(tab, dict) else getattr(tab, "tab_id", "")
    if tab_id:
        paths.append(_thumbnail_path_for("", tab_id=tab_id))
    if _is_untitled_tab(tab):
        return paths
    for key in ("filepath", "cache_filepath"):
        value = str(tab.get(key, "")) if isinstance(tab, dict) else getattr(tab, key, "")
        if value:
            paths.append(_thumbnail_path_for(value))
    unique = []
    seen = set()
    for path in paths:
        abspath = bpy.path.abspath(path)
        if abspath and abspath not in seen:
            seen.add(abspath)
            unique.append(abspath)
    return unique


def _best_thumbnail_for_tab(tab):
    newest_path = ""
    newest_time = -1.0
    for path in _candidate_thumbnail_paths(tab):
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        if mtime > newest_time:
            newest_time = mtime
            newest_path = path
    return newest_path


def _view3d_window_region(area):
    if area is None:
        return None
    try:
        for region in area.regions:
            if region.type == "WINDOW":
                return region
    except (AttributeError, ReferenceError, RuntimeError):
        return None
    return None


def _view3d_areas_sorted(screen=None):
    screen = screen or getattr(bpy.context, "screen", None)
    if not screen:
        return []
    return sorted(
        [area for area in screen.areas if area.type == "VIEW_3D"],
        key=lambda area: (int(getattr(area, "y", 0)), int(getattr(area, "x", 0)), int(getattr(area, "height", 0)), int(getattr(area, "width", 0))),
    )


def _active_capture_area(context=None):
    context = context or bpy.context
    area = getattr(context, "area", None)
    if area is not None and area.type == "VIEW_3D":
        return area
    mx, my = _overlay_mouse_abs
    screen = getattr(context, "screen", None)
    if screen:
        for candidate in screen.areas:
            if candidate.type != "VIEW_3D":
                continue
            region = _view3d_window_region(candidate)
            if region and region.x <= mx <= region.x + region.width and region.y <= my <= region.y + region.height:
                return candidate
    return _primary_view3d_area(context)


def _flatten_gpu_buffer(buffer):
    try:
        values = list(buffer)
    except TypeError:
        return []
    if values and isinstance(values[0], (list, tuple)):
        flat = []
        for item in values:
            flat.extend(item)
        return flat
    return values


def _mesh_projection_bounds(area, region):
    try:
        rv3d = area.spaces.active.region_3d
    except (AttributeError, ReferenceError, RuntimeError):
        return None
    if rv3d is None:
        return None

    xs = []
    ys = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        try:
            if obj.hide_viewport or not obj.visible_get():
                continue
        except Exception:
            if getattr(obj, "hide_viewport", False):
                continue
        for corner in obj.bound_box:
            try:
                world = obj.matrix_world @ mathutils.Vector(corner)
                point = view3d_utils.location_3d_to_region_2d(region, rv3d, world)
            except Exception:
                point = None
            if point is None:
                continue
            xs.append(float(point.x))
            ys.append(float(point.y))

    if not xs or not ys:
        return None
    min_x = max(0.0, min(xs))
    max_x = min(float(region.width), max(xs))
    min_y = max(0.0, min(ys))
    max_y = min(float(region.height), max(ys))
    if max_x - min_x < 4 or max_y - min_y < 4:
        return None

    width = max_x - min_x
    height = max_y - min_y
    pad = max(width, height) * 0.24 + 18.0
    min_x = max(0.0, min_x - pad)
    max_x = min(float(region.width), max_x + pad)
    min_y = max(0.0, min_y - pad)
    max_y = min(float(region.height), max_y + pad)
    return min_x, min_y, max_x, max_y


def _aspect_fit_crop_rect(cx, cy, desired_w, desired_h, max_w, max_h, target_aspect):
    max_w = max(8.0, float(max_w))
    max_h = max(8.0, float(max_h))
    target_aspect = max(0.01, float(target_aspect))
    crop_w = max(8.0, float(desired_w))
    crop_h = max(8.0, float(desired_h))

    if crop_w / max(crop_h, 1.0) > target_aspect:
        crop_h = crop_w / target_aspect
    else:
        crop_w = crop_h * target_aspect

    if crop_w > max_w:
        crop_w = max_w
        crop_h = crop_w / target_aspect
    if crop_h > max_h:
        crop_h = max_h
        crop_w = crop_h * target_aspect

    crop_w = min(max_w, max(8.0, crop_w))
    crop_h = min(max_h, max(8.0, crop_h))
    crop_x = min(max(0.0, cx - crop_w * 0.5), max_w - crop_w)
    crop_y = min(max(0.0, cy - crop_h * 0.5), max_h - crop_h)
    return int(round(crop_x)), int(round(crop_y)), int(round(crop_w)), int(round(crop_h))


def _crop_rect_for_thumbnail(area, region, target_aspect):
    src_w = int(region.width)
    src_h = int(region.height)
    bounds = _mesh_projection_bounds(area, region)
    if bounds:
        min_x, min_y, max_x, max_y = bounds
        return _aspect_fit_crop_rect(
            (min_x + max_x) * 0.5,
            (min_y + max_y) * 0.5,
            max_x - min_x,
            max_y - min_y,
            src_w,
            src_h,
            target_aspect,
        )
    return _aspect_fit_crop_rect(src_w * 0.5, src_h * 0.5, src_w, src_h, src_w, src_h, target_aspect)


def _thumbnail_alpha_for_pixel(r, g, b, edge_r, edge_g, edge_b):
    luminance = r * 0.2126 + g * 0.7152 + b * 0.0722
    bg_distance = math.sqrt((r - edge_r) ** 2 + (g - edge_g) ** 2 + (b - edge_b) ** 2)
    if luminance < 0.18 and bg_distance < 0.18:
        return 0.0
    alpha = min(1.0, max(0.0, (bg_distance - 0.055) / 0.18))
    alpha = max(alpha, min(1.0, max(0.0, (luminance - 0.24) / 0.28)))
    if alpha < 0.16:
        return 0.0
    return alpha



def _composite_pixel_on_thumbnail_background(r, g, b, alpha):
    bg_r, bg_g, bg_b, _bg_a = THUMBNAIL_BACKGROUND
    alpha = min(1.0, max(0.0, alpha))
    return (
        r * alpha + bg_r * (1.0 - alpha),
        g * alpha + bg_g * (1.0 - alpha),
        b * alpha + bg_b * (1.0 - alpha),
        1.0,
    )


def _force_edge_background_to_thumbnail_white(pixels, width, height):
    if not pixels or width <= 0 or height <= 0:
        return

    sample_indices = []
    for x in range(width):
        sample_indices.append(x * 4)
        sample_indices.append(((height - 1) * width + x) * 4)
    for y in range(height):
        sample_indices.append((y * width) * 4)
        sample_indices.append((y * width + width - 1) * 4)

    samples = []
    for index in sample_indices:
        if index + 2 >= len(pixels):
            continue
        r, g, b = pixels[index], pixels[index + 1], pixels[index + 2]
        lum = r * 0.2126 + g * 0.7152 + b * 0.0722
        samples.append((lum, r, g, b))
    if not samples:
        return

    samples.sort(key=lambda item: item[0])
    darkest = samples[:max(1, len(samples) // 4)]
    edge_r = sum(item[1] for item in darkest) / len(darkest)
    edge_g = sum(item[2] for item in darkest) / len(darkest)
    edge_b = sum(item[3] for item in darkest) / len(darkest)
    edge_lum = edge_r * 0.2126 + edge_g * 0.7152 + edge_b * 0.0722
    if edge_lum > 0.55:
        return

    threshold = 0.20 if edge_lum < 0.22 else 0.14
    visited = bytearray(width * height)
    stack = []
    for x in range(width):
        stack.append(x)
        stack.append((height - 1) * width + x)
    for y in range(height):
        stack.append(y * width)
        stack.append(y * width + width - 1)

    bg_r, bg_g, bg_b, bg_a = THUMBNAIL_BACKGROUND
    while stack:
        pixel_index = stack.pop()
        if pixel_index < 0 or pixel_index >= width * height or visited[pixel_index]:
            continue
        visited[pixel_index] = 1
        index = pixel_index * 4
        r, g, b = pixels[index], pixels[index + 1], pixels[index + 2]
        lum = r * 0.2126 + g * 0.7152 + b * 0.0722
        distance = math.sqrt((r - edge_r) ** 2 + (g - edge_g) ** 2 + (b - edge_b) ** 2)
        if distance > threshold or lum > max(0.62, edge_lum + 0.38):
            continue

        pixels[index] = bg_r
        pixels[index + 1] = bg_g
        pixels[index + 2] = bg_b
        pixels[index + 3] = bg_a

        x = pixel_index % width
        y = pixel_index // width
        if x > 0:
            stack.append(pixel_index - 1)
        if x < width - 1:
            stack.append(pixel_index + 1)
        if y > 0:
            stack.append(pixel_index - width)
        if y < height - 1:
            stack.append(pixel_index + width)


def _tag_view3d_redraw(context=None):
    context = context or bpy.context
    screen = getattr(context, "screen", None)
    if not screen:
        return
    for area in screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


def _refresh_view_before_thumbnail(context=None):
    _tag_view3d_redraw(context)
    try:
        bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
    except Exception:
        pass


class _TemporaryOffscreenThumbnailShading:
    def __init__(self, space):
        self.space = space
        self.state = {}

    def __enter__(self):
        shading = getattr(self.space, "shading", None)
        if shading is None:
            return self
        for attr in ("background_type", "background_color", "use_scene_world", "use_scene_world_render"):
            if hasattr(shading, attr):
                self.state[attr] = getattr(shading, attr)
        try:
            shading.background_type = "VIEWPORT"
        except Exception:
            pass
        try:
            shading.background_color = THUMBNAIL_BACKGROUND[:3]
        except Exception:
            pass
        for attr in ("use_scene_world", "use_scene_world_render"):
            if hasattr(shading, attr):
                try:
                    setattr(shading, attr, False)
                except Exception:
                    pass
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        shading = getattr(self.space, "shading", None)
        if shading is not None:
            for attr, value in self.state.items():
                try:
                    setattr(shading, attr, value)
                except Exception:
                    pass
        return False


class _TemporarilyPrepareThumbnailViewport:
    def __enter__(self):
        global _overlay_area_states
        self.was_states = dict(_overlay_area_states)
        self.was_default_state = _overlay_default_state
        self.shading_states = []
        for area in _view3d_areas_sorted(getattr(bpy.context, "screen", None)):
            area_id = _area_id(area)
            if area_id:
                _overlay_area_states[area_id] = "HIDDEN"
        _overlay_hitboxes_by_area.clear()
        _overlay_dock_rects_by_area.clear()
        _overlay_hitboxes.clear()

        screen = getattr(bpy.context, "screen", None)
        if screen:
            for area in screen.areas:
                if area.type != "VIEW_3D":
                    continue
                for space in area.spaces:
                    if space.type != "VIEW_3D":
                        continue
                    shading = getattr(space, "shading", None)
                    if shading is None:
                        continue
                    state = {"shading": shading}
                    for attr in (
                        "background_type",
                        "background_color",
                        "use_scene_world",
                        "use_scene_world_render",
                    ):
                        if hasattr(shading, attr):
                            state[attr] = getattr(shading, attr)
                    self.shading_states.append(state)
                    try:
                        shading.background_type = "VIEWPORT"
                    except Exception:
                        pass
                    try:
                        shading.background_color = THUMBNAIL_BACKGROUND[:3]
                    except Exception:
                        pass
                    for attr in ("use_scene_world", "use_scene_world_render"):
                        if hasattr(shading, attr):
                            try:
                                setattr(shading, attr, False)
                            except Exception:
                                pass
        _refresh_view_before_thumbnail()
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        global _overlay_area_states, _overlay_default_state
        for state in self.shading_states:
            shading = state.get("shading")
            if shading is None:
                continue
            for attr, value in state.items():
                if attr == "shading":
                    continue
                try:
                    setattr(shading, attr, value)
                except Exception:
                    pass
        _overlay_area_states = dict(self.was_states)
        _overlay_default_state = self.was_default_state
        _refresh_view_before_thumbnail()
        return False


def _crop_rendered_preview_to_thumbnail(source_path, target_path):
    if not source_path or not os.path.exists(source_path):
        return ""
    image = None
    out_image = None
    try:
        image = bpy.data.images.load(source_path, check_existing=False)
        src_w = int(image.size[0])
        src_h = int(image.size[1])
        if src_w <= 1 or src_h <= 1:
            return ""
        raw = [0.0] * (src_w * src_h * 4)
        image.pixels.foreach_get(raw)

        target_w = THUMBNAIL_WIDTH * 2
        target_h = THUMBNAIL_HEIGHT * 2
        target_aspect = target_w / target_h
        crop_w = src_w
        crop_h = int(crop_w / target_aspect)
        if crop_h > src_h:
            crop_h = src_h
            crop_w = int(crop_h * target_aspect)
        crop_x = max(0, int((src_w - crop_w) * 0.5))
        crop_y = max(0, int((src_h - crop_h) * 0.5))

        pixels = [0.0] * (target_w * target_h * 4)
        for ty in range(target_h):
            sy = crop_y + min(crop_h - 1, int((ty + 0.5) * crop_h / target_h))
            for tx in range(target_w):
                sx = crop_x + min(crop_w - 1, int((tx + 0.5) * crop_w / target_w))
                src = (sy * src_w + sx) * 4
                dst = (ty * target_w + tx) * 4
                r = raw[src]
                g = raw[src + 1]
                b = raw[src + 2]
                a = raw[src + 3]
                pixels[dst], pixels[dst + 1], pixels[dst + 2], pixels[dst + 3] = _composite_pixel_on_thumbnail_background(r, g, b, a)

        _force_edge_background_to_thumbnail_white(pixels, target_w, target_h)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        out_image = bpy.data.images.new("Multi Blender Bookmark Preview", target_w, target_h, alpha=True)
        out_image.pixels.foreach_set(pixels)
        out_image.filepath_raw = target_path
        out_image.file_format = "PNG"
        out_image.save()
    except Exception:
        return ""
    finally:
        if image is not None:
            try:
                bpy.data.images.remove(image)
            except Exception:
                pass
        if out_image is not None:
            try:
                bpy.data.images.remove(out_image)
            except Exception:
                pass
    return target_path if os.path.exists(target_path) else ""


def _save_view3d_offscreen_thumbnail(filepath):
    area = _active_capture_area(bpy.context)
    region = _view3d_window_region(area)
    if area is None or region is None or region.width <= 8 or region.height <= 8:
        return ""
    try:
        space = area.spaces.active
        rv3d = space.region_3d
    except (AttributeError, ReferenceError, RuntimeError):
        return ""
    if rv3d is None:
        return ""

    src_w = int(region.width)
    src_h = int(region.height)
    target_w = THUMBNAIL_WIDTH * 2
    target_h = THUMBNAIL_HEIGHT * 2
    target_aspect = target_w / target_h
    local_x, local_y, crop_w, crop_h = _crop_rect_for_thumbnail(area, region, target_aspect)
    thumb_path = _thumbnail_path_for(filepath)
    offscreen = None
    image = None

    try:
        offscreen = gpu.types.GPUOffScreen(src_w, src_h)
        with _TemporaryOffscreenThumbnailShading(space):
            with offscreen.bind():
                framebuffer = gpu.state.active_framebuffer_get()
                try:
                    framebuffer.clear(color=THUMBNAIL_BACKGROUND, depth=1.0)
                except Exception:
                    pass
                offscreen.draw_view3d(
                    bpy.context.scene,
                    bpy.context.view_layer,
                    space,
                    region,
                    rv3d.view_matrix,
                    rv3d.window_matrix,
                    do_color_management=True,
                    draw_background=False,
                )
        buffer = offscreen.texture_color.read()
        try:
            buffer.dimensions = src_w * src_h * 4
        except Exception:
            pass
        values = _flatten_gpu_buffer(buffer)
        if len(values) < src_w * src_h * 4:
            return ""

        pixels = [0.0] * (target_w * target_h * 4)
        for ty in range(target_h):
            sy = local_y + min(crop_h - 1, int((ty + 0.5) * crop_h / target_h))
            for tx in range(target_w):
                sx = local_x + min(crop_w - 1, int((tx + 0.5) * crop_w / target_w))
                src = (sy * src_w + sx) * 4
                dst = (ty * target_w + tx) * 4
                pixels[dst] = values[src] / 255.0
                pixels[dst + 1] = values[src + 1] / 255.0
                pixels[dst + 2] = values[src + 2] / 255.0
                pixels[dst + 3] = 1.0

        _force_edge_background_to_thumbnail_white(pixels, target_w, target_h)
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        image = bpy.data.images.new("Multi Blender Bookmark Preview", target_w, target_h, alpha=True)
        image.pixels.foreach_set(pixels)
        image.filepath_raw = thumb_path
        image.file_format = "PNG"
        image.save()
    except Exception:
        return ""
    finally:
        if image is not None:
            try:
                bpy.data.images.remove(image)
            except Exception:
                pass
        if offscreen is not None:
            try:
                offscreen.free()
            except Exception:
                pass

    if os.path.exists(thumb_path):
        _clear_thumbnail_texture(thumb_path)
        tab = _find_tab_by_any_path(filepath)
        if tab:
            _upsert_registry_tab(
                tab["filepath"],
                _title_from_path(tab["filepath"]),
                cache_filepath=tab.get("cache_filepath") or None,
                thumbnail_filepath=thumb_path,
                thumbnail_placeholder=False,
                is_active=True,
            )
        else:
            _upsert_registry_tab(filepath, _title_from_path(filepath), thumbnail_filepath=thumb_path, thumbnail_placeholder=False, is_active=True)
        _sync_registry_to_properties(bpy.context)
        return thumb_path
    return ""


def _render_transparent_view_thumbnail(filepath):
    area = _active_capture_area(bpy.context)
    region = _view3d_window_region(area)
    if area is None or region is None:
        return ""

    thumb_path = _thumbnail_path_for(filepath)
    preview_path = os.path.join(_cache_dir(), "_viewport_preview_tmp.png")
    scene = bpy.context.scene
    render = scene.render
    old_filepath = render.filepath
    old_x = render.resolution_x
    old_y = render.resolution_y
    old_percentage = render.resolution_percentage
    old_film_transparent = getattr(render, "film_transparent", False)
    world = scene.world
    old_world_color = tuple(world.color) if world is not None and hasattr(world, "color") else None

    try:
        render.filepath = preview_path
        render.resolution_x = 480
        render.resolution_y = 360
        render.resolution_percentage = 100
        render.film_transparent = True
        space = area.spaces.active
        if world is not None and hasattr(world, "color"):
            try:
                world.color = THUMBNAIL_BACKGROUND[:3]
            except Exception:
                pass
        override = {
            "window": bpy.context.window,
            "screen": bpy.context.screen,
            "area": area,
            "region": region,
            "space_data": space,
            "scene": scene,
        }
        with bpy.context.temp_override(**override):
            bpy.ops.render.opengl("EXEC_DEFAULT", write_still=True, view_context=True)
        result = _crop_rendered_preview_to_thumbnail(preview_path, thumb_path)
    except Exception:
        result = ""
    finally:
        render.filepath = old_filepath
        render.resolution_x = old_x
        render.resolution_y = old_y
        render.resolution_percentage = old_percentage
        render.film_transparent = old_film_transparent
        if scene.world is not None and old_world_color is not None:
            try:
                scene.world.color = old_world_color
            except Exception:
                pass
        try:
            if os.path.exists(preview_path):
                os.remove(preview_path)
        except OSError:
            pass

    if result:
        _clear_thumbnail_texture(result)
        tab = _find_tab_by_any_path(filepath)
        if tab:
            _upsert_registry_tab(
                tab["filepath"],
                _title_from_path(tab["filepath"]),
                cache_filepath=tab.get("cache_filepath") or None,
                thumbnail_filepath=result,
                thumbnail_placeholder=False,
                is_active=True,
            )
        else:
            _upsert_registry_tab(
                filepath,
                _title_from_path(filepath),
                thumbnail_filepath=result,
                thumbnail_placeholder=False,
                is_active=True,
            )
        _sync_registry_to_properties(bpy.context)
    return result


def _save_view3d_framebuffer_thumbnail(filepath):
    area = _active_capture_area(bpy.context)
    region = _view3d_window_region(area)
    if area is None or region is None or region.width <= 8 or region.height <= 8:
        return ""

    thumb_path = _thumbnail_path_for(filepath)
    target_w = THUMBNAIL_WIDTH * 2
    target_h = THUMBNAIL_HEIGHT * 2
    target_aspect = target_w / target_h
    local_x, local_y, crop_w, crop_h = _crop_rect_for_thumbnail(area, region, target_aspect)
    crop_x = int(region.x + local_x)
    crop_y = int(region.y + local_y)

    try:
        framebuffer = gpu.state.active_framebuffer_get()
        buffer = framebuffer.read_color(crop_x, crop_y, crop_w, crop_h, 4, 0, "UBYTE")
        try:
            buffer.dimensions = crop_w * crop_h * 4
        except Exception:
            pass
        values = _flatten_gpu_buffer(buffer)
        if len(values) < crop_w * crop_h * 4:
            return ""

        pixels = [0.0] * (target_w * target_h * 4)
        for ty in range(target_h):
            sy = min(crop_h - 1, int((ty + 0.5) * crop_h / target_h))
            for tx in range(target_w):
                sx = min(crop_w - 1, int((tx + 0.5) * crop_w / target_w))
                src = (sy * crop_w + sx) * 4
                dst = (ty * target_w + tx) * 4
                r = values[src] / 255.0
                g = values[src + 1] / 255.0
                b = values[src + 2] / 255.0
                pixels[dst], pixels[dst + 1], pixels[dst + 2], pixels[dst + 3] = r, g, b, 1.0

        _force_edge_background_to_thumbnail_white(pixels, target_w, target_h)
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        image = bpy.data.images.new("Multi Blender Bookmark Preview", target_w, target_h, alpha=True)
        image.pixels.foreach_set(pixels)
        image.filepath_raw = thumb_path
        image.file_format = "PNG"
        image.save()
        bpy.data.images.remove(image)
    except Exception:
        return ""

    if os.path.exists(thumb_path):
        _clear_thumbnail_texture(thumb_path)
        return thumb_path
    return ""


def _capture_current_thumbnail(filepath, force=False):
    if bpy.app.background or not filepath:
        return ""
    capture_area = _active_capture_area(bpy.context)
    if not force and _overlay_view_mode(_area_id(capture_area), capture_area) != "THUMBNAILS":
        return ""

    try:
        result = _save_view3d_offscreen_thumbnail(filepath)
        if result:
            return result
    except Exception:
        pass

    with _TemporarilyPrepareThumbnailViewport():
        result = _render_transparent_view_thumbnail(filepath)
        if result:
            return result
        return _save_view3d_framebuffer_thumbnail(filepath)


def _read_registry():
    data = None
    for path in (REGISTRY_PATH, LEGACY_REGISTRY_PATH):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            break
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            continue
    if data is None:
        return {"tabs": []}

    tabs = data.get("tabs")
    if not isinstance(tabs, list):
        return {"tabs": []}
    return {"tabs": tabs}


def _write_registry(data):
    safe_data = {"tabs": data.get("tabs", [])}
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    temp_path = REGISTRY_PATH + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(safe_data, handle, ensure_ascii=False, indent=2)
    os.replace(temp_path, REGISTRY_PATH)


def _read_tabs_file(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return _clean_registry(json.load(handle))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"tabs": []}


def _write_tabs_file(path, data):
    safe_data = _clean_registry(data)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(safe_data, handle, ensure_ascii=False, indent=2)
    os.replace(temp_path, path)


def _tab_key(tab):
    return bpy.path.abspath(tab.get("filepath", ""))


def _existing_target_for_tab(tab):
    cache_path = bpy.path.abspath(tab.get("cache_filepath", "")) if tab.get("cache_filepath", "") else ""
    if cache_path and os.path.exists(cache_path):
        return cache_path
    filepath = bpy.path.abspath(tab.get("filepath", "")) if tab.get("filepath", "") else ""
    return filepath if filepath and os.path.exists(filepath) else ""


def _rounded_float(value, digits=5):
    try:
        return round(float(value), digits)
    except Exception:
        return 0.0


def _sequence_floats(values, digits=5):
    return [_rounded_float(value, digits) for value in values]


def _space_ui_state(space):
    state = {"type": getattr(space, "type", "")}
    if getattr(space, "type", "") == "VIEW_3D":
        region_3d = getattr(space, "region_3d", None)
        if region_3d is not None:
            state["view"] = {
                "distance": _rounded_float(getattr(region_3d, "view_distance", 0.0)),
                "location": _sequence_floats(getattr(region_3d, "view_location", ())),
                "rotation": _sequence_floats(getattr(region_3d, "view_rotation", ())),
                "perspective": getattr(region_3d, "view_perspective", ""),
                "lens": _rounded_float(getattr(space, "lens", 0.0), 3),
                "clip_start": _rounded_float(getattr(space, "clip_start", 0.0), 4),
                "clip_end": _rounded_float(getattr(space, "clip_end", 0.0), 2),
            }
        shading = getattr(space, "shading", None)
        if shading is not None:
            state["shading"] = {
                "type": getattr(shading, "type", ""),
                "light": getattr(shading, "light", ""),
                "studio_light": getattr(shading, "studio_light", ""),
                "background_type": getattr(shading, "background_type", ""),
                "background_color": _sequence_floats(getattr(shading, "background_color", ()), 4),
            }
    return state


def _current_ui_state_hash(context=None):
    context = context or bpy.context
    screen = getattr(context, "screen", None)
    workspace = getattr(context, "workspace", None)
    state = {
        "screen": getattr(screen, "name", ""),
        "workspace": getattr(workspace, "name", ""),
        "areas": [],
    }
    if screen is not None:
        for area in sorted(screen.areas, key=lambda item: (item.y, item.x, item.width, item.height, item.type)):
            area_state = {
                "type": area.type,
                "x": int(getattr(area, "x", 0)),
                "y": int(getattr(area, "y", 0)),
                "width": int(getattr(area, "width", 0)),
                "height": int(getattr(area, "height", 0)),
                "spaces": [],
            }
            try:
                for space in area.spaces:
                    area_state["spaces"].append(_space_ui_state(space))
            except Exception:
                pass
            state["areas"].append(area_state)
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _store_last_closed_tabs(tabs):
    global _last_closed_tabs, _closed_tab_history
    _last_closed_tabs = [_clean_registry({"tabs": [tab]})["tabs"][0] for tab in tabs if tab.get("filepath")]
    if _last_closed_tabs:
        _closed_tab_history.append([dict(tab) for tab in _last_closed_tabs])
        if len(_closed_tab_history) > 100:
            _closed_tab_history = _closed_tab_history[-100:]


def _initialize_new_window_session(context=None):
    global _startup_session_initialized, _last_closed_tabs, _closed_tab_history
    if _startup_session_initialized:
        return
    _startup_session_initialized = True
    _last_closed_tabs = []
    _closed_tab_history = []
    current = _current_blend_filepath()
    if not current:
        current = _first_window_untitled_cache_path()
        try:
            bpy.ops.wm.save_as_mainfile("EXEC_DEFAULT", filepath=current, copy=False, check_existing=False)
        except Exception:
            current = ""
    if current:
        _write_registry({"tabs": [{
            "tab_id": _new_tab_id() if _is_untitled_path(current) else _stable_tab_id_for_paths(current, current),
            "filepath": bpy.path.abspath(current),
            "cache_filepath": bpy.path.abspath(current),
            "thumbnail_filepath": "",
            "thumbnail_placeholder": _is_untitled_path(current),
            "title": _title_from_path(current),
            "is_active": True,
            "updated_at": _now(),
            "ui_state_hash": _current_ui_state_hash(context or bpy.context),
        }]})
    else:
        _write_registry({"tabs": []})
    _sync_registry_to_properties(context or bpy.context)


def _clean_registry(data):
    cleaned = []
    seen = set()
    for tab in data.get("tabs", []):
        filepath = str(tab.get("filepath", ""))
        if not filepath:
            continue
        key = bpy.path.abspath(filepath)
        if key in seen:
            continue
        seen.add(key)

        cache_filepath = str(tab.get("cache_filepath", ""))
        tab_id = str(tab.get("tab_id", "")) or _stable_tab_id_for_paths(filepath, cache_filepath)
        cleaned.append({
            "tab_id": tab_id,
            "filepath": filepath,
            "cache_filepath": cache_filepath,
            "thumbnail_filepath": str(tab.get("thumbnail_filepath", "")),
            "thumbnail_placeholder": bool(tab.get("thumbnail_placeholder", False)),
            "title": str(tab.get("title", "")) or _title_from_path(filepath),
            "is_active": bool(tab.get("is_active", False)),
            "updated_at": float(tab.get("updated_at", _now())),
            "ui_state_hash": str(tab.get("ui_state_hash", "")),
        })
    return {"tabs": cleaned}


def _set_active_in_registry(filepath):
    target = bpy.path.abspath(filepath) if filepath else ""
    data = _clean_registry(_read_registry())
    for tab in data["tabs"]:
        tab_path = bpy.path.abspath(tab["filepath"])
        tab["is_active"] = bool(target and tab_path == target)
        tab["updated_at"] = _now()
    _write_registry(data)


def _upsert_registry_tab(
    filepath,
    title=None,
    cache_filepath=None,
    thumbnail_filepath=None,
    is_active=False,
    ui_state_hash=None,
    tab_id=None,
    thumbnail_placeholder=None,
):
    filepath = bpy.path.abspath(filepath) if filepath else ""
    if not filepath:
        return

    data = _clean_registry(_read_registry())
    found = False

    for tab in data["tabs"]:
        if bpy.path.abspath(tab["filepath"]) == filepath:
            tab["filepath"] = filepath
            if tab_id:
                tab["tab_id"] = tab_id
            tab["title"] = title or _title_from_path(filepath)
            if cache_filepath is not None:
                tab["cache_filepath"] = cache_filepath
            if thumbnail_filepath is not None:
                tab["thumbnail_filepath"] = thumbnail_filepath
                tab["thumbnail_placeholder"] = False
            if thumbnail_placeholder is not None:
                tab["thumbnail_placeholder"] = bool(thumbnail_placeholder)
                if thumbnail_placeholder:
                    tab["thumbnail_filepath"] = ""
            if ui_state_hash is not None:
                tab["ui_state_hash"] = ui_state_hash
            tab["is_active"] = bool(is_active)
            tab["updated_at"] = _now()
            found = True
            break

    if not found:
        new_tab_id = tab_id or _new_tab_id()
        data["tabs"].append({
            "tab_id": new_tab_id,
            "filepath": filepath,
            "cache_filepath": cache_filepath or "",
            "thumbnail_filepath": "" if thumbnail_placeholder else (thumbnail_filepath or ""),
            "thumbnail_placeholder": bool(thumbnail_placeholder) if thumbnail_placeholder is not None else False,
            "title": title or _title_from_path(filepath),
            "is_active": bool(is_active),
            "updated_at": _now(),
            "ui_state_hash": ui_state_hash or "",
        })

    if is_active:
        for tab in data["tabs"]:
            tab["is_active"] = bpy.path.abspath(tab["filepath"]) == filepath

    _write_registry(data)


def _remove_registry_tab(filepath):
    target = bpy.path.abspath(filepath) if filepath else ""
    data = _clean_registry(_read_registry())
    data["tabs"] = [tab for tab in data["tabs"] if bpy.path.abspath(tab["filepath"]) != target]
    _write_registry(data)


def _find_tab_by_any_path(filepath):
    target = bpy.path.abspath(filepath) if filepath else ""
    if not target:
        return None
    for tab in _clean_registry(_read_registry())["tabs"]:
        paths = [tab["filepath"], tab.get("cache_filepath", "")]
        for path in paths:
            if path and bpy.path.abspath(path) == target:
                return tab
    return None


def _active_registry_tab():
    for tab in _clean_registry(_read_registry())["tabs"]:
        if bool(tab.get("is_active", False)):
            return tab
    return None


def _next_untitled_cache_path():
    data = _clean_registry(_read_registry())
    used = set()
    for tab in data["tabs"]:
        for path in (tab.get("filepath", ""), tab.get("cache_filepath", "")):
            if path:
                used.add(bpy.path.abspath(path))

    first_path = os.path.join(_cache_dir(), "Untitled.blend")
    if bpy.path.abspath(first_path) not in used:
        return first_path

    for index in range(1, 1000):
        name = f"Untitled_{index:02d}.blend"
        path = os.path.join(_cache_dir(), name)
        if bpy.path.abspath(path) not in used:
            return path
    return os.path.join(_cache_dir(), f"Untitled_{int(_now())}.blend")


def _first_window_untitled_cache_path():
    return os.path.join(_cache_dir(), "Untitled.blend")


def _save_current_project_to_cache(force=False, capture_thumbnail=False):
    current = _current_blend_filepath()
    active_tab = _active_registry_tab()
    if not current and not active_tab:
        return ""

    tab = _find_tab_by_any_path(current)
    if tab is None and active_tab:
        tab = active_tab
    original = tab["filepath"] if tab else current
    cache_path = _cache_path_for(original)
    if tab and tab.get("cache_filepath") and bpy.path.abspath(tab["filepath"]) == bpy.path.abspath(tab["cache_filepath"]):
        cache_path = bpy.path.abspath(tab["cache_filepath"])

    ui_state_hash = _current_ui_state_hash(bpy.context)
    ui_dirty = bool(tab and ui_state_hash and ui_state_hash != tab.get("ui_state_hash", ""))
    thumbnail_path = _capture_current_thumbnail(original, force=True) if capture_thumbnail else ""

    if not force and not _is_current_file_dirty() and not ui_dirty:
        if thumbnail_path:
            _upsert_registry_tab(
                original,
                _title_from_path(original),
                cache_filepath=bpy.path.abspath(tab["cache_filepath"]) if tab and tab.get("cache_filepath") else None,
                thumbnail_filepath=thumbnail_path,
                thumbnail_placeholder=False,
                ui_state_hash=ui_state_hash,
                is_active=True,
            )
        if tab and tab.get("cache_filepath"):
            return bpy.path.abspath(tab["cache_filepath"])
        return ""

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    # copy=True keeps bpy.data.filepath pointing at the current file/cache. It
    # writes an overwriteable cache copy without changing the user's original.
    bpy.ops.wm.save_as_mainfile(
        "EXEC_DEFAULT",
        filepath=cache_path,
        copy=True,
        check_existing=False,
    )
    _upsert_registry_tab(
        original,
        _title_from_path(original),
        cache_filepath=cache_path,
        thumbnail_filepath=thumbnail_path if thumbnail_path else None,
        thumbnail_placeholder=False if thumbnail_path else None,
        ui_state_hash=ui_state_hash,
        is_active=True,
    )
    _sync_registry_to_properties(bpy.context)
    return cache_path


def _bookmark_target_path_from_tab(tab):
    cache_path = tab.get("cache_filepath", "") or ""
    if cache_path and os.path.exists(bpy.path.abspath(cache_path)):
        return bpy.path.abspath(cache_path)
    return bpy.path.abspath(tab.get("filepath", ""))


def _open_registry_tab(tab):
    target = _bookmark_target_path_from_tab(tab)
    if not target or not os.path.exists(target):
        return {"CANCELLED"}
    _set_active_in_registry(tab["filepath"])
    return _open_mainfile_current_window(target)


def _next_remaining_tab_after_close(tabs, closing_indices, active_index):
    if not tabs:
        return None
    closing = set(closing_indices)
    remaining_indices = [index for index in range(len(tabs)) if index not in closing]
    if not remaining_indices:
        return None
    if active_index < 0:
        active_index = 0
    for offset in range(1, len(tabs) + 1):
        candidate = (active_index + offset) % len(tabs)
        if candidate not in closing:
            return tabs[candidate]
    return tabs[remaining_indices[0]]


def _write_tabs_after_close(context, tabs_to_close, fallback_tab=None):
    closing_paths = {bpy.path.abspath(tab["filepath"]) for tab in tabs_to_close if tab.get("filepath")}
    data = _clean_registry(_read_registry())
    data["tabs"] = [tab for tab in data["tabs"] if bpy.path.abspath(tab["filepath"]) not in closing_paths]
    if fallback_tab and data["tabs"]:
        fallback_path = bpy.path.abspath(fallback_tab["filepath"])
        for tab in data["tabs"]:
            tab["is_active"] = bpy.path.abspath(tab["filepath"]) == fallback_path
    _write_registry(data)
    _sync_registry_to_properties(context)
    _prune_selection(len(context.window_manager.mbb_bookmarks))


def _bookmark_target_path(bookmark):
    cache_path = getattr(bookmark, "cache_filepath", "") or ""
    if cache_path and os.path.exists(bpy.path.abspath(cache_path)):
        return bpy.path.abspath(cache_path)
    return bpy.path.abspath(bookmark.filepath)


def _create_untitled_bookmark(context=None, save_current=True):
    if save_current:
        _save_current_project_to_cache(capture_thumbnail=True)

    context = context or bpy.context
    cache_path = _next_untitled_cache_path()
    bpy.ops.wm.read_homefile(
        "EXEC_DEFAULT",
        load_ui=True,
        use_splash=False,
        use_empty=False,
    )
    bpy.ops.wm.save_as_mainfile(
        "EXEC_DEFAULT",
        filepath=cache_path,
        copy=False,
        check_existing=False,
    )
    _upsert_registry_tab(
        cache_path,
        _title_from_path(cache_path),
        cache_filepath=cache_path,
        tab_id=_new_tab_id(),
        thumbnail_placeholder=True,
        ui_state_hash=_current_ui_state_hash(context),
        is_active=True,
    )
    _sync_registry_to_properties(context)
    return cache_path


def _register_current_process_tab(is_active=True):
    filepath = _current_blend_filepath()
    if not filepath:
        return

    tab = _find_tab_by_any_path(filepath)
    if tab:
        _upsert_registry_tab(
            tab["filepath"],
            tab.get("title") or _title_from_path(tab["filepath"]),
            cache_filepath=tab.get("cache_filepath") or None,
            thumbnail_filepath=tab.get("thumbnail_filepath") or None,
            tab_id=tab.get("tab_id") or None,
            thumbnail_placeholder=tab.get("thumbnail_placeholder", None),
            ui_state_hash=_current_ui_state_hash(bpy.context),
            is_active=is_active,
        )
        return

    _upsert_registry_tab(filepath, _title_from_path(filepath), ui_state_hash=_current_ui_state_hash(bpy.context), is_active=is_active)


def _sync_registry_to_properties(context):
    wm = _window_manager_from_context(context)
    if wm is None or not hasattr(wm, "mbb_bookmarks"):
        return

    data = _clean_registry(_read_registry())
    wm.mbb_bookmarks.clear()
    for tab_data in data["tabs"]:
        tab = wm.mbb_bookmarks.add()
        tab.tab_id = tab_data.get("tab_id", "")
        tab.filepath = tab_data["filepath"]
        tab.cache_filepath = tab_data.get("cache_filepath", "")
        tab.thumbnail_filepath = tab_data.get("thumbnail_filepath", "")
        tab.thumbnail_placeholder = bool(tab_data.get("thumbnail_placeholder", False))
        tab.title = tab_data["title"]
        tab.is_active = bool(tab_data["is_active"])
    _prune_selection(len(wm.mbb_bookmarks))


class MBB_BookmarkItem(bpy.types.PropertyGroup):
    tab_id: StringProperty(
        name="Tab ID",
        description="Internal stable ID used to keep generated previews separate",
    )
    filepath: StringProperty(
        name="Original File Path",
        subtype="FILE_PATH",
        description="Original .blend file represented by this bookmark",
    )
    cache_filepath: StringProperty(
        name="Cache File Path",
        subtype="FILE_PATH",
        description="Cached .blend file used to preserve unsaved edits",
    )
    thumbnail_filepath: StringProperty(
        name="Thumbnail File Path",
        subtype="FILE_PATH",
        description="Preview image for the latest cached project state",
    )
    thumbnail_placeholder: BoolProperty(
        name="Use Placeholder Thumbnail",
        description="Use the default placeholder instead of falling back to stale preview files",
    )
    title: StringProperty(
        name="Title",
        description="Bookmark display title",
    )
    is_active: BoolProperty(
        name="Is Active",
        description="Whether this bookmark is currently marked active",
    )


class MBB_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_MODULE

    dock_top_offset: IntProperty(
        name="Dock Top Offset",
        description="Distance between the top of the 3D View and the bookmark dock",
        default=OVERLAY_TOP_OFFSET,
        min=0,
        max=120,
    )
    dock_ui_scale: FloatProperty(
        name="Dock UI Scale",
        description="Scale of the floating bookmark dock",
        default=1.0,
        min=0.8,
        max=1.6,
        precision=2,
    )
    cache_directory: StringProperty(
        name="Cache Folder",
        description="Folder for cached .blend files and bookmark thumbnails",
        default=DEFAULT_CACHE_DIR,
        subtype="DIR_PATH",
    )

    def draw(self, context):
        layout = self.layout
        intro = layout.column(align=True)
        intro.label(text="Dock栏位于3D View窗口顶部，可通过书签Icon或Toggle Bar快捷键开闭。")
        intro.label(text="Dock bar sits atop the 3D View and toggles via the bookmark icon or Toggle Bar shortcut.")
        self.draw_control_pair(layout)
        self.draw_cache_and_toggle_pair(layout)
        targets = list(SHORTCUT_TARGETS)
        for offset in range(0, len(targets), 2):
            self.draw_shortcut_pair(layout, targets[offset], targets[offset + 1] if offset + 1 < len(targets) else "")

    def draw_control_pair(self, layout):
        row = layout.row(align=True)
        left_col = row.column(align=True)
        self.draw_control_cell(left_col, "TRIA_UP", "Dock Height", "dock_top_offset")
        row.separator(factor=1.6)
        right_col = row.column(align=True)
        self.draw_control_cell(right_col, "FULLSCREEN_ENTER", "Dock Scale", "dock_ui_scale")

    def draw_control_cell(self, layout, icon, label_text, prop_name):
        cell = layout.split(factor=0.48, align=True)
        label_area = cell.row(align=True)
        label_area.label(text="", icon=icon)
        label_area.separator(factor=0.35)
        label_area.label(text=label_text)
        control_area = cell.row(align=True)
        control_area.prop(self, prop_name, text="", slider=True)

    def draw_cache_and_toggle_pair(self, layout):
        row = layout.row(align=True)
        left_col = row.column(align=True)
        self.draw_cache_cell(left_col)
        row.separator(factor=1.6)
        right_col = row.column(align=True)
        self.draw_toggle_shortcut_cell(right_col)

    def draw_cache_cell(self, layout):
        cell = layout.split(factor=0.48, align=True)
        label_area = cell.row(align=True)
        label_area.label(text="", icon="FILE_FOLDER")
        label_area.separator(factor=0.35)
        label_area.label(text="Cache Folder")
        control_area = cell.row(align=True)
        control_area.prop(self, "cache_directory", text="")

    def draw_toggle_shortcut_cell(self, layout):
        self.draw_shortcut_row(layout, "shortcut_toggle_bar")

    def draw_shortcut_pair(self, layout, left_target, right_target):
        row = layout.row(align=True)
        left_col = row.column(align=True)
        self.draw_shortcut_row(left_col, left_target)
        row.separator(factor=1.6)
        right_col = row.column(align=True)
        if right_target:
            self.draw_shortcut_row(right_col, right_target)
        else:
            empty = right_col.row(align=True)
            empty.label(text="")

    def draw_shortcut_row(self, layout, target):
        _kc, _km, kmi = _keymap_item_for_target(target)
        cell = layout.split(factor=0.48, align=True)
        label_area = cell.row(align=True)
        if kmi is None:
            label_area.label(text="", icon="ERROR")
            label_area.separator(factor=0.35)
            label_area.label(text=f"{SHORTCUT_TARGET_LABELS[target]}: shortcut not found")
            control_area = cell.row(align=True)
            control_area.label(text="Restart Blender")
            return
        label_area.prop(kmi, "active", text="")
        label_area.separator(factor=0.35)
        label_area.label(text=SHORTCUT_TARGET_LABELS[target])
        control_area = cell.row(align=True)
        control_area.prop(kmi, "type", text="", full_event=True)

def _clean_overlay_state(state, fallback="NAMES"):
    state = str(state or "").upper()
    return state if state in OVERLAY_STATES else fallback


def _read_overlay_state_file():
    try:
        with open(OVERLAY_STATE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"default_state": "NAMES", "area_states": []}
    area_states = data.get("area_states", [])
    if not isinstance(area_states, list):
        area_states = []
    return {
        "default_state": _clean_overlay_state(data.get("default_state", "NAMES")),
        "area_states": [_clean_overlay_state(state) for state in area_states],
    }


def _write_overlay_state_file(data):
    safe_data = {
        "default_state": _clean_overlay_state(data.get("default_state", "NAMES")),
        "area_states": [_clean_overlay_state(state) for state in data.get("area_states", [])],
        "updated_at": _now(),
    }
    try:
        os.makedirs(os.path.dirname(OVERLAY_STATE_PATH), exist_ok=True)
        temp_path = OVERLAY_STATE_PATH + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(safe_data, handle, ensure_ascii=False, indent=2)
        os.replace(temp_path, OVERLAY_STATE_PATH)
    except OSError:
        pass


def _initialize_overlay_state_from_disk(context=None):
    global _overlay_default_state, _overlay_saved_area_states, _overlay_area_states, _overlay_area_previous_modes, _overlay_view_mode_state
    data = _read_overlay_state_file()
    _overlay_default_state = _clean_overlay_state(data.get("default_state", "NAMES"))
    _overlay_saved_area_states = [_clean_overlay_state(state) for state in data.get("area_states", [])]
    _overlay_area_states.clear()
    _overlay_area_previous_modes.clear()
    for index, area in enumerate(_view3d_areas_sorted(getattr(context or bpy.context, "screen", None))):
        area_id = _area_id(area)
        if not area_id:
            continue
        state = _overlay_saved_area_states[index] if index < len(_overlay_saved_area_states) else _overlay_default_state
        _overlay_area_states[area_id] = _clean_overlay_state(state)
        if _overlay_area_states[area_id] in VISIBLE_OVERLAY_STATES:
            _overlay_area_previous_modes[area_id] = _overlay_area_states[area_id]
    _overlay_view_mode_state = "THUMBNAILS" if _overlay_default_state == "THUMBNAILS" else "NAMES"


def _overlay_state_for_area(area=None, area_id=""):
    area = area or getattr(bpy.context, "area", None)
    area_id = area_id or _area_id(area)
    if not area_id:
        return _overlay_default_state
    if area_id not in _overlay_area_states:
        state = _overlay_default_state
        sorted_areas = _view3d_areas_sorted(getattr(bpy.context, "screen", None))
        for index, candidate in enumerate(sorted_areas):
            if _area_id(candidate) == area_id:
                if index < len(_overlay_saved_area_states):
                    state = _overlay_saved_area_states[index]
                break
        _overlay_area_states[area_id] = _clean_overlay_state(state)
        if _overlay_area_states[area_id] in VISIBLE_OVERLAY_STATES:
            _overlay_area_previous_modes[area_id] = _overlay_area_states[area_id]
    return _overlay_area_states[area_id]


def _overlay_view_mode(area_id="", area=None):
    state = _overlay_state_for_area(area, area_id)
    return "THUMBNAILS" if state == "THUMBNAILS" else "NAMES"


def _persist_overlay_state(context=None):
    global _overlay_default_state
    screen = getattr(context or bpy.context, "screen", None)
    area_states = []
    for area in _view3d_areas_sorted(screen):
        area_id = _area_id(area)
        if not area_id:
            continue
        area_states.append(_overlay_state_for_area(area, area_id))
    if area_states:
        active_area = getattr(context or bpy.context, "area", None)
        active_state = _overlay_state_for_area(active_area) if active_area and active_area.type == "VIEW_3D" else area_states[0]
        _overlay_default_state = active_state
    _write_overlay_state_file({"default_state": _overlay_default_state, "area_states": area_states})


def _set_overlay_area_state(area_id, state, context=None):
    global _overlay_default_state, _overlay_view_mode_state
    state = _clean_overlay_state(state)
    if area_id:
        _overlay_area_states[area_id] = state
        if state in VISIBLE_OVERLAY_STATES:
            _overlay_area_previous_modes[area_id] = state
    _overlay_default_state = state
    _overlay_view_mode_state = "THUMBNAILS" if state == "THUMBNAILS" else "NAMES"
    _persist_overlay_state(context)


def _toggle_overlay_area(area_id, context=None):
    current = _overlay_state_for_area(area_id=area_id)
    if current == "HIDDEN":
        next_state = _overlay_area_previous_modes.get(area_id, "NAMES")
    else:
        _overlay_area_previous_modes[area_id] = current
        next_state = "HIDDEN"
    _set_overlay_area_state(area_id, next_state, context)


def _show_view3d_tab_bar():
    return True


def _addon_preferences():
    addon = bpy.context.preferences.addons.get(ADDON_MODULE)
    return addon.preferences if addon else None


def _dock_top_offset():
    prefs = _addon_preferences()
    if prefs and hasattr(prefs, "dock_top_offset"):
        return max(0, min(120, int(prefs.dock_top_offset)))
    return OVERLAY_TOP_OFFSET


def _dock_ui_scale():
    prefs = _addon_preferences()
    if prefs and hasattr(prefs, "dock_ui_scale"):
        return max(0.8, min(1.6, float(prefs.dock_ui_scale)))
    return 1.0


def _scaled(value):
    return value * _dock_ui_scale()


def _shortcut_value(prop_name):
    return _normalize_shortcut(SHORTCUT_DEFAULTS.get(prop_name, ""))


def _open_mainfile_current_window(filepath):
    # load_ui=True is intentional: every .blend owns its saved Workspaces,
    # screens, editor split layout, and UI state. Keeping it False would force
    # all projects to inherit the currently visible Blender page layout.
    return bpy.ops.wm.open_mainfile(
        "EXEC_DEFAULT",
        filepath=filepath,
        load_ui=True,
        display_file_selector=False,
    )


def _is_current_file_dirty():
    try:
        return bool(getattr(bpy.data, "is_dirty", False))
    except (AttributeError, ReferenceError, RuntimeError):
        return False


def _current_ui_state_is_dirty(tab=None):
    tab = tab or _active_registry_tab()
    if not tab:
        return False
    try:
        current_hash = _current_ui_state_hash(bpy.context)
    except Exception:
        return False
    return bool(current_hash and current_hash != tab.get("ui_state_hash", ""))


def _defer_ui_action(action):
    if bpy.app.background:
        action()
        return
    def _run_action():
        try:
            action()
        except Exception as exc:
            print(f"Multi Blender Bookmark deferred action failed: {exc}")
        return None
    try:
        bpy.app.timers.register(_run_action, first_interval=0.01)
    except ValueError:
        action()


def _restore_closed_or_new_impl(context):
    global _last_closed_tabs
    restored = []
    data = _clean_registry(_read_registry())

    while _closed_tab_history and not restored:
        closed_tabs = _closed_tab_history.pop()
        _last_closed_tabs = [dict(tab) for tab in closed_tabs]
        data = _clean_registry(_read_registry())
        existing = {bpy.path.abspath(tab["filepath"]) for tab in data["tabs"]}
        for tab in closed_tabs:
            key = bpy.path.abspath(tab.get("filepath", ""))
            if not key or key in existing:
                continue
            if not _existing_target_for_tab(tab):
                continue
            tab = dict(tab)
            tab["is_active"] = False
            data["tabs"].append(tab)
            existing.add(key)
            restored.append(tab)

    if not restored:
        _last_closed_tabs = []
        return bpy.ops.wm.mbb_new_blend()

    active_tab = restored[-1]
    active_key = bpy.path.abspath(active_tab["filepath"])
    for tab in data["tabs"]:
        tab["is_active"] = bpy.path.abspath(tab["filepath"]) == active_key
    _write_registry(data)
    _sync_registry_to_properties(context)
    _set_single_selection(len(data["tabs"]) - 1)
    return _open_registry_tab(active_tab)


def _execute_or_defer(action):
    if bpy.app.background:
        return action()
    _defer_ui_action(action)
    return {"FINISHED"}


class MBB_OT_open_blend_bookmark(bpy.types.Operator):
    bl_idname = "wm.mbb_open_blend"
    bl_label = "Open Blend Bookmark"
    bl_description = "Open a .blend file in this Blender window and add it as a tab"
    bl_options = {"REGISTER"}

    filepath: StringProperty(name="File Path", subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.blend", options={"HIDDEN"})

    def invoke(self, context, _event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        filepath = bpy.path.abspath(self.filepath)
        if not filepath:
            self.report({"ERROR"}, "No .blend file selected.")
            return {"CANCELLED"}
        if not filepath.lower().endswith(".blend"):
            self.report({"ERROR"}, "Please select a .blend file.")
            return {"CANCELLED"}

        _save_current_project_to_cache(capture_thumbnail=True)
        _upsert_registry_tab(filepath, _title_from_path(filepath), is_active=True)
        return _open_mainfile_current_window(filepath)


class MBB_OT_new_blend_bookmark(bpy.types.Operator):
    bl_idname = "wm.mbb_new_blend"
    bl_label = "New Blend Bookmark"
    bl_description = "Create a new unnamed Blender project tab in this window"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        return _execute_or_defer(lambda: (_create_untitled_bookmark(bpy.context, save_current=True), {"FINISHED"})[1])


class MBB_OT_open_bookmark(bpy.types.Operator):
    bl_idname = "wm.mbb_open_bookmark"
    bl_label = "Open Bookmark"
    bl_description = "Switch to this cached .blend bookmark in the current Blender window"
    bl_options = {"INTERNAL"}

    index: StringProperty(name="Bookmark Index", default="-1")

    def _bookmark(self, context):
        wm = context.window_manager
        try:
            index = int(self.index)
        except ValueError:
            return None
        if index < 0 or index >= len(wm.mbb_bookmarks):
            return None
        return wm.mbb_bookmarks[index]

    def invoke(self, context, event):
        bookmark = self._bookmark(context)
        if bookmark is None:
            self.report({"ERROR"}, "Bookmark index is invalid.")
            return {"CANCELLED"}

        current = bpy.path.abspath(_current_blend_filepath()) if _current_blend_filepath() else ""
        target = _bookmark_target_path(bookmark)
        if target and current != target and _is_current_file_dirty():
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)

    def execute(self, context):
        bookmark = self._bookmark(context)
        if bookmark is None:
            self.report({"ERROR"}, "Bookmark index is invalid.")
            return {"CANCELLED"}
        if not bookmark.filepath:
            self.report({"ERROR"}, "This bookmark has no file path.")
            return {"CANCELLED"}

        target = _bookmark_target_path(bookmark)
        if not os.path.exists(target):
            self.report({"ERROR"}, f"File does not exist: {target}")
            return {"CANCELLED"}

        current = bpy.path.abspath(_current_blend_filepath()) if _current_blend_filepath() else ""
        if current == target:
            _set_active_in_registry(bookmark.filepath)
            _sync_registry_to_properties(context)
            self.report({"INFO"}, "Bookmark is already open.")
            return {"FINISHED"}

        _save_current_project_to_cache(capture_thumbnail=True)
        _set_active_in_registry(bookmark.filepath)
        return _open_mainfile_current_window(target)


class MBB_OT_remove_bookmark(bpy.types.Operator):
    bl_idname = "wm.mbb_remove_bookmark"
    bl_label = "Remove Bookmark"
    bl_description = "Remove this tab; cached files are left in Blender's cache directory"
    bl_options = {"INTERNAL"}

    index: StringProperty(name="Bookmark Index", default="-1")

    def execute(self, context):
        wm = context.window_manager
        try:
            index = int(self.index)
        except ValueError:
            index = -1
        if index < 0 or index >= len(wm.mbb_bookmarks):
            self.report({"ERROR"}, "Bookmark index is invalid.")
            return {"CANCELLED"}

        data = _clean_registry(_read_registry())
        tabs = data["tabs"]
        if index >= len(tabs):
            self.report({"ERROR"}, "Bookmark index is invalid.")
            return {"CANCELLED"}

        closing_tab = tabs[index]
        _store_last_closed_tabs([closing_tab])
        active_index = _active_bookmark_index(context)
        fallback_tab = _next_remaining_tab_after_close(tabs, {index}, active_index)
        active_closed = index == active_index

        if fallback_tab is None:
            _create_untitled_bookmark(context, save_current=False)
        elif active_closed:
            result = _open_registry_tab(fallback_tab)
            if result == {"CANCELLED"}:
                self.report({"ERROR"}, "Could not switch to the next bookmark before closing.")
                return {"CANCELLED"}

        _write_tabs_after_close(context, [closing_tab], fallback_tab if active_closed else None)
        _selected_bookmark_indices.clear()
        global _selection_anchor_index
        _selection_anchor_index = -1
        self.report({"INFO"}, "Removed bookmark tab.")
        return {"FINISHED"}


class MBB_OT_restore_closed_or_new(bpy.types.Operator):
    bl_idname = "wm.mbb_restore_closed_or_new"
    bl_label = "Reopen Closed Bookmark or New"
    bl_description = "Reopen tabs from the last close action, or create a new project if nothing was closed in this window"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        return _execute_or_defer(lambda: _restore_closed_or_new_impl(bpy.context))


class MBB_OT_toggle_area_tab_bar(bpy.types.Operator):
    bl_idname = "wm.mbb_toggle_area_tab_bar"
    bl_label = "Toggle Bookmark Bar"
    bl_description = "Show or hide the Multi Blender Bookmark floating tab bar for this 3D View"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        area = getattr(context, "area", None)
        if area is None or area.type != "VIEW_3D":
            area = _primary_view3d_area(context)
        area_id = _area_id(area)
        if not area_id:
            self.report({"WARNING"}, "No 3D View area is available.")
            return {"CANCELLED"}

        _toggle_overlay_area(area_id, context)
        _overlay_hitboxes_by_area.clear()
        screen = getattr(context, "screen", None)
        if screen:
            for redraw_area in screen.areas:
                if redraw_area.type == "VIEW_3D":
                    redraw_area.tag_redraw()
        return {"FINISHED"}


class MBB_OT_set_view_mode(bpy.types.Operator):
    bl_idname = "wm.mbb_set_view_mode"
    bl_label = "Set Bookmark View Mode"
    bl_description = "Switch the floating bookmark bar between file-name and thumbnail views"
    bl_options = {"INTERNAL"}

    mode: StringProperty(name="Mode", default="NAMES")

    def execute(self, context):
        mode = self.mode if self.mode in {"NAMES", "THUMBNAILS"} else "NAMES"
        area = getattr(context, "area", None)
        if area is None or area.type != "VIEW_3D":
            area = _primary_view3d_area(context)
        area_id = _area_id(area)
        if not area_id:
            return {"CANCELLED"}
        _set_overlay_area_state(area_id, mode, context)
        if hasattr(context.window_manager, "mbb_view_mode"):
            context.window_manager.mbb_view_mode = mode
        screen = getattr(context, "screen", None)
        if screen:
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
        return {"FINISHED"}


class MBB_OT_close_active_bookmark(bpy.types.Operator):
    bl_idname = "wm.mbb_close_active_bookmark"
    bl_label = "Close Active Bookmark"
    bl_description = "Close the active or selected bookmark tabs"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        return _execute_or_defer(lambda: _close_active_bookmark(bpy.context))


class MBB_OT_next_bookmark(bpy.types.Operator):
    bl_idname = "wm.mbb_next_bookmark"
    bl_label = "Next Bookmark"
    bl_description = "Switch to the next bookmark tab"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        return _execute_or_defer(lambda: _switch_bookmark_relative(bpy.context, 1))


class MBB_OT_prev_bookmark(bpy.types.Operator):
    bl_idname = "wm.mbb_prev_bookmark"
    bl_label = "Previous Bookmark"
    bl_description = "Switch to the previous bookmark tab"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        return _execute_or_defer(lambda: _switch_bookmark_relative(bpy.context, -1))


class MBB_OT_dock_shortcut(bpy.types.Operator):
    bl_idname = DOCK_SHORTCUT_OPERATOR_ID
    bl_label = "Multi Files Bookmark Dock Shortcut"
    bl_options = {"INTERNAL"}

    target: EnumProperty(
        name="Dock Shortcut",
        items=tuple((target, SHORTCUT_TARGET_LABELS[target], "") for target in SHORTCUT_TARGETS),
    )

    @classmethod
    def poll(cls, _context):
        return bpy.app.background or _mouse_over_any_dock()

    def execute(self, _context):
        if self.target == "shortcut_restore_closed":
            return _execute_or_defer(lambda: bpy.ops.wm.mbb_restore_closed_or_new())
        if self.target == "shortcut_close":
            return _execute_or_defer(lambda: _close_active_bookmark(bpy.context))
        if self.target == "shortcut_next":
            return _execute_or_defer(lambda: _switch_bookmark_relative(bpy.context, 1))
        if self.target == "shortcut_prev":
            return _execute_or_defer(lambda: _switch_bookmark_relative(bpy.context, -1))
        return {"CANCELLED"}


def _draw_poly(points, color):
    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    batch = batch_for_shader(shader, "TRIS", {"pos": points})
    gpu.state.blend_set("ALPHA")
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set("NONE")


def _sdf_viewport_size():
    try:
        viewport = gpu.state.viewport_get()
        return float(viewport[2]), float(viewport[3])
    except Exception:
        return None


# The 3D View Dock is drawn in POST_PIXEL. Rounded UI shapes are evaluated as
# signed-distance fields in the fragment shader, using smoothstep at the edge
# instead of polygonal arc tessellation. This keeps capsules, circles, and
# icon strokes crisp at small sizes.
def _get_sdf_round_rect_shader():
    global _sdf_round_rect_shader, _sdf_shader_warning_printed
    if _sdf_round_rect_shader is not None:
        return _sdf_round_rect_shader
    try:
        iface = gpu.types.GPUStageInterfaceInfo("mbb_sdf_round_rect_iface")
        iface.smooth("VEC2", "localCoord")
        info = gpu.types.GPUShaderCreateInfo()
        info.push_constant("VEC2", "uViewportSize")
        info.push_constant("VEC2", "uSize")
        info.push_constant("FLOAT", "uRadius")
        info.push_constant("FLOAT", "uPad")
        info.push_constant("FLOAT", "uBorderWidth")
        info.push_constant("FLOAT", "uAA")
        info.push_constant("VEC4", "uFillColor")
        info.push_constant("VEC4", "uBorderColor")
        info.vertex_in(0, "VEC2", "pos")
        info.vertex_in(1, "VEC2", "local")
        info.vertex_out(iface)
        info.fragment_out(0, "VEC4", "FragColor")
        info.vertex_source(
            """
            void main()
            {
                localCoord = local;
                vec2 ndc = (pos.xy / uViewportSize) * 2.0 - 1.0;
                gl_Position = vec4(ndc, 0.0, 1.0);
            }
            """
        )
        info.fragment_source(
            """
            float sdRoundRect(vec2 p, vec2 halfSize, float radius)
            {
                radius = clamp(radius, 0.0, min(halfSize.x, halfSize.y));
                vec2 q = abs(p) - halfSize + vec2(radius);
                return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - radius;
            }

            void main()
            {
                vec2 p = localCoord - vec2(uPad) - uSize * 0.5;
                float dist = sdRoundRect(p, uSize * 0.5, uRadius);
                float fillAlpha = 1.0 - smoothstep(-uAA, uAA, dist);
                vec4 fill = vec4(uFillColor.rgb, uFillColor.a * fillAlpha);

                if (uBorderWidth > 0.0 && uBorderColor.a > 0.0) {
                    float outerAlpha = 1.0 - smoothstep(-uAA, uAA, dist);
                    float innerAlpha = 1.0 - smoothstep(-uAA, uAA, dist + uBorderWidth);
                    float borderAlpha = max(outerAlpha - innerAlpha, 0.0);
                    vec4 border = vec4(uBorderColor.rgb, uBorderColor.a * borderAlpha);
                    float outAlpha = border.a + fill.a * (1.0 - border.a);
                    vec3 outRgb = fill.rgb;
                    if (outAlpha > 0.0) {
                        outRgb = (border.rgb * border.a + fill.rgb * fill.a * (1.0 - border.a)) / outAlpha;
                    }
                    FragColor = vec4(outRgb, outAlpha);
                }
                else {
                    FragColor = fill;
                }

                if (FragColor.a <= 0.001) {
                    discard;
                }
            }
            """
        )
        _sdf_round_rect_shader = gpu.shader.create_from_info(info)
    except Exception as ex:
        if not bpy.app.background and not _sdf_shader_warning_printed:
            print("Multi Blender Bookmark: SDF rounded-rect shader unavailable:", ex)
            _sdf_shader_warning_printed = True
        _sdf_round_rect_shader = None
    return _sdf_round_rect_shader


def _get_sdf_line_shader():
    global _sdf_line_shader, _sdf_shader_warning_printed
    if _sdf_line_shader is not None:
        return _sdf_line_shader
    try:
        iface = gpu.types.GPUStageInterfaceInfo("mbb_sdf_line_iface")
        iface.smooth("VEC2", "pixelCoord")
        info = gpu.types.GPUShaderCreateInfo()
        info.push_constant("VEC2", "uViewportSize")
        info.push_constant("VEC2", "uStart")
        info.push_constant("VEC2", "uEnd")
        info.push_constant("FLOAT", "uRadius")
        info.push_constant("FLOAT", "uAA")
        info.push_constant("VEC4", "uColor")
        info.vertex_in(0, "VEC2", "pos")
        info.vertex_out(iface)
        info.fragment_out(0, "VEC4", "FragColor")
        info.vertex_source(
            """
            void main()
            {
                pixelCoord = pos;
                vec2 ndc = (pos.xy / uViewportSize) * 2.0 - 1.0;
                gl_Position = vec4(ndc, 0.0, 1.0);
            }
            """
        )
        info.fragment_source(
            """
            float sdSegment(vec2 p, vec2 a, vec2 b)
            {
                vec2 pa = p - a;
                vec2 ba = b - a;
                float denom = max(dot(ba, ba), 0.0001);
                float h = clamp(dot(pa, ba) / denom, 0.0, 1.0);
                return length(pa - ba * h);
            }

            void main()
            {
                float dist = sdSegment(pixelCoord, uStart, uEnd) - uRadius;
                float alpha = 1.0 - smoothstep(-uAA, uAA, dist);
                FragColor = vec4(uColor.rgb, uColor.a * alpha);
                if (FragColor.a <= 0.001) {
                    discard;
                }
            }
            """
        )
        _sdf_line_shader = gpu.shader.create_from_info(info)
    except Exception as ex:
        if not bpy.app.background and not _sdf_shader_warning_printed:
            print("Multi Blender Bookmark: SDF line shader unavailable:", ex)
            _sdf_shader_warning_printed = True
        _sdf_line_shader = None
    return _sdf_line_shader


def _draw_sdf_rounded_rect(x, y, w, h, radius, fill, border=(0, 0, 0, 0), border_width=0.0, aa=1.0):
    if w <= 0 or h <= 0:
        return
    shader = _get_sdf_round_rect_shader()
    if shader is None:
        _draw_poly(_rounded_rect_tris(x, y, w, h, radius, 24), fill)
        return
    pad = max(2.0, float(border_width) + float(aa))
    px = x - pad
    py = y - pad
    pw = w + pad * 2.0
    ph = h + pad * 2.0
    points = (
        (px, py), (px + pw, py), (px + pw, py + ph),
        (px, py), (px + pw, py + ph), (px, py + ph),
    )
    local = (
        (0, 0), (pw, 0), (pw, ph),
        (0, 0), (pw, ph), (0, ph),
    )
    viewport_size = _sdf_viewport_size()
    if viewport_size is None:
        return
    batch = batch_for_shader(shader, "TRIS", {"pos": points, "local": local})
    gpu.state.blend_set("ALPHA")
    shader.bind()
    shader.uniform_float("uViewportSize", viewport_size)
    shader.uniform_float("uSize", (w, h))
    shader.uniform_float("uRadius", max(0.0, min(radius, w * 0.5, h * 0.5)))
    shader.uniform_float("uPad", pad)
    shader.uniform_float("uBorderWidth", float(border_width))
    shader.uniform_float("uAA", float(aa))
    shader.uniform_float("uFillColor", fill)
    shader.uniform_float("uBorderColor", border)
    batch.draw(shader)
    gpu.state.blend_set("NONE")


def _draw_rect(x, y, w, h, color):
    _draw_sdf_rounded_rect(x, y, w, h, 0, color)


def _rounded_rect_tris(x, y, w, h, radius, segments=18):
    radius = max(0, min(radius, w * 0.5, h * 0.5))
    centers = (
        (x + w - radius, y + h - radius, 0.0),
        (x + radius, y + h - radius, 90.0),
        (x + radius, y + radius, 180.0),
        (x + w - radius, y + radius, 270.0),
    )
    points = []
    for cx, cy, start in centers:
        for step in range(segments + 1):
            angle = (start + step * 90.0 / segments) * 3.141592653589793 / 180.0
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

    center = (x + w * 0.5, y + h * 0.5)
    tris = []
    for index, point in enumerate(points):
        tris.extend((center, point, points[(index + 1) % len(points)]))
    return tris


def _draw_rounded_rect(x, y, w, h, radius, color):
    _draw_sdf_rounded_rect(x, y, w, h, radius, color)


def _rounded_rect_outline_points(x, y, w, h, radius, segments=12):
    radius = max(0, min(radius, w * 0.5, h * 0.5))
    arcs = (
        (x + w - radius, y + h - radius, 0.0),
        (x + radius, y + h - radius, 90.0),
        (x + radius, y + radius, 180.0),
        (x + w - radius, y + radius, 270.0),
    )
    points = []
    for cx, cy, start in arcs:
        for step in range(segments + 1):
            angle = math.radians(start + step * 90.0 / segments)
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def _draw_rounded_rect_outline(x, y, w, h, radius, thickness, color):
    _draw_sdf_rounded_rect(x, y, w, h, radius, (0, 0, 0, 0), color, thickness)


def _draw_frosted_panel(x, y, w, h, radius, active=False, hovered=False):
    # Blender's GPU draw handler cannot sample and blur the viewport behind the
    # UI, so true CSS-like glass/backdrop-filter is unavailable here. This
    # version avoids stacked white slabs: one translucent surface, a thin rim,
    # and a small specular line create a lighter frosted feel without covering
    # the viewport like a bright bubble.
    base = (1.0, 1.0, 1.0, 0.985)
    rim = (1.0, 1.0, 1.0, 0.92)
    if active:
        base = (0.94, 0.97, 1.0, 0.99)
        rim = (0.50, 0.66, 1.0, 0.92)
    elif hovered:
        base = (0.90, 0.94, 1.0, 0.99)
        rim = (0.42, 0.58, 0.96, 0.88)
    _draw_rounded_rect(x, y, w, h, radius, base)
    _draw_rounded_rect_outline(x, y, w, h, radius, 1.1, rim)


def _draw_dock_panel(x, y, w, h, radius):
    # A clean bright shell matches the user's preferred Microsoft-like white
    # capsule better than a highly translucent glass layer.
    _draw_rounded_rect(x, y, w, h, radius, (0.84, 0.845, 0.84, 0.98))
    _draw_rounded_rect_outline(x, y, w, h, radius, 1.0, (1.0, 1.0, 1.0, 0.76))


def _draw_soft_shadow(x, y, w, h, radius):
    _draw_rounded_rect(x + 1, y - 3, w, h, radius, (0.02, 0.04, 0.08, 0.08))
    _draw_rounded_rect(x + 2, y - 7, w - 1, h, radius, (0.02, 0.04, 0.08, 0.045))


def _draw_trapezoid(x, y, w, h, color):
    inset = 12
    _draw_poly(
        [
            (x + inset, y),
            (x + w - inset, y),
            (x + w, y + h),
            (x + inset, y),
            (x + w, y + h),
            (x, y + h),
        ],
        color,
    )


def _draw_text(text, x, y, size=15, color=(0.12, 0.16, 0.22, 1.0)):
    font_id = 0
    blf.size(font_id, size)
    blf.color(font_id, *color)
    blf.position(font_id, x, y, 0)
    blf.draw(font_id, text)


def _text_dimensions(text, size):
    font_id = 0
    blf.size(font_id, size)
    return blf.dimensions(font_id, text)


def _draw_centered_text(text, x, y, w, h, size=14, color=(0.12, 0.16, 0.22, 1.0)):
    text_w, text_h = _text_dimensions(text, size)
    # BLF positions text at its baseline, so a slight downward correction keeps
    # visual centering consistent inside Blender's rounded GPU shapes.
    tx = x + (w - text_w) * 0.5
    ty = y + (h - text_h) * 0.5 + text_h * 0.16
    _draw_text(text, tx, ty, size, color)


def _draw_circle(cx, cy, radius, color, segments=24):
    _draw_sdf_rounded_rect(cx - radius, cy - radius, radius * 2.0, radius * 2.0, radius, color)


def _draw_bookmark_icon(x, y, size, color=(0.18, 0.38, 0.78, 1.0)):
    # Browser/bookmark glyph. The proportions are based on the open-source
    # Microsoft Fluent UI System Icons, redrawn with GPU primitives so this
    # add-on remains one self-contained Python file.
    notch = size * 0.28
    points = [
        (x, y + size),
        (x + size, y + size),
        (x + size, y),
        (x + size * 0.5, y + notch),
        (x, y),
        (x, y + size),
    ]
    _draw_poly(
        [points[0], points[1], points[2], points[0], points[2], points[3], points[0], points[3], points[4]],
        color,
    )


def _draw_thick_line(x1, y1, x2, y2, thickness, color):
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length <= 0:
        return
    shader = _get_sdf_line_shader()
    if shader is None:
        px = -dy / length * thickness * 0.5
        py = dx / length * thickness * 0.5
        _draw_poly(
            [
                (x1 + px, y1 + py),
                (x2 + px, y2 + py),
                (x2 - px, y2 - py),
                (x1 + px, y1 + py),
                (x2 - px, y2 - py),
                (x1 - px, y1 - py),
            ],
            color,
        )
        return
    pad = max(2.0, thickness * 0.5 + 1.5)
    min_x = min(x1, x2) - pad
    max_x = max(x1, x2) + pad
    min_y = min(y1, y2) - pad
    max_y = max(y1, y2) + pad
    points = (
        (min_x, min_y), (max_x, min_y), (max_x, max_y),
        (min_x, min_y), (max_x, max_y), (min_x, max_y),
    )
    viewport_size = _sdf_viewport_size()
    if viewport_size is None:
        return
    batch = batch_for_shader(shader, "TRIS", {"pos": points})
    gpu.state.blend_set("ALPHA")
    shader.bind()
    shader.uniform_float("uViewportSize", viewport_size)
    shader.uniform_float("uStart", (x1, y1))
    shader.uniform_float("uEnd", (x2, y2))
    shader.uniform_float("uRadius", float(thickness) * 0.5)
    shader.uniform_float("uAA", 0.85)
    shader.uniform_float("uColor", color)
    batch.draw(shader)
    gpu.state.blend_set("NONE")


def _draw_plus_icon(cx, cy, size, color=(0.05, 0.31, 0.72, 1.0)):
    half = size * 0.5
    _draw_thick_line(cx - half, cy, cx + half, cy, 3.9, color)
    _draw_thick_line(cx, cy - half, cx, cy + half, 3.9, color)


def _draw_grid_icon(x, y, size, color=(0.18, 0.40, 0.95, 1.0)):
    center_x = x + size * 0.5
    center_y = y + size * 0.5
    cell = size * 0.35
    gap = size * 0.13
    origin_x = center_x - (cell * 2 + gap) * 0.5
    origin_y = center_y - (cell * 2 + gap) * 0.5
    for row in range(2):
        for col in range(2):
            _draw_rounded_rect_outline(
                origin_x + col * (cell + gap),
                origin_y + row * (cell + gap),
                cell,
                cell,
                2.5,
                2.7,
                color,
            )


def _draw_list_icon(x, y, size, color=(0.38, 0.42, 0.48, 1.0)):
    # Keep the glyph optically centered in the same square used by the grid
    # icon. The previous version started at the lower edge, so the active pill
    # looked off-center even when the outer box was centered.
    center_y = y + size * 0.5
    spacing = size * 0.25
    bullet_x = x + size * 0.22
    line_x1 = x + size * 0.40
    line_x2 = x + size * 0.84
    for yy in (center_y + spacing, center_y, center_y - spacing):
        _draw_circle(bullet_x, yy, 2.15, color, 12)
        _draw_thick_line(line_x1, yy, line_x2, yy, 2.75, color)


def _draw_close_icon(cx, cy, size, color=(0.25, 0.31, 0.42, 0.92)):
    half = size * 0.5
    _draw_thick_line(cx - half, cy - half, cx + half, cy + half, 2.9, color)
    _draw_thick_line(cx - half, cy + half, cx + half, cy - half, 2.9, color)


def _draw_browser_icon(x, y, size, active=True, hovered=False):
    color = (0.02, 0.32, 0.78, 1.0) if active else (0.42, 0.50, 0.62, 0.95)
    if hovered:
        color = (0.0, 0.42, 0.98, 1.0)
    _draw_bookmark_icon(x + size * 0.25, y + size * 0.18, size * 0.50, color)


def _draw_new_file_icon(x, y, size, color=(0.74, 0.86, 1.0, 1.0)):
    # Inspired by Microsoft Fluent UI System Icons (MIT). It is redrawn here
    # with GPU primitives so the add-on remains a single installable .py file.
    body_w = size * 0.68
    body_h = size * 0.82
    _draw_rounded_rect_outline(x, y, body_w, body_h, size * 0.14, 2.7, color)
    _draw_thick_line(x + body_w * 0.30, y + body_h * 0.57, x + body_w * 0.68, y + body_h * 0.57, 2.5, color)
    _draw_thick_line(x + body_w * 0.30, y + body_h * 0.41, x + body_w * 0.58, y + body_h * 0.41, 2.5, color)
    badge_cx = x + body_w * 0.82
    badge_cy = y + body_h * 0.20
    _draw_plus_icon(badge_cx, badge_cy, 7.4, color)


def _draw_open_plus_icon(x, y, size, color=(0.78, 0.88, 1.0, 1.0)):
    # Plus/open glyph, also styled after Fluent's soft geometry and written as
    # local vector drawing instead of loading an external SVG.
    cx = x + size * 0.5
    cy = y + size * 0.5
    _draw_plus_icon(cx, cy, size * 0.30, color)


def _texture_for_thumbnail(filepath):
    path = bpy.path.abspath(filepath) if filepath else ""
    if not path or not os.path.exists(path):
        return None
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return None
    cached = _thumbnail_textures.get(path)
    if cached is not None and cached[0] == mtime:
        return cached[2]
    if cached is not None:
        _clear_thumbnail_texture(path)
    image = None
    texture = None
    try:
        # Avoid check_existing: generated previews reuse the same filepath, and
        # Blender can otherwise hand back an older in-memory image.
        image = bpy.data.images.load(path, check_existing=False)
        texture = gpu.texture.from_image(image)
    except Exception:
        texture = None
    if texture is not None:
        _thumbnail_textures[path] = (mtime, image, texture)
    return texture


def _draw_image_rect(filepath, x, y, w, h, alpha=1.0):
    path = bpy.path.abspath(filepath) if filepath else ""
    texture = _texture_for_thumbnail(path)
    if texture is None:
        return False

    tex_coords = ((0, 0), (1, 0), (1, 1), (0, 1))
    cached = _thumbnail_textures.get(path)
    if cached is not None:
        try:
            image = cached[1]
            image_w = max(1.0, float(image.size[0]))
            image_h = max(1.0, float(image.size[1]))
            image_aspect = image_w / image_h
            target_aspect = max(1.0, float(w)) / max(1.0, float(h))
            if image_aspect > target_aspect:
                keep = target_aspect / image_aspect
                u0 = (1.0 - keep) * 0.5
                u1 = 1.0 - u0
                tex_coords = ((u0, 0), (u1, 0), (u1, 1), (u0, 1))
            elif image_aspect < target_aspect:
                keep = image_aspect / target_aspect
                v0 = (1.0 - keep) * 0.5
                v1 = 1.0 - v0
                tex_coords = ((0, v0), (1, v0), (1, v1), (0, v1))
        except Exception:
            tex_coords = ((0, 0), (1, 0), (1, 1), (0, 1))

    try:
        _draw_rounded_rect(x, y, w, h, 10, THUMBNAIL_BACKGROUND)
        shader = gpu.shader.from_builtin("IMAGE")
        batch = batch_for_shader(
            shader,
            "TRI_FAN",
            {
                "pos": ((x, y), (x + w, y), (x + w, y + h), (x, y + h)),
                "texCoord": tex_coords,
            },
        )
        gpu.state.blend_set("ALPHA")
        shader.bind()
        shader.uniform_sampler("image", texture)
        batch.draw(shader)
        gpu.state.blend_set("NONE")
    except Exception:
        return False
    if alpha < 1.0:
        _draw_rounded_rect(x, y, w, h, 8, (1.0, 1.0, 1.0, 1.0 - alpha))
    return True


def _draw_thumbnail_placeholder(x, y, w, h, label, active=False):
    _draw_rounded_rect(x, y, w, h, 10, (0.78, 0.84, 0.94, 0.52))
    _draw_rounded_rect(x + 1, y + 1, w - 2, h - 2, 9, (0.96, 0.98, 1.0, 0.50))
    accent = (0.30, 0.45, 1.0, 0.82) if active else (0.54, 0.62, 0.74, 0.64)
    _draw_circle(x + w * 0.5, y + h * 0.54, 22, accent, 28)
    initial = (_display_title(label)[:1] or "?").upper()
    _draw_text(initial, x + w * 0.5 - 6, y + h * 0.54 - 8, 20, (1.0, 1.0, 1.0, 0.96))
    _draw_thick_line(x + 18, y + 16, x + w - 18, y + h - 18, 1.4, (1.0, 1.0, 1.0, 0.18))


def _tab_dimensions(view_mode=None):
    scale = _dock_ui_scale()
    if (view_mode or _overlay_view_mode()) == "THUMBNAILS":
        return THUMB_TAB_WIDTH * scale, THUMB_TAB_HEIGHT * scale
    return TAB_WIDTH * scale, TAB_HEIGHT * scale


def _layout_overlay(width, height, tabs, view_mode=None):
    scale = _dock_ui_scale()
    margin = OVERLAY_MARGIN * scale
    tab_gap = TAB_GAP * scale
    new_button_width = NEW_BUTTON_WIDTH * scale
    icon_button_size = ICON_BUTTON_SIZE * scale
    view_toggle_width = VIEW_TOGGLE_WIDTH * scale
    control_gap = CONTROL_GAP * scale
    tab_group_gap = TAB_GROUP_GAP * scale
    dock_padding_y = DOCK_PADDING_Y * scale
    tab_width, tab_height = _tab_dimensions(view_mode)
    tabs_width = 0
    if tabs:
        tabs_width = (len(tabs) * tab_width) + ((len(tabs) - 1) * tab_gap)
    gap_width = tab_group_gap + control_gap + (tab_group_gap if tabs else 0)
    total_width = new_button_width + tabs_width + view_toggle_width + icon_button_size + gap_width
    total_width = min(total_width, width - 2 * margin)
    x = (width - total_width) * 0.5
    overlay_height = tab_height + (dock_padding_y * 2)
    y = max(margin + dock_padding_y, height - _dock_top_offset() - overlay_height + dock_padding_y)
    return x, y, total_width


def _dock_geometry(x, y, total_width, tab_height):
    scale = _dock_ui_scale()
    dock_padding_y = DOCK_PADDING_Y * scale
    control_height = TAB_HEIGHT * scale
    icon_button_size = ICON_BUTTON_SIZE * scale
    dock_h = tab_height + (dock_padding_y * 2)
    dock_radius = dock_h * 0.5
    left_center_x = x + (control_height * 0.5)
    right_center_x = x + total_width - (icon_button_size * 0.5)
    dock_x = left_center_x - dock_radius
    dock_y = y - dock_padding_y
    dock_w = (right_center_x - left_center_x) + (dock_radius * 2)
    control_y = dock_y + (dock_h - control_height) * 0.5
    return dock_x, dock_y, dock_w, dock_h, dock_radius, control_y


def _build_overlay_hitboxes(width, height, tabs, offset_x=0, offset_y=0, area_id="", view_mode=None):
    scale = _dock_ui_scale()
    tab_gap = TAB_GAP * scale
    new_button_width = NEW_BUTTON_WIDTH * scale
    icon_button_size = ICON_BUTTON_SIZE * scale
    view_toggle_width = VIEW_TOGGLE_WIDTH * scale
    control_gap = CONTROL_GAP * scale
    tab_group_gap = TAB_GROUP_GAP * scale
    control_height = TAB_HEIGHT * scale
    hitboxes = []
    x, y, total_width = _layout_overlay(width, height, tabs, view_mode)
    tab_width, tab_height = _tab_dimensions(view_mode)
    _dock_x, _dock_y, _dock_w, _dock_h, _dock_radius, control_y = _dock_geometry(x, y, total_width, tab_height)

    hitboxes.append({
        "action": "new",
        "area_id": area_id,
        "index": -1,
        "rect": (x + offset_x - (5 * scale), control_y + offset_y - (5 * scale), new_button_width + (10 * scale), control_height + (10 * scale)),
    })
    x += new_button_width + tab_group_gap

    for index, _tab in enumerate(tabs):
        close_x = x + tab_width - (28 * scale)
        close_y = y + (tab_height - (20 * scale)) * 0.5
        hitboxes.append({
            "action": "switch",
            "area_id": area_id,
            "index": index,
            "rect": (x + offset_x - (3 * scale), y + offset_y - (4 * scale), tab_width - (28 * scale), tab_height + (8 * scale)),
        })
        hitboxes.append({
            "action": "close",
            "area_id": area_id,
            "index": index,
            "rect": (close_x + offset_x - (6 * scale), close_y + offset_y - (6 * scale), 28 * scale, 28 * scale),
        })
        x += tab_width + tab_gap

    if tabs:
        x += tab_group_gap - tab_gap

    hitboxes.append({
        "action": "view_thumbnails",
        "area_id": area_id,
        "index": -1,
        "rect": (x + offset_x - (4 * scale), control_y + offset_y - (5 * scale), view_toggle_width * 0.5 + (8 * scale), control_height + (10 * scale)),
    })
    hitboxes.append({
        "action": "view_names",
        "area_id": area_id,
        "index": -1,
        "rect": (x + offset_x + view_toggle_width * 0.5 - (4 * scale), control_y + offset_y - (5 * scale), view_toggle_width * 0.5 + (8 * scale), control_height + (10 * scale)),
    })
    x += view_toggle_width + control_gap

    hitboxes.append({
        "action": "open",
        "area_id": area_id,
        "index": -1,
        "rect": (x + offset_x - (5 * scale), control_y + offset_y - (5 * scale), icon_button_size + (10 * scale), control_height + (10 * scale)),
    })
    return hitboxes


def _hitbox_at(mx, my, hitboxes):
    for item in reversed(hitboxes):
        x, y, w, h = item["rect"]
        if x <= mx <= x + w and y <= my <= y + h:
            return item
    return None


def _point_in_rect(mx, my, rect):
    x, y, w, h = rect
    return x <= mx <= x + w and y <= my <= y + h


def _mouse_over_any_dock():
    mx, my = _overlay_mouse_abs
    return any(_point_in_rect(mx, my, rect) for rect in _overlay_dock_rects_by_area.values())


def _prune_selection(count):
    global _selection_anchor_index
    _selected_bookmark_indices.intersection_update(set(range(max(0, count))))
    if _selection_anchor_index < 0 or _selection_anchor_index >= count:
        _selection_anchor_index = next(iter(sorted(_selected_bookmark_indices)), -1)


def _set_single_selection(index):
    global _selection_anchor_index
    _selected_bookmark_indices.clear()
    if index >= 0:
        _selected_bookmark_indices.add(index)
        _selection_anchor_index = index
    else:
        _selection_anchor_index = -1


def _select_bookmark_range(context, index):
    global _selection_anchor_index
    count = len(context.window_manager.mbb_bookmarks)
    if index < 0 or index >= count:
        return
    if _selection_anchor_index < 0 or _selection_anchor_index >= count:
        _selection_anchor_index = _active_bookmark_index(context)
    if _selection_anchor_index < 0:
        _selection_anchor_index = index
    start = min(_selection_anchor_index, index)
    end = max(_selection_anchor_index, index)
    _selected_bookmark_indices.clear()
    _selected_bookmark_indices.update(range(start, end + 1))


def _is_bookmark_selected(index):
    return index in _selected_bookmark_indices


def _active_bookmark_index(context):
    wm = context.window_manager
    for index, bookmark in enumerate(wm.mbb_bookmarks):
        if bookmark.is_active:
            return index
    active_tab = _active_registry_tab()
    if active_tab:
        active_path = bpy.path.abspath(active_tab["filepath"])
        for index, bookmark in enumerate(wm.mbb_bookmarks):
            if bpy.path.abspath(bookmark.filepath) == active_path:
                return index
    return 0 if len(wm.mbb_bookmarks) else -1


def _switch_bookmark_relative(context, direction):
    count = len(context.window_manager.mbb_bookmarks)
    if count <= 0:
        return {"CANCELLED"}
    current_index = _active_bookmark_index(context)
    if current_index < 0:
        current_index = 0
    target_index = (current_index + direction) % count
    _set_single_selection(target_index)
    return bpy.ops.wm.mbb_open_bookmark(index=str(target_index))


def _close_active_bookmark(context):
    if _selected_bookmark_indices:
        return _close_selected_bookmarks(context)
    index = _active_bookmark_index(context)
    if index < 0:
        return {"CANCELLED"}
    return bpy.ops.wm.mbb_remove_bookmark(index=str(index))


def _close_selected_bookmarks(context):
    wm = context.window_manager
    count = len(wm.mbb_bookmarks)
    _prune_selection(count)
    if not _selected_bookmark_indices:
        return {"CANCELLED"}

    data = _clean_registry(_read_registry())
    tabs = data["tabs"]
    selected_indices = [index for index in sorted(_selected_bookmark_indices) if 0 <= index < len(tabs)]
    if not selected_indices:
        return {"CANCELLED"}

    closing_tabs = [tabs[index] for index in selected_indices]
    _store_last_closed_tabs(closing_tabs)
    active_index = _active_bookmark_index(context)
    fallback_tab = _next_remaining_tab_after_close(tabs, selected_indices, active_index)
    active_closed = active_index in selected_indices

    if fallback_tab is None:
        _create_untitled_bookmark(context, save_current=False)
    elif active_closed:
        result = _open_registry_tab(fallback_tab)
        if result == {"CANCELLED"}:
            return {"CANCELLED"}

    _write_tabs_after_close(context, closing_tabs, fallback_tab if active_closed else None)
    _selected_bookmark_indices.clear()
    global _selection_anchor_index
    _selection_anchor_index = -1
    _sync_registry_to_properties(context)
    return {"FINISHED"}


def _area_id(area):
    if area is None:
        return ""
    try:
        region = _view3d_window_region(area) if area.type == "VIEW_3D" else None
        if region is not None:
            return str(region.as_pointer())
        return str(area.as_pointer())
    except (AttributeError, ReferenceError, RuntimeError):
        return ""


def _primary_view3d_area(context):
    screen = getattr(context, "screen", None)
    if not screen:
        return getattr(context, "area", None)
    areas = [area for area in screen.areas if area.type == "VIEW_3D"]
    if not areas:
        return None
    return max(areas, key=lambda area: area.width * area.height)


def _is_primary_view3d_area(context):
    area = getattr(context, "area", None)
    primary = _primary_view3d_area(context)
    return area is not None and primary is not None and area == primary


def _is_overlay_enabled_for_area(context):
    area = getattr(context, "area", None)
    area_id = _area_id(area)
    return _overlay_state_for_area(area, area_id) != "HIDDEN"


def _is_hit_hovered(action, index=-1, area_id=""):
    mx, my = _overlay_mouse_abs
    for item in _overlay_hitboxes_by_area.get(area_id, []):
        if item.get("action") != action or item.get("index", -1) != index:
            continue
        if _hitbox_at(mx, my, [item]):
            return True
    return False


def _draw_icon_button(x, y, size, hovered=False, active=True):
    _draw_frosted_panel(x, y, size, _scaled(TAB_HEIGHT), _scaled(12), active=active, hovered=hovered)


def _draw_view3d_tab_bar():
    global _overlay_hitboxes, _overlay_last_region_size

    if not _show_view3d_tab_bar():
        return

    region = bpy.context.region
    area = bpy.context.area
    try:
        area_id = str(region.as_pointer()) if region and region.type == "WINDOW" else _area_id(area)
    except (AttributeError, ReferenceError, RuntimeError):
        area_id = _area_id(area)
    if region is None or not area_id:
        return

    width = region.width
    height = region.height
    _overlay_last_region_size = (width, height)

    tabs = _clean_registry(_read_registry())["tabs"]
    offset_x = getattr(region, "x", 0)
    offset_y = getattr(region, "y", 0)
    view_mode = _overlay_view_mode(area_id, area)
    enabled = _overlay_state_for_area(area, area_id) != "HIDDEN"
    if not enabled:
        _overlay_hitboxes_by_area[area_id] = []
        _overlay_dock_rects_by_area.pop(area_id, None)
        _overlay_hitboxes = [item for items in _overlay_hitboxes_by_area.values() for item in items]
        return

    hitboxes = _build_overlay_hitboxes(width, height, tabs, offset_x, offset_y, area_id, view_mode)
    _overlay_hitboxes_by_area[area_id] = hitboxes
    _overlay_hitboxes = [item for items in _overlay_hitboxes_by_area.values() for item in items]

    scale = _dock_ui_scale()
    tab_gap = TAB_GAP * scale
    new_button_width = NEW_BUTTON_WIDTH * scale
    icon_button_size = ICON_BUTTON_SIZE * scale
    view_toggle_width = VIEW_TOGGLE_WIDTH * scale
    control_gap = CONTROL_GAP * scale
    tab_group_gap = TAB_GROUP_GAP * scale
    control_height = TAB_HEIGHT * scale
    x, y, total_width = _layout_overlay(width, height, tabs, view_mode)
    tab_width, tab_height = _tab_dimensions(view_mode)
    thumb_mode = view_mode == "THUMBNAILS"
    dock_x, dock_y, dock_w, dock_h, dock_radius, control_y = _dock_geometry(x, y, total_width, tab_height)
    _overlay_dock_rects_by_area[area_id] = (
        dock_x + offset_x,
        dock_y + offset_y,
        dock_w,
        dock_h,
    )

    _draw_soft_shadow(dock_x, dock_y, dock_w, dock_h, dock_radius)
    _draw_dock_panel(dock_x, dock_y, dock_w, dock_h, dock_radius)

    hovered_new = _is_hit_hovered("new", -1, area_id)
    _draw_frosted_panel(x, control_y, new_button_width, control_height, control_height * 0.5, active=False, hovered=hovered_new)
    _draw_new_file_icon(x + (13 * scale), control_y + (control_height - (25 * scale) * 0.82) * 0.5, 25 * scale, (0.06, 0.07, 0.10, 0.98))
    _draw_centered_text("New", x + (30 * scale), control_y, new_button_width - (30 * scale), control_height, 14 * scale, (0.05, 0.06, 0.08, 0.98))
    x += new_button_width + tab_group_gap

    for index, tab in enumerate(tabs):
        active = bool(tab.get("is_active", False))
        selected = _is_bookmark_selected(index)
        hovered_tab = _is_hit_hovered("switch", index, area_id)
        hovered_close = _is_hit_hovered("close", index, area_id)
        text_color = (0.05, 0.06, 0.08, 0.96)
        _draw_frosted_panel(x, y, tab_width, tab_height, (control_height * 0.5) if not thumb_mode else (18 * scale), active=active or selected, hovered=hovered_tab)
        if selected:
            _draw_rounded_rect_outline(x + (2 * scale), y + (2 * scale), tab_width - (4 * scale), tab_height - (4 * scale), (control_height * 0.5 - (2 * scale)) if not thumb_mode else (16 * scale), 1.4 * scale, (0.22, 0.38, 1.0, 0.64))

        label = _display_title(tab.get("title", "Untitled"))
        if thumb_mode:
            thumb_content_x = x + (14 * scale)
            thumb_content_w = tab_width - (56 * scale)
            thumbnail_width = THUMBNAIL_WIDTH * scale
            thumbnail_height = THUMBNAIL_HEIGHT * scale
            thumb_x = thumb_content_x + (thumb_content_w - thumbnail_width) * 0.5
            thumb_y = y + (38 * scale)
            thumb_path = _best_thumbnail_for_tab(tab)
            _draw_rounded_rect(thumb_x - scale, thumb_y - scale, thumbnail_width + (2 * scale), thumbnail_height + (2 * scale), 12 * scale, (1.0, 1.0, 1.0, 0.62))
            if not _draw_image_rect(thumb_path, thumb_x, thumb_y, thumbnail_width, thumbnail_height, 1.0):
                _draw_thumbnail_placeholder(thumb_x, thumb_y, thumbnail_width, thumbnail_height, label, active)
            _draw_centered_text(label, thumb_content_x, y + (6 * scale), thumb_content_w, 28 * scale, 13 * scale, text_color)
        else:
            _draw_centered_text(label, x + (22 * scale), y, tab_width - (54 * scale), tab_height, 14 * scale, text_color)

        close_x = x + tab_width - (28 * scale)
        close_y = y + (tab_height - (20 * scale)) * 0.5
        if hovered_close:
            _draw_rounded_rect(close_x, close_y, 20 * scale, 20 * scale, 10 * scale, (0.56, 0.64, 0.78, 0.66))
            _draw_close_icon(close_x + (10 * scale), close_y + (10 * scale), 9.2 * scale, (0.10, 0.12, 0.17, 1.0))
        else:
            _draw_close_icon(close_x + (10 * scale), close_y + (10 * scale), 8.6 * scale, (0.28, 0.31, 0.38, 0.92))

        x += tab_width + tab_gap

    if tabs:
        x += tab_group_gap - tab_gap

    hovered_thumbs = _is_hit_hovered("view_thumbnails", -1, area_id)
    hovered_names = _is_hit_hovered("view_names", -1, area_id)
    toggle_y = control_y + (control_height - icon_button_size) * 0.5
    _draw_frosted_panel(x, toggle_y, view_toggle_width, icon_button_size, icon_button_size * 0.5, active=False, hovered=hovered_thumbs or hovered_names)
    grid_active = thumb_mode
    list_active = not thumb_mode
    if grid_active:
        _draw_rounded_rect(x + (6 * scale), toggle_y + (7 * scale), 34 * scale, icon_button_size - (14 * scale), 15 * scale, (0.76, 0.84, 1.0, 0.92))
    if list_active:
        _draw_rounded_rect(x + (48 * scale), toggle_y + (7 * scale), 34 * scale, icon_button_size - (14 * scale), 15 * scale, (0.76, 0.84, 1.0, 0.92))
    mode_icon_size = 22 * scale
    grid_icon_x = x + (6 * scale) + ((34 * scale) - mode_icon_size) * 0.5
    grid_icon_y = toggle_y + (7 * scale) + (icon_button_size - (14 * scale) - mode_icon_size) * 0.5
    list_icon_x = x + (48 * scale) + ((34 * scale) - mode_icon_size) * 0.5
    list_icon_y = grid_icon_y
    _draw_grid_icon(grid_icon_x, grid_icon_y, mode_icon_size, (0.18, 0.34, 1.0, 1.0 if grid_active or hovered_thumbs else 0.82))
    _draw_list_icon(list_icon_x, list_icon_y, mode_icon_size, (0.18, 0.22, 0.30, 1.0 if list_active or hovered_names else 0.82))
    x += view_toggle_width + control_gap

    hovered_open = _is_hit_hovered("open", -1, area_id)
    plus_color = ADD_BUTTON_BLUE_HOVER if hovered_open else ADD_BUTTON_BLUE
    _draw_circle(x + icon_button_size * 0.5, control_y + control_height * 0.5, control_height * 0.5, plus_color, 32)
    _draw_plus_icon(x + icon_button_size * 0.5, control_y + control_height * 0.5, 16 * scale, (1.0, 1.0, 1.0, 1.0))


class MBB_OT_overlay_router(bpy.types.Operator):
    bl_idname = "wm.mbb_overlay_router"
    bl_label = "Multi Blender Bookmark Overlay Router"
    bl_options = {"INTERNAL"}

    def invoke(self, context, _event):
        global _overlay_draw_handler, _overlay_router_running
        if _overlay_draw_handler is None:
            _overlay_draw_handler = bpy.types.SpaceView3D.draw_handler_add(
                _draw_view3d_tab_bar,
                (),
                "WINDOW",
                "POST_PIXEL",
            )
        _overlay_router_running = True
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        global _overlay_mouse_abs, _overlay_absorb_leftmouse_release
        if not _overlay_router_running:
            return {"CANCELLED"}

        if event.type in {"MOUSEMOVE", "LEFTMOUSE"}:
            _overlay_mouse_abs = (
                getattr(event, "mouse_x", -100000),
                getattr(event, "mouse_y", -100000),
            )

        if event.type == "LEFTMOUSE" and event.value == "RELEASE" and _overlay_absorb_leftmouse_release:
            _overlay_absorb_leftmouse_release = False
            screen = getattr(context, "screen", None)
            if screen:
                for area in screen.areas:
                    if area.type == "VIEW_3D":
                        area.tag_redraw()
            return {"RUNNING_MODAL"}

        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            mx = getattr(event, "mouse_x", -1)
            my = getattr(event, "mouse_y", -1)
            hitboxes = _overlay_hitboxes
            if not hitboxes and context.region:
                tabs = _clean_registry(_read_registry())["tabs"]
                area_id = _area_id(getattr(context, "area", None))
                view_mode = _overlay_view_mode(area_id, getattr(context, "area", None))
                hitboxes = _build_overlay_hitboxes(
                    context.region.width,
                    context.region.height,
                    tabs,
                    getattr(context.region, "x", 0),
                    getattr(context.region, "y", 0),
                    area_id,
                    view_mode,
                )

            item = _hitbox_at(mx, my, hitboxes)
            if item:
                _overlay_absorb_leftmouse_release = True
                if item["action"] == "new":
                    _defer_ui_action(lambda: bpy.ops.wm.mbb_new_blend())
                elif item["action"] == "open":
                    _defer_ui_action(lambda: bpy.ops.wm.mbb_open_blend("INVOKE_DEFAULT"))
                elif item["action"] == "view_names":
                    _set_overlay_area_state(item.get("area_id", ""), "NAMES", context)
                elif item["action"] == "view_thumbnails":
                    _set_overlay_area_state(item.get("area_id", ""), "THUMBNAILS", context)
                elif item["action"] == "switch":
                    if getattr(event, "shift", False):
                        _select_bookmark_range(context, int(item["index"]))
                    else:
                        _set_single_selection(int(item["index"]))
                        _defer_ui_action(lambda idx=str(item["index"]): bpy.ops.wm.mbb_open_bookmark(index=idx))
                elif item["action"] == "close":
                    _defer_ui_action(lambda idx=str(item["index"]): bpy.ops.wm.mbb_remove_bookmark(index=idx))
                return {"RUNNING_MODAL"}

        if event.type in {"MOUSEMOVE", "LEFTMOUSE"}:
            screen = getattr(context, "screen", None)
            if screen:
                for area in screen.areas:
                    if area.type == "VIEW_3D":
                        area.tag_redraw()

        return {"PASS_THROUGH"}


@persistent
def _mbb_load_post(_dummy):
    global _overlay_router_running, _overlay_visibility_initialized
    _overlay_router_running = False
    _overlay_visibility_initialized = False
    _overlay_hitboxes_by_area.clear()
    _overlay_dock_rects_by_area.clear()
    _overlay_hitboxes.clear()
    _initialize_overlay_state_from_disk(bpy.context)
    wm = _window_manager_from_context()
    if wm is not None and hasattr(wm, "mbb_view_mode"):
        wm.mbb_view_mode = _overlay_view_mode_state
    _register_current_process_tab(is_active=True)
    _sync_registry_to_properties(bpy.context)
    _schedule_overlay_router_restart()


@persistent
def _mbb_save_post(_dummy):
    _persist_overlay_state(bpy.context)
    _register_current_process_tab(is_active=False)
    _sync_registry_to_properties(bpy.context)


def _draw_header_tab_toggle(layout, context):
    # Blender does not expose a supported "insert before transform
    # orientation" slot for add-ons. We patch VIEW3D_HT_header.draw_xform_template
    # in register() so this native header button is drawn immediately before
    # Blender's orientation / pivot controls, then restore the original function
    # in unregister().
    area_id = _area_id(getattr(context, "area", None))
    active = bool(area_id and _is_overlay_enabled_for_area(context))
    row = layout.row(align=True)
    row.operator(
        MBB_OT_toggle_area_tab_bar.bl_idname,
        text="",
        icon="BOOKMARKS",
        depress=active,
    )
    row.separator(factor=0.7)


def _draw_xform_template_with_bookmark(layout, context):
    _draw_header_tab_toggle(layout, context)
    if _original_draw_xform_template is not None:
        _original_draw_xform_template(layout, context)


def _install_header_toggle():
    global _original_draw_xform_template
    header = getattr(bpy.types, "VIEW3D_HT_header", None)
    if header is None or _original_draw_xform_template is not None:
        return
    _original_draw_xform_template = header.draw_xform_template
    header.draw_xform_template = staticmethod(_draw_xform_template_with_bookmark)


def _remove_header_toggle():
    global _original_draw_xform_template
    header = getattr(bpy.types, "VIEW3D_HT_header", None)
    if header is not None and _original_draw_xform_template is not None:
        header.draw_xform_template = staticmethod(_original_draw_xform_template)
    _original_draw_xform_template = None


classes = (
    MBB_AddonPreferences,
    MBB_BookmarkItem,
    MBB_OT_open_blend_bookmark,
    MBB_OT_new_blend_bookmark,
    MBB_OT_open_bookmark,
    MBB_OT_remove_bookmark,
    MBB_OT_restore_closed_or_new,
    MBB_OT_toggle_area_tab_bar,
    MBB_OT_set_view_mode,
    MBB_OT_close_active_bookmark,
    MBB_OT_next_bookmark,
    MBB_OT_prev_bookmark,
    MBB_OT_dock_shortcut,
    MBB_OT_overlay_router,
)


def _register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon if wm else None
    if not kc:
        return
    km = kc.keymaps.new(name=KEYMAP_NAME, space_type=KEYMAP_SPACE_TYPE)
    toggle_key, toggle_modifiers = _shortcut_parts(_shortcut_value("shortcut_toggle_bar"))
    if toggle_key:
        kmi = km.keymap_items.new(
            TOGGLE_BAR_SHORTCUT_OPERATOR_ID,
            toggle_key,
            "PRESS",
            ctrl="CTRL" in toggle_modifiers,
            shift="SHIFT" in toggle_modifiers,
            alt="ALT" in toggle_modifiers,
            oskey="OSKEY" in toggle_modifiers,
        )
        addon_keymaps.append((km, kmi))
    for target in SHORTCUT_TARGETS:
        main_key, modifiers = _shortcut_parts(_shortcut_value(target))
        if not main_key:
            continue
        kmi = km.keymap_items.new(
            DOCK_SHORTCUT_OPERATOR_ID,
            main_key,
            "PRESS",
            ctrl="CTRL" in modifiers,
            shift="SHIFT" in modifiers,
            alt="ALT" in modifiers,
            oskey="OSKEY" in modifiers,
        )
        kmi.properties.target = target
        addon_keymaps.append((km, kmi))


def _unregister_keymaps():
    for km, kmi in addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass
    addon_keymaps.clear()


def _start_overlay_router():
    if bpy.app.background:
        return None
    if _overlay_router_running:
        return None
    try:
        bpy.ops.wm.mbb_overlay_router("INVOKE_DEFAULT")
    except Exception:
        return 1.0
    return None


def _schedule_overlay_router_restart():
    if bpy.app.background:
        return
    try:
        bpy.app.timers.register(_start_overlay_router, first_interval=0.25)
    except ValueError:
        pass


def _remove_overlay_draw_handler():
    global _overlay_draw_handler
    if _overlay_draw_handler is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_overlay_draw_handler, "WINDOW")
        except (ReferenceError, RuntimeError, ValueError):
            pass
    _overlay_draw_handler = None


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.mbb_bookmarks = CollectionProperty(type=MBB_BookmarkItem)
    bpy.types.WindowManager.mbb_view_mode = EnumProperty(
        name="Bookmark View Mode",
        description="Display bookmark tabs as file names or cached thumbnails",
        items=(
            ("NAMES", "Project File Names", "Show compact project file-name tabs"),
            ("THUMBNAILS", "Thumbnails", "Show taller tabs with cached project thumbnails"),
        ),
        default="NAMES",
    )

    _initialize_overlay_state_from_disk(bpy.context)
    _initialize_new_window_session(bpy.context)
    _register_keymaps()
    _install_header_toggle()

    if _mbb_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_mbb_load_post)
    if _mbb_save_post not in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.append(_mbb_save_post)
    if not bpy.app.background:
        bpy.app.timers.register(_start_overlay_router, first_interval=0.2)


def unregister():
    global _overlay_router_running, _overlay_visibility_initialized
    _persist_overlay_state(bpy.context)
    _overlay_router_running = False
    _overlay_visibility_initialized = False
    _overlay_hitboxes_by_area.clear()
    _overlay_dock_rects_by_area.clear()
    _overlay_hitboxes.clear()
    for path in list(_thumbnail_textures.keys()):
        _clear_thumbnail_texture(path)
    _thumbnail_textures.clear()
    _remove_overlay_draw_handler()
    _remove_header_toggle()

    if _mbb_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_mbb_load_post)
    if _mbb_save_post in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.remove(_mbb_save_post)

    _unregister_keymaps()

    if hasattr(bpy.types.WindowManager, "mbb_bookmarks"):
        del bpy.types.WindowManager.mbb_bookmarks
    if hasattr(bpy.types.WindowManager, "mbb_view_mode"):
        del bpy.types.WindowManager.mbb_view_mode

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()











