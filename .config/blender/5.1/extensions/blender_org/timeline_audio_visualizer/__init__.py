# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2026 Maxim K.

import array
import math
import os
import sys
import tempfile
import wave

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    StringProperty,
)


DETAIL_ITEMS = (
    ("BLOCKY", "Blocky", "Fastest, coarse waveform"),
    ("VERY_LOW", "Very Low", "Very low detail"),
    ("LOW", "Low", "Low detail"),
    ("MEDIUM", "Medium", "Balanced detail"),
    ("HIGH", "High", "Highest detail, slower refresh"),
)

DETAIL_BINS_PER_SECOND = {
    "BLOCKY": 6,
    "VERY_LOW": 12,
    "LOW": 24,
    "MEDIUM": 48,
    "HIGH": 96,
}

SOURCE_ITEMS = (
    ("ALL", "All", "Use sequencer strips and speakers"),
    ("SEQUENCER", "Sequencer Only", "Use sound strips from the video sequencer"),
    ("SPEAKER", "Speaker Only", "Use speaker objects in the scene"),
)

SEQUENCER_MODE_ITEMS = (
    ("AUDIBLE", "Audible Strips", "Show unmuted audible sound strips"),
    ("SELECTED", "Selected Strips", "Show selected sound strips, including muted strips"),
    ("LISTED", "Sound In List", "Show only sound strips listed in this panel, including muted strips"),
)

WAVEFORM_VIEW_ITEMS = (
    ("PEAKS", "Peaks / Bars", "Current vertical peak bars"),
    ("SOLID", "Solid Mirror", "Filled mirrored waveform, close to DAW clip waveforms"),
    ("OUTLINE", "Outline", "Thin mirrored waveform outline"),
    ("RMS", "RMS Envelope", "Smoothed loudness envelope"),
    ("PEAK_RMS", "Peak + RMS", "Peak bars with a smoothed loudness envelope"),
    ("POSITIVE", "Positive Fill", "One-sided filled waveform for compact timing reads"),
)

WAVEFORM_ANCHOR_ITEMS = (
    ("CENTER", "Center", "Place the waveform in the vertical center of the editor"),
    ("BOTTOM", "Bottom", "Place the waveform near the bottom of the editor"),
    ("TOP", "Top", "Place the waveform near the top of the editor"),
)


_DRAW_HANDLES = []
_WAVE_CACHE = {}
_WAVE_EVENTS = []
_LAST_STATUS = "Off"
_LAST_ERRORS = []
_TEMP_FILES = []
_HEADER_DRAWN = False


def _log(message):
    if _pref("verbose", False):
        print("[Timeline Audio Visualizer]", message)


def _pref(name, default=None):
    addons = getattr(bpy.context.preferences, "addons", {})
    addon = addons.get(__package__)
    if addon and addon.preferences:
        return getattr(addon.preferences, name, default)
    return default


def _bins_per_second():
    detail = _pref("waveform_detail", "MEDIUM")
    return DETAIL_BINS_PER_SECOND.get(detail, DETAIL_BINS_PER_SECOND["MEDIUM"])


def _scene_fps(scene):
    fps_base = scene.render.fps_base or 1.0
    return scene.render.fps / fps_base


def _set_status(message, errors=None):
    global _LAST_STATUS, _LAST_ERRORS
    _LAST_STATUS = message
    _LAST_ERRORS = list(errors or [])
    _log(message)


def _tag_redraw_all():
    wm = bpy.context.window_manager
    for window in wm.windows:
        screen = window.screen
        if not screen:
            continue
        for area in screen.areas:
            if area.type in {"DOPESHEET_EDITOR", "GRAPH_EDITOR", "NLA_EDITOR"}:
                area.tag_redraw()


def _sound_abs_path(sound):
    if not sound:
        return ""
    try:
        path = bpy.path.abspath(sound.filepath)
    except Exception:
        path = sound.filepath or ""
    return os.path.normpath(path) if path else ""


