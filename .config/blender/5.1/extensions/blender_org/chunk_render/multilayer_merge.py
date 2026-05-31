import bpy
import os
import sys
import json
import base64
import shutil

import tempfile
import subprocess
import ctypes
import numpy as np
import OpenImageIO as oiio

try:
    from .tile_common import cr_compute_grid_offsets
except Exception:
    import importlib.util

    _tile_common_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tile_common.py")
    _tile_common_spec = importlib.util.spec_from_file_location("chunk_render_tile_common", _tile_common_path)
    _tile_common_mod = importlib.util.module_from_spec(_tile_common_spec)
    sys.modules[_tile_common_spec.name] = _tile_common_mod
    _tile_common_spec.loader.exec_module(_tile_common_mod)
    cr_compute_grid_offsets = _tile_common_mod.cr_compute_grid_offsets


_CR_DEBUG_LOGGING = False
_CR_MULTILAYER_PREFIX = "[Multilayer EXR Merge]"


def _cr_set_debug_logging(enabled):
    global _CR_DEBUG_LOGGING
    _CR_DEBUG_LOGGING = bool(enabled)


def _cr_translate(message):
    translations = getattr(bpy.app, "translations", None)
    if translations is None:
        return message
    try:
        return translations.pgettext_iface(message)
    except Exception:
        return message


def _cr_fmt(message, **kwargs):
    text = _cr_translate(message)
    return text.format(**kwargs) if kwargs else text


def _cr_log(message, debug=False):
    if debug and not _CR_DEBUG_LOGGING:
        return
    print(message)


