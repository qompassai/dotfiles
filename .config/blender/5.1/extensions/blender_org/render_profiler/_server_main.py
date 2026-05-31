"""
Standalone report HTTP server script. 

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

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


def _parse_form_body(raw: bytes) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in raw.decode("utf-8", errors="replace").strip().split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _main() -> None:
    state_dict = globals().get("state_dict")
    pending_mode_dict = globals().get("pending_mode_dict")
    shutdown_event = globals().get("shutdown_event")
    port = globals().get("port")
    if state_dict is None or pending_mode_dict is None or shutdown_event is None or port is None:
        return

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = (self.path.split("?")[0] or "/").rstrip("/") or "/"
            if path == "/":
                html = state_dict.get("full_html") or "<p>No data.</p>"
                body = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif path == "/state.json":
                body = json.dumps(dict(state_dict)).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self) -> None:
            path = (self.path.split("?")[0] or "/").rstrip("/") or "/"
            if path == "/mode":
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b""
                form = _parse_form_body(raw)
                mode = form.get("mode", "").lower()
                if mode in ("off", "viewport", "render"):
                    pending_mode_dict["mode"] = mode
                self.send_response(204)
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format: str, *args: Any) -> None:
            pass

    try:
        server = HTTPServer(("127.0.0.1", port), Handler)
    except OSError:
        return
    server.socket.settimeout(0.5)
    try:
        while not shutdown_event.is_set():
            server.handle_request()
    finally:
        server.server_close()

_main()
