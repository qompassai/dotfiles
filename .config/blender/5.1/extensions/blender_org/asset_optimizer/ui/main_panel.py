import bpy
from bpy.types import Panel
from ..utils import helpers


class VIEW3D_PT_vr_asset_optimizer(Panel):
    """Main panel for Game Asset Optimizer"""
    bl_label = "Game Asset Optimizer"
    bl_idname = "VIEW3D_PT_vr_asset_optimizer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Assets"
    bl_context = "objectmode"

    @classmethod
    def poll(cls, context):
        """Show panel when in object mode"""
        return True

    def draw(self, context):
        """Draw the panel UI"""
        layout = self.layout
        scene = context.scene
        props = scene.vr_asset_optimizer
        
        # Header with icon
        row = layout.row()
        row.label(text="Game Asset Optimization Toolkit", icon='SCENE_DATA')
        
        layout.separator()
        
        # Selection info
        box = layout.box()
        mesh_count = helpers.get_selected_mesh_count(context)
        
        if mesh_count == 0:
            box.label(text="No mesh objects selected", icon='ERROR')
        else:
            col = box.column(align=True)
            col.label(text=f"Selected: {mesh_count} mesh object{'s' if mesh_count != 1 else ''}", icon='OBJECT_DATA')
            
            poly_count = helpers.get_total_poly_count(context)
            vert_count = helpers.get_total_vertex_count(context)
            
            col.label(text=f"Polygons: {helpers.format_number(poly_count)}")
            col.label(text=f"Vertices: {helpers.format_number(vert_count)}")
        
        layout.separator()
        
        # Quick Batch Optimization
        box = layout.box()
        box.label(text="Quick Batch Optimization", icon='SORTSIZE')
        
        col = box.column(align=True)
        col.scale_y = 1.3
        
        # Preset buttons
        row = col.row(align=True)
        op = row.operator("mesh.batch_optimize", text="CAD Import", icon='IMPORT')
        op.optimization_preset = 'CAD_IMPORT'
        
        op = row.operator("mesh.batch_optimize", text="Game Asset", icon='MESH_CUBE')
        op.optimization_preset = 'GAME_ASSET'
        
        row = col.row(align=True)
        op = row.operator("mesh.batch_optimize", text="VR Optimized", icon='VIEW_CAMERA')
        op.optimization_preset = 'VR_OPTIMIZED'
        
        op = row.operator("mesh.batch_optimize", text="Custom", icon='SETTINGS')
        op.optimization_preset = 'CUSTOM'
        
        layout.separator()
        
        # Target Engine
        box = layout.box()
        box.label(text="Target Engine", icon='WORLD')
        box.prop(props, "target_engine", expand=True)
        
        layout.separator()
        
        # Individual Tools
        box = layout.box()
        box.label(text="Individual Tools", icon='TOOL_SETTINGS')
        
        # Vertex Merge
        col = box.column(align=True)
        col.operator("mesh.smart_vertex_merge", text="Merge Vertices", icon='AUTOMERGE_ON')
        
        # Mesh Decimation
        col.operator("mesh.auto_decimate", text="Decimate Mesh", icon='MOD_DECIM')
        
        # Dual UV Unwrap
        col.operator("mesh.dual_uv_unwrap", text="Dual UV Unwrap (UV0 + UV1)", icon='UV_DATA')
        
        # LOD Generation
        col.operator("mesh.generate_lods", text="Generate LOD Groups", icon='OUTLINER_OB_MESH')
        
        layout.separator()
        
        # UV Information
        if mesh_count > 0:
            box = layout.box()
            box.label(text="UV Information", icon='UV')
            
            uv_info_col = box.column(align=True)
            
            for obj in context.selected_objects:
                if obj.type == 'MESH' and helpers.has_uv_layers(obj):
                    uv_count = helpers.get_uv_layer_count(obj)
                    row = uv_info_col.row()
                    row.label(text=f"{obj.name}: {uv_count} UV layer{'s' if uv_count != 1 else ''}", 
                             icon='CHECKMARK')
        
        layout.separator()
        
        # Tips section
        box = layout.box()
        box.label(text="Tips", icon='INFO')
        col = box.column(align=True)
        col.scale_y = 0.8
        col.label(text="• CAD Import: For imported CAD models")
        col.label(text="• Game Asset: For standard game objects")
        col.label(text="• VR Optimized: Aggressive optimization")
        col.label(text="• UV0: Texturing | UV1: Lightmaps")
        col.label(text="• LODs reduce draw calls in VR")


class VIEW3D_PT_vr_asset_optimizer_advanced(Panel):
    """Advanced settings panel"""
    bl_label = "Advanced Settings"
    bl_idname = "VIEW3D_PT_vr_asset_optimizer_advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Game Assets"
    bl_parent_id = "VIEW3D_PT_vr_asset_optimizer"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """Draw advanced settings"""
        layout = self.layout
        scene = context.scene
        props = scene.vr_asset_optimizer
        
        box = layout.box()
        box.label(text="Quick Settings", icon='SETTINGS')
        box.prop(props, "quick_decimate_ratio", slider=True)
        box.prop(props, "quick_merge_distance")
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Export Recommendations", icon='EXPORT')
        
        col = box.column(align=True)
        col.scale_y = 0.8
        
        if props.target_engine == 'UNITY':
            col.label(text="Unity Export:")
            col.label(text="• Use FBX format")
            col.label(text="• Enable 'Apply Transform'")
            col.label(text="• LOD naming: Object_LOD0")
            col.label(text="• UV0 = Albedo, UV1 = Lightmap")
        else:
            col.label(text="Unreal Export:")
            col.label(text="• Use FBX format")
            col.label(text="• LOD naming: Object_LOD_0")
            col.label(text="• Enable 'Generate Lightmap UVs'")
            col.label(text="• UV0 = BaseColor, UV1 = Lightmap")


def register():
    """Register the panel"""
    bpy.utils.register_class(VIEW3D_PT_vr_asset_optimizer)
    bpy.utils.register_class(VIEW3D_PT_vr_asset_optimizer_advanced)


def unregister():
    """Unregister the panel"""
    bpy.utils.unregister_class(VIEW3D_PT_vr_asset_optimizer_advanced)
    bpy.utils.unregister_class(VIEW3D_PT_vr_asset_optimizer)
