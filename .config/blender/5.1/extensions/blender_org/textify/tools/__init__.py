import importlib
import os
import sys

# Get the package directory
package_dir = os.path.dirname(__file__)
package_name = __package__

submodules = []

def load_submodules():
    global submodules
    submodules.clear()

    for filename in os.listdir(package_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]  # remove .py extension
            full_name = f"{package_name}.{module_name}"

            # Reload if already imported
            if full_name in sys.modules:
                module = importlib.reload(sys.modules[full_name])
            else:
                module = importlib.import_module(full_name)

            submodules.append(module)

# Load on import
load_submodules()

def register():
    for mod in submodules:
        if hasattr(mod, "register"):
            mod.register()

def unregister():
    for mod in reversed(submodules):
        if hasattr(mod, "unregister"):
            try:
                mod.unregister()
            except Exception as e:
                print(f"Error unregistering {mod.__name__}: {e}")
