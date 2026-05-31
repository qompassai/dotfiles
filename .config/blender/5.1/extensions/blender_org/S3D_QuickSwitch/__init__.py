import bpy
from bpy.props import CollectionProperty, StringProperty, EnumProperty, IntProperty
from bpy.types import PropertyGroup, Operator, UIList, AddonPreferences

# List of editor types
def tab_items():
    return [
        ('EMPTY', "Empty", "", 'CANCEL', 0),
        ('VIEW_3D', "3D Viewport", "", 'VIEW3D', 1),
        ('IMAGE_EDITOR', "Image Editor", "", 'IMAGE', 2),
        ('UV', "UV Editor", "", 'UV', 3),
        ('ShaderNodeTree', "Shader Editor", "", 'NODE_MATERIAL', 4),
        ('CompositorNodeTree', "Compositor", "", 'NODE_COMPOSITING', 5),
        ('TextureNodeTree', "Texture Node Editor", "", 'NODE_TEXTURE', 6),
        ('GeometryNodeTree', "Geometry Node Editor", "", 'NODETREE', 7),
        ('SEQUENCE_EDITOR', "Video Sequencer", "", 'SEQUENCE', 8),
        ('CLIP_EDITOR', "Movie Clip Editor", "", 'TRACKER', 9),
        ('DOPESHEET', "Dope Sheet", "", 'ACTION', 10),
        ('TIMELINE', "Timeline", "", 'TIME', 11),
        ('FCURVES', "Graph Editor", "", 'GRAPH', 12),
        ('DRIVERS', "Drivers", "", 'DRIVER', 13),
        ('NLA_EDITOR', "NLA Editor", "", 'NLA', 14),
        ('TEXT_EDITOR', "Text Editor", "", 'TEXT', 15),
        ('CONSOLE', "Python Console", "", 'CONSOLE', 16),
        ('INFO', "Info", "", 'INFO', 17),
        ('OUTLINER', "Outliner", "", 'OUTLINER', 18),
        ('PROPERTIES', "Properties", "", 'PROPERTIES', 19),
        ('SPREADSHEET', "Spreadsheet", "", 'SPREADSHEET', 20),
        ('PREFERENCES', "Preferences", "", 'PREFERENCES', 21),
        ('FILES', "File Browser", "", 'FILEBROWSER', 22),
        ('ASSETS', "Asset Browser", "", 'ASSET_MANAGER', 23),
    ]

# Property Groups
class EditorEntry(PropertyGroup):
    editor_type: EnumProperty(
        name="Editor Type",
        items=tab_items(),
        description="Type of editor to switch to when this entry is clicked",
    )

class EditorGroup(PropertyGroup):
    name: StringProperty(
        name="Group Name",
        description="Name of this editor group - helps organize related editors together",
        default="Group"
    )
    editors: CollectionProperty(
        type=EditorEntry,
        description="Collection of editor switches in this group"
    )
    active_editor_index: IntProperty(
        description="Index of the currently selected editor in this group"
    )

# UI List for Groups
class EDITOR_UL_Groups(UIList):
    """UI List that displays all editor groups"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False)

# UI List for Editors
class EDITOR_UL_Entries(UIList):
    """UI List that displays all editors in a group"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        
        # Display dropdown
        row.prop(item, "editor_type", text="", icon_only=True, emboss=True)
        
        # Retrieve the name of the enum item
        editor_name = item.bl_rna.properties['editor_type'].enum_items[item.editor_type].name
        
        # Display the editor name as a non-interactive label
        row.label(text=editor_name)

# Operators that handle the re ordering in EDITOR_UL_Entries
class OT_MoveEditorUp(Operator):
    """Move selected editor up in the list"""
    bl_idname = "scene.move_editor_up"
    bl_label = "Move Up"
    bl_description = "Move the selected editor switch up in the list"

    def execute(self, context):
        preferences = context.preferences.addons[__package__].preferences
        group = preferences.editor_groups[preferences.active_group_index]
        index = group.active_editor_index

        if index > 0:
            group.editors.move(index, index - 1)
            group.active_editor_index -= 1

            # Force a UI redraw for all areas
            for area in context.screen.areas:
                area.tag_redraw()

        return {'FINISHED'}

