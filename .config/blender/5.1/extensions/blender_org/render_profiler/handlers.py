"""
Render Profiler - Blender handlers - get dependency graph data and pass it to the report.

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
import bpy  # type: ignore

from bpy.app.handlers import persistent  # type: ignore
from . import properties
from .server_controller import get_and_clear_pending_mode, get_report_state, set_report_state
from .utils import build_html_report


_last_viewport_update: float = 0.0
_VIEWPORT_THROTTLE_SEC = 1.0
_timer_stop = False


def _get_report_mode() -> str:
    """Current report mode from WindowManager (OFF, VIEWPORT, RENDER)."""
    wm = bpy.context.window_manager   
    return wm.render_profiler.report_mode


def _apply_pending_mode_timer() -> float:
    """Timer callback: apply mode chosen on the web page to Blender and push state"""
    global _timer_stop
    if _timer_stop:
        return None 
    pending = get_and_clear_pending_mode()
    if pending is not None:
        try:
            wm = bpy.context.window_manager
            if wm and getattr(wm, "render_profiler", None):
                wm.render_profiler.report_mode = pending.upper() if pending != "off" else "OFF"
                state = get_report_state()
                state["mode"] = pending
                state["modifiers_html"] = ""
                state["heavy_meshes_html"] = ""
                state["textures_html"] = ""
                state["statistics_html"] = ""
                state["memory_html"] = ""
                state["last_update_html"] = ""
                set_report_state(state)
        except Exception as e:
            print(f"Error applying pending mode: {e}")
    return 0.5


@persistent
def _on_frame_change_post(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph) -> None:
    """When depsgraph.mode == RENDER and report mode is Render, collect data from render depsgraph."""

    if _get_report_mode() != properties.REPORT_MODE_RENDER:
        return
    if getattr(depsgraph, "mode", None) != "RENDER":
        return
    
    build_html_report(depsgraph=depsgraph, scene=scene, mode="render")
    
@persistent
def _on_file_load_post(file: str)-> None:
    """Update live report state when file is loaded."""
    
    if _get_report_mode() != properties.REPORT_MODE_VIEWPORT:
        return

    depsgraph = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene

    build_html_report(depsgraph=depsgraph, scene=scene, mode="viewport")

@persistent
def _on_depsgraph_update(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph) -> None:
    """Update live report state on dependency graph (viewport) updates (only if mode is Viewport, throttled)."""

    if _get_report_mode() != properties.REPORT_MODE_VIEWPORT:
        return
    if getattr(depsgraph, "mode", None) != "VIEWPORT":
        return
        
    global _last_viewport_update
    now = time.time()
    if now - _last_viewport_update < _VIEWPORT_THROTTLE_SEC:
        return

    build_html_report(depsgraph=depsgraph, scene=scene, mode="viewport")



def register() -> None:
    global _timer_stop
    _timer_stop = False
    bpy.app.timers.register(_apply_pending_mode_timer, persistent=True)
    bpy.app.handlers.frame_change_post.append(_on_frame_change_post)
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)
    bpy.app.handlers.load_post.append(_on_file_load_post)


def unregister() -> None:
    global _timer_stop
    _timer_stop = True
    try:
        bpy.app.timers.unregister(_apply_pending_mode_timer)
    except ValueError:
        pass
    if _on_frame_change_post in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(_on_frame_change_post)
    if _on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update)
    if _on_file_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_file_load_post)