def _materialize_packed_sound(sound):
    packed = getattr(sound, "packed_file", None)
    if not packed:
        return ""
    suffix = os.path.splitext(sound.filepath or sound.name)[1] or ".audio"
    handle = tempfile.NamedTemporaryFile(
        delete=False,
        prefix="eyesync_waveform_",
        suffix=suffix,
    )
    try:
        handle.write(packed.data)
        handle.close()
        _TEMP_FILES.append(handle.name)
        return handle.name
    except Exception:
        handle.close()
        try:
            os.remove(handle.name)
        except OSError:
            pass
        return ""


def _sound_decode_path(sound):
    path = _sound_abs_path(sound)
    if path and os.path.exists(path):
        return path
    packed_path = _materialize_packed_sound(sound)
    if packed_path:
        return packed_path
    return path


def _strip_iter(scene):
    editor = scene.sequence_editor
    if not editor:
        return []
    strips = getattr(editor, "sequences_all", None)
    if strips is None:
        strips = getattr(editor, "strips_all", None)
    return list(strips or [])


def _is_sound_strip(strip):
    return getattr(strip, "type", "") == "SOUND" and getattr(strip, "sound", None)


def _strip_is_audible(strip):
    if getattr(strip, "mute", False):
        return False
    if getattr(strip, "volume", 1.0) <= 0:
        return False
    return True


def _clamp_range(start, end, clamp_start, clamp_end):
    return max(start, clamp_start), min(end, clamp_end)


def _collect_sequencer_events(scene, errors):
    events = []
    mode = scene.eyesync_seq_mode
    listed = {item.strip_name for item in scene.eyesync_strip_items}
    fps = _scene_fps(scene)

    for strip in _strip_iter(scene):
        if not _is_sound_strip(strip):
            continue

        if mode == "SELECTED" and not getattr(strip, "select", False):
            continue
        if mode == "LISTED" and strip.name not in listed:
            continue
        if mode == "AUDIBLE" and not _strip_is_audible(strip):
            continue

        start = float(getattr(strip, "frame_final_start", strip.frame_start))
        end = float(getattr(strip, "frame_final_end", start + strip.frame_duration))
        if scene.eyesync_scene_range:
            start, end = _clamp_range(start, end, scene.frame_start, scene.frame_end)
        if end <= start:
            continue

        sound = strip.sound
        path = _sound_decode_path(sound)
        if not path or not os.path.exists(path):
            errors.append("Missing audio file for strip: %s" % strip.name)
            continue

        frame_offset = float(getattr(strip, "frame_offset_start", 0.0))
        if start > getattr(strip, "frame_final_start", start):
            frame_offset += start - float(getattr(strip, "frame_final_start", start))

        events.append(
            {
                "kind": "SEQUENCER",
                "name": strip.name,
                "path": path,
                "frame_start": start,
                "frame_end": end,
                "offset_sec": max(0.0, frame_offset / fps),
                "gain": max(0.0, float(getattr(strip, "volume", 1.0))),
            }
        )
    return events


def _collect_speaker_events(scene, errors):
    events = []
    fps = _scene_fps(scene)
    for obj in scene.objects:
        if obj.type != "SPEAKER":
            continue
        speaker = obj.data
        sound = getattr(speaker, "sound", None)
        if not sound:
            continue
        if getattr(speaker, "muted", False):
            continue
        path = _sound_decode_path(sound)
        if not path or not os.path.exists(path):
            errors.append("Missing audio file for speaker: %s" % obj.name)
            continue
        volume = max(0.0, float(getattr(speaker, "volume", 1.0)))
        events.append(
            {
                "kind": "SPEAKER",
                "name": obj.name,
                "path": path,
                "frame_start": float(scene.frame_start),
                "frame_end": float(scene.frame_end),
                "offset_sec": 0.0,
                "gain": volume,
                "fps": fps,
            }
        )
    return events


def _collect_events(scene):
    errors = []
    source = scene.eyesync_source
    events = []
    if source in {"ALL", "SEQUENCER"}:
        events.extend(_collect_sequencer_events(scene, errors))
    if source in {"ALL", "SPEAKER"}:
        events.extend(_collect_speaker_events(scene, errors))
    return events, errors


def _file_signature(path, bins):
    try:
        stat = os.stat(path)
        return (os.path.normcase(os.path.abspath(path)), int(stat.st_mtime), stat.st_size, bins)
    except OSError:
        return (os.path.normcase(os.path.abspath(path)), 0, 0, bins)


