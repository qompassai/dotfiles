bl_info = {
    "name": "PBR Lookdev",
    "author": "BHiMAX",
    "version": (4, 2, 1),
    "blender": (4, 2, 0),
    "location": "Shader Editor > N-Panel > PBR Lookdev  |  View3D > N-Panel > PBR Lookdev  |  Properties > Material > PBR Lookdev",
    "description": "Layered PBR Lookdev panel — full shader inputs, image+mask overlay stacks, min/max point controls.",
    "category": "Material",
}

import bpy, os, json
from pathlib import Path
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import (
    StringProperty, BoolProperty, FloatProperty, FloatVectorProperty,
    IntProperty, CollectionProperty, EnumProperty, PointerProperty,
)

# ── UI state stored on WindowManager (never triggers IPR) ────────────────────
def _ui_key(*parts): return "|".join(str(p) for p in parts)

def _ui_get(context, *parts, default=False):
    wm = context.window_manager
    store = getattr(wm, 'pbr_ui_state', '{}')
    try: return json.loads(store).get(_ui_key(*parts), default)
    except Exception: return default

def _ui_set(context, value, *parts):
    wm = context.window_manager
    store = getattr(wm, 'pbr_ui_state', '{}')
    try: d = json.loads(store)
    except Exception: d = {}
    d[_ui_key(*parts)] = value
    wm.pbr_ui_state = json.dumps(d)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

IMAGE_EXTENSIONS = {'.png','.jpg','.jpeg','.exr','.tif','.tiff','.tga','.bmp','.hdr','.webp'}

MASK_TYPES = [
    ('IMAGE',    'Image',    'Use an image texture as mask'),
    ('NOISE',    'Noise',    'Procedural noise texture'),
    ('WAVE',     'Wave',     'Procedural wave texture'),
    ('GRADIENT', 'Gradient', 'Procedural gradient'),
    ('VORONOI',  'Voronoi',  'Voronoi / cellular texture'),
]

WAVE_TYPES = [
    ('BANDS', 'Bands', ''), ('RINGS', 'Rings', ''),
    ('BANDSAW', 'Bandsaw', ''), ('RINGSAW', 'Ringsaw', ''),
]

WAVE_PROFILES = [
    ('SIN', 'Sine', ''), ('SAW', 'Saw', ''), ('TRI', 'Triangle', ''),
]

GRADIENT_TYPES = [
    ('LINEAR', 'Linear', ''), ('QUADRATIC', 'Quadratic', ''),
    ('EASING', 'Easing', ''), ('DIAGONAL', 'Diagonal', ''),
    ('SPHERICAL', 'Spherical', ''), ('QUADRATIC_SPHERE', 'Quadratic Sphere', ''),
    ('RADIAL', 'Radial', ''),
]

VORONOI_FEATURES = [
    ('F1', 'F1', ''), ('F2', 'F2', ''),
    ('SMOOTH_F1', 'Smooth F1', ''),
    ('DISTANCE_TO_EDGE', 'Distance to Edge', ''),
    ('N_SPHERE_RADIUS', 'N-Sphere Radius', ''),
]

VORONOI_DISTANCES = [
    ('EUCLIDEAN', 'Euclidean', ''), ('MANHATTAN', 'Manhattan', ''),
    ('CHEBYCHEV', 'Chebychev', ''), ('MINKOWSKI', 'Minkowski', ''),
]

BLEND_MODES = [
    ('MIX',      'Mix',      'Blend using mask'),
    ('MULTIPLY', 'Multiply', 'Multiply (darken)'),
    ('ADD',      'Add',      'Add (brighten)'),
    ('SCREEN',   'Screen',   'Screen (lighten)'),
    ('OVERLAY',  'Overlay',  'Overlay'),
    ('SOFT_LIGHT','Soft Light','Soft light'),
]

ORM_LAYOUTS = [
    ('AO_ROUGH_MET', 'R=AO  G=Rough  B=Metal',  'Standard ORM / ARM'),
    ('MET_ROUGH_AO', 'R=Metal  G=Rough  B=AO',   'Inverted (some engines)'),
    ('ROUGH_MET_AO', 'R=Rough  G=Metal  B=AO',   'Custom layout'),
    ('AO_MET_ROUGH', 'R=AO  G=Metal  B=Rough',   'Custom layout'),
]

ORM_LAYOUT_MAP = {
    'AO_ROUGH_MET':  ('ao', 'roughness', 'metallic'),
    'MET_ROUGH_AO':  ('metallic', 'roughness', 'ao'),
    'ROUGH_MET_AO':  ('roughness', 'metallic', 'ao'),
    'AO_MET_ROUGH':  ('ao', 'metallic', 'roughness'),
}

SHADER_ITEMS = [
    ('PRINCIPLED', 'Principled BSDF',       'Full PBR shader',         'NODE_MATERIAL',      0),
    ('GLASS',      'Glass BSDF',            'Refractive glass shader', 'MATERIAL',            1),
    ('EMISSION',   'Emission',              'Emissive light shader',   'LIGHT_SUN',           2),
    ('DIFFUSE',    'Diffuse BSDF',          'Simple diffuse shader',   'SHADING_SOLID',       3),
    ('SSS',        'Subsurface Scattering', 'SSS shader',              'OUTLINER_DATA_META',  4),
]

# Per-map default CS
_MAP_DEFAULT_CS = {d[0]: d[3] for d in [
    ('base_color','Base Color','MATERIAL','sRGB','COLOR'),
    ('roughness','Roughness','NODE_MATERIAL','Non-Color','FLOAT'),
    ('diffuse_roughness','Diffuse Roughness','NODE_MATERIAL','Non-Color','FLOAT'),
    ('metallic','Metallic','SHADING_RENDERED','Non-Color','FLOAT'),
    ('ior','IOR','DRIVER','Non-Color','FLOAT'),
    ('specular','Specular','LIGHT','Non-Color','FLOAT'),
    ('specular_ior','Specular IOR Level','DRIVER','Non-Color','FLOAT'),
    ('specular_tint','Specular Tint','COLOR','sRGB','COLOR'),
    ('anisotropic','Anisotropic','ORIENTATION_GIMBAL','Non-Color','FLOAT'),
    ('anisotropic_rot','Anisotropic Rotation','LOOP_FORWARDS','Non-Color','FLOAT'),
    ('normal','Normal','NORMALS_FACE','Non-Color','NONE'),
    ('bump','Bump','MOD_DISPLACE','Non-Color','NONE'),
    ('coat_weight','Coat Weight','NODE_MATERIAL','Non-Color','FLOAT'),
    ('coat_roughness','Coat Roughness','MESH_CIRCLE','Non-Color','FLOAT'),
    ('coat_ior','Coat IOR','DRIVER','Non-Color','FLOAT'),
    ('coat_normal','Coat Normal','NORMALS_VERTEX_FACE','Non-Color','NONE'),
    ('sheen_weight','Sheen Weight','SURFACE_DATA','Non-Color','FLOAT'),
    ('sheen_roughness','Sheen Roughness','OUTLINER_DATA_SURFACE','Non-Color','FLOAT'),
    ('sheen_tint','Sheen Tint','COLOR','sRGB','COLOR'),
    ('emission','Emission','LIGHT_SUN','sRGB','COLOR'),
    ('opacity','Opacity / Alpha','IMAGE_ALPHA','Non-Color','FLOAT'),
    ('ao','Ambient Occ.','SHADING_SOLID','Non-Color','FLOAT'),
    ('sss','Subsurface Weight','OUTLINER_DATA_META','Non-Color','FLOAT'),
    ('translucency','Transmission / Translucency','MOD_OPACITY','Non-Color','FLOAT'),
    ('displacement','Displacement','MOD_WARP','Non-Color','FLOAT'),
    ('glossiness','Glossiness','SHADING_TEXTURE','Non-Color','FLOAT'),
    ('sss_radius','SSS Radius','OUTLINER_DATA_META','sRGB','COLOR'),
    ('sss_scale','SSS Scale','OUTLINER_DATA_META','Non-Color','FLOAT'),
    ('sss_anisotropy','SSS Anisotropy','ORIENTATION_GIMBAL','Non-Color','FLOAT'),
    ('sss_ior','SSS IOR','DRIVER','Non-Color','FLOAT'),
    ('thin_film_thick','Thin Film Thickness','MESH_CIRCLE','Non-Color','FLOAT'),
    ('thin_film_ior','Thin Film IOR','DRIVER','Non-Color','FLOAT'),
]}

MAP_DEF = [
    ('base_color',        'Base Color',              'MATERIAL',             'sRGB',      'COLOR'),
    ('roughness',         'Roughness',               'NODE_MATERIAL',        'Non-Color', 'FLOAT'),
    ('diffuse_roughness', 'Diffuse Roughness',        'NODE_MATERIAL',        'Non-Color', 'FLOAT'),
    ('metallic',          'Metallic',                'SHADING_RENDERED',     'Non-Color', 'FLOAT'),
    ('ior',               'IOR',                     'DRIVER',               'Non-Color', 'FLOAT'),
    ('specular',          'Specular',                'LIGHT',                'Non-Color', 'FLOAT'),
    ('specular_ior',      'Specular IOR Level',      'DRIVER',               'Non-Color', 'FLOAT'),
    ('specular_tint',     'Specular Tint',           'COLOR',                'sRGB',      'COLOR'),
    ('anisotropic',       'Anisotropic',             'ORIENTATION_GIMBAL',   'Non-Color', 'FLOAT'),
    ('anisotropic_rot',   'Anisotropic Rotation',    'LOOP_FORWARDS',        'Non-Color', 'FLOAT'),
    ('normal',            'Normal',                  'NORMALS_FACE',         'Non-Color', 'NONE'),
    ('bump',              'Bump',                    'MOD_DISPLACE',         'Non-Color', 'NONE'),
    ('coat_weight',       'Coat Weight',             'NODE_MATERIAL',        'Non-Color', 'FLOAT'),
    ('coat_roughness',    'Coat Roughness',          'MESH_CIRCLE',          'Non-Color', 'FLOAT'),
    ('coat_ior',          'Coat IOR',                'DRIVER',               'Non-Color', 'FLOAT'),
    ('coat_normal',       'Coat Normal',             'NORMALS_VERTEX_FACE',  'Non-Color', 'NONE'),
    ('sheen_weight',      'Sheen Weight',            'SURFACE_DATA',         'Non-Color', 'FLOAT'),
    ('sheen_roughness',   'Sheen Roughness',         'OUTLINER_DATA_SURFACE','Non-Color', 'FLOAT'),
    ('sheen_tint',        'Sheen Tint',              'COLOR',                'sRGB',      'COLOR'),
    ('emission',          'Emission',                'LIGHT_SUN',            'sRGB',      'COLOR'),
    ('opacity',           'Opacity / Alpha',         'IMAGE_ALPHA',          'Non-Color', 'FLOAT'),
    ('ao',                'Ambient Occ.',            'SHADING_SOLID',        'Non-Color', 'FLOAT'),
    ('sss',               'Subsurface Weight',       'OUTLINER_DATA_META',   'Non-Color', 'FLOAT'),
    ('translucency',      'Transmission / Translucency', 'MOD_OPACITY',      'Non-Color', 'FLOAT'),
    ('displacement',      'Displacement',            'MOD_WARP',             'Non-Color', 'FLOAT'),
    ('glossiness',        'Glossiness',              'SHADING_TEXTURE',      'Non-Color', 'FLOAT'),
    ('sss_radius',        'SSS Radius',              'OUTLINER_DATA_META',   'sRGB',      'COLOR'),
    ('sss_scale',         'SSS Scale',               'OUTLINER_DATA_META',   'Non-Color', 'FLOAT'),
    ('sss_anisotropy',    'SSS Anisotropy',          'ORIENTATION_GIMBAL',   'Non-Color', 'FLOAT'),
    ('sss_ior',           'SSS IOR',                 'DRIVER',               'Non-Color', 'FLOAT'),
    ('thin_film_thick',   'Thin Film Thickness',     'MESH_CIRCLE',          'Non-Color', 'FLOAT'),
    ('thin_film_ior',     'Thin Film IOR',           'DRIVER',               'Non-Color', 'FLOAT'),
]

MAP_KEYS  = [d[0] for d in MAP_DEF]
MAP_INFO  = {d[0]: d[1:] for d in MAP_DEF}

BSDF_SOCKETS = {
    'PRINCIPLED': {
        'base_color':      'Base Color',
        'roughness':       'Roughness',
        'diffuse_roughness': ('Diffuse Roughness',),
        'glossiness':      'Roughness',
        'metallic':        'Metallic',
        'ior':             'IOR',
        'specular':        'Specular Tint',
        'specular_ior':    ('Specular IOR Level',),
        'specular_tint':   'Specular Tint',
        'anisotropic':     'Anisotropic',
        'anisotropic_rot': 'Anisotropic Rotation',
        'normal':          'Normal',
        'bump':            'Normal',
        'coat_weight':     ('Coat Weight', 'Clearcoat'),
        'coat_roughness':  ('Coat Roughness', 'Clearcoat Roughness'),
        'coat_ior':       ('Coat IOR',),
        'coat_normal':     ('Coat Normal', 'Clearcoat Normal'),
        'sheen_weight':    ('Sheen Weight', 'Sheen'),
        'sheen_roughness': ('Sheen Roughness',),
        'sheen_tint':      ('Sheen Tint',),
        'emission':        ('Emission Color', 'Emission'),
        'opacity':         'Alpha',
        'sss':             ('Subsurface Weight', 'Subsurface'),
        'sss_radius':      ('Subsurface Radius',),
        'sss_scale':       ('Subsurface Scale',),
        'sss_anisotropy':  ('Subsurface Anisotropy',),
        'thin_film_thick': ('Thin Film Thickness',),
        'thin_film_ior':   ('Thin Film IOR',),
        'translucency':    ('Transmission Weight', 'Transmission'),
    },
    'GLASS':    {
        'base_color':      'Color',
        'roughness':       'Roughness',
        'glossiness':      'Roughness',
        'ior':             'IOR',
        'normal':          'Normal',
        'bump':            'Normal',
        'thin_film_thick': ('Thin Film Thickness',),
        'thin_film_ior':   ('Thin Film IOR',),
    },
    'EMISSION': {
        'emission':         'Color',
        'emission_strength': 'Strength',
    },
    'DIFFUSE':  {
        'base_color': 'Color',
        'roughness':  'Roughness',
        'glossiness': 'Roughness',
        'normal':     'Normal',
        'bump':       'Normal',
    },
    'SSS':      {
        'base_color':    'Color',
        'roughness':     'Roughness',
        'normal':        'Normal',
        'bump':          'Normal',
        'sss_radius':    ('Radius', 'Subsurface Radius'),
        'sss_scale':     ('Scale',),
        'sss_anisotropy':('Anisotropy',),
        'sss_ior':       ('IOR',),
        'anisotropic':   ('Anisotropy',),
    },
}

SHADER_MAPS = {
    'PRINCIPLED': [k for k in MAP_KEYS if k != 'displacement'],
    'GLASS':      ['base_color','roughness','glossiness','ior','normal','bump','thin_film_thick','thin_film_ior'],
    'EMISSION':   ['emission'],
    'DIFFUSE':    ['base_color','roughness','glossiness','normal','bump'],
    'SSS':        ['base_color','roughness','normal','bump','sss_radius','sss_scale','sss_anisotropy','sss_ior','anisotropic'],
}

SHADER_NODE_TYPE = {
    'PRINCIPLED': 'ShaderNodeBsdfPrincipled',
    'GLASS':      'ShaderNodeBsdfGlass',
    'EMISSION':   'ShaderNodeEmission',
    'DIFFUSE':    'ShaderNodeBsdfDiffuse',
    'SSS':        'ShaderNodeSubsurfaceScattering',
}

SHADER_OUTPUT_SOCKET = {
    'PRINCIPLED': 'BSDF',
    'GLASS':      'BSDF',
    'EMISSION':   'Emission',
    'DIFFUSE':    'BSDF',
    'SSS':        'BSDF',
}

SHADER_BSDF_TYPE = {
    'PRINCIPLED': 'BSDF_PRINCIPLED',
    'GLASS':      'BSDF_GLASS',
    'EMISSION':   'EMISSION',
    'DIFFUSE':    'BSDF_DIFFUSE',
    'SSS':        'SUBSURFACE_SCATTERING',
}

MAP_GROUPS = [
    ('base',        'Base Color',      'MATERIAL',           ['base_color','ao']),
    ('roughness',   'Roughness',       'NODE_MATERIAL',      ['roughness','glossiness','diffuse_roughness']),
    ('metal_spec',  'Metal / Specular','SHADING_RENDERED',   ['metallic','ior','specular_ior','specular_tint','anisotropic','anisotropic_rot']),
    ('normal',      'Normal / Bump',   'NORMALS_FACE',       ['normal','bump']),
    ('coat',        'Coat',            'NODE_MATERIAL',      ['coat_weight','coat_roughness','coat_ior','coat_normal']),
    ('sheen',       'Sheen',           'SURFACE_DATA',       ['sheen_weight','sheen_roughness','sheen_tint']),
    ('emission',    'Emission',        'LIGHT_SUN',          ['emission']),
    ('transparency','Transparency',    'IMAGE_ALPHA',        ['opacity','translucency']),
    ('sss',         'Subsurface',      'OUTLINER_DATA_META', ['sss','sss_radius','sss_scale','sss_anisotropy']),
    ('thin_film',   'Thin Film',       'MESH_CIRCLE',        ['thin_film_thick','thin_film_ior']),
    ('displacement','Displacement',    'MOD_WARP',           ['displacement']),
]

SHADER_GROUPS = {
    'PRINCIPLED': ['base','roughness','metal_spec','normal','coat','sheen','emission','transparency','sss','thin_film','displacement'],
    'GLASS':      ['base','roughness','metal_spec','normal','thin_film'],
    'EMISSION':   ['emission'],
    'DIFFUSE':    ['base','roughness','normal'],
    'SSS':        ['base','roughness','normal','sss','thin_film'],
}

GRAYSCALE_KEYS = {k for k in MAP_KEYS if MAP_INFO[k][3] == 'FLOAT'}

MAP_KEYWORDS = {
    'base_color':      ['basecolor','base_color','albedo','diffuse','_diff','_col_','_color','_alb','_bc'],
    'roughness':       ['roughness','_rough','_rgh','_roughness'],
    'diffuse_roughness': ['diffuse_rough','diffuseroughness','_diffrough'],
    'glossiness':      ['glossiness','_gloss','_gls','gloss'],
    'metallic':        ['metallic','metalness','_metal','_met_','_mtl'],
    'normal':          ['_normal','_nor_','_nrm','_nrl','normalgl','normaldx'],
    'bump':            ['_bump','_bmp','bump_'],
    'ao':              ['ambientocclusion','ambient_occlusion','_ao','_ao_','occlusion','_occ'],
    'emission':        ['emission','emissive','_emit','_glow'],
    'opacity':         ['opacity','_alpha','_transparent','_mask','_opac'],
    'displacement':    ['displacement','_disp','_height','_hgt','heightmap'],
    'sss':             ['subsurface','_sss','scattering'],
    'translucency':    ['translucency','translucent','transmission','_trans_'],
    'specular':        [],
    'specular_ior':    ['specularior','specular_ior','spec_ior'],
    'specular_tint':   ['speculartint','specular_tint','specular','_spec','_spc'],
    'coat_weight':     ['clearcoat','coat','_coat'],
    'coat_roughness':  ['clearcoat_rough','coat_rough','coatroughness'],
    'coat_ior':       ['coat_ior','clearcoat_ior'],
    'sheen_weight':    ['sheen','_sheen'],
    'anisotropic':     ['anisotropic','aniso'],
    'anisotropic_rot': ['anisotropic_rot','aniso_rot'],
    'ior':             [],
    'coat_normal':     ['coat_normal','clearcoat_normal'],
    'sheen_roughness': ['sheen_rough','sheenroughness'],
    'sheen_tint':      ['sheen_tint','sheentint'],
    'sss_radius':      ['sss_radius','subsurface_radius'],
    'sss_scale':       ['sss_scale','subsurface_scale'],
    'sss_anisotropy':  ['sss_anisotropy'],
    'sss_ior':         ['sss_ior'],
    'thin_film_thick': ['thin_film','thinfilm'],
    'thin_film_ior':   ['thin_film_ior'],
}

# ══════════════════════════════════════════════════════════════════════════════
# DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def _detect_map(filename):
    name = os.path.splitext(filename)[0].lower().replace('-','_').replace(' ','_')
    scores = {mt: sum(len(k) for k in kws if kws and k.replace(' ','_') in name)
              for mt, kws in MAP_KEYWORDS.items()}
    scores = {k: v for k, v in scores.items() if v}
    return max(scores, key=scores.get) if scores else None

ORM_KEYWORDS = ['_orm','_arm','orm_','arm_','_occ_rough_met','_ambientocclusion_roughness_metallic']

ORM_CHANNELS = {
    'Red':   'ao',
    'Green': 'roughness',
    'Blue':  'metallic',
}

def _detect_orm(filename):
    name = os.path.splitext(filename)[0].lower().replace('-','_').replace(' ','_')
    return any(k in name for k in ORM_KEYWORDS)