def _cr_collect_relevant_stdout(stdout):
    lines = []
    for raw in str(stdout or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(_CR_MULTILAYER_PREFIX):
            lines.append(line)
    return lines


def _cr_log_oiio_detection(prefix=_CR_MULTILAYER_PREFIX):
    if not _CR_DEBUG_LOGGING:
        return

    module_path = str(getattr(oiio, "__file__", "") or "<Built-in module or hidden path>")
    version = str(
        getattr(oiio, "__version__", "")
        or getattr(oiio, "VERSION_STRING", "")
        or getattr(oiio, "VERSION", "")
        or "<Unknown version>"
    )
    _cr_log(f"{prefix}[DEBUG] OIIO version={version}", debug=True)
    _cr_log(f"{prefix}[DEBUG] module={module_path}", debug=True)
    _cr_log(f"{prefix}[DEBUG] python={sys.executable}", debug=True)
    _cr_log(f"{prefix}[DEBUG] blender_binary={getattr(bpy.app, 'binary_path', '')}", debug=True)
    _cr_log(f"{prefix}[DEBUG] cwd={os.getcwd()}", debug=True)
    for idx, path_item in enumerate(sys.path[:8]):
        _cr_log(f"{prefix}[DEBUG] sys.path[{idx}]={path_item}", debug=True)


def _cr_guess_blender_file_format(filepath, is_multilayer=False):
    ext = os.path.splitext(str(filepath or ""))[1].lower()
    if ext == ".exr":
        return 'OPEN_EXR_MULTILAYER' if is_multilayer else 'OPEN_EXR'
    mapping = {
        ".png": "PNG",
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".bmp": "BMP",
        ".tga": "TARGA",
        ".tif": "TIFF",
        ".tiff": "TIFF",
        ".jp2": "JPEG2000",
        ".j2c": "JPEG2000",
        ".webp": "WEBP",
        ".cin": "CINEON",
        ".dpx": "DPX",
        ".hdr": "HDR",
        ".rgb": "IRIS",
    }
    return mapping.get(ext, ext.lstrip(".").upper())


def cr_get_exr_info(filepath):
    info = {
        "file_format": "",
        "image_type": "",
        "channels": 0,
        "is_float": False,
        "use_half_precision": False,
        "is_multilayer": False,
    }
    img_input = None
    try:
        img_input = oiio.ImageInput.open(filepath)
        if img_input is None:
            info["file_format"] = _cr_guess_blender_file_format(filepath)
            return info

        spec = img_input.spec()
        if spec is None:
            info["file_format"] = _cr_guess_blender_file_format(filepath)
            return info

        schema = _cr_extract_oiio_schema_from_spec(spec)
        native_types = [
            str(name or "").strip().lower()
            for name in list(schema.get("channelformats", []) or [])
            if str(name or "").strip()
        ]
        if not native_types:
            native_type = str(_cr_get_schema_native_type_name(schema) or "").strip().lower()
            if native_type:
                native_types.append(native_type)

        subimage_count = 1
        while img_input.seek_subimage(subimage_count, 0):
            subimage_count += 1

        is_multilayer = subimage_count > 1
        is_float = any(name in {"half", "float", "double"} for name in native_types)
        use_half_precision = any(name == "half" for name in native_types) and not any(
            name in {"float", "double"} for name in native_types
        )

        info.update({
            "file_format": _cr_guess_blender_file_format(filepath, is_multilayer=is_multilayer),
            "image_type": 'MULTILAYER' if is_multilayer else 'IMAGE',
            "channels": int(schema.get("nchannels", 0) or 0),
            "is_float": is_float,
            "use_half_precision": use_half_precision,
            "is_multilayer": is_multilayer,
        })
    except Exception:
        info["file_format"] = _cr_guess_blender_file_format(filepath)
    finally:
        if img_input is not None:
            try:
                img_input.close()
            except Exception:
                pass
    return info


def cr_is_multilayer_exr(filepath):
    return bool(cr_get_exr_info(filepath).get("is_multilayer"))



def _cr_format_bytes(num_bytes):
    value = float(max(0, int(num_bytes or 0)))
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    unit_index = 0
    while value >= 1024.0 and unit_index < len(units) - 1:
        value /= 1024.0
        unit_index += 1
    return f"{value:.2f} {units[unit_index]}"


def _cr_get_available_memory_bytes():
    try:
        if os.name == "nt":
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.ullAvailPhys)
        elif hasattr(os, "sysconf"):
            pages = os.sysconf("SC_AVPHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            if int(pages) > 0 and int(page_size) > 0:
                return int(pages) * int(page_size)
    except Exception:
        pass
    return 0


def _cr_estimate_merge_memory_bytes(target_w, target_h, spec_layout):
    total_bytes = 0
    for spec in list(spec_layout or []):
        nchannels = int(spec.get("nchannels", 0) or 0)
        if nchannels <= 0:
            continue
        dtype = _cr_numpy_dtype_from_typedesc_name(_cr_get_schema_native_type_name(spec)) or np.float32
        total_bytes += int(target_w) * int(target_h) * nchannels * np.dtype(dtype).itemsize
    return int(total_bytes)


def _cr_validate_merge_memory_budget(target_w, target_h, spec_layout):
    estimated_bytes = _cr_estimate_merge_memory_bytes(target_w, target_h, spec_layout)
    if estimated_bytes <= 0:
        return

    overhead_bytes = max(int(estimated_bytes * 0.75), 512 * 1024 * 1024)
    required_bytes = estimated_bytes + overhead_bytes
    available_bytes = _cr_get_available_memory_bytes()

    _cr_log(
        f"{_CR_MULTILAYER_PREFIX}[DEBUG] Estimated merge memory={_cr_format_bytes(required_bytes)} | image_buffers={_cr_format_bytes(estimated_bytes)} | available={_cr_format_bytes(available_bytes) if available_bytes > 0 else 'unknown'}",
        debug=True,
    )

    if available_bytes > 0 and required_bytes > available_bytes:
        raise RuntimeError(
            _cr_fmt(
                "Multilayer EXR merge needs about {required}, but only about {available} system memory is available. Reduce resolution/layers or use a machine with more memory",
                required=_cr_format_bytes(required_bytes),
                available=_cr_format_bytes(available_bytes),
            )
        )

    if available_bytes <= 0 and required_bytes >= 8 * 1024 * 1024 * 1024:
        raise RuntimeError(
            _cr_fmt(
                "Multilayer EXR merge needs about {required}. Available system memory could not be detected, so the merge was stopped for safety",
                required=_cr_format_bytes(required_bytes),
            )
        )


def _cr_json_safe(value):

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, bytes):
        return {"__cr_bytes__": base64.b64encode(value).decode("ascii")}
    if isinstance(value, tuple):
        return {"__cr_tuple__": [_cr_json_safe(v) for v in value]}
    if isinstance(value, list):
        return [_cr_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _cr_json_safe(v) for k, v in value.items()}
    return str(value)