def _amps_from_numpy(data, sample_rate, bins):
    import numpy as np

    arr = np.asarray(data)
    if arr.ndim == 2:
        arr = arr[:, 0]
    arr = np.asarray(arr, dtype=np.float32)
    if arr.size == 0:
        return [], 0.0

    duration = float(arr.size) / float(sample_rate)
    bin_size = max(1, int(round(float(sample_rate) / float(bins))))
    pad = (-arr.size) % bin_size
    if pad:
        arr = np.pad(arr, (0, pad), mode="constant")
    arr = np.abs(arr).reshape((-1, bin_size)).max(axis=1)
    arr = np.clip(arr, 0.0, 1.0)
    return arr.astype(np.float32).tolist(), duration


def _decode_with_aud(path, bins):
    import aud

    sample_rate = max(8000, bins * 160)
    sound = aud.Sound.file(path)
    sound = sound.rechannel(1).resample(sample_rate, 0)
    data = sound.data()
    return _amps_from_numpy(data, sample_rate, bins)


def _amps_from_int16(samples, sample_rate, bins):
    if not samples:
        return [], 0.0
    bin_size = max(1, int(round(float(sample_rate) / float(bins))))
    amps = []
    count = len(samples)
    for start in range(0, count, bin_size):
        peak = 0
        end = min(start + bin_size, count)
        for value in samples[start:end]:
            av = -value if value < 0 else value
            if av > peak:
                peak = av
        amps.append(min(1.0, float(peak) / 32768.0))
    return amps, float(count) / float(sample_rate)


def _decode_wav_fallback(path, bins):
    with wave.open(path, "rb") as reader:
        channels = max(1, reader.getnchannels())
        sample_rate = reader.getframerate()
        width = reader.getsampwidth()
        raw = reader.readframes(reader.getnframes())

    if width != 2:
        raise RuntimeError("WAV fallback supports 16-bit PCM only")

    values = array.array("h")
    values.frombytes(raw)
    if sys.byteorder != "little":
        values.byteswap()

    mono = array.array("h")
    if channels == 1:
        mono = values
    else:
        for i in range(0, len(values), channels):
            peak = 0
            for value in values[i : i + channels]:
                av = -value if value < 0 else value
                if av > peak:
                    peak = av
            mono.append(peak)
    return _amps_from_int16(mono, sample_rate, bins)


def _decode_audio(path, bins):
    failures = []
    for name, decoder in (
        ("Blender AUD", _decode_with_aud),
        ("WAV", _decode_wav_fallback),
    ):
        try:
            amps, duration = decoder(path, bins)
            if amps and duration > 0:
                return {
                    "amplitudes": amps,
                    "duration": duration,
                    "bins": bins,
                    "decoder": name,
                    "path": path,
                }
            failures.append("%s returned no samples" % name)
        except Exception as exc:
            failures.append("%s: %s" % (name, exc))
    raise RuntimeError("; ".join(failures))


def _ensure_cache(path, bins):
    key = _file_signature(path, bins)
    cached = _WAVE_CACHE.get(key)
    if cached:
        return cached
    decoded = _decode_audio(path, bins)
    _WAVE_CACHE[key] = decoded
    return decoded


def refresh_waveforms(scene):
    global _WAVE_EVENTS
    bins = _bins_per_second()
    events, errors = _collect_events(scene)

    refreshed = []
    decoders = set()
    for event in events:
        try:
            wave_data = _ensure_cache(event["path"], bins)
            event["cache_key"] = _file_signature(event["path"], bins)
            event["duration"] = wave_data["duration"]
            event["frame_end"] = min(
                event["frame_end"],
                event["frame_start"] + max(0.0, wave_data["duration"] - event["offset_sec"]) * _scene_fps(scene),
            )
            if event["frame_end"] > event["frame_start"]:
                refreshed.append(event)
                decoders.add(wave_data["decoder"])
        except Exception as exc:
            errors.append("%s: %s" % (event["name"], exc))

    _WAVE_EVENTS = refreshed
    if refreshed:
        _set_status(
            "Ready: %d source(s), %d cached file(s), %s"
            % (len(refreshed), len({e["cache_key"] for e in refreshed}), "/".join(sorted(decoders))),
            errors,
        )
    else:
        _set_status("No waveform sources found", errors)
    _tag_redraw_all()


