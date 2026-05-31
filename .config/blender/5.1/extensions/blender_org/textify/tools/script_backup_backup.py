import bpy
from bpy.types import Operator, Menu
from bpy.props import StringProperty
from pathlib import Path
import json
import os

# --- JSON Path ---
ADDON_DIR = Path(__file__).parent
BACKUP_JSON = ADDON_DIR / "backup_locations.json"


# --- JSON Helpers ---
def load_backup_map():
    if BACKUP_JSON.exists():
        try:
            with BACKUP_JSON.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception:
            return {}
    return {}


def save_backup_map(data):
    try:
        with BACKUP_JSON.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving backup map: {e}")


def migrate_old_format():
    """Manually migrate old format to new format"""
    backup_map = load_backup_map()
    migrated = False
    
    for key, value in backup_map.items():
        if isinstance(value, str):
            backup_map[key] = {"location": value, "backups": []}
            migrated = True
    
    if migrated:
        save_backup_map(backup_map)
    
    return backup_map


def get_backup_data(text):
    """Return stored backup data for this script file path."""
    backup_map = load_backup_map()
    key = text.filepath if text.filepath else text.name
    return backup_map.get(key, {"location": "", "backups": []})


def update_backup_map(text, backup_path):
    """Update JSON with new backup path for this script."""
    # First migrate any old format data
    backup_map = migrate_old_format()
    
    key = text.filepath if text.filepath else text.name

    # Ensure the entry exists with proper structure
    if key not in backup_map:
        backup_map[key] = {"location": "", "backups": []}
    
    # Double-check the structure is correct
    if not isinstance(backup_map[key], dict):
        old_location = backup_map[key] if isinstance(backup_map[key], str) else ""
        backup_map[key] = {"location": old_location, "backups": []}
    
    # Ensure required keys exist
    if "location" not in backup_map[key]:
        backup_map[key]["location"] = ""
    if "backups" not in backup_map[key]:
        backup_map[key]["backups"] = []

    # Update the location to the directory of the backup
    backup_map[key]["location"] = str(Path(backup_path).parent)
    
    # Add the backup path if it's not already in the list
    backup_path_str = str(backup_path)
    if backup_path_str not in backup_map[key]["backups"]:
        backup_map[key]["backups"].append(backup_path_str)
    
    save_backup_map(backup_map)


def list_backups_for_text(text):
    """Return stored backup paths for this script file that actually exist."""
    backup_data = get_backup_data(text)
    backup_paths = []
    
    for backup_path_str in backup_data.get("backups", []):
        backup_path = Path(backup_path_str)
        # Only include backups that actually exist
        if backup_path.exists():
            backup_paths.append(backup_path)
    
    return backup_paths


# --- Operators ---
class TEXTIFY_OT_save_backup(Operator):
    bl_idname = "textify.save_backup"
    bl_label = "Save Script Backup"
    bl_description = "Saves a backup of the current script.\n\n • Shift-Click for a numbered backup.\n • Ctrl-Click to save in a dedicated backup folder.\n\nWithout a modifier key, it opens a file save dialog."
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')

    def invoke(self, context, event):
        text = context.edit_text
        if not text:
            self.report({'ERROR'}, "No active text block")
            return {'CANCELLED'}

        shift_pressed = event.shift
        ctrl_pressed = event.ctrl
        backup_data = get_backup_data(text)
        backup_dir = backup_data.get("location")

        # --- Shift: Quick numbered backup in the stored dir or script dir ---
        if shift_pressed:
            if backup_dir:
                target_dir = Path(backup_dir)
            elif text.filepath:
                target_dir = Path(text.filepath).parent
            else:
                target_dir = Path.home()

            base_name = Path(text.name).stem
            existing = list(target_dir.glob(f"{base_name}_*.py"))
            numbers = [int(p.stem.split('_')[-1]) for p in existing if p.stem.split('_')[-1].isdigit()]
            next_num = max(numbers, default=0) + 1

            self.filepath = str(target_dir / f"{base_name}_{next_num}.py")
            return self.execute(context)

        # --- Ctrl: Quick numbered save to 'backup' folder ---
        if ctrl_pressed:
            if not text.filepath:
                self.report({'ERROR'}, "Cannot save to 'backup' folder for unsaved scripts.")
                return {'CANCELLED'}

            parent_dir = Path(text.filepath).parent
            backup_folder = parent_dir / "backup"
            backup_folder.mkdir(exist_ok=True)  # Create the folder if it doesn't exist

            base_name = Path(text.name).stem
            existing = list(backup_folder.glob(f"{base_name}_*.py"))
            numbers = [int(p.stem.split('_')[-1]) for p in existing if p.stem.split('_')[-1].isdigit()]
            next_num = max(numbers, default=0) + 1

            self.filepath = str(backup_folder / f"{base_name}_{next_num}.py")
            return self.execute(context)

        # --- Normal picker ---
        base_name = Path(text.name).stem
        if not backup_dir:
            if text.filepath:
                self.filepath = str(Path(text.filepath).with_name(f"{base_name}_backup.py"))
            else:
                self.filepath = str(Path.home() / f"{base_name}_backup.py")
        else:
            self.filepath = str(Path(backup_dir) / f"{base_name}_backup.py")

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        text = context.edit_text
        if not text:
            self.report({'ERROR'}, "No active text block")
            return {'CANCELLED'}

        backup_path = Path(self.filepath)
        backup_path.write_text(text.as_string(), encoding='utf-8')

        update_backup_map(text, str(backup_path))

        self.report({'INFO'}, f"Backup saved: {backup_path}")
        return {'FINISHED'}


class TEXTIFY_OT_open_backup(Operator):
    bl_idname = "textify.open_backup"
    bl_label = "Open Backup File"
    bl_description = "Opens the selected backup file in a new text block."

    filepath: StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        path = Path(self.filepath)
        if not path.exists():
            self.report({'ERROR'}, "File not found")
            return {'CANCELLED'}

        bpy.data.texts.load(str(path))
        return {'FINISHED'}


# --- Menu ---
class TEXTIFY_MT_backup_menu(Menu):
    bl_label = "Backups"

    @classmethod
    def poll(cls, context):
        text = context.edit_text
        if not text:
            return False
        backups = list_backups_for_text(text)
        return bool(backups)

    def draw(self, context):
        layout = self.layout
        text = context.edit_text
        backups = list_backups_for_text(text)

        for backup in backups:
            op = layout.operator("textify.open_backup", text=backup.name, icon='WORDWRAP_ON')
            op.filepath = str(backup)


# --- Registration ---
classes = (
    TEXTIFY_OT_save_backup,
    TEXTIFY_OT_open_backup,
    TEXTIFY_MT_backup_menu,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)