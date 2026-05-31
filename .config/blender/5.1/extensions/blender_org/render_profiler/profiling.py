"""
Render Profiler - Collect modifier / object evaluation data.

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
from typing import Any, Optional

import bpy  # type: ignore

_DEBUG_TIMES: bool = False

# 81 bytes per object for camera, light, empty, etc. (from --cycles-print-stats)
_BYTES_PER_OTHER_OBJECT = 81

def collect_modifier_times_by_object(
    depsgraph: Optional[bpy.types.Depsgraph] = None,
) -> list[dict[str, Any]]:
    """
    Collect modifier execution times by object.
    """
    if _DEBUG_TIMES:
        t0 = time.time()

    if depsgraph is None:
        return []

    by_data: dict[int, dict[str, Any]] = {}

    for eval_obj in depsgraph.objects:
        if eval_obj is None:
            continue
        key = id(eval_obj.data)
        if key in by_data:
            by_data[key]["instance_count"] += 1
            continue
        if not getattr(eval_obj, "modifiers", None) or len(eval_obj.modifiers) == 0:
            continue
        modifiers_info = [
            {"name": mod.name, "type": getattr(mod, "type", "?")}
            for mod in eval_obj.modifiers
        ]
        execution_time_ms = sum(
            m.execution_time * 1000 for m in eval_obj.modifiers)
        by_data[key] = {
            "object_name": eval_obj.name,
            "execution_time_ms": round(execution_time_ms, 3),
            "modifiers": modifiers_info,
            "instance_count": 1,
        }

    results = list(by_data.values())
    results.sort(key=lambda x: x["execution_time_ms"], reverse=True)

    if _DEBUG_TIMES:
        t1 = time.time()
        print(f"collect_modifier_times_by_object: {t1 - t0:.3f}s")
    return results


def collect_heavy_meshes(
    depsgraph: Optional[bpy.types.Depsgraph] = None,
) -> list[dict[str, Any]]:
    """
    For each unique mesh object (by object.data), get vertex/face/tri counts from the evaluated mesh.
    """

    if _DEBUG_TIMES:
        t0 = time.time()
    if depsgraph is None:
        return []

    by_data: dict[int, dict[str, Any]] = {}

    for inst in depsgraph.object_instances:
        eval_obj = inst.object
        if eval_obj is None:
            continue

        key = id(eval_obj.data)
        if key in by_data:
            by_data[key]["instance_count"] += 1
            continue

        if eval_obj.type != "MESH":
            continue
        mesh = getattr(eval_obj, "data", None)
        if mesh is None or not hasattr(mesh, "vertices"):
            continue
        try:
            verts = len(mesh.vertices)
            edges = len(mesh.edges) if hasattr(mesh, "edges") else 0
            faces = len(mesh.polygons) if hasattr(mesh, "polygons") else 0
            loops = len(mesh.loops) if hasattr(mesh, "loops") else 0
 
            materials = [ mat for mat in mesh.materials if mat is not None ]
            used_attr_names = _used_attributes_from_materials(materials, mesh)
          
            attributes_extra_bytes = 0
            
            for attr in mesh.attributes:
                name = getattr(attr, "name", None) or ""
                if name == "position":
                    continue
                if name not in used_attr_names:
                    continue
                domain = getattr(attr, "domain", "POINT")
                data_type = getattr(attr, "data_type", "FLOAT")
                domain_size = _mesh_attribute_domain_size(
                    domain, verts, edges, loops, faces
                )
                attributes_extra_bytes += domain_size * _attribute_element_bytes(
                    data_type
                )
            if hasattr(mesh, "calc_loop_triangles") and hasattr(mesh, "loop_triangles"):
                try:
                    mesh.calc_loop_triangles()
                    tris = len(mesh.loop_triangles)
                except Exception:
                    tris = sum(len(p.vertices) -
                               2 for p in mesh.polygons) if mesh.polygons else 0
            else:
                tris = sum(len(p.vertices) - 2 for p in mesh.polygons) if hasattr(
                    mesh, "polygons") and mesh.polygons else 0
            by_data[key] = {
                "object_name": eval_obj.name,
                "vertices": verts,
                "edges": edges,
                "faces": faces,
                "tris": tris,
                "loops": loops,
                "attributes_extra_bytes": attributes_extra_bytes,
                "instance_count": 1,
            }
        except Exception as e:
            print(f"Error calculating mesh memory: {e}")
            continue

    results = list(by_data.values())
    results.sort(key=lambda x: x["tris"], reverse=True)

    if _DEBUG_TIMES:
        t1 = time.time()
        print(f"collect_heavy_meshes: {t1 - t0:.3f}s")

    return results



def _used_attributes_from_materials(materials: list[Any], mesh: Any) -> set[str]:
    """
    Scan material node trees for attribute references.
    """
    used: set[str] = set()
    active_uv_name: Optional[str] = None
    if mesh and getattr(mesh, "uv_layers", None) and mesh.uv_layers:
        active_idx = getattr(mesh.uv_layers, "active_index", 0)
        if 0 <= active_idx < len(mesh.uv_layers):
            active_uv_name = mesh.uv_layers[active_idx].name
        else:
            active_uv_name = mesh.uv_layers[0].name
    for mat in materials:
        if not mat or not getattr(mat, "node_tree", None):
            continue
        for node in mat.node_tree.nodes:
            ntype = getattr(node, "type", None)
            if ntype == "UVMAP":
                uv_map = getattr(node, "uv_map", None)
                if uv_map:
                    used.add(uv_map)
                elif active_uv_name:
                    used.add(active_uv_name)
            elif ntype == "ATTRIBUTE":
                attr_name = getattr(node, "attribute_name", None) or getattr(
                    node, "attribute", None
                )
                if attr_name and attr_name != "position":
                    used.add(attr_name)
            elif ntype == "TEX_COORD" and active_uv_name:
                used.add(active_uv_name)
    return used


def _attribute_element_bytes(data_type: str) -> int:
    """Bytes per element for Blender attribute data_type."""
    _sizes: dict[str, int] = {
        "FLOAT": 4,
        "INT": 4,
        "FLOAT_VECTOR": 12,
        "FLOAT_COLOR": 16,
        "BYTE_COLOR": 4,
        "QUATERNION": 16,
        "FLOAT2": 8,
        "INT8": 1,
        "INT32_2D": 8,
        "INT8_2D": 2,
        "BOOLEAN": 1,
    }
    return _sizes.get(data_type, 4)


def _mesh_attribute_domain_size(
    domain: str, verts: int, edges: int, loops: int, faces: int
) -> int:
    """Element count for attribute domain on a mesh."""
    if domain == "POINT":
        return verts
    if domain == "EDGE":
        return edges
    if domain == "CORNER":
        return loops
    if domain == "FACE":
        return faces
    return 0


def collect_curves_memory(
    depsgraph: Optional[bpy.types.Depsgraph] = None,
) -> list[dict[str, Any]]:
    """
    For each unique Curves object (hair/Geometry Nodes, not legacy Curve), get curve count,
    point count, and estimated memory. Deduplicates by id(object.data), keeps instance_count.
    """
    if _DEBUG_TIMES:
        t0 = time.time()
    if depsgraph is None:
        return []

    by_data: dict[int, dict[str, Any]] = {}

    for inst in depsgraph.object_instances:
        eval_obj = inst.object
        if eval_obj is None:
            continue
        key = id(eval_obj.data)
        if key in by_data:
            by_data[key]["instance_count"] += 1
            continue
        if eval_obj.type != "CURVES":
            continue
        curves_data = getattr(eval_obj, "data", None)
        if curves_data is None:
            continue
        if not hasattr(curves_data, "points") or not hasattr(curves_data, "curves"):
            continue
        try:
            points_count = len(curves_data.points)
            curves_count = len(curves_data.curves)
            # Estimate: position 3f + radius 1f + normal 3f(?) + curve len (int)
            size_bytes = points_count * 28 + curves_count * 4
            size_kb = size_bytes / 1024.0
            by_data[key] = {
                "object_name": eval_obj.name,
                "curves_count": curves_count,
                "points_count": points_count,
                "size_kb": round(size_kb, 2),
                "instance_count": 1,
            }
        except Exception:
            continue

    results = list(by_data.values())
    results.sort(key=lambda x: x["size_kb"], reverse=True)
    if _DEBUG_TIMES:
        t1 = time.time()
        print(f"collect_curves_memory: {t1 - t0:.3f}s")
    return results





def collect_other_objects_memory(
    depsgraph: Optional[bpy.types.Depsgraph] = None,
) -> list[dict[str, Any]]:
    """
    Add other objects to the report. 
   
    """
    if depsgraph is None:
        return []

    by_data: dict[int, dict[str, Any]] = {}
    size_kb = _BYTES_PER_OTHER_OBJECT / 1024.0

    for inst in depsgraph.object_instances:
        eval_obj = inst.object
        if eval_obj is None:
            continue
        obj_type = getattr(eval_obj, "type", None)
        if obj_type in ("MESH", "CURVES"):
            continue
        key = id(eval_obj.data) if eval_obj.data else id(eval_obj)
        if key in by_data:
            by_data[key]["instance_count"] += 1
            continue
        by_data[key] = {
            "object_name": getattr(eval_obj, "name", "?"),
            "object_type": obj_type or "EMPTY",
            "size_kb": size_kb,
            "instance_count": 1,
        }

    results = list(by_data.values())
    results.sort(key=lambda x: (x["object_type"], x["object_name"]))
    return results


def _materials_using_image(image: Any) -> list[str]:
    """Return list of material names that use this image in a TEX_IMAGE or TEX_ENVIRONMENT node."""
    names: list[str] = []
    for mat in bpy.data.materials:
        if not mat or mat.node_tree is None:
            continue
        for node in mat.node_tree.nodes:
            if getattr(node, "type", None) in ("TEX_IMAGE", "TEX_ENVIRONMENT") and getattr(node, "image", None) == image:
                if mat.name not in names:
                    names.append(mat.name)
                break
    return names


def _image_used_in_world(image: Any, scene: Any) -> bool:
    """Return True if the image is used in the scene's world node tree."""
    world = getattr(scene, "world", None) if scene else None
    if not world or getattr(world, "node_tree", None) is None:
        return False
    for node in world.node_tree.nodes:
        if getattr(node, "type", None) in ("TEX_IMAGE", "TEX_ENVIRONMENT") and getattr(node, "image", None) == image:
            return True
    return False


