import bpy
from bpy.types import Operator
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty


class MESH_OT_generate_lods(Operator):
    """Generate LOD (Level of Detail) groups or collections for VR optimization"""
    bl_idname = "mesh.generate_lods"
    bl_label = "Generate LOD Groups"
    bl_description = "Create multiple LOD levels with progressive decimation for Unity/Unreal Engine"
    bl_options = {'REGISTER', 'UNDO'}

    # LOD settings
    lod_count: IntProperty(
        name="LOD Levels",
        description="Number of LOD levels to generate (including LOD0)",
        default=4,
        min=2,
        max=8
    )
    
    target_engine: EnumProperty(
        name="Target Engine",
        description="Target game engine for LOD setup",
        items=[
            ('UNITY', "Unity", "Unity LOD Group format"),
            ('UNREAL', "Unreal", "Unreal Engine LOD format"),
            ('COLLECTION', "Collection", "Blender collection-based LODs")
        ],
        default='UNITY'
    )
    
    # Decimation progression
    lod0_ratio: FloatProperty(
        name="LOD0 Ratio",
        description="LOD0 is the original mesh (1.0 = 100%)",
        default=1.0,
        min=0.9,
        max=1.0
    )
    
    lod1_ratio: FloatProperty(
        name="LOD1 Ratio",
        description="Ratio for LOD1",
        default=0.6,
        min=0.1,
        max=1.0
    )
    
    lod2_ratio: FloatProperty(
        name="LOD2 Ratio",
        description="Ratio for LOD2",
        default=0.3,
        min=0.05,
        max=1.0
    )
    
    lod3_ratio: FloatProperty(
        name="LOD3 Ratio",
        description="Ratio for LOD3",
        default=0.1,
        min=0.01,
        max=1.0
    )
    
    lod4_ratio: FloatProperty(
        name="LOD4 Ratio",
        description="Ratio for LOD4",
        default=0.05,
        min=0.01,
        max=0.5
    )
    
    # Progressive settings
    use_progressive: BoolProperty(
        name="Auto Progressive",
        description="Automatically calculate progressive ratios",
        default=True
    )
    
    progressive_factor: FloatProperty(
        name="Progressive Factor",
        description="Factor for automatic progression (0.5 = halve each level)",
        default=0.5,
        min=0.1,
        max=0.9
    )
    
    # Modifiers
    use_weighted_normals: BoolProperty(
        name="Add Weighted Normals",
        description="Add weighted normal modifier to each LOD",
        default=True
    )
    
    use_auto_smooth: BoolProperty(
        name="Auto Smooth",
        description="Enable auto smooth on all LODs",
        default=True
    )
    
    # Decimation settings
    decimate_type: EnumProperty(
        name="Decimate Type",
        description="Decimation algorithm to use",
        items=[
            ('COLLAPSE', "Collapse", "Merge vertices together (best for organic)"),
            ('UNSUBDIV', "Un-Subdivide", "Remove subdivision levels"),
            ('DISSOLVE', "Planar", "Dissolve geometry based on planar angle (best for CAD)")
        ],
        default='COLLAPSE'
    )
    
    planar_angle: FloatProperty(
        name="Planar Angle",
        description="Angle limit for planar decimation",
        default=0.0872665,  # 5 degrees
        min=0.0,
        max=3.14159,
        subtype='ANGLE'
    )
    
    # Naming
    suffix_format: EnumProperty(
        name="Suffix Format",
        description="Naming convention for LOD objects",
        items=[
            ('UNDERSCORE', "Object_LOD0", "Unity style: Object_LOD0"),
            ('UNREAL', "Object_LOD_0", "Unreal style: Object_LOD_0"),
            ('CUSTOM', "Object.LOD0", "Custom style: Object.LOD0")
        ],
        default='UNDERSCORE'
    )
    
    create_collection: BoolProperty(
        name="Create Collection",
        description="Create a collection to organize LOD objects",
        default=True
    )

    @classmethod
    def poll(cls, context):
        """Check if the operator can be executed"""
        return (context.mode == 'OBJECT' and
                context.selected_objects and
                any(obj.type == 'MESH' for obj in context.selected_objects))

    def get_lod_ratios(self):
        """Calculate LOD ratios based on settings"""
        if self.use_progressive:
            ratios = [1.0]  # LOD0 is always 100%
            current_ratio = 1.0
            for i in range(1, self.lod_count):
                current_ratio *= self.progressive_factor
                ratios.append(max(0.01, current_ratio))
            return ratios
        else:
            # Use manual ratios
            return [
                self.lod0_ratio,
                self.lod1_ratio,
                self.lod2_ratio,
                self.lod3_ratio,
                self.lod4_ratio
            ][:self.lod_count]

    def get_lod_name(self, base_name, lod_level):
        """Generate LOD name based on suffix format"""
        if self.suffix_format == 'UNDERSCORE':
            return f"{base_name}_LOD{lod_level}"
        elif self.suffix_format == 'UNREAL':
            return f"{base_name}_LOD_{lod_level}"
        else:  # CUSTOM
            return f"{base_name}.LOD{lod_level}"

    def execute(self, context):
        """Execute the LOD generation"""
        # Filter out non-mesh objects (ignore empties, cameras, lights, etc.)
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not mesh_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        # Get LOD ratios
        lod_ratios = self.get_lod_ratios()
        
        self.report({'INFO'}, f"Generating {self.lod_count} LOD levels for {len(mesh_objects)} objects...")
        
        processed_count = 0
        
        for original_obj in mesh_objects:
            try:
                # Store original selection
                original_poly_count = len(original_obj.data.polygons)
                base_name = original_obj.name
                
                # Create collection for this object's LODs if requested
                if self.create_collection:
                    collection_name = f"{base_name}_LODs"
                    if collection_name in bpy.data.collections:
                        lod_collection = bpy.data.collections[collection_name]
                    else:
                        lod_collection = bpy.data.collections.new(collection_name)
                        context.scene.collection.children.link(lod_collection)
                
                # For Unity, rename original object first to free up the base name
                if self.target_engine == 'UNITY':
                    original_obj.name = f"{base_name}_temp"
                
                # Create root empty for Unity LOD Group (only for Unity)
                lod_root = None
                if self.target_engine == 'UNITY':
                    lod_root = bpy.data.objects.new(base_name, None)
                    lod_root.empty_display_type = 'PLAIN_AXES'
                    lod_root.empty_display_size = 1.0
                    
                    if self.create_collection:
                        lod_collection.objects.link(lod_root)
                    else:
                        context.collection.objects.link(lod_root)
                    
                    # Copy original transform
                    lod_root.location = original_obj.location
                    lod_root.rotation_euler = original_obj.rotation_euler
                    lod_root.scale = original_obj.scale
                
                lod_objects = []
                lod0_object = None
                
                # Generate each LOD level
                for lod_level in range(self.lod_count):
                    ratio = lod_ratios[lod_level]
                    
                    # For LOD0, rename original or duplicate
                    if lod_level == 0 and ratio >= 0.99:
                        # Rename original as LOD0
                        lod_obj = original_obj
                        lod_obj.name = self.get_lod_name(base_name, lod_level)
                    else:
                        # Duplicate the original object
                        lod_obj = original_obj.copy()
                        lod_obj.data = original_obj.data.copy()
                        lod_obj.name = self.get_lod_name(base_name, lod_level)
                        context.collection.objects.link(lod_obj)
                    
                    # Store LOD0 as parent reference
                    if lod_level == 0:
                        lod0_object = lod_obj
                    
                    # Move to LOD collection
                    if self.create_collection:
                        if lod_obj.name in context.collection.objects:
                            context.collection.objects.unlink(lod_obj)
                        if lod_obj.name not in lod_collection.objects:
                            lod_collection.objects.link(lod_obj)
                    
                    # Apply decimation if not LOD0 or if LOD0 ratio < 1.0
                    if lod_level > 0 or ratio < 1.0:
                        # Add decimate modifier
                        decimate_mod = lod_obj.modifiers.new(name=f"Decimate_LOD{lod_level}", type='DECIMATE')
                        decimate_mod.decimate_type = self.decimate_type
                        
                        if self.decimate_type == 'COLLAPSE':
                            decimate_mod.ratio = ratio
                            decimate_mod.use_collapse_triangulate = True
                        elif self.decimate_type == 'DISSOLVE':
                            decimate_mod.angle_limit = self.planar_angle
                            decimate_mod.use_dissolve_boundaries = False
                            # For planar, we still need to reduce complexity, so we apply multiple times
                            # based on the target ratio
                        elif self.decimate_type == 'UNSUBDIV':
                            # Calculate iterations based on target ratio
                            decimate_mod.iterations = max(1, int((1.0 - ratio) * 5))
                        
                        # Apply the modifier
                        context.view_layer.objects.active = lod_obj
                        bpy.ops.object.select_all(action='DESELECT')
                        lod_obj.select_set(True)
                        bpy.ops.object.modifier_apply(modifier=decimate_mod.name)
                        
                        # For planar decimation, apply additional collapse decimation to reach target ratio
                        if self.decimate_type == 'DISSOLVE':
                            current_poly_count = len(lod_obj.data.polygons)
                            target_poly_count = int(original_poly_count * ratio)
                            
                            if current_poly_count > target_poly_count:
                                collapse_ratio = target_poly_count / current_poly_count
                                collapse_mod = lod_obj.modifiers.new(name=f"Collapse_LOD{lod_level}", type='DECIMATE')
                                collapse_mod.decimate_type = 'COLLAPSE'
                                collapse_mod.ratio = collapse_ratio
                                collapse_mod.use_collapse_triangulate = True
                                bpy.ops.object.modifier_apply(modifier=collapse_mod.name)
                    
                    # Parent LODs based on target engine
                    if self.target_engine == 'UNITY' and lod_root:
                        # For Unity: Parent all LODs to root empty
                        lod_obj.parent = lod_root
                        lod_obj.matrix_parent_inverse = lod_root.matrix_world.inverted()
                    elif lod_level > 0 and lod0_object:
                        # For Unreal/Collection: Parent LOD1+ to LOD0
                        lod_obj.parent = lod0_object
                        lod_obj.matrix_parent_inverse = lod0_object.matrix_world.inverted()
                    
                    # Add weighted normals if requested
                    if self.use_weighted_normals and lod_level > 0:
                        wn_mod = lod_obj.modifiers.new(name="WeightedNormal", type='WEIGHTED_NORMAL')
                        wn_mod.weight = 100
                        wn_mod.mode = 'FACE_AREA'
                        wn_mod.keep_sharp = True
                    
                    # Set auto smooth
                    if self.use_auto_smooth:
                        if bpy.app.version < (4, 1, 0):
                            lod_obj.data.use_auto_smooth = True
                            lod_obj.data.auto_smooth_angle = 0.523599  # 30 degrees
                    
                    # Shade smooth
                    bpy.ops.object.shade_smooth()
                    
                    lod_objects.append(lod_obj)
                    
                    # Report poly count
                    new_poly_count = len(lod_obj.data.polygons)
                    reduction = ((original_poly_count - new_poly_count) / original_poly_count) * 100
                    self.report({'INFO'}, 
                               f"  LOD{lod_level}: {new_poly_count} polys ({reduction:.1f}% reduction)")
                
                # Add metadata for Unity/Unreal
                if self.target_engine == 'UNITY':
                    # Store LOD info in custom properties
                    for i, lod_obj in enumerate(lod_objects):
                        lod_obj["LOD_Level"] = i
                        lod_obj["LOD_Group"] = base_name
                
                processed_count += 1
                
            except Exception as e:
                self.report({'WARNING'}, f"Failed on {original_obj.name}: {str(e)}")
                continue
        
        self.report({'INFO'}, f"SUCCESS: Generated LODs for {processed_count} objects! (LOD1-{self.lod_count-1} parented to LOD0)")
        return {'FINISHED'}

    def draw(self, context):
        """Draw the operator properties in the UI"""
        layout = self.layout
        
        # Target engine
        box = layout.box()
        box.label(text="Target Engine", icon='WORLD')
        box.prop(self, "target_engine", expand=True)
        
        # LOD settings
        box = layout.box()
        box.label(text="LOD Settings", icon='OUTLINER_OB_MESH')
        box.prop(self, "lod_count")
        box.prop(self, "use_progressive")
        
        if self.use_progressive:
            box.prop(self, "progressive_factor", slider=True)
        else:
            col = box.column(align=True)
            for i in range(min(self.lod_count, 5)):
                col.prop(self, f"lod{i}_ratio", slider=True)
        
        # Decimation settings
        box = layout.box()
        box.label(text="Decimation Settings", icon='MOD_DECIM')
        box.prop(self, "decimate_type")
        
        if self.decimate_type == 'DISSOLVE':
            box.prop(self, "planar_angle")
            box.label(text="Note: Planar + Collapse for target ratio", icon='INFO')
        
        # Modifiers
        box = layout.box()
        box.label(text="Modifiers", icon='MODIFIER')
        box.prop(self, "use_weighted_normals")
        box.prop(self, "use_auto_smooth")
        
        # Organization
        box = layout.box()
        box.label(text="Organization", icon='OUTLINER')
        box.prop(self, "suffix_format")
        box.prop(self, "create_collection")

    def invoke(self, context, event):
        """Show dialog before executing"""
        return context.window_manager.invoke_props_dialog(self, width=450)


def register():
    """Register the operator"""
    bpy.utils.register_class(MESH_OT_generate_lods)


def unregister():
    """Unregister the operator"""
    bpy.utils.unregister_class(MESH_OT_generate_lods)