def scan_dir(directory, keyword=None):
    if not (directory and os.path.isdir(directory)): return {}, None
    best = {}
    orm_path = None
    kw = keyword.lower().strip() if keyword else None
    for f in os.listdir(directory):
        if os.path.splitext(f)[1].lower() not in IMAGE_EXTENSIONS: continue
        # Apply keyword filter if set
        if kw and kw not in f.lower(): continue
        fp = os.path.join(directory, f)
        if _detect_orm(f):
            orm_path = fp
            continue
        mt = _detect_map(f)
        if not mt: continue
        sc = sum(len(k) for k in MAP_KEYWORDS.get(mt,[]) if k.replace(' ','_') in f.lower())
        if mt not in best or sc > best[mt][0]:
            best[mt] = (sc, fp)
    return {mt: v[1] for mt, v in best.items()}, orm_path


def detect_part_names(directory):
    """
    Token-based part name detection.
    Split each filename into tokens, remove all known map-type and convention tokens,
    what remains = the part name (e.g. 'Hair', 'Body', 'Tire').
    Only returns names that appear paired with at least 2 different map types
    (confirming it is a genuine texture set prefix, not a lone file).
    """
    import re
    if not (directory and os.path.isdir(directory)):
        return []

    # Build set of all individual word-tokens that are map identifiers
    STRIP_TOKENS = set()
    for kws in MAP_KEYWORDS.values():
        for k in kws:
            for t in re.split(r'[_\-\s]+', k):
                if t: STRIP_TOKENS.add(t.lower())
    for k in ORM_KEYWORDS:
        for t in re.split(r'[_\-\s]+', k):
            if t: STRIP_TOKENS.add(t.lower())
    # Convention/variant suffixes that are NOT part names
    STRIP_TOKENS.update({
        'opengl', 'directx', 'dx', 'gl', 'orm', 'arm',
        '4k', '2k', '1k', '8k', '16k',
        'v1', 'v2', 'v3', 'final', 'new', 'old',
        'low', 'high', 'mid', 'lod', 'packed', 'map',
        'tex', 'texture', 'img', 'image',
    })

    # part_name -> set of map types seen
    part_map_types = {}

    for f in os.listdir(directory):
        ext = os.path.splitext(f)[1].lower()
        if ext not in IMAGE_EXTENSIONS:
            continue
        stem = os.path.splitext(f)[0].lower()
        tokens = re.split(r'[_\-\s]+', stem)
        # Keep only tokens that are NOT map/convention identifiers and not pure digits
        part_tokens = [t for t in tokens
                       if t and t not in STRIP_TOKENS and not t.isdigit() and len(t) >= 2]
        if not part_tokens:
            continue
        part = '_'.join(part_tokens)
        mt = _detect_map(f)
        if part not in part_map_types:
            part_map_types[part] = set()
        if mt:
            part_map_types[part].add(mt)

    # Show any part that has at least 1 detected map type
    result = sorted(p for p, mts in part_map_types.items() if len(mts) >= 1)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# PROPERTIES
# ══════════════════════════════════════════════════════════════════════════════

def _live(self, context):
    mat = _active_mat(context)
    if mat and mat.pbr_props.is_built:
        build_network(mat)


