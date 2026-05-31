"""
TexOps - Texture Operations Addon
"""

import bpy
import importlib

# Import submodules
from . import core
from . import image_tools
from . import rgba_toggles
from . import channel_packer
from . import bit_packer
from . import resolution_packer
from . import map_converter
from . import seamless
from . import dilation
from . import pbr_validator
from . import rasterizer
from . import sdf
from . import msdf
from . import csm
from . import unpacker

modules = (
    core,
    image_tools,
    rgba_toggles,
    channel_packer,
    bit_packer,
    resolution_packer,
    map_converter,
    seamless,
    dilation,
    pbr_validator,
    rasterizer,
    sdf,
    msdf,
    csm,
    unpacker,
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()