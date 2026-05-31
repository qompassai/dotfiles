from . import core
from . import ui

def register():
    # 1. Register Core Logic 
    # (Handles Tag Filter & Catalogue Backup operators and properties)
    core.register_core()
    
    # 2. Register UI State 
    # (Handles Catalogue Backup toggle properties)
    core.ui_state.register_ui_state()
    
    # 3. Register Main UI 
    # (Handles the Side Panel)
    ui.register_ui()

def unregister():
    ui.unregister_ui()
    core.ui_state.unregister_ui_state()
    core.unregister_core()