def _shader():
    import gpu

    try:
        return gpu.shader.from_builtin("UNIFORM_COLOR")
    except Exception:
        return gpu.shader.from_builtin("2D_UNIFORM_COLOR")


def _wave_color():
    color = _pref("waveform_color", (0.15, 0.78, 1.0, 0.55))
    luminance = color[0] * 0.2126 + color[1] * 0.7152 + color[2] * 0.0722
    if luminance < 0.035:
        return (1.0, 1.0, 1.0, max(0.25, color[3]))
    return color


def _color_alpha(color, factor):
    return (
        color[0],
        color[1],
        color[2],
        max(0.0, min(1.0, color[3] * factor)),
    )


def _polyline_segments(points):
    vertices = []
    for index in range(1, len(points)):
        vertices.append(points[index - 1])
        vertices.append(points[index])
    return vertices


def _filled_mirror_tris(points, center_y, max_height):
    vertices = []
    for index in range(1, len(points)):
        x0, amp0 = points[index - 1]
        x1, amp1 = points[index]
        if abs(x1 - x0) < 0.01:
            continue
        h0 = amp0 * max_height
        h1 = amp1 * max_height
        top0 = (x0, center_y + h0)
        bottom0 = (x0, center_y - h0)
        top1 = (x1, center_y + h1)
        bottom1 = (x1, center_y - h1)
        vertices.extend((top0, bottom0, top1, top1, bottom0, bottom1))
    return vertices


def _filled_positive_tris(points, center_y, max_height):
    vertices = []
    for index in range(1, len(points)):
        x0, amp0 = points[index - 1]
        x1, amp1 = points[index]
        if abs(x1 - x0) < 0.01:
            continue
        top0 = (x0, center_y + amp0 * max_height)
        base0 = (x0, center_y)
        top1 = (x1, center_y + amp1 * max_height)
        base1 = (x1, center_y)
        vertices.extend((top0, base0, top1, top1, base0, base1))
    return vertices


