import bpy
from bpy.types import Operator
from bpy.props import FloatProperty, BoolProperty, IntProperty


class MESH_OT_smart_vertex_merge(Operator):
    """Smart vertex merging for CAD models and cleanup"""
    bl_idname = "mesh.smart_vertex_merge"
    bl_label = "Merge Vertices by Distance"
    bl_description = "Merge vertices by distance - essential for imported CAD models"
    bl_options = {'REGISTER', 'UNDO'}

    # Merge settings
    merge_distance: FloatProperty(
        name="Merge Distance",
        description="Maximum distance between vertices to merge",
        default=0.0001,
        min=0.00001,
        max=1.0,
        precision=5,
        subtype='DISTANCE'
    )
    
    use_sharp_edge_from_normals: BoolProperty(
        name="Sharp Edges from Normals",
        description="Mark edges as sharp based on angle between faces (prevents merging across hard edges)",
        default=True
    )
    
    sharp_edge_angle: FloatProperty(
        name="Sharp Edge Angle",
        description="Angle threshold for marking edges as sharp",
        default=0.523599,  # 30 degrees
        min=0.0,
        max=3.14159,
        subtype='ANGLE'
    )
    
    remove_doubles: BoolProperty(
        name="Remove Doubles",
        description="Use remove doubles algorithm (legacy)",
        default=True
    )
    
    # Additional cleanup
    dissolve_degenerate: BoolProperty(
        name="Dissolve Degenerate",
        description="Remove degenerate geometry (zero-area faces)",
        default=True
    )
    
    degenerate_threshold: FloatProperty(
        name="Degenerate Threshold",
        description="Threshold for degenerate faces",
        default=0.0001,
        min=0.00001,
        max=1.0,
        precision=5
    )
    
    delete_loose: BoolProperty(
        name="Delete Loose",
        description="Delete loose vertices and edges",
        default=True
    )
    
    recalculate_normals: BoolProperty(
        name="Recalculate Normals",
        description="Recalculate face normals after merging",
        default=True
    )

    @classmethod
    def poll(cls, context):
        """Check if the operator can be executed"""
        return (context.mode == 'OBJECT' and
                context.selected_objects and
                any(obj.type == 'MESH' for obj in context.selected_objects))

    def execute(self, context):
        """Execute the vertex merging operation"""
        # Ensure we're in object mode
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not mesh_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        processed_count = 0
        total_vertices_merged = 0
        
        self.report({'INFO'}, f"Processing {len(mesh_objects)} objects...")
        
        for obj in mesh_objects:
            try:
                # Get original vertex count
                original_vert_count = len(obj.data.vertices)
                
                # Select only this object
                for o in context.selected_objects:
                    o.select_set(False)
                obj.select_set(True)
                context.view_layer.objects.active = obj
                
                # Enter edit mode
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                
                # Mark sharp edges from normals first (before merging)
                if self.use_sharp_edge_from_normals:
                    try:
                        bpy.ops.mesh.edges_select_sharp(sharpness=self.sharp_edge_angle)
                        bpy.ops.mesh.mark_sharp()
                        bpy.ops.mesh.select_all(action='SELECT')
                    except Exception as sharp_error:
                        # If sharp edge detection fails, continue anyway
                        self.report({'WARNING'}, f"{obj.name}: Sharp edge detection failed, continuing...")
                        bpy.ops.mesh.select_all(action='SELECT')
                
                # Merge vertices by distance
                try:
                    # Try modern method first (Blender 2.8+)
                    bpy.ops.mesh.merge_by_distance(threshold=self.merge_distance)
                except AttributeError:
                    # Fall back to legacy method if modern method doesn't exist
                    try:
                        bpy.ops.mesh.remove_doubles(threshold=self.merge_distance)
                    except Exception as merge_error:
                        raise Exception(f"Merge operation failed: {str(merge_error)}")
                
                # Dissolve degenerate geometry
                if self.dissolve_degenerate:
                    bpy.ops.mesh.dissolve_degenerate(threshold=self.degenerate_threshold)
                
                # Delete loose geometry
                if self.delete_loose:
                    bpy.ops.mesh.delete_loose()
                
                # Recalculate normals
                if self.recalculate_normals:
                    bpy.ops.mesh.normals_make_consistent(inside=False)
                
                # Return to object mode
                bpy.ops.object.mode_set(mode='OBJECT')
                
                # Calculate merged vertices
                new_vert_count = len(obj.data.vertices)
                merged_count = original_vert_count - new_vert_count
                total_vertices_merged += merged_count
                
                self.report({'INFO'}, 
                           f"{obj.name}: {merged_count} vertices merged ({original_vert_count} → {new_vert_count})")
                
                processed_count += 1
                
            except Exception as e:
                self.report({'WARNING'}, f"Failed on {obj.name}: {str(e)}")
                try:
                    if context.mode != 'OBJECT':
                        bpy.ops.object.mode_set(mode='OBJECT')
                except:
                    pass
                continue
        
        # Ensure we end in object mode
        if context.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except:
                pass
        
        self.report({'INFO'}, 
                   f"SUCCESS: {total_vertices_merged} total vertices merged across {processed_count} objects!")
        
        return {'FINISHED'}

    def draw(self, context):
        """Draw the operator properties in the UI"""
        layout = self.layout
        
        # Merge settings
        box = layout.box()
        box.label(text="Merge Settings", icon='AUTOMERGE_ON')
        box.prop(self, "merge_distance")
        box.prop(self, "remove_doubles")
        
        # Sharp edge preservation
        box = layout.box()
        box.label(text="Edge Preservation", icon='EDGESEL')
        box.prop(self, "use_sharp_edge_from_normals")
        
        if self.use_sharp_edge_from_normals:
            box.prop(self, "sharp_edge_angle")
        
        # Cleanup options
        box = layout.box()
        box.label(text="Cleanup", icon='BRUSH_DATA')
        box.prop(self, "dissolve_degenerate")
        
        if self.dissolve_degenerate:
            box.prop(self, "degenerate_threshold")
        
        box.prop(self, "delete_loose")
        box.prop(self, "recalculate_normals")


def register():
    """Register the operator"""
    bpy.utils.register_class(MESH_OT_smart_vertex_merge)


def unregister():
    """Unregister the operator"""
    bpy.utils.unregister_class(MESH_OT_smart_vertex_merge)
