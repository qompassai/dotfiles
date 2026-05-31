bl_info = {
    "name": "Maya Pivot",
    "category": "Mesh",
    "author": "Zinkenite",
    "description": "Implements features for the 3D cursor inspired by Maya's pivot system",
    "version": (1, 0),
}

from . import Maya_Pivot

def register():
    Maya_Pivot.register()

def unregister():
    Maya_Pivot.unregister()

if __name__ == "__main__":
    register() 