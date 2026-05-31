import bpy
import os


def resolve_active_library(require_explicit=False, verbose=False):
    """
    Return the active user asset library (bpy.types.AssetLibraryReference-like object),
    or None if it cannot be resolved.

    If require_explicit is False and exactly one user library exists, it will be used
    as a fallback.
    """
    def log(msg):
        if verbose:
            print(f"[Asset Library Tools][resolve] {msg}")

    def iter_asset_browser_spaces():
        # Prefer current space_data if it is an ASSETS browser
        space_ctx = getattr(bpy.context, "space_data", None)
        if space_ctx and getattr(space_ctx, "browse_mode", None) == "ASSETS":
            yield space_ctx

        wm = bpy.context.window_manager
        if not wm:
            return

        for win in wm.windows:
            screen = getattr(win, "screen", None)
            if not screen:
                continue
            for area in screen.areas:
                if area.type != "FILE_BROWSER":
                    continue
                for space in area.spaces:
                    if getattr(space, "browse_mode", None) == "ASSETS":
                        if space is not space_ctx:
                            yield space

    prefs = bpy.context.preferences.filepaths
    user_libs = list(getattr(prefs, "asset_libraries", []))

    def by_name(name):
        if not name:
            return None
        for lib in user_libs:
            if lib.name == name:
                return lib
        for lib in user_libs:
            if lib.name.lower() == str(name).lower():
                return lib
        return None

    def by_path(directory):
        if not directory:
            return None
        try:
            dir_abs = bpy.path.abspath(directory)
        except Exception:
            dir_abs = directory

        for lib in user_libs:
            lib_abs = bpy.path.abspath(lib.path)
            try:
                if os.path.commonpath([lib_abs, dir_abs]) == lib_abs:
                    return lib
            except Exception:
                # commonpath can raise if drives differ, etc.
                pass
        return None

    # First, try to resolve from any ASSETS File Browser
    for space in iter_asset_browser_spaces():
        params = getattr(space, "params", None)
        attr_candidates = []
        if params:
            attr_candidates.extend([
                getattr(params, "asset_library_reference", None),
                getattr(params, "asset_library_ref", None),
                getattr(params, "asset_library_identifier", None),
                getattr(params, "asset_library_custom", None),
            ])
        # Some Blender versions store it directly on the space
        attr_candidates.append(getattr(space, "asset_library_reference", None))
        attr_candidates.append(getattr(space, "asset_library_ref", None))

        # Try name-based resolution
        for ref in attr_candidates:
            if ref and ref not in {"LOCAL", "ALL", "ESSENTIALS"}:
                lib = by_name(ref)
                if lib:
                    try:
                        log(f"Resolved by name: {ref} -> {bpy.path.abspath(lib.path)}")
                    except Exception:
                        log(f"Resolved by name: {ref} -> {lib.path}")
                    return lib

        # Fallback: resolve by directory
        directory = getattr(params, "directory", None) if params else None
        lib_by_dir = by_path(directory)
        if lib_by_dir:
            log(f"Resolved by directory: {directory} -> {lib_by_dir.name}")
            return lib_by_dir

    # If exactly one user library exists and explicit resolution is not required, use it.
    if len(user_libs) == 1 and not require_explicit:
        log(f"Falling back to single library: {user_libs[0].name}")
        return user_libs[0]

    log("Failed to resolve active library.")
    return None


def get_active_library_path(require_explicit=False, verbose=False):
    """
    Convenience wrapper: return the absolute path to the active asset library,
    or None if not resolved.
    """
    lib = resolve_active_library(require_explicit=require_explicit, verbose=verbose)
    if not lib:
        return None
    try:
        return bpy.path.abspath(lib.path)
    except Exception:
        return lib.path
