"""
Render Profiler - Report server process and shared state controller.

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

import multiprocessing
import runpy
import socket
import webbrowser
from pathlib import Path
from typing import Any, Optional

_ADDON_DIR = Path(__file__).resolve().parent

# -----------------------------------------------------------------------------
# Shared state dicts
# -----------------------------------------------------------------------------

_manager: Any = None
_state_dict: Any = None
_pending_mode_dict: Any = None
_shutdown_event: Any = None
_server_process: Optional[multiprocessing.Process] = None
_server_port: Optional[int] = None

DEFAULT_PORT = 8765


def get_report_state() -> dict[str, Any]:
    """Return a copy of current report state."""
    if _state_dict is not None:
        return dict(_state_dict)
    return {}


def set_report_state(data: dict[str, Any]) -> None:
    """Update report state. Builds full_html via report.build_report_html before storing."""
    if _state_dict is not None:
        from .report import build_report_html
        data = dict(data)
        data["full_html"] = build_report_html(data)
        _state_dict.clear()
        _state_dict.update(data)


def set_pending_mode(mode: str) -> None:
    """Set mode chosen from the web page (off/viewport/render). Called from server process."""
    if _pending_mode_dict is not None:
        _pending_mode_dict["mode"] = mode.lower()


def get_and_clear_pending_mode() -> Optional[str]:
    """Read and clear pending mode. Called from Blender main thread."""
    if _pending_mode_dict is not None:
        return _pending_mode_dict.pop("mode", None)
    return None


# -----------------------------------------------------------------------------
# Server process lifecycle
# -----------------------------------------------------------------------------


def init_report_server(port: int = DEFAULT_PORT, max_tries: int = 5) -> Optional[int]:
    """
    Create the shared state (Manager and proxy dicts) and reserve a port.
    Used to initialize the server process so that we can write the initial state before the server process is started.
    """
    global _manager, _state_dict, _pending_mode_dict, _shutdown_event, _server_port
    if _manager is not None:
        return _server_port
    ctx = multiprocessing.get_context("spawn")
    for try_port in range(port, port + max_tries):
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            probe.bind(("127.0.0.1", try_port))
            probe.close()
        except OSError:
            continue
        _manager = ctx.Manager()
        _state_dict = _manager.dict()
        _pending_mode_dict = _manager.dict()
        _shutdown_event = _manager.Event()
        _server_port = try_port
        return _server_port
    return None


def start_report_server(port: int = DEFAULT_PORT, max_tries: int = 5) -> Optional[int]:
    """
    Start the report HTTP server process.
    Returns the port bound, or None if the server process failed to start.
    """
    global _manager, _state_dict, _pending_mode_dict, _shutdown_event, _server_process, _server_port
    if _server_process is not None and _server_process.is_alive():
        return _server_port
    if _manager is None:
        if init_report_server(port, max_tries) is None:
            return None
    ctx = multiprocessing.get_context("spawn")
    _server_main_path = str((_ADDON_DIR / "_server_main.py").resolve())
    _server_process = ctx.Process(
        target=runpy.run_path,
        args=(_server_main_path,),
        kwargs={
            "init_globals": {
                "state_dict": _state_dict,
                "pending_mode_dict": _pending_mode_dict,
                "shutdown_event": _shutdown_event,
                "port": _server_port,
            },
        },
        daemon=True,
    )
    _server_process.start()
    return _server_port


def stop_report_server() -> None:
    """Stop the report server process."""
    global _manager, _state_dict, _pending_mode_dict, _shutdown_event, _server_process, _server_port
    if _server_process is None:
        return
    if _shutdown_event is not None:
        _shutdown_event.set()
    _server_process.join(timeout=3.0)
    if _server_process.is_alive():
        _server_process.terminate()
        _server_process.join(timeout=1.0)
    _server_process = None
    _server_port = None
    _state_dict = None
    _pending_mode_dict = None
    _shutdown_event = None
    if _manager is not None:
        try:
            _manager.shutdown()
        except Exception:
            pass
        _manager = None


def open_live_report_in_browser() -> Optional[str]:
    """Ensure the report server is running, and open the browser to the live report URL."""
    port = start_report_server()
    if port is None:
        return None
    if _state_dict is not None and len(_state_dict) == 0:
        from .report import get_default_report_state
        set_report_state(get_default_report_state())
    url = f"http://127.0.0.1:{port}/"
    webbrowser.open(url)
    return url
