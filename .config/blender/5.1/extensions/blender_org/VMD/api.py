import bpy

from bpy import types as bpy_types
from bpy.types import NodesModifier, Operator, KeyMapItem
from bpy_extras import anim_utils

bl_rna_get_subclass_py = Operator.bl_rna_get_subclass_py
KeyMapItem_bl_rna_props_type_enum_items = KeyMapItem.bl_rna.properties['type'].enum_items
action_ensure_channelbag_for_slot = anim_utils.action_ensure_channelbag_for_slot

attr_NodesModifier_bake_directory = "bake_directory" if "bake_directory" in NodesModifier.bl_rna.properties else "simulation_bake_directory"


D_blendData_id = {
    "actions":          "ACTION",
    "annotations":      "GREASEPENCIL",
    "armatures":        "ARMATURE",
    "brushes":          "BRUSH",
    "cache_files":      "CACHEFILE",
    "cameras":          "CAMERA",
    "collections":      "COLLECTION",
    "curves":           "CURVE",
    "fonts":            "FONT",
    "grease_pencils":   "GREASEPENCIL",
    "hair_curves":      "CURVES",
    "images":           "IMAGE",
    "lattices":         "LATTICE",
    "libraries":        "LIBRARY",
    "lightprobes":      "LIGHT_PROBE",
    "lights":           "LIGHT",
    "linestyles":       "LINESTYLE",
    "masks":            "MASK",
    "materials":        "MATERIAL",
    "meshes":           "MESH",
    "metaballs":        "META",
    "movieclips":       "MOVIECLIP",
    "node_groups":      "NODETREE",
    "objects":          "OBJECT",
    "paint_curves":     "PAINTCURVE",
    "palettes":         "PALETTE",
    "particles":        "PARTICLE",
    "pointclouds":      "POINTCLOUD",
    "scenes":           "SCENE",
    "screens":          "SCREEN",
    "shape_keys":       "KEY",
    "sounds":           "SOUND",
    "speakers":         "SPEAKER",
    "texts":            "TEXT",
    "textures":         "TEXTURE",
    "volumes":          "VOLUME",
    "window_managers":  "WINDOWMANAGER",
    "workspaces":       "WORKSPACE",
    "worlds":           "WORLD"}
D_id_blendData = {k: e for e, k in D_blendData_id.items()}

D_blendData_cls = {
    "actions":          "Action",
    "annotations":      "Annotation",
    "armatures":        "Armature",
    "brushes":          "Brush",
    "cache_files":      "CacheFile",
    "cameras":          "Camera",
    "collections":      "Collection",
    "curves":           "Curve",
    "fonts":            "VectorFont",
    "grease_pencils":   "GreasePencil",
    "hair_curves":      "Curves",
    "images":           "Image",
    "lattices":         "Lattice",
    "libraries":        "Library",
    "lightprobes":      "LightProbe",
    "lights":           "Light",
    "linestyles":       "FreestyleLineStyle",
    "masks":            "Mask",
    "materials":        "Material",
    "meshes":           "Mesh",
    "metaballs":        "MetaBall",
    "movieclips":       "MovieClip",
    "node_groups":      "NodeTree",
    "objects":          "Object",
    "paint_curves":     "PaintCurve",
    "palettes":         "Palette",
    "particles":        "ParticleSettings",
    "pointclouds":      "PointCloud",
    "scenes":           "Scene",
    "screens":          "Screen",
    "shape_keys":       "Key",
    "sounds":           "Sound",
    "speakers":         "Speaker",
    "texts":            "Text",
    "textures":         "Texture",
    "volumes":          "Volume",
    "window_managers":  "WindowManager",
    "workspaces":       "WorkSpace",
    "worlds":           "World"}
D_cls_blendData = {k: e for e, k in D_blendData_cls.items()}
D_cls_id = {k: D_blendData_id[e] for k, e in D_cls_blendData.items()}
D_id_cls = {k: e for e, k in D_cls_id.items()}

S_ALLOW_ASSET = {
    'MATERIAL',
    'COLLECTION',
    'OBJECT',
    'BRUSH',
    'ACTION',
    'WORLD'}
S_ALLOW_PREVIEW = {
    'IMAGE',
    'MATERIAL',
    'TEXTURE',
}


def r_fcurves(anim_data):
    try:
        return action_ensure_channelbag_for_slot(anim_data.action, anim_data.action_slot).fcurves
    except:
        return None

def r_ops_from_idname(idname):
    try:
        category, name = idname.split(".")
        return getattr(getattr(bpy.ops, category), name)
    except:
        return None

def r_rna_type_from_ops(o):
    try:
        return o.get_rna_type()
    except:
        return None

def r_py_cls_from_idname(idname):
    try:
        return getattr(bpy_types, r_rna_type_from_ops(r_ops_from_idname(idname)).identifier)
    except:
        return None

def rl_all_keymap_types():
    return [e.identifier for e in KeyMapItem_bl_rna_props_type_enum_items]

def r_bl_ID_by_uid(bpy_data, uid):
    for e in bpy_data:
        if e.session_uid == uid:
            return e
    return None


def r_bbox_nodes(nodes):
    bbox = [0.0, 0.0, 0.0, 0.0]
    for e in nodes:
        L, T = e.location_absolute
        bbox[0] = min(bbox[0], L)
        bbox[3] = max(bbox[3], T)
        bbox[1] = max(bbox[1], L + e.dimensions.x)
        bbox[2] = min(bbox[2], T - e.dimensions.y)

    return bbox

def r_eevee_output(nodes, ty='EEVEE'):
    for e in nodes:
        if e.type == 'OUTPUT_MATERIAL' and e.target == ty: return e

    return None