def _cr_json_restore(value):
    if isinstance(value, list):
        return [_cr_json_restore(v) for v in value]
    if isinstance(value, dict):
        if "__cr_bytes__" in value:
            try:
                return base64.b64decode(str(value.get("__cr_bytes__", "") or ""))
            except Exception:
                return b""
        if "__cr_tuple__" in value:
            return tuple(_cr_json_restore(v) for v in list(value.get("__cr_tuple__", []) or []))
        return {str(k): _cr_json_restore(v) for k, v in value.items()}
    return value


def _cr_typedesc_to_string(value):
    return str(value or "")


def _cr_typedesc_from_string(value):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return oiio.TypeDesc(text)
    except Exception:
        return None


def _cr_numpy_dtype_from_typedesc_name(value):
    type_name = str(value or "").strip().lower()
    dtype_map = {
        "half": np.float16,
        "float": np.float32,
        "double": np.float64,
        "uint8": np.uint8,
        "int8": np.int8,
        "uint16": np.uint16,
        "int16": np.int16,
        "uint32": np.uint32,
        "int32": np.int32,
    }
    return dtype_map.get(type_name)


def _cr_get_schema_native_type_name(schema):
    channelformats = [str(name or "") for name in list(schema.get("channelformats", []) or [])]
    unique_types = {name for name in channelformats if name}
    if len(unique_types) == 1:
        return next(iter(unique_types))
    if not channelformats:
        return str(schema.get("format", "") or "")
    return ""


def _cr_get_spec_string_attribute(spec, name, default=""):
    try:
        return str(spec.get_string_attribute(name, default) or default)
    except Exception:
        return str(default or "")


def _cr_extract_oiio_schema_from_spec(spec):
    schema = {
        "width": int(getattr(spec, "width", 0) or 0),
        "height": int(getattr(spec, "height", 0) or 0),
        "depth": int(getattr(spec, "depth", 1) or 1),
        "full_width": int(getattr(spec, "full_width", 0) or 0),
        "full_height": int(getattr(spec, "full_height", 0) or 0),
        "full_depth": int(getattr(spec, "full_depth", 1) or 1),
        "tile_width": int(getattr(spec, "tile_width", 0) or 0),
        "tile_height": int(getattr(spec, "tile_height", 0) or 0),
        "tile_depth": int(getattr(spec, "tile_depth", 0) or 0),
        "deep": bool(getattr(spec, "deep", False)),
        "nchannels": int(getattr(spec, "nchannels", 0) or 0),
        "format": _cr_typedesc_to_string(getattr(spec, "format", "")),
        "channelformats": [_cr_typedesc_to_string(name) for name in list(getattr(spec, "channelformats", []) or [])],
        "channelnames": [str(name) for name in list(getattr(spec, "channelnames", []) or [])],
        "alpha_channel": int(getattr(spec, "alpha_channel", -1) or -1),
        "z_channel": int(getattr(spec, "z_channel", -1) or -1),
        "x": int(getattr(spec, "x", 0) or 0),
        "y": int(getattr(spec, "y", 0) or 0),
        "full_x": int(getattr(spec, "full_x", 0) or 0),
        "full_y": int(getattr(spec, "full_y", 0) or 0),
        "subimage_name": _cr_get_spec_string_attribute(spec, "oiio:subimagename") or _cr_get_spec_string_attribute(spec, "name"),
        "extra_attribs": [],
    }
    for attr in list(getattr(spec, "extra_attribs", []) or []):
        try:
            schema["extra_attribs"].append({
                "name": str(getattr(attr, "name", "") or ""),
                "type": _cr_typedesc_to_string(getattr(attr, "type", "")),
                "value": _cr_json_safe(getattr(attr, "value", None)),
            })
        except Exception:
            pass
    return schema