def _active_materials_from_view_layer(
    context: Optional[bpy.types.Context] = None,
    scene: Optional[Any] = None,
) -> set[Any]:
    """Return set of materials used by objects in the given view layer (from context or scene)."""
    active: set[Any] = set()
    view_layer = None
    if context is not None:
        view_layer = getattr(context, "view_layer", None)
    elif scene is not None and getattr(scene, "view_layers", None):
        vl_collection = scene.view_layers
        idx = getattr(vl_collection, "active_index", 0)
        if 0 <= idx < len(vl_collection):
            view_layer = vl_collection[idx]
    if not view_layer:
        return active
    for obj in getattr(view_layer, "objects", []) or []:
        if not obj:
            continue
        for slot in getattr(obj, "material_slots", []) or []:
            mat = getattr(slot, "material", None) if slot else None
            if mat:
                active.add(mat)
    return active


def _image_pixel_format_and_bpp(img: Any) -> tuple[str]:
    """
    Return a short layout label (e.g. RGBA32F, RGB8) and packed bytes per pixel.
    """

    depth_bits: int = getattr(img, "depth", 8) or 8
    is_float: bool = getattr(img, "is_float", False)
    channels: int = getattr(img, "channels", 0) or 0

    bytes_per_channel = depth_bits // channels 

    layout = {1: "BW", 2: "LA", 3: "RGB", 4: "RGBA"}.get(channels, f"{channels}ch")
    if is_float:
        label = f"{layout}{bytes_per_channel}F"
    else:
        label = f"{layout}{bytes_per_channel}"
    return label


