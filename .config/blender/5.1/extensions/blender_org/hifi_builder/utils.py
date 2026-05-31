import bpy, sys, os, math
import addon_utils
from datetime import datetime

PREVIEW_PREFIX = "hifi_prev_"
GEN_PREFIX = "hifi_"
APPLY_LOCK = {"locked": False}

def get_unit_scale(unit_type):
    if unit_type == 'METERS': return 1.0
    elif unit_type == 'CENTIMETERS': return 0.01
    elif unit_type == 'MILLIMETERS': return 0.001
    elif unit_type == 'FEET': return 0.3048
    elif unit_type == 'INCHES': return 0.0254
    return 1.0

def to_internal(val, scale_factor):
    try: return float(val) * scale_factor
    except: return 0.0

def cleanup_previews():
    objs = [o for o in bpy.data.objects if o.name.startswith(PREVIEW_PREFIX)]
    for o in objs:
        try: bpy.data.objects.remove(o, do_unlink=True)
        except: pass

def apply_transform(obj):
    try:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try: bpy.ops.object.mode_set(mode='OBJECT')
        except: pass
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        obj.select_set(False)
    except: pass

def save_params_to_object(obj, params):
    for k, v in params.items():
        try: obj[f"hifi_{k}"] = v
        except: pass
    try:
        obj["hifi_saved_loc_x"] = obj.location.x; obj["hifi_saved_loc_y"] = obj.location.y; obj["hifi_saved_loc_z"] = obj.location.z
        obj["hifi_saved_rot_x_deg"] = math.degrees(obj.rotation_euler.x); obj["hifi_saved_rot_y_deg"] = math.degrees(obj.rotation_euler.y); obj["hifi_saved_rot_z_deg"] = math.degrees(obj.rotation_euler.z)
        obj["hifi_saved_scale_x"] = obj.scale.x; obj["hifi_saved_scale_y"] = obj.scale.y; obj["hifi_saved_scale_z"] = obj.scale.z
    except: pass

def is_hifi_object(obj):
    try:
        if "hifi_gen_type" in obj: return True
        for k in obj.keys():
            if isinstance(k, str) and k.startswith("hifi_"): return True
    except: pass
    return False

def read_hifi_params_from_object(obj):
    d = {}
    try:
        for k in obj.keys():
            if isinstance(k, str) and k.startswith("hifi_"): d[k[5:]] = obj.get(k)
    except: pass
    return d

def apply_boolean(target_obj, cutter_obj, operation='DIFFERENCE', modname_prefix='hifi_bool'):
    try:
        try: bpy.ops.object.mode_set(mode='OBJECT')
        except: pass
        bpy.context.view_layer.objects.active = target_obj
        mod = target_obj.modifiers.new(name=modname_prefix, type='BOOLEAN')
        mod.operation = operation
        mod.object = cutter_obj
        mod.solver = 'EXACT' 
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return True
    except: return False

def create_arch_shape(width, height, depth, res, base_z=0.0, offset_x=0.0, offset_y=0.0):
    r = width / 2.0
    straight_h = max(height - r, 0.0)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(offset_x, offset_y, base_z + straight_h/2.0))
    cube = bpy.context.active_object
    cube.scale = (width, depth, straight_h)
    apply_transform(cube)
    
    if r > 0.001:
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=res, location=(offset_x, offset_y, base_z + straight_h))
        cyl = bpy.context.active_object
        cyl.rotation_euler.x = math.radians(90)
        apply_transform(cyl)
        
        bpy.ops.object.select_all(action='DESELECT')
        cube.select_set(True)
        cyl.select_set(True)
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.join()
    return cube

def get_dynamic_addon_info():
    name = "HiFi Architecture Builder"
    version = "Unknown"
    author = "Malik Nomi"
    try:
        for mod in addon_utils.modules():
            if mod.__name__ == __package__:
                info = mod.bl_info
                name = info.get('name', name)
                v = info.get('version', (0, 0, 0))
                version = ".".join(str(x) for x in v)
                author = info.get('author', author)
                break
    except: pass
    return name, version, author

def hifi_orphan_cleanup():
    data_collections = [
        ('Actions', bpy.data.actions), ('Armatures', bpy.data.armatures), 
        ('Brushes', bpy.data.brushes), ('Cameras', bpy.data.cameras), 
        ('Curves', bpy.data.curves), ('Fonts', bpy.data.fonts), 
        ('Grease Pencils', bpy.data.grease_pencils), ('Images', bpy.data.images), 
        ('Lattices', bpy.data.lattices), ('Light Probes', bpy.data.lightprobes), 
        ('Lights', bpy.data.lights), ('Line Styles', bpy.data.linestyles), 
        ('Masks', bpy.data.masks), ('Materials', bpy.data.materials), 
        ('Meshes', bpy.data.meshes), ('Metaballs', bpy.data.metaballs), 
        ('Movie Clips', bpy.data.movieclips), ('Node Groups', bpy.data.node_groups), 
        ('Objects', bpy.data.objects), ('Paint Curves', bpy.data.paint_curves), 
        ('Palettes', bpy.data.palettes), ('Particles', bpy.data.particles), 
        ('Point Clouds', bpy.data.pointclouds), ('Sounds', bpy.data.sounds), 
        ('Speakers', bpy.data.speakers), ('Texts', bpy.data.texts), 
        ('Textures', bpy.data.textures), ('Volumes', bpy.data.volumes), 
        ('Worlds', bpy.data.worlds)
    ]
    before_records = {name: set(item.name for item in col) for name, col in data_collections}
    try:
        for _ in range(10): bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    except: pass
    after_records = {name: set(item.name for item in col) for name, col in data_collections}
    
    deleted_items = {}
    total_deleted = 0
    for name in before_records:
        deleted = sorted(list(before_records[name] - after_records[name]))
        if deleted:
            deleted_items[name] = deleted
            total_deleted += len(deleted)
            
    addon_name, version, author = get_dynamic_addon_info()
    timestamp_inner = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_timestamp = datetime.now().strftime("%B_%d_%H_%M_%S")
    
    report_lines = [
        "=== HiFi Deep X-Ray Orphan Cleanup Report ===",
        f"Generated on: {timestamp_inner}", f"Addon: {addon_name}",
        f"Author: {author}", f"Version: {version}", "-" * 30,
        f"TOTAL ORPHANS PURGED: {total_deleted}", "-" * 30
    ]
    if total_deleted == 0: report_lines.append("\nProject is already clean.")
    else:
        report_lines.append("\nCategory Breakdown:")
        for cat, items in deleted_items.items(): report_lines.append(f" - {cat} deleted: {len(items)}")
        report_lines.append("\nDetailed X-Ray List:\n")
        for cat, items in deleted_items.items():
            report_lines.append(f"[{cat}]")
            for item in items: report_lines.append(f"  - {item}")
            report_lines.append("")
            
    final_report = "\n".join(report_lines)
    try:
        blend_path = bpy.data.filepath
        save_dir = os.path.join(os.path.dirname(blend_path), "HiFi Builder Reports") if blend_path else os.path.join(os.path.expanduser("~"), "HiFi Builder Reports")
        if not os.path.exists(save_dir): os.makedirs(save_dir)
        full_path = os.path.join(save_dir, f"HiFi Orphan Cleanup Report {file_timestamp}.txt")
        with open(full_path, "w", encoding="utf-8") as f: f.write(final_report)
    except: pass
