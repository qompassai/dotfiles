import bpy
from bpy.types import Operator
from bpy.props import FloatProperty, BoolProperty, IntProperty, EnumProperty


class MESH_OT_auto_decimate(Operator):
    """Automated mesh decimation with weighted normals and smooth shading for CAD model optimization"""
    bl_idname = "mesh.auto_decimate"
    bl_label = "Auto Decimate Mesh"
    bl_description = "Apply decimate modifier with weighted normal and auto smooth for optimized CAD models"
    bl_options = {'REGISTER', 'UNDO'}

    # Decimation settings
    ratio: FloatProperty(
        name="Decimate Ratio",
        description="Ratio of faces to keep (0.1 = 10% of original)",
        default=0.5,
        min=0.01,
        max=1.0,
        precision=3
    )
    
    decimate_type: EnumProperty(
        name="Decimate Type",
        description="Type of decimation algorithm",
        items=[
            ('COLLAPSE', "Collapse", "Merge vertices together"),
            ('UNSUBDIV', "Un-Subdivide", "Remove subdivision levels"),
            ('DISSOLVE', "Planar", "Dissolve geometry based on planar angle")
        ],
        default='COLLAPSE'
    )
    
    # Angle for planar decimation
    angle_limit: FloatProperty(
        name="Angle Limit",
        description="Angle limit for planar decimation",
        default=0.0872665,  # 5 degrees
        min=0.0,
        max=3.14159,
        subtype='ANGLE'
    )
    
    # Weighted normal settings
    use_weighted_normals: BoolProperty(
        name="Add Weighted Normals",
        description="Add weighted normal modifier for better shading",
        default=True
    )
    
    weighted_mode: EnumProperty(
        name="Weighting Mode",
        description="How to weight face normals",
        items=[
            ('FACE_AREA', "Face Area", "Weight by face area"),
            ('CORNER_ANGLE', "Corner Angle", "Weight by corner angle"),
            ('FACE_AREA_WITH_ANGLE', "Area & Angle", "Weight by both face area and corner angle")
        ],
        default='FACE_AREA'
    )
    
    # Auto smooth settings
    use_auto_smooth: BoolProperty(
        name="Auto Smooth",
        description="Enable auto smooth with custom angle",
        default=True
    )
    
    smooth_angle: FloatProperty(
        name="Smooth Angle",
        description="Angle for auto smooth",
        default=0.523599,  # 30 degrees
        min=0.0,
        max=3.14159,
        subtype='ANGLE'
    )
    
    # Additional options
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply all modifiers after adding them",
        default=False
    )
    
    triangulate: BoolProperty(
        name="Triangulate",
        description="Triangulate the mesh before decimation (recommended for game engines)",
        default=False
    )

    @classmethod
    def poll(cls, context):
        """Check if the operator can be executed"""
        return (context.mode == 'OBJECT' and
                context.selected_objects and
                any(obj.type == 'MESH' for obj in context.selected_objects))

    def execute(self, context):
        """Execute the decimation operation"""
        # Ensure we're in object mode
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not mesh_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        processed_count = 0
        failed_objects = []
        
        self.report({'INFO'}, f"Processing {len(mesh_objects)} objects...")
        
        for obj in mesh_objects:
            try:
                # Store original poly count
                original_poly_count = len(obj.data.polygons)
                
                # Deselect all and select current object
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                
                # Triangulate first if requested
                if self.triangulate:
                    tri_mod = obj.modifiers.new(name="Triangulate", type='TRIANGULATE')
                    tri_mod.quad_method = 'BEAUTY'
                    tri_mod.ngon_method = 'BEAUTY'
                
                # Add Decimate modifier
                decimate_mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
                decimate_mod.decimate_type = self.decimate_type
                
                if self.decimate_type == 'COLLAPSE':
                    decimate_mod.ratio = self.ratio
                    decimate_mod.use_collapse_triangulate = True
                elif self.decimate_type == 'DISSOLVE':
                    decimate_mod.angle_limit = self.angle_limit
                    decimate_mod.use_dissolve_boundaries = False
                elif self.decimate_type == 'UNSUBDIV':
                    decimate_mod.iterations = int((1.0 - self.ratio) * 5)
                
                # Add Weighted Normal modifier if requested
                if self.use_weighted_normals:
                    wn_mod = obj.modifiers.new(name="WeightedNormal", type='WEIGHTED_NORMAL')
                    wn_mod.weight = 100
                    wn_mod.mode = self.weighted_mode
                    wn_mod.keep_sharp = True
                
                # Apply modifiers if requested
                if self.apply_modifiers:
                    # Apply in correct order using lower-level API
                    if self.triangulate:
                        with context.temp_override(object=obj):
                            bpy.ops.object.modifier_apply(modifier="Triangulate")
                    
                    with context.temp_override(object=obj):
                        bpy.ops.object.modifier_apply(modifier="Decimate")
                    
                    if self.use_weighted_normals:
                        with context.temp_override(object=obj):
                            bpy.ops.object.modifier_apply(modifier="WeightedNormal")
                
                # Set auto smooth
                if self.use_auto_smooth:
                    # For Blender 4.1+, use new normals system
                    if bpy.app.version >= (4, 1, 0):
                        # Use modifier instead
                        if not self.apply_modifiers and not self.use_weighted_normals:
                            smooth_mod = obj.modifiers.new(name="SmoothByAngle", type='NODES')
                    else:
                        # Legacy auto smooth for older Blender versions
                        obj.data.use_auto_smooth = True
                        obj.data.auto_smooth_angle = self.smooth_angle
                
                # Shade smooth using lower-level API
                for poly in obj.data.polygons:
                    poly.use_smooth = True
                
                # Calculate new poly count
                new_poly_count = len(obj.data.polygons)
                reduction = ((original_poly_count - new_poly_count) / original_poly_count) * 100
                
                processed_count += 1
                
                self.report({'INFO'}, 
                           f"{obj.name}: {original_poly_count} → {new_poly_count} polys ({reduction:.1f}% reduction)")
                
            except Exception as e:
                failed_objects.append(f"{obj.name}: {str(e)}")
                self.report({'WARNING'}, f"Failed on {obj.name}: {str(e)}")
                continue
        
        # Final report
        if failed_objects:
            self.report({'WARNING'}, f"Completed: {processed_count}/{len(mesh_objects)} objects processed")
        else:
            self.report({'INFO'}, f"SUCCESS: All {processed_count} objects decimated!")
        
        return {'FINISHED'}

    def draw(self, context):
        """Draw the operator properties in the UI"""
        layout = self.layout
        
        # Decimation settings
        box = layout.box()
        box.label(text="Decimation Settings", icon='MOD_DECIM')
        box.prop(self, "decimate_type")
        
        if self.decimate_type in ['COLLAPSE', 'UNSUBDIV']:
            box.prop(self, "ratio", slider=True)
        
        if self.decimate_type == 'DISSOLVE':
            box.prop(self, "angle_limit")
        
        box.prop(self, "triangulate")
        
        # Weighted normals
        box = layout.box()
        box.label(text="Weighted Normals", icon='MOD_NORMALEDIT')
        box.prop(self, "use_weighted_normals")
        
        if self.use_weighted_normals:
            box.prop(self, "weighted_mode")
        
        # Auto smooth
        box = layout.box()
        box.label(text="Smooth Shading", icon='SMOOTHCURVE')
        box.prop(self, "use_auto_smooth")
        
        if self.use_auto_smooth:
            box.prop(self, "smooth_angle")
        
        # Apply options
        box = layout.box()
        box.label(text="Options", icon='MODIFIER')
        box.prop(self, "apply_modifiers")


def register():
    """Register the operator"""
    bpy.utils.register_class(MESH_OT_auto_decimate)


def unregister():
    """Unregister the operator"""
    bpy.utils.unregister_class(MESH_OT_auto_decimate)