class OT_MoveEditorDown(Operator):
    """Move selected editor down in the list"""
    bl_idname = "scene.move_editor_down"
    bl_label = "Move Down"
    bl_description = "Move the selected editor switch down in the list"

    def execute(self, context):
        preferences = context.preferences.addons[__package__].preferences
        group = preferences.editor_groups[preferences.active_group_index]
        index = group.active_editor_index

        if index < len(group.editors) - 1:
            group.editors.move(index, index + 1)
            group.active_editor_index += 1

            # Force a UI redraw for all areas
            for area in context.screen.areas:
                area.tag_redraw()

        return {'FINISHED'}

# Core Operators
class OT_AddEditorGroup(Operator):
    bl_idname = "scene.add_editor_group"
    bl_label = "Add Editor Group"
    bl_description = "Add a new group of editor switches"

    def execute(self, context):
        preferences = context.preferences.addons[__package__].preferences
        new_group = preferences.editor_groups.add()
        new_group.name = f"Group {len(preferences.editor_groups)}"
        preferences.active_group_index = len(preferences.editor_groups) - 1
        return {'FINISHED'}

class OT_RemoveEditorGroup(Operator):
    bl_idname = "scene.remove_editor_group"
    bl_label = "Remove Editor Group"
    bl_description = "Remove the selected editor group"

    def execute(self, context):
        preferences = context.preferences.addons[__package__].preferences
        preferences.editor_groups.remove(preferences.active_group_index)
        preferences.active_group_index = max(0, preferences.active_group_index - 1)
        return {'FINISHED'}

class OT_AddEditorToGroup(Operator):
    bl_idname = "scene.add_editor_to_group"
    bl_label = "Add Editor to Group"
    bl_description = "Add a new editor switch to the selected group"

    def execute(self, context):
        preferences = context.preferences.addons[__package__].preferences
        group = preferences.editor_groups[preferences.active_group_index]
        group.editors.add()
        return {'FINISHED'}

class OT_RemoveEditorFromGroup(Operator):
    bl_idname = "scene.remove_editor_from_group"
    bl_label = "Remove Editor from Group"
    bl_description = "Remove the selected editor switch from the group"

    def execute(self, context):
        preferences = context.preferences.addons[__package__].preferences
        group = preferences.editor_groups[preferences.active_group_index]
        group.editors.remove(group.active_editor_index)
        group.active_editor_index = max(0, group.active_editor_index - 1)
        return {'FINISHED'}

class OT_SwitchEditor(Operator):
    bl_idname = "wm.switch_editor"
    bl_label = "Switch Editor"
    bl_description = "Switch to the selected editor type"

    editor_type: StringProperty(
        description="Type of editor to switch to"
    )

    def execute(self, context):
        # Prevent switching to EMPTY type which is just a placeholder
        if self.editor_type == 'EMPTY':
            self.report({'ERROR'}, "Cannot switch to Empty editor type. Please select a valid editor in preferences.")
            return {'CANCELLED'}
        
        # Try switching to the editor type
        try:
            context.area.ui_type = self.editor_type
            return {'FINISHED'}
        except TypeError as e:
            self.report({'ERROR'}, f"Invalid editor type: {self.editor_type}. Error: {str(e)}")
            return {'CANCELLED'}

# Add this new operator after the existing OT_SwitchEditor class
class OT_CycleEditors(Operator):
    bl_idname = "wm.cycle_editors"
    bl_label = "Cycle Through Editors"
    bl_description = "Cycle to the next editor in the current editor group"
    
    def execute(self, context):
        preferences = context.preferences.addons[__package__].preferences
        current_type = context.area.ui_type
        
        # Find the active group that contains the current editor
        active_group = None
        editors_list = []
        
        for group in preferences.editor_groups:
            for editor in group.editors:
                if editor.editor_type == current_type:
                    active_group = group
                    # Get the list of editors in this group
                    editors_list = [e.editor_type for e in group.editors if e.editor_type != 'EMPTY']
                    break
            if active_group:
                break
        
        if not active_group or not editors_list:
            self.report({'WARNING'}, "Current editor is not in any group or group is empty")
            return {'CANCELLED'}
        
        # Find the current editor's position and determine the next one
        try:
            current_index = editors_list.index(current_type)
            next_index = (current_index + 1) % len(editors_list)  # Wrap around to first item
            next_type = editors_list[next_index]
            
            # Switch to the next editor type
            context.area.ui_type = next_type
            return {'FINISHED'}
            
        except ValueError:
            self.report({'ERROR'}, f"Could not find editor {current_type} in group")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error cycling editors: {str(e)}")
            return {'CANCELLED'}

