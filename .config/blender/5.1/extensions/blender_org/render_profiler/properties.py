"""
Render Profiler - Property definitions.

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
from bpy.props import EnumProperty, PointerProperty  # type: ignore
from bpy.types import PropertyGroup  # type: ignore
from typing import Any


REPORT_MODE_OFF = "OFF"
REPORT_MODE_VIEWPORT = "VIEWPORT"
REPORT_MODE_RENDER = "RENDER"

REPORT_MODE_ITEMS = (
    (REPORT_MODE_OFF, "Off", "No automatic updates"),
    (REPORT_MODE_VIEWPORT, "Viewport", "Update on dependency graph (viewport) updates"),
    (REPORT_MODE_RENDER, "Render", "Update when render finishes"),
)

# Stored in Python so it persists across New/Load 
_report_mode: str = REPORT_MODE_OFF


def _get_report_mode_prop(_self: Any) -> int:
    """Return enum index (Blender EnumProperty getter expects int)."""
    identifiers = [item[0] for item in REPORT_MODE_ITEMS]
    try:
        return identifiers.index(_report_mode)
    except ValueError:
        return 0


def _set_report_mode_prop(_self: Any, value: int) -> None:
    """Receive enum index and store corresponding mode string."""
    global _report_mode
    if 0 <= value < len(REPORT_MODE_ITEMS):
        _report_mode = REPORT_MODE_ITEMS[value][0]
    else:
        _report_mode = REPORT_MODE_VIEWPORT


class RenderProfilerWMProperties(PropertyGroup):
    """WindowManager settings for the live report (mode switcher)."""

    report_mode: EnumProperty(  # type: ignore
        name="Report updates",
        description="When to update the live report page",
        items=REPORT_MODE_ITEMS,
        default=REPORT_MODE_OFF,
        get=_get_report_mode_prop,
        set=_set_report_mode_prop,
    )


classes: tuple[type[Any], ...] = (
    RenderProfilerWMProperties,
)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.render_profiler = PointerProperty(
        type=RenderProfilerWMProperties,
        name="Render Profiler",
        description="Render Profiler window settings",
    )


def unregister() -> None:
    del bpy.types.WindowManager.render_profiler
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