def collect_textures(
    context: Optional[bpy.types.Context] = None,
    scene: Optional[Any] = None,
) -> list[dict[str, Any]]:
    """
    Collect texture (image) data for images that are used by at least one object in the
    active view layer or by the scene's world. 
    """
    if _DEBUG_TIMES:
        t0 = time.time()

    if context is None and scene is None:
        return []
    active_materials = _active_materials_from_view_layer(
        context=context, scene=scene)

    scene_for_world = scene if scene is not None else (
        getattr(context, "scene", None) if context else None)

    results: list[dict[str, Any]] = []
    for img in bpy.data.images:

        if not img or not img.size:
            continue

        materials = _materials_using_image(img)
        used_by_object_in_view_layer = any(
            bpy.data.materials.get(name) in active_materials
            for name in materials
        )

        used_by_world = _image_used_in_world(img, scene_for_world)
        if not used_by_object_in_view_layer and not used_by_world:
            continue

        w, h = img.size[0], img.size[1]
        if w <= 0 or h <= 0:
            continue

        depth = getattr(img, "depth", 8) or 8 
        bytes_per_pixel =  (depth // 8)

        pixel_format = _image_pixel_format_and_bpp(img)
        size_bytes = w * h * bytes_per_pixel
        size_kb = size_bytes / 1024.0

        results.append({
            "texture_name": img.name,
            "materials": materials,
            "size_kb": round(size_kb, 0),
            "dimensions": f"{w}×{h}",
            "pixel_format": pixel_format,
            "bytes_per_pixel": bytes_per_pixel,
            "instance_count": img.users,
        })

    results.sort(key=lambda x: x["size_kb"], reverse=True)

    if _DEBUG_TIMES:
        t1 = time.time()
        print(f"collect_textures: {t1 - t0:.3f}s")
    return results
