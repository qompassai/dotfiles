# SPDX-License-Identifier: GPL-3.0-or-later
"""Cache management for onion skin overlays."""

from collections import OrderedDict
import gpu
from gpu_extras.batch import batch_for_shader

# Onion skin frame cache
_shader = None
_frame_cache = OrderedDict()   # {frame: (verts, indices, prim_type)}
_batch_cache = {}              # {frame: gpu_batch}
_max_cache_size = 500
_last_frame = -999

# Ghost marker cache
_ghost_markers = []   # [(frame, verts, indices, prim_type), ...]
_ghost_batches = {}   # {index: gpu_batch}


def get_shader():
    """Get or create the GPU shader."""
    global _shader
    if _shader is None:
        _shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    return _shader


# --- Frame cache ---

def clear_cache():
    """Clear all onion skin frame data."""
    global _last_frame
    _frame_cache.clear()
    _batch_cache.clear()
    _last_frame = -999


def get_last_frame():
    return _last_frame


def set_last_frame(frame):
    global _last_frame
    _last_frame = frame


def is_frame_cached(frame):
    return frame in _frame_cache


def add_to_cache(frame, verts, indices, prim_type):
    """Add mesh data to the frame cache with LRU eviction."""
    if not verts or not indices:
        return

    _frame_cache[frame] = (verts, indices, prim_type)
    _frame_cache.move_to_end(frame)
    _batch_cache.pop(frame, None)

    while len(_frame_cache) > _max_cache_size:
        old_frame = next(iter(_frame_cache))
        del _frame_cache[old_frame]
        _batch_cache.pop(old_frame, None)


def get_batch(frame):
    """Get GPU batch for frame, building lazily if needed."""
    if frame in _batch_cache:
        return _batch_cache[frame]

    data = _frame_cache.get(frame)
    if data is None:
        return None

    verts, indices, prim_type = data
    batch = batch_for_shader(get_shader(), prim_type, {"pos": verts}, indices=indices)
    _batch_cache[frame] = batch
    return batch


# --- Ghost markers ---

def add_ghost_marker(frame, verts, indices, prim_type):
    """Add a persistent ghost marker."""
    _ghost_markers.append((frame, verts, indices, prim_type))


def clear_ghost_markers():
    """Clear all ghost markers."""
    _ghost_markers.clear()
    _ghost_batches.clear()


def get_ghost_markers():
    """Return the list of ghost markers."""
    return _ghost_markers


def get_ghost_batch(index):
    """Get GPU batch for ghost marker at index, building lazily."""
    if index in _ghost_batches:
        return _ghost_batches[index]

    if index < 0 or index >= len(_ghost_markers):
        return None

    _, verts, indices, prim_type = _ghost_markers[index]
    batch = batch_for_shader(get_shader(), prim_type, {"pos": verts}, indices=indices)
    _ghost_batches[index] = batch
    return batch


# --- Cleanup ---

def cleanup():
    global _shader
    _shader = None
    clear_cache()
    clear_ghost_markers()
