import bpy
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, BoolProperty, IntProperty, EnumProperty


class VRAssetOptimizerProperties(PropertyGroup):
    """Properties for VR Asset Optimizer"""
    
    # Quick access properties
    quick_decimate_ratio: FloatProperty(
        name="Decimate Ratio",
        description="Quick decimate ratio",
        default=0.5,
        min=0.01,
        max=1.0
    )
    
    quick_merge_distance: FloatProperty(
        name="Merge Distance",
        description="Quick merge distance",
        default=0.0001,
        min=0.00001,
        max=1.0,
        precision=5
    )
    
    target_engine: EnumProperty(
        name="Target Engine",
        description="Target game engine for export",
        items=[
            ('UNITY', "Unity", "Unity Engine"),
            ('UNREAL', "Unreal", "Unreal Engine")
        ],
        default='UNITY'
    )
    
    show_advanced: BoolProperty(
        name="Show Advanced",
        description="Show advanced options",
        default=False
    )


def register():
    """Register properties"""
    bpy.utils.register_class(VRAssetOptimizerProperties)
    bpy.types.Scene.vr_asset_optimizer = bpy.props.PointerProperty(type=VRAssetOptimizerProperties)


def unregister():
    """Unregister properties"""
    del bpy.types.Scene.vr_asset_optimizer
    bpy.utils.unregister_class(VRAssetOptimizerProperties)
