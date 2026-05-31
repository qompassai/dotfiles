"""
Render Profiler - Operators.

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


import bpy  # type: ignore
from bpy.types import Operator  # type: ignore
from typing import Any

from . import properties
from .server_controller import (
    get_report_state,
    init_report_server,
    open_live_report_in_browser,
    set_report_state,
)
from .utils import build_html_report


def _default_report_data(context: bpy.types.Context) -> dict:
    wm = context.window_manager
    mode = wm.render_profiler.report_mode
    mode_lower = mode.lower() if isinstance(mode, str) else "viewport"
    depsgraph = context.evaluated_depsgraph_get()
    build_html_report(depsgraph=depsgraph, scene=context.scene, mode=mode_lower)
    state = get_report_state()
    state["title"] = "Render Profiler Report"
    return state


# -----------------------------------------------------------------------------
# Operators
# -----------------------------------------------------------------------------


class RENDER_PROFILER_OT_open_report(Operator):
    """Open a live HTML report in the browser. It stays linked to Blender and updates when viewport updates or render initiates."""

    bl_idname = "render_profiler.open_report"
    bl_label = "Open Render Profiler Report in Browser"
    bl_options = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        wm = context.window_manager
        wm.render_profiler.report_mode = properties.REPORT_MODE_VIEWPORT
        init_report_server()
        set_report_state(_default_report_data(context))
        url = open_live_report_in_browser()
        if url is None:
            self.report({"ERROR"}, "Could not start report server (ports in use?)")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Report opened: {url}")
        return {"FINISHED"}


class RENDER_PROFILER_OT_stop_profiling(Operator):
    """Stop profiling and live report updates."""

    bl_idname = "render_profiler.stop_profiling"
    bl_label = "Stop Profiling"
    bl_options = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        context.window_manager.render_profiler.report_mode = properties.REPORT_MODE_OFF
        # Push state so the report page updates to "Profiler is disabled" on next poll
        state = get_report_state()
        state["mode"] = "off"
        state["modifiers_html"] = ""
        state["heavy_meshes_html"] = ""
        state["textures_html"] = ""
        state["statistics_html"] = ""
        state["memory_html"] = ""
        state["last_update_html"] = ""
        set_report_state(state)
        self.report({"INFO"}, "Profiling stopped.")
        return {"FINISHED"}


# -----------------------------------------------------------------------------
# Registration
# -----------------------------------------------------------------------------

classes: tuple[type[Any], ...] = (
    RENDER_PROFILER_OT_open_report,
    RENDER_PROFILER_OT_stop_profiling,
)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