def _smooth_points(points):
    if len(points) < 3:
        return points
    radius = max(2, min(16, len(points) // 32))
    smoothed = []
    for index, (x, _amp) in enumerate(points):
        start = max(0, index - radius)
        end = min(len(points), index + radius + 1)
        total = 0.0
        for _x, amp in points[start:end]:
            total += amp * amp
        rms = math.sqrt(total / float(end - start))
        smoothed.append((x, rms))
    return smoothed


def _draw_batch(shader, batch_for_shader, primitive, vertices, color, line_width=1.0):
    if not vertices:
        return
    import gpu

    batch = batch_for_shader(shader, primitive, {"pos": vertices})
    gpu.state.blend_set("ALPHA")
    try:
        gpu.state.line_width_set(line_width)
    except Exception:
        pass
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def _waveform_vertical_layout(region_height, gain, anchor, view_mode):
    margin = 8.0
    usable_height = max(8.0, float(region_height) - margin * 2.0)
    max_height = min(float(region_height) * 0.18 * gain, 80.0, usable_height * 0.5)
    if max_height <= 0:
        return None, None

    if view_mode == "POSITIVE":
        if anchor == "TOP":
            baseline_y = float(region_height) - margin - max_height
        elif anchor == "BOTTOM":
            baseline_y = margin
        else:
            baseline_y = float(region_height) * 0.5 - max_height * 0.5
        baseline_y = max(margin, min(float(region_height) - margin - max_height, baseline_y))
        return baseline_y, max_height

    if anchor == "TOP":
        center_y = float(region_height) - margin - max_height
    elif anchor == "BOTTOM":
        center_y = margin + max_height
    else:
        center_y = float(region_height) * 0.5
    center_y = max(margin + max_height, min(float(region_height) - margin - max_height, center_y))
    return center_y, max_height


def _draw_waveforms(_space_name):
    context = bpy.context
    scene = context.scene
    if not scene or not getattr(scene, "eyesync_enabled", False):
        return
    if not _WAVE_EVENTS:
        return
    if not context.region or context.region.type != "WINDOW":
        return
    region = context.region
    view2d = getattr(region, "view2d", None)
    if not view2d:
        return

    try:
        frame_min = view2d.region_to_view(0, 0)[0]
        frame_max = view2d.region_to_view(region.width, 0)[0]
    except Exception:
        return
    if frame_max < frame_min:
        frame_min, frame_max = frame_max, frame_min

    fps = _scene_fps(scene)
    gain = max(0.05, scene.eyesync_height_offset)
    view_mode = getattr(scene, "eyesync_view_mode", "PEAKS")
    anchor = getattr(scene, "eyesync_vertical_anchor", "CENTER")
    center_y, max_height = _waveform_vertical_layout(region.height, gain, anchor, view_mode)
    if center_y is None or max_height <= 0:
        return

    peak_lines = []
    outline_lines = []
    rms_lines = []
    filled_tris = []
    positive_tris = []
    for event in _WAVE_EVENTS:
        wave_data = _WAVE_CACHE.get(event.get("cache_key"))
        if not wave_data:
            continue
        amps = wave_data["amplitudes"]
        bins = wave_data["bins"]
        if not amps or bins <= 0:
            continue

        start_frame = max(frame_min, event["frame_start"])
        end_frame = min(frame_max, event["frame_end"])
        if end_frame <= start_frame:
            continue

        start_time = (start_frame - event["frame_start"]) / fps + event["offset_sec"]
        end_time = (end_frame - event["frame_start"]) / fps + event["offset_sec"]
        first = max(0, int(math.floor(start_time * bins)) - 1)
        last = min(len(amps), int(math.ceil(end_time * bins)) + 1)
        if last <= first:
            continue

        visible_bins = last - first
        max_lines = max(64, region.width * 2)
        step = max(1, int(math.ceil(float(visible_bins) / float(max_lines))))
        event_gain = max(0.0, event.get("gain", 1.0))

        points = []
        for idx in range(first, last, step):
            sample = max(amps[idx : min(idx + step, last)])
            amp = min(1.0, sample * event_gain)
            t = float(idx) / float(bins)
            frame = event["frame_start"] + (t - event["offset_sec"]) * fps
            x = view2d.view_to_region(frame, 0.0, clip=False)[0]
            if x < -4 or x > region.width + 4:
                continue
            points.append((x, amp))

        if len(points) < 2:
            continue

        if view_mode in {"PEAKS", "PEAK_RMS"}:
            for x, amp in points:
                h = amp * max_height
                peak_lines.append((x, center_y - h))
                peak_lines.append((x, center_y + h))

        if view_mode == "SOLID":
            filled_tris.extend(_filled_mirror_tris(points, center_y, max_height))
        elif view_mode == "POSITIVE":
            positive_tris.extend(_filled_positive_tris(points, center_y, max_height))
            outline_lines.extend(_polyline_segments([(x, center_y) for x, _amp in points]))
        elif view_mode == "OUTLINE":
            top = [(x, center_y + amp * max_height) for x, amp in points]
            bottom = [(x, center_y - amp * max_height) for x, amp in points]
            outline_lines.extend(_polyline_segments(top))
            outline_lines.extend(_polyline_segments(bottom))
        elif view_mode in {"RMS", "PEAK_RMS"}:
            smooth = _smooth_points(points)
            top = [(x, center_y + amp * max_height) for x, amp in smooth]
            bottom = [(x, center_y - amp * max_height) for x, amp in smooth]
            rms_lines.extend(_polyline_segments(top))
            rms_lines.extend(_polyline_segments(bottom))
            if view_mode == "RMS":
                filled_tris.extend(_filled_mirror_tris(smooth, center_y, max_height))

        if view_mode == "PEAKS":
            continue

    if not any((peak_lines, outline_lines, rms_lines, filled_tris, positive_tris)):
        return

    import gpu
    from gpu_extras.batch import batch_for_shader

    shader = _shader()
    color = _wave_color()
    _draw_batch(shader, batch_for_shader, "TRIS", filled_tris, _color_alpha(color, 0.32))
    _draw_batch(shader, batch_for_shader, "TRIS", positive_tris, _color_alpha(color, 0.42))
    _draw_batch(
        shader,
        batch_for_shader,
        "LINES",
        peak_lines,
        _color_alpha(color, 0.45 if view_mode == "PEAK_RMS" else 1.0),
    )
    _draw_batch(shader, batch_for_shader, "LINES", outline_lines, _color_alpha(color, 0.9), 1.2)
    _draw_batch(shader, batch_for_shader, "LINES", rms_lines, _color_alpha(color, 1.0), 1.6)
    gpu.state.blend_set("NONE")


def _ensure_draw_handlers():
    if _DRAW_HANDLES:
        return
    spaces = (
        (bpy.types.SpaceDopeSheetEditor, "DOPESHEET_EDITOR"),
        (bpy.types.SpaceGraphEditor, "GRAPH_EDITOR"),
        (bpy.types.SpaceNLA, "NLA_EDITOR"),
    )
    for space_type, name in spaces:
        handle = space_type.draw_handler_add(_draw_waveforms, (name,), "WINDOW", "POST_PIXEL")
        _DRAW_HANDLES.append((space_type, handle))
    _tag_redraw_all()


def _remove_draw_handlers():
    while _DRAW_HANDLES:
        space_type, handle = _DRAW_HANDLES.pop()
        try:
            space_type.draw_handler_remove(handle, "WINDOW")
        except Exception:
            pass
    _tag_redraw_all()


def _draw_dopesheet_header(self, context):
    if not context.scene:
        return
    layout = self.layout
    row = layout.row(align=True)
    row.separator()
    row.popover(panel="EYESYNC_PT_dopesheet", text="TAV", icon="SOUND")


def _ensure_header_button():
    global _HEADER_DRAWN
    if _HEADER_DRAWN:
        return
    bpy.types.DOPESHEET_HT_header.append(_draw_dopesheet_header)
    _HEADER_DRAWN = True
    _tag_redraw_all()


def _remove_header_button():
    global _HEADER_DRAWN
    if not _HEADER_DRAWN:
        return
    try:
        bpy.types.DOPESHEET_HT_header.remove(_draw_dopesheet_header)
    except Exception:
        pass
    _HEADER_DRAWN = False
    _tag_redraw_all()


def _enabled_update(self, _context):
    if self.eyesync_enabled:
        _ensure_draw_handlers()
    else:
        _remove_draw_handlers()


class EYESYNC_PG_strip_item(bpy.types.PropertyGroup):
    strip_name: StringProperty(name="Strip")


class EYESYNC_UL_strip_list(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, _icon, _active_data, _active_propname, _index):
        layout.label(text=item.strip_name, icon="SOUND")


class EYESYNC_OT_enable(bpy.types.Operator):
    bl_idname = "eyesync_waveform.enable"
    bl_label = "On / Refresh"
    bl_description = "Enable the waveform overlay and refresh audio waveforms"

    def execute(self, context):
        scene = context.scene
        scene.eyesync_enabled = True
        _ensure_draw_handlers()
        refresh_waveforms(scene)
        return {"FINISHED"}


class EYESYNC_OT_disable(bpy.types.Operator):
    bl_idname = "eyesync_waveform.disable"
    bl_label = "Off"
    bl_description = "Disable the waveform overlay"

    def execute(self, context):
        context.scene.eyesync_enabled = False
        _remove_draw_handlers()
        _set_status("Off")
        return {"FINISHED"}


class EYESYNC_OT_refresh(bpy.types.Operator):
    bl_idname = "eyesync_waveform.refresh"
    bl_label = "Refresh"
    bl_description = "Regenerate waveform data from current audio sources"

    def execute(self, context):
        if not context.scene.eyesync_enabled:
            context.scene.eyesync_enabled = True
        _ensure_draw_handlers()
        refresh_waveforms(context.scene)
        return {"FINISHED"}


class EYESYNC_OT_clear_cache(bpy.types.Operator):
    bl_idname = "eyesync_waveform.clear_cache"
    bl_label = "Clear Cache"
    bl_description = "Clear generated waveform data"

    def execute(self, _context):
        _WAVE_CACHE.clear()
        _WAVE_EVENTS.clear()
        _set_status("Cache cleared")
        _tag_redraw_all()
        return {"FINISHED"}


class EYESYNC_OT_add_selected_strips(bpy.types.Operator):
    bl_idname = "eyesync_waveform.add_selected_strips"
    bl_label = "Add Selected"
    bl_description = "Add selected sound strips to the Sound In List filter"

    def execute(self, context):
        scene = context.scene
        existing = {item.strip_name for item in scene.eyesync_strip_items}
        added = 0
        for strip in _strip_iter(scene):
            if _is_sound_strip(strip) and getattr(strip, "select", False) and strip.name not in existing:
                item = scene.eyesync_strip_items.add()
                item.strip_name = strip.name
                existing.add(strip.name)
                added += 1
        self.report({"INFO"}, "Added %d sound strip(s)" % added)
        return {"FINISHED"}


class EYESYNC_OT_remove_list_item(bpy.types.Operator):
    bl_idname = "eyesync_waveform.remove_list_item"
    bl_label = "Remove"
    bl_description = "Remove selected strip from the Sound In List filter"

    def execute(self, context):
        scene = context.scene
        index = scene.eyesync_strip_index
        if 0 <= index < len(scene.eyesync_strip_items):
            scene.eyesync_strip_items.remove(index)
            scene.eyesync_strip_index = min(index, max(0, len(scene.eyesync_strip_items) - 1))
        return {"FINISHED"}


class EYESYNC_OT_clear_list(bpy.types.Operator):
    bl_idname = "eyesync_waveform.clear_list"
    bl_label = "Clear"
    bl_description = "Clear the Sound In List filter"

    def execute(self, context):
        context.scene.eyesync_strip_items.clear()
        context.scene.eyesync_strip_index = 0
        return {"FINISHED"}


class EYESYNC_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    waveform_color: FloatVectorProperty(
        name="Waveform Color",
        subtype="COLOR",
        size=4,
        default=(0.15, 0.78, 1.0, 0.55),
        min=0.0,
        max=1.0,
        description="Overlay waveform color. Very dark colors fall back to white.",
    )
    waveform_detail: EnumProperty(
        name="Waveform Detail",
        items=DETAIL_ITEMS,
        default="MEDIUM",
        description="Waveform resolution. Higher values take more time and memory.",
    )
    verbose: BoolProperty(
        name="Verbose",
        default=False,
        description="Print status and decoder messages to the console.",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "waveform_color")
        layout.prop(self, "waveform_detail")
        layout.prop(self, "verbose")
        layout.label(text="Decoder order: Blender AUD, WAV fallback.")


class EYESYNC_PT_panel_base:
    bl_category = "Sound"
    bl_label = "Timeline Audio Visualizer"

    @classmethod
    def poll(cls, context):
        return bool(context.scene)

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        row = layout.row(align=True)
        row.operator("eyesync_waveform.enable", text="On", icon="PLAY")
        row.operator("eyesync_waveform.disable", text="Off", icon="PAUSE")
        layout.operator("eyesync_waveform.refresh", icon="FILE_REFRESH")

        layout.prop(scene, "eyesync_view_mode")
        layout.prop(scene, "eyesync_vertical_anchor")
        layout.prop(scene, "eyesync_height_offset")
        layout.prop(scene, "eyesync_source")

        if scene.eyesync_source in {"ALL", "SEQUENCER"}:
            box = layout.box()
            box.label(text="Sequencer", icon="SEQUENCE")
            box.prop(scene, "eyesync_seq_mode")
            box.prop(scene, "eyesync_scene_range")
            if scene.eyesync_seq_mode == "LISTED":
                box.template_list(
                    "EYESYNC_UL_strip_list",
                    "",
                    scene,
                    "eyesync_strip_items",
                    scene,
                    "eyesync_strip_index",
                    rows=3,
                )
                row = box.row(align=True)
                row.operator("eyesync_waveform.add_selected_strips", icon="ADD")
                row.operator("eyesync_waveform.remove_list_item", icon="REMOVE")
                row.operator("eyesync_waveform.clear_list", icon="TRASH")

        row = layout.row(align=True)
        row.operator("eyesync_waveform.clear_cache", icon="TRASH")

        layout.separator()
        icon = "CHECKMARK" if scene.eyesync_enabled and _WAVE_EVENTS else "INFO"
        layout.label(text=_LAST_STATUS, icon=icon)
        for error in _LAST_ERRORS[:3]:
            layout.label(text=error[:80], icon="ERROR")
        if len(_LAST_ERRORS) > 3:
            layout.label(text="%d more warning(s)" % (len(_LAST_ERRORS) - 3), icon="ERROR")


class EYESYNC_PT_dopesheet(EYESYNC_PT_panel_base, bpy.types.Panel):
    bl_space_type = "DOPESHEET_EDITOR"
    bl_region_type = "UI"


class EYESYNC_PT_graph(EYESYNC_PT_panel_base, bpy.types.Panel):
    bl_space_type = "GRAPH_EDITOR"
    bl_region_type = "UI"


class EYESYNC_PT_nla(EYESYNC_PT_panel_base, bpy.types.Panel):
    bl_space_type = "NLA_EDITOR"
    bl_region_type = "UI"


CLASSES = (
    EYESYNC_PG_strip_item,
    EYESYNC_UL_strip_list,
    EYESYNC_OT_enable,
    EYESYNC_OT_disable,
    EYESYNC_OT_refresh,
    EYESYNC_OT_clear_cache,
    EYESYNC_OT_add_selected_strips,
    EYESYNC_OT_remove_list_item,
    EYESYNC_OT_clear_list,
    EYESYNC_AddonPreferences,
    EYESYNC_PT_dopesheet,
    EYESYNC_PT_graph,
    EYESYNC_PT_nla,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.eyesync_enabled = BoolProperty(
        name="On",
        default=False,
        update=_enabled_update,
        description="Enable waveform overlay in animation editors.",
    )
    bpy.types.Scene.eyesync_height_offset = FloatProperty(
        name="Height Offset",
        default=1.0,
        min=0.05,
        max=5.0,
        soft_min=0.25,
        soft_max=2.5,
        description="Scale waveform peak height.",
    )
    bpy.types.Scene.eyesync_view_mode = EnumProperty(
        name="Waveform View",
        items=WAVEFORM_VIEW_ITEMS,
        default="PEAKS",
        description="Visual style used for the waveform overlay.",
    )
    bpy.types.Scene.eyesync_vertical_anchor = EnumProperty(
        name="Vertical Anchor",
        items=WAVEFORM_ANCHOR_ITEMS,
        default="CENTER",
        description="Vertical placement of the waveform overlay.",
    )
    bpy.types.Scene.eyesync_source = EnumProperty(
        name="Source",
        items=SOURCE_ITEMS,
        default="SEQUENCER",
        description="Audio source used to draw waveform overlays.",
    )
    bpy.types.Scene.eyesync_seq_mode = EnumProperty(
        name="Strip Filter",
        items=SEQUENCER_MODE_ITEMS,
        default="AUDIBLE",
        description="How sequencer sound strips are selected.",
    )
    bpy.types.Scene.eyesync_scene_range = BoolProperty(
        name="Scene Range",
        default=True,
        description="Clamp sequencer waveforms to the scene start/end range.",
    )
    bpy.types.Scene.eyesync_strip_items = CollectionProperty(type=EYESYNC_PG_strip_item)
    bpy.types.Scene.eyesync_strip_index = IntProperty(default=0)
    _ensure_header_button()


def unregister():
    _remove_draw_handlers()
    _remove_header_button()

    for name in (
        "eyesync_strip_index",
        "eyesync_strip_items",
        "eyesync_scene_range",
        "eyesync_seq_mode",
        "eyesync_source",
        "eyesync_vertical_anchor",
        "eyesync_view_mode",
        "eyesync_height_offset",
        "eyesync_enabled",
    ):
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)

    for temp_path in list(_TEMP_FILES):
        try:
            os.remove(temp_path)
        except OSError:
            pass
    _TEMP_FILES.clear()

    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
