import bpy
import os
import re
import json
import time
import shutil
import numpy as np
from collections import defaultdict
from bpy.types import Operator
from .tile_common import (
    CRRegion as Region,
    cr_compute_grid_offsets,
    cr_make_region_name_parts,
    cr_row_col_to_index,
)
from bpy.app.handlers import render_pre, render_post, render_cancel
from .utils import (
    get_comp_tree,
    cr_get_output_file_base_dir,
    cr_get_output_file_base_dir_value,
    cr_get_output_file_name,
    cr_get_output_file_items,
    cr_get_output_file_item_path,
    cr_set_output_file_base_dir,
    cr_set_output_file_name,
    cr_set_output_file_item_path,
    cr_output_file_item_supports_path,
    cr_output_file_has_linked_slots,
    cr_strip_chunk_suffix,
    cr_tag_view3d_redraw,
    cr_parse_custom_indices,
    cr_debug_enabled,
    cr_log,
    cr_log_debug,
    cr_suspend_overlay_draw,
    cr_resume_overlay_draw,
    get_border_range,
)
from .multilayer_merge import cr_get_exr_info, cr_is_multilayer_exr, cr_read_multilayer_schema, cr_run_hidden_multilayer_merge
from .translations import iface_


_cr_pending_crop_data = None
_cr_pending_merge_data = None
_cr_pending_collect_jobs = []   # list of (operator_ref, region_index, bleed_pixels)

_CR_TILE_MARKER_PREFIX = "__CR_TILE_"
_CR_REMERGE_MANIFEST_NAME = "chunk_render_remerge_manifest.json"
_CR_REGION_RE = re.compile(r'(?P<cols>\d+)x(?P<rows>\d+)_(?P<nrow>\d+)_(?P<ncol>\d+)')


def _cr_clean_name_tokens(text):
    cleaned = str(text or "")
    cleaned = re.sub(r'__+', '_', cleaned)
    cleaned = re.sub(r'--+', '-', cleaned)
    cleaned = re.sub(r'(_-|-_)+', '_', cleaned)
    return cleaned.strip(" ._-")


def _cr_parse_region_name(region_name):
    match = _CR_REGION_RE.fullmatch(str(region_name or ""))
    if match is None:
        return None
    return {
        "region_name": match.group(0),
        "cols": int(match.group("cols")),
        "rows": int(match.group("rows")),
        "nrow": int(match.group("nrow")),
        "ncol": int(match.group("ncol")),
    }


def _cr_strip_tile_marker(text):
    return _cr_clean_name_tokens(re.sub(rf'{re.escape(_CR_TILE_MARKER_PREFIX)}\d+x\d+_\d+_\d+', '', str(text or '')))


def _cr_make_output_tile_name(base_name, region_name):
    base = _cr_strip_tile_marker(base_name)
    if not base:
        base = "render"
    return f"{base}{_CR_TILE_MARKER_PREFIX}{region_name}"


def _cr_get_region_name_parts(num_cols, num_rows, index):
    return cr_make_region_name_parts(num_cols, num_rows, index)


def _cr_build_regions(rnd, output_img_name, task_output_dir, num_cols, num_rows,
                      base_min_x, base_max_x, base_min_y, base_max_y,
                      bleed_px=0, render_indices=None):
    total = max(1, int(num_cols)) * max(1, int(num_rows))
    render_set = set(range(total)) if render_indices is None else set(render_indices)
    regions = []
    delta_x = (base_max_x - base_min_x) / max(1, int(num_cols))
    delta_y = (base_max_y - base_min_y) / max(1, int(num_rows))

    for i in range(total):
        reg = Region()
        reg.index = i
        r_name, r_row, r_col = _cr_get_region_name_parts(num_cols, num_rows, i)
        reg.regionName = r_name
        reg.baseName = output_img_name + "_" + r_name + rnd.file_extension
        reg.task_output_dir = task_output_dir
        reg.fullName = os.path.join(reg.task_output_dir, reg.baseName)
        reg.nrow, reg.ncol = int(r_row), int(r_col)
        reg.minx = base_min_x + (delta_x * reg.ncol)
        reg.maxx = base_min_x + (delta_x * (reg.ncol + 1))
        reg.miny = base_min_y + (delta_y * (num_rows - reg.nrow))
        reg.maxy = base_min_y + (delta_y * (num_rows - reg.nrow - 1))

        if bleed_px > 0:
            perc = rnd.resolution_percentage / 100.0
            rx, ry = int(rnd.resolution_x * perc), int(rnd.resolution_y * perc)
            bfx, bfy = bleed_px / rx if rx > 0 else 0.0, bleed_px / ry if ry > 0 else 0.0
            ox1, ox2, oy1, oy2 = reg.minx, reg.maxx, reg.miny, reg.maxy
            reg.minx, reg.maxx = max(0.0, reg.minx - bfx), min(1.0, reg.maxx + bfx)
            reg.miny, reg.maxy = min(1.0, reg.miny + bfy), max(0.0, reg.maxy - bfy)
            reg.bleed_frac_left, reg.bleed_frac_right = ox1 - reg.minx, reg.maxx - ox2
            reg.bleed_frac_top, reg.bleed_frac_bottom = reg.miny - oy1, oy2 - reg.maxy

        reg.render = i in render_set
        regions.append(reg)
    return regions


def _cr_make_manifest_path(task_root_dir):
    return os.path.join(task_root_dir, _CR_REMERGE_MANIFEST_NAME)


def _cr_write_json_file(filepath, data):
    out_dir = os.path.dirname(filepath)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    tmp_path = filepath + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp_path, filepath)