# Callback functions for preference updates
def update_shortcuts(self, context):
    # Clear existing shortcuts
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    # Register with the new settings
    register_shortcuts()

# Preferences Panel
class VIEW3D_PT_QuickSwitchPreferences(AddonPreferences):
    bl_idname = __package__

    show_separator: bpy.props.BoolProperty(
        name="Separator",
        description="Enable or disable the visual separator between the editor switches and other header operators",
        default=True,
    )
    
    switch_position: bpy.props.EnumProperty(
        name="Switch Position",
        description="Position switches on the left or right side of the header",
        items=[
            ('LEFT', "Left", "Position switches on the left side, after editor type dropdown"),
            ('RIGHT', "Right", "Position switches on the right side (default)"),
        ],
        default='RIGHT',
    )
    
    # Shortcut key preferences
    use_shortcuts: bpy.props.BoolProperty(
        name="Enable Keyboard Shortcuts",
        description="Enable keyboard shortcuts for cycling through editors",
        default=True,
        update=update_shortcuts
    )
    
    cycle_shortcut_key: bpy.props.EnumProperty(
        name="Key",
        description="Key to use for cycling through editors",
        items=[
            ('SPACE', "Space", "Use Space for editor cycling"),
            ('QUOTE', "Quote (')", "Use quote (') for editor cycling"),
            ('ACCENT_GRAVE', "Backtick (`)", "Use backtick (`) for editor cycling"),
            ('PERIOD', "Period (.)", "Use period (.) for editor cycling"),
            ('COMMA', "Comma (,)", "Use comma (,) for editor cycling"),
            ('A', "A", "Use A for editor cycling"),
            ('Q', "Q", "Use Q for editor cycling"),
            ('W', "W", "Use W for editor cycling"),
            ('E', "E", "Use E for editor cycling"),
            ('S', "S", "Use S for editor cycling"),
            ('D', "D", "Use D for editor cycling"),
            ('F', "F", "Use F for editor cycling"),
            ('X', "X", "Use X for editor cycling"),
            ('Z', "Z", "Use Z for editor cycling"),
        ],
        default='ACCENT_GRAVE',
        update=update_shortcuts
    )

    cycle_shortcut_modifier: bpy.props.EnumProperty(
        name="Modifier",
        description="Modifier key to combine with the selected key",
        items=[
            ('CTRL', "Ctrl", "Use Ctrl as the modifier key"),
            ('ALT', "Alt", "Use Alt as the modifier key"),
            ('SHIFT', "Shift", "Use Shift as the modifier key"),
            ('NONE', "None", "Don't use a modifier key"),
            ('CTRL_ALT', "Ctrl+Alt", "Use Ctrl+Alt as the modifier keys"),
            ('CTRL_SHIFT', "Ctrl+Shift", "Use Ctrl+Shift as the modifier keys"),
            ('ALT_SHIFT', "Alt+Shift", "Use Alt+Shift as the modifier keys"),
        ],
        default='ALT',
        update=update_shortcuts
    )

    # Add editor groups to preferences
    editor_groups: CollectionProperty(
        type=EditorGroup,
        description="List of all editor groups configured in this addon"
    )
    active_group_index: IntProperty(
        description="Index of the currently selected editor group"
    )

    def draw(self, context):
        layout = self.layout

        # Split the layout into two columns for the lists
        split = layout.split(factor=0.5)

        # Group List
        col = split.column()
        col.label(text="Editor Groups")

        row = col.row()
        row.template_list(
            "EDITOR_UL_Groups", "", 
            self, "editor_groups", 
            self, "active_group_index",
            rows=7
        )

        row = col.row(align=True)
        row.operator("scene.add_editor_group", text="Add", icon="ADD")
        row.operator("scene.remove_editor_group", text="Remove", icon="REMOVE")

        # Switch List
        col = split.column()
        col.label(text="Editor Switches")

        if self.editor_groups and len(self.editor_groups) > 0:
            group = self.editor_groups[self.active_group_index]
            
            row = col.row()
            row.template_list(
                "EDITOR_UL_Entries", "", 
                group, "editors", 
                group, "active_editor_index",
                rows=7
            )

            row = col.row(align=True)
            row.operator("scene.add_editor_to_group", text="Add", icon="ADD")
            row.operator("scene.remove_editor_from_group", text="Remove", icon="REMOVE")
            
            # Add move up/down button
            row.separator_spacer()
            row.operator("scene.move_editor_up", text="Up", icon="TRIA_UP")
            row.operator("scene.move_editor_down", text="Down", icon="TRIA_DOWN")


        # Position and separator options
        box = layout.box()
        
        # Create a row and split it 50/50
        row = box.row()
        split = row.split(factor=0.5)
        
        # Left side: Label and toggle in one row
        left_col = split.column()
        left_row = left_col.row()
        left_row.label(text="Switch Position:")
        left_row.prop(self, "switch_position", expand=True)
        
        # Right side: Separator checkbox
        right_col = split.column()
        right_col.prop(self, "show_separator")
        
        # Add shortcut preferences in a new box
        box = layout.box()
        box.label(text="Keyboard Shortcuts", icon='KEYINGSET')
        
        row = box.row()
        row.prop(self, "use_shortcuts")
        
        # Only show key selection if shortcuts are enabled
        if self.use_shortcuts:
            # A row for selecting the modifier key
            row = box.row()
            row.label(text="Cycle Editors:")
            
            # Create two columns for the modifier and key
            split = row.split(factor=0.5)
            split.prop(self, "cycle_shortcut_modifier", text="")
            split.prop(self, "cycle_shortcut_key", text="")
            
            # Add helpful explanation
            row = box.row()
            
            # Get user-friendly modifier name
            modifier_text = ""
            if self.cycle_shortcut_modifier == 'CTRL':
                modifier_text = "Ctrl+"
            elif self.cycle_shortcut_modifier == 'ALT':
                modifier_text = "Alt+"
            elif self.cycle_shortcut_modifier == 'SHIFT':
                modifier_text = "Shift+"
            elif self.cycle_shortcut_modifier == 'CTRL_ALT':
                modifier_text = "Ctrl+Alt+"
            elif self.cycle_shortcut_modifier == 'CTRL_SHIFT':
                modifier_text = "Ctrl+Shift+"
            elif self.cycle_shortcut_modifier == 'ALT_SHIFT':
                modifier_text = "Alt+Shift+"
            
            # Get user-friendly key name
            key_text = ""
            if self.cycle_shortcut_key == 'ACCENT_GRAVE':
                key_text = "Backtick (`)"
            elif self.cycle_shortcut_key == 'QUOTE':
                key_text = "Quote (')"
            elif self.cycle_shortcut_key == 'COMMA':
                key_text = "Comma (,)"
            elif self.cycle_shortcut_key == 'PERIOD':
                key_text = "Period (.)"
            else:
                key_text = self.cycle_shortcut_key
                
            row.label(text=f"Press {modifier_text}{key_text} to cycle through editors in a group")
            
            # Warning about possible conflicts
            if self.cycle_shortcut_key == 'TAB' and self.cycle_shortcut_modifier == 'CTRL':
                row = box.row()
                row.label(text="Warning: Ctrl+Tab conflicts with Blender's built-in shortcuts", icon='ERROR')

