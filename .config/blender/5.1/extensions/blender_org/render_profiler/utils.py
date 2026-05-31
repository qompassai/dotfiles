"""
Render Profiler - Shared utilities for building report data.

Copyright (C) 2026 multlabs (crantisz@gmail.com, to@multlabs.com)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import time
from pathlib import Path

import bpy  # type: ignore

from . import preferences
from .profiling import (
    collect_curves_memory,
    collect_heavy_meshes,
    collect_modifier_times_by_object,
    collect_other_objects_memory,
    collect_textures,
)
from .report import (
    build_heavy_meshes_table_html,
    build_memory_usage_html,
    build_modifier_table_html,
    build_statistics_html,
    build_textures_table_html,
)
from .server_controller import get_report_state, set_report_state


def _last_update_line(label: str, update_time: int) -> str:
    """Return HTML line for 'Last update' with a span that JS can update to 'X ago'."""
    return f'<strong>{label}</strong> <span class="last-update-ago" data-time="{update_time}">just now</span>'


def _blend_file_name() -> str:
    """Current .blend file name or 'Unsaved'."""
    fp = bpy.data.filepath or False
    if not fp:
        return "Unsaved"
    return Path(fp).name


def build_html_report(depsgraph: bpy.types.Depsgraph, scene: bpy.types.Scene, mode: str) -> None:
    """Build HTML report from depsgraph data and update report state."""
    update_time = int(time.time())

    state = get_report_state()
    state["file_name"] = _blend_file_name()
    state["scene_name"] = scene.name
    state["view_layer_name"] = bpy.context.view_layer.name
    state["mode"] = mode
    state["last_update_time"] = update_time
    state["font_size_pct"] = preferences.get_report_font_size()
    label = "Last render initialized:" if mode == "render" else "Last viewport update:"
    state["last_update_html"] = _last_update_line(label, update_time)
    mod_rows: list = []
    heavy_rows: list = []
    tex_rows: list = []

    try:
        mod_rows = collect_modifier_times_by_object(depsgraph=depsgraph)
        state["modifiers_html"] = (
            "<p>Modifier evaluation time by object. Multiple modifiers may run in parallel, execution time is not a reliable metric.</p>"
            + build_modifier_table_html(mod_rows)
        )
    except Exception as e:
        state["modifiers_html"] = f"<p>Could not collect profiler data. {e}</p>"

    try:
        heavy_rows = collect_heavy_meshes(depsgraph=depsgraph)
        state["heavy_meshes_html"] = (
            "<p>Mesh size by object sorted by triangles, heaviest first.</p>"
            + build_heavy_meshes_table_html(heavy_rows)
        )
    except Exception as e:
        state["heavy_meshes_html"] = f"<p>Could not collect mesh data. {e}</p>"

    try:
        tex_rows = collect_textures(context=bpy.context, scene=scene)
        state["textures_html"] = (
            "<p>Texture memory sorted by size expected to be on GPU.</p>"
            + build_textures_table_html(tex_rows)
        )
    except Exception as e:
        state["textures_html"] = f"<p>Could not collect texture data. {e}</p>"

    try:
        curves_rows = collect_curves_memory(depsgraph=depsgraph)
        other_rows = collect_other_objects_memory(depsgraph=depsgraph)
        state["memory_html"] = (
            "<p>Estimated memory usage sorted by size. Should be less than actual memory usage. Does not include data such as volumes, BVH, etc.</p>"
            + build_memory_usage_html(
            tex_rows=tex_rows,
            heavy_rows=heavy_rows,
            curves_rows=curves_rows,
            other_rows=other_rows,
        ))
    except Exception as e:
        state["memory_html"] = f"<p>Could not build memory usage table. {e}</p>"

    num_objects = len(depsgraph.objects)
    num_instances = len(depsgraph.object_instances) - num_objects
    depsgraph_debug = depsgraph.debug_stats()

    stats = {
        "modifier_total_ms": sum(r.get("execution_time_ms", 0) for r in mod_rows),
        "total_vertices": sum(r.get("vertices", 0) for r in heavy_rows),
        "total_edges": sum(r.get("edges", 0) for r in heavy_rows),
        "total_faces": sum(r.get("faces", 0) for r in heavy_rows),
        "total_tris": sum(r.get("tris", 0) for r in heavy_rows),
        "num_objects": num_objects,
        "num_instances": max(0, num_instances),
        "texture_total_kb": sum(r.get("size_kb", 0) for r in tex_rows),
        "depsgraph_debug": depsgraph_debug,
    }
    state["statistics_html"] = (
        "<p>Combined totals from all profilers and dependency graph stats.</p>"
        + build_statistics_html(stats)
    )
    set_report_state(state)