def cr_read_multilayer_schema(filepath):
    img_input = oiio.ImageInput.open(filepath)
    if img_input is None:
        raise RuntimeError(_cr_fmt("Failed to read multilayer EXR: {path}", path=filepath))

    schemas = []
    subimage = 0
    try:
        while True:
            spec = img_input.spec()
            if spec is None:
                raise RuntimeError(_cr_fmt("Failed to read multilayer EXR spec: {path}", path=filepath))
            schemas.append(_cr_extract_oiio_schema_from_spec(spec))
            if not img_input.seek_subimage(subimage + 1, 0):
                break
            subimage += 1
    finally:
        img_input.close()
    return schemas


def _cr_schema_layout_signature(schema_list):
    return [
        {
            "nchannels": int(spec.get("nchannels", 0) or 0),
            "format": str(spec.get("format", "") or ""),
            "channelformats": [str(name) for name in list(spec.get("channelformats", []) or [])],
            "channelnames": [str(name) for name in list(spec.get("channelnames", []) or [])],
            "subimage_name": str(spec.get("subimage_name", "") or ""),
        }
        for spec in list(schema_list or [])
    ]


def _cr_apply_schema_to_output_spec(output_spec, schema, target_w, target_h):
    if schema:
        format_name = _cr_get_schema_native_type_name(schema) or str(schema.get("format", "") or "")
        format_desc = _cr_typedesc_from_string(format_name)
        if format_desc is not None:
            try:
                output_spec.set_format(format_desc)
            except Exception:
                pass

        channel_formats = []
        for value in list(schema.get("channelformats", []) or []):
            typedesc = _cr_typedesc_from_string(value)
            if typedesc is None:
                channel_formats = []
                break
            channel_formats.append(typedesc)
        if channel_formats and len(channel_formats) == int(schema.get("nchannels", 0) or 0):
            try:
                output_spec.channelformats = tuple(channel_formats)
            except Exception:
                pass

        try:
            output_spec.alpha_channel = int(schema.get("alpha_channel", -1) or -1)
        except Exception:
            pass
        try:
            output_spec.z_channel = int(schema.get("z_channel", -1) or -1)
        except Exception:
            pass
        for attr in list(schema.get("extra_attribs", []) or []):
            name = str(attr.get("name", "") or "")
            if not name:
                continue
            value = _cr_json_restore(attr.get("value", None))
            if isinstance(value, list):
                value = tuple(value)
            attr_type = _cr_typedesc_from_string(attr.get("type", ""))
            try:
                if attr_type is not None:
                    output_spec.attribute(name, attr_type, value)
                else:
                    output_spec.attribute(name, value)
            except Exception:
                pass

    for field_name, field_value in (
        ("x", 0),
        ("y", 0),
        ("full_x", 0),
        ("full_y", 0),
        ("full_width", int(target_w)),
        ("full_height", int(target_h)),
        ("depth", 1),
        ("full_depth", int(schema.get("full_depth", 1) or 1) if schema else 1),
    ):
        try:
            setattr(output_spec, field_name, field_value)
        except Exception:
            pass




def cr_run_hidden_multilayer_merge(jobs, debug_logging=False):

    if not jobs:
        return

    _cr_set_debug_logging(debug_logging)
    _cr_log_oiio_detection(f"{_CR_MULTILAYER_PREFIX}[Main Process]")

    blender_bin = bpy.app.binary_path
    if not blender_bin or not os.path.isfile(blender_bin):
        raise RuntimeError(_cr_translate("Blender executable not found, cannot launch background multilayer EXR merge instance"))

    fd, config_path = tempfile.mkstemp(prefix="cr_multilayer_merge_", suffix=".json")
    os.close(fd)
    try:
        with open(config_path, "w", encoding="utf-8") as fh:
            json.dump({"jobs": jobs, "debug_logging": bool(debug_logging)}, fh, ensure_ascii=False, indent=2)

        script_path = os.path.abspath(__file__)
        worker_expr = (
            "import importlib.util;"
            f"spec=importlib.util.spec_from_file_location('chunk_render_multilayer_merge_worker', {script_path!r});"
            "mod=importlib.util.module_from_spec(spec);"
            "spec.loader.exec_module(mod);"
            f"mod.cr_run_multilayer_merge_from_config({config_path!r})"
        )
        cmd = [
            blender_bin,
            "-b",
            "--factory-startup",
            "--python-expr",
            worker_expr,
        ]
        _cr_log(f"{_CR_MULTILAYER_PREFIX}[Main Process][DEBUG] jobs={len(jobs)} | config={config_path}", debug=True)
        _cr_log(f"{_CR_MULTILAYER_PREFIX}[Main Process][DEBUG] cmd={' '.join(cmd)}", debug=True)

        kwargs = {
            "capture_output": True,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "check": False,
        }
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            kwargs["startupinfo"] = startupinfo

        result = subprocess.run(cmd, **kwargs)
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if result.returncode != 0:
            message = stderr or stdout or _cr_fmt("Background Blender exited with code {code}", code=result.returncode)
            raise RuntimeError(message)
        if _CR_DEBUG_LOGGING:
            if stdout:
                print(stdout)
            if stderr:
                print(stderr)
        elif stdout:
            for line in _cr_collect_relevant_stdout(stdout):
                print(line)
    finally:
        try:
            os.remove(config_path)
        except Exception:
            pass


