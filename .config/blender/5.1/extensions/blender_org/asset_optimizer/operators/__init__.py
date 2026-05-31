from . import mesh_decimation
from . import lod_generator
from . import dual_uv_unwrap
from . import vertex_merge
from . import batch_optimizer

def register():
    """Register all operators"""
    mesh_decimation.register()
    lod_generator.register()
    dual_uv_unwrap.register()
    vertex_merge.register()
    batch_optimizer.register()

def unregister():
    """Unregister all operators"""
    batch_optimizer.unregister()
    vertex_merge.unregister()
    dual_uv_unwrap.unregister()
    lod_generator.unregister()
    mesh_decimation.unregister()