# Draw UI Switches in Headers
def draw_tab_switcher_btn(self, context):
    layout = self.layout
    preferences = context.preferences.addons[__package__].preferences
    
    # Only draw on the right side if that option is enabled
    if preferences.switch_position == 'RIGHT':
        # Check if there are any editor groups
        if len(preferences.editor_groups) == 0:
            return

        # Find if there are any switches for the current editor type
        found_switches = False
        for group in preferences.editor_groups:
            for editor in group.editors:
                if context.area.ui_type == editor.editor_type:
                    found_switches = True
                    break
            if found_switches:
                break
        
        # Exit if no switches found for this editor
        if not found_switches:
            return
            
        row = layout.row(align=True)
        
        # Special Case for Console, Info, Spreadsheet (push to far right)
        if context.area.ui_type in {'CONSOLE', 'INFO', 'SPREADSHEET', 'ASSETS', 'FILES'}:
            row.separator_spacer()
        
        # Enable / Disable Separator (before switches for right position)
        if preferences.show_separator:
            row.label(text="||")  # Visual separator only when needed
        
        # Create a box to hold the buttons
        box = row.box()
        switch_row = box.row(align=True)
        
        # Find the active editor group and draw its switches
        for group in preferences.editor_groups:
            for editor in group.editors:
                if context.area.ui_type == editor.editor_type:
                    for e in group.editors:
                        # Get the icon and name for the tooltip
                        icon = next((item[3] for item in tab_items() if item[0] == e.editor_type), 'NONE')
                        name = next((item[1] for item in tab_items() if item[0] == e.editor_type), 'Unknown')
                        is_active = context.area.ui_type == e.editor_type
                        
                        # Create operator with proper tooltip
                        op = switch_row.operator(
                            "wm.switch_editor", 
                            text="", 
                            icon=icon, 
                            depress=is_active,
                            # Add tooltip for each switch
                            text_ctxt=f"Switch to {name}"
                        )
                        op.editor_type = e.editor_type
                    
                    return