def _cr_load_json_file(filepath):
    with open(filepath, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _cr_is_path_inside_root(filepath, root_dir):
    try:
        return os.path.commonpath([os.path.abspath(filepath), os.path.abspath(root_dir)]) == os.path.abspath(root_dir)
    except Exception:
        return False


def _cr_safe_relpath(filepath, root_dir):
    try:
        relpath = os.path.relpath(filepath, root_dir)
        if not relpath.startswith(".."):
            return relpath
    except Exception:
        pass
    return os.path.basename(filepath)


def _cr_region_to_manifest_record(reg):
    if hasattr(reg, "to_manifest_record"):
        return reg.to_manifest_record()
    return Region.from_object(reg).to_manifest_record()


def _cr_region_from_manifest_record(record):
    return Region.from_manifest_record(record)


def _cr_resolve_manifest_tile_path(folder, manifest_dir, tile_record, file_index):
    rel_path = str(tile_record.get("path_rel", "") or "")
    file_name = str(tile_record.get("file_name", "") or os.path.basename(rel_path) or "")
    for base_dir in (manifest_dir, folder):
        if rel_path and base_dir:
            candidate = os.path.normpath(os.path.join(base_dir, rel_path))
            if os.path.isfile(candidate):
                return candidate
    candidates = list(file_index.get(file_name, [])) if file_name else []
    if len(candidates) == 1:
        return candidates[0]

    wanted_region = str(tile_record.get("region_name", "") or "")
    wanted_merge_relpath = str(tile_record.get("merge_relpath", "") or "")
    for candidate in candidates:
        parsed = _cr_parse_tile_file_identity(candidate)
        if parsed is None:
            continue
        if wanted_region and str(parsed.get("region_name", "") or "") != wanted_region:
            continue
        if wanted_merge_relpath and str(parsed.get("merge_relpath", "") or "") != wanted_merge_relpath:
            continue
        return candidate
    return ""


def _cr_parse_tile_file_identity(filepath):
    basename = os.path.basename(filepath)
    stem, ext = os.path.splitext(basename)

    marker_match = re.search(rf'{re.escape(_CR_TILE_MARKER_PREFIX)}(?P<region>\d+x\d+_\d+_\d+)', stem)
    if marker_match is not None:
        info = _cr_parse_region_name(marker_match.group("region"))
        if info is not None:
            merge_stem = _cr_clean_name_tokens(stem[:marker_match.start()] + stem[marker_match.end():])
            info.update({
                "path": filepath,
                "merge_relpath": f"{merge_stem or 'Merged'}{ext}",
            })
            return info

    parent_name = os.path.basename(os.path.dirname(filepath))
    info = _cr_parse_region_name(parent_name)
    if info is not None and info["region_name"] == parent_name:
        info.update({
            "path": filepath,
            "merge_relpath": basename,
        })
        return info

    matches = list(_CR_REGION_RE.finditer(stem))
    if matches:
        match = matches[-1]
        info = _cr_parse_region_name(match.group(0))
        if info is not None:
            merge_stem = _cr_clean_name_tokens(stem[:match.start()] + stem[match.end():])
            info.update({
                "path": filepath,
                "merge_relpath": f"{merge_stem or 'Merged'}{ext}",
            })
            return info

    return None


_CR_OUTPUT_FORMAT_ATTRS = ("file_format", "color_mode", "color_depth", "exr_codec")


def _cr_capture_output_format(fmt, *, skip_empty=False, stringify=False):
    data = {}
    if fmt is None:
        return data
    for attr in _CR_OUTPUT_FORMAT_ATTRS:
        if not hasattr(fmt, attr):
            continue
        try:
            value = getattr(fmt, attr)
        except Exception:
            continue
        if skip_empty and value in (None, ""):
            continue
        data[attr] = str(value) if stringify else value
    return data


def _cr_snapshot_output_format(fmt):
    return _cr_capture_output_format(fmt, skip_empty=True, stringify=True)


def _cr_capture_output_format_state(fmt):
    return _cr_capture_output_format(fmt)


def _cr_apply_output_format(fmt, data):
    if fmt is None or not data:
        return
    for attr in _CR_OUTPUT_FORMAT_ATTRS:
        if attr not in data or not hasattr(fmt, attr):
            continue
        try:
            setattr(fmt, attr, data[attr])
        except Exception:
            pass


def _cr_save_image(image, filepath, output_format=None, scene=None):
    fmt_info = dict(output_format or {})
    out_dir = os.path.dirname(filepath)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    target_format = str(fmt_info.get("file_format") or getattr(image, "file_format", "") or "")
    if target_format:
        try:
            image.file_format = target_format
        except Exception:
            pass

    if hasattr(image, "use_half_precision"):
        try:
            if "use_half_precision" in fmt_info:
                image.use_half_precision = bool(fmt_info.get("use_half_precision"))
            elif target_format in ('OPEN_EXR', 'OPEN_EXR_MULTILAYER'):
                depth = str(fmt_info.get("color_depth") or "")
                if depth in {'16', '32'}:
                    image.use_half_precision = (depth == '16')
        except Exception:
            pass

    image.filepath_raw = filepath
    if target_format in ('OPEN_EXR', 'OPEN_EXR_MULTILAYER'):
        render_settings = getattr(getattr(scene, "render", None), "image_settings", None) if scene is not None else None
        if render_settings is None:
            image.save()
            return
        restore_state = _cr_capture_output_format_state(render_settings)
        try:
            if target_format and "file_format" not in fmt_info:
                fmt_info["file_format"] = target_format
            _cr_apply_output_format(render_settings, fmt_info)
            image.save_render(filepath, scene=scene)
        finally:
            _cr_apply_output_format(render_settings, restore_state)
    else:
        image.save()


def _cr_get_region_crop_ratios(reg):
    tw = reg.maxx - reg.minx
    th = reg.miny - reg.maxy
    if tw <= 0 or th <= 0:
        return (0.0, 0.0, 0.0, 0.0)
    return (
        reg.bleed_frac_left / tw,
        reg.bleed_frac_right / tw,
        reg.bleed_frac_top / th,
        reg.bleed_frac_bottom / th,
    )


def _cr_get_region_crop_pixels(reg, res_x, res_y):
    return (
        max(0, int(round(reg.bleed_frac_left * res_x))),
        max(0, int(round(reg.bleed_frac_right * res_x))),
        max(0, int(round(reg.bleed_frac_top * res_y))),
        max(0, int(round(reg.bleed_frac_bottom * res_y))),
    )


def _cr_get_region_render_size(reg, res_x, res_y):
    return (
        max(1, int(round((reg.maxx - reg.minx) * res_x))),
        max(1, int(round((reg.miny - reg.maxy) * res_y))),
    )


def _cr_normalize_path(path_value):
    path_text = str(path_value or "").strip()
    if not path_text:
        return ""
    try:
        path_text = bpy.path.abspath(path_text)
    except (AttributeError, TypeError, ValueError):
        pass
    return os.path.normcase(os.path.normpath(path_text))


def _cr_is_default_render_path(path_value):
    normalized_path = _cr_normalize_path(path_value)
    if not normalized_path:
        return True
    temp_dir = _cr_normalize_path(bpy.app.tempdir)
    return bool(temp_dir) and normalized_path == temp_dir


def _cr_iter_task_files(root_dir, region_name=None, filter_by_region_name=True):
    if not root_dir or not os.path.isdir(root_dir):
        return []
    files = []
    for fpath in _cr_walk_sorted_files(root_dir):
        if filter_by_region_name and region_name and region_name not in os.path.basename(fpath):
            continue
        files.append(fpath)
    return files


def _cr_walk_sorted_files(root_dir):
    if not root_dir or not os.path.isdir(root_dir):
        return []
    files = []
    for dirpath, _dirs, filenames in os.walk(root_dir):
        for filename in sorted(filenames):
            fpath = os.path.join(dirpath, filename)
            if os.path.isfile(fpath):
                files.append(fpath)
    return files


def _cr_make_merge_relpath(filename, region_name, task_id):
    raw_name = str(filename or "")
    stem, ext = os.path.splitext(raw_name)
    suffix = f"Merged_{task_id}" if task_id else "Merged"
    cleaned_stem = _cr_strip_tile_marker(stem)
    if cleaned_stem != stem:
        cleaned_stem = _cr_clean_name_tokens(cleaned_stem)
        return f"{cleaned_stem + '_' if cleaned_stem else ''}{suffix}{ext}"

    replaced_name = raw_name.replace(region_name, suffix).replace("__", "_") if region_name else raw_name
    replaced_base, ext = os.path.splitext(replaced_name)
    replaced_base = _cr_clean_name_tokens(replaced_base)
    if region_name and region_name in raw_name:
        return f"{replaced_base or suffix}{ext}"
    return f"{replaced_base + '_' if replaced_base else ''}{suffix}{ext}"


def _cr_make_tile_entry(path="", merge_dir="", merge_relpath="", output_format=None, multilayer_schema=None):
    return {
        "path": str(path or ""),
        "merge_dir": str(merge_dir or ""),
        "merge_relpath": str(merge_relpath or ""),
        "output_format": dict(output_format or {}),
        "multilayer_schema": list(multilayer_schema or []),
    }


def _cr_make_region_target(root_dir, merge_dir, output_format=None, filter_by_region_name=True):
    return {
        "root_dir": str(root_dir or ""),
        "merge_dir": str(merge_dir or ""),
        "output_format": dict(output_format or {}),
        "filter_by_region_name": bool(filter_by_region_name),
    }


def _cr_make_manifest_tile_record(reg, fpath, task_root_dir, merge_relpath):
    return {
        "region_index": int(reg.index),
        "region_name": str(reg.regionName),
        "nrow": int(reg.nrow),
        "ncol": int(reg.ncol),
        "file_name": os.path.basename(fpath),
        "path_rel": _cr_safe_relpath(fpath, task_root_dir),
        "merge_relpath": str(merge_relpath or ""),
    }


def _cr_make_merge_request(all_regions, tile_files, res_x, res_y, start_time, delete_after_merge,
                           debug_logging, task_root_dirs, task_id, merge_dir_fallback, main_output_format):
    return {
        "allRegions": all_regions,
        "tile_files": tile_files,
        "res_x": int(res_x),
        "res_y": int(res_y),
        "start_time": start_time,
        "delete_after_merge": bool(delete_after_merge),
        "debug_logging": bool(debug_logging),
        "task_root_dirs": list(task_root_dirs or []),
        "task_id": str(task_id or ""),
        "merge_dir_fallback": str(merge_dir_fallback or ""),
        "main_output_format": dict(main_output_format or {}),
    }


def _cr_build_multilayer_tile_info(reg, entry, res_x, res_y):
    crop_ratios = _cr_get_region_crop_ratios(reg)
    crop_pixels = _cr_get_region_crop_pixels(reg, res_x, res_y)
    render_size = _cr_get_region_render_size(reg, res_x, res_y)
    return {
        "path": entry.get("path", ""),
        "nrow": reg.nrow,
        "ncol": reg.ncol,
        "crop_left_ratio": crop_ratios[0],
        "crop_right_ratio": crop_ratios[1],
        "crop_top_ratio": crop_ratios[2],
        "crop_bottom_ratio": crop_ratios[3],
        "crop_left_px": crop_pixels[0],
        "crop_right_px": crop_pixels[1],
        "crop_top_px": crop_pixels[2],
        "crop_bottom_px": crop_pixels[3],
        "expected_width": render_size[0],
        "expected_height": render_size[1],
    }


class ChunkRenderJobContext:
    def __init__(self):
        self.finished = False
        self.allRegions = []
        self._task_folder_name = ""
        self._region_output_targets = {}
        self._tile_files = {}
        self._remerge_manifest_states = []

    def _collect_new_files(self, region_index):
        reg = next((r for r in self.allRegions if r.index == region_index), None)
        if reg is None:
            return

        collected = []
        task_id = self._task_folder_name.rsplit("_", 1)[-1]
        targets = self._region_output_targets.get(region_index, [])
        for target in targets:
            root_dir = target.get("root_dir", "")
            merge_dir = target.get("merge_dir", "")
            output_format = dict(target.get("output_format") or {})
            filter_by_region_name = bool(target.get("filter_by_region_name", True))
            if not root_dir or not merge_dir:
                continue
            for fpath in _cr_iter_task_files(root_dir, reg.regionName, filter_by_region_name):
                collected.append(_cr_make_tile_entry(
                    fpath,
                    merge_dir,
                    _cr_make_merge_relpath(os.path.basename(fpath), reg.regionName, task_id),
                    output_format,
                ))
        if collected:
            self._tile_files[region_index] = collected
            self._update_remerge_manifests()

    def _update_remerge_manifests(self):
        manifest_states = getattr(self, "_remerge_manifest_states", [])
        if not manifest_states:
            return

        region_map = {reg.index: reg for reg in self.allRegions}
        for state in manifest_states:
            task_root_dir = state.get("task_root_dir", "")
            if not task_root_dir:
                continue

            tiles = []
            merge_outputs = {}
            for region_index, entries in self._tile_files.items():
                reg = region_map.get(region_index)
                if reg is None:
                    continue
                for entry in entries:
                    fpath = entry.get("path", "")
                    if not fpath or not _cr_is_path_inside_root(fpath, task_root_dir):
                        continue
                    merge_relpath = str(entry.get("merge_relpath", "") or os.path.basename(fpath))
                    output_format = dict(entry.get("output_format") or {})
                    tiles.append(_cr_make_manifest_tile_record(reg, fpath, task_root_dir, merge_relpath))

                    merge_key = merge_relpath
                    merge_output = merge_outputs.setdefault(merge_key, {
                        "merge_relpath": merge_relpath,
                        "output_format": output_format,
                        "multilayer_schema": [],
                    })
                    if not merge_output.get("output_format"):
                        merge_output["output_format"] = output_format
                    if not merge_output.get("multilayer_schema"):
                        try:
                            if str(output_format.get("file_format") or "") == 'OPEN_EXR_MULTILAYER' or cr_is_multilayer_exr(fpath):
                                merge_output["multilayer_schema"] = cr_read_multilayer_schema(fpath)
                        except Exception as e:
                            cr_log_debug(f"[Chunk Render][DEBUG] Failed to capture multilayer schema for manifest: {e}")

            state["data"]["tiles"] = sorted(
                tiles,
                key=lambda item: (str(item.get("merge_relpath", "")), int(item.get("region_index", 0)), str(item.get("path_rel", ""))),
            )
            state["data"]["merge_outputs"] = [
                merge_outputs[key] for key in sorted(merge_outputs.keys())
            ]
            try:
                _cr_write_json_file(state["manifest_path"], state["data"])
            except Exception as e:
                cr_log_debug(f"[Chunk Render][DEBUG] Failed to write re-merge manifest: {e}")


def _cr_deferred_crop():

    global _cr_pending_crop_data, _cr_pending_collect_jobs

    # Delay all file collection/cropping until the tile render operator is fully done.
    if any(op is not None and not getattr(op, "finished", False) for op, _region_index, _bleed_pixels in _cr_pending_collect_jobs):
        return 0.5

    # Collect pending tile files after they have been written to disk.
    collect_jobs = _cr_pending_collect_jobs[:]
    _cr_pending_collect_jobs.clear()
    for op, region_index, bleed_pixels in collect_jobs:
        try:
            op._collect_new_files(region_index)
            if bleed_pixels > 0:
                reg = next((r for r in op.allRegions if r.index == region_index), None)
                if reg and reg.render:
                    file_entries = op._tile_files.get(region_index, [])
                    files = [
                        (e.get("path", ""), dict(e.get("output_format") or {}))
                        for e in file_entries if e.get("path") and os.path.exists(e.get("path", ""))
                    ]
                    tw, th = reg.maxx - reg.minx, reg.miny - reg.maxy
                    if tw > 0 and th > 0 and files:
                        jobs = [
                            (fpath, reg.bleed_frac_left / tw, reg.bleed_frac_right / tw, reg.bleed_frac_top / th, reg.bleed_frac_bottom / th, fmt_info)
                            for fpath, fmt_info in files
                        ]
                        if _cr_pending_crop_data is None:
                            _cr_pending_crop_data = []
                        _cr_pending_crop_data.extend(jobs)
        except Exception as e:
            cr_log(f"[Chunk Render] Deferred file collection failed (region {region_index}): {e}")

    jobs = _cr_pending_crop_data
    _cr_pending_crop_data = None
    if not jobs:
        return None
    try:
        count = 0
        skipped_multilayer = 0
        for fpath, l, r, t, b, fmt_info in jobs:
            if cr_is_multilayer_exr(fpath):
                skipped_multilayer += 1
                continue
            if _cr_crop_bleed_file(fpath, l, r, t, b, fmt_info):
                count += 1
        if skipped_multilayer:
            cr_log_debug(f"[Chunk Render][DEBUG] Cropped {count} file(s), skipped {skipped_multilayer} multilayer EXR file(s) for background merging")
        elif count:
            cr_log_debug(f"[Chunk Render][DEBUG] Cropped {count} file(s)")
    except Exception as e:
        cr_log(f"[Chunk Render] Deferred crop failed: {e}")
    return None


def _cr_auto_merge_timer():
    global _cr_pending_crop_data, _cr_pending_merge_data
    if _cr_pending_collect_jobs or _cr_pending_crop_data:
        return 1.0
    data = _cr_pending_merge_data
    _cr_pending_merge_data = None
    if data:
        try:
            _cr_do_auto_merge(data)
        except Exception as e:
            cr_log(f"[Chunk Merge] Auto merge failed: {e}")
    return None

def _cr_do_auto_merge(data):
    allRegions = data["allRegions"]
    tile_files = data.get("tile_files", {})
    task_root_dirs = data.get("task_root_dirs", [])
    res_x, res_y = data["res_x"], data["res_y"]
    task_id = data.get("task_id", "")
    if res_x <= 0 or res_y <= 0:
        return

    render_regions = [r for r in allRegions if r.render]
    if not render_regions:
        return

    pass_groups = defaultdict(list)
    for reg in render_regions:
        entries = tile_files.get(reg.index, [])
        found = [
            _cr_make_tile_entry(
                e.get("path", ""),
                e.get("merge_dir", ""),
                e.get("merge_relpath", ""),
                e.get("output_format"),
                e.get("multilayer_schema"),
            )
            for e in entries if e.get("path") and os.path.exists(e.get("path", ""))
        ]

        if not found:
            for root_dir in task_root_dirs:
                merge_dir = data.get("merge_dir_fallback", "")
                region_dir = os.path.join(root_dir, reg.regionName) if root_dir else ""
                candidate_roots = []
                if region_dir and os.path.isdir(region_dir):
                    candidate_roots.append((region_dir, False))
                candidate_roots.append((root_dir, True))
                for candidate_root, filter_by_region_name in candidate_roots:
                    for fpath in _cr_iter_task_files(candidate_root, reg.regionName, filter_by_region_name):
                        merge_relpath = _cr_make_merge_relpath(os.path.basename(fpath), reg.regionName, task_id)
                        found.append(_cr_make_tile_entry(
                            fpath,
                            merge_dir,
                            merge_relpath,
                            data.get("main_output_format"),
                        ))

        for entry in found:
            merge_dir = entry.get("merge_dir", "")
            merge_relpath = entry.get("merge_relpath", "") or os.path.basename(entry.get("path", ""))
            group_key = (merge_dir, merge_relpath)
            pass_groups[group_key].append((reg, entry))

    expected_count = len(render_regions)
    delete_after_merge = data.get("delete_after_merge", True)
    files_to_delete = []
    multilayer_jobs = []
    multilayer_source_files = []
    merge_failed = False

    for (merge_dir, merge_relpath), items in pass_groups.items():
        if not merge_dir:
            continue
        if len(items) != expected_count:
            cr_log(f"[Chunk Merge] Skipped '{merge_relpath}': expected {expected_count} tile(s), received {len(items)}")
            merge_failed = True
            continue

        try:
            first_entry = items[0][1]
            first_path = first_entry.get("path", "")

            # 用 bpy.data.images.load 统一探测通道数和浮点属性，
            # 避免 OIIO 与 Blender 对 JPG 等格式的通道数不一致
            probe_img = bpy.data.images.load(first_path, check_existing=False)
            channels = probe_img.channels
            is_float = probe_img.is_float
            use_half_prec = getattr(probe_img, "use_half_precision", False)
            bpy.data.images.remove(probe_img)

            # 文件格式和 multilayer 检测仍通过 cr_get_exr_info（仅 EXR 需要）
            first_info = cr_get_exr_info(first_path)
            file_format = str(first_info.get("file_format") or "")

            output_format = dict(first_entry.get("output_format") or {})
            output_file_format = str(output_format.get("file_format") or "")
            output_format.setdefault("file_format", file_format)
            output_format.setdefault("use_half_precision", use_half_prec)
            if "color_depth" not in output_format:
                output_format["color_depth"] = '16' if use_half_prec else '32'

            is_multilayer = bool(first_info.get("is_multilayer", False)) or output_file_format == 'OPEN_EXR_MULTILAYER'
            if is_multilayer:
                output_format["file_format"] = 'OPEN_EXR_MULTILAYER'
                cr_log_debug(f"[Multilayer EXR Merge][DEBUG] Detected multilayer EXR output: {merge_relpath}")
                multilayer_jobs.append({
                    "merge_dir": merge_dir,
                    "merge_relpath": merge_relpath,
                    "output_path": os.path.join(merge_dir, merge_relpath),
                    "output_format": output_format,
                    "multilayer_schema": list(first_entry.get("multilayer_schema") or []),
                    "tiles": [_cr_build_multilayer_tile_info(reg, entry, res_x, res_y) for reg, entry in items],
                })

                cr_log_debug(f"[Multilayer EXR Merge][DEBUG] Queued background merge job: {merge_relpath} | tiles={len(items)}")
                multilayer_source_files.extend([entry.get("path", "") for _, entry in items])
                continue

            row_heights, col_widths = {}, {}
            mismatch = False
            for reg, entry in items:
                fpath = entry.get("path", "")
                tmp = bpy.data.images.load(fpath, check_existing=False)
                if tmp.channels != channels:
                    cr_log(f"[Chunk Merge] Skipped '{merge_relpath}': tile {reg.regionName} has {tmp.channels} channel(s), expected {channels}")
                    bpy.data.images.remove(tmp)
                    mismatch = True
                    break
                row_heights[reg.nrow], col_widths[reg.ncol] = tmp.size[1], tmp.size[0]
                bpy.data.images.remove(tmp)
            if mismatch:
                merge_failed = True
                continue

            row_y_offsets, col_x_offsets, t_w, t_h = cr_compute_grid_offsets(
                row_heights,
                col_widths,
                top_to_bottom=False,
            )
            merged_pixels = np.zeros((t_h, t_w, channels), dtype=np.float32)

            for reg, entry in items:
                fpath = entry.get("path", "")
                img = bpy.data.images.load(fpath, check_existing=False)
                w, h, c = img.size[0], img.size[1], img.channels
                if c == channels:
                    pixels = np.empty(w * h * c, dtype=np.float32)
                    img.pixels.foreach_get(pixels)
                    ox, oy = col_x_offsets.get(reg.ncol, 0), row_y_offsets.get(reg.nrow, 0)
                    merged_pixels[oy:oy + h, ox:ox + w] = pixels.reshape((h, w, c))
                bpy.data.images.remove(img)

            out_path = os.path.join(merge_dir, merge_relpath)
            new_img = bpy.data.images.new("_cr_merged_tmp", t_w, t_h, alpha=(channels == 4), float_buffer=is_float)
            new_img.pixels.foreach_set(merged_pixels.ravel())
            if hasattr(new_img, "use_half_precision"):
                new_img.use_half_precision = use_half_prec
            scene = bpy.context.scene
            _cr_save_image(new_img, out_path, output_format=output_format, scene=scene)
            bpy.data.images.remove(new_img)

            if delete_after_merge:
                files_to_delete.extend([entry.get("path", "") for _, entry in items])

        except Exception as e:
            merge_failed = True
            cr_log(f"[Chunk Merge] Merge failed: {e}")

    if multilayer_jobs:
        try:
            cr_run_hidden_multilayer_merge(multilayer_jobs, debug_logging=bool(data.get("debug_logging", False)))
            if delete_after_merge:
                files_to_delete.extend(multilayer_source_files)
        except Exception as e:
            merge_failed = True
            cr_log(f"[Multilayer EXR Merge] Background Blender merge failed: {e}")

    if delete_after_merge:
        seen = set()
        for fpath in files_to_delete:
            if not fpath or fpath in seen:
                continue
            seen.add(fpath)
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception as e:
                    merge_failed = True
                    cr_log(f"[Chunk Render] Failed to delete tile file {fpath}: {e}")
        if not merge_failed:
            for task_root_dir in task_root_dirs:
                if task_root_dir and "_chunk_render_task_" in os.path.basename(task_root_dir) and os.path.isdir(task_root_dir):
                    try:
                        shutil.rmtree(task_root_dir, ignore_errors=True)
                        cr_log_debug(f"[Chunk Render][DEBUG] Cleaned task temp directory: {task_root_dir}")
                    except Exception as e:
                        cr_log(f"[Chunk Render] Failed to clean task directory: {e}")

    start_time = data.get("start_time", 0)
    if start_time > 0:
        total_time = time.time() - start_time
        if merge_failed:
            cr_log(f"[Chunk Render] Merge finished with failures. Total time: {total_time:.2f}s")
        else:
            cr_log(f"[Chunk Render] All tile merges completed. Total time: {total_time:.2f}s")


def _cr_crop_bleed_file(filepath, l_r, r_r, t_r, b_r, output_format=None):
    try:
        img = bpy.data.images.load(filepath, check_existing=False)
        w, h, channels = img.size[0], img.size[1], img.channels
        cl, cr, ct, cb = round(l_r * w), round(r_r * w), round(t_r * h), round(b_r * h)
        nw, nh = w - cl - cr, h - ct - cb
        if nw <= 0 or nh <= 0:
            bpy.data.images.remove(img)
            return False
        pixels = np.empty(w * h * channels, dtype=np.float32)
        img.pixels.foreach_get(pixels)
        cropped = pixels.reshape(h, w, channels)[cb:h - ct, cl:w - cr, :].copy()
        fmt, is_f, depth = img.file_format, img.is_float, getattr(img, "depth", 32) // channels
        save_format = dict(output_format or {})
        if fmt and "file_format" not in save_format:
            save_format["file_format"] = str(fmt)
        if "use_half_precision" not in save_format:
            save_format["use_half_precision"] = bool(is_f and depth <= 16)
        if str(save_format.get("file_format") or "") in {'OPEN_EXR', 'OPEN_EXR_MULTILAYER'} and "color_depth" not in save_format:
            save_format["color_depth"] = '16' if bool(is_f and depth <= 16) else '32'
        bpy.data.images.remove(img)
        new_img = bpy.data.images.new("_cr_crop_tmp", nw, nh, alpha=(channels == 4), float_buffer=is_f)
        new_img.pixels.foreach_set(cropped.ravel())
        if hasattr(new_img, "use_half_precision"):
            new_img.use_half_precision = (depth <= 16 and is_f)
        _cr_save_image(new_img, filepath, output_format=save_format, scene=bpy.context.scene)
        bpy.data.images.remove(new_img)
        return True
    except Exception as e:
        cr_log(f"[Chunk Render] Crop failed: {e}")
        return False

class ChunkRenderStop(Operator):
    bl_idname = 'chunk_render.stop'
    bl_label = "Stop Render"
    bl_description = "Stop the current tile render task"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        ps = getattr(context.scene, "chunk_render_settings", None)
        return ps is not None and ps.CR_renderGo

    def execute(self, context):
        ps = context.scene.chunk_render_settings
        ps.CR_renderGo = False
        cancelled = False
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    for space in area.spaces:
                        if getattr(space, "image", None) and getattr(space.image, "type", "") == 'RENDER_RESULT':
                            with context.temp_override(window=window, area=area):
                                try:
                                    bpy.ops.render.view_cancel('INVOKE_DEFAULT')
                                    cancelled = True
                                except Exception:
                                    pass
                            break
                if cancelled:
                    break
            if cancelled:
                break
        if not cancelled:
            try:
                bpy.ops.render.view_cancel('EXEC_DEFAULT')
            except Exception:
                pass
        return {'FINISHED'}


class ChunkRenderRegions(Operator):
    bl_idname = 'chunk_render.regions'
    bl_label = "Render Regions"
    bl_description = "Start rendering the image tile by tile"
    bl_options = {'REGISTER'}
    _timer = None

    def pre(self, scene, context=None):
        self.rendering = True
        ps = scene.chunk_render_settings
        ps.CR_msg1 = iface_("Rendering {current}/{total}").format(
            current=min(ps.CR_done_count + 1, ps.CR_maxrnd),
            total=ps.CR_maxrnd,
        )

    def post(self, scene, context=None):
        if getattr(self, "stop", False):
            return
        self.rendering = self.render_ready = False

        ps = scene.chunk_render_settings
        if self.last_rendered_region is not None:
            region_index = self.last_rendered_region
            bleed_pixels = ps.CR_bleed_pixels
            if hasattr(self, "job_context"):
                self.job_context.finished = getattr(self, "finished", False)
                self.job_context.allRegions = self.allRegions
                self.job_context._task_folder_name = self._task_folder_name
                self.job_context._region_output_targets = self._region_output_targets
                self.job_context._tile_files = self._tile_files
                self.job_context._remerge_manifest_states = getattr(self, "_remerge_manifest_states", [])
                _cr_pending_collect_jobs.append((self.job_context, region_index, bleed_pixels))
            else:
                _cr_pending_collect_jobs.append((self, region_index, bleed_pixels))
            if not bpy.app.timers.is_registered(_cr_deferred_crop):
                bpy.app.timers.register(_cr_deferred_crop, first_interval=1.0)
            ps.CR_done_count += 1
            self.last_rendered_region = None
            if ps.CR_done_count >= ps.CR_maxrnd:
                self.finished = True
                if hasattr(self, "job_context"):
                    self.job_context.finished = True

    def cancelled(self, scene, context=None):
        self.stop = True
        self.rendering = False
        self.render_ready = False
        self.finished = True
        if hasattr(self, "job_context"):
            self.job_context.finished = True
        if scene and hasattr(scene, "chunk_render_settings"):
            scene.chunk_render_settings.CR_renderGo = False
        cr_log("[Chunk Render] Render cancelled by user")

    def add_handlers(self, context):
        render_pre.append(self.pre)
        render_post.append(self.post)
        render_cancel.append(self.cancelled)
        self._timer = context.window_manager.event_timer_add(0.2, window=context.window)
        context.window_manager.modal_handler_add(self)

    def remove_handlers(self, context):
        if self.pre in render_pre:
            render_pre.remove(self.pre)
        if self.post in render_post:
            render_post.remove(self.post)
        if self.cancelled in render_cancel:
            render_cancel.remove(self.cancelled)
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        self._restore_render_settings(context)

    def _restore_render_settings(self, context):
        scn, ps = context.scene, context.scene.chunk_render_settings
        ps.CR_active_index = -1
        cr_tag_view3d_redraw()
        tree = get_comp_tree(scn)
        if tree is not None:
            for node_state in getattr(self, "saveFileOutputs", []):
                node = tree.nodes.get(node_state["node_name"])
                if node and node.type == 'OUTPUT_FILE':
                    cr_set_output_file_base_dir(node, node_state.get("base_dir", ""))
                    cr_set_output_file_name(node, node_state.get("file_name", ""))
                    items = cr_get_output_file_items(node)
                    for item_index, slot_path in node_state.get("slot_path_items", []):
                        if item_index < len(items):
                            cr_set_output_file_item_path(items[item_index], slot_path)
        if ps.CR_oldoutputfilepath:
            scn.render.filepath = ps.CR_oldoutputfilepath
        scn.render.resolution_percentage = ps.CR_oldPerc
        scn.render.use_border = ps.CR_old_use_border
        scn.render.use_crop_to_border = ps.CR_old_use_crop
        scn.render.border_min_x = ps.CR_old_border_min_x
        scn.render.border_max_x = ps.CR_old_border_max_x
        scn.render.border_min_y = ps.CR_old_border_min_y
        scn.render.border_max_y = ps.CR_old_border_max_y
        if hasattr(scn.render, "compositor_device") and ps.CR_oldCompositorDevice:
            scn.render.compositor_device = ps.CR_oldCompositorDevice
        if getattr(self, "_old_display_mode", None) is not None:
            try:
                context.preferences.view.render_display_type = self._old_display_mode
            except (AttributeError, TypeError, RuntimeError):
                pass
        self._restore_view3d(context)

    def _cleanup_task_dirs(self):
        dirs_to_remove = set()
        main_dir = getattr(self, "_main_task_dir", None)
        if main_dir:
            dirs_to_remove.add(main_dir)
        for node_state in getattr(self, "saveFileOutputs", []):
            td = node_state.get("task_dir", "")
            if td:
                dirs_to_remove.add(td)
        for d in dirs_to_remove:
            try:
                if "_chunk_render_task_" in os.path.basename(d) and os.path.isdir(d):
                    shutil.rmtree(d)
                    cr_log_debug(f"[Chunk Render][DEBUG] Cleaned leftover directory: {d}")
            except Exception as e:
                cr_log(f"[Chunk Render] Failed to clean directory {d}: {e}")

    def _init_remerge_manifests(self, context):
        scn = context.scene
        rnd = scn.render
        ps = scn.chunk_render_settings
        res_x = int(rnd.resolution_x * rnd.resolution_percentage / 100)
        res_y = int(rnd.resolution_y * rnd.resolution_percentage / 100)
        task_id = self._task_folder_name.rsplit("_", 1)[-1]
        base_regions = [_cr_region_to_manifest_record(reg) for reg in self.allRegions]

        manifest_states = []
        if not self._use_comp_only:
            manifest_states.append({
                "task_root_dir": self._main_task_dir,
                "merge_dir_hint": self.outputFolderAbs,
                "target_kind": "main_output",
                "node_name": "",
                "file_name": "",
                "output_format": dict(getattr(self, "_main_output_format", {}) or {}),
            })
        for node_state in self.saveFileOutputs:
            manifest_states.append({
                "task_root_dir": node_state.get("task_dir", ""),
                "merge_dir_hint": node_state.get("merge_dir", ""),
                "target_kind": "file_output",
                "node_name": node_state.get("node_name", ""),
                "file_name": node_state.get("file_name", ""),
                "output_format": dict(node_state.get("output_format") or {}),
            })

        self.job_context._remerge_manifest_states = self._remerge_manifest_states = []
        for state in manifest_states:
            task_root_dir = state.get("task_root_dir", "")
            if not task_root_dir:
                continue
            manifest_data = {
                "manifest_version": 3,
                "task_id": task_id,
                "task_root_dir": task_root_dir,
                "merge_dir_hint": state.get("merge_dir_hint", ""),
                "output_name": self.outputImgName,
                "output_format": dict(state.get("output_format") or {}),
                "main_output_format": dict(getattr(self, "_main_output_format", {}) or {}),
                "cols": int(self.num_cols),
                "rows": int(self.num_rows),
                "base_min_x": float(self.base_min_x),
                "base_max_x": float(self.base_max_x),
                "base_min_y": float(self.base_min_y),
                "base_max_y": float(self.base_max_y),
                "bleed_px": int(ps.CR_bleed_pixels),
                "res_x": int(res_x),
                "res_y": int(res_y),
                "target_kind": state.get("target_kind", ""),
                "node_name": state.get("node_name", ""),
                "file_name": state.get("file_name", ""),
                "regions": list(base_regions),
                "tiles": [],
                "merge_outputs": [],
            }
            self._remerge_manifest_states.append({
                "task_root_dir": task_root_dir,
                "manifest_path": _cr_make_manifest_path(task_root_dir),
                "data": manifest_data,
            })

        self._update_remerge_manifests()

    def _update_remerge_manifests(self):
        manifest_states = getattr(self, "_remerge_manifest_states", [])
        if not manifest_states:
            return

        region_map = {reg.index: reg for reg in self.allRegions}
        for state in manifest_states:
            task_root_dir = state.get("task_root_dir", "")
            if not task_root_dir:
                continue

            tiles = []
            merge_outputs = {}
            for region_index, entries in self._tile_files.items():
                reg = region_map.get(region_index)
                if reg is None:
                    continue
                for entry in entries:
                    fpath = entry.get("path", "")
                    if not fpath or not _cr_is_path_inside_root(fpath, task_root_dir):
                        continue
                    merge_relpath = str(entry.get("merge_relpath", "") or os.path.basename(fpath))
                    output_format = dict(entry.get("output_format") or {})
                    tiles.append(_cr_make_manifest_tile_record(reg, fpath, task_root_dir, merge_relpath))

                    merge_key = merge_relpath
                    merge_output = merge_outputs.setdefault(merge_key, {
                        "merge_relpath": merge_relpath,
                        "output_format": output_format,
                        "multilayer_schema": [],
                    })
                    if not merge_output.get("output_format"):
                        merge_output["output_format"] = output_format
                    if not merge_output.get("multilayer_schema"):
                        try:
                            if str(output_format.get("file_format") or "") == 'OPEN_EXR_MULTILAYER' or cr_is_multilayer_exr(fpath):
                                merge_output["multilayer_schema"] = cr_read_multilayer_schema(fpath)
                        except Exception as e:
                            cr_log_debug(f"[Chunk Render][DEBUG] Failed to capture multilayer schema for manifest: {e}")

            state["data"]["tiles"] = sorted(
                tiles,
                key=lambda item: (str(item.get("merge_relpath", "")), int(item.get("region_index", 0)), str(item.get("path_rel", ""))),
            )
            state["data"]["merge_outputs"] = [
                merge_outputs[key] for key in sorted(merge_outputs.keys())
            ]
            try:
                _cr_write_json_file(state["manifest_path"], state["data"])
            except Exception as e:
                cr_log_debug(f"[Chunk Render][DEBUG] Failed to write re-merge manifest: {e}")

    def _find_view3d_area(self, context):
        window = getattr(context, "window", None)
        screen = getattr(window, "screen", None)
        if screen is None:
            return None
        camera_area = None
        for area in screen.areas:
            if area.type != 'VIEW_3D':
                continue
            space = next((s for s in area.spaces if s.type == 'VIEW_3D'), None)
            region_3d = getattr(space, "region_3d", None)
            is_camera = bool(region_3d and region_3d.view_perspective == 'CAMERA')
            if is_camera:
                if camera_area is None:
                    camera_area = area
            else:
                return area
        return camera_area

    def _resolve_switched_area(self):
        window = getattr(self, "_switched_window", None)
        area_index = int(getattr(self, "_switched_area_index", -1))
        if window is None or area_index < 0:
            return None
        screen = getattr(window, "screen", None)
        if screen is None:
            return None
        areas = tuple(getattr(screen, "areas", ()))
        if area_index >= len(areas):
            return None
        return areas[area_index]

    def _get_image_editor_space(self, area):
        spaces = getattr(area, "spaces", None)
        if not spaces:
            return None
        active_space = getattr(spaces, "active", None)
        if active_space is not None and getattr(active_space, "type", "") == 'IMAGE_EDITOR':
            return active_space
        for space in spaces:
            if getattr(space, "type", "") == 'IMAGE_EDITOR':
                return space
        return None

    def _switch_to_image_editor(self, context):
        self._switched_window = None
        self._switched_area_index = -1
        self._switched_area_orig_type = None
        area = self._find_view3d_area(context)
        if area is None:
            return False

        space = next((s for s in area.spaces if s.type == 'VIEW_3D'), None)
        region_3d = getattr(space, "region_3d", None)
        if region_3d is not None and region_3d.view_perspective == 'CAMERA':
            return False

        window = getattr(context, "window", None)
        screen = getattr(window, "screen", None)
        if window is None or screen is None:
            return False

        areas = tuple(getattr(screen, "areas", ()))
        try:
            area_index = next(index for index, candidate in enumerate(areas) if candidate == area)
        except StopIteration:
            return False

        cr_suspend_overlay_draw()
        cr_tag_view3d_redraw()
        try:
            orig_type = area.ui_type
            area.ui_type = 'IMAGE_EDITOR'
        except (AttributeError, TypeError, RuntimeError, ReferenceError):
            return False
        finally:
            cr_resume_overlay_draw()
            cr_tag_view3d_redraw()

        self._switched_window = window
        self._switched_area_index = area_index
        self._switched_area_orig_type = orig_type

        target_window = window
        target_area_index = area_index
        max_attempts = 20
        retry_interval = 0.1
        attempts = {"count": 0}

        def _set_render_result():
            attempts["count"] += 1
            target_screen = getattr(target_window, "screen", None)
            if target_screen is None:
                return None
            target_areas = tuple(getattr(target_screen, "areas", ()))
            if target_area_index < 0 or target_area_index >= len(target_areas):
                return None
            target_area = target_areas[target_area_index]
            if getattr(target_area, "ui_type", "") != 'IMAGE_EDITOR':
                return retry_interval if attempts["count"] < max_attempts else None

            image_space = self._get_image_editor_space(target_area)
            if image_space is None or not hasattr(image_space, "image"):
                return retry_interval if attempts["count"] < max_attempts else None

            render_img = bpy.data.images.get("Render Result")
            if render_img is None:
                return retry_interval if attempts["count"] < max_attempts else None

            try:
                image_space.image = render_img
                cr_log_debug(
                    f"[Chunk Render][DEBUG] Bound Render Result to IMAGE_EDITOR on attempt {attempts['count']}"
                )
            except (AttributeError, TypeError, RuntimeError, ReferenceError) as e:
                cr_log_debug(f"[Chunk Render][DEBUG] Failed to bind Render Result image: {e}")
                return retry_interval if attempts["count"] < max_attempts else None
            return None

        bpy.app.timers.register(_set_render_result, first_interval=0.05)
        return True

    def _restore_view3d(self, context):
        area = self._resolve_switched_area()
        orig_type = getattr(self, "_switched_area_orig_type", None)
        self._switched_window = None
        self._switched_area_index = -1
        self._switched_area_orig_type = None
        if area is not None and orig_type is not None:
            cr_suspend_overlay_draw()
            cr_tag_view3d_redraw()
            try:
                area.ui_type = orig_type
            except (AttributeError, TypeError, RuntimeError, ReferenceError):
                pass
            finally:
                cr_resume_overlay_draw()
        cr_tag_view3d_redraw()

    def _cancel_task(self, context, message, error=None):
        if error is None:
            cr_log(message)
        else:
            cr_log(f"{message}: {error}")
        self.remove_handlers(context)
        self._cleanup_task_dirs()
        context.scene.chunk_render_settings.CR_renderGo = False
        self.finished = True
        if hasattr(self, "job_context"):
            self.job_context.finished = True
        return {'CANCELLED'}

    def _invoke_render(self):
        bpy.ops.render.render("INVOKE_DEFAULT", write_still=not self._use_comp_only)

    def getRegionName(self, context, index):
        return _cr_get_region_name_parts(self.num_cols, self.num_rows, index)

    def setRender(self, context):
        scn, ps = context.scene, context.scene.chunk_render_settings
        rnd = scn.render
        if ps.CR_cntrnd < len(self.allRegions):
            reg = self.allRegions[ps.CR_cntrnd]
            if reg.render:
                self.last_rendered_region = reg.index
                ps.CR_active_index = reg.index
                cr_tag_view3d_redraw()

                rnd.border_min_x, rnd.border_min_y = reg.minx, reg.maxy
                rnd.border_max_x, rnd.border_max_y = reg.maxx, reg.miny

                region_targets = []
                if not self._use_comp_only:
                    os.makedirs(reg.task_output_dir, exist_ok=True)
                    rnd.filepath = reg.fullName
                    region_targets.append(_cr_make_region_target(
                        reg.task_output_dir,
                        self.outputFolderAbs,
                        getattr(self, "_main_output_format", {}),
                        True,
                    ))
                tree = get_comp_tree(scn)
                if tree is not None:
                    for node_state in self.saveFileOutputs:
                        node = tree.nodes.get(node_state["node_name"])
                        if not node or node.type != 'OUTPUT_FILE' or node.mute:
                            continue
                        items = cr_get_output_file_items(node)
                        node_task_dir = node_state["task_dir"]
                        node_region_task_dir = os.path.join(node_task_dir, reg.regionName)
                        os.makedirs(node_region_task_dir, exist_ok=True)
                        cr_set_output_file_base_dir(node, node_region_task_dir)
                        node_output_format = dict(node_state.get("output_format") or {})
                        if str(node_output_format.get("file_format") or "") == 'OPEN_EXR_MULTILAYER':
                            tile_base_name = node_state.get("file_name", "") or self.outputImgName or "render"
                            cr_set_output_file_name(node, _cr_make_output_tile_name(tile_base_name, reg.regionName))
                        else:
                            cr_set_output_file_name(node, node_state.get("file_name", ""))
                        region_targets.append(_cr_make_region_target(
                            node_region_task_dir,
                            node_state["merge_dir"],
                            node_output_format,
                            False,
                        ))

                        for item_index, slot_path in node_state.get("slot_path_items", []):
                            if item_index < len(items) and item_index < len(node.inputs) and node.inputs[item_index].is_linked:
                                base = cr_strip_chunk_suffix(slot_path)
                                cr_set_output_file_item_path(items[item_index], base + reg.regionName + "_")
                self._region_output_targets[reg.index] = region_targets
                ps.CR_cntrnd += 1
                return 1
            else:
                ps.CR_cntrnd += 1
                return -1
        else:
            self.finished = True
            if hasattr(self, "job_context"):
                self.job_context.finished = True
            return 0

    def prepareAllRegions(self, context):
        scn, ps = context.scene, context.scene.chunk_render_settings
        rnd = scn.render
        reg_indices = []
        if ps.CR_select_mode == 'ALL':
            reg_indices = list(range(self.tot_reg))
        elif ps.CR_select_mode == 'CUSTOM':
            reg_indices = cr_parse_custom_indices(ps.CR_custom_indices, self.tot_reg)

        self.allRegions = _cr_build_regions(
            rnd,
            self.outputImgName,
            self._main_task_dir,
            self.num_cols,
            self.num_rows,
            self.base_min_x,
            self.base_max_x,
            self.base_min_y,
            self.base_max_y,
            bleed_px=ps.CR_bleed_pixels,
            render_indices=reg_indices,
        )
        if hasattr(self, "job_context"):
            self.job_context.allRegions = self.allRegions
        return reg_indices

    def modal(self, context, event):
        if event.type == 'TIMER':
            scn, ps = context.scene, context.scene.chunk_render_settings
            if self.stop or not ps.CR_renderGo:
                self.remove_handlers(context)
                return {'CANCELLED'}
            if self.finished or not self.allRegions:
                if ps.CR_save_region:
                    global _cr_pending_merge_data
                    task_root_dirs = {self._main_task_dir}
                    for node_state in self.saveFileOutputs:
                        td = node_state.get("task_dir", "")
                        if td:
                            task_root_dirs.add(td)
                    _cr_pending_merge_data = _cr_make_merge_request(
                        self.allRegions,
                        self._tile_files,
                        int(scn.render.resolution_x * scn.render.resolution_percentage / 100),
                        int(scn.render.resolution_y * scn.render.resolution_percentage / 100),
                        self._start_time,
                        ps.CR_delete_after_merge,
                        getattr(self, "_debug_logging", False),
                        task_root_dirs,
                        self._task_folder_name.rsplit("_", 1)[-1],
                        self.outputFolderAbs,
                        getattr(self, "_main_output_format", {}),
                    )

                    if not bpy.app.timers.is_registered(_cr_auto_merge_timer):
                        bpy.app.timers.register(_cr_auto_merge_timer, first_interval=1.0)
                self.remove_handlers(context)
                ps.CR_renderGo = False
                
                if not ps.CR_save_region:
                    start_time = getattr(self, "_start_time", 0)
                    if start_time > 0:
                        cr_log(f"[Chunk Render] Task completed. Total time: {time.time() - start_time:.2f}s")

                return {'FINISHED'}

            if not self.rendering:
                if not self.render_ready:
                    try:
                        res = self.setRender(context)
                    except Exception as e:
                        return self._cancel_task(context, "[Chunk Render] setRender failed, aborting task", e)
                    if res == 1:
                        self.render_ready = True
                        try:
                            self._invoke_render()
                        except Exception as e:
                            return self._cancel_task(context, "[Chunk Render] Failed to start render, aborting task", e)
                    elif res == 0:
                        self.finished = True
                        if hasattr(self, "job_context"):
                            self.job_context.finished = True
                else:
                    try:
                        self._invoke_render()
                    except Exception as e:
                        return self._cancel_task(context, "[Chunk Render] Failed to start render, aborting task", e)
        return {'PASS_THROUGH'}

    def execute(self, context):
        scn = context.scene
        rnd = scn.render
        ps = scn.chunk_render_settings

        self.job_context = ChunkRenderJobContext()
        self.stop = False
        self.rendering = False
        self.render_ready = False
        self.finished = False
        self.last_rendered_region = None
        self.job_context.allRegions = self.allRegions = []
        self.job_context._tile_files = self._tile_files = {}
        self.job_context._region_output_targets = self._region_output_targets = {}
        self._switched_window = None
        self._switched_area_index = -1
        self._switched_area_orig_type = None
        self._debug_logging = cr_debug_enabled(context)

        ps.CR_msg1 = ""
        ps.CR_cntrnd = 0
        ps.CR_maxrnd = 0
        ps.CR_active_index = -1
        ps.CR_done_count = 0

        current_output_path = bpy.path.abspath(rnd.filepath)
        self.outputFolderAbs = os.path.split(current_output_path)[0]

        self._use_comp_only = _cr_is_default_render_path(rnd.filepath)
        if self._use_comp_only:
            has_valid_comp_output = False
            fallback_base_path = ""
            comp_tree = get_comp_tree(scn)
            if comp_tree is not None:
                for node in comp_tree.nodes:
                    if getattr(node, "type", "") != "OUTPUT_FILE" or getattr(node, "mute", False):
                        continue
                    base_dir = cr_get_output_file_base_dir(node)
                    if str(base_dir).strip() == "":
                        continue
                    items = cr_get_output_file_items(node)
                    if len(items) > 0 or cr_output_file_has_linked_slots(node):
                        fallback_base_path = base_dir
                        has_valid_comp_output = True
                        break
            if not has_valid_comp_output:
                self.report({'ERROR'}, iface_("Output path is invalid. Set a valid output path or enable a valid File Output node in the compositor"))
                return {"CANCELLED"}
            if fallback_base_path == "":
                blend_path = bpy.context.blend_data.filepath
                blend_dir = os.path.dirname(bpy.path.abspath(blend_path)) if blend_path != "" else bpy.app.tempdir
                self.outputFolderAbs = blend_dir
            else:
                self.outputFolderAbs = fallback_base_path

        self.outputImgName = os.path.splitext(os.path.split(bpy.path.abspath(rnd.filepath))[1])[0]
        if self.outputImgName == "":
            blend_base = bpy.path.basename(bpy.context.blend_data.filepath)
            self.outputImgName = os.path.splitext(blend_base)[0] if blend_base != "" else "render"

        self._task_folder_name = f"_chunk_render_task_{int(time.time() * 1000)}"
        self.job_context._task_folder_name = self._task_folder_name
        self._main_task_dir = os.path.join(self.outputFolderAbs, self._task_folder_name)

        ps.CR_oldoutputfilepath = rnd.filepath
        ps.CR_oldPerc = rnd.resolution_percentage
        ps.CR_old_use_border = rnd.use_border
        ps.CR_old_use_crop = rnd.use_crop_to_border
        ps.CR_old_border_min_x = rnd.border_min_x
        ps.CR_old_border_max_x = rnd.border_max_x
        ps.CR_old_border_min_y = rnd.border_min_y
        ps.CR_old_border_max_y = rnd.border_max_y
        try:
            if hasattr(rnd, "compositor_device"):
                ps.CR_oldCompositorDevice = rnd.compositor_device
                rnd.compositor_device = 'CPU'
        except (AttributeError, TypeError, RuntimeError) as e:
            cr_log_debug(f"[Chunk Render][DEBUG] Failed to switch compositor device to CPU: {e}")

        self._main_output_format = _cr_snapshot_output_format(rnd.image_settings)
        self.saveFileOutputs = []
        comp_tree = get_comp_tree(scn)
        if comp_tree:
            file_output_index = 0
            for n in comp_tree.nodes:
                if n.type != 'OUTPUT_FILE':
                    continue
                items = cr_get_output_file_items(n)
                base_dir_raw = cr_get_output_file_base_dir_value(n)
                base_dir_abs = cr_get_output_file_base_dir(n)
                merge_dir = base_dir_abs if base_dir_abs else self.outputFolderAbs
                task_dir_name = f"{self._task_folder_name}_file_output_{file_output_index:02d}"
                self.saveFileOutputs.append({
                    "node_name": n.name,
                    "base_dir": base_dir_raw,
                    "file_name": cr_get_output_file_name(n),
                    "merge_dir": merge_dir,
                    "task_dir": os.path.join(merge_dir, task_dir_name),
                    "slot_path_items": [
                        (item_index, cr_get_output_file_item_path(item))
                        for item_index, item in enumerate(items)
                        if cr_output_file_item_supports_path(item)
                    ],
                    "output_format": _cr_snapshot_output_format(getattr(n, "format", None)),
                })
                file_output_index += 1

        if ps.CR_use_render_border:
            self.base_min_x, self.base_max_x, self.base_min_y, self.base_max_y = get_border_range(rnd, True)
        else:
            self.base_min_x, self.base_max_x, self.base_min_y, self.base_max_y = (0.0, 1.0, 0.0, 1.0)
        ps.CR_saved_border_min_x = self.base_min_x
        ps.CR_saved_border_max_x = self.base_max_x
        ps.CR_saved_border_min_y = self.base_min_y
        ps.CR_saved_border_max_y = self.base_max_y

        sync_level_grid = getattr(ps, "sync_level_grid", None)
        if callable(sync_level_grid):
            _ = sync_level_grid(context)

        self.num_cols, self.num_rows = ps.CR_reg_columns, ps.CR_reg_rows
        self.tot_reg = self.num_cols * self.num_rows
        self.delta_x = (self.base_max_x - self.base_min_x) / self.num_cols
        self.delta_y = (self.base_max_y - self.base_min_y) / self.num_rows

        rnd.use_border = True
        rnd.use_crop_to_border = True

        try:
            reg_indices = self.prepareAllRegions(context)
        except Exception as e:
            self.report({'ERROR'}, iface_("Failed to prepare regions: {error}").format(error=e))
            self._restore_render_settings(context)
            self._cleanup_task_dirs()
            return {"CANCELLED"}

        if not reg_indices:
            self._restore_render_settings(context)
            self._cleanup_task_dirs()
            return {"CANCELLED"}

        self._init_remerge_manifests(context)

        ps.CR_maxrnd = len(reg_indices)
        ps.CR_renderGo = True
        self._start_time = time.time()
        cr_log(f"[Chunk Render] Task started with {ps.CR_maxrnd} tile(s)")

        cr_log_debug(
            f"[Chunk Render][DEBUG] Output directory={self.outputFolderAbs} | Main task directory={self._main_task_dir} | Output name={self.outputImgName} | Compositor-only output={self._use_comp_only}"
        )
        cr_log_debug(
            f"[Chunk Render][DEBUG] Grid={self.num_cols}x{self.num_rows} | Render area=({self.base_min_x:.4f}, {self.base_max_x:.4f}, {self.base_min_y:.4f}, {self.base_max_y:.4f}) | bleed={ps.CR_bleed_pixels}px | File Output node count={len(self.saveFileOutputs)}"
        )

        prefs = context.preferences.addons.get(__package__)
        if prefs and prefs.preferences.show_render_progress:
            switched = self._switch_to_image_editor(context)
            if switched:
                try:
                    self._old_display_mode = context.preferences.view.render_display_type
                    context.preferences.view.render_display_type = 'NONE'
                except (AttributeError, TypeError, RuntimeError):
                    self._old_display_mode = None
            else:
                self._old_display_mode = None
        else:
            self._old_display_mode = None

        self.add_handlers(context)
        return {'RUNNING_MODAL'}


    def _collect_new_files(self, region_index):
        reg = next((r for r in self.allRegions if r.index == region_index), None)
        if reg is None:
            return

        collected = []
        task_id = self._task_folder_name.rsplit("_", 1)[-1]
        targets = self._region_output_targets.get(region_index, [])
        for target in targets:
            root_dir = target.get("root_dir", "")
            merge_dir = target.get("merge_dir", "")
            output_format = dict(target.get("output_format") or {})
            filter_by_region_name = bool(target.get("filter_by_region_name", True))
            if not root_dir or not merge_dir:
                continue
            for fpath in _cr_iter_task_files(root_dir, reg.regionName, filter_by_region_name):
                collected.append(_cr_make_tile_entry(
                    fpath,
                    merge_dir,
                    _cr_make_merge_relpath(os.path.basename(fpath), reg.regionName, task_id),
                    output_format,
                ))
        if collected:
            self._tile_files[region_index] = collected
            self._update_remerge_manifests()

class CHUNK_RENDER_OT_cr_remerge_tiles(Operator):
    bl_idname = "chunk_render.remerge_tiles"
    bl_label = "Re-Merge Tiles"
    bl_description = "Merge existing tile files in the selected folder into final images"
    bl_options = {'REGISTER'}

    def _build_manifest_group_key(self, data):
        return (
            int(data.get("cols", 0) or 0),
            int(data.get("rows", 0) or 0),
            round(float(data.get("base_min_x", 0.0) or 0.0), 10),
            round(float(data.get("base_max_x", 0.0) or 0.0), 10),
            round(float(data.get("base_min_y", 0.0) or 0.0), 10),
            round(float(data.get("base_max_y", 0.0) or 0.0), 10),
            int(data.get("bleed_px", 0) or 0),
            int(data.get("res_x", 0) or 0),
            int(data.get("res_y", 0) or 0),
            str(data.get("target_kind", "") or ""),
            str(data.get("node_name", "") or ""),
            str(data.get("file_name", "") or ""),
        )

    def _build_regions_from_manifest(self, data):
        regions = []
        for record in list(data.get("regions", []) or []):
            reg = _cr_region_from_manifest_record(record)
            reg.render = True
            regions.append(reg)
        return regions

    def _collect_manifest_groups(self, folder, parsed_entries, file_index):
        manifest_paths = [
            fpath for fpath in _cr_walk_sorted_files(folder)
            if os.path.basename(fpath) == _CR_REMERGE_MANIFEST_NAME
        ]

        groups = {}
        for manifest_path in manifest_paths:
            try:
                data = _cr_load_json_file(manifest_path)
            except Exception as e:
                cr_log_debug(f"[Chunk Render][DEBUG] Failed to load re-merge manifest '{manifest_path}': {e}")
                continue

            regions = self._build_regions_from_manifest(data)
            if not regions:
                continue

            group_key = self._build_manifest_group_key(data)
            group = groups.setdefault(group_key, {
                "allRegions": regions,
                "tile_entries": {},
                "output_infos": {},
                "res_x": int(data.get("res_x", 0) or 0),
                "res_y": int(data.get("res_y", 0) or 0),
                "main_output_format": dict(data.get("main_output_format") or {}),
                "default_output_format": dict(data.get("output_format") or {}),
                "cols": int(data.get("cols", 0) or 0),
                "rows": int(data.get("rows", 0) or 0),
            })

            manifest_dir = os.path.dirname(manifest_path)
            for output_info in list(data.get("merge_outputs", []) or []):
                merge_relpath = str(output_info.get("merge_relpath", "") or "")
                if not merge_relpath:
                    continue
                current = group["output_infos"].setdefault(merge_relpath, {
                    "output_format": dict(output_info.get("output_format") or {}),
                    "multilayer_schema": list(output_info.get("multilayer_schema") or []),
                })
                if not current.get("output_format"):
                    current["output_format"] = dict(output_info.get("output_format") or {})
                if not current.get("multilayer_schema"):
                    current["multilayer_schema"] = list(output_info.get("multilayer_schema") or [])

            for tile_record in list(data.get("tiles", []) or []):
                resolved_path = _cr_resolve_manifest_tile_path(folder, manifest_dir, tile_record, file_index)
                if not resolved_path:
                    continue
                merge_relpath = str(tile_record.get("merge_relpath", "") or os.path.basename(resolved_path))
                region_index = int(tile_record.get("region_index", 0) or 0)
                output_info = dict(group["output_infos"].get(merge_relpath) or {})
                group["tile_entries"][(region_index, merge_relpath)] = _cr_make_tile_entry(
                    resolved_path,
                    folder,
                    merge_relpath,
                    output_info.get("output_format") or group["default_output_format"],
                    output_info.get("multilayer_schema"),
                )

        for group in groups.values():
            known_merge_relpaths = set(group["output_infos"].keys())
            if not known_merge_relpaths:
                continue
            cols = int(group.get("cols", 0) or 0)
            rows = int(group.get("rows", 0) or 0)
            for entry in parsed_entries:
                if int(entry.get("cols", 0) or 0) != cols or int(entry.get("rows", 0) or 0) != rows:
                    continue
                merge_relpath = str(entry.get("merge_relpath", "") or "")
                if merge_relpath not in known_merge_relpaths:
                    continue
                region_index = cr_row_col_to_index(entry.get("nrow", 0), entry.get("ncol", 0), cols)
                tile_key = (region_index, merge_relpath)
                if tile_key in group["tile_entries"]:
                    continue
                output_info = dict(group["output_infos"].get(merge_relpath) or {})
                group["tile_entries"][tile_key] = _cr_make_tile_entry(
                    entry["path"],
                    folder,
                    merge_relpath,
                    output_info.get("output_format") or group["default_output_format"],
                    output_info.get("multilayer_schema"),
                )
        return groups

    def execute(self, context):
        scn = context.scene
        rnd = scn.render
        ps = scn.chunk_render_settings
        folder = bpy.path.abspath(ps.CR_remerge_folder).strip()
        if not folder or not os.path.isdir(folder):
            self.report({'ERROR'}, iface_("Re-merge folder path is invalid"))
            return {'CANCELLED'}

        parsed_entries = []
        file_index = defaultdict(list)
        for fpath in _cr_walk_sorted_files(folder):
            filename = os.path.basename(fpath)
            file_index[filename].append(fpath)
            info = _cr_parse_tile_file_identity(fpath)
            if info is not None:
                parsed_entries.append(info)

        if not parsed_entries:
            self.report({'ERROR'}, iface_("No tile files with chunk markers were found in the selected folder"))
            return {'CANCELLED'}

        start_time = time.time()
        processed_groups = 0
        manifest_groups = self._collect_manifest_groups(folder, parsed_entries, file_index)
        if manifest_groups:
            for group in manifest_groups.values():
                if not group["tile_entries"]:
                    continue
                tile_files = defaultdict(list)
                for (region_index, _merge_relpath), entry in sorted(group["tile_entries"].items()):
                    tile_files[region_index].append(entry)
                _cr_do_auto_merge(_cr_make_merge_request(
                    group["allRegions"],
                    dict(tile_files),
                    int(group.get("res_x", 0) or 0),
                    int(group.get("res_y", 0) or 0),
                    start_time,
                    ps.CR_delete_after_merge,
                    cr_debug_enabled(context),
                    [folder],
                    "",
                    folder,
                    group.get("main_output_format"),
                ))
                processed_groups += 1
        if not manifest_groups or processed_groups == 0:
            if ps.CR_use_render_border:
                base_min_x, base_max_x, base_min_y, base_max_y = get_border_range(rnd, True)
            else:
                base_min_x, base_max_x, base_min_y, base_max_y = (0.0, 1.0, 0.0, 1.0)

            output_name = os.path.splitext(os.path.split(bpy.path.abspath(rnd.filepath))[1])[0]
            if not output_name:
                output_name = os.path.basename(folder) or "render"

            grouped_entries = defaultdict(list)
            for entry in parsed_entries:
                grouped_entries[(entry["cols"], entry["rows"])].append(entry)

            for (cols, rows), entries in grouped_entries.items():
                total_tiles = cols * rows
                all_regions = _cr_build_regions(
                    rnd,
                    output_name,
                    folder,
                    cols,
                    rows,
                    base_min_x,
                    base_max_x,
                    base_min_y,
                    base_max_y,
                    bleed_px=ps.CR_bleed_pixels,
                    render_indices=range(total_tiles),
                )
                tile_files = defaultdict(list)
                for entry in entries:
                    region_index = cr_row_col_to_index(entry["nrow"], entry["ncol"], cols)
                    is_multilayer = False
                    schema = []
                    try:
                        is_multilayer = cr_is_multilayer_exr(entry["path"])
                        if is_multilayer:
                            schema = cr_read_multilayer_schema(entry["path"])
                    except Exception as e:
                        cr_log_debug(f"[Chunk Render][DEBUG] Failed to inspect EXR schema during re-merge: {e}")
                    tile_files[region_index].append(_cr_make_tile_entry(
                        entry["path"],
                        folder,
                        entry["merge_relpath"],
                        {"file_format": 'OPEN_EXR_MULTILAYER'} if is_multilayer else {},
                        schema,
                    ))

                _cr_do_auto_merge(_cr_make_merge_request(
                    all_regions,
                    dict(tile_files),
                    int(scn.render.resolution_x * scn.render.resolution_percentage / 100),
                    int(scn.render.resolution_y * scn.render.resolution_percentage / 100),
                    start_time,
                    ps.CR_delete_after_merge,
                    cr_debug_enabled(context),
                    [folder],
                    "",
                    folder,
                    _cr_snapshot_output_format(rnd.image_settings),
                ))
                processed_groups += 1

        self.report({'INFO'}, iface_("Re-merge finished. Processed {count} grid group(s)").format(count=processed_groups))
        return {'FINISHED'}

class CHUNK_RENDER_OT_cr_align_border(Operator):
    bl_idname = "chunk_render.align_border"
    bl_label = "Align Render Border"
    bl_description = "Snap the render border to exact tile-sized pixel boundaries"
    def execute(self, context):
        scn, ps = context.scene, context.scene.chunk_render_settings
        rnd = scn.render
        perc = rnd.resolution_percentage / 100.0
        rx, ry = rnd.resolution_x * perc, rnd.resolution_y * perc
        if rx <= 0 or ry <= 0: return {'CANCELLED'}

        min_x, max_x = min(rnd.border_min_x, rnd.border_max_x), max(rnd.border_min_x, rnd.border_max_x)
        min_y, max_y = min(rnd.border_min_y, rnd.border_max_y), max(rnd.border_min_y, rnd.border_max_y)

        cw_px = round((max_x - min_x) * rx / ps.CR_reg_columns)
        ch_px = round((max_y - min_y) * ry / ps.CR_reg_rows)
        tw_px = cw_px * ps.CR_reg_columns
        th_px = ch_px * ps.CR_reg_rows

        cx_px = (min_x + max_x) * rx / 2.0
        cy_px = (min_y + max_y) * ry / 2.0

        nx1, nx2 = (cx_px - tw_px/2) / rx, (cx_px + tw_px/2) / rx
        ny1, ny2 = (cy_px - th_px/2) / ry, (cy_px + th_px/2) / ry

        rnd.border_min_x, rnd.border_max_x = max(0.0, nx1), min(1.0, nx2)
        rnd.border_min_y, rnd.border_max_y = max(0.0, ny1), min(1.0, ny2)

        ps.CR_saved_border_min_x, ps.CR_saved_border_max_x = rnd.border_min_x, rnd.border_max_x
        ps.CR_saved_border_min_y, ps.CR_saved_border_max_y = rnd.border_min_y, rnd.border_max_y
        
        cr_tag_view3d_redraw()
        return {'FINISHED'}

class CHUNK_RENDER_OT_cr_save_border(Operator):
    bl_idname = "chunk_render.save_border"
    bl_label = "Save Render Border"
    bl_description = "Save the current render border to the history list"
    def execute(self, context):
        ps = context.scene.chunk_render_settings
        item = ps.CR_saved_borders.add()
        item.name = iface_("Region {index}").format(index=len(ps.CR_saved_borders))
        item.min_x, item.max_x = context.scene.render.border_min_x, context.scene.render.border_max_x
        item.min_y, item.max_y = context.scene.render.border_min_y, context.scene.render.border_max_y
        ps.CR_saved_borders_index = len(ps.CR_saved_borders) - 1
        return {'FINISHED'}

class CHUNK_RENDER_OT_cr_remove_border(Operator):
    bl_idname = "chunk_render.remove_border"
    bl_label = "Remove Render Border"
    bl_description = "Delete the selected saved render border"

    @classmethod
    def poll(cls, context):
        ps = getattr(context.scene, "chunk_render_settings", None)
        return ps is not None and len(ps.CR_saved_borders) > 0

    def execute(self, context):
        ps = context.scene.chunk_render_settings
        if len(ps.CR_saved_borders) == 0:
            self.report({'WARNING'}, iface_("No saved border to delete"))
            return {'CANCELLED'}
        idx = ps.CR_saved_borders_index
        if idx < 0 or idx >= len(ps.CR_saved_borders):
            self.report({'WARNING'}, iface_("Index {index} is out of range").format(index=idx))
            return {'CANCELLED'}
        ps.CR_saved_borders.remove(idx)
        ps.CR_saved_borders_index = max(0, idx - 1)
        return {'FINISHED'}

class CHUNK_RENDER_OT_cr_restore_border(Operator):
    bl_idname = "chunk_render.restore_border"
    bl_label = "Restore Render Border"
    bl_description = "Apply the selected saved render border to the current scene"

    @classmethod
    def poll(cls, context):
        ps = getattr(context.scene, "chunk_render_settings", None)
        return ps is not None and len(ps.CR_saved_borders) > 0

    def execute(self, context):
        ps, rnd = context.scene.chunk_render_settings, context.scene.render
        if len(ps.CR_saved_borders) == 0:
            self.report({'WARNING'}, iface_("No saved border to restore"))
            return {'CANCELLED'}
        idx = ps.CR_saved_borders_index
        if idx < 0 or idx >= len(ps.CR_saved_borders):
            self.report({'WARNING'}, iface_("Index {index} is out of range").format(index=idx))
            return {'CANCELLED'}
        item = ps.CR_saved_borders[idx]
        rnd.border_min_x, rnd.border_max_x = item.min_x, item.max_x
        rnd.border_min_y, rnd.border_max_y = item.min_y, item.max_y
        rnd.use_border = ps.CR_use_render_border = True
        return {'FINISHED'}
