# PROTO Tools script
# 2024 PROTOWLF, Licensed under GPL-3.0

import bpy
from bpy.props import (
    IntProperty,
    FloatProperty,
    BoolProperty,
    EnumProperty,
)


# Properties for Vertex Tools UI
class ProtoTools_VertexToolsProperties(bpy.types.PropertyGroup):

    fill_weight: bpy.props.FloatProperty(
        name="Weight",
        description="Weight",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    
    fill_skip_mask: bpy.props.BoolProperty(
        name="Skip Mask",
        description="Skip the active Paint Mask",
        default=False
    )
    
    group_to_color_invert: bpy.props.BoolProperty(
        name="Invert",
        description="Invert the Vertex Group values before copying to Vertex Colors",
        default=False
    )
    
    group_to_color_skip_mask: bpy.props.BoolProperty(
        name="Skip Mask",
        description="Skip the active Paint Mask",
        default=False
    )


def get_paintable_loops(ob, skip_mask):
    loops = []
    # Check mask
    if ob.data.use_paint_mask and not skip_mask:
        # Iterate through all faces, and store a list of selected faces' loops
        for face in ob.data.polygons:
            if face.select:
                for index in face.loop_indices:
                    loops.append(ob.data.loops[index])
    else:
        # All loops
        loops = ob.data.loops
    
    return loops


class ProtoTools_VertexGroupToVertexColor(bpy.types.Operator):
    """Copy the weight of the current Vertex Group into the given channel of the current Vertex Color Attribute"""
    bl_idname = "prototools.vertex_group_to_vertex_color"
    bl_label = "Vertex Group To Vertex Color)"
    bl_options = {'REGISTER', 'UNDO'}
    
    channel: EnumProperty(
        name="Channel",
        description="Which color channel to fill (Red, Green, Blue, Alpha)",
        options=set(),
        items=(('R', "Red", "Red color channel"),
               ('G', "Green", "Green color channel"),
               ('B', "Blue", "Blue color channel"),
               ('A', "Alpha", "Alpha color channel"),
               ('RGB', "RGB", "Fill Red Green and Blue color channels"),
               ('RGBA', "RGBA", "Fill Red Green Blue and Alpha color channels"),
               ),
        default='RGB',
    )
    
    invert: bpy.props.BoolProperty(
        name="Invert",
        description="Invert the Vertex Group values before copying to Vertex Colors",
        default=False,
    )
    
    skip_mask: bpy.props.BoolProperty(
        name="Skip Mask",
        description="Skip the active Paint Mask.\n\nNOTE: Paint Mask is only visible in Vertex Paint mode, but can still be applied in all modes",
        default=False,
    )
    
    @classmethod
    def poll(self, context):
        ob = context.active_object
        if ob != None and ob.type == "MESH" and ob.vertex_groups.active != None and context.mode != 'EDIT_MESH':
            return True
        return False
    
    def execute(self, context):
        # Active Object and active Vertex Group assumed to exist
        ob = context.active_object
        vertex_group = ob.vertex_groups.active
        
        # Make Vertex Color Attribute if one doesn't exist
        if ob.data.attributes.active_color is None:
            bpy.ops.geometry.color_attribute_add(name='Col', domain='CORNER', data_type='BYTE_COLOR')
        
        # Verify active Vertex Color Attribute
        if ob.data.attributes.active_color.domain != 'CORNER':
            self.report({'ERROR'}, "Invalid Color Attribute - Active color attribute must be of type Face Corner")
            return {'CANCELLED'}
        vertex_colors = ob.data.attributes.active_color.data
        
        loops = get_paintable_loops(ob, self.skip_mask)
        
        # Copy weight
        for loop in loops:
            try:
                weight = 1.0 - vertex_group.weight(loop.vertex_index) if self.invert else vertex_group.weight(loop.vertex_index)
            except:
                weight = 1.0 if self.invert else 0.0
            
            # Set weight
            if self.channel == 'RGB':
                vertex_colors[loop.index].color[0] = weight
                vertex_colors[loop.index].color[1] = weight
                vertex_colors[loop.index].color[2] = weight
            elif self.channel == 'RGBA':
                vertex_colors[loop.index].color[0] = weight
                vertex_colors[loop.index].color[1] = weight
                vertex_colors[loop.index].color[2] = weight
                vertex_colors[loop.index].color[3] = weight
            else:
                # Convert channel property to int
                channel_index = 0
                if self.channel == 'R':
                    channel_index = 0
                if self.channel == 'G':
                    channel_index = 1
                if self.channel == 'B':
                    channel_index = 2
                if self.channel == 'A':
                    channel_index = 3
                
                vertex_colors[loop.index].color[channel_index] = weight
        
        return {'FINISHED'}
    

class ProtoTools_FillVertexColor(bpy.types.Operator):
    """Set the given channel of the current Vertex Color Attribute to the given weight"""
    bl_idname = "prototools.fill_vertex_color"
    bl_label = "Fill Vertex Color"
    bl_options = {'REGISTER', 'UNDO'}
    
    channel: EnumProperty(
        name="Channel",
        description="Which color channel to fill (Red, Green, Blue, Alpha)",
        options=set(),
        items=(('R', "Red", "Red color channel"),
               ('G', "Green", "Green color channel"),
               ('B', "Blue", "Blue color channel"),
               ('A', "Alpha", "Alpha color channel"),
               ('RGB', "RGB", "Fill Red Green and Blue color channels"),
               ('RGBA', "RGBA", "Fill Red Green Blue and Alpha color channels"),
               ),
        default='RGB',
    )
    
    weight: bpy.props.FloatProperty(
        name="Weight",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    
    skip_mask: bpy.props.BoolProperty(
        name="Skip Mask",
        description="If True, skip the active Paint Mask.\n\nNOTE: Paint Mask is only visible in Vertex Paint mode, but can still be applied in all modes",
        default=False
    )
    
    @classmethod
    def poll(self, context):
        ob = context.active_object
        if ob != None and ob.type == "MESH" and ob.data.vertex_colors.active != None and context.mode != 'EDIT_MESH':
            return True
        return False
    
    def execute(self, context):
        # Active Object assumed to exist
        ob = context.active_object
        
        # Verify active Vertex Color Attribute
        if ob.data.attributes.active_color.domain != 'CORNER':
            self.report({'ERROR'}, "Invalid Color Attribute - Active color attribute must be of type Face Corner")
            return {'CANCELLED'}
        vertex_colors = ob.data.attributes.active_color.data
        
        loops = get_paintable_loops(ob, self.skip_mask)
        
        # Set weight
        if self.channel == 'RGB':
            for loop in loops:
                vertex_colors[loop.index].color[0] = self.weight
                vertex_colors[loop.index].color[1] = self.weight
                vertex_colors[loop.index].color[2] = self.weight
        elif self.channel == 'RGBA':
            for loop in loops:
                vertex_colors[loop.index].color[0] = self.weight
                vertex_colors[loop.index].color[1] = self.weight
                vertex_colors[loop.index].color[2] = self.weight
                vertex_colors[loop.index].color[3] = self.weight
        else:
            # Convert channel property to int
            channel_index = 0
            if self.channel == 'R':
                channel_index = 0
            if self.channel == 'G':
                channel_index = 1
            if self.channel == 'B':
                channel_index = 2
            if self.channel == 'A':
                channel_index = 3
            
            for loop in loops:
                vertex_colors[loop.index].color[channel_index] = self.weight
        
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ProtoTools_VertexToolsProperties)
    
    bpy.utils.register_class(ProtoTools_VertexGroupToVertexColor)
    bpy.utils.register_class(ProtoTools_FillVertexColor)
    
    bpy.types.Scene.proto_vertextools = bpy.props.PointerProperty(type=ProtoTools_VertexToolsProperties)
    

def unregister():
    bpy.utils.unregister_class(ProtoTools_FillVertexColor)
    bpy.utils.unregister_class(ProtoTools_VertexGroupToVertexColor)
    
    bpy.utils.unregister_class(ProtoTools_VertexToolsProperties)
    
    del bpy.types.Scene.proto_vertextools

