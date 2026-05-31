import bpy, os, tempfile


def get_set_show_overlays(value=None):
    """
    Get or set the current state of the overlays in the 3D Viewport.
    """
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    if value is None:
                        return space.overlay.show_overlays
                    else:
                        space.overlay.show_overlays = value
                    break

class ASSETBROWSER_OT_RenderThumbnail(bpy.types.Operator):
    bl_idname = "asset_browser.capture_viewport_thumbnail"
    bl_label = "Render Thumbnail"
    bl_description = "Render a thumbnail from the viewport and set it as the asset preview"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        def reset_to_previous_state():
            if current_scene_path:
                bpy.context.scene.render.filepath = current_scene_path
            if not context.window_manager.show_ui:
                if current_show_ui_value:
                    get_set_show_overlays(current_show_ui_value)
            if current_transparent_background_value:
                bpy.context.scene.render.film_transparent = current_transparent_background_value

        try:
            current_scene_path = bpy.context.scene.render.filepath
            current_show_ui_value = get_set_show_overlays()
            current_transparent_background_value = bpy.context.scene.render.film_transparent

            if not context.window_manager.show_ui:
                get_set_show_overlays(False)

            bpy.context.scene.render.film_transparent = context.window_manager.transparant_background

            thumbnail_path = os.path.join(tempfile.gettempdir(), "viewport_thumbnail.png")
            bpy.context.scene.render.filepath = thumbnail_path
            bpy.ops.render.opengl(write_still=True)
            bpy.ops.ed.lib_id_load_custom_preview(filepath=thumbnail_path)

            reset_to_previous_state()

        except Exception as e:
            reset_to_previous_state()
            self.report({'ERROR'}, f"Failed to capture thumbnail: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}


def draw_render_thumbnail_button(self, context):
    layout = self.layout
    row = layout.row()
    row.operator("asset_browser.capture_viewport_thumbnail", text="Capture Thumbnail from Viewport", icon='RESTRICT_RENDER_OFF')
    layout.prop(context.window_manager, "transparant_background", text="Transparent Background")
    layout.prop(context.window_manager, "show_ui", text="Show UI")

def register():
    bpy.types.ASSETBROWSER_PT_metadata_preview.append(draw_render_thumbnail_button)
    bpy.utils.register_class(ASSETBROWSER_OT_RenderThumbnail)
    
    bpy.types.WindowManager.transparant_background = bpy.props.BoolProperty(
        name="Transparent Background",
        description="Render with a transparent background",
        default=False,
    ) # type: ignore
    bpy.types.WindowManager.show_ui = bpy.props.BoolProperty(
        name="Show UI",
        description="Show the UI while rendering",
        default=True,
    ) # type: ignore


def unregister():
    bpy.types.ASSETBROWSER_PT_metadata_preview.remove(draw_render_thumbnail_button)
    bpy.utils.unregister_class(ASSETBROWSER_OT_RenderThumbnail)

    del bpy.types.WindowManager.transparant_background # type: ignore
    del bpy.types.WindowManager.show_ui # type: ignore