def _get_oiio_output_type(fmt_info):
    color_depth = str((fmt_info or {}).get("color_depth") or "")
    if not color_depth:
        color_depth = '16' if (fmt_info or {}).get("use_half_precision") else '32'
    return oiio.HALF if str(color_depth) == '16' else oiio.FLOAT


def _get_oiio_exr_codec(fmt_info):
    codec = str((fmt_info or {}).get("exr_codec") or "").upper()
    codec_map = {
        'NONE': 'none',
        'ZIP': 'zip',
        'ZIPS': 'zips',
        'PIZ': 'piz',
        'RLE': 'rle',
        'PXR24': 'pxr24',
        'B44': 'b44',
        'B44A': 'b44a',
        'DWAA': 'dwaa',
        'DWAB': 'dwab',
    }
    return codec_map.get(codec, "")


def _inspect_oiio_multilayer_file(filepath):
    return cr_read_multilayer_schema(filepath)



def _read_oiio_multilayer_pixels(filepath, spec_layout):
    img_input = oiio.ImageInput.open(filepath)
    if img_input is None:
        raise RuntimeError(_cr_fmt("Failed to read multilayer EXR: {path}", path=filepath))

    pixels_by_subimage = []
    subimage = 0
    try:
        while True:
            spec = img_input.spec()
            if spec is None:
                raise RuntimeError(_cr_fmt("Failed to read multilayer EXR spec: {path}", path=filepath))
            expected = spec_layout[subimage]
            if int(spec.nchannels) != expected["nchannels"] or [str(name) for name in list(spec.channelnames)] != expected["channelnames"]:
                raise RuntimeError(
                    _cr_fmt("Tile '{path}' multilayer EXR channel layout does not match the first tile", path=filepath)
                )
            native_type_name = _cr_get_schema_native_type_name(expected)
            read_format = _cr_typedesc_from_string(native_type_name) or oiio.FLOAT
            read_dtype = _cr_numpy_dtype_from_typedesc_name(native_type_name) or np.float32
            pixels = np.asarray(img_input.read_image(format=read_format), dtype=read_dtype)
            if pixels.ndim == 2:
                pixels = pixels[:, :, np.newaxis]
            pixels_by_subimage.append(pixels)
            if not img_input.seek_subimage(subimage + 1, 0):
                break
            subimage += 1
    finally:
        img_input.close()

    if len(pixels_by_subimage) != len(spec_layout):
        raise RuntimeError(
            _cr_fmt("Tile '{path}' multilayer EXR subimage count does not match the first tile", path=filepath)
        )
    return pixels_by_subimage



