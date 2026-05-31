import bpy
import os
import time
import shutil

from . import utils


# ------------------------------------------------------------------------
# Core Backup Logic
# ------------------------------------------------------------------------

def get_catalog_files(active_only=False):
    paths = []
    prefs = bpy.context.preferences.filepaths
    if not hasattr(prefs, "asset_libraries"):
        return paths

    if active_only:
        # Use shared resolver from utils
        lib = utils.resolve_active_library(require_explicit=False, verbose=False)
        if not lib:
            return paths
        target_libs = [lib]
    else:
        target_libs = prefs.asset_libraries

    for lib in target_libs:
        lib_path = bpy.path.abspath(lib.path)
        if not os.path.isdir(lib_path):
            continue
        for filename in ("blender_assets.cats.txt", "blender_assets.cats.json"):
            candidate = os.path.join(lib_path, filename)
            if os.path.exists(candidate):
                paths.append(candidate)

    return paths


def backup_catalog(catalog_path):
    if not os.path.exists(catalog_path):
        return None

    folder = os.path.dirname(catalog_path)
    backup_folder = os.path.join(folder, "Backup catalogue")
    os.makedirs(backup_folder, exist_ok=True)

    base = os.path.basename(catalog_path)
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = os.path.join(backup_folder, f"{base}_backup_{timestamp}")

    try:
        shutil.copy2(catalog_path, backup_path)
        now = time.time()
        os.utime(backup_path, (now, now))  # force Date Modified = now
        print(f"[Asset Catalogue Backup] ✅ Created: {backup_path}")
        prune_backups(catalog_path, keep=2)
        return {"path": backup_path}
    except Exception as e:
        print(f"[Asset Catalogue Backup] ❌ Failed: {e}")
        return None


def _list_backups(catalog_path):
    folder = os.path.dirname(catalog_path)
    backup_folder = os.path.join(folder, "Backup catalogue")
    if not os.path.isdir(backup_folder):
        return []
    base = os.path.basename(catalog_path)
    files = [f for f in os.listdir(backup_folder) if f.startswith(base + "_backup_")]
    files.sort(reverse=True)
    return [os.path.join(backup_folder, f) for f in files]


def prune_backups(catalog_path, keep=2):
    removed = 0
    backups = _list_backups(catalog_path)
    for old in backups[keep:]:
        try:
            os.remove(old)
            removed += 1
            print(f"[Asset Catalogue Backup] ✂ Pruned: {old}")
        except Exception as e:
            print(f"[Asset Catalogue Backup] ❌ Failed to prune {old}: {e}")
    return removed


def find_latest_backup(catalog_path):
    folder = os.path.dirname(catalog_path)
    backup_folder = os.path.join(folder, "Backup catalogue")
    if not os.path.exists(backup_folder):
        return None

    base = os.path.basename(catalog_path)
    backups = [f for f in os.listdir(backup_folder) if f.startswith(base + "_backup_")]
    if not backups:
        return None

    backups.sort(reverse=True)
    return os.path.join(backup_folder, backups[0])


def restore_latest_backup(catalog_path):
    latest = find_latest_backup(catalog_path)
    if not latest:
        print(f"[Asset Catalogue Backup] ⚠️ No backup found for {catalog_path}")
        return None
    try:
        shutil.copy2(latest, catalog_path)
        now = time.time()
        os.utime(catalog_path, (now, now))  # touch restored file so it shows as updated
        print(f"[Asset Catalogue Backup] 🔁 Restored from: {latest}")
        return latest
    except Exception as e:
        print(f"[Asset Catalogue Backup] ❌ Restore failed: {e}")
        return None


def clear_all_backups():
    prefs = bpy.context.preferences.filepaths
    deleted_count = 0
    if not hasattr(prefs, "asset_libraries"):
        return 0

    for lib in prefs.asset_libraries:
        lib_path = bpy.path.abspath(lib.path)
        backup_folder = os.path.join(lib_path, "Backup catalogue")
        if os.path.exists(backup_folder):
            try:
                shutil.rmtree(backup_folder)
                deleted_count += 1
                print(f"[Asset Catalogue Backup] 🗑️ Deleted: {backup_folder}")
            except Exception as e:
                print(f"[Asset Catalogue Backup] ❌ Failed to delete {backup_folder}: {e}")
    return deleted_count


# ------------------------------------------------------------------------
# Operators
# ------------------------------------------------------------------------

class ASSETCATALOGUE_OT_BackupNow(bpy.types.Operator):
    bl_idname = "assetcatalogue.backup_now"
    bl_label = "Backup All Catalogues"

    @classmethod
    def description(cls, context, properties):
        return "Backup all asset library catalogues."

    def execute(self, context):
        catalogs = get_catalog_files(active_only=False)
        if not catalogs:
            self.report({'WARNING'}, "No asset catalogues found.")
            return {'CANCELLED'}

        count = 0
        for cfile in catalogs:
            if backup_catalog(cfile):
                count += 1
        self.report({'INFO'}, f"Backed up {count} catalogue(s)")
        return {'FINISHED'}


class ASSETCATALOGUE_OT_BackupActive(bpy.types.Operator):
    bl_idname = "assetcatalogue.backup_active"
    bl_label = "Backup Active Library Only"

    @classmethod
    def description(cls, context, properties):
        return "Backup active asset library catalogues."

    def execute(self, context):
        catalogs = get_catalog_files(active_only=True)
        if not catalogs:
            self.report({'WARNING'}, "No active user Asset Library selected in the Asset Browser.")
            return {'CANCELLED'}

        count = 0
        for cfile in catalogs:
            if backup_catalog(cfile):
                count += 1
        self.report({'INFO'}, f"Backed up {count} catalogue(s) from active library")
        return {'FINISHED'}


class ASSETCATALOGUE_OT_RestoreLast(bpy.types.Operator):
    bl_idname = "assetcatalogue.restore_last"
    bl_label = "Restore Last Backup"

    @classmethod
    def description(cls, context, properties):
        return "Restore all catalogues from recent backup."

    def execute(self, context):
        catalogs = get_catalog_files()
        if not catalogs:
            self.report({'WARNING'}, "No asset catalogues found.")
            return {'CANCELLED'}

        count = 0
        for cfile in catalogs:
            if restore_latest_backup(cfile):
                count += 1
        self.report({'INFO'}, f"Restored {count} catalogue(s)")
        return {'FINISHED'}


class ASSETCATALOGUE_OT_ClearBackups(bpy.types.Operator):
    bl_idname = "assetcatalogue.clear_backups"
    bl_label = "Clear All Backups"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        deleted = clear_all_backups()
        if deleted:
            self.report({'INFO'}, f"Deleted {deleted} backup folder(s).")
        else:
            self.report({'WARNING'}, "No backup folders found.")
        return {'FINISHED'}


# ------------------------------------------------------------------------
# Registration (module API)
# ------------------------------------------------------------------------

classes = (
    ASSETCATALOGUE_OT_BackupNow,
    ASSETCATALOGUE_OT_BackupActive,
    ASSETCATALOGUE_OT_RestoreLast,
    ASSETCATALOGUE_OT_ClearBackups,
)


def register_catalogue_backup():
    """Register everything related to the Catalogue Backup tool."""
    for cls in classes:
        bpy.utils.register_class(cls)
    print("[Asset Catalogue Backup] Registered.")


def unregister_catalogue_backup():
    """Unregister everything related to the Catalogue Backup tool."""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    print("[Asset Catalogue Backup] Unregistered.")
