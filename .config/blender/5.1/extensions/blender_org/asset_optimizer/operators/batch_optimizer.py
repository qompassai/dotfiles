import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, FloatProperty, EnumProperty, IntProperty


class MESH_OT_batch_optimize(Operator):
    """Batch optimize all selected objects with preset workflows"""
    bl_idname = "mesh.batch_optimize"
    bl_label = "Batch Optimize VR Assets"
    bl_description = "One-click optimization for VR - combines vertex merge, decimation, and UV unwrap"
    bl_options = {'REGISTER', 'UNDO'}

    # Preset workflows
    optimization_preset: EnumProperty(
        name="Optimization Preset",
        description="Preset optimization workflow",
        items=[
            ('CAD_IMPORT', "CAD Import", "Optimize imported CAD models (merge vertices, decimate, dual UV)"),
            ('GAME_ASSET', "Game Asset", "Convert models to game-ready assets (decimate, dual UV, LODs)"),
            ('VR_OPTIMIZED', "VR Optimized", "Aggressive optimization for VR (heavy decimate, LODs, lightmap UV)"),
            ('CUSTOM', "Custom", "Custom settings")
        ],
        default='CAD_IMPORT'
    )
    
    # Enable/disable steps
    enable_vertex_merge: BoolProperty(
        name="Merge Vertices",
        description="Merge vertices by distance",
        default=True
    )
    
    enable_decimation: BoolProperty(
        name="Decimate Mesh",
        description="Apply mesh decimation",
        default=True
    )
    
    enable_dual_uv: BoolProperty(
        name="Dual UV Unwrap",
        description="Generate UV0 and UV1",
        default=True
    )
    
    enable_lod_generation: BoolProperty(
        name="Generate LODs",
        description="Generate LOD levels",
        default=False
    )
    
    # Quick settings
    merge_distance: FloatProperty(
        name="Merge Distance",
        description="Vertex merge distance",
        default=0.0001,
        min=0.00001,
        max=1.0,
        precision=5
    )
    
    decimate_ratio: FloatProperty(
        name="Decimate Ratio",
        description="Target poly count ratio",
        default=0.5,
        min=0.01,
        max=1.0
    )
    
    lod_count: IntProperty(
        name="LOD Count",
        description="Number of LOD levels",
        default=3,
        min=2,
        max=8
    )
    
    target_engine: EnumProperty(
        name="Target Engine",
        description="Target game engine",
        items=[
            ('UNITY', "Unity", "Unity"),
            ('UNREAL', "Unreal", "Unreal Engine")
        ],
        default='UNITY'
    )

    @classmethod
    def poll(cls, context):
        """Check if the operator can be executed"""
        return (context.mode == 'OBJECT' and
                context.selected_objects and
                any(obj.type == 'MESH' for obj in context.selected_objects))

    def apply_preset(self):
        """Apply preset values"""
        if self.optimization_preset == 'CAD_IMPORT':
            self.enable_vertex_merge = True
            self.enable_decimation = True
            self.enable_dual_uv = True
            self.enable_lod_generation = False
            self.merge_distance = 0.0001
            self.decimate_ratio = 0.6
            
        elif self.optimization_preset == 'GAME_ASSET':
            self.enable_vertex_merge = True
            self.enable_decimation = True
            self.enable_dual_uv = True
            self.enable_lod_generation = True
            self.merge_distance = 0.0001
            self.decimate_ratio = 0.5
            self.lod_count = 3
            
        elif self.optimization_preset == 'VR_OPTIMIZED':
            self.enable_vertex_merge = True
            self.enable_decimation = True
            self.enable_dual_uv = True
            self.enable_lod_generation = True
            self.merge_distance = 0.0001
            self.decimate_ratio = 0.3
            self.lod_count = 4

    def execute(self, context):
        """Execute the batch optimization"""
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not mesh_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        self.report({'INFO'}, f"Batch optimizing {len(mesh_objects)} objects with preset: {self.optimization_preset}")
        
        # Step 1: Merge vertices
        if self.enable_vertex_merge:
            self.report({'INFO'}, "Step 1/4: Merging vertices...")
            try:
                bpy.ops.mesh.smart_vertex_merge('EXEC_DEFAULT',
                    merge_distance=self.merge_distance,
                    use_sharp_edge_from_normals=True,
                    remove_doubles=True,
                    dissolve_degenerate=True,
                    delete_loose=True,
                    recalculate_normals=True
                )
            except Exception as e:
                self.report({'WARNING'}, f"Vertex merge failed: {str(e)}")
        
        # Step 2: Decimate mesh
        if self.enable_decimation:
            self.report({'INFO'}, "Step 2/4: Decimating mesh...")
            try:
                bpy.ops.mesh.auto_decimate('EXEC_DEFAULT',
                    ratio=self.decimate_ratio,
                    use_weighted_normals=True,
                    use_auto_smooth=True,
                    apply_modifiers=True
                )
            except Exception as e:
                self.report({'WARNING'}, f"Decimation failed: {str(e)}")
        
        # Step 3: Generate dual UV maps
        if self.enable_dual_uv:
            self.report({'INFO'}, "Step 3/4: Generating dual UV maps...")
            try:
                bpy.ops.mesh.dual_uv_unwrap('EXEC_DEFAULT',
                    uv0_enabled=True,
                    uv0_method='SMART',
                    uv0_pack_islands=True,
                    uv1_enabled=True,
                    uv1_method='LIGHTMAP',
                    multi_object_mode=True
                )
            except Exception as e:
                self.report({'WARNING'}, f"UV unwrap failed: {str(e)}")
        
        # Step 4: Generate LODs
        if self.enable_lod_generation:
            self.report({'INFO'}, "Step 4/4: Generating LOD levels...")
            try:
                bpy.ops.mesh.generate_lods('EXEC_DEFAULT',
                    lod_count=self.lod_count,
                    target_engine=self.target_engine,
                    use_progressive=True,
                    use_weighted_normals=True,
                    create_collection=True
                )
            except Exception as e:
                self.report({'WARNING'}, f"LOD generation failed: {str(e)}")
        
        self.report({'INFO'}, f"SUCCESS: Batch optimization complete!")
        return {'FINISHED'}

    def draw(self, context):
        """Draw the operator properties in the UI"""
        layout = self.layout
        
        # Preset selection
        box = layout.box()
        box.label(text="Optimization Preset", icon='PRESET')
        box.prop(self, "optimization_preset", text="")
        
        if self.optimization_preset != 'CUSTOM':
            box.label(text="Click OK to apply preset", icon='INFO')
        
        layout.separator()
        
        # Steps to perform
        box = layout.box()
        box.label(text="Optimization Steps", icon='SORTSIZE')
        box.prop(self, "enable_vertex_merge")
        box.prop(self, "enable_decimation")
        box.prop(self, "enable_dual_uv")
        box.prop(self, "enable_lod_generation")
        
        layout.separator()
        
        # Quick settings (only for custom preset)
        if self.optimization_preset == 'CUSTOM':
            box = layout.box()
            box.label(text="Quick Settings", icon='SETTINGS')
            
            if self.enable_vertex_merge:
                box.prop(self, "merge_distance")
            
            if self.enable_decimation:
                box.prop(self, "decimate_ratio", slider=True)
            
            if self.enable_lod_generation:
                box.prop(self, "lod_count")
                box.prop(self, "target_engine")

    def invoke(self, context, event):
        """Show dialog before executing"""
        # Apply preset defaults
        self.apply_preset()
        return context.window_manager.invoke_props_dialog(self, width=400)


def register():
    """Register the operator"""
    bpy.utils.register_class(MESH_OT_batch_optimize)


def unregister():
    """Unregister the operator"""
    bpy.utils.unregister_class(MESH_OT_batch_optimize)