def _load_multilayer_tile_infos(job):
    tiles = []
    row_heights, col_widths = {}, {}
    spec_layout = None

    for tile in job["tiles"]:
        specs = _inspect_oiio_multilayer_file(tile["path"])
        if not specs:
            raise RuntimeError(_cr_fmt("Tile '{path}' does not contain any multilayer EXR channels", path=tile["path"]))

        width = int(specs[0]["width"])
        height = int(specs[0]["height"])
        expected_width = max(1, int(tile.get("expected_width", 1) or 1))
        expected_height = max(1, int(tile.get("expected_height", 1) or 1))
        if width <= 0 or height <= 0:
            _cr_log(
                f"{_CR_MULTILAYER_PREFIX} "
                f"{_cr_fmt('Warning: failed to read tile size, using fallback region size {width}x{height}: {path}', width=expected_width, height=expected_height, path=tile['path'])}"
            )

            width, height = expected_width, expected_height

        for spec in specs[1:]:
            if int(spec["width"]) != width or int(spec["height"]) != height:
                raise RuntimeError(
                    _cr_fmt("Tile '{path}' multilayer EXR subimage sizes are inconsistent", path=tile["path"])
                )

        current_layout = _cr_schema_layout_signature(specs)
        if spec_layout is None:
            spec_layout = list(specs)
        elif current_layout != _cr_schema_layout_signature(spec_layout):
            raise RuntimeError(
                _cr_fmt("Tile '{path}' multilayer EXR channel layout does not match the first tile", path=tile["path"])
            )


        crop_left = tile.get("crop_left_px")
        crop_right = tile.get("crop_right_px")
        crop_top = tile.get("crop_top_px")
        crop_bottom = tile.get("crop_bottom_px")
        if crop_left is None:
            crop_left = round(float(tile.get("crop_left_ratio", 0.0)) * width)
        if crop_right is None:
            crop_right = round(float(tile.get("crop_right_ratio", 0.0)) * width)
        if crop_top is None:
            crop_top = round(float(tile.get("crop_top_ratio", 0.0)) * height)
        if crop_bottom is None:
            crop_bottom = round(float(tile.get("crop_bottom_ratio", 0.0)) * height)
        crop_left = max(0, min(int(crop_left), width))
        crop_right = max(0, min(int(crop_right), width - crop_left))
        crop_top = max(0, min(int(crop_top), height))
        crop_bottom = max(0, min(int(crop_bottom), height - crop_top))

        core_w = width - crop_left - crop_right
        core_h = height - crop_top - crop_bottom
        if core_w <= 0 or core_h <= 0:
            raise RuntimeError(
                _cr_fmt(
                    "Tile '{path}' has an invalid size after cropping: source={width}x{height}, expected={expected_width}x{expected_height}, crop(LRTB)=({crop_left},{crop_right},{crop_top},{crop_bottom})",
                    path=tile["path"],
                    width=width,
                    height=height,
                    expected_width=expected_width,
                    expected_height=expected_height,
                    crop_left=crop_left,
                    crop_right=crop_right,
                    crop_top=crop_top,
                    crop_bottom=crop_bottom,
                )
            )

        row = int(tile["nrow"])
        col = int(tile["ncol"])
        prev_h = row_heights.get(row)
        prev_w = col_widths.get(col)
        if prev_h is not None and prev_h != core_h:
            raise RuntimeError(_cr_fmt("Tile heights in row {row} are inconsistent, cannot merge as multilayer EXR", row=row))
        if prev_w is not None and prev_w != core_w:
            raise RuntimeError(_cr_fmt("Tile widths in column {col} are inconsistent, cannot merge as multilayer EXR", col=col))

        row_heights[row] = core_h
        col_widths[col] = core_w
        tiles.append({
            "path": tile["path"],
            "nrow": row,
            "ncol": col,
            "crop_left": crop_left,
            "crop_right": crop_right,
            "crop_top": crop_top,
            "crop_bottom": crop_bottom,
            "core_w": core_w,
            "core_h": core_h,
        })

    _cr_log(
        f"{_CR_MULTILAYER_PREFIX}[DEBUG] Loaded {len(tiles)} tile(s) | rows={len(row_heights)} | cols={len(col_widths)} | subimages={len(spec_layout or [])}",
        debug=True,
    )
    return tiles, row_heights, col_widths, spec_layout or []