class PBR_Overlay(PropertyGroup):
    name:        StringProperty(name="Name", default="Texture Layer")
    enabled:     BoolProperty(default=True, update=_live)
    path:        StringProperty(name="Image", subtype='FILE_PATH', update=_live)
    udim:        BoolProperty(name="UDIM", default=False, update=_live,
                              description="Treat as UDIM tile sequence")
    img_min:     FloatProperty(name="Min", default=0.0, min=0.0, max=1.0,
                               description="Black point", update=_live)
    img_max:     FloatProperty(name="Max", default=1.0, min=0.0, max=1.0,
                               description="White point", update=_live)
    blend_mode:  EnumProperty(items=BLEND_MODES, default='MIX', update=_live)
    strength:    FloatProperty(name="Strength", default=1.0, min=0.0, max=1.0,
                               subtype='FACTOR', update=_live)
    hue:         FloatProperty(name="Hue",        default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_live)
    saturation:  FloatProperty(name="Saturation", default=1.0, min=0.0, soft_max=2.0, update=_live)
    value:       FloatProperty(name="Value",      default=1.0, min=0.0, soft_max=2.0, update=_live)
    contrast:    FloatProperty(name="Contrast",   default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    gamma:       FloatProperty(name="Gamma",      default=1.0, min=0.01, soft_max=5.0, update=_live)
    mask_path:   StringProperty(name="Mask", subtype='FILE_PATH', update=_live)
    mask_udim:   BoolProperty(name="UDIM", default=False, update=_live,
                              description="Treat mask as UDIM tile sequence")
    mask_min:    FloatProperty(name="Min", default=0.0, min=0.0, max=1.0,
                               description="Mask black point", update=_live)
    mask_max:    FloatProperty(name="Max", default=1.0, min=0.0, max=1.0,
                               description="Mask white point", update=_live)
    mask_invert: BoolProperty(name="Invert", default=False, update=_live)
    mask_use_own_mapping: BoolProperty(name="Override Mapping", default=False, update=_live)
    mask_tiling_x:    FloatProperty(name="X", default=1.0, min=0.001, soft_max=100.0, update=_live)
    mask_tiling_y:    FloatProperty(name="Y", default=1.0, min=0.001, soft_max=100.0, update=_live)
    mask_tiling_lock: BoolProperty(name="Lock", default=True, update=_live)
    mask_offset_x:    FloatProperty(name="X", default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    mask_offset_y:    FloatProperty(name="Y", default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    mask_rotation:    FloatProperty(name="Rot", default=0.0, subtype='ANGLE', update=_live)
    mask_type:             EnumProperty(name='Mask Type', items=MASK_TYPES, default='IMAGE', update=_live)
    mask_proc_scale:       FloatProperty(name='Scale',      default=5.0, min=0.0, soft_max=100.0, update=_live)
    mask_proc_detail:      FloatProperty(name='Detail',     default=2.0, min=0.0, max=15.0,       update=_live)
    mask_proc_roughness:   FloatProperty(name='Roughness',  default=0.5, min=0.0, max=1.0,        update=_live)
    mask_proc_distortion:  FloatProperty(name='Distortion', default=0.0, min=-1000.0, max=1000.0, update=_live)
    mask_wave_type:        EnumProperty(name='Wave Type',    items=WAVE_TYPES,     default='BANDS', update=_live)
    mask_wave_profile:     EnumProperty(name='Wave Profile', items=WAVE_PROFILES,  default='SIN',   update=_live)
    mask_gradient_type:    EnumProperty(name='Gradient Type', items=GRADIENT_TYPES, default='LINEAR', update=_live)
    mask_voronoi_feature:  EnumProperty(name='Feature',  items=VORONOI_FEATURES,  default='F1',         update=_live)
    mask_voronoi_distance: EnumProperty(name='Distance', items=VORONOI_DISTANCES, default='EUCLIDEAN',  update=_live)
    mask_voronoi_random:   FloatProperty(name='Randomness', default=1.0, min=0.0, max=1.0, update=_live)
    img_tiling_x:    FloatProperty(name="X", default=1.0, min=0.001, soft_max=100.0, update=_live)
    img_tiling_y:    FloatProperty(name="Y", default=1.0, min=0.001, soft_max=100.0, update=_live)
    img_tiling_lock: BoolProperty(name="Lock", default=True, update=_live)
    img_offset_x:    FloatProperty(name="X", default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    img_offset_y:    FloatProperty(name="Y", default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    img_rotation:    FloatProperty(name="Rot", default=0.0, subtype='ANGLE', update=_live)
    img_use_own_mapping: BoolProperty(name="Override Mapping", default=False, update=_live)
    img_colorspace: StringProperty(name="Color Space", default='sRGB', update=_live)
    img_tex_coord: EnumProperty(name="Coordinate", default='UV', update=_live, items=[
        ('UV','UV',''),('OBJECT','Object',''),('GENERATED','Generated',''),
        ('CAMERA','Camera',''),('WINDOW','Window',''),('NORMAL','Normal',''),('REFLECTION','Reflection',''),
    ])
    img_projection: EnumProperty(name="Projection", default='FLAT', update=_live, items=[
        ('FLAT','Flat',''),('BOX','Box',''),('SPHERE','Sphere',''),('TUBE','Tube',''),
    ])
    img_projection_blend: FloatProperty(name="Blend", default=0.0, min=0.0, max=1.0, update=_live)
    mask_tex_coord: EnumProperty(name="Coordinate", default='UV', update=_live, items=[
        ('UV','UV',''),('OBJECT','Object',''),('GENERATED','Generated',''),
        ('CAMERA','Camera',''),('WINDOW','Window',''),('NORMAL','Normal',''),('REFLECTION','Reflection',''),
    ])
    mask_projection: EnumProperty(name="Projection", default='FLAT', update=_live, items=[
        ('FLAT','Flat',''),('BOX','Box',''),('SPHERE','Sphere',''),('TUBE','Tube',''),
    ])
    mask_projection_blend: FloatProperty(name="Blend", default=0.0, min=0.0, max=1.0, update=_live)
    show_overlay:             BoolProperty(default=True,  options={'SKIP_SAVE'})
    show_mask_settings:       BoolProperty(default=False, options={'SKIP_SAVE'})
    show_color_correction:    BoolProperty(default=False, options={'SKIP_SAVE'})


def _make_path_props():
    return {f"path_{k}": StringProperty(name=MAP_INFO[k][0], subtype='FILE_PATH')
            for k in MAP_KEYS}

def _make_use_props():
    return {f"use_{k}": BoolProperty(default=True, update=_live) for k in MAP_KEYS}

def _make_strength_props():
    return {f"str_{k}": FloatProperty(name="Strength", default=1.0,
                                        min=0.0, soft_max=100.0,
                                        update=_live)
            for k in MAP_KEYS}

def _make_udim_props():
    return {f"udim_{k}": BoolProperty(name="UDIM", default=False,
                                        description="Treat this path as a UDIM tile sequence",
                                        update=_live)
            for k in MAP_KEYS}

def _make_extra_props():
    return {f"extra_{k}": CollectionProperty(type=PBR_Overlay) for k in MAP_KEYS}

def _make_range_props():
    props = {}
    for k in GRAYSCALE_KEYS:
        props[f"min_{k}"] = FloatProperty(name="Min", default=0.0, min=0.0, max=1.0,
                                           description=f"{MAP_INFO[k][0]} black point", update=_live)
        props[f"max_{k}"] = FloatProperty(name="Max", default=1.0, min=0.0, max=1.0,
                                           description=f"{MAP_INFO[k][0]} white point", update=_live)
    return props

def _make_val_props():
    props = {}
    for k in MAP_KEYS:
        vtype = MAP_INFO[k][3]
        if vtype == 'COLOR':
            if k == 'sss_radius':
                props[f"val_{k}"] = FloatVectorProperty(name=MAP_INFO[k][0], subtype='NONE',
                                                         default=(1.0,0.2,0.1), size=3, min=0.0, soft_max=10.0, update=_live)
            else:
                default = (1.0,1.0,1.0,1.0) if k not in ('emission','specular_tint','sheen_tint') else (0.0,0.0,0.0,1.0)
                props[f"val_{k}"] = FloatVectorProperty(name=MAP_INFO[k][0], subtype='COLOR',
                                                         default=default, size=4, min=0.0, max=1.0, update=_live)
        elif vtype == 'FLOAT':
            defaults = {'roughness':0.5,'metallic':0.0,'ior':1.45,'specular':0.5,
                        'specular_ior':1.5,'diffuse_roughness':0.0,
                        'coat_weight':0.0,'sheen_weight':0.0,'opacity':1.0,'ao':1.0,
                        'sss':0.0,'translucency':0.0,'displacement':0.0,'glossiness':0.5,
                        'anisotropic':0.0,'anisotropic_rot':0.0,'coat_ior':1.5,'coat_roughness':0.03,
                        'sss_scale':0.05,'sss_anisotropy':0.0,'sss_ior':1.4,
                        'thin_film_thick':0.0,'thin_film_ior':1.5,
                        'sheen_roughness':0.5}
            range_overrides = {
                'ior':           (1.0, 5.0),
                'specular_ior':  (1.0, 5.0),
                'sss_ior':       (1.0, 5.0),
                'coat_ior':      (1.0, 5.0),
                'thin_film_ior': (1.0, 5.0),
                'sss_scale':     (0.0, 100.0),
                'thin_film_thick':(0.0, 1000.0),
                'displacement':  (-10.0, 10.0),
                'anisotropic_rot':(0.0, 1.0),
            }
            mn, mx = range_overrides.get(k, (0.0, 1.0))
            props[f"val_{k}"] = FloatProperty(name=MAP_INFO[k][0],
                                               default=defaults.get(k, 0.0),
                                               min=mn, soft_max=mx,
                                               update=_live)
    return props


class PBR_MapLayer(PropertyGroup):
    name:        StringProperty(name="Layer Name", default="Layer")
    enabled:     BoolProperty(default=True, update=_live)
    shader_type: EnumProperty(name="Shader", items=SHADER_ITEMS, default='PRINCIPLED', update=_live)

    tiling_x:    FloatProperty(name="X",        default=1.0, min=0.001, soft_max=100.0, update=_live)
    tiling_y:    FloatProperty(name="Y",        default=1.0, min=0.001, soft_max=100.0, update=_live)
    tiling_lock: BoolProperty(name="Lock",      default=True, update=_live)
    offset_x:    FloatProperty(name="X",        default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    offset_y:    FloatProperty(name="Y",        default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    rotation:    FloatProperty(name="Rotation", default=0.0, subtype='ANGLE', update=_live)

    hue:         FloatProperty(name="Hue",        default=0.5, min=0.0, max=1.0, subtype='FACTOR', update=_live)
    saturation:  FloatProperty(name="Saturation", default=1.0, min=0.0, soft_max=2.0, update=_live)
    value:       FloatProperty(name="Value",      default=1.0, min=0.0, soft_max=2.0, update=_live)
    contrast:    FloatProperty(name="Contrast",   default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    gamma:       FloatProperty(name="Gamma",      default=1.0, min=0.01, soft_max=5.0, update=_live)

    normal_strength:   FloatProperty(name="Normal Strength",   default=1.0, min=0.0, soft_max=10.0, update=_live)
    bump_strength:     FloatProperty(name="Bump Strength",     default=0.1, min=0.0, soft_max=1.0,  update=_live)
    normal_bump_mode:  EnumProperty(name="Use", update=_live, items=[
        ('NORMAL', 'Normal Map', 'Use Normal map only'),
        ('BUMP',   'Bump Map',   'Use Bump map only'),
        ('BOTH',   'Both',       'Stack Normal then Bump'),
    ], default='NORMAL')
    ao_strength:       FloatProperty(name="AO Strength",       default=0.8, min=0.0, soft_max=1.0,  subtype='FACTOR', update=_live)
    emission_strength: FloatProperty(name="Emission Strength", default=1.0, min=0.0, soft_max=10.0, update=_live)
    roughness_bias:    FloatProperty(name="Roughness Bias",    default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    metallic_bias:     FloatProperty(name="Metallic Bias",     default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)

    disp_scale:    FloatProperty(name="Scale",    default=0.1, min=0.0, soft_max=1.0, update=_live)
    disp_midlevel: FloatProperty(name="Midlevel", default=0.5, min=0.0, max=1.0,      update=_live)

    sss_scale: FloatProperty(name="SSS Scale", default=0.05, min=0.0, soft_max=2.0, update=_live)

    mask_path:        StringProperty(name="Mask", subtype='FILE_PATH', update=_live)
    mask_udim:        BoolProperty(name="UDIM", default=False, update=_live,
                                   description="Treat mask as UDIM tile sequence")
    mask_invert:      BoolProperty(name="Invert", default=False, update=_live)
    mask_strength:    FloatProperty(name="Strength", default=1.0, min=0.0, max=1.0, subtype='FACTOR', update=_live)
    mask_min:         FloatProperty(name="Min", default=0.0, min=0.0, max=1.0, update=_live)
    mask_max:         FloatProperty(name="Max", default=1.0, min=0.0, max=1.0, update=_live)
    blend_mode:       EnumProperty(name="Blend", items=BLEND_MODES, default='MIX', update=_live)
    mask_type:             EnumProperty(name='Mask Type', items=MASK_TYPES, default='IMAGE', update=_live)
    mask_proc_scale:       FloatProperty(name='Scale',      default=5.0, min=0.0, soft_max=100.0, update=_live)
    mask_proc_detail:      FloatProperty(name='Detail',     default=2.0, min=0.0, max=15.0,       update=_live)
    mask_proc_roughness:   FloatProperty(name='Roughness',  default=0.5, min=0.0, max=1.0,        update=_live)
    mask_proc_distortion:  FloatProperty(name='Distortion', default=0.0, min=-1000.0, max=1000.0, update=_live)
    mask_wave_type:        EnumProperty(name='Wave Type',    items=WAVE_TYPES,     default='BANDS', update=_live)
    mask_wave_profile:     EnumProperty(name='Wave Profile', items=WAVE_PROFILES,  default='SIN',   update=_live)
    mask_gradient_type:    EnumProperty(name='Gradient Type', items=GRADIENT_TYPES, default='LINEAR', update=_live)
    mask_voronoi_feature:  EnumProperty(name='Feature',  items=VORONOI_FEATURES,  default='F1',        update=_live)
    mask_voronoi_distance: EnumProperty(name='Distance', items=VORONOI_DISTANCES, default='EUCLIDEAN', update=_live)
    mask_voronoi_random:   FloatProperty(name='Randomness', default=1.0, min=0.0, max=1.0, update=_live)
    mask_tiling_x:    FloatProperty(name="X", default=1.0, min=0.001, soft_max=100.0, update=_live)
    mask_tiling_y:    FloatProperty(name="Y", default=1.0, min=0.001, soft_max=100.0, update=_live)
    mask_tiling_lock: BoolProperty(name="Lock", default=True, update=_live)
    mask_offset_x:    FloatProperty(name="X", default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    mask_offset_y:    FloatProperty(name="Y", default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    mask_rotation:    FloatProperty(name="Rot", default=0.0, subtype='ANGLE', update=_live)
    mask_tex_coord:   EnumProperty(name="Coordinate", default='UV', update=_live, items=[
        ('UV','UV',''),('OBJECT','Object',''),('GENERATED','Generated',''),
        ('CAMERA','Camera',''),('WINDOW','Window',''),('NORMAL','Normal',''),('REFLECTION','Reflection',''),
    ])
    mask_projection:  EnumProperty(name="Projection", default='FLAT', update=_live, items=[
        ('FLAT','Flat',''),('BOX','Box',''),('SPHERE','Sphere',''),('TUBE','Tube',''),
    ])
    mask_projection_blend: FloatProperty(name="Blend", default=0.0, min=0.0, max=1.0, update=_live)

    specular_distribution: EnumProperty(
        name="Distribution",
        items=[('GGX','GGX',''),('MULTI_GGX','Multiscatter GGX','')],
        default='MULTI_GGX', update=_live)
    sss_method: EnumProperty(
        name="SSS Method",
        items=[('BURLEY','Christensen-Burley',''),
               ('RANDOM_WALK','Random Walk',''),
               ('RANDOM_WALK_SKIN','Random Walk (Skin)','')],
        default='RANDOM_WALK', update=_live)

    bc_tiling_x:    FloatProperty(name="X",   default=1.0, min=0.001, soft_max=100.0, update=_live)
    bc_tiling_y:    FloatProperty(name="Y",   default=1.0, min=0.001, soft_max=100.0, update=_live)
    bc_tiling_lock: BoolProperty(name="Lock", default=True, update=_live)
    bc_offset_x:    FloatProperty(name="X",   default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    bc_offset_y:    FloatProperty(name="Y",   default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    bc_rotation:    FloatProperty(name="Rot", default=0.0, subtype='ANGLE', update=_live)
    bc_use_own_mapping: BoolProperty(name="Override Mapping", default=False, update=_live)
    scan_dir_path: StringProperty(name="Folder", subtype='DIR_PATH', default="")
    scan_filter:   StringProperty(name="Part Filter", default="",
                                  description="Only scan files whose name contains this keyword (e.g. 'hair', 'body')")
    orm_path:      StringProperty(name="ORM Map", subtype='FILE_PATH', default="", update=_live)
    orm_layout:    EnumProperty(name="ORM Layout", items=ORM_LAYOUTS, default='AO_ROUGH_MET', update=_live)
    tri_planar:    BoolProperty(name="Tri-Planar Projection", default=False, update=_live,
                                description="Legacy — use Projection Type instead")
    tex_coord_src: EnumProperty(name="Texture Coordinate",
        items=[
            ('UV',         'UV',         'Standard UV map'),
            ('OBJECT',     'Object',     'Object-space coordinates'),
            ('GENERATED',  'Generated',  'Auto-generated coordinates'),
            ('CAMERA',     'Camera',     'Camera / projector space'),
            ('WINDOW',     'Window',     'Screen-space projection'),
            ('NORMAL',     'Normal',     'Surface normal direction'),
            ('REFLECTION', 'Reflection', 'Reflection / environment'),
        ],
        default='UV', update=_live)
    img_projection: EnumProperty(name="Image Projection",
        items=[
            ('FLAT',   'Flat',   'Standard flat projection'),
            ('BOX',    'Box',    'Box / tri-planar (blends 3 axes)'),
            ('SPHERE', 'Sphere', 'Spherical projection'),
            ('TUBE',   'Tube',   'Cylindrical projection'),
        ],
        default='FLAT', update=_live)
    img_projection_blend: FloatProperty(name="Blend", default=0.0, min=0.0, max=1.0,
        description="Box projection blend at seams", update=_live)
    tiling_z:   FloatProperty(name="Z", default=1.0, min=0.001, soft_max=100.0, update=_live)
    offset_z:   FloatProperty(name="Z", default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
    normal_dx:     BoolProperty(name="DirectX Normal Map", default=False, update=_live,
                                description="Flip green channel: DirectX → OpenGL convention")

    expanded:      BoolProperty(default=True,  options={'SKIP_SAVE'})
    show_maps:     BoolProperty(default=False, options={'SKIP_SAVE'})
    show_mapping:  BoolProperty(default=False, options={'SKIP_SAVE'})
    show_color:    BoolProperty(default=False, options={'SKIP_SAVE'})
    show_surface:  BoolProperty(default=False, options={'SKIP_SAVE'})
    show_geometry: BoolProperty(default=False, options={'SKIP_SAVE'})
    show_mask:     BoolProperty(default=False, options={'SKIP_SAVE'})


def _make_own_transform_props():
    props = {}
    for k in MAP_KEYS:
        props[f"ch_tiling_x_{k}"]    = FloatProperty(name="X",   default=1.0, min=0.001, soft_max=100.0, update=_live)
        props[f"ch_tiling_y_{k}"]    = FloatProperty(name="Y",   default=1.0, min=0.001, soft_max=100.0, update=_live)
        props[f"ch_tiling_lock_{k}"] = BoolProperty(name="Lock", default=True, update=_live)
        props[f"ch_offset_x_{k}"]    = FloatProperty(name="X",   default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
        props[f"ch_offset_y_{k}"]    = FloatProperty(name="Y",   default=0.0, soft_min=-1.0, soft_max=1.0, update=_live)
        props[f"ch_rotation_{k}"]    = FloatProperty(name="Rot", default=0.0, subtype='ANGLE', update=_live)
        props[f"ch_own_mapping_{k}"] = BoolProperty(name="Override Mapping", default=False, update=_live)
    return props

def _make_cs_props():
    props = {}
    for k in MAP_KEYS:
        default_cs = _MAP_DEFAULT_CS.get(k, 'Non-Color')
        props[f"cs_{k}"] = StringProperty(
            name="Color Space",
            description=f"Color space override (default: {default_cs})",
            default=default_cs,
            update=_live,
        )
    return props

_slot_show  = {f"show_slot_{k}":     BoolProperty(default=False, options={'SKIP_SAVE'}) for k in MAP_KEYS}
_group_show = {f"show_group_{g[0]}": BoolProperty(default=False, options={'SKIP_SAVE'}) for g in MAP_GROUPS}
for _k, _prop in {**_make_path_props(), **_make_use_props(), **_make_udim_props(),
                   **_make_strength_props(),
                   **_make_extra_props(), **_make_range_props(),
                   **_make_val_props(), **_make_own_transform_props(),
                   **_make_cs_props(),
                   **_slot_show, **_group_show}.items():
    PBR_MapLayer.__annotations__[_k] = _prop


class PBR_MaterialProps(PropertyGroup):
    layers:             CollectionProperty(type=PBR_MapLayer)
    active_layer_index: IntProperty(default=0)
    is_built:           BoolProperty(default=False)
    solo_layer:         IntProperty(default=-1, description="Index of soloed layer (-1 = none)")
    compact_mode:       BoolProperty(name="Compact", default=False,
                                     description="Hide Coat, Sheen, Thin Film, SSS sub-param groups")
    detail_view:        BoolProperty(name="Detail View", default=True,
                                     description="Show full controls per slot")


# ── Helpers ───────────────────────────────────────────────────────────────────
def _ppath(layer, key):
    p = getattr(layer, f"path_{key}", '').strip()
    return bpy.path.abspath(p) if p else ''

def _has_img(layer, key):
    p = _ppath(layer, key)
    return bool(p and os.path.isfile(p))

def _has_extras(layer, key):
    return any(
        os.path.isfile(bpy.path.abspath(e.path.strip()))
        for e in getattr(layer, f"extra_{key}", [])
        if e.path.strip()
    )

def _use(layer, key):
    return getattr(layer, f"use_{key}", True)


# ══════════════════════════════════════════════════════════════════════════════
# CONTEXT
# ══════════════════════════════════════════════════════════════════════════════

def _active_mat(context):
    spc = getattr(context, 'space_data', None)
    if spc and getattr(spc, 'type', '') == 'NODE_EDITOR':
        id_ = getattr(spc, 'id', None)
        if isinstance(id_, bpy.types.Material): return id_
    obj = getattr(context, 'active_object', None)
    if obj and obj.type == 'MESH': return obj.active_material
    return None


# ══════════════════════════════════════════════════════════════════════════════
# NODE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _nl(li, tag):   return f"L{li}_{tag}"

def _by_lbl(nt, l):
    for n in nt.nodes:
        if n.get('pbr_id') == l:
            return n
    return next((n for n in nt.nodes if n.label == l), None)

def _ensure(nt, ntype, label, x, y):
    n = _by_lbl(nt, label)
    if n is None:
        n = nt.nodes.new(ntype)
        n['pbr_id'] = label
        n.label = label
        n.location = (x, y)
    else:
        if not n.get('pbr_id'):
            n['pbr_id'] = label
    return n

def _link(nt, a, b):
    for l in list(b.links): nt.links.remove(l)
    nt.links.new(a, b)

def _load_img(path, cs, udim=False):
    if not path or not path.strip():
        return None
    abs_path = bpy.path.abspath(path.strip())

    if udim:
        img_name = os.path.basename(abs_path)
        existing = bpy.data.images.get(img_name)
        if existing and existing.source == 'TILED':
            existing.colorspace_settings.name = cs
            return existing
        if existing:
            bpy.data.images.remove(existing)
        if not os.path.isfile(abs_path):
            return None
        img = bpy.data.images.load(abs_path, check_existing=False)
        img.name   = img_name
        img.source = 'TILED'
        img.colorspace_settings.name = cs
        try: img.reload()
        except Exception: pass
        return img

    if not os.path.isfile(abs_path):
        return None
    try:
        img = bpy.data.images.load(abs_path, check_existing=True)
        img.colorspace_settings.name = cs
        if img.source == 'TILED':
            img.source = 'FILE'
        return img
    except Exception:
        return None

def _purge(nt, prefix):
    to_remove = [n for n in nt.nodes if
                 n.get('pbr_id', '').startswith(prefix) or n.label.startswith(prefix)]
    for n in to_remove:
        nt.nodes.remove(n)

def _maprange(nt, label, in_sock, mn, mx, x, y):
    if mn == 0.0 and mx == 1.0:
        n = _by_lbl(nt, label)
        if n: nt.nodes.remove(n)
        return in_sock
    mr = _ensure(nt, 'ShaderNodeMapRange', label, x, y)
    mr.data_type = 'FLOAT'
    mr.interpolation_type = 'LINEAR'
    mr.clamp = True
    mr.inputs[1].default_value = mn
    mr.inputs[2].default_value = mx
    mr.inputs[3].default_value = 0.0
    mr.inputs[4].default_value = 1.0
    _link(nt, in_sock, mr.inputs[0])
    return mr.outputs[0]

def _bsdf_out(bsdf, stype):
    name = SHADER_OUTPUT_SOCKET.get(stype, 'BSDF')
    try: return bsdf.outputs[name]
    except Exception: return bsdf.outputs[0]

def _sock(bsdf, name_or_tuple):
    names = name_or_tuple if isinstance(name_or_tuple, (list, tuple)) else [name_or_tuple]
    for nm in names:
        try: return bsdf.inputs[nm]
        except Exception: pass
    return None

def _connect(nt, bsdf, key, sockets_map, out_sock):
    target = sockets_map.get(key)
    if not target: return
    s = _sock(bsdf, target)
    if s: _link(nt, out_sock, s)

def _set_val(bsdf, key, sockets_map, value):
    target = sockets_map.get(key)
    if not target: return
    s = _sock(bsdf, target)
    if s:
        try: s.default_value = value
        except Exception: pass


# ══════════════════════════════════════════════════════════════════════════════
# MASK BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def _build_proc_mask(nt, props, label_prefix, x, y):
    mtype  = getattr(props, 'mask_type', 'NOISE')
    scale  = getattr(props, 'mask_proc_scale', 5.0)
    detail = getattr(props, 'mask_proc_detail', 2.0)
    rough  = getattr(props, 'mask_proc_roughness', 0.5)
    dist   = getattr(props, 'mask_proc_distortion', 0.0)
    tx     = getattr(props, 'mask_tiling_x', 1.0)
    ty     = getattr(props, 'mask_tiling_y', 1.0)
    lock   = getattr(props, 'mask_tiling_lock', True)
    ox     = getattr(props, 'mask_offset_x', 0.0)
    oy     = getattr(props, 'mask_offset_y', 0.0)
    rot    = getattr(props, 'mask_rotation', 0.0)

    uv   = _ensure(nt, 'ShaderNodeTexCoord', f"{label_prefix}_UV",   x - 440, y)
    mapp = _ensure(nt, 'ShaderNodeMapping',  f"{label_prefix}_MAPP", x - 220, y)
    _link(nt, uv.outputs['UV'], mapp.inputs['Vector'])
    mapp.inputs['Scale'].default_value    = (tx, ty if not lock else tx, 1.0)
    mapp.inputs['Location'].default_value = (ox, oy, 0.0)
    mapp.inputs['Rotation'].default_value = (0.0, 0.0, rot)

    if mtype == 'NOISE':
        nd = _ensure(nt, 'ShaderNodeTexNoise', f"{label_prefix}_PROC", x, y)
        nd.inputs['Scale'].default_value       = scale
        nd.inputs['Detail'].default_value      = detail
        nd.inputs['Roughness'].default_value   = rough
        nd.inputs['Distortion'].default_value  = dist
        _link(nt, mapp.outputs['Vector'], nd.inputs['Vector'])
        return nd.outputs['Fac']

    elif mtype == 'WAVE':
        nd = _ensure(nt, 'ShaderNodeTexWave', f"{label_prefix}_PROC", x, y)
        nd.wave_type    = getattr(props, 'mask_wave_type',    'BANDS')
        nd.bands_direction = 'X'
        nd.wave_profile = getattr(props, 'mask_wave_profile', 'SIN')
        nd.inputs['Scale'].default_value      = scale
        nd.inputs['Distortion'].default_value = dist
        nd.inputs['Detail'].default_value     = detail
        nd.inputs['Detail Roughness'].default_value = rough
        _link(nt, mapp.outputs['Vector'], nd.inputs['Vector'])
        return nd.outputs['Color']

    elif mtype == 'GRADIENT':
        nd = _ensure(nt, 'ShaderNodeTexGradient', f"{label_prefix}_PROC", x, y)
        nd.gradient_type = getattr(props, 'mask_gradient_type', 'LINEAR')
        _link(nt, mapp.outputs['Vector'], nd.inputs['Vector'])
        return nd.outputs['Fac']

    elif mtype == 'VORONOI':
        nd = _ensure(nt, 'ShaderNodeTexVoronoi', f"{label_prefix}_PROC", x, y)
        nd.feature        = getattr(props, 'mask_voronoi_feature',  'F1')
        nd.distance       = getattr(props, 'mask_voronoi_distance', 'EUCLIDEAN')
        nd.inputs['Scale'].default_value      = scale
        nd.inputs['Randomness'].default_value = getattr(props, 'mask_voronoi_random', 1.0)
        _link(nt, mapp.outputs['Vector'], nd.inputs['Vector'])
        try:    return nd.outputs['Distance']
        except: return nd.outputs['Color']

    return None

def _build_mask(nt, mask_path, mask_invert, mask_min, mask_max,
                tx, ty, lock, ox, oy, rot,
                uv_node, label_prefix, x, y,
                mask_type='IMAGE', proc_props=None, udim=False):
    if mask_type != 'IMAGE' and proc_props is not None:
        out = _build_proc_mask(nt, proc_props, label_prefix, x, y)
        if out is None:
            _purge(nt, f"{label_prefix}_")
            return None
        if mask_invert:
            inv = _ensure(nt, 'ShaderNodeInvert', f"{label_prefix}_INV", x + 220, y)
            _link(nt, out, inv.inputs['Color'])
            out = inv.outputs['Color']
        else:
            n = _by_lbl(nt, f"{label_prefix}_INV")
            if n: nt.nodes.remove(n)
        out = _maprange(nt, f"{label_prefix}_RANGE", out, mask_min, mask_max, x + 440, y)
        n = _by_lbl(nt, f"{label_prefix}_TEX")
        if n: nt.nodes.remove(n)
        return out

    abs_mp = bpy.path.abspath(mask_path.strip()) if mask_path.strip() else ''
    if not abs_mp or not os.path.isfile(abs_mp):
        _purge(nt, f"{label_prefix}_")
        return None
    n = _by_lbl(nt, f"{label_prefix}_PROC")
    if n: nt.nodes.remove(n)

    mapp = _ensure(nt, 'ShaderNodeMapping', f"{label_prefix}_MAPP", x - 220, y)
    _link(nt, uv_node.outputs['UV'], mapp.inputs['Vector'])
    ty_ = ty if not lock else tx
    mapp.inputs['Scale'].default_value    = (tx, ty_, 1.0)
    mapp.inputs['Location'].default_value = (ox, oy, 0.0)
    mapp.inputs['Rotation'].default_value = (0.0, 0.0, rot)

    tex = _ensure(nt, 'ShaderNodeTexImage', f"{label_prefix}_TEX", x, y)
    img = _load_img(abs_mp, 'Non-Color', udim=udim)
    if img: tex.image = img
    if udim:
        _link(nt, uv_node.outputs['UV'], tex.inputs['Vector'])
        n = _by_lbl(nt, f"{label_prefix}_MAPP")
        if n: nt.nodes.remove(n)
    else:
        _link(nt, mapp.outputs['Vector'], tex.inputs['Vector'])

    out = tex.outputs['Color']

    if mask_invert:
        inv = _ensure(nt, 'ShaderNodeInvert', f"{label_prefix}_INV", x + 220, y)
        _link(nt, out, inv.inputs['Color'])
        out = inv.outputs['Color']
    else:
        n = _by_lbl(nt, f"{label_prefix}_INV")
        if n: nt.nodes.remove(n)

    out = _maprange(nt, f"{label_prefix}_RANGE", out, mask_min, mask_max, x + 440, y)
    return out


# ══════════════════════════════════════════════════════════════════════════════
# CHANNEL COMPOSITE BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def _disconnect_bsdf_input(nt, bsdf, key, sockets_map):
    """Remove any link going into the BSDF socket for this key."""
    target = sockets_map.get(key)
    if not target: return
    s = _sock(bsdf, target)
    if s:
        for lnk in list(s.links):
            nt.links.remove(lnk)


def _build_channel(nt, layer, li, key, mapp_node, uv_node, x, y, cc_layer=None):
    label, icon, cs, vtype = MAP_INFO[key]
    px   = _ppath(layer, key)
    use  = _use(layer, key)
    TAG  = _nl(li, key.upper())

    if not use:
        # Mute only THIS channel's nodes — exclude nodes of longer-named keys sharing our prefix
        other_tags = {_nl(li, k.upper()) for k in MAP_KEYS if k != key and _nl(li, k.upper()).startswith(TAG + '_')}
        for n in nt.nodes:
            pid = n.get('pbr_id', '')
            if pid.startswith(TAG + '_') and not any(pid.startswith(t + '_') for t in other_tags):
                n.mute = True
        return None

    # Re-enable: unmute only THIS channel's nodes
    other_tags = {_nl(li, k.upper()) for k in MAP_KEYS if k != key and _nl(li, k.upper()).startswith(TAG + '_')}
    for n in nt.nodes:
        pid = n.get('pbr_id', '')
        if pid.startswith(TAG + '_') and not any(pid.startswith(t + '_') for t in other_tags):
            n.mute = False

    extras = getattr(layer, f"extra_{key}", [])
    valid_extras = [e for e in extras if e.path.strip() and
                    os.path.isfile(bpy.path.abspath(e.path.strip()))]

    has_primary = px and os.path.isfile(px)

    if not has_primary and not valid_extras:
        _purge(nt, f"{TAG}_")
        return None

    cur_y = y

    if has_primary:
        is_udim = getattr(layer, f'udim_{key}', False)
        cs_override = getattr(layer, f'cs_{key}', '').strip()
        effective_cs = cs_override if cs_override else cs
        img = _load_img(px, effective_cs, udim=is_udim)

        if key == 'base_color' and getattr(layer, 'bc_use_own_mapping', False):
            bc_uv   = _ensure(nt, 'ShaderNodeTexCoord', f"{TAG}_BCUV",   x - 440, cur_y)
            bc_mapp = _ensure(nt, 'ShaderNodeMapping',  f"{TAG}_BCMAPP", x - 220, cur_y)
            _link(nt, bc_uv.outputs['UV'], bc_mapp.inputs['Vector'])
            bc_ty = layer.bc_tiling_y if not layer.bc_tiling_lock else layer.bc_tiling_x
            bc_mapp.inputs['Scale'].default_value    = (layer.bc_tiling_x, bc_ty, 1.0)
            bc_mapp.inputs['Location'].default_value = (layer.bc_offset_x, layer.bc_offset_y, 0.0)
            bc_mapp.inputs['Rotation'].default_value = (0.0, 0.0, layer.bc_rotation)
            vec_src = bc_mapp.outputs['Vector']
        elif getattr(layer, f'ch_own_mapping_{key}', False):
            ch_uv   = _ensure(nt, 'ShaderNodeTexCoord', f"{TAG}_CHUV",   x - 440, cur_y)
            ch_mapp = _ensure(nt, 'ShaderNodeMapping',  f"{TAG}_CHMAPP", x - 220, cur_y)
            _link(nt, ch_uv.outputs['UV'], ch_mapp.inputs['Vector'])
            ch_ty = getattr(layer, f'ch_tiling_y_{key}', 1.0) if not getattr(layer, f'ch_tiling_lock_{key}', True) else getattr(layer, f'ch_tiling_x_{key}', 1.0)
            ch_mapp.inputs['Scale'].default_value    = (getattr(layer, f'ch_tiling_x_{key}', 1.0), ch_ty, 1.0)
            ch_mapp.inputs['Location'].default_value = (getattr(layer, f'ch_offset_x_{key}', 0.0), getattr(layer, f'ch_offset_y_{key}', 0.0), 0.0)
            ch_mapp.inputs['Rotation'].default_value = (0.0, 0.0, getattr(layer, f'ch_rotation_{key}', 0.0))
            vec_src = ch_mapp.outputs['Vector']
        else:
            for lbl in (f"{TAG}_BCUV", f"{TAG}_BCMAPP", f"{TAG}_CHUV", f"{TAG}_CHMAPP"):
                n = _by_lbl(nt, lbl)
                if n: nt.nodes.remove(n)
            vec_src = uv_node.outputs['UV'] if is_udim else mapp_node.outputs['Vector']

        img_proj       = getattr(layer, 'img_projection', 'FLAT')
        img_proj_blend = getattr(layer, 'img_projection_blend', 0.0)

        pn = _ensure(nt, 'ShaderNodeTexImage', f"{TAG}_IMG0", x, cur_y)
        if img: pn.image = img
        pn.projection       = img_proj
        pn.projection_blend = img_proj_blend
        _link(nt, vec_src, pn.inputs['Vector'])
        out = pn.outputs['Color']

        str_val = getattr(layer, f'str_{key}', 1.0)
        if str_val != 1.0:
            vtype = MAP_INFO[key][3]
            if vtype == 'COLOR':
                sm = _ensure(nt, 'ShaderNodeMixRGB', f"{TAG}_STR", x + 220, cur_y)
                sm.blend_type = 'MULTIPLY'
                sm.inputs['Fac'].default_value = 1.0
                sm.inputs['Color1'].default_value = (str_val, str_val, str_val, 1.0)
                _link(nt, out, sm.inputs['Color2'])
                out = sm.outputs['Color']
            else:
                sm = _ensure(nt, 'ShaderNodeMath', f"{TAG}_STR", x + 220, cur_y)
                sm.operation = 'MULTIPLY'
                sm.inputs[1].default_value = str_val
                _link(nt, out, sm.inputs[0])
                out = sm.outputs['Value']
        else:
            n = _by_lbl(nt, f"{TAG}_STR")
            if n: nt.nodes.remove(n)

        if key in GRAYSCALE_KEYS:
            mn = getattr(layer, f"min_{key}", 0.0)
            mx = getattr(layer, f"max_{key}", 1.0)
            out = _maprange(nt, f"{TAG}_RANGE0", out, mn, mx, x + 240, cur_y)

        if cc_layer is not None:
            cc_x = x + 500
            hs_exists = _by_lbl(nt, f"{TAG}_HUESAT") is not None
            hs = _ensure(nt, 'ShaderNodeHueSaturation', f"{TAG}_HUESAT", cc_x, cur_y)
            if not hs_exists:
                hs.inputs['Hue'].default_value        = cc_layer.hue
                hs.inputs['Saturation'].default_value = cc_layer.saturation
                hs.inputs['Value'].default_value      = cc_layer.value
            _link(nt, out, hs.inputs['Color'])
            out = hs.outputs['Color']
            bc_exists = _by_lbl(nt, f"{TAG}_BRTCON") is not None
            bc_n = _ensure(nt, 'ShaderNodeBrightContrast', f"{TAG}_BRTCON", cc_x + 220, cur_y)
            if not bc_exists:
                bc_n.inputs['Bright'].default_value   = 0.0
                bc_n.inputs['Contrast'].default_value = cc_layer.contrast
            _link(nt, out, bc_n.inputs['Color'])
            out = bc_n.outputs['Color']
            gm_exists = _by_lbl(nt, f"{TAG}_GAMMA") is not None
            gm_n = _ensure(nt, 'ShaderNodeGamma', f"{TAG}_GAMMA", cc_x + 440, cur_y)
            if not gm_exists:
                gm_n.inputs['Gamma'].default_value = cc_layer.gamma
            _link(nt, out, gm_n.inputs['Color'])
            out = gm_n.outputs['Color']
        cur_y -= 350
    else:
        first = valid_extras.pop(0)
        pn = _ensure(nt, 'ShaderNodeTexImage', f"{TAG}_IMG0", x, cur_y)
        img = _load_img(bpy.path.abspath(first.path.strip()), cs)
        if img: pn.image = img
        _link(nt, mapp_node.outputs['Vector'], pn.inputs['Vector'])
        out = pn.outputs['Color']
        if key in GRAYSCALE_KEYS:
            out = _maprange(nt, f"{TAG}_RANGE0", out, first.img_min, first.img_max, x + 240, cur_y)
        cur_y -= 350

    for oi, extra in enumerate(valid_extras):
        if not extra.enabled: continue
        EP = f"{TAG}_OV{oi}"

        ex_tex = _ensure(nt, 'ShaderNodeTexImage', f"{EP}_TEX", x, cur_y)
        ov_udim = getattr(extra, 'udim', False)
        ov_cs_override = getattr(extra, 'img_colorspace', '').strip()
        ov_effective_cs = ov_cs_override if ov_cs_override else cs
        img = _load_img(bpy.path.abspath(extra.path.strip()), ov_effective_cs, udim=ov_udim)
        if img: ex_tex.image = img
        if getattr(extra, 'img_use_own_mapping', False):
            ov_uv   = _ensure(nt, 'ShaderNodeTexCoord', f"{EP}_OVUV",   x - 440, cur_y)
            ov_mapp = _ensure(nt, 'ShaderNodeMapping',  f"{EP}_OVMAPP", x - 220, cur_y)
            _link(nt, ov_uv.outputs['UV'], ov_mapp.inputs['Vector'])
            ov_ty = extra.img_tiling_y if not extra.img_tiling_lock else extra.img_tiling_x
            ov_mapp.inputs['Scale'].default_value    = (extra.img_tiling_x, ov_ty, 1.0)
            ov_mapp.inputs['Location'].default_value = (extra.img_offset_x, extra.img_offset_y, 0.0)
            ov_mapp.inputs['Rotation'].default_value = (0.0, 0.0, extra.img_rotation)
            ov_vec = ov_mapp.outputs['Vector']
        else:
            for lbl in (f"{EP}_OVUV", f"{EP}_OVMAPP"):
                n = _by_lbl(nt, lbl)
                if n: nt.nodes.remove(n)
            ov_vec = uv_node.outputs['UV'] if ov_udim else mapp_node.outputs['Vector']
        _link(nt, ov_vec, ex_tex.inputs['Vector'])
        ex_out = ex_tex.outputs['Color']

        if key in GRAYSCALE_KEYS:
            ex_out = _maprange(nt, f"{EP}_IMGRANGE", ex_out,
                               extra.img_min, extra.img_max, x + 240, cur_y)

        ov_hs = _ensure(nt, 'ShaderNodeHueSaturation', f"{EP}_HUESAT", x + 500, cur_y)
        ov_hs.inputs['Hue'].default_value        = extra.hue
        ov_hs.inputs['Saturation'].default_value = extra.saturation
        ov_hs.inputs['Value'].default_value      = extra.value
        _link(nt, ex_out, ov_hs.inputs['Color'])
        ex_out = ov_hs.outputs['Color']
        ov_bc = _ensure(nt, 'ShaderNodeBrightContrast', f"{EP}_BRTCON", x + 720, cur_y)
        ov_bc.inputs['Bright'].default_value   = 0.0
        ov_bc.inputs['Contrast'].default_value = extra.contrast
        _link(nt, ex_out, ov_bc.inputs['Color'])
        ex_out = ov_bc.outputs['Color']
        ov_gm = _ensure(nt, 'ShaderNodeGamma', f"{EP}_GAMMA", x + 940, cur_y)
        ov_gm.inputs['Gamma'].default_value = extra.gamma
        _link(nt, ex_out, ov_gm.inputs['Color'])
        ex_out = ov_gm.outputs['Color']

        mix = _ensure(nt, 'ShaderNodeMixRGB', f"{EP}_MIX", x + 1200, cur_y + 175)
        mix.blend_type = extra.blend_mode
        _link(nt, out,    mix.inputs['Color1'])
        _link(nt, ex_out, mix.inputs['Color2'])

        fac = _build_mask(nt, extra.mask_path, extra.mask_invert,
                          extra.mask_min, extra.mask_max,
                          extra.mask_tiling_x, extra.mask_tiling_y, extra.mask_tiling_lock,
                          extra.mask_offset_x, extra.mask_offset_y, extra.mask_rotation,
                          uv_node, f"{EP}_MASK", x - 500, cur_y - 200,
                          mask_type=getattr(extra,'mask_type','IMAGE'), proc_props=extra,
                          udim=getattr(extra, 'mask_udim', False))
        if fac:
            str_n = _ensure(nt, 'ShaderNodeMath', f"{EP}_STR", x - 200, cur_y - 200)
            str_n.operation = 'MULTIPLY'
            str_n.inputs[1].default_value = extra.strength
            _link(nt, fac, str_n.inputs[0])
            _link(nt, str_n.outputs['Value'], mix.inputs['Fac'])
        else:
            mix.inputs['Fac'].default_value = extra.strength

        out = mix.outputs['Color']
        cur_y -= 350

    return out


# ══════════════════════════════════════════════════════════════════════════════
# LAYER BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def _build_layer(nt, layer, li, y_base):
    X_UV  = -1800
    X_MAP = -1580
    X_TEX = -1200
    X_MID = 200
    X_AO  = 560
    X_BSD = 800
    STEP  = 380

    stype   = layer.shader_type
    v_keys  = SHADER_MAPS.get(stype, MAP_KEYS)
    sockets = BSDF_SOCKETS.get(stype, {})

    uv   = _ensure(nt, 'ShaderNodeTexCoord', _nl(li,'UV'),   X_UV,  y_base)
    mapp = _ensure(nt, 'ShaderNodeMapping',  _nl(li,'MAPP'), X_MAP, y_base)

    uv.object = None
    src = getattr(layer, 'tex_coord_src', 'UV')
    if getattr(layer, 'tri_planar', False) and src == 'UV':
        src = 'OBJECT'
    _COORD_OUT = {
        'UV': 'UV', 'OBJECT': 'Object', 'GENERATED': 'Generated',
        'CAMERA': 'Camera', 'WINDOW': 'Window',
        'NORMAL': 'Normal', 'REFLECTION': 'Reflection',
    }
    try:
        coord_out = uv.outputs[_COORD_OUT.get(src, 'UV')]
    except Exception:
        coord_out = uv.outputs['UV']

    _link(nt, coord_out, mapp.inputs['Vector'])
    ty = layer.tiling_y if not layer.tiling_lock else layer.tiling_x
    tz = layer.tiling_x if layer.tiling_lock else getattr(layer, 'tiling_z', 1.0)
    mapp.inputs['Scale'].default_value = (layer.tiling_x, ty, tz)
    mapp.inputs['Location'].default_value = (
        layer.offset_x,
        layer.offset_y,
        getattr(layer, 'offset_z', 0.0))
    mapp.inputs['Rotation'].default_value = (0.0, 0.0, layer.rotation)

    bsdf_new = False
    bsdf = _by_lbl(nt, _nl(li,'BSDF'))
    if bsdf is None:
        if li == 0:
            bsdf = next((n for n in nt.nodes
                         if n.type == SHADER_BSDF_TYPE.get(stype,'') and not n.get('pbr_id') and not n.label), None)
        if bsdf is None:
            bsdf = nt.nodes.new(SHADER_NODE_TYPE[stype])
            bsdf_new = True
        bsdf['pbr_id'] = _nl(li,'BSDF')
        bsdf.label = _nl(li,'BSDF')
    elif bsdf.type != SHADER_BSDF_TYPE.get(stype,''):
        loc = bsdf.location.copy()
        nt.nodes.remove(bsdf)
        bsdf = nt.nodes.new(SHADER_NODE_TYPE[stype])
        bsdf_new = True
        bsdf['pbr_id'] = _nl(li,'BSDF')
        bsdf.label = _nl(li,'BSDF')
        bsdf.location = loc
    bsdf.location = (X_BSD, y_base)

    y_cur = [y_base - STEP]
    def ny(): v = y_cur[0]; y_cur[0] -= STEP; return v

    def ch(key, cc=False):
        return _build_channel(nt, layer, li, key, mapp, uv, X_TEX, ny(),
                              cc_layer=layer if cc else None)

    def _mute_tag(tag, mute):
        for n in nt.nodes:
            pid = n.get('pbr_id', '')
            if pid.startswith(tag + '_'):
                n.mute = mute

    if 'base_color' in v_keys and 'base_color' in sockets:
        use_bc = _use(layer, 'base_color')
        use_ao = _use(layer, 'ao') and ('ao' in v_keys)

        # Always call ch() so mute/unmute runs on channel nodes
        bc_sock = ch('base_color', cc=True)
        ao_sock = ch('ao') if 'ao' in v_keys else None

        ao_mix_node = _by_lbl(nt, _nl(li,'AO_MIX'))

        if not use_bc:
            # Mute base color nodes, AO nodes AND AO_MIX
            if ao_mix_node: ao_mix_node.mute = True
        elif not use_ao:
            # Base color on, AO off: mute AO_MIX, connect base color directly
            if ao_mix_node: ao_mix_node.mute = True
            if bc_sock:
                _connect(nt, bsdf, 'base_color', sockets, bc_sock)
        else:
            # Both on
            if bc_sock:
                final_bc = bc_sock
                if stype == 'PRINCIPLED' and ao_sock:
                    ao_mix_node2 = _ensure(nt, 'ShaderNodeMixRGB', _nl(li,'AO_MIX'), X_AO, y_base)
                    ao_mix_node2.mute = False
                    ao_mix_node2.blend_type = 'MULTIPLY'
                    ao_mix_node2.inputs['Fac'].default_value = layer.ao_strength
                    _link(nt, final_bc, ao_mix_node2.inputs['Color1'])
                    _link(nt, ao_sock,  ao_mix_node2.inputs['Color2'])
                    final_bc = ao_mix_node2.outputs['Color']
                elif ao_mix_node:
                    ao_mix_node.mute = False
                _connect(nt, bsdf, 'base_color', sockets, final_bc)

    if 'roughness' in v_keys and 'roughness' in sockets:
        r_sock = ch('roughness')
        if r_sock:
            if layer.roughness_bias != 0.0:
                rb = _ensure(nt, 'ShaderNodeMath', _nl(li,'ROUGH_BIAS'), X_MID, y_cur[0]+STEP)
                rb.operation = 'ADD'; rb.inputs[1].default_value = layer.roughness_bias
                _link(nt, r_sock, rb.inputs[0])
                _connect(nt, bsdf, 'roughness', sockets, rb.outputs['Value'])
            else:
                _connect(nt, bsdf, 'roughness', sockets, r_sock)
        elif 'glossiness' in v_keys:
            g_sock = ch('glossiness')
            if g_sock:
                inv = _ensure(nt, 'ShaderNodeInvert', _nl(li,'GLOSS_INV'), X_MID, y_cur[0]+STEP)
                _link(nt, g_sock, inv.inputs['Color'])
                _connect(nt, bsdf, 'roughness', sockets, inv.outputs['Color'])
        # else: no roughness map, leave socket at default value

    skip_in_simple = {'base_color','roughness','glossiness','ao','normal','bump',
                      'coat_normal','emission','displacement'}
    if stype == 'SSS':
        skip_in_simple |= {'sss_scale','sss_anisotropy','sss_ior','anisotropic'}
    simple_keys = [k for k in v_keys if k not in skip_in_simple]
    for key in simple_keys:
        if key not in sockets: continue
        sock = ch(key)
        if sock:
            _connect(nt, bsdf, key, sockets, sock)
        # else: nodes muted, wire stays, no action needed

    nor_target = sockets.get('normal') or sockets.get('bump')
    if nor_target:
        nbm = getattr(layer, 'normal_bump_mode', 'NORMAL')
        has_normal = 'normal' in v_keys
        has_bump   = 'bump'   in v_keys

        n_sock = ch('normal') if has_normal else None  # always call so mute runs
        b_sock = ch('bump')   if has_bump   else None  # always call so mute runs

        use_normal = bool(n_sock) and nbm in ('NORMAL', 'BOTH')
        use_bump   = bool(b_sock) and nbm in ('BUMP',   'BOTH')

        if use_normal:
            if getattr(layer, 'normal_dx', False):
                sep_n = _ensure(nt, 'ShaderNodeSeparateColor', _nl(li,'NOR_SEP'), X_MID - 440, y_cur[0]+STEP)
                inv_g = _ensure(nt, 'ShaderNodeMath',          _nl(li,'NOR_INVG'), X_MID - 220, y_cur[0]+STEP)
                inv_g.operation = 'SUBTRACT'
                inv_g.inputs[0].default_value = 1.0
                cmb_n = _ensure(nt, 'ShaderNodeCombineColor',  _nl(li,'NOR_CMB'), X_MID - 10, y_cur[0]+STEP)
                _link(nt, n_sock, sep_n.inputs['Color'])
                _link(nt, sep_n.outputs['Red'],   cmb_n.inputs['Red'])
                _link(nt, sep_n.outputs['Green'], inv_g.inputs[1])
                _link(nt, inv_g.outputs['Value'], cmb_n.inputs['Green'])
                _link(nt, sep_n.outputs['Blue'],  cmb_n.inputs['Blue'])
                n_sock = cmb_n.outputs['Color']
            else:
                for lbl in (_nl(li,'NOR_SEP'), _nl(li,'NOR_INVG'), _nl(li,'NOR_CMB')):
                    nd = _by_lbl(nt, lbl); 
                    if nd: nt.nodes.remove(nd)
            nm = _ensure(nt, 'ShaderNodeNormalMap', _nl(li,'NMAP'), X_MID, y_cur[0]+STEP)
            nm.inputs['Strength'].default_value = layer.normal_strength
            _link(nt, n_sock, nm.inputs['Color'])
            if use_bump:
                # BOTH: chain bump after normal map
                bm = _ensure(nt, 'ShaderNodeBump', _nl(li,'BUMP_N'), X_MID + 220, y_cur[0]+STEP)
                bm.inputs['Strength'].default_value = layer.bump_strength
                _link(nt, b_sock, bm.inputs['Height'])
                _link(nt, nm.outputs['Normal'], bm.inputs['Normal'])
                _connect(nt, bsdf, 'normal', sockets, bm.outputs['Normal'])
            else:
                _connect(nt, bsdf, 'normal', sockets, nm.outputs['Normal'])
                n = _by_lbl(nt, _nl(li,'BUMP_N'))
                if n: nt.nodes.remove(n)
        elif use_bump:
            bm = _ensure(nt, 'ShaderNodeBump', _nl(li,'BUMP_N'), X_MID, y_cur[0]+STEP)
            bm.inputs['Strength'].default_value = layer.bump_strength
            _link(nt, b_sock, bm.inputs['Height'])
            _connect(nt, bsdf, 'bump', sockets, bm.outputs['Normal'])
            for lbl in (_nl(li,'NMAP'), _nl(li,'NOR_SEP'), _nl(li,'NOR_INVG'), _nl(li,'NOR_CMB')):
                nd = _by_lbl(nt, lbl)
                if nd: nt.nodes.remove(nd)

    if 'coat_normal' in v_keys and 'coat_normal' in sockets:
        cn_sock = ch('coat_normal')
        if cn_sock:
            cnm = _ensure(nt, 'ShaderNodeNormalMap', _nl(li,'COAT_NMAP'), X_MID, y_cur[0]+STEP)
            cnm.inputs['Strength'].default_value = layer.normal_strength
            _link(nt, cn_sock, cnm.inputs['Color'])
            _connect(nt, bsdf, 'coat_normal', sockets, cnm.outputs['Normal'])

    if 'emission' in v_keys and 'emission' in sockets:
        e_sock = ch('emission')
        if e_sock:
            _connect(nt, bsdf, 'emission', sockets, e_sock)
        if bsdf_new:
            try: bsdf.inputs['Emission Strength'].default_value = layer.emission_strength
            except Exception: pass

    if bsdf_new:
        if stype == 'EMISSION':
            try: bsdf.inputs['Strength'].default_value = layer.emission_strength
            except Exception: pass
        if stype == 'SSS':
            try: bsdf.inputs['Scale'].default_value = layer.val_sss_scale
            except Exception: pass
            try: bsdf.inputs['IOR'].default_value = layer.val_sss_ior
            except Exception: pass
            try: bsdf.inputs['Anisotropy'].default_value = layer.val_sss_anisotropy
            except Exception: pass
            try: bsdf.inputs['Roughness'].default_value = layer.val_roughness
            except Exception: pass
        if stype == 'GLASS':
            try: bsdf.inputs['IOR'].default_value = layer.val_ior
            except Exception: pass
            try: bsdf.inputs['Roughness'].default_value = layer.val_roughness
            except Exception: pass
            try: bsdf.inputs['Thin Film Thickness'].default_value = layer.val_thin_film_thick
            except Exception: pass
            try: bsdf.inputs['Thin Film IOR'].default_value = layer.val_thin_film_ior
            except Exception: pass
        if stype == 'DIFFUSE':
            try: bsdf.inputs['Roughness'].default_value = layer.val_roughness
            except Exception: pass

    # Distribution/method are node properties, not socket values — safe to set always
    if stype == 'SSS':
        try: bsdf.subsurface_method = layer.sss_method
        except Exception: pass
    if stype == 'PRINCIPLED':
        try: bsdf.distribution = layer.specular_distribution
        except Exception: pass
        try: bsdf.subsurface_method = layer.sss_method
        except Exception: pass

    orm_path = getattr(layer, 'orm_path', '').strip()
    if orm_path:
        orm_abs = bpy.path.abspath(orm_path)
        if os.path.isfile(orm_abs):
            orm_tex = _ensure(nt, 'ShaderNodeTexImage',      _nl(li,'ORM_TEX'), X_TEX, y_base - 600)
            orm_sep = _ensure(nt, 'ShaderNodeSeparateColor', _nl(li,'ORM_SEP'), X_TEX + 240, y_base - 600)
            orm_img = _load_img(orm_abs, 'Non-Color')
            if orm_img: orm_tex.image = orm_img
            _link(nt, mapp.outputs['Vector'], orm_tex.inputs['Vector'])
            _link(nt, orm_tex.outputs['Color'], orm_sep.inputs['Color'])

            layout_key = getattr(layer, 'orm_layout', 'AO_ROUGH_MET')
            ch_r, ch_g, ch_b = ORM_LAYOUT_MAP.get(layout_key, ('ao', 'roughness', 'metallic'))
            ch_names = {'Red': ch_r, 'Green': ch_g, 'Blue': ch_b}

            for ch_name, map_key in ch_names.items():
                if map_key == 'ao':
                    if not _has_img(layer, 'ao'):
                        ao_mix = _by_lbl(nt, _nl(li,'AO_MIX'))
                        if ao_mix is None:
                            ao_mix = _ensure(nt, 'ShaderNodeMixRGB', _nl(li,'AO_MIX'), X_AO, y_base)
                            ao_mix.blend_type = 'MULTIPLY'
                            ao_mix.inputs['Fac'].default_value = layer.ao_strength
                            bc_s = _sock(bsdf, sockets.get('base_color', ''))
                            if bc_s and bc_s.is_linked:
                                src = bc_s.links[0].from_socket
                                _link(nt, src, ao_mix.inputs['Color1'])
                                _link(nt, ao_mix.outputs['Color'], bc_s)
                        _link(nt, orm_sep.outputs[ch_name], ao_mix.inputs['Color2'])
                else:
                    if not _has_img(layer, map_key):
                        s = _sock(bsdf, sockets.get(map_key, ''))
                        if s:
                            try: _link(nt, orm_sep.outputs[ch_name], s)
                            except Exception: pass
        else:
            for lbl in (_nl(li,'ORM_TEX'), _nl(li,'ORM_SEP')):
                n = _by_lbl(nt, lbl)
                if n: nt.nodes.remove(n)
    else:
        for lbl in (_nl(li,'ORM_TEX'), _nl(li,'ORM_SEP')):
            n = _by_lbl(nt, lbl)
            if n: nt.nodes.remove(n)

    return bsdf


# ══════════════════════════════════════════════════════════════════════════════
# FULL NETWORK BUILD
# ══════════════════════════════════════════════════════════════════════════════

def _arrange_nodes(nt):
    try:
        for n in nt.nodes:
            n.select = True
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'NODE_EDITOR':
                    for space in area.spaces:
                        if getattr(space, 'tree_type', '') == 'ShaderNodeTree':
                            try:
                                with bpy.context.temp_override(
                                    screen=screen, area=area,
                                    space_data=space, region=area.regions[-1]):
                                    bpy.ops.node.view_all()
                            except Exception:
                                pass
    except Exception:
        pass
    finally:
        for n in nt.nodes:
            n.select = False


def build_network(mat):
    if not mat: return
    props = mat.pbr_props
    if not props.layers: return
    mat.use_nodes = True
    nt = mat.node_tree

    active = [l for l in props.layers if l.enabled]
    if not active: return

    out = _by_lbl(nt, 'PBR_OUTPUT')
    if out is None:
        out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if out: out.label = 'PBR_OUTPUT'
        else:
            out = nt.nodes.new('ShaderNodeOutputMaterial'); out.label = 'PBR_OUTPUT'
    out.location = (1400, 300)

    Y_STEP = 3200
    bsdfs  = []
    for idx, layer in enumerate(active):
        bsdf = _build_layer(nt, layer, idx, -(idx * Y_STEP))
        bsdfs.append((idx, layer, bsdf))

    base = active[0]
    base_mapp = _by_lbl(nt, _nl(0,'MAPP'))
    base_uv   = _by_lbl(nt, _nl(0,'UV'))
    if base_mapp and base_uv and (_has_img(base,'displacement') or _has_extras(base,'displacement')):
        d_sock = _build_channel(nt, base, 0, 'displacement', base_mapp, base_uv, -880, -2400)
        if d_sock:
            dn = _ensure(nt, 'ShaderNodeDisplacement', 'PBR_DISP', 800, -300)
            dn.inputs['Scale'].default_value    = base.disp_scale
            dn.inputs['Midlevel'].default_value = base.disp_midlevel
            _link(nt, d_sock, dn.inputs['Height'])
            _link(nt, dn.outputs['Displacement'], out.inputs['Displacement'])
            try: mat.cycles.displacement_method = 'BOTH'
            except AttributeError: pass
    else:
        n = _by_lbl(nt, 'PBR_DISP')
        if n: nt.nodes.remove(n)

    has_opacity = any(_has_img(l,'opacity') or _has_extras(l,'opacity') for l in active)
    mat.blend_method = 'CLIP' if has_opacity else 'OPAQUE'
    if hasattr(mat, 'shadow_method'):
        mat.shadow_method = 'CLIP' if has_opacity else 'OPAQUE'

    solo_idx = getattr(props, 'solo_layer', -1)
    if solo_idx >= 0:
        all_layers = list(props.layers)
        solo_active = None
        for idx, layer in enumerate(active):
            orig_idx = next((i for i, l in enumerate(all_layers) if l == layer), -1)
            if orig_idx == solo_idx:
                solo_active = (idx, layer, bsdfs[idx][2])
                break
        if solo_active:
            _link(nt, _bsdf_out(solo_active[2], solo_active[1].shader_type), out.inputs['Surface'])
            return

    _purge(nt, 'LMIX_')
    if len(bsdfs) == 1:
        _link(nt, _bsdf_out(bsdfs[0][2], active[0].shader_type), out.inputs['Surface'])
        return

    prev = _bsdf_out(bsdfs[0][2], active[0].shader_type)
    for si in range(1, len(bsdfs)):
        li, layer, bsdf = bsdfs[si]
        y_base = -(li * Y_STEP)
        mix = _ensure(nt, 'ShaderNodeMixShader', f"LMIX_{si}", 900, 300 - (si-1)*200)
        _link(nt, prev, mix.inputs[1])
        _link(nt, _bsdf_out(bsdf, layer.shader_type), mix.inputs[2])

        uv_node = _by_lbl(nt, _nl(li,'UV'))
        fac = _build_mask(nt, layer.mask_path, layer.mask_invert,
                          layer.mask_min, layer.mask_max,
                          layer.mask_tiling_x, layer.mask_tiling_y, layer.mask_tiling_lock,
                          layer.mask_offset_x, layer.mask_offset_y, layer.mask_rotation,
                          uv_node, f"LMASK_{li}", -1500, y_base - 300,
                          mask_type=layer.mask_type, proc_props=layer,
                          udim=getattr(layer, 'mask_udim', False)) if uv_node else None
        if fac:
            str_n = _ensure(nt, 'ShaderNodeMath', f"LMASK_{li}_STR", -1200, y_base-300)
            str_n.operation = 'MULTIPLY'
            str_n.inputs[1].default_value = layer.mask_strength
            _link(nt, fac, str_n.inputs[0])
            _link(nt, str_n.outputs['Value'], mix.inputs['Fac'])
        else:
            mix.inputs['Fac'].default_value = layer.mask_strength
        prev = mix.outputs['Shader']

    _link(nt, prev, out.inputs['Surface'])


# ══════════════════════════════════════════════════════════════════════════════
# OPERATORS
# ══════════════════════════════════════════════════════════════════════════════

class PBR_OT_CreateMaterial(Operator):
    bl_idname = "pbr_ld.create_material"; bl_label = "New PBR Material"
    bl_description = "Create a new named material"; bl_options = {'REGISTER','UNDO'}
    mat_name: StringProperty(name="Name", default="PBR_Material")
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    def draw(self, context): self.layout.prop(self, "mat_name", text="Name")
    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Select a mesh first."); return {'CANCELLED'}
        mat = bpy.data.materials.new(name=self.mat_name)
        mat.use_nodes = True
        if obj.data.materials: obj.data.materials[0] = mat
        else: obj.data.materials.append(mat)
        obj.active_material_index = 0
        mat.pbr_props.layers.add().name = "Base Layer"
        self.report({'INFO'}, f"Created '{mat.name}'."); return {'FINISHED'}


class PBR_OT_AddLayer(Operator):
    bl_idname = "pbr_ld.add_layer"; bl_label = "Add Layer"
    bl_description = "Add a new shader layer"; bl_options = {'REGISTER','UNDO'}
    shader_type: EnumProperty(name="Shader", items=SHADER_ITEMS, default='PRINCIPLED')
    layer_name:  StringProperty(name="Name", default="")
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(self, "shader_type"); col.prop(self, "layer_name")
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        layer = mat.pbr_props.layers.add()
        layer.shader_type = self.shader_type
        layer.name = self.layer_name.strip() or f"Layer {len(mat.pbr_props.layers)}"
        mat.pbr_props.active_layer_index = len(mat.pbr_props.layers) - 1
        if mat.pbr_props.is_built: build_network(mat)
        return {'FINISHED'}


class PBR_OT_RemoveLayer(Operator):
    bl_idname = "pbr_ld.remove_layer"; bl_label = "Remove Layer"
    bl_options = {'REGISTER','UNDO'}
    layer_index: IntProperty()
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        props = mat.pbr_props
        if len(props.layers) <= 1:
            self.report({'WARNING'}, "Cannot remove last layer."); return {'CANCELLED'}
        if mat.use_nodes: _purge(mat.node_tree, f"L{self.layer_index}_")
        props.layers.remove(self.layer_index)
        props.active_layer_index = max(0, min(props.active_layer_index, len(props.layers)-1))
        if props.is_built: build_network(mat)
        return {'FINISHED'}


class PBR_OT_MoveLayer(Operator):
    bl_idname = "pbr_ld.move_layer"; bl_label = "Move Layer"
    bl_options = {'REGISTER','UNDO'}
    layer_index: IntProperty()
    direction: EnumProperty(items=[('UP','Up',''),('DOWN','Down','')])
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        props = mat.pbr_props; i = self.layer_index
        if self.direction == 'UP' and i > 0:
            props.layers.move(i, i-1); props.active_layer_index = i-1
        elif self.direction == 'DOWN' and i < len(props.layers)-1:
            props.layers.move(i, i+1); props.active_layer_index = i+1
        else:
            return {'FINISHED'}
        if props.is_built and mat.use_nodes:
            nt = mat.node_tree
            for n in [x for x in nt.nodes if x.label and x.label[:1] == 'L'
                      and '_' in x.label and x.label.split('_')[0][1:].isdigit()]:
                nt.nodes.remove(n)
            _purge(nt, 'LMIX_')
            _purge(nt, 'LMASK_')
            _purge(nt, 'PBR_DISP')
            build_network(mat)
        return {'FINISHED'}


class PBR_OT_ScanLayer(Operator):
    bl_idname = "pbr_ld.scan_layer"; bl_label = "Scan Folder"
    bl_options = {'REGISTER','UNDO'}
    layer_index: IntProperty()
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        layer = mat.pbr_props.layers[self.layer_index]
        d = bpy.path.abspath(layer.scan_dir_path.strip())
        if not os.path.isdir(d):
            self.report({'WARNING'}, "Set a valid folder."); return {'CANCELLED'}
        kw = layer.scan_filter.strip() or None
        found, orm_path = scan_dir(d, keyword=kw)
        for k, fp in found.items(): setattr(layer, f"path_{k}", fp)
        if orm_path:
            layer.orm_path = orm_path
        msg = f"Found {len(found)} maps"
        if kw: msg += f" (filter: '{kw}')"
        if orm_path: msg += " + ORM"
        msg += " — click Build."
        self.report({'INFO'}, msg); return {'FINISHED'}


class PBR_OT_DetectParts(Operator):
    """Scan folder and show detected part names as a selection popup."""
    bl_idname = "pbr_ld.detect_parts"; bl_label = "Detect Parts"
    bl_description = "Detect part names in folder (e.g. Hair, Body, Face) and select one as scan filter"
    bl_options = {'REGISTER'}
    layer_index: IntProperty()

    def invoke(self, context, event):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        layer = mat.pbr_props.layers[self.layer_index]
        d = bpy.path.abspath(layer.scan_dir_path.strip())
        if not os.path.isdir(d):
            self.report({'WARNING'}, "Set a valid folder first."); return {'CANCELLED'}
        self._parts = detect_part_names(d)
        if not self._parts:
            self.report({'INFO'}, "No distinct part names found in folder.")
            return {'CANCELLED'}
        context.window_manager.popup_menu(self._draw_menu,
                                          title="Select Part Filter", icon='FILTER')
        return {'FINISHED'}

    def _draw_menu(self, menu, context):
        layout = menu.layout
        mat = _active_mat(context)
        if not mat: return
        layer = mat.pbr_props.layers[self.layer_index]
        cur = layer.scan_filter.lower().strip()
        # "All" option to clear filter
        op = layout.operator("pbr_ld.apply_part_filter", text="— All (no filter) —",
                             icon='RADIOBUT_ON' if cur == '' else 'RADIOBUT_OFF')
        op.layer_index = self.layer_index; op.part_name = ''
        layout.separator()
        for p in self._parts:
            op = layout.operator("pbr_ld.apply_part_filter", text=p.replace('_',' ').title(),
                                 icon='RADIOBUT_ON' if p == cur else 'RADIOBUT_OFF')
            op.layer_index = self.layer_index; op.part_name = p

    def execute(self, context):
        return {'FINISHED'}


class PBR_OT_ApplyPartFilter(Operator):
    """Apply a part name as the scan filter."""
    bl_idname = "pbr_ld.apply_part_filter"; bl_label = "Apply Part Filter"
    bl_options = {'REGISTER', 'UNDO'}
    layer_index: IntProperty()
    part_name:   StringProperty()

    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        mat.pbr_props.layers[self.layer_index].scan_filter = self.part_name
        return {'FINISHED'}


class PBR_OT_ClearLayer(Operator):
    bl_idname = "pbr_ld.clear_layer"; bl_label = "Clear Layer"
    bl_options = {'REGISTER','UNDO'}
    layer_index: IntProperty()
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        layer = mat.pbr_props.layers[self.layer_index]
        for k in MAP_KEYS: setattr(layer, f"path_{k}", '')
        layer.mask_path = ''
        layer.orm_path = ''
        if mat.pbr_props.is_built:
            _purge(mat.node_tree, f"L{self.layer_index}_"); build_network(mat)
        return {'FINISHED'}


class PBR_OT_AddOverlay(Operator):
    bl_idname = "pbr_ld.add_overlay"; bl_label = "Add Overlay"
    bl_description = "Add an image overlay with blend mask for this channel"
    bl_options = {'REGISTER','UNDO'}
    layer_index: IntProperty()
    map_key:     StringProperty()
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        layer = mat.pbr_props.layers[self.layer_index]
        getattr(layer, f"extra_{self.map_key}").add()
        return {'FINISHED'}


class PBR_OT_RemoveOverlay(Operator):
    bl_idname = "pbr_ld.remove_overlay"; bl_label = "Remove Overlay"
    bl_options = {'REGISTER','UNDO'}
    layer_index:   IntProperty()
    map_key:       StringProperty()
    overlay_index: IntProperty()
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        layer = mat.pbr_props.layers[self.layer_index]
        getattr(layer, f"extra_{self.map_key}").remove(self.overlay_index)
        if mat.pbr_props.is_built: build_network(mat)
        return {'FINISHED'}


class PBR_OT_MoveOverlay(Operator):
    bl_idname = "pbr_ld.move_overlay"; bl_label = "Move Overlay"
    bl_options = {'REGISTER','UNDO'}
    layer_index:   IntProperty()
    map_key:       StringProperty()
    overlay_index: IntProperty()
    direction:     EnumProperty(items=[('UP','Up',''),('DOWN','Down','')])
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        layer = mat.pbr_props.layers[self.layer_index]
        col = getattr(layer, f"extra_{self.map_key}", None)
        if col is None: return {'CANCELLED'}
        i = self.overlay_index
        if self.direction == 'UP' and i > 0:
            col.move(i, i-1)
        elif self.direction == 'DOWN' and i < len(col)-1:
            col.move(i, i+1)
        if mat.pbr_props.is_built: build_network(mat)
        return {'FINISHED'}


class PBR_OT_CopyLayer(Operator):
    bl_idname = "pbr_ld.copy_layer"; bl_label = "Duplicate Layer"
    bl_description = "Duplicate this shader layer with all its settings"
    bl_options = {'REGISTER','UNDO'}
    layer_index: IntProperty()
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        props = mat.pbr_props
        if self.layer_index >= len(props.layers): return {'CANCELLED'}
        src_layer = props.layers[self.layer_index]
        new_layer = props.layers.add()
        skip = {'rna_type'}
        for prop in src_layer.bl_rna.properties:
            if prop.identifier in skip or prop.identifier.startswith('extra_'):
                continue
            try:
                setattr(new_layer, prop.identifier, getattr(src_layer, prop.identifier))
            except Exception:
                pass
        new_layer.name = src_layer.name + " Copy"
        target_idx = self.layer_index + 1
        props.layers.move(len(props.layers)-1, target_idx)
        props.active_layer_index = target_idx
        if props.is_built: build_network(mat)
        return {'FINISHED'}


class PBR_OT_SetTiling(Operator):
    bl_idname = "pbr_ld.set_tiling"; bl_label = "Set Tiling"
    bl_description = "Set tiling to a preset value"
    bl_options = {'REGISTER','UNDO'}
    layer_index: IntProperty()
    value: bpy.props.FloatProperty(default=1.0)
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        layer = mat.pbr_props.layers[self.layer_index]
        layer.tiling_x = self.value
        layer.tiling_y = self.value
        layer.tiling_z = self.value
        if mat.pbr_props.is_built: build_network(mat)
        return {'FINISHED'}


class PBR_OT_CollapseAll(Operator):
    bl_idname = "pbr_ld.collapse_all"; bl_label = "Collapse All"
    bl_description = "Collapse every layer, map group and overlay"
    bl_options = {'REGISTER','UNDO'}
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        wm = context.window_manager
        try:
            d = json.loads(getattr(wm, 'pbr_ui_state', '{}'))
            mn = mat.name
            # Remove all keys for this material
            keys_to_remove = [k for k in d if k.startswith(mn + '|')]
            for k in keys_to_remove:
                del d[k]
            # Explicitly collapse all layer accordions and channel tabs
            for li in range(len(mat.pbr_props.layers)):
                d[_ui_key(mn, li, 'exp')]        = False
                d[_ui_key(mn, li, 'ch_open')]    = False
                # close all map groups
                for grp_key, *_ in MAP_GROUPS:
                    d[_ui_key(mn, li, 'mgrp', grp_key)] = False
                d[_ui_key(mn, li, 'mgrp', 'orm')] = False
            wm.pbr_ui_state = json.dumps(d)
        except Exception:
            wm.pbr_ui_state = '{}'
        for area in context.screen.areas: area.tag_redraw()
        return {'FINISHED'}


class PBR_OT_BatchScanFolders(Operator):
    bl_idname = "pbr_ld.batch_scan"; bl_label = "Batch Scan Subfolders"
    bl_description = "Scan all subfolders and create a layer per texture set found"
    bl_options = {'REGISTER','UNDO'}
    layer_index: IntProperty()
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        layer = mat.pbr_props.layers[self.layer_index]
        root = bpy.path.abspath(layer.scan_dir_path.strip())
        if not os.path.isdir(root):
            self.report({'WARNING'}, "Set a valid folder first."); return {'CANCELLED'}
        subdirs = [os.path.join(root, d) for d in os.listdir(root)
                   if os.path.isdir(os.path.join(root, d))]
        if not subdirs:
            self.report({'WARNING'}, "No subfolders found — use Scan for flat folders."); return {'CANCELLED'}
        props = mat.pbr_props
        added = 0
        for sd in sorted(subdirs):
            found, orm_path = scan_dir(sd)
            if not found and not orm_path: continue
            new_layer = props.layers.add()
            new_layer.name = os.path.basename(sd)
            new_layer.scan_dir_path = sd
            for k, fp in found.items(): setattr(new_layer, f"path_{k}", fp)
            if orm_path: new_layer.orm_path = orm_path
            added += 1
        if props.is_built: build_network(mat)
        self.report({'INFO'}, f"Added {added} layer(s) from subfolders."); return {'FINISHED'}


class PBR_OT_PickColorSpace(Operator):
    bl_idname  = "pbr_ld.pick_colorspace"
    bl_label   = "Color Space"
    bl_description = "Choose color space for this texture slot"
    bl_options = {'REGISTER', 'UNDO'}
    layer_index:   IntProperty()
    map_key:       StringProperty()
    overlay_index: IntProperty(default=-1)

    def _cs_list(self):
        try:
            items = bpy.types.ColorManagedInputColorspaceSettings.bl_rna.properties['name'].enum_items
            return [s.identifier for s in items]
        except Exception:
            return [
                'sRGB', 'Non-Color', 'Linear Rec.709', 'Linear',
                'Linear ACES', 'Linear ACEScg', 'ACEScg', 'ACES2065-1',
                'AgX Base sRGB', 'AgX Base Rec.2020', 'AgX Base Display P3',
                'Filmic Log', 'Filmic sRGB', 'Raw', 'XYZ',
            ]

    def invoke(self, context, event):
        context.window_manager.popup_menu(self._draw_menu, title="Color Space", icon='COLOR')
        return {'FINISHED'}

    def _draw_menu(self, menu, context):
        layout = menu.layout
        mat = _active_mat(context)
        if not mat: return
        layer = mat.pbr_props.layers[self.layer_index]
        if self.overlay_index >= 0:
            extras = getattr(layer, f"extra_{self.map_key}", [])
            cur = extras[self.overlay_index].img_colorspace if self.overlay_index < len(extras) else ''
        else:
            cur = getattr(layer, f"cs_{self.map_key}", '')
        for cs in self._cs_list():
            row = layout.row(align=True)
            row.active = True
            op = row.operator("pbr_ld.apply_colorspace", text=cs,
                              icon='RADIOBUT_ON' if cs == cur else 'RADIOBUT_OFF')
            op.layer_index   = self.layer_index
            op.map_key       = self.map_key
            op.overlay_index = self.overlay_index
            op.colorspace    = cs

    def execute(self, context):
        return {'FINISHED'}


class PBR_OT_ApplyColorSpace(Operator):
    bl_idname  = "pbr_ld.apply_colorspace"
    bl_label   = "Apply Color Space"
    bl_options = {'REGISTER', 'UNDO'}
    layer_index:   IntProperty()
    map_key:       StringProperty()
    overlay_index: IntProperty(default=-1)
    colorspace:    StringProperty()

    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        layer = mat.pbr_props.layers[self.layer_index]
        cs = self.colorspace
        if self.overlay_index >= 0:
            extras = getattr(layer, f"extra_{self.map_key}", [])
            if self.overlay_index < len(extras):
                extras[self.overlay_index].img_colorspace = cs
                p = bpy.path.abspath(extras[self.overlay_index].path.strip())
                img = bpy.data.images.get(os.path.basename(p)) if p else None
                if img:
                    try: img.colorspace_settings.name = cs
                    except Exception: pass
        else:
            setattr(layer, f"cs_{self.map_key}", cs)
            p = _ppath(layer, self.map_key)
            img = bpy.data.images.get(os.path.basename(p)) if p else None
            if img:
                try: img.colorspace_settings.name = cs
                except Exception: pass
        if mat.pbr_props.is_built:
            build_network(mat)
        return {'FINISHED'}


class PBR_OT_SoloLayer(Operator):
    bl_idname = "pbr_ld.solo_layer"; bl_label = "Solo Layer"
    bl_description = "Preview only this layer (click again to unsolo)"
    bl_options = {'REGISTER', 'UNDO'}
    layer_index: IntProperty()
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        props = mat.pbr_props
        if props.solo_layer == self.layer_index:
            props.solo_layer = -1
        else:
            props.solo_layer = self.layer_index
        if props.is_built:
            build_network(mat)
        return {'FINISHED'}


class PBR_OT_Build(Operator):
    bl_idname = "pbr_ld.build_network"; bl_label = "Build Material"
    bl_description = "Build the full layered shader network"
    bl_options = {'REGISTER','UNDO'}
    @classmethod
    def poll(cls, context):
        mat = _active_mat(context)
        return mat is not None and not mat.pbr_props.is_built
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        build_network(mat); mat.pbr_props.is_built = True
        _arrange_nodes(mat.node_tree)
        self.report({'INFO'}, f"Built {len(mat.pbr_props.layers)} layer(s).")
        return {'FINISHED'}


class PBR_OT_Rebuild(Operator):
    bl_idname = "pbr_ld.rebuild_network"; bl_label = "Rebuild"
    bl_description = "Force full rebuild of the shader network"
    bl_options = {'REGISTER','UNDO'}
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        mat.pbr_props.is_built = False
        build_network(mat); mat.pbr_props.is_built = True
        _arrange_nodes(mat.node_tree)
        self.report({'INFO'}, "Rebuilt."); return {'FINISHED'}


class PBR_OT_ToggleUI(Operator):
    bl_idname = "pbr_ld.toggle_ui"; bl_label = "Toggle UI"
    bl_options = {'INTERNAL'}
    key: StringProperty()
    default: BoolProperty(default=False)
    def execute(self, context):
        cur = _ui_get(context, self.key, default=self.default)
        _ui_set(context, not cur, self.key)
        for area in context.screen.areas: area.tag_redraw()
        return {'FINISHED'}


def _tog(layout, context, label, icon_open, icon_closed, *key_parts, default=False, **kwargs):
    key = _ui_key(*key_parts)
    expanded = _ui_get(context, key, default=default)
    op = layout.operator("pbr_ld.toggle_ui", text=label,
                         icon=icon_open if expanded else icon_closed,
                         emboss=False, **kwargs)
    op.key = key
    op.default = default
    return expanded


# ══════════════════════════════════════════════════════════════════════════════
# PANEL DRAW
# ══════════════════════════════════════════════════════════════════════════════

def _draw_proc_mask_ui(layout, props):
    mtype = getattr(props, 'mask_type', 'NOISE')
    col = layout.column(align=True)
    col.prop(props, 'mask_proc_scale',   slider=True)

    if mtype == 'NOISE':
        col.prop(props, 'mask_proc_detail',     slider=True)
        col.prop(props, 'mask_proc_roughness',  slider=True)
        col.prop(props, 'mask_proc_distortion', slider=True)
    elif mtype == 'WAVE':
        col.prop(props, 'mask_wave_type',    text='Wave')
        col.prop(props, 'mask_wave_profile', text='Profile')
        col.prop(props, 'mask_proc_distortion', slider=True)
        col.prop(props, 'mask_proc_detail',     slider=True)
        col.prop(props, 'mask_proc_roughness',  slider=True)
    elif mtype == 'GRADIENT':
        col.prop(props, 'mask_gradient_type', text='Type')
    elif mtype == 'VORONOI':
        col.prop(props, 'mask_voronoi_feature',  text='Feature')
        col.prop(props, 'mask_voronoi_distance', text='Distance')
        col.prop(props, 'mask_voronoi_random',   slider=True)


def _draw_transform_block(layout, props, prefix="", lock_prop="tiling_lock",
                          tx_prop="tiling_x", ty_prop="tiling_y", tz_prop="tiling_z",
                          ox_prop="offset_x", oy_prop="offset_y", oz_prop="offset_z",
                          rot_prop="rotation", show_z=True, layer_index=None):
    """Shared transform UI block — lock sits in label column so value columns always align."""
    SPLIT = 0.32
    col = layout.column(align=True)

    # Preset buttons — only in main layer mapping
    if layer_index is not None:
        sp = col.split(factor=SPLIT, align=True)
        sp.label(text="Preset:")
        btn = sp.row(align=True)
        for val, lbl in ((0.5,'\u00bd'),(1,'1\xd7'),(2,'2\xd7'),(4,'4\xd7'),(8,'8\xd7')):
            op = btn.operator("pbr_ld.set_tiling", text=lbl)
            op.layer_index = layer_index; op.value = val
        col.separator(factor=0.2)

    lock_val = getattr(props, lock_prop, True)

    # Scale — lock icon sits in the label cell so value cells align with Offset
    sp = col.split(factor=SPLIT, align=True)
    lbl_row = sp.row(align=True)
    lbl_row.prop(props, lock_prop, text="",
                 icon='LOCKED' if lock_val else 'UNLOCKED')
    lbl_row.label(text="Scale:")
    val_row = sp.row(align=True)
    if lock_val:
        val_row.prop(props, tx_prop, text="XYZ")
    else:
        val_row.prop(props, tx_prop, text="X")
        val_row.prop(props, ty_prop, text="Y")
        if show_z:
            val_row.prop(props, tz_prop, text="Z")

    # Offset — value cells align with Scale values above
    sp = col.split(factor=SPLIT, align=True)
    sp.label(text="Offset:")
    val_row = sp.row(align=True)
    val_row.prop(props, ox_prop, text="X")
    val_row.prop(props, oy_prop, text="Y")
    if show_z:
        val_row.prop(props, oz_prop, text="Z")

    # Rotation
    sp = col.split(factor=SPLIT, align=True)
    sp.label(text="Rotation:")
    sp.prop(props, rot_prop, text="")


def _draw_overlay(col, ov, li, key, oi):
    label, icon, _, _ = MAP_INFO[key]
    box = col.box()
    mat_name = ov.id_data.name if hasattr(ov, 'id_data') and ov.id_data else ''

    hdr = box.row(align=True)
    ctx = bpy.context
    ov_expanded = _ui_get(ctx, mat_name, li, key, oi, 'ov', default=True)
    op_ov = hdr.operator("pbr_ld.toggle_ui", text="",
                         icon='TRIA_DOWN' if ov_expanded else 'TRIA_RIGHT', emboss=False)
    op_ov.key = _ui_key(mat_name, li, key, oi, 'ov'); op_ov.default = True
    hdr.prop(ov, "enabled", text="", icon='HIDE_OFF' if ov.enabled else 'HIDE_ON')
    hdr.prop(ov, "name", text="", emboss=True)
    up = hdr.operator("pbr_ld.move_overlay", text="", icon='TRIA_UP', emboss=False)
    up.layer_index = li; up.map_key = key; up.overlay_index = oi; up.direction = 'UP'
    dn = hdr.operator("pbr_ld.move_overlay", text="", icon='TRIA_DOWN', emboss=False)
    dn.layer_index = li; dn.map_key = key; dn.overlay_index = oi; dn.direction = 'DOWN'
    rm = hdr.operator("pbr_ld.remove_overlay", text="", icon='X', emboss=False)
    rm.layer_index = li; rm.map_key = key; rm.overlay_index = oi

    if not ov_expanded:
        return

    inner = box.column(align=False)

    d1 = inner.box()
    r1 = d1.row(align=True)
    cc_expanded = _ui_get(ctx, mat_name, li, key, oi, 'cc', default=False)
    op_cc = r1.operator("pbr_ld.toggle_ui", text="",
                        icon='TRIA_DOWN' if cc_expanded else 'TRIA_RIGHT', emboss=False)
    op_cc.key = _ui_key(mat_name, li, key, oi, 'cc'); op_cc.default = False
    r1.prop(ov, "enabled", text="", icon='HIDE_OFF' if ov.enabled else 'HIDE_ON')
    r1.label(text=f"Layer {oi+1:02d}")

    if cc_expanded:
        c1 = d1.column(align=True)
        pr = c1.row(align=True)
        pr.prop(ov, "path", text="", icon='FILE_IMAGE')
        if hasattr(ov, 'udim'):
            pr.prop(ov, "udim", text="",
                    icon='LIBRARY_DATA_DIRECT' if ov.udim else 'LIBRARY_DATA_OVERRIDE')
        if ov.path.strip():
            cur_cs = getattr(ov, 'img_colorspace', 'sRGB')
            cs_row = c1.row(align=True)
            op = cs_row.operator("pbr_ld.pick_colorspace", text=cur_cs, icon='COLOR')
            op.layer_index = li; op.map_key = key; op.overlay_index = oi
        bs = c1.row(align=True)
        bs.prop(ov, "blend_mode", text="")
        bs.prop(ov, "strength", text="Strength", slider=True)
        if key in GRAYSCALE_KEYS and ov.path.strip():
            rng = c1.row(align=True)
            rng.label(text="Range:")
            rng.prop(ov, "img_min", text="Min", slider=True)
            rng.prop(ov, "img_max", text="Max", slider=True)
        c1.separator(factor=0.3)
        c1.label(text="Color Correction", icon='COLOR')
        cc = c1.column(align=True)
        cc.prop(ov, "hue",        slider=True)
        cc.prop(ov, "saturation", slider=True)
        cc.prop(ov, "value",      slider=True)
        cc.prop(ov, "contrast",   slider=True)
        cc.prop(ov, "gamma",      slider=True)
        c1.separator(factor=0.3)
        c1.prop(ov, "img_use_own_mapping", text="Override Mapping", icon='DRIVER_TRANSFORM')
        if ov.img_use_own_mapping:
            sp = c1.split(factor=0.32, align=True); sp.label(text="Coordinate:"); sp.prop(ov, "img_tex_coord",  text="")
            sp = c1.split(factor=0.32, align=True); sp.label(text="Projection:");  sp.prop(ov, "img_projection", text="")
            if ov.img_projection == 'BOX':
                sp = c1.split(factor=0.32, align=True); sp.label(text="Blend:"); sp.prop(ov, "img_projection_blend", text="", slider=True)
            c1.separator(factor=0.2)
            _draw_transform_block(c1, ov,
                                  lock_prop="img_tiling_lock",
                                  tx_prop="img_tiling_x", ty_prop="img_tiling_y",
                                  ox_prop="img_offset_x", oy_prop="img_offset_y",
                                  rot_prop="img_rotation", show_z=False)

    d2 = inner.box()
    r2 = d2.row(align=True)
    msk_expanded = _ui_get(ctx, mat_name, li, key, oi, 'msk', default=False)
    op_msk = r2.operator("pbr_ld.toggle_ui", text="",
                         icon='TRIA_DOWN' if msk_expanded else 'TRIA_RIGHT', emboss=False)
    op_msk.key = _ui_key(mat_name, li, key, oi, 'msk'); op_msk.default = False
    r2.label(text="Mask", icon='IMAGE_ALPHA')

    if msk_expanded:
        ms = d2.column(align=True)
        ms.prop(ov, "mask_type", text="")
        if ov.mask_type == 'IMAGE':
            mr = ms.row(align=True)
            mr.prop(ov, "mask_path", text="", icon='FILE_IMAGE')
            if hasattr(ov, 'mask_udim'):
                mr.prop(ov, "mask_udim", text="",
                        icon='LIBRARY_DATA_DIRECT' if ov.mask_udim else 'LIBRARY_DATA_OVERRIDE')
        else:
            _draw_proc_mask_ui(ms, ov)
        ms.prop(ov, "mask_invert")
        rng = ms.row(align=True)
        rng.prop(ov, "mask_min", text="Min", slider=True)
        rng.prop(ov, "mask_max", text="Max", slider=True)
        ms.separator(factor=0.3)
        ms.prop(ov, "mask_use_own_mapping", text="Mapping", icon='DRIVER_TRANSFORM')
        if getattr(ov, 'mask_use_own_mapping', False):
            sp = ms.split(factor=0.32, align=True); sp.label(text="Coordinate:"); sp.prop(ov, "mask_tex_coord",  text="")
            sp = ms.split(factor=0.32, align=True); sp.label(text="Projection:");  sp.prop(ov, "mask_projection", text="")
            if ov.mask_projection == 'BOX':
                sp = ms.split(factor=0.32, align=True); sp.label(text="Blend:"); sp.prop(ov, "mask_projection_blend", text="", slider=True)
            ms.separator(factor=0.2)
            _draw_transform_block(ms, ov,
                                  lock_prop="mask_tiling_lock",
                                  tx_prop="mask_tiling_x", ty_prop="mask_tiling_y",
                                  ox_prop="mask_offset_x", oy_prop="mask_offset_y",
                                  rot_prop="mask_rotation", show_z=False)


def _draw_map_slot(col, layer, li, key, detail=True):
    label, icon, cs, vtype = MAP_INFO[key]
    primary  = getattr(layer, f"path_{key}", '').strip()
    use_key  = f"use_{key}"
    use_val  = getattr(layer, use_key, True)
    abs_p    = bpy.path.abspath(primary) if primary else ''
    ok       = bool(primary and os.path.isfile(abs_p))
    miss     = bool(primary and not ok)
    extras   = getattr(layer, f"extra_{key}", [])
    has_any  = bool(primary) or any(e.path.strip() for e in extras)

    orm_active = False
    orm_path = getattr(layer, 'orm_path', '').strip()
    if orm_path and not ok:
        layout_key = getattr(layer, 'orm_layout', 'AO_ROUGH_MET')
        orm_maps = set(ORM_LAYOUT_MAP.get(layout_key, ('ao', 'roughness', 'metallic')))
        orm_active = key in orm_maps

    slot_box = col.box()

    r1 = slot_box.row(align=True)
    r1.prop(layer, use_key, text="",
            icon='HIDE_OFF' if use_val else 'HIDE_ON', emboss=False)
    if orm_active or ok:
        r1.label(text="", icon='COLORSET_03_VEC')  # green
    elif miss:
        r1.label(text="", icon='COLORSET_01_VEC')  # red
    else:
        r1.label(text="", icon='RADIOBUT_OFF')      # grey
    r1.label(text=label, icon=icon)
    if orm_active:
        r1.label(text="", icon='PLUGIN')

    r2 = slot_box.row(align=True)
    r2.prop(layer, f"path_{key}", text="", icon='FILE_IMAGE')
    if hasattr(layer, f'udim_{key}'):
        r2.prop(layer, f"udim_{key}", text="",
                icon='LIBRARY_DATA_DIRECT' if getattr(layer, f'udim_{key}', False) else 'LIBRARY_DATA_OVERRIDE')
    add = r2.operator("pbr_ld.add_overlay", text="", icon='ADD')
    add.layer_index = li; add.map_key = key

    if primary:
        cur_cs = getattr(layer, f'cs_{key}', _MAP_DEFAULT_CS.get(key, 'Non-Color'))
        cs_row = slot_box.row(align=True)
        op = cs_row.operator("pbr_ld.pick_colorspace", text=cur_cs, icon='COLOR')
        op.layer_index = li; op.map_key = key; op.overlay_index = -1

    SPLIT = 0.3

    if ok and key in GRAYSCALE_KEYS:
        sp = slot_box.split(factor=SPLIT, align=True)
        sp.label(text="Range:")
        rv = sp.row(align=True)
        rv.prop(layer, f"min_{key}", text="Min", slider=True)
        rv.prop(layer, f"max_{key}", text="Max", slider=True)

    if not has_any and vtype != 'NONE' and use_val:
        sp = slot_box.split(factor=SPLIT, align=True)
        sp.label(text="Value:")
        if vtype == 'COLOR':
            sp.prop(layer, f"val_{key}", text="")
        else:
            sp.prop(layer, f"val_{key}", text="", slider=True)

    if key == 'base_color' and has_any:
        cc_box = slot_box.box()
        cc_col = cc_box.column(align=True)
        cc_col.label(text="Color Correction", icon='COLOR')
        cc_col.prop(layer, "hue",        slider=True)
        cc_col.prop(layer, "saturation", slider=True)
        cc_col.prop(layer, "value",      slider=True)
        cc_col.prop(layer, "contrast",   slider=True)
        cc_col.prop(layer, "gamma",      slider=True)
        cc_col.separator(factor=0.3)
        cc_col.prop(layer, "bc_use_own_mapping", text="Override Mapping", icon='DRIVER_TRANSFORM')
        if layer.bc_use_own_mapping:
            sp = cc_col.split(factor=0.32, align=True); sp.label(text="Coordinate:"); sp.prop(layer, "tex_coord_src",  text="")
            sp = cc_col.split(factor=0.32, align=True); sp.label(text="Projection:");  sp.prop(layer, "img_projection", text="")
            if layer.img_projection == 'BOX':
                sp = cc_col.split(factor=0.32, align=True); sp.label(text="Blend:"); sp.prop(layer, "img_projection_blend", text="", slider=True)
            cc_col.separator(factor=0.2)
            _draw_transform_block(cc_col, layer,
                                  lock_prop="bc_tiling_lock",
                                  tx_prop="bc_tiling_x", ty_prop="bc_tiling_y",
                                  ox_prop="bc_offset_x", oy_prop="bc_offset_y",
                                  rot_prop="bc_rotation", show_z=False)

    elif key in ('roughness', 'glossiness') and has_any:
        sp = slot_box.split(factor=SPLIT, align=True)
        sp.label(text="Bias:")
        sp.prop(layer, "roughness_bias", text="", slider=True)
        sp2 = slot_box.split(factor=SPLIT, align=True)
        sp2.label(text="Strength:")
        sp2.prop(layer, f"str_{key}", text="", slider=True)

    elif key == 'metallic' and has_any:
        sp = slot_box.split(factor=SPLIT, align=True)
        sp.label(text="Bias:")
        sp.prop(layer, "metallic_bias", text="", slider=True)
        sp2 = slot_box.split(factor=SPLIT, align=True)
        sp2.label(text="Strength:")
        sp2.prop(layer, "str_metallic", text="", slider=True)

    elif key == 'normal' and has_any:
        sp = slot_box.split(factor=SPLIT, align=True)
        sp.label(text="Strength:")
        sp.prop(layer, "normal_strength", text="", slider=True)
        dx_row = slot_box.row(align=True)
        dx_row.prop(layer, "normal_dx", text="DirectX → OpenGL", icon='NORMALS_FACE', toggle=True)

    elif key == 'bump' and has_any:
        sp = slot_box.split(factor=SPLIT, align=True)
        sp.label(text="Strength:")
        sp.prop(layer, "bump_strength", text="", slider=True)

    elif key == 'ao' and has_any:
        sp = slot_box.split(factor=SPLIT, align=True)
        sp.label(text="Strength:")
        sp.prop(layer, "ao_strength", text="", slider=True)

    elif key == 'emission':
        sp = slot_box.split(factor=SPLIT, align=True)
        sp.label(text="Strength:")
        sp.prop(layer, "emission_strength", text="", slider=True)

    elif key == 'coat_normal' and has_any:
        sp = slot_box.split(factor=SPLIT, align=True)
        sp.label(text="Strength:")
        sp.prop(layer, "normal_strength", text="", slider=True)

    elif key == 'displacement' and li == 0:
        sp1 = slot_box.split(factor=SPLIT, align=True)
        sp1.label(text="Scale:")
        sp1.prop(layer, "disp_scale", text="", slider=True)
        sp2 = slot_box.split(factor=SPLIT, align=True)
        sp2.label(text="Midlevel:")
        sp2.prop(layer, "disp_midlevel", text="", slider=True)

    # Per-channel override mapping (non base_color)
    if key != 'base_color' and ok:
        own_key  = f"ch_own_mapping_{key}"
        lock_k   = f"ch_tiling_lock_{key}"
        tr = slot_box.box()
        tr.prop(layer, own_key, text="Override Mapping", icon='DRIVER_TRANSFORM')
        if getattr(layer, own_key, False):
            tc_col = tr.column(align=True)
            sp = tc_col.split(factor=0.32, align=True); sp.label(text="Coordinate:"); sp.prop(layer, "tex_coord_src",  text="")
            sp = tc_col.split(factor=0.32, align=True); sp.label(text="Projection:");  sp.prop(layer, "img_projection", text="")
            if layer.img_projection == 'BOX':
                sp = tc_col.split(factor=0.32, align=True); sp.label(text="Blend:"); sp.prop(layer, "img_projection_blend", text="", slider=True)
            tc_col.separator(factor=0.3)
            _draw_transform_block(tc_col, layer,
                                  lock_prop=lock_k,
                                  tx_prop=f"ch_tiling_x_{key}", ty_prop=f"ch_tiling_y_{key}",
                                  ox_prop=f"ch_offset_x_{key}", oy_prop=f"ch_offset_y_{key}",
                                  rot_prop=f"ch_rotation_{key}", show_z=False)

    for oi, ov in enumerate(extras):
        _draw_overlay(col, ov, li, key, oi)


def _draw_layer(layout, layer, li, is_only, props=None):
    compact = props.compact_mode if props else False
    detail  = props.detail_view  if props else True
    COMPACT_HIDDEN = {'coat', 'sheen', 'thin_film'}

    v_keys = SHADER_MAPS.get(layer.shader_type, MAP_KEYS)
    _orm_maps = set()
    _orm_path = getattr(layer, 'orm_path', '').strip()
    if _orm_path and os.path.isfile(bpy.path.abspath(_orm_path)):
        _layout_key = getattr(layer, 'orm_layout', 'AO_ROUGH_MET')
        _orm_maps = set(ORM_LAYOUT_MAP.get(_layout_key, ('ao', 'roughness', 'metallic')))
    n_conn = sum(1 for k in v_keys if _has_img(layer, k) or _has_extras(layer, k) or k in _orm_maps)
    ctx = bpy.context
    mat = _active_mat(ctx)
    mn = mat.name if mat else ''

    box = layout.box()
    hrow = box.row(align=True)
    layer_expanded = _ui_get(ctx, mn, li, 'exp', default=True)
    op_exp = hrow.operator("pbr_ld.toggle_ui", text="",
                           icon='TRIA_DOWN' if layer_expanded else 'TRIA_RIGHT', emboss=False)
    op_exp.key = _ui_key(mn, li, 'exp'); op_exp.default = True
    hrow.prop(layer, "enabled", text="",
              icon='HIDE_OFF' if layer.enabled else 'HIDE_ON', emboss=False)
    is_solo = (props.solo_layer == li) if props else False
    solo_op = hrow.operator("pbr_ld.solo_layer", text="",
                            icon='SOLO_ON' if is_solo else 'SOLO_OFF', emboss=is_solo,
                            depress=is_solo)
    solo_op.layer_index = li
    hrow.prop(layer, "name", text="", emboss=layer_expanded)
    if not layer_expanded:
        if n_conn: hrow.label(text=f"{n_conn} maps")
        stype_icons = {'PRINCIPLED':'NODE_MATERIAL','GLASS':'MATERIAL','EMISSION':'LIGHT_SUN',
                       'DIFFUSE':'SHADING_SOLID','SSS':'OUTLINER_DATA_META'}
        hrow.label(text="", icon=stype_icons.get(layer.shader_type, 'NODE_MATERIAL'))
    up = hrow.operator("pbr_ld.move_layer", text="", icon='TRIA_UP',   emboss=False)
    up.layer_index = li; up.direction = 'UP'
    dn = hrow.operator("pbr_ld.move_layer", text="", icon='TRIA_DOWN', emboss=False)
    dn.layer_index = li; dn.direction = 'DOWN'
    cp = hrow.operator("pbr_ld.copy_layer", text="", icon='DUPLICATE', emboss=False)
    cp.layer_index = li
    if not is_only:
        rm = hrow.operator("pbr_ld.remove_layer", text="", icon='X', emboss=False)
        rm.layer_index = li

    if not layer_expanded: return

    col = box.column(align=False)

    if detail:
        col.separator(factor=0.2)

    sr = col.row(align=True); sr.label(text="Shader", icon='NODE_MATERIAL')
    sr.prop(layer, "shader_type", text="")
    if detail:
        if layer.shader_type == 'PRINCIPLED':
            col.prop(layer, "specular_distribution", text="Distribution")
            col.prop(layer, "sss_method", text="SSS Method")
        if layer.shader_type == 'SSS':
            col.prop(layer, "sss_method", text="SSS Method")
    col.separator(factor=0.4)

    sb = col.box()
    sb.prop(layer, "scan_dir_path", text="")

    # Part filter — only shown when folder has multiple distinct texture sets
    if layer.scan_dir_path.strip():
        d_check = bpy.path.abspath(layer.scan_dir_path.strip())
        _parts_check = detect_part_names(d_check) if os.path.isdir(d_check) else []
        if len(_parts_check) >= 2 or layer.scan_filter.strip():
            fr = sb.row(align=True)
            cur_filter = layer.scan_filter.strip()
            dp = fr.operator("pbr_ld.detect_parts",
                             text=cur_filter.replace('_', ' ').title() if cur_filter else "Select Part…",
                             icon='FILTER')
            dp.layer_index = li
            if cur_filter:
                cl = fr.operator("pbr_ld.apply_part_filter", text="", icon='X')
                cl.layer_index = li; cl.part_name = ''

    sr2 = sb.row(align=True); sr2.scale_y = 1.1
    so  = sr2.operator("pbr_ld.scan_layer",  text="Scan",  icon='VIEWZOOM');    so.layer_index  = li
    co  = sr2.operator("pbr_ld.clear_layer", text="Clear", icon='X');           co.layer_index  = li
    bso = sr2.operator("pbr_ld.batch_scan",  text="Batch", icon='FILEBROWSER'); bso.layer_index = li
    col.separator(factor=0.3)

    maps_expanded = _ui_get(ctx, mn, li, 'maps', default=False)
    op_maps = col.operator("pbr_ld.toggle_ui",
                           text=f"Maps  ({n_conn})" if n_conn else "Maps",
                           icon='TRIA_DOWN' if maps_expanded else 'TRIA_RIGHT', emboss=False)
    op_maps.key = _ui_key(mn, li, 'maps'); op_maps.default = False
    if maps_expanded:
        stype_ = layer.shader_type
        visible_groups = SHADER_GROUPS.get(stype_, [g[0] for g in MAP_GROUPS])
        for grp_key, grp_label, grp_icon, grp_keys in MAP_GROUPS:
            if grp_key not in visible_groups: continue
            if grp_key == 'displacement' and li != 0: continue
            if compact and grp_key in COMPACT_HIDDEN: continue
            visible_keys = [k for k in grp_keys if k in v_keys or grp_key == 'displacement']
            if not visible_keys: continue
            grp_conn = sum(1 for k in visible_keys if _has_img(layer, k) or _has_extras(layer, k) or k in _orm_maps)
            grp_expanded = _ui_get(ctx, mn, li, 'grp', grp_key, default=False)
            grp_box = col.box()
            grp_hdr = grp_box.row(align=True)
            op_grp = grp_hdr.operator("pbr_ld.toggle_ui", text="",
                                      icon='TRIA_DOWN' if grp_expanded else 'TRIA_RIGHT', emboss=False)
            op_grp.key = _ui_key(mn, li, 'grp', grp_key); op_grp.default = False
            grp_hdr.label(text=f"{grp_label}  ({grp_conn})" if grp_conn else grp_label, icon=grp_icon)
            if grp_expanded:
                for k in visible_keys:
                    _draw_map_slot(grp_box.column(align=True), layer, li, k, detail=detail)

        orm_box = col.box()
        orm_hdr = orm_box.row(align=True)
        orm_exp = _ui_get(ctx, mn, li, 'orm', default=False)
        op_orm = orm_hdr.operator("pbr_ld.toggle_ui", text="",
                                  icon='TRIA_DOWN' if orm_exp else 'TRIA_RIGHT', emboss=False)
        op_orm.key = _ui_key(mn, li, 'orm'); op_orm.default = False
        has_orm = bool(getattr(layer, 'orm_path', '').strip())
        orm_hdr.label(text="ORM / ARM", icon='PLUGIN')
        if has_orm: orm_hdr.label(text="", icon='CHECKMARK')
        if orm_exp:
            orm_box.prop(layer, "orm_path",   text="", icon='FILE_IMAGE')
            orm_box.prop(layer, "orm_layout", text="")

    col.separator(factor=0.3)

    # ── Mapping section ─────────────────────────────────────────────────────
    mapping_expanded = _ui_get(ctx, mn, li, 'mapping', default=False)
    op_map = col.operator("pbr_ld.toggle_ui", text="Mapping",
                          icon='TRIA_DOWN' if mapping_expanded else 'TRIA_RIGHT', emboss=False)
    op_map.key = _ui_key(mn, li, 'mapping'); op_map.default = False
    if mapping_expanded:
        mb2 = col.box()
        MSPLIT = 0.32

        # Texture Coordinate
        sp = mb2.split(factor=MSPLIT, align=True)
        sp.label(text="Tex Coord:")
        sp.prop(layer, "tex_coord_src", text="")

        # Image Projection
        sp = mb2.split(factor=MSPLIT, align=True)
        sp.label(text="Projection:")
        sp.prop(layer, "img_projection", text="")
        if layer.img_projection == 'BOX':
            sp2 = mb2.split(factor=MSPLIT, align=True)
            sp2.label(text="Blend:")
            sp2.prop(layer, "img_projection_blend", text="", slider=True)

        mb2.separator(factor=0.3)

        # Transform
        mb2.label(text="Transform", icon='OBJECT_ORIGIN')
        _draw_transform_block(mb2, layer,
                              lock_prop="tiling_lock",
                              tx_prop="tiling_x", ty_prop="tiling_y", tz_prop="tiling_z",
                              ox_prop="offset_x", oy_prop="offset_y", oz_prop="offset_z",
                              rot_prop="rotation", show_z=True, layer_index=li)

    col.separator(factor=0.3)

    if li > 0:
        mp = layer.mask_path.strip()
        has_m = bool(mp and os.path.isfile(bpy.path.abspath(mp)))
        mask_expanded = _ui_get(ctx, mn, li, 'lmask', default=False)
        op_lmask = col.operator("pbr_ld.toggle_ui",
                                text=f"Layer Mask  ({'connected' if has_m else 'none'})",
                                icon='TRIA_DOWN' if mask_expanded else 'TRIA_RIGHT', emboss=False)
        op_lmask.key = _ui_key(mn, li, 'lmask'); op_lmask.default = False
        if mask_expanded:
            mk = col.box()
            mk.prop(layer, "blend_mode",    text="Blend Mode")
            mk.prop(layer, "mask_strength", slider=True)
            mk.separator(factor=0.3)
            mk.prop(layer, "mask_type", text="")
            if layer.mask_type == 'IMAGE':
                mr = mk.row(align=True)
                mr.prop(layer, "mask_path", text="", icon='FILE_IMAGE')
                if hasattr(layer, 'mask_udim'):
                    mr.prop(layer, "mask_udim", text="",
                             icon='LIBRARY_DATA_DIRECT' if layer.mask_udim else 'LIBRARY_DATA_OVERRIDE')
            else:
                _draw_proc_mask_ui(mk, layer)
            mk.prop(layer, "mask_invert")
            mnmxr = mk.row(align=True)
            mnmxr.prop(layer, "mask_min", text="Min", slider=True)
            mnmxr.prop(layer, "mask_max", text="Max", slider=True)
            mk.separator(factor=0.3)
            mk.label(text="Mask Transform", icon='DRIVER_TRANSFORM')
            sp = mk.split(factor=0.32, align=True); sp.label(text="Coordinate:"); sp.prop(layer, "mask_tex_coord",  text="")
            sp = mk.split(factor=0.32, align=True); sp.label(text="Projection:");  sp.prop(layer, "mask_projection", text="")
            if layer.mask_projection == 'BOX':
                sp = mk.split(factor=0.32, align=True); sp.label(text="Blend:"); sp.prop(layer, "mask_projection_blend", text="", slider=True)
            mk.separator(factor=0.2)
            _draw_transform_block(mk, layer,
                                  lock_prop="mask_tiling_lock",
                                  tx_prop="mask_tiling_x", ty_prop="mask_tiling_y",
                                  ox_prop="mask_offset_x", oy_prop="mask_offset_y",
                                  rot_prop="mask_rotation", show_z=False)
        col.separator(factor=0.3)


# ══════════════════════════════════════════════════════════════════════════════
# NEW UI — LAYER STACK + ACTIVE DETAIL PANEL
# ══════════════════════════════════════════════════════════════════════════════

_STYPE_ICONS = {
    'PRINCIPLED': 'NODE_MATERIAL',
    'GLASS':      'MATERIAL',
    'EMISSION':   'LIGHT_SUN',
    'DIFFUSE':    'SHADING_SOLID',
    'SSS':        'OUTLINER_DATA_META',
}


def _draw_layer_row(layout, layer, li, is_only, props, mn):
    """Compact single-row layer entry; active layer gets a box highlight."""
    is_active = (li == props.active_layer_index)
    is_solo   = (props.solo_layer == li)

    outer = layout.box() if is_active else layout
    row   = outer.row(align=True)

    row.prop(layer, "enabled", text="",
             icon='HIDE_OFF' if layer.enabled else 'HIDE_ON', emboss=False)

    sol = row.operator("pbr_ld.solo_layer", text="",
                       icon='SOLO_ON' if is_solo else 'SOLO_OFF',
                       emboss=False, depress=is_solo)
    sol.layer_index = li

    sel = row.operator("pbr_ld.set_active_layer",
                       text=layer.name, emboss=False, depress=is_active)
    sel.index = li

    row.label(text="", icon=_STYPE_ICONS.get(layer.shader_type, 'NODE_MATERIAL'))

    u = row.operator("pbr_ld.move_layer", text="", icon='TRIA_UP',   emboss=False)
    u.layer_index = li; u.direction = 'UP'
    d = row.operator("pbr_ld.move_layer", text="", icon='TRIA_DOWN', emboss=False)
    d.layer_index = li; d.direction = 'DOWN'

    cp = row.operator("pbr_ld.copy_layer", text="", icon='DUPLICATE', emboss=False)
    cp.layer_index = li

    if not is_only:
        rm = row.operator("pbr_ld.remove_layer", text="", icon='X', emboss=False)
        rm.layer_index = li


def _draw_active_layer_detail(layout, context, mat, props, li_override=None):
    """Full controls for the currently selected layer, shown below the stack."""
    li    = li_override if li_override is not None else props.active_layer_index
    if li >= len(props.layers): return
    layer = props.layers[li]
    mn    = mat.name
    compact         = props.compact_mode
    COMPACT_HIDDEN  = {'coat', 'sheen', 'thin_film'}
    v_keys          = SHADER_MAPS.get(layer.shader_type, MAP_KEYS)

    _orm_maps = set()
    _orm_path = getattr(layer, 'orm_path', '').strip()
    if _orm_path and os.path.isfile(bpy.path.abspath(_orm_path)):
        _layout_key = getattr(layer, 'orm_layout', 'AO_ROUGH_MET')
        _orm_maps = set(ORM_LAYOUT_MAP.get(_layout_key, ('ao', 'roughness', 'metallic')))

    n_conn = sum(1 for k in v_keys
                 if _has_img(layer, k) or _has_extras(layer, k) or k in _orm_maps)

    layout.separator(factor=0.15)

    # ── Texture Folder ────────────────────────────────────────────────────────
    frow = layout.row(align=True)
    frow.label(text="Texture Folder", icon='FILE_FOLDER')
    layout.prop(layer, "scan_dir_path", text="")

    if layer.scan_dir_path.strip():
        d_check = bpy.path.abspath(layer.scan_dir_path.strip())
        _parts  = detect_part_names(d_check) if os.path.isdir(d_check) else []
        if len(_parts) >= 2 or layer.scan_filter.strip():
            fr  = layout.row(align=True)
            cur = layer.scan_filter.strip()
            dp  = fr.operator("pbr_ld.detect_parts",
                              text=cur.replace('_',' ').title() if cur else "Select Part…",
                              icon='FILTER')
            dp.layer_index = li
            if cur:
                cl = fr.operator("pbr_ld.apply_part_filter", text="", icon='X')
                cl.layer_index = li; cl.part_name = ''

    sbr = layout.row(align=True)
    sbr.scale_y = 1.1
    so  = sbr.operator("pbr_ld.scan_layer",  text="Scan",  icon='VIEWZOOM');    so.layer_index  = li
    co  = sbr.operator("pbr_ld.clear_layer", text="Clear", icon='X');           co.layer_index  = li
    bso = sbr.operator("pbr_ld.batch_scan",  text="Batch", icon='FILEBROWSER'); bso.layer_index = li

    layout.separator(factor=0.8)

    # ── Shader type ─────────────────────────────────────────────────────────
    layout.prop(layer, "shader_type", text="")
    if props.detail_view:
        if layer.shader_type == 'PRINCIPLED':
            sub = layout.row(align=True)
            sub.prop(layer, "specular_distribution", text="")
            sub.prop(layer, "sss_method",            text="")
        elif layer.shader_type == 'SSS':
            layout.prop(layer, "sss_method", text="")

    layout.separator(factor=0.2)

    # ── Channels — collapsible section ────────────────────────────────────────
    ch_open  = _ui_get(context, mn, li, 'ch_open', default=True)
    ch_hdr   = layout.row(align=True)
    op_ch    = ch_hdr.operator("pbr_ld.toggle_ui", text="",
                               icon='TRIA_DOWN' if ch_open else 'TRIA_RIGHT', emboss=False)
    op_ch.key = _ui_key(mn, li, 'ch_open'); op_ch.default = True
    ch_center = ch_hdr.row()
    ch_center.alignment = 'CENTER'
    ch_center.label(text=f"Channels  ({n_conn})" if n_conn else "Channels")

    if not ch_open:
        layout.separator(factor=0.2)
    else:
        stype_       = layer.shader_type
        visible_grps = SHADER_GROUPS.get(stype_, [g[0] for g in MAP_GROUPS])

        # Missing maps warning
        missing_maps = [MAP_INFO[k][0] for k in v_keys
                        if getattr(layer, f'path_{k}', '').strip()
                        and not os.path.isfile(bpy.path.abspath(
                            getattr(layer, f'path_{k}', '').strip()))]
        if missing_maps:
            warn = layout.box()
            warn.alert = True
            warn.label(text=f"Missing: {', '.join(missing_maps[:3])}{'…' if len(missing_maps) > 3 else ''}",
                       icon='ERROR')

        _TAB_SHORT = {
            'base':         'Base Color',
            'roughness':    'Roughness',
            'metal_spec':   'Metal/Spec',
            'normal':       'Normal',
            'coat':         'Coat',
            'sheen':        'Sheen',
            'emission':     'Emission',
            'transparency': 'Alpha',
            'sss':          'Subsurface',
            'thin_film':    'Thin Film',
            'ao':           'AO',
            'displacement': 'Displace',
            'orm':          'ORM/ARM',
        }

        all_tab_defs = []
        for grp_key, grp_label, grp_icon, grp_keys in MAP_GROUPS:
            if grp_key not in visible_grps: continue
            if grp_key == 'displacement' and li != 0: continue
            if compact and grp_key in COMPACT_HIDDEN: continue
            vis = [k for k in grp_keys if k in v_keys or grp_key == 'displacement']
            if not vis: continue
            all_tab_defs.append((grp_key, _TAB_SHORT.get(grp_key, grp_label), grp_keys))

        all_tab_defs.append(('orm', 'ORM/ARM', []))

        def _tab_status(grp_key, grp_keys):
            """Return 'ok', 'missing', or 'empty' for a group."""
            if grp_key == 'orm':
                p = getattr(layer, 'orm_path', '').strip()
                if p: return 'ok' if os.path.isfile(bpy.path.abspath(p)) else 'missing'
                return 'empty'
            vis = [k for k in grp_keys if k in v_keys or grp_key == 'displacement']
            has_ok = has_miss = False
            for k in vis:
                p = getattr(layer, f'path_{k}', '').strip()
                if p:
                    if os.path.isfile(bpy.path.abspath(p)): has_ok = True
                    else: has_miss = True
            if has_miss: return 'missing'
            if has_ok:   return 'ok'
            return 'empty'

        TABS_PER_ROW = 4
        for row_start in range(0, len(all_tab_defs), TABS_PER_ROW):
            row_tabs = all_tab_defs[row_start:row_start + TABS_PER_ROW]
            trow = layout.row(align=True)
            trow.scale_y = 1.15
            for grp_key, short_lbl, grp_keys in row_tabs:
                is_open  = _ui_get(context, mn, li, 'mgrp', grp_key, default=False)
                status   = _tab_status(grp_key, grp_keys)
                tab_cell = trow.row(align=True)
                tab_cell.alert = (status == 'missing')
                op = tab_cell.operator("pbr_ld.set_map_group",
                                       text=short_lbl, emboss=True, depress=is_open)
                op.layer_index = li; op.group_key = grp_key

        for grp_key, short_lbl, grp_stored_keys in all_tab_defs:
            is_open = _ui_get(context, mn, li, 'mgrp', grp_key, default=False)
            if not is_open:
                continue

            layout.separator(factor=0.15)
            lbl_row = layout.row(align=True)
            lbl_row.alignment = 'CENTER'
            lbl_row.label(text=short_lbl)

            if grp_key == 'orm':
                ob = layout.box()
                ob.prop(layer, "orm_path",   text="ORM Map", icon='FILE_IMAGE')
                ob.prop(layer, "orm_layout", text="Layout")
            else:
                # Find the group definition and draw its slots
                found = False
                for gk, gl, gi, gkeys in MAP_GROUPS:
                    if gk != grp_key:
                        continue
                    vis = [k for k in gkeys if k in v_keys or (gk == 'displacement' and li == 0)]
                    if vis:
                        gc = layout.column(align=True)
                        # Normal/Bump group: show Use button at top inside the column
                        if gk == 'normal':
                            has_nor = bool(getattr(layer, 'path_normal', '').strip())
                            has_bmp = bool(getattr(layer, 'path_bump',   '').strip())
                            if has_nor and has_bmp:
                                nb_row = gc.row(align=True)
                                nb_row.prop(layer, "normal_bump_mode", expand=True)
                        for k in vis:
                            _draw_map_slot(gc, layer, li, k)
                    found = True
                    break
                if not found:
                    layout.label(text=f"(no slots for {grp_key})")

    layout.separator(factor=0.2)

    # ── Mapping ───────────────────────────────────────────────────────────────
    map_exp  = _ui_get(context, mn, li, 'mapping', default=False)
    map_hdr  = layout.row(align=True)
    op_map   = map_hdr.operator("pbr_ld.toggle_ui", text="",
                                icon='TRIA_DOWN' if map_exp else 'TRIA_RIGHT', emboss=False)
    op_map.key = _ui_key(mn, li, 'mapping'); op_map.default = False
    map_center = map_hdr.row()
    map_center.alignment = 'CENTER'
    map_center.label(text="Mapping")

    if map_exp:
        mb = layout.box()
        S  = 0.32
        sp = mb.split(factor=S, align=True); sp.label(text="Tex Coord:")
        sp.prop(layer, "tex_coord_src",  text="")
        sp = mb.split(factor=S, align=True); sp.label(text="Projection:")
        sp.prop(layer, "img_projection", text="")
        if layer.img_projection == 'BOX':
            sp = mb.split(factor=S, align=True); sp.label(text="Blend:")
            sp.prop(layer, "img_projection_blend", text="", slider=True)
        mb.separator(factor=0.3)
        mb.label(text="Transform", icon='OBJECT_ORIGIN')
        _draw_transform_block(mb, layer,
                              lock_prop="tiling_lock",
                              tx_prop="tiling_x", ty_prop="tiling_y", tz_prop="tiling_z",
                              ox_prop="offset_x", oy_prop="offset_y", oz_prop="offset_z",
                              rot_prop="rotation", show_z=True, layer_index=li)

    # ── Layer Mask (layers above base) ────────────────────────────────────────
    if li > 0:
        mp    = layer.mask_path.strip()
        has_m = bool(mp and os.path.isfile(bpy.path.abspath(mp)))
        msk_e = _ui_get(context, mn, li, 'lmask', default=False)
        msk_hdr = layout.row(align=True)
        op_m    = msk_hdr.operator("pbr_ld.toggle_ui", text="",
                                   icon='TRIA_DOWN' if msk_e else 'TRIA_RIGHT', emboss=False)
        op_m.key = _ui_key(mn, li, 'lmask'); op_m.default = False
        msk_center = msk_hdr.row()
        msk_center.alignment = 'CENTER'
        msk_center.label(text=f"Layer Mask  ({'connected' if has_m else 'none'})")

        if msk_e:
            mk = layout.box()
            mk.prop(layer, "blend_mode",    text="Blend Mode")
            mk.prop(layer, "mask_strength", slider=True)
            mk.separator(factor=0.3)
            mk.prop(layer, "mask_type", text="")
            if layer.mask_type == 'IMAGE':
                mr = mk.row(align=True)
                mr.prop(layer, "mask_path", text="", icon='FILE_IMAGE')
                if hasattr(layer, 'mask_udim'):
                    mr.prop(layer, "mask_udim", text="",
                            icon='LIBRARY_DATA_DIRECT' if layer.mask_udim else 'LIBRARY_DATA_OVERRIDE')
            else:
                _draw_proc_mask_ui(mk, layer)
            mk.prop(layer, "mask_invert")
            mnr = mk.row(align=True)
            mnr.prop(layer, "mask_min", text="Min", slider=True)
            mnr.prop(layer, "mask_max", text="Max", slider=True)
            mk.separator(factor=0.3)
            mk.label(text="Mask Transform", icon='DRIVER_TRANSFORM')
            sp = mk.split(factor=0.32, align=True); sp.label(text="Coordinate:"); sp.prop(layer, "mask_tex_coord",  text="")
            sp = mk.split(factor=0.32, align=True); sp.label(text="Projection:");  sp.prop(layer, "mask_projection", text="")
            if layer.mask_projection == 'BOX':
                sp = mk.split(factor=0.32, align=True); sp.label(text="Blend:"); sp.prop(layer, "mask_projection_blend", text="", slider=True)
            mk.separator(factor=0.2)
            _draw_transform_block(mk, layer,
                                  lock_prop="mask_tiling_lock",
                                  tx_prop="mask_tiling_x", ty_prop="mask_tiling_y",
                                  ox_prop="mask_offset_x", oy_prop="mask_offset_y",
                                  rot_prop="mask_rotation", show_z=False)


def _draw_layer_accordion(layout, context, layer, li, is_only, props, mn):
    """Original-style box with expand toggle + full detail inside when expanded."""
    is_solo   = (props.solo_layer == li)
    _orm_maps = set()
    _orm_path = getattr(layer, 'orm_path', '').strip()
    v_keys    = SHADER_MAPS.get(layer.shader_type, MAP_KEYS)
    if _orm_path and os.path.isfile(bpy.path.abspath(_orm_path)):
        _lk = getattr(layer, 'orm_layout', 'AO_ROUGH_MET')
        _orm_maps = set(ORM_LAYOUT_MAP.get(_lk, ('ao', 'roughness', 'metallic')))
    n_conn = sum(1 for k in v_keys
                 if _has_img(layer, k) or _has_extras(layer, k) or k in _orm_maps)

    layer_expanded = _ui_get(context, mn, li, 'exp', default=True)

    box  = layout.box()
    hrow = box.row(align=True)

    op_exp = hrow.operator("pbr_ld.toggle_ui", text="",
                           icon='TRIA_DOWN' if layer_expanded else 'TRIA_RIGHT', emboss=False)
    op_exp.key = _ui_key(mn, li, 'exp'); op_exp.default = True

    hrow.prop(layer, "enabled", text="",
              icon='HIDE_OFF' if layer.enabled else 'HIDE_ON', emboss=False)

    sol = hrow.operator("pbr_ld.solo_layer", text="",
                        icon='SOLO_ON' if is_solo else 'SOLO_OFF',
                        emboss=False, depress=is_solo)
    sol.layer_index = li

    hrow.prop(layer, "name", text="", emboss=layer_expanded)

    if not layer_expanded:
        if n_conn: hrow.label(text=f"{n_conn} maps")
        hrow.label(text="", icon=_STYPE_ICONS.get(layer.shader_type, 'NODE_MATERIAL'))

    u = hrow.operator("pbr_ld.move_layer", text="", icon='TRIA_UP',   emboss=False)
    u.layer_index = li; u.direction = 'UP'
    d = hrow.operator("pbr_ld.move_layer", text="", icon='TRIA_DOWN', emboss=False)
    d.layer_index = li; d.direction = 'DOWN'
    cp = hrow.operator("pbr_ld.copy_layer", text="", icon='DUPLICATE', emboss=False)
    cp.layer_index = li
    if not is_only:
        rm = hrow.operator("pbr_ld.remove_layer", text="", icon='X', emboss=False)
        rm.layer_index = li

    if layer_expanded:
        _draw_active_layer_detail(box.column(align=False), context,
                                  bpy.data.materials.get(mn) or _active_mat(context),
                                  props, li_override=li)


def draw_pbr_panel(layout, context):
    wm   = context.window_manager
    mode = getattr(wm, 'pbr_mode', 'MANUAL')

    # ── Mode tabs ─────────────────────────────────────────────────────────────
    top = layout.row(align=True)
    top.scale_y = 1.2
    top.prop(wm, "pbr_mode", expand=True)
    layout.separator(factor=0.35)

    # ── AUTO MODE ─────────────────────────────────────────────────────────────
    if mode == 'AUTO':
        draw_auto_mode_panel(layout, context)
        return

    # ── MANUAL MODE ───────────────────────────────────────────────────────────
    mat = _active_mat(context)
    if mat is None:
        box = layout.box()
        box.label(text="No active material", icon='INFO')
        box.scale_y = 1.1
        box.operator("pbr_ld.create_material", text="New PBR Material", icon='MATERIAL_DATA')
        return

    props = mat.pbr_props
    if not props.layers: props.layers.add().name = "Base Layer"
    mn = mat.name

    # ── Material header ───────────────────────────────────────────────────────
    mhdr = layout.row(align=True)
    mhdr.label(text=mat.name, icon='MATERIAL')
    mhdr.prop(props, "compact_mode", text="",
              icon='COMMUNITY'   if props.compact_mode else 'COLLAPSEMENU', toggle=True)
    mhdr.prop(props, "detail_view",  text="",
              icon='PREFERENCES' if props.detail_view  else 'ALIGN_JUSTIFY', toggle=True)
    mhdr.operator("pbr_ld.collapse_all",    text="", icon='RIGHTARROW_THIN')
    mhdr.operator("pbr_ld.create_material", text="", icon='ADD')

    layout.separator(factor=0.15)

    # ── Layer Stack — original box+accordion style ────────────────────────────
    is_only = len(props.layers) == 1
    for idx, layer in enumerate(props.layers):
        _draw_layer_accordion(layout, context, layer, idx, is_only, props, mn)

    add = layout.row(align=True)
    add.scale_y = 1.1
    add.operator("pbr_ld.add_layer", text="Add Layer", icon='ADD')

    layout.separator(factor=0.4)

    # ── Build / Rebuild — prominent footer ────────────────────────────────────
    br = layout.row(align=True)
    br.scale_y = 1.1
    if props.is_built:
        br.operator("pbr_ld.rebuild_network", text="Rebuild Network", icon='FILE_REFRESH')
    else:
        br.operator("pbr_ld.build_network", text="Build Material", icon='NODE_COMPOSITING')


class PBR_OT_AutoBuild(bpy.types.Operator):
    """Auto-build PBR layers from material slot names and texture folder."""
    bl_idname  = "pbr_ld.auto_build"
    bl_label   = "Auto-Build Selected"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        return (bool(getattr(wm, 'pbr_auto_folder', '').strip()) and
                any(o.type == 'MESH' for o in context.selected_objects))

    def execute(self, context):
        wm        = context.window_manager
        folder    = bpy.path.abspath(wm.pbr_auto_folder.strip())
        fold_mode = wm.pbr_auto_mode
        on_exist  = wm.pbr_auto_on_exist

        if not os.path.isdir(folder):
            self.report({'WARNING'}, "Set a valid textures folder."); return {'CANCELLED'}

        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        if not meshes:
            self.report({'WARNING'}, "No mesh objects selected."); return {'CANCELLED'}

        results   = []
        processed = set()

        for obj in meshes:
            for slot in obj.material_slots:
                mat = slot.material
                if not mat or mat.name in processed:
                    continue
                if mat.library:
                    results.append((mat.name, '', 0, 'SKIPPED_LINKED'))
                    continue
                processed.add(mat.name)

                # Find common keyword between material name and texture filenames
                kw = _find_common_keyword(mat.name, folder, fold_mode)
                if not kw:
                    results.append((mat.name, '', 0, 'NO_KEYWORD'))
                    continue

                # Scan
                if fold_mode == 'SUBDIR':
                    scan_folder = os.path.join(folder, kw)
                    found, orm_path = scan_dir(scan_folder)
                else:
                    found, orm_path = scan_dir(folder, keyword=kw)

                if not found and not orm_path:
                    results.append((mat.name, kw, 0, 'NO_MAPS'))
                    continue

                props = mat.pbr_props
                existing = next((i for i, l in enumerate(props.layers)
                                 if l.name == kw or i == 0), None)

                if existing is not None and on_exist == 'SKIP':
                    results.append((mat.name, kw, len(found), 'SKIPPED'))
                    continue

                if existing is not None and on_exist == 'REBUILD':
                    while props.layers:
                        props.layers.remove(0)
                    existing = None

                if existing is None or not props.layers:
                    layer = props.layers.add()
                else:
                    layer = props.layers[existing]

                layer.name = kw

                # Assign found maps
                for k, fp in found.items():
                    setattr(layer, f"path_{k}", fp)
                if orm_path:
                    layer.orm_path = orm_path

                # Build network
                mat.use_nodes = True
                build_network(mat)
                mat.pbr_props.is_built = True

                results.append((mat.name, kw, len(found) + (1 if orm_path else 0), 'OK'))

        # Store results for UI display
        wm.pbr_ui_state = _auto_results_to_state(context, results)

        ok    = sum(1 for r in results if r[3] == 'OK')
        skip  = sum(1 for r in results if r[3] in ('SKIPPED','SKIPPED_LINKED'))
        fail  = sum(1 for r in results if r[3] in ('NO_MAPS','NO_SUBFOLDER','NO_KEYWORD'))
        self.report({'INFO'},
            f"Auto-Build: {ok} built, {skip} skipped, {fail} not found.")
        return {'FINISHED'}


def _mat_tokens(name):
    """
    Tokenise a material name into meaningful words, stripping noise.
    e.g. 'Body_Hand_Mat' → {'body','hand'}
         'Hand'          → {'hand'}
         'M_Car_Body_01' → {'car','body'}
    """
    import re
    # Split on underscore, space, dash, and camelCase boundaries
    raw = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
    tokens = re.split(r'[_\-\s]+', raw.lower())
    # Noise words to throw away
    NOISE = {
        'mat','material','m','mi','sm','pm',
        'shader','shd','base','surface',
        '2k','4k','8k','1k','16k',
        '0','1','2','3','4','5','6','7','8','9',
        'v1','v2','v3','final','new','old','low','high',
    }
    return {t for t in tokens if t and t not in NOISE and not t.isdigit() and len(t) >= 2}


def _find_common_keyword(mat_name, folder, fold_mode):
    """
    Find the best keyword to use for scanning by matching mat tokens
    against tokens found in actual filenames in the folder.
    Returns the single best token string, or None.
    """
    import re
    mat_tks = _mat_tokens(mat_name)
    if not mat_tks:
        return None

    if fold_mode == 'SUBDIR':
        # In subdir mode, match folder name directly
        try:
            match = next(d for d in os.listdir(folder)
                         if _mat_tokens(d) & mat_tks
                         and os.path.isdir(os.path.join(folder, d)))
            return match
        except StopIteration:
            return None

    # Flat mode — check all image filenames for token overlap
    token_hits = {}   # token → how many files contain it
    for f in os.listdir(folder):
        if os.path.splitext(f)[1].lower() not in IMAGE_EXTENSIONS:
            continue
        file_tks = _mat_tokens(os.path.splitext(f)[0])
        for t in mat_tks & file_tks:
            token_hits[t] = token_hits.get(t, 0) + 1

    if not token_hits:
        return None
    # Return the token that appears in the most files (most specific match)
    return max(token_hits, key=token_hits.get)

def _auto_results_to_state(context, results):
    """Persist auto-build results into pbr_ui_state for display."""
    wm = context.window_manager
    try:
        d = json.loads(getattr(wm, 'pbr_ui_state', '{}'))
    except Exception:
        d = {}
    d['auto_results'] = results
    return json.dumps(d)


def _get_auto_results(context):
    wm = context.window_manager
    try:
        return json.loads(getattr(wm, 'pbr_ui_state', '{}')).get('auto_results', [])
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# AUTO MODE PANEL DRAW
# ══════════════════════════════════════════════════════════════════════════════

def draw_auto_mode_panel(layout, context):
    wm = context.window_manager
    SPLIT = 0.32

    box = layout.box()
    box.label(text="Auto-Build Settings", icon='SHADERFX')

    # Folder
    sp = box.split(factor=SPLIT, align=True)
    sp.label(text="Folder:")
    sp.prop(wm, "pbr_auto_folder", text="")

    # Folder mode
    sp = box.split(factor=SPLIT, align=True)
    sp.label(text="Layout:")
    sp.prop(wm, "pbr_auto_mode", text="")

    box.separator(factor=0.3)

    # On-exist behaviour
    sp = box.split(factor=SPLIT, align=True)
    sp.label(text="Existing:")
    sp.prop(wm, "pbr_auto_on_exist", text="")

    box.separator(factor=0.5)

    # Auto-build button
    sel = [o for o in context.selected_objects if o.type == 'MESH']
    btn = box.row(align=True)
    btn.scale_y = 1.4
    btn.enabled = bool(getattr(wm, 'pbr_auto_folder', '').strip()) and bool(sel)
    btn.operator("pbr_ld.auto_build",
                 text=f"Auto-Build  ({len(sel)} object{'s' if len(sel)!=1 else ''})",
                 icon='SHADERFX')

    # ── Results list ──────────────────────────────────────────────────────────
    results = _get_auto_results(context)
    if not results:
        return

    layout.separator(factor=0.3)
    res_box = layout.box()
    res_box.label(text="Last Build Results", icon='INFO')

    STATUS_ICON = {
        'OK':             'CHECKMARK',
        'SKIPPED':        'RADIOBUT_OFF',
        'SKIPPED_LINKED': 'LIBRARY_DATA_OVERRIDE',
        'NO_MAPS':        'ERROR',
        'NO_SUBFOLDER':   'ERROR',
        'NO_KEYWORD':     'ERROR',
    }
    STATUS_LABEL = {
        'OK':             '',
        'SKIPPED':        'skipped',
        'SKIPPED_LINKED': 'linked — skipped',
        'NO_MAPS':        'no maps found',
        'NO_SUBFOLDER':   'subfolder missing',
        'NO_KEYWORD':     'could not derive keyword',
    }

    for mat_name, kw, n_maps, status in results:
        row = res_box.row(align=True)
        row.label(text="", icon=STATUS_ICON.get(status, 'QUESTION'))
        if status == 'OK':
            row.label(text=f"{mat_name}  →  {n_maps} map{'s' if n_maps!=1 else ''}")
        else:
            row.label(text=f"{mat_name}  —  {STATUS_LABEL.get(status, status)}")


# ══════════════════════════════════════════════════════════════════════════════
# NEW OPERATORS — ACTIVE LAYER SELECTION + MAP GROUP TABS
# ══════════════════════════════════════════════════════════════════════════════

class PBR_OT_DropImage(Operator):
    """Drop an image file onto a map slot"""
    bl_idname  = "pbr_ld.drop_image"
    bl_label   = "Drop Image"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    layer_index: IntProperty()
    map_key:     StringProperty()
    filepath:    StringProperty(subtype='FILE_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        layer = mat.pbr_props.layers[self.layer_index]
        setattr(layer, f"path_{self.map_key}", self.filepath)
        if mat.pbr_props.is_built:
            build_network(mat)
        return {'FINISHED'}


class PBR_OT_SetActiveLayer(Operator):
    bl_idname = "pbr_ld.set_active_layer"
    bl_label  = "Select Layer"
    bl_options = {'INTERNAL'}
    index: IntProperty()
    def execute(self, context):
        mat = _active_mat(context)
        if mat and self.index < len(mat.pbr_props.layers):
            mat.pbr_props.active_layer_index = self.index
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}


class PBR_OT_SetMapGroup(Operator):
    """Toggle a map-group tab (multi-select)."""
    bl_idname  = "pbr_ld.set_map_group"
    bl_label   = "Toggle Map Group"
    bl_options = {'INTERNAL'}
    layer_index: IntProperty()
    group_key:   StringProperty()
    def execute(self, context):
        mat = _active_mat(context)
        if not mat: return {'CANCELLED'}
        mn  = mat.name
        li  = self.layer_index
        cur = _ui_get(context, mn, li, 'mgrp', self.group_key, default=False)
        _ui_set(context, not cur, mn, li, 'mgrp', self.group_key)
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}


# ══════════════════════════════════════════════════════════════════════════════
# PANELS
# ══════════════════════════════════════════════════════════════════════════════

class PBR_PT_ShaderEditor(Panel):
    bl_label = "PBR Lookdev"; bl_idname = "PBR_PT_shader_editor"
    bl_space_type = 'NODE_EDITOR'; bl_region_type = 'UI'; bl_category = 'PBR Lookdev'
    @classmethod
    def poll(cls, context):
        s = context.space_data
        return s.type == 'NODE_EDITOR' and s.tree_type == 'ShaderNodeTree' and s.shader_type == 'OBJECT'
    def draw_header(self, context): self.layout.label(text="", icon="NODE_MATERIAL")
    def draw(self, context): draw_pbr_panel(self.layout, context)


class PBR_PT_Viewport(Panel):
    bl_label = "PBR Lookdev"; bl_idname = "PBR_PT_viewport"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = 'PBR Lookdev'
    def draw_header(self, context): self.layout.label(text="", icon="NODE_MATERIAL")
    def draw(self, context): draw_pbr_panel(self.layout, context)


class PBR_PT_MaterialProperties(Panel):
    bl_label = "PBR Lookdev"; bl_idname = "PBR_PT_material_properties"
    bl_space_type = 'PROPERTIES'; bl_region_type = 'WINDOW'; bl_context = 'material'
    def draw_header(self, context): self.layout.label(text="", icon="NODE_MATERIAL")
    def draw(self, context): draw_pbr_panel(self.layout, context)


# ══════════════════════════════════════════════════════════════════════════════
# REGISTRATION
# ══════════════════════════════════════════════════════════════════════════════

classes = (
    PBR_Overlay,
    PBR_MapLayer,
    PBR_MaterialProps,
    PBR_OT_CreateMaterial,
    PBR_OT_AddLayer,
    PBR_OT_RemoveLayer,
    PBR_OT_MoveLayer,
    PBR_OT_ScanLayer,
    PBR_OT_DetectParts,
    PBR_OT_ApplyPartFilter,
    PBR_OT_ClearLayer,
    PBR_OT_AddOverlay,
    PBR_OT_RemoveOverlay,
    PBR_OT_MoveOverlay,
    PBR_OT_CopyLayer,
    PBR_OT_SetTiling,
    PBR_OT_CollapseAll,
    PBR_OT_ToggleUI,
    PBR_OT_PickColorSpace,
    PBR_OT_ApplyColorSpace,
    PBR_OT_BatchScanFolders,
    PBR_OT_SoloLayer,
    PBR_OT_SetActiveLayer,
    PBR_OT_SetMapGroup,
    PBR_OT_AutoBuild,
    PBR_OT_Build,
    PBR_OT_Rebuild,
    PBR_PT_ShaderEditor,
    PBR_PT_Viewport,
    PBR_PT_MaterialProperties,
)

def register():
    for c in classes: bpy.utils.register_class(c)
    bpy.types.Material.pbr_props = PointerProperty(type=PBR_MaterialProps)
    bpy.types.WindowManager.pbr_ui_state  = StringProperty(default='{}')
    bpy.types.WindowManager.pbr_mode      = EnumProperty(
        name="PBR Mode",
        items=[
            ('MANUAL', 'Manual', 'Build layers manually', 'TOOL_SETTINGS',   0),
            ('AUTO',   'Auto',   'Auto-build from material slot names', 'SHADERFX', 1),
        ],
        default='MANUAL',
    )
    bpy.types.WindowManager.pbr_auto_folder   = StringProperty(name="Textures Folder", subtype='DIR_PATH', default="")
    bpy.types.WindowManager.pbr_auto_mode     = EnumProperty(
        name="Folder Mode",
        items=[
            ('FLAT',    'Flat',       'All textures in one folder'),
            ('SUBDIR',  'Subfolders', 'Each material has its own subfolder named after it'),
        ],
        default='FLAT',
    )
    bpy.types.WindowManager.pbr_auto_on_exist = EnumProperty(
        name="If Layer Exists",
        items=[
            ('UPDATE',  'Update',  'Repopulate paths, keep manual tweaks'),
            ('REBUILD', 'Rebuild', 'Delete and recreate the layer from scratch'),
            ('SKIP',    'Skip',    'Leave existing layers untouched'),
        ],
        default='UPDATE',
    )

def unregister():
    for c in reversed(classes):
        try: bpy.utils.unregister_class(c)
        except Exception: pass
    try: del bpy.types.Material.pbr_props
    except Exception: pass
    for prop in ('pbr_ui_state','pbr_mode','pbr_auto_folder',
                 'pbr_auto_mode','pbr_auto_on_exist'):
        try: delattr(bpy.types.WindowManager, prop)
        except Exception: pass

if __name__ == "__main__": register()
