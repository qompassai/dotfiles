import bpy
from bpy.types import Panel, Operator
from bpy.props import StringProperty
from contextlib import suppress

from .core import utils, tag_filter


class ALT_OT_OpenLibraryFolder(Operator):
    bl_idname = "alt.open_library_folder"
    bl_label = "Open Library Folder"

    path: StringProperty(
        name="Library Path",
        subtype='DIR_PATH',
    )

    @classmethod
    def description(cls, context, properties):
        p = properties.get("path", "")
        if p:
            # Tooltip shows the full path
            return f"Open asset library folder:\n{p}"
        return "Open asset library folder"

    def execute(self, context):
        if not self.path:
            self.report({'WARNING'}, "No library path set.")
            return {'CANCELLED'}
        try:
            bpy.ops.wm.path_open(filepath=self.path)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open folder: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class ALT_PT_AssetLibraryTools(Panel):
    bl_label = "Asset Library Tools"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOLS"  # Tool shelf in Asset Browser
    #bl_category = "ALT"
    bl_ui_units_x = 8
    bl_order = 1000

    @classmethod
    def poll(cls, context):
        space = getattr(context, "space_data", None)
        return bool(space and getattr(space, "browse_mode", None) == "ASSETS")

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # ---------------------------------------------------------
        # Active library status row (compact)
        # ---------------------------------------------------------

        lib = None
        lib_path = ""
        with suppress(Exception):
            lib = utils.resolve_active_library(require_explicit=False, verbose=False)

        if lib:
            lib_path = bpy.path.abspath(lib.path)
            
            # Create a row
            row = layout.row(align=True)
            
            # SPLIT the row: 0.85 means text gets 85%, button gets 15%
            # Change 0.85 to 0.80 to make the button wider, or 0.90 to make it smaller.
            split = row.split(factor=0.8, align=True)
            
            split.label(text=f"Active: {lib.name}")

            op = split.operator(
                "alt.open_library_folder",
                text="", 
                icon='FILEBROWSER',
            )
            op.path = lib_path

        else:
            row = layout.row(align=True)
            row.label(
                text="Active: (unresolved — select a user Asset Library)",
                icon='INFO',
            )

        layout.separator()

        # ---------------------------------------------------------
        # Tag Filter (NEW Logic)
        # ---------------------------------------------------------
        tag_filter.draw_tag_filter_ui(layout, context)

        # ---------------------------------------------------------
        # Catalogue tools (collapsible)
        # ---------------------------------------------------------
       
        show_cat = getattr(scene, "assetcatalogue_show_ui", False)

        box = layout.box()
        header = box.row(align=True)

        icon = 'TRIA_DOWN' if show_cat else 'TRIA_RIGHT'
        header.prop(
            scene,
            "assetcatalogue_show_ui",
            text="",
            icon=icon,
            emboss=False,
        )
        header.label(text="Catalogue Backup", icon="FILE_BACKUP")

        if show_cat:
            # Row 1: Backup actions (minimal text, clear intent)
            row = box.row(align=True)
            row.scale_y = 1.0
            row.operator(
                "assetcatalogue.backup_active",
                text="Backup Active",
                icon="CURRENT_FILE",
            )

            row.separator(factor=0.5)

            row.operator(
                "assetcatalogue.backup_now",
                text="Backup All",
                icon="FILE_VOLUME",
            )

            # Row 2: Restore + tiny cleanup toggle on the side
            row = box.row(align=True)
            row.operator(
                "assetcatalogue.restore_last",
                text="Restore Last",
                icon="FILE_REFRESH",
            )

            row.separator(factor=0.5)

            # Small cleanup toggle tucked at the right side
            if hasattr(scene, "assetcatalogue_show_cleanup"):
                tri_icon = (
                    'TRIA_DOWN'
                    if scene.assetcatalogue_show_cleanup
                    else 'TRIA_RIGHT'
                )
                row.prop(
                    scene,
                    "assetcatalogue_show_cleanup",
                    text="Cleanup",
                    icon=tri_icon,
                    emboss=True,
                )

                # Inline cleanup, only when expanded
                if scene.assetcatalogue_show_cleanup:
                    sub = box.column(align=True)
                    sub.separator()
                    sub.alert = True
                    sub.label(
                        text="Delete all catalogue backups.",
                        icon="ERROR",
                    )
                    sub.operator(
                        "assetcatalogue.clear_backups",
                        text="Delete Backups",
                        icon="TRASH",
                    )


# -------- register for UI module --------

classes = (
    ALT_OT_OpenLibraryFolder,
    ALT_PT_AssetLibraryTools,
)


def register_ui():
    for c in classes:
        bpy.utils.register_class(c)


def unregister_ui():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)