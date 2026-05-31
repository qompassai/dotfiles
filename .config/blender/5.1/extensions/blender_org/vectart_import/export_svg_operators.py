import bpy
import os
import subprocess
from bpy.types import Operator
from bpy.props import BoolProperty

class VECTART_OT_ExportCurvesAsSVG(Operator):
    bl_idname = "object.export_curves_svg"
    bl_label = "Export Curves as SVG"
    bl_description = "Export selected curves as SVG and open in external editor"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects and any(obj.type == 'CURVE' for obj in context.selected_objects)
    
    def execute(self, context):
        props = context.scene.vectart_props
        
        if not props.svg_editor_path:
            # Try to auto-detect if path not set
            if props.svg_editor_type != 'CUSTOM':
                from . import __init__ as main_module
                props.svg_editor_path = main_module.find_svg_editor_path(props.svg_editor_type)
                
            if not props.svg_editor_path:
                self.report({'ERROR'}, "SVG editor path not set or detected")
                return {'CANCELLED'}
        
        # Get selected curves
        selected_curves = [obj for obj in context.selected_objects if obj.type == 'CURVE']
        
        if not selected_curves:
            self.report({'ERROR'}, "No curves selected")
            return {'CANCELLED'}
        
        # Create temp file path
        temp_dir = bpy.app.tempdir
        temp_svg = os.path.join(temp_dir, "vectart_temp.svg")
        
        try:
            # Export curves to SVG using our custom exporter
            from . import export_svg
            export_svg.export_curves_to_svg(selected_curves, temp_svg)
            
            # Open in editor
            subprocess.Popen([props.svg_editor_path, temp_svg])
            self.report({'INFO'}, f"Exported {len(selected_curves)} curves to SVG for editing")
            
            # Store path for reimport
            props.last_exported_svg = temp_svg
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error exporting curves: {str(e)}")
            return {'CANCELLED'}

class VECTART_OT_ReimportSVG(Operator):
    bl_idname = "object.reimport_svg"
    bl_label = "Reimport SVG"
    bl_description = "Reimport the last edited SVG file"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        props = context.scene.vectart_props
        return props.last_exported_svg and os.path.exists(props.last_exported_svg)
    
    def execute(self, context):
        props = context.scene.vectart_props
        
        if not props.last_exported_svg or not os.path.exists(props.last_exported_svg):
            self.report({'ERROR'}, "No SVG file to reimport")
            return {'CANCELLED'}
        
        try:
            # Import SVG
            bpy.ops.import_curve.svg(filepath=props.last_exported_svg)
            
            # Get imported curves
            imported_curves = [obj for obj in context.selected_objects if obj.type == 'CURVE']
            
            if not imported_curves:
                self.report({'WARNING'}, "No curves imported")
                return {'CANCELLED'}
            
            # Apply settings to imported curves
            for curve in imported_curves:
                # Apply bevel settings
                curve.data.bevel_depth = props.bevel_depth
                curve.data.bevel_resolution = props.bevel_resolution
                
                # Apply cyclic setting
                for spline in curve.data.splines:
                    spline.use_cyclic_u = props.use_cyclic
            
            self.report({'INFO'}, f"Successfully reimported {len(imported_curves)} curves")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error reimporting SVG: {str(e)}")
            return {'CANCELLED'}