# Left side drawing function
def draw_left_switches(self, context):
    # Only draw on the left side if that option is enabled
    preferences = context.preferences.addons[__package__].preferences
    if preferences.switch_position == 'LEFT':
        # Check if there are any editor groups
        if len(preferences.editor_groups) == 0:
            return

        # Find if there are any switches for the current editor type
        found_switches = False
        for group in preferences.editor_groups:
            for editor in group.editors:
                if context.area.ui_type == editor.editor_type:
                    found_switches = True
                    break
            if found_switches:
                break
        
        # Exit if no switches found for this editor
        if not found_switches:
            return
            
        layout = self.layout
        row = layout.row(align=True)
        
        # Create a box to hold the buttons
        box = row.box()
        switch_row = box.row(align=True)
        
        # Find the active editor group and draw its switches
        for group in preferences.editor_groups:
            for editor in group.editors:
                if context.area.ui_type == editor.editor_type:
                    for e in group.editors:
                        # Get the icon and name for the tooltip
                        icon = next((item[3] for item in tab_items() if item[0] == e.editor_type), 'NONE')
                        name = next((item[1] for item in tab_items() if item[0] == e.editor_type), 'Unknown')
                        is_active = context.area.ui_type == e.editor_type
                        
                        # Create operator with proper tooltip
                        op = switch_row.operator(
                            "wm.switch_editor", 
                            text="", 
                            icon=icon, 
                            depress=is_active,
                            # Add tooltip for each switch
                            text_ctxt=f"Switch to {name}"
                        )
                        op.editor_type = e.editor_type
                    
                    # Enable / Disable Separator (after switches for left position)
                    if preferences.show_separator:
                        row.label(text="||")  # Visual separator only when needed
                    
                    return

# Add the keyboard shortcut management
def get_hotkey_entry_item(km, kmi_name, kmi_value):
    """Find a keymap item by name and value"""
    for i, km_item in enumerate(km.keymap_items):
        if km_item.idname == kmi_name and km_item.properties.get("name", "") == kmi_value:
            return km_item
    return None

# Keymap storage - will be used to keep track of our shortcuts
addon_keymaps = []

