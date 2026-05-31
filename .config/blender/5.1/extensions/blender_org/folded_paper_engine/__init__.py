from .folded_paper_engine import bl_info as _bl_info
from .folded_paper_engine import register as _inner_register, unregister as _inner_unregister

bl_info = _bl_info

def register():
  _inner_register()

def unregister():
  _inner_unregister()
