"""
Render Profiler - Convert collected profiling data to HTML report.

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

import html as html_module
from pathlib import Path
from typing import Any, Optional

_ADDON_DIR = Path(__file__).resolve().parent
_TEMPLATES_DIR = _ADDON_DIR / "templates"
_STATIC_DIR = _ADDON_DIR / "static"

POLL_INTERVAL_MS = 1000


def escape(s: str) -> str:
    """Escape string for safe use in HTML."""
    return html_module.escape(s, quote=True)


def _load_template(name: str) -> Optional[str]:
    """Load a template file from render_profiler/templates/. Returns None if not found."""
    path = _TEMPLATES_DIR / name
    try:
        if path.exists():
            return path.read_text(encoding="utf-8")
    except Exception:
        pass
    return None


def _load_poll_script(poll_interval_ms: int) -> str:
    """Load report_poll.js and inject POLL_INTERVAL_MS. Returns empty string if file missing."""
    path = _STATIC_DIR / "report_poll.js"
    try:
        if path.exists():
            return path.read_text(encoding="utf-8").replace("__POLL_INTERVAL_MS__", str(poll_interval_ms))
    except Exception:
        pass
    return ""


def _load_style_css() -> str:
    """Load style.css for inline injection. Returns empty string if file missing."""
    path = _STATIC_DIR / "style.css"
    try:
        if path.exists():
            return path.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""


def _load_favicon_link() -> str:
    """Load favicon.ico and return a link tag with inline data URL, or empty string if missing."""
    import base64
    path = _STATIC_DIR / "favicon.ico"
    try:
        if path.exists():
            b64 = base64.b64encode(path.read_bytes()).decode("ascii")
            return f'<link rel="icon" href="data:image/x-icon;base64,{b64}" type="image/x-icon">'
    except Exception:
        pass
    return ""


def _pct_bar_color(pct: float) -> str:
    """Return HSL color for progress bar: green (0%) → yellow → red (50%+)."""
    if pct >= 50.0:
        hue = 0.0
    else:
        hue = 120.0 * (1.0 - pct / 50.0)  
    return f"hsl({hue:.0f}, 85%, 25%)"


# -----------------------------------------------------------------------------
# Modifiers tab
# -----------------------------------------------------------------------------

def build_modifier_table_html(rows: list[dict[str, Any]]) -> str:
    """
    Build HTML table from profiling data
    """
    if not rows:
        return "<p>No objects with modifiers in this view layer.</p>"
    total_ms = sum(r["execution_time_ms"] for r in rows) or 1.0
    total_time_cell = (
        f'<td class="exec-time-bold">{total_ms / 1000:.2f} s</td>'
        if total_ms >= 1000
        else f"<td>{total_ms:.2f} ms</td>"
    )
    total_pct_cell = (
        '<td class="pct-cell">'
        '<div class="pct-bar" style="width:100%;background:hsl(0,85%,25%);"></div>'
        '<span class="pct-text">100%</span></td>'
    )
    lines = [
        "<table>",
        "<thead><tr><th>Object</th><th>Execution time</th><th>Share %</th><th>Modifiers</th></tr></thead>",
        "<tbody>",
        f'<tr class="total-row"><td>Total</td>{total_time_cell}{total_pct_cell}<td>—</td></tr>',
    ]
    for r in rows:
        name = escape(r["object_name"])
        instance_count = r.get("instance_count", 1)
        if instance_count > 1:
            name = f"{name} <span class='instance-count'>{instance_count:,} instances</span>"
        ms = r["execution_time_ms"]
        if ms >= 1000:
            time_cell = f'<td class="exec-time-bold">{ms / 1000:.2f} s</td>'
        else:
            time_cell = f"<td>{ms:.2f} ms</td>"
        pct = (ms / total_ms) * 100.0
        bar_color = _pct_bar_color(pct)
        pct_cell = (
            f'<td class="pct-cell">'
            f'<div class="pct-bar" style="width:{pct:.1f}%;background:{bar_color};"></div>'
            f'<span class="pct-text">{pct:.1f}%</span>'
            f"</td>"
        )
        mods = r.get("modifiers", [])
        mod_str = ", ".join(escape(m.get("name", m.get("type", "?"))) for m in mods)
        lines.append(
            f"<tr><td>{name}</td>"
            f"{time_cell}"
            f"{pct_cell}"
            f"<td>{mod_str}</td></tr>"
        )
    lines.append("</tbody></table>")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Heavy meshes tab
# -----------------------------------------------------------------------------

def build_heavy_meshes_table_html(rows: list[dict[str, Any]]) -> str:
    """Build HTML table from heavy-mesh data: object name, vertices, share %, edges, faces, tris."""
    if not rows:
        return "<p>No mesh objects in this view layer.</p>"
    total_verts = sum(r.get("vertices", 0) for r in rows) 
    total_edges = sum(r.get("edges", 0) for r in rows)
    total_faces = sum(r.get("faces", 0) for r in rows)
    total_tris = sum(r.get("tris", 0) for r in rows)
    total_pct_cell = (
        '<td class="pct-cell">'
        '<div class="pct-bar" style="width:100%;background:hsl(0,85%,25%);"></div>'
        '<span class="pct-text">100%</span></td>'
    )
    lines = [
        "<table>",
        "<thead><tr><th>Object</th><th>Vertices</th><th>Share %</th><th>Edges</th><th>Faces</th><th>Triangles</th></tr></thead>",
        "<tbody>",
        f'<tr class="total-row"><td>Total</td><td>{total_verts:,}</td>{total_pct_cell}<td>{total_edges:,}</td><td>{total_faces:,}</td><td>{total_tris:,}</td></tr>',
    ]
    for r in rows:
        name = escape(r["object_name"])
        instance_count = r.get("instance_count", 1)
        if instance_count > 1:
            name = f"{name} <span class='instance-count'>{instance_count} instances</span>"
        v = r.get("vertices", 0)
        e = r.get("edges", 0)
        f = r.get("faces", 0)
        t = r.get("tris", 0)
        pct = (v / total_verts) * 100.0
        bar_color = _pct_bar_color(pct)
        pct_cell = (
            f'<td class="pct-cell">'
            f'<div class="pct-bar" style="width:{pct:.1f}%;background:{bar_color};"></div>'
            f'<span class="pct-text">{pct:.1f}%</span>'
            f"</td>"
        )
        lines.append(f"<tr><td>{name}</td><td>{v:,}</td>{pct_cell}<td>{e:,}</td><td>{f:,}</td><td>{t:,}</td></tr>")
    lines.append("</tbody></table>")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Textures tab
# -----------------------------------------------------------------------------

def build_textures_table_html(rows: list[dict[str, Any]]) -> str:
    """Build HTML table: texture name, materials, size, share %, dimensions, pixel format."""
    if not rows:
        return "<p>No textures in the project.</p>"
    total_kb = sum(r.get("size_kb", 0) for r in rows) or 1.0
    total_size_str = f"<b>{total_kb / 1024:,.1f} MB</b>" if total_kb >= 1024 else f"<b>{total_kb:,.0f} KB</b>"
    total_pct_cell = (
        '<td class="pct-cell">'
        '<div class="pct-bar" style="width:100%;background:hsl(0,85%,25%);"></div>'
        '<span class="pct-text">100%</span></td>'
    )
    lines = [
        "<table>",
        "<thead><tr><th>Texture</th><th>Materials</th><th>Size (KB)</th><th>Share %</th><th>Dimensions</th><th>Format</th></tr></thead>",
        "<tbody>",
        f'<tr class="total-row"><td>Total</td><td>—</td><td>{total_size_str}</td>{total_pct_cell}<td>—</td><td>—</td></tr>',
    ]
    for r in rows:
        name = escape(r.get("texture_name", "?"))
        materials = r.get("materials", [])
        mat_str = ", ".join(escape(m) for m in materials) if materials else "—"
        size_kb = r.get("size_kb", 0)
        pct = (size_kb / total_kb) * 100.0
        bar_color = _pct_bar_color(pct)
        pct_cell = (
            f'<td class="pct-cell">'
            f'<div class="pct-bar" style="width:{pct:.1f}%;background:{bar_color};"></div>'
            f'<span class="pct-text">{pct:.1f}%</span>'
            f"</td>"
        )
        dims = escape(r.get("dimensions", "—"))
        pf = r.get("pixel_format")
        bpp = r.get("bytes_per_pixel")
        if pf is not None and bpp is not None:
            fmt = escape(f"{pf} ({int(bpp)} B/px)")
        else:
            fmt = "—"
        size_str = f"<b>{size_kb / 1024:,.1f} MB</b>" if size_kb >= 1024 else f"{size_kb:,.0f} KB"
        lines.append(
            f"<tr><td>{name}</td><td>{mat_str}</td><td>{size_str}</td>{pct_cell}<td>{dims}</td><td>{fmt}</td></tr>"
        )
    lines.append("</tbody></table>")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Statistics tab
# -----------------------------------------------------------------------------


def build_statistics_html(stats: dict[str, Any]) -> str:
    """Build Statistics tab: combined totals from all profilers, object/instance counts, depsgraph.debug_stats()."""
    modifier_total_ms = stats.get("modifier_total_ms", 0) 
    total_vertices = stats.get("total_vertices", 0) 
    total_edges = stats.get("total_edges", 0) 
    total_faces = stats.get("total_faces", 0) 
    total_tris = stats.get("total_tris", 0) 
    num_objects = stats.get("num_objects", 0) 
    num_instances = stats.get("num_instances", 0)
    texture_total_kb = stats.get("texture_total_kb", 0)
    depsgraph_debug = stats.get("depsgraph_debug", "") 

    time_str = f"{modifier_total_ms / 1000:.2f} s" if modifier_total_ms >= 1000 else f"{modifier_total_ms:.2f} ms"
    lines = [
        "<table>",
        "<thead><tr><th>Source</th><th>Value</th></tr></thead>",
        "<tbody>",
        f"<tr><td>Modifier execution time (total)</td><td>{time_str}</td></tr>",
        f"<tr><td>Vertices</td><td>{total_vertices:,}</td></tr>",
        f"<tr><td>Edges</td><td>{total_edges:,}</td></tr>",
        f"<tr><td>Faces</td><td>{total_faces:,}</td></tr>",
        f"<tr><td>Triangles</td><td>{total_tris:,}</td></tr>",
        f"<tr><td>Objects</td><td>{num_objects:,}</td></tr>",
        f"<tr><td>Instances</td><td>{num_instances:,}</td></tr>",
        f"<tr><td>Texture memory total</td><td>{texture_total_kb:,.0f} KB</td></tr>",
        f"<tr><td>Dependency graph stats</td><td>{escape(depsgraph_debug)}</td></tr>",
        "</tbody></table>",
    ]
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Memory size calculation 
# -----------------------------------------------------------------------------

_MESH_BYTES_VERTEX = 12   # 3 * 4 (position )
_MESH_BYTES_EDGE = 8     # 2 * 4
_MESH_BYTES_LOOP = 20    # 8 (vertex_index, edge_index) + 12 (normal)
_MESH_BYTES_POLYGON = 16  # 4 * 4 (typical quad)


def _fmt_size_kb(size_kb: float) -> str:
    """Format size as Bytes, KB, or MB."""
    if size_kb >= 1024:
        return f"{size_kb / 1024:,.1f} MB"
    if size_kb >= 1:
        return f"{size_kb:,.0f} KB"
    size_b = round(size_kb * 1024)
    return f"{size_b:,} B"

_OBJECT_ICONS: dict[str, str] = {
    "MESH": "icon-mesh",
    "CAMERA": "icon-camera",
    "LIGHT": "icon-light",
    "EMPTY": "icon-empty",
    "VOLUME": "icon-volume",
    "LATTICE": "icon-lattice",
    "ARMATURE": "icon-armature",
    "SPEAKER": "icon-speaker",
    "LIGHT_PROBE": "icon-lightprobe",
    "CURVE": "icon-curve",
    "CURVES": "icon-curves",
    "SURFACE": "icon-surface",
    "META": "icon-meta",
    "FONT": "icon-font",
    "GREASEPENCIL": "icon-greasepencil",
    "POINTCLOUD": "icon-pointcloud",
    "IMAGE": "icon-image",
}
_DEFAULT_ICON = "icon-object"


def build_memory_usage_html(
    tex_rows: list[dict[str, Any]],
    heavy_rows: list[dict[str, Any]],
    curves_rows: list[dict[str, Any]],
    other_rows: list[dict[str, Any]],
) -> str:
    """Build Memory usage tab: one table (Mesh, Texture, Curves, other types) sorted by estimated size."""
    unified: list[dict[str, Any]] = []

    for r in heavy_rows:
        v = r.get("vertices", 0)
        e = r.get("edges", 0)
        faces = r.get("faces", 0)
        loops = r.get("loops", 0)
        attrs_extra = r.get("attributes_extra_bytes", 0)
        inst = r.get("instance_count", 1)
        size_bytes = (
            _MESH_BYTES_VERTEX * v
            + _MESH_BYTES_EDGE * e
            + _MESH_BYTES_LOOP * loops
            + _MESH_BYTES_POLYGON * faces
            + attrs_extra
        )
        size_kb = size_bytes / 1024.0  
        t = r.get("tris", 0)
        details = f"{v:,} verts, {t:,} tris"
        if inst > 1:
            details += f" × {inst}"
        unified.append({
            "type": "Mesh",
            "instance_count": inst,
            "type_icon": _OBJECT_ICONS.get("MESH", _DEFAULT_ICON),
            "name": r.get("object_name", "?"),
            "size_kb": size_kb,
            "details": details,
        })

    for r in tex_rows:
        size_kb = r.get("size_kb", 0)
        dims = r.get("dimensions", "—")
        pf = r.get("pixel_format")
        bpp = r.get("bytes_per_pixel")
        if pf is not None and bpp is not None:
            details = f"{dims}, {pf} ({int(bpp)} B/px)"
        else:
            details = dims
        inst = r.get("instance_count", 1)
        unified.append({
            "type": "Texture",
            "instance_count": inst,
            "type_icon": _OBJECT_ICONS.get("IMAGE", _DEFAULT_ICON),
            "name": r.get("texture_name", "?"),
            "size_kb": size_kb,
            "details": details,
        })

    for r in curves_rows:
        inst = r.get("instance_count", 1)
        size_kb = r.get("size_kb", 0) 
        curves_count = r.get("curves_count", 0)
        points_count = r.get("points_count", 0)
        details = f"{curves_count:,} curves, {points_count:,} pts"
        if inst > 1:
            details += f" × {inst}"
        unified.append({
            "type": "Curves",
            "instance_count": inst,
            "type_icon": _OBJECT_ICONS.get("CURVES", _DEFAULT_ICON),
            "name": r.get("object_name", "?"),
            "size_kb": size_kb,
            "details": details,
        })

    for r in other_rows:
        obj_type = r.get("object_type", "EMPTY")
        type_label = obj_type.replace("_", " ").title()
        size_kb = r.get("size_kb", 0)
        inst = r.get("instance_count", 1)
        if obj_type == "VOLUME":
            details = "Not supported by profiler"
            size_kb = 0  # do not count in total
        else:
            details = f"× {inst}" if inst > 1 else "—"
        icon = _OBJECT_ICONS.get(obj_type, _DEFAULT_ICON)
        unified.append({
            "type": type_label,
            "instance_count": inst,
            "type_icon": icon,
            "name": r.get("object_name", "?"),
            "size_kb": size_kb,
            "details": details,
        })

    unified.sort(key=lambda x: x["size_kb"], reverse=True)
    total_kb = sum(x["size_kb"] for x in unified) or 1.0

    if not unified:
        return "<p>No data.</p>"

    total_size_str = _fmt_size_kb(total_kb)
    total_pct_cell = (
        '<td class="pct-cell">'
        '<div class="pct-bar" style="width:100%;background:hsl(0,85%,25%);"></div>'
        '<span class="pct-text">100%</span></td>'
    )
    lines = [
        "<table>",
        "<thead><tr><th>Type</th><th>Name</th><th>Est. size</th><th>Share %</th><th>Details</th></tr></thead>",
        "<tbody>",
        f'<tr class="total-row"><td>Total</td><td>—</td><td>{total_size_str}</td>{total_pct_cell}<td>—</td></tr>',
    ]
    for row in unified:
        type_ = escape(row["type"])
        type_icon = row.get("type_icon", "")
        icon_html = f'<span class="{escape(type_icon)} type-icon" aria-hidden="true"></span>' if type_icon else ""
        name = escape(row["name"])
        instance_count = row.get("instance_count", 1)
        if instance_count > 1:
            name = f"{name} <span class='instance-count'>{instance_count} instances</span>"
        details = escape(row["details"])
        size_kb = row["size_kb"]
        pct = (size_kb / total_kb) * 100.0
        bar_color = _pct_bar_color(pct)
        pct_cell = (
            f'<td class="pct-cell">'
            f'<div class="pct-bar" style="width:{pct:.1f}%;background:{bar_color};"></div>'
            f'<span class="pct-text">{pct:.1f}%</span>'
            f"</td>"
        )
        type_cell = f"{icon_html} {type_}" if icon_html else type_
        lines.append(
            f'<tr><td>{type_cell}</td><td>{name}</td><td>{_fmt_size_kb(size_kb)}</td>{pct_cell}<td>{details}</td></tr>'
        )
    lines.append("</tbody></table>")
    return "\n".join(lines)


def get_default_report_state() -> dict[str, Any]:
    """Return default report state (no Blender context). Used when opening the report before any data is sent."""
    return {
        "title": "Render Profiler Report",
        "modifiers_html": "<p>No data yet.</p>",
        "heavy_meshes_html": "<p>No mesh data.</p>",
        "textures_html": "<p>No texture data.</p>",
        "statistics_html": "<p>No statistics.</p>",
        "memory_html": "<p>No memory data.</p>",
        "last_update_html": "",
        "font_size_pct": 14,
        "mode": "off",
        "file_name": "—",
        "scene_name": "—",
        "view_layer_name": "—",
    }


def build_report_html(data: dict[str, Any]) -> str:
    """
    Build the live report HTML
    """
    title = escape(data.get("title", "Render Profiler Report"))
    modifiers_content = data.get("modifiers_html", "<p>No data yet.</p>")
    heavy_content = data.get("heavy_meshes_html", "<p>No mesh data.</p>")
    textures_content = data.get("textures_html", "<p>No texture data.</p>")
    statistics_content = data.get("statistics_html", "<p>No statistics.</p>")
    memory_content = data.get("memory_html", "<p>No memory data.</p>")
    font_size_pct = data.get("font_size_pct", 14)
    last_update_html = data.get("last_update_html", "")
    file_name = escape(data.get("file_name", "—"))
    scene_name = escape(data.get("scene_name", "—"))
    view_layer_name = escape(data.get("view_layer_name", "—"))

    poll_script = _load_poll_script(POLL_INTERVAL_MS) or ""
    style_css = _load_style_css()
    favicon_link = _load_favicon_link()
    tpl = _load_template("report_live.html")
    if tpl is None:
        return ""
    return (
        tpl.replace("__TITLE__", title)
        .replace("__FAVICON_LINK__", favicon_link)
        .replace("__MODIFIERS_CONTENT__", modifiers_content)
        .replace("__HEAVY_CONTENT__", heavy_content)
        .replace("__TEXTURES_CONTENT__", textures_content)
        .replace("__STATISTICS_CONTENT__", statistics_content)
        .replace("__MEMORY_CONTENT__", memory_content)
        .replace("__LAST_UPDATE_HTML__", last_update_html)
        .replace("__FONT_SIZE_PCT__", str(round(font_size_pct, 1)))
        .replace("__FILE_NAME__", file_name)
        .replace("__SCENE_NAME__", scene_name)
        .replace("__VIEW_LAYER_NAME__", view_layer_name)
        .replace("/*__STYLE_CSS__*/", style_css)
        .replace("__POLL_SCRIPT__", poll_script)
    )



