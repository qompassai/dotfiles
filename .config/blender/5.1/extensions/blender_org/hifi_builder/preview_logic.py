import bpy, math
from mathutils import Euler
from .utils import PREVIEW_PREFIX, get_unit_scale, cleanup_previews, to_internal
from .gen_group_1 import *
from .gen_group_2 import *
from .gen_group_3 import *
from .gen_group_4 import *
from .gen_group_5 import *
from .gen_group_6 import *
from .gen_group_7 import *
from .gen_group_8 import *
from .gen_group_9 import *
from .gen_group_10 import *
from .gen_group_11 import *
from .gen_group_12 import *

def update_preview(context_scene):
    props = context_scene.hifi_props
    gen = props.generator_type
    sc = get_unit_scale(props.unit_type)
    if sc == 0: sc = 1.0
    
    existing_matrix = None
    for obj in context_scene.objects:
        if obj.name.lower().startswith(PREVIEW_PREFIX.lower()):
            existing_matrix = obj.matrix_world.copy()
            break
            
    cleanup_previews()
    
    preview = None
    params = {}
    
    if gen == 'NONE':
        return None, {}
        
    try:
        if gen == 'WALL': preview, params = gen_wall(props, sc)
        elif gen == 'FLOOR': preview, params = gen_floor(props, sc)
        elif gen == 'CEILING': preview, params = gen_ceiling(props, sc)
        elif gen == 'PILLAR': preview, params = gen_pillar(props, sc)
        elif gen == 'DOME_1': preview, params = gen_dome_1_shell(props, sc)
        elif gen == 'DOME_2': preview, params = gen_dome_2_shell(props, sc)
        elif gen == 'STAIRS': preview, params = gen_stairs(props, sc)
        elif gen == 'RAMP': preview, params = gen_ramp(props, sc)
        elif gen == 'WINDOW_FLAT': preview, params = gen_window_frame_flat(props, sc)
        elif gen == 'WINDOW_CIRCULAR': preview, params = gen_window_frame_circular(props, sc)
        elif gen == 'DOOR_FLAT': preview, params = gen_door_frame_flat(props, sc)
        elif gen == 'BALCONY': preview, params = gen_balcony(props, sc)
        elif gen == 'FENCE': preview, params = gen_fence(props, sc)
        elif gen == 'CIRCULAR_FLOOR': preview, params = gen_circular_floor(props, sc)
        elif gen == 'CIRCULAR_CEILING': preview, params = gen_circular_ceiling(props, sc)
        elif gen == 'CIRCULAR_WALL': preview, params = gen_circular_wall(props, sc)
        elif gen == 'MOON': preview, params = gen_moon(props, sc)
        elif gen == 'STAR': preview, params = gen_star(props, sc)
        elif gen == 'PIPE': preview, params = gen_pipe(props, sc)
        elif gen == 'PIPE_L': preview, params = gen_pipe_l(props, sc)
        elif gen == 'PIPE_U': preview, params = gen_pipe_u(props, sc)
        elif gen == 'PIPE_45': preview, params = gen_pipe_45(props, sc)
        elif gen == 'GTA_STATUE': preview, params = gen_gta_statue(props, sc)
        elif gen == 'CEILING_FAN': preview, params = gen_ceiling_fan(props, sc)
        elif gen == 'TOILET': preview, params = gen_toilet(props, sc)
        elif gen == 'OFFICE_SINKS': preview, params = gen_office_sinks(props, sc)
        elif gen == 'OFFICE_SHOWER': preview, params = gen_office_shower(props, sc)
        elif gen == 'BILLBOARD': preview, params = gen_billboard(props, sc)
        elif gen == 'CABLE': preview, params = gen_procedural_cable(props, sc)
    except Exception as e:
        cleanup_previews()
        return None, {}

    if preview:
        prefix = PREVIEW_PREFIX.lower()

        def process_and_transform(o):
            try:
                if o.name.lower().startswith(prefix):
                    o.name = o.name.lower()
                else:
                    raw_name = o.name.replace("HIFI_PREV_", "").replace("hifi_prev_", "").replace("HIFI_", "").replace("hifi_", "")
                    o.name = f"{prefix}{raw_name}".lower()

                if existing_matrix:
                    o.matrix_world = existing_matrix
            except:
                pass

        if isinstance(preview, list):
            for obj in preview:
                if obj: process_and_transform(obj)
        else:
            process_and_transform(preview)

    return preview, params
