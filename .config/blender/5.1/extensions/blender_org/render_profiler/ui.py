"""
Render Profiler - User interface.

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

from . import properties


def _draw_window_menu_item(self: bpy.types.Menu, context: bpy.types.Context) -> None:
    """Draw the "Render Profiler Report" menu item in the Window menu."""
    self.layout.separator()
    self.layout.operator(
        "render_profiler.open_report",
        icon="WINDOW",
        text="Render Profiler Report",
    )
    addon = context.preferences.addons.get("render_profiler")
    if addon and getattr(addon, "preferences", None):
        self.layout.prop(addon.preferences, "font_size", text="Report font size (px)")


def _draw_topbar_profiler(self: bpy.types.Header, context: bpy.types.Context) -> None:
    """Draw profiling indicator and actions in the top bar when profiling is active."""
    wm = context.window_manager
    mode = wm.render_profiler.report_mode

    if mode == properties.REPORT_MODE_OFF:
        return

    region = context.region

    if region.alignment == 'RIGHT':
        return

    mode_label = mode.lower()
    row = self.layout.row(align=True)
    
    row.operator("render_profiler.open_report", text=f"Profiling ({mode_label})", icon="WINDOW")
    row.operator("render_profiler.stop_profiling", text="", icon="PANEL_CLOSE")


def register() -> None:
    bpy.types.TOPBAR_MT_window.append(_draw_window_menu_item)
    bpy.types.TOPBAR_MT_file_context_menu.append(_draw_window_menu_item)
    bpy.types.TOPBAR_HT_upper_bar.append(_draw_topbar_profiler)


def unregister() -> None:
    bpy.types.TOPBAR_MT_window.remove(_draw_window_menu_item)
    bpy.types.TOPBAR_MT_file_context_menu.remove(_draw_window_menu_item)
    bpy.types.TOPBAR_HT_upper_bar.remove(_draw_topbar_profiler)