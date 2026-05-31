import bpy
from bpy.types import Operator
from bpy.props import FloatProperty, BoolProperty, EnumProperty


class MESH_OT_dual_uv_unwrap(Operator):
    """Smart UV unwrap with dual UV support - UV0 for texturing and UV1 for lightmapping"""
    bl_idname = "mesh.dual_uv_unwrap"
    bl_label = "Dual UV Unwrap (UV0 + UV1)"
    bl_description = "Generate UV0 for textures and UV1 for lightmaps - optimized for Unity/Unreal Engine"
    bl_options = {'REGISTER', 'UNDO'}

    # UV0 Settings (Texturing)
    uv0_enabled: BoolProperty(
        name="Generate UV0",
        description="Generate UV0 map for texturing",
        default=True
    )
    
    uv0_method: EnumProperty(
        name="UV0 Method",
        description="Unwrapping method for UV0",
        items=[
            ('SMART', "Smart UV Project", "Smart UV projection (good for complex models)"),
            ('LIGHTMAP', "Lightmap Pack", "Lightmap packing (good for simple objects)"),
            ('CUBE', "Cube Projection", "Cube projection (good for architectural)"),
            ('CYLINDER', "Cylinder", "Cylinder projection"),
            ('SPHERE', "Sphere", "Sphere projection")
        ],
        default='SMART'
    )
    
    uv0_angle_limit: FloatProperty(
        name="UV0 Angle Limit",
        description="Angle limit for UV0 smart projection",
        default=1.15192,  # 66 degrees
        min=0.0,
        max=3.14159,
        subtype='ANGLE'
    )
    
    uv0_island_margin: FloatProperty(
        name="UV0 Island Margin",
        description="Margin between UV0 islands",
        default=0.02,
        min=0.0,
        max=1.0
    )
    
    uv0_pack_islands: BoolProperty(
        name="Pack UV0 Islands",
        description="Pack UV0 islands for optimal space usage",
        default=True
    )
    
    uv0_pack_margin: FloatProperty(
        name="UV0 Pack Margin",
        description="Margin when packing UV0 islands",
        default=0.001,
        min=0.0,
        max=0.1
    )
    
    uv0_rotate: BoolProperty(
        name="Rotate UV0 Islands",
        description="Allow rotation of UV0 islands during packing",
        default=True
    )
    
    # UV1 Settings (Lightmapping)
    uv1_enabled: BoolProperty(
        name="Generate UV1",
        description="Generate UV1 map for lightmapping",
        default=True
    )
    
    uv1_method: EnumProperty(
        name="UV1 Method",
        description="Unwrapping method for UV1 (lightmaps need non-overlapping UVs)",
        items=[
            ('SMART', "Smart UV Project", "Smart UV projection"),
            ('LIGHTMAP', "Lightmap Pack", "Lightmap packing (recommended for lightmaps)"),
        ],
        default='LIGHTMAP'
    )
    
    uv1_margin: FloatProperty(
        name="UV1 Margin",
        description="Margin between UV1 islands (larger for lightmaps to avoid bleeding)",
        default=0.05,
        min=0.0,
        max=0.5
    )
    
    uv1_angle_limit: FloatProperty(
        name="UV1 Angle Limit",
        description="Angle limit for UV1 smart projection",
        default=1.15192,  # 66 degrees
        min=0.0,
        max=3.14159,
        subtype='ANGLE'
    )
    
    # General settings
    correct_aspect: BoolProperty(
        name="Correct Aspect",
        description="Map UVs taking image aspect ratio into account",
        default=True
    )
    
    area_weight: FloatProperty(
        name="Area Weight",
        description="Weight for area preservation",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    multi_object_mode: BoolProperty(
        name="Multi-Object Mode",
        description="Process multiple objects, each with its own UV space",
        default=True
    )

    @classmethod
    def poll(cls, context):
        """Check if the operator can be executed"""
        return (context.mode == 'OBJECT' and
                context.selected_objects and
                any(obj.type == 'MESH' for obj in context.selected_objects))

    def create_or_get_uv_layer(self, obj, layer_name, index):
        """Create or get UV layer at specific index"""
        # Check if UV layer exists
        uv_layer = obj.data.uv_layers.get(layer_name)
        
        if uv_layer:
            # Set as active
            obj.data.uv_layers.active_index = obj.data.uv_layers.find(layer_name)
        else:
            # Create new UV layer
            uv_layer = obj.data.uv_layers.new(name=layer_name)
            
            # Move to correct index if possible
            if len(obj.data.uv_layers) > 1:
                # Move to target index
                current_index = len(obj.data.uv_layers) - 1
                while current_index > index and current_index > 0:
                    obj.data.uv_layers.active_index = current_index
                    bpy.ops.mesh.uv_texture_add()
                    obj.data.uv_layers.active_index = current_index - 1
                    current_index -= 1
            
            obj.data.uv_layers.active_index = index
        
        return uv_layer

    def unwrap_uv_layer(self, obj, method, angle_limit, margin, pack, pack_margin, rotate, area_weight):
        """Unwrap current UV layer with specified method"""
        # Enter edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        if method == 'SMART':
            bpy.ops.uv.smart_project(
                angle_limit=angle_limit,
                island_margin=margin,
                area_weight=area_weight,
                correct_aspect=self.correct_aspect
            )
            
            if pack:
                bpy.ops.uv.pack_islands(
                    margin=pack_margin,
                    rotate=rotate
                )
        
        elif method == 'LIGHTMAP':
            bpy.ops.uv.lightmap_pack(
                PREF_CONTEXT='ALL_FACES',
                PREF_PACK_IN_ONE=True,
                PREF_NEW_UVLAYER=False,
                PREF_APPLY_IMAGE=False,
                PREF_IMG_PX_SIZE=1024,
                PREF_BOX_DIV=48,
                PREF_MARGIN_DIV=margin
            )
        
        elif method == 'CUBE':
            bpy.ops.uv.cube_project(cube_size=1.0, correct_aspect=self.correct_aspect)
            if pack:
                bpy.ops.uv.pack_islands(margin=pack_margin, rotate=rotate)
        
        elif method == 'CYLINDER':
            bpy.ops.uv.cylinder_project(correct_aspect=self.correct_aspect)
            if pack:
                bpy.ops.uv.pack_islands(margin=pack_margin, rotate=rotate)
        
        elif method == 'SPHERE':
            bpy.ops.uv.sphere_project(correct_aspect=self.correct_aspect)
            if pack:
                bpy.ops.uv.pack_islands(margin=pack_margin, rotate=rotate)
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')

    def execute(self, context):
        """Execute the dual UV unwrapping operation"""
        original_active = context.active_object
        original_mode = context.mode
        original_selection = list(context.selected_objects)
        
        # Get all selected mesh objects
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not mesh_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        if not self.uv0_enabled and not self.uv1_enabled:
            self.report({'WARNING'}, "Please enable at least one UV layer")
            return {'CANCELLED'}
        
        processed_count = 0
        failed_objects = []
        
        self.report({'INFO'}, f"Processing {len(mesh_objects)} objects...")
        
        try:
            # Ensure we're in Object mode
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Process each mesh object
            for obj in mesh_objects:
                try:
                    # Verify object has geometry
                    if len(obj.data.polygons) == 0:
                        continue
                    
                    # Select only this object
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    context.view_layer.objects.active = obj
                    
                    # Generate UV0 (Texturing)
                    if self.uv0_enabled:
                        uv0_layer = self.create_or_get_uv_layer(obj, "UVMap", 0)
                        obj.data.uv_layers.active = uv0_layer
                        
                        self.unwrap_uv_layer(
                            obj,
                            self.uv0_method,
                            self.uv0_angle_limit,
                            self.uv0_island_margin,
                            self.uv0_pack_islands,
                            self.uv0_pack_margin,
                            self.uv0_rotate,
                            self.area_weight
                        )
                        
                        self.report({'INFO'}, f"  {obj.name}: UV0 generated ({self.uv0_method})")
                    
                    # Generate UV1 (Lightmapping)
                    if self.uv1_enabled:
                        uv1_layer = self.create_or_get_uv_layer(obj, "UVMap_Lightmap", 1)
                        obj.data.uv_layers.active = uv1_layer
                        
                        self.unwrap_uv_layer(
                            obj,
                            self.uv1_method,
                            self.uv1_angle_limit,
                            self.uv1_margin,
                            False,  # Don't pack lightmaps separately
                            0.0,
                            False,
                            self.area_weight
                        )
                        
                        self.report({'INFO'}, f"  {obj.name}: UV1 generated ({self.uv1_method})")
                    
                    # Set UV0 as active by default
                    if self.uv0_enabled and len(obj.data.uv_layers) > 0:
                        obj.data.uv_layers.active_index = 0
                    
                    processed_count += 1
                    
                except Exception as obj_error:
                    failed_objects.append(f"{obj.name}: {str(obj_error)}")
                    try:
                        if context.mode != 'OBJECT':
                            bpy.ops.object.mode_set(mode='OBJECT')
                    except:
                        pass
                    continue
        
        except Exception as e:
            self.report({'ERROR'}, f"Critical error: {str(e)}")
            return {'CANCELLED'}
        
        finally:
            # Restore original state
            try:
                if context.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
                
                bpy.ops.object.select_all(action='DESELECT')
                for obj in original_selection:
                    if obj:
                        obj.select_set(True)
                
                if original_active and original_active in original_selection:
                    context.view_layer.objects.active = original_active
                
                context.view_layer.update()
            except Exception as restore_error:
                self.report({'WARNING'}, f"Could not fully restore state: {str(restore_error)}")
        
        # Final report
        if failed_objects:
            self.report({'WARNING'}, f"Completed: {processed_count}/{len(mesh_objects)} objects processed")
        else:
            self.report({'INFO'}, f"SUCCESS: Dual UV unwrap completed for {processed_count} objects!")
        
        return {'FINISHED'}

    def draw(self, context):
        """Draw the operator properties in the UI"""
        layout = self.layout
        
        # Multi-object mode
        layout.prop(self, "multi_object_mode")
        layout.separator()
        
        # UV0 Settings
        box = layout.box()
        box.prop(self, "uv0_enabled", text="Generate UV0 (Texturing)", toggle=True)
        
        if self.uv0_enabled:
            col = box.column()
            col.prop(self, "uv0_method")
            
            if self.uv0_method == 'SMART':
                col.prop(self, "uv0_angle_limit")
                col.prop(self, "uv0_island_margin")
                col.prop(self, "uv0_pack_islands")
                
                if self.uv0_pack_islands:
                    sub = col.column(align=True)
                    sub.prop(self, "uv0_pack_margin")
                    sub.prop(self, "uv0_rotate")
        
        layout.separator()
        
        # UV1 Settings
        box = layout.box()
        box.prop(self, "uv1_enabled", text="Generate UV1 (Lightmapping)", toggle=True)
        
        if self.uv1_enabled:
            col = box.column()
            col.prop(self, "uv1_method")
            col.prop(self, "uv1_margin")
            
            if self.uv1_method == 'SMART':
                col.prop(self, "uv1_angle_limit")
        
        layout.separator()
        
        # General settings
        box = layout.box()
        box.label(text="General Settings", icon='SETTINGS')
        box.prop(self, "correct_aspect")
        box.prop(self, "area_weight")

    def invoke(self, context, event):
        """Show dialog before executing"""
        return context.window_manager.invoke_props_dialog(self, width=400)


def register():
    """Register the operator"""
    bpy.utils.register_class(MESH_OT_dual_uv_unwrap)


def unregister():
    """Unregister the operator"""
    bpy.utils.unregister_class(MESH_OT_dual_uv_unwrap)
