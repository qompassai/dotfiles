"""
Render Profiler - Profile and analyze Blender render and viewport performance.

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

from . import handlers
from . import operators
from . import preferences
from . import properties
from . import server_controller
from . import ui

bl_info = {
    "name": "Render Profiler",
    "author": "multlabs",
    "version": (0, 9, 4),
    "blender": (4, 2, 0),
    "location": "Topbar > Window > Render Profiler Report",
    "description": "Profile and analyze Blender render/viewport performance",
    "warning": "",
    "doc_url": "https://t.me/multlabs",
    "category": "Render",
}


def register() -> None:
    """Register all add-on classes."""
    properties.register()
    operators.register()
    ui.register()
    handlers.register()
    preferences.register()


def unregister() -> None:
    """Unregister all add-on classes and stop the report server."""
    server_controller.stop_report_server()
    preferences.unregister()
    handlers.unregister()
    ui.unregister()
    operators.unregister()
    properties.unregister()


if __name__ == "__main__":
    register()
