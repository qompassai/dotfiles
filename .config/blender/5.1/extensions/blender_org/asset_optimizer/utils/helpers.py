import bpy


def get_selected_mesh_count(context):
    """Get number of selected mesh objects"""
    return len([obj for obj in context.selected_objects if obj.type == 'MESH'])


def get_total_poly_count(context):
    """Get total polygon count of selected objects"""
    total = 0
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            total += len(obj.data.polygons)
    return total


def get_total_vertex_count(context):
    """Get total vertex count of selected objects"""
    total = 0
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            total += len(obj.data.vertices)
    return total


def format_number(num):
    """Format number with thousand separators"""
    if num >= 1000000:
        return f"{num/1000000:.2f}M"
    elif num >= 1000:
        return f"{num/1000:.2f}K"
    else:
        return str(num)


def has_uv_layers(obj):
    """Check if object has UV layers"""
    if obj.type == 'MESH':
        return len(obj.data.uv_layers) > 0
    return False


def get_uv_layer_count(obj):
    """Get number of UV layers"""
    if obj.type == 'MESH':
        return len(obj.data.uv_layers)
    return 0