def _merge_job_with_oiio(job):
    tiles, row_heights, col_widths, spec_layout = _load_multilayer_tile_infos(job)

    # OIIO numpy arrays use top-to-bottom y order, so nrow=0 must start at the top.
    row_y_offsets, col_x_offsets, target_w, target_h = cr_compute_grid_offsets(
        row_heights,
        col_widths,
        top_to_bottom=True,
    )
    _cr_validate_merge_memory_budget(target_w, target_h, spec_layout)

    merged_subimages = []

    for spec in spec_layout:
        dtype = _cr_numpy_dtype_from_typedesc_name(_cr_get_schema_native_type_name(spec)) or np.float32
        merged_subimages.append(np.zeros((target_h, target_w, int(spec["nchannels"])), dtype=dtype))


    for tile in tiles:
        tile["offset_x"] = col_x_offsets.get(tile["ncol"], 0)
        tile["offset_y"] = row_y_offsets.get(tile["nrow"], 0)
        tile_pixels = _read_oiio_multilayer_pixels(tile["path"], spec_layout)
        src_y1 = int(tile["crop_top"])
        src_y2 = src_y1 + int(tile["core_h"])
        src_x1 = int(tile["crop_left"])
        src_x2 = src_x1 + int(tile["core_w"])


        dst_y1 = int(tile["offset_y"])
        dst_y2 = dst_y1 + int(tile["core_h"])
        dst_x1 = int(tile["offset_x"])
        dst_x2 = dst_x1 + int(tile["core_w"])

        for subimage_index, pixels in enumerate(tile_pixels):
            cropped = pixels[src_y1:src_y2, src_x1:src_x2, :]
            if cropped.shape[0] != tile["core_h"] or cropped.shape[1] != tile["core_w"]:
                raise RuntimeError(
                    _cr_fmt("Tile '{path}' has an unexpected multilayer EXR cropped size", path=tile["path"])
                )
            merged_subimages[subimage_index][dst_y1:dst_y2, dst_x1:dst_x2, :] = cropped

    fmt_info = job.get("output_format") or {}
    output_type = _get_oiio_output_type(fmt_info)
    schema_layout = list(job.get("multilayer_schema") or spec_layout)
    if _cr_schema_layout_signature(schema_layout) != _cr_schema_layout_signature(spec_layout):
        schema_layout = list(spec_layout)
    compression = _get_oiio_exr_codec(fmt_info)

    out_path = job["output_path"]
    temp_output_dir = tempfile.mkdtemp(prefix="cr_multilayer_out_")
    produced = os.path.join(temp_output_dir, "merged.exr")
    try:
        output = oiio.ImageOutput.create(produced)
        if output is None:
            raise RuntimeError(_cr_fmt("Failed to create multilayer EXR output file: {path}", path=produced))
        try:
            for subimage_index, (schema, pixels) in enumerate(zip(schema_layout, merged_subimages)):
                output_spec = oiio.ImageSpec(int(target_w), int(target_h), int(schema["nchannels"]), output_type)
                output_spec.channelnames = tuple(schema.get("channelnames", []))
                _cr_apply_schema_to_output_spec(output_spec, schema, target_w, target_h)
                if compression:
                    output_spec.attribute("compression", compression)
                mode = "Create" if subimage_index == 0 else "AppendSubimage"
                if not output.open(produced, output_spec, mode=mode):
                    raise RuntimeError(output.geterror() or _cr_fmt("Failed to open multilayer EXR output file: {path}", path=produced))
                if not output.write_image(np.ascontiguousarray(pixels)):
                    raise RuntimeError(output.geterror() or _cr_fmt("Failed to write multilayer EXR output file: {path}", path=produced))
        finally:
            output.close()

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        if os.path.exists(out_path):
            os.remove(out_path)
        shutil.move(produced, out_path)
        _cr_log(f"{_CR_MULTILAYER_PREFIX} {_cr_fmt('Written output: {path}', path=out_path)}")

    finally:
        shutil.rmtree(temp_output_dir, ignore_errors=True)



def _merge_job(job):
    _cr_log(
        f"{_CR_MULTILAYER_PREFIX}[DEBUG] Using OpenImageIO path | output={job.get('output_path', '')} | tiles={len(job.get('tiles', []))}",
        debug=True,
    )
    return _merge_job_with_oiio(job)


def cr_run_multilayer_merge_from_config(config_path):
    with open(config_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    _cr_set_debug_logging(data.get("debug_logging", False))
    _cr_log_oiio_detection(f"{_CR_MULTILAYER_PREFIX}[Worker]")
    jobs = data.get("jobs", [])
    _cr_log(f"{_CR_MULTILAYER_PREFIX}[Worker][DEBUG] jobs={len(jobs)} | config={config_path}", debug=True)

    if not jobs:
        return
    for job in jobs:
        _merge_job(job)