# Class List
classes = [
    EditorEntry,
    EditorGroup,
    OT_MoveEditorUp,
    OT_MoveEditorDown,
    VIEW3D_PT_QuickSwitchPreferences,
    EDITOR_UL_Groups,
    EDITOR_UL_Entries,
    OT_AddEditorGroup,
    OT_RemoveEditorGroup,
    OT_AddEditorToGroup,
    OT_RemoveEditorFromGroup,
    OT_SwitchEditor,
    OT_CycleEditors,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # No longer register scene properties as we're using addon preferences now
    # bpy.types.Scene.editor_groups = CollectionProperty(type=EditorGroup)
    # bpy.types.Scene.active_group_index = IntProperty()
    
    # Migration code: If there are existing groups in the scene, move them to preferences
    # Use a deferred execution approach for migration to avoid context issues
    bpy.app.timers.register(migrate_scene_data_to_preferences, first_interval=0.5)
    
    # Get all supported headers
    headers = [
        bpy.types.NODE_HT_header, bpy.types.DOPESHEET_HT_header, bpy.types.PROPERTIES_HT_header,
        bpy.types.OUTLINER_HT_header, bpy.types.SPREADSHEET_HT_header, bpy.types.IMAGE_HT_header,
        bpy.types.VIEW3D_HT_header, bpy.types.USERPREF_HT_header, bpy.types.CONSOLE_HT_header,
        bpy.types.TEXT_HT_header, bpy.types.GRAPH_HT_header, bpy.types.SEQUENCER_HT_header,
        bpy.types.CLIP_HT_header, bpy.types.NLA_HT_header, bpy.types.INFO_HT_header,
        bpy.types.FILEBROWSER_HT_header,
    ]
    
    # Register both drawing functions
    for header in headers:
        # This is drawn first on the left side
        header.prepend(draw_left_switches)
        # This is drawn last on the right side
        header.append(draw_tab_switcher_btn)
        
    # Register keyboard shortcuts - we'll handle this in a separate function
    # that we can call when preferences change too
    register_shortcuts()

# Deferred migration function to run after the addon is fully registered
def migrate_scene_data_to_preferences():
    # Try to access the current scene safely
    try:
        scene = bpy.context.scene
        # Make sure the addon is registered and we can access preferences
        if __package__ in bpy.context.preferences.addons:
            preferences = bpy.context.preferences.addons[__package__].preferences
            
            # Check if scene has the properties we need to migrate
            if hasattr(scene, "editor_groups") and hasattr(scene, "active_group_index"):
                # Only migrate if we have groups to migrate and the preferences are empty
                if len(preferences.editor_groups) == 0 and len(scene.editor_groups) > 0:
                    for group in scene.editor_groups:
                        new_group = preferences.editor_groups.add()
                        new_group.name = group.name
                        
                        # Copy editors for this group
                        for editor in group.editors:
                            new_editor = new_group.editors.add()
                            new_editor.editor_type = editor.editor_type
                    
                    # Set active group index
                    preferences.active_group_index = scene.active_group_index
                    
                    print(f"Migrated {len(scene.editor_groups)} editor groups to addon preferences")
    except Exception as e:
        print(f"Error during migration: {e}")
    
    # Return None to prevent the timer from repeating
    return None

# Add a function to register shortcuts
def register_shortcuts():
    # Get preferences
    prefs = None
    try:
        if __package__ in bpy.context.preferences.addons:
            prefs = bpy.context.preferences.addons[__package__].preferences
    except:
        return
    
    # Only register if shortcuts are enabled
    if not prefs or not prefs.use_shortcuts:
        return
        
    # Get active keyconfig
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    
    if kc:
        # Define keymap for window
        km = kc.keymaps.new(name="Window", space_type='EMPTY', region_type='WINDOW')
        
        # Create a new shortcut based on the modifier selection
        kwargs = {
            "idname": "wm.cycle_editors",
            "type": prefs.cycle_shortcut_key,
            "value": 'PRESS',
        }
        
        # Add modifiers based on the selected option
        if prefs.cycle_shortcut_modifier == 'CTRL':
            kwargs["ctrl"] = True
        elif prefs.cycle_shortcut_modifier == 'ALT':
            kwargs["alt"] = True
        elif prefs.cycle_shortcut_modifier == 'SHIFT':
            kwargs["shift"] = True
        elif prefs.cycle_shortcut_modifier == 'CTRL_ALT':
            kwargs["ctrl"] = True
            kwargs["alt"] = True
        elif prefs.cycle_shortcut_modifier == 'CTRL_SHIFT':
            kwargs["ctrl"] = True
            kwargs["shift"] = True
        elif prefs.cycle_shortcut_modifier == 'ALT_SHIFT':
            kwargs["alt"] = True
            kwargs["shift"] = True
        # For 'NONE', we don't add any modifier
        
        # Create the keymap item
        kmi = km.keymap_items.new(**kwargs)
        
        # Store the shortcut
        addon_keymaps.append((km, kmi))

def unregister():
    # Get all supported headers
    headers = [
        bpy.types.NODE_HT_header, bpy.types.DOPESHEET_HT_header, bpy.types.PROPERTIES_HT_header,
        bpy.types.OUTLINER_HT_header, bpy.types.SPREADSHEET_HT_header, bpy.types.IMAGE_HT_header,
        bpy.types.VIEW3D_HT_header, bpy.types.USERPREF_HT_header, bpy.types.CONSOLE_HT_header,
        bpy.types.TEXT_HT_header, bpy.types.GRAPH_HT_header, bpy.types.SEQUENCER_HT_header,
        bpy.types.CLIP_HT_header, bpy.types.NLA_HT_header, bpy.types.INFO_HT_header,
        bpy.types.FILEBROWSER_HT_header,
    ]
    
    # Remove both draw functions
    for header in headers:
        try:
            header.remove(draw_tab_switcher_btn)
        except Exception:
            pass
            
        try:
            header.remove(draw_left_switches)
        except Exception:
            pass

    # Clean up the scene properties if they exist
    if hasattr(bpy.types.Scene, "editor_groups"):
        try:
            del bpy.types.Scene.editor_groups
        except Exception:
            pass
            
    if hasattr(bpy.types.Scene, "active_group_index"):
        try:
            del bpy.types.Scene.active_group_index
        except Exception:
            pass
            
    # Clean up keyboard shortcuts
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __package__ == "__main__":
    register() 