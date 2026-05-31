import bpy
import os
import json
import traceback
from bpy.types import PropertyGroup, Operator
from bpy.props import StringProperty, IntProperty, BoolProperty

# Folder name for storing data files inside the library
DATA_DIR_NAME = "_ALT_data"

# ===================================================================
# LOGIC: Asset Type Filter
# ===================================================================

ASSET_TYPES = [
    ("OBJECT", "Object", 'OBJECT_DATA'),
    ("MATERIAL", "Material", 'MATERIAL'),
    ("COLLECTION", "Collection", 'OUTLINER_COLLECTION'),
    ("WORLD", "World", 'WORLD'),
    ("NODE_TREE", "Node Tree", 'NODETREE'),
    ("ACTION", "Action", 'ACTION'),
]

KNOWN_TYPE_MAPPING = {
    "OBJECT": "filter_object",
    "MATERIAL": "filter_material",
    "COLLECTION": "filter_group",
    "WORLD": "filter_world",
    "NODE_TREE": "filter_node_tree",
    "ACTION": "filter_action",
}

TYPE_KEYWORDS = {
    "OBJECT": ["object"],
    "MATERIAL": ["material"],
    "COLLECTION": ["collection", "coll", "group"],
    "WORLD": ["world"],
    "NODE_TREE": ["node_tree", "nodetree", "node", "tree"],
    "ACTION": ["action"],
}

def get_asset_space(context):
    """Return active SpaceFileBrowser in Asset Browser mode, or None."""
    space = getattr(context, "space_data", None)
    if space and space.type == 'FILE_BROWSER':
        if getattr(space, "ui_type", None) == 'ASSETS' or getattr(space, "browse_mode", None) == 'ASSETS':
            return space

    win = getattr(context, "window", None)
    screen = getattr(win, "screen", None)
    if not screen:
        return None

    for area in screen.areas:
        if area.type != 'FILE_BROWSER':
            continue
        sp = area.spaces.active
        if getattr(sp, "ui_type", None) == 'ASSETS' or getattr(sp, "browse_mode", None) == 'ASSETS':
            return sp

    return None

def get_asset_params(context):
    space = get_asset_space(context)
    return getattr(space, "params", None) if space else None

def tag_redraw_asset_browser(context):
    win = getattr(context, "window", None)
    screen = getattr(win, "screen", None)
    if not screen:
        return
    for area in screen.areas:
        if area.type == 'FILE_BROWSER':
            area.tag_redraw()

def _rna_bool_props(obj, prefix="filter"):
    props = []
    rna = getattr(obj, "bl_rna", None)
    if not rna:
        return props

    for p in rna.properties:
        if p.identifier == "rna_type":
            continue
        if prefix and not p.identifier.startswith(prefix):
            continue
        if getattr(p, "type", None) == 'BOOLEAN':
            props.append(p.identifier)

    return props

def _resolve_filter_attr(filter_struct, asset_type, bool_filters):
    kws = TYPE_KEYWORDS.get(asset_type, [])
    if not kws:
        return None

    for kw in kws:
        kw = kw.lower()
        for name in bool_filters:
            low = name.lower()
            if kw in low:
                if asset_type == "COLLECTION" and "collapse" in low:
                    continue
                return name

    if asset_type == "NODE_TREE":
        for name in bool_filters:
            low = name.lower()
            if "node" in low and "tree" in low:
                return name

    return None

def _fast_mapping_available(filt):
    for attr in KNOWN_TYPE_MAPPING.values():
        if not hasattr(filt, attr):
            return False
    return True

def _set_filter_asset_id(params, asset_type=None):
    filt = getattr(params, "filter_asset_id", None)
    if not filt:
        return False

    bool_filters = _rna_bool_props(filt, prefix="filter")
    if not bool_filters:
        return False

    # Turn everything OFF first
    for n in bool_filters:
        try:
            setattr(filt, n, False)
        except Exception:
            pass

    # If None passed (Show All), turn everything ON
    if asset_type is None:
        for n in bool_filters:
            try:
                setattr(filt, n, True)
            except Exception:
                pass
        return True

    # Try fast path
    if _fast_mapping_available(filt):
        target = KNOWN_TYPE_MAPPING.get(asset_type)
        if target and hasattr(filt, target):
            try:
                setattr(filt, target, True)
                return True
            except Exception:
                pass

    # Try heuristic resolution
    target = _resolve_filter_attr(filt, asset_type, bool_filters)
    if not target:
        return False

    try:
        setattr(filt, target, True)
    except Exception:
        return False

    return True

def _set_asset_type_enum(params, asset_type=None):
    if not hasattr(params, "asset_type"):
        return False

    if asset_type is None:
        for candidate in ("NONE", "", "OBJECT"):
            try:
                params.asset_type = candidate
                return True
            except Exception:
                continue
        return False

    try:
        params.asset_type = asset_type
        return True
    except Exception:
        return False

def set_asset_type_filter(context, asset_type=None):
    params = get_asset_params(context)
    if not params:
        return False, "Asset Browser params not found (open Asset Browser and click inside it)."

    if _set_filter_asset_id(params, asset_type=asset_type):
        return True, None

    if _set_asset_type_enum(params, asset_type=asset_type):
        return True, None

    return False, "No compatible asset-type filter property found on this Blender build."

def _late_reapply(asset_type):
    try:
        set_asset_type_filter(bpy.context, asset_type)
        tag_redraw_asset_browser(bpy.context)
    except Exception:
        pass
    return None

class ATFT_OT_SetAssetType(Operator):
    bl_idname = "atf_type.set_asset_type"
    bl_label = "Set Asset Type"
    bl_options = {'REGISTER'}

    asset_type: StringProperty(default="OBJECT")

    def execute(self, context):
        ok, err = set_asset_type_filter(context, self.asset_type)
        if not ok:
            self.report({'ERROR'}, err)
            return {'CANCELLED'}

        # Timer needed to fight UI normalization
        bpy.app.timers.register(lambda: _late_reapply(self.asset_type), first_interval=0.01)
        tag_redraw_asset_browser(context)
        return {'FINISHED'}

class ATFT_OT_AllTypes(Operator):
    bl_idname = "atf_type.all_types"
    bl_label = "All Types"
    bl_options = {'REGISTER'}

    def execute(self, context):
        ok, err = set_asset_type_filter(context, None)
        if not ok:
            self.report({'ERROR'}, err)
            return {'CANCELLED'}

        bpy.app.timers.register(lambda: _late_reapply(None), first_interval=0.01)
        tag_redraw_asset_browser(context)
        return {'FINISHED'}


# ===================================================================
# LOGIC: Asset Tag Filter
# ===================================================================

SEARCH_PROP_CANDIDATES = (
    "asset_filter_search",
    "search_filter",
    "filter_search",
    "search_string",
)

def _get_search_prop(params):
    for name in SEARCH_PROP_CANDIDATES:
        if hasattr(params, name):
            return name
    return None

def set_asset_browser_search(text: str):
    wm = bpy.context.window_manager
    for win in wm.windows:
        scr = win.screen
        if not scr:
            continue
        for area in scr.areas:
            if area.type != "FILE_BROWSER":
                continue
            space = area.spaces.active
            if getattr(space, "browse_mode", "") != "ASSETS":
                continue
            params = getattr(space, "params", None)
            if not params:
                continue
            if hasattr(params, "use_filter"):
                params.use_filter = True
            pname = _get_search_prop(params)
            if pname:
                try:
                    setattr(params, pname, text)
                except (AttributeError, TypeError):
                    pass
            area.tag_redraw()

def get_asset_browser_search():
    wm = bpy.context.window_manager
    for win in wm.windows:
        scr = win.screen
        if not scr:
            continue
        for area in scr.areas:
            if area.type != "FILE_BROWSER":
                continue
            space = area.spaces.active
            if getattr(space, "browse_mode", "") != "ASSETS":
                continue
            params = getattr(space, "params", None)
            if not params:
                continue
            pname = _get_search_prop(params)
            if pname and hasattr(params, pname):
                try:
                    return getattr(params, pname, "")
                except (AttributeError, TypeError):
                    return ""
    return ""

def get_active_asset_library_ref_and_path(context):
    space = getattr(context, "space_data", None)
    if not space or getattr(space, "browse_mode", "") != "ASSETS":
        return None, None

    params = getattr(space, "params", None)
    if not params:
        return None, None

    lib_ref = getattr(params, "asset_library_reference", None)
    if lib_ref in {None, "", "LOCAL", "ESSENTIALS", "ALL"}:
        return lib_ref, None

    prefs = bpy.context.preferences
    lib_path = None
    if hasattr(prefs, "filepaths") and hasattr(prefs.filepaths, "asset_libraries"):
        for lib in prefs.filepaths.asset_libraries:
            if lib.name == lib_ref:
                lib_path = bpy.path.abspath(lib.path)
                break

    return lib_ref, lib_path

def get_library_json_path(lib_path):
    if not lib_path:
        return None
    # Use the dedicated subfolder
    return os.path.join(lib_path, DATA_DIR_NAME, "asset_tag_filter.json")

def read_library_json(context):
    asset_count = 0
    tag_count = 0
    tags = []

    lib_ref, lib_path = get_active_asset_library_ref_and_path(context)
    if not lib_path:
        return asset_count, tag_count, tags

    json_path = get_library_json_path(lib_path)
    if not json_path or not os.path.exists(json_path):
        return asset_count, tag_count, tags

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return asset_count, tag_count, tags

    tags = data.get("tags", []) or []
    tags = sorted(set(tags), key=str.lower)

    asset_count = int(data.get("asset_count", 0))
    tag_count = int(data.get("tag_count", len(tags)))

    return asset_count, tag_count, tags

def is_lib_writable(lib_path):
    if not lib_path or not os.path.exists(lib_path):
        return False
    return os.access(lib_path, os.W_OK)

def get_user_json_path(lib_path):
    if not lib_path:
        return None
    # Use the dedicated subfolder
    return os.path.join(lib_path, DATA_DIR_NAME, "asset_tag_filter_user.json")

def read_user_json(context):
    _lib_ref, lib_path = get_active_asset_library_ref_and_path(context)
    if not lib_path:
        return {"pinned": []}

    path = get_user_json_path(lib_path)
    if not path or not os.path.exists(path):
        return {"pinned": []}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"pinned": []}

    if not isinstance(data, dict):
        data = {}

    pinned = data.get("pinned", [])
    if not isinstance(pinned, list):
        pinned = []

    data["pinned"] = [str(t) for t in pinned]
    return data

def write_user_json(context, data):
    _lib_ref, lib_path = get_active_asset_library_ref_and_path(context)
    if not lib_path:
        return False

    path = get_user_json_path(lib_path)
    if not path:
        return False

    try:
        # Ensure the DATA_DIR_NAME folder exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False

def get_pinned_tags_for_lib(context):
    data = read_user_json(context)
    return [t for t in data.get("pinned", []) if isinstance(t, str)]

def add_pinned_tag_for_lib(context, tag: str, max_items: int = 6):
    tag = (tag or "").strip()
    if not tag:
        return False

    data = read_user_json(context)
    pinned = [t for t in data.get("pinned", []) if isinstance(t, str)]

    if tag in pinned:
        return True

    pinned.append(tag)
    if len(pinned) > max_items:
        pinned = pinned[-max_items:]

    data["pinned"] = pinned
    return write_user_json(context, data)

def remove_pinned_tag_for_lib(context, tag: str):
    tag = (tag or "").strip()
    if not tag:
        return False

    data = read_user_json(context)
    pinned = [t for t in data.get("pinned", []) if isinstance(t, str)]
    if tag not in pinned:
        return True

    pinned = [t for t in pinned if t != tag]
    data["pinned"] = pinned
    return write_user_json(context, data)

def clear_pinned_tags_for_lib(context):
    data = read_user_json(context)
    data["pinned"] = []
    return write_user_json(context, data)

def _split_tag_list(s):
    if not s:
        return []
    return [t for t in s.split("|") if t]

def _join_tag_list(lst):
    return "|".join(dict.fromkeys(lst))

def _get_recent_map(props):
    raw = props.recent_by_lib or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return data

def _set_recent_map(props, data):
    try:
        props.recent_by_lib = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        props.recent_by_lib = "{}"

def get_recent_tags_for_lib(context, props):
    lib_ref, _ = get_active_asset_library_ref_and_path(context)
    if not lib_ref:
        return []

    data = _get_recent_map(props)
    s = data.get(lib_ref, "")
    return _split_tag_list(s)

def set_recent_tags_for_lib(context, props, tags_list):
    lib_ref, _ = get_active_asset_library_ref_and_path(context)
    if not lib_ref:
        return
    data = _get_recent_map(props)
    data[lib_ref] = _join_tag_list(tags_list)
    _set_recent_map(props, data)

def add_recent_tag(context, props, tag: str, max_items: int = 10):
    tag = (tag or "").strip()
    if not tag:
        return

    items = get_recent_tags_for_lib(context, props)
    items = [t for t in items if t != tag]
    items.insert(0, tag)
    if len(items) > max_items:
        items = items[:max_items]

    set_recent_tags_for_lib(context, props, items)


class ATF_Props(PropertyGroup):
    asset_count: IntProperty(
        name="Indexed Asset Count",
        default=0,
        options={"SKIP_SAVE"},
    )
    tag_count: IntProperty(
        name="Indexed Tag Count",
        default=0,
        options={"SKIP_SAVE"},
    )
    recent_by_lib: StringProperty(
        name="Recent Tags By Library",
        default="{}",
        options={"SKIP_SAVE"},
    )
    show_indexer: BoolProperty(
        name="Show Indexer",
        default=False,
        description="Toggle visibility of the Tag Indexer tools",
        options={"SKIP_SAVE"},
    )


# --- VALIDATION LOGIC ---

def get_clean_name(name):
    """
    Remove common suffixes and extensions to allow better comparison.
    Examples:
    'FoodCoconut001_4k_Instance' -> 'foodcoconut001'
    'Concrete.jpg' -> 'concrete'
    """
    clean = name.lower().strip()
    
    # Remove standard extensions
    if "." in clean:
        clean = clean.rsplit(".", 1)[0]

    # Suffixes to strip. Order matters somewhat (longest first helps).
    # We strip iteratively to handle combos like 'Asset_4k_Instance'
    suffixes = [
        "_4k", "4k", "_2k", "2k", "_1k", "1k", "_8k", "8k", "_3k", "3k", "_6k", "6k",
        "_instance", "instance", "_copy", "copy", 
        "_low", "_high", "_mid", "_raw", "_geo"
    ]
    
    # Loop until no suffixes remain at the end
    modified = True
    while modified:
        modified = False
        for suffix in suffixes:
            if clean.endswith(suffix):
                clean = clean[:-len(suffix)]
                modified = True
                break # Restart loop to check for next suffix
    
    return clean.strip(" _-")

def is_valid_tag(tag_name, asset_name):
    """
    Validation Rules for Indexing:
    Rule A: Length <= 15 chars
    Rule B: Word count <= 2
    Rule C: Tag should not be redundant (i.e. identical to cleaned Asset Name)
    """
    tag_clean = tag_name.strip()
    if not tag_clean:
        return False
        
    # Rule A
    if len(tag_clean) > 15:
        return False
        
    # Rule B
    if len(tag_clean.split()) > 2:
        return False
        
    # Rule C
    t_low = tag_clean.lower()
    a_low = asset_name.lower().strip()
    a_clean = get_clean_name(asset_name)

    # 1. Exact match check
    if t_low == a_low:
        return False
        
    # 2. Cleaned match check
    if t_low == a_clean:
        return False
    
    return True


class ATF_OT_BuildLibraryIndex(Operator):
    bl_idname = "atf.build_library_index"
    bl_label = "Build Tag Index"

    _win = None
    _area = None
    _region = None
    _space = None
    _scene = None
    _step = 0
    _lib_ref = None
    _lib_path = None
    _json_path = None

    def _setup_context_refs(self, context):
        self._win = context.window
        self._area = context.area
        self._space = context.space_data
        self._scene = context.scene
        self._region = None

        if self._area:
            for reg in self._area.regions:
                if reg.type == "WINDOW":
                    self._region = reg
                    break

        return bool(self._win and self._area and self._region and self._space and self._scene)

    def _area_is_valid(self):
        try:
            if not self._win or not self._area:
                return False
            screen = self._win.screen
            if not screen:
                return False
            for area in screen.areas:
                if area == self._area:
                    return True
        except (ReferenceError, AttributeError):
            return False
        return False

    def execute(self, context):
        space = context.space_data
        if not space or getattr(space, "browse_mode", "") != "ASSETS":
            self.report({"WARNING"}, "Open Asset Browser in ASSETS mode.")
            return {"CANCELLED"}

        params = getattr(space, "params", None)
        if not params:
            self.report({"WARNING"}, "Asset Browser parameters unavailable.")
            return {"CANCELLED"}

        lib_ref = getattr(params, "asset_library_reference", None)
        if lib_ref in {None, "", "LOCAL", "ESSENTIALS", "ALL"}:
            self.report({"WARNING"}, "Select a user Asset Library.")
            return {"CANCELLED"}

        self._lib_ref, self._lib_path = get_active_asset_library_ref_and_path(context)
        if not self._lib_path:
            self.report({"WARNING"}, "Could not resolve asset library path.")
            return {"CANCELLED"}

        if not is_lib_writable(self._lib_path):
            self.report({"WARNING"}, f"Library folder is read-only: {self._lib_path}")
            return {"CANCELLED"}

        self._json_path = get_library_json_path(self._lib_path)

        if not self._setup_context_refs(context):
            self.report({"WARNING"}, "Could not prepare context.")
            return {"CANCELLED"}

        set_asset_browser_search("")

        self._step = 0
        context.window_manager.modal_handler_add(self)
        self.report({"INFO"}, "Building tag index...")
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type == "ESC":
            self.report({"INFO"}, "Cancelled.")
            return {"CANCELLED"}

        if not self._area_is_valid():
            self.report({"WARNING"}, "Asset Browser closed or invalid.")
            return {"CANCELLED"}

        if self._step < 1:
            self._step += 1
            return {"RUNNING_MODAL"}

        tags = set()

        override = dict(
            window=self._win,
            screen=self._win.screen,
            area=self._area,
            region=self._region,
            space_data=self._space,
        )

        try:
            with bpy.context.temp_override(**override):
                try:
                    bpy.ops.asset.select_all(action="DESELECT")
                    bpy.ops.asset.select_all(action="SELECT")
                except (RuntimeError, AttributeError):
                    try:
                        bpy.ops.file.select_all(action="DESELECT")
                        bpy.ops.file.select_all(action="SELECT")
                    except (RuntimeError, AttributeError):
                        self.report({"WARNING"}, "Could not select assets.")
                        return {"CANCELLED"}

                assets = getattr(bpy.context, "selected_assets", None) or []

            if not assets:
                self.report({"WARNING"}, "No assets found.")
                return {"CANCELLED"}

            for asset in assets:
                md = getattr(asset, "metadata", None)
                if not md:
                    continue
                # Capture asset name for validation
                asset_name = asset.name
                for t in getattr(md, "tags", []):
                    name = getattr(t, "name", "").strip()
                    # Updated logic: Validate tag vs asset name before adding
                    if name and is_valid_tag(name, asset_name):
                        tags.add(name)

        except Exception as e:
            self.report({"ERROR"}, f"Indexing failed: {e}")
            traceback.print_exc()
            return {"CANCELLED"}

        finally:
            if self._area_is_valid():
                try:
                    with bpy.context.temp_override(**override):
                        try:
                            bpy.ops.asset.select_all(action="DESELECT")
                        except (RuntimeError, AttributeError):
                            try:
                                bpy.ops.file.select_all(action="DESELECT")
                            except Exception:
                                pass
                except Exception:
                    pass

        props = self._scene.atf_props
        props.asset_count = len(assets)
        props.tag_count = len(tags)

        sorted_tags = sorted(tags, key=str.lower)

        if self._json_path and self._lib_path:
            try:
                # Ensure the folder exists before writing
                os.makedirs(os.path.dirname(self._json_path), exist_ok=True)
                
                data = {
                    "asset_library_reference": self._lib_ref,
                    "asset_count": props.asset_count,
                    "tag_count": props.tag_count,
                    "tags": sorted_tags,
                }
                with open(self._json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except OSError as ex:
                self.report({"WARNING"}, f"Could not write index: {ex}")

        self.report({"INFO"}, f"Indexed {props.asset_count} assets | {props.tag_count} tag(s)")
        return {"FINISHED"}


class ATF_OT_FilterByTagDirect(Operator):
    bl_idname = "atf.filter_by_tag_direct"
    bl_label = "Filter By Tag"
    
    tag: StringProperty()

    @classmethod
    def description(cls, context, properties):
        t = properties.get("tag", "")
        if t:
            return f"Filter by: {t}"
        return "Filter by this tag"

    def execute(self, context):
        tag = (self.tag or "").strip()
        if not tag:
            return {"CANCELLED"}

        set_asset_browser_search(tag)
        props = context.scene.atf_props
        add_recent_tag(context, props, tag)

        return {"FINISHED"}


class ATF_OT_ClearFilter(Operator):
    bl_idname = "atf.clear_tag_filter"
    bl_label = "Clear Tag Filter"
    bl_description = "Clear the current search filter"

    def execute(self, context):
        set_asset_browser_search("")
        return {"FINISHED"}


class ATF_OT_PinCurrentTag(Operator):
    bl_idname = "atf.pin_current_tag"
    bl_label = "Pin Current Tag"

    def execute(self, context):
        search = (get_asset_browser_search() or "").strip()
        if not search:
            return {"CANCELLED"}

        tag = search
        _lib_ref, lib_path = get_active_asset_library_ref_and_path(context)
        if not lib_path:
            return {"CANCELLED"}

        if not is_lib_writable(lib_path):
            self.report({"WARNING"}, "Library is read-only. Cannot pin.")
            return {"CANCELLED"}

        _a, _b, tags = read_library_json(context)
        if tag not in tags:
            return {"CANCELLED"}

        pinned = get_pinned_tags_for_lib(context)
        if tag in pinned:
            return {"CANCELLED"}

        if len(pinned) >= 6:
            self.report({"INFO"}, "Max pinned tags reached (6).")
            return {"CANCELLED"}

        success = add_pinned_tag_for_lib(context, tag, max_items=6)
        if not success:
            self.report({"WARNING"}, "Failed to save pinned tag.")
        return {"FINISHED"}


class ATF_OT_UnpinCurrentTag(Operator):
    bl_idname = "atf.unpin_current_tag"
    bl_label = "Unpin Current Tag"

    def execute(self, context):
        search = (get_asset_browser_search() or "").strip()
        if not search:
            return {"CANCELLED"}

        tag = search
        _lib_ref, lib_path = get_active_asset_library_ref_and_path(context)
        if not lib_path:
            return {"CANCELLED"}

        if not is_lib_writable(lib_path):
            self.report({"WARNING"}, "Library is read-only. Cannot unpin.")
            return {"CANCELLED"}

        pinned = get_pinned_tags_for_lib(context)
        if tag not in pinned:
            return {"CANCELLED"}

        success = remove_pinned_tag_for_lib(context, tag)
        if not success:
            self.report({"WARNING"}, "Failed to save pinned tag changes.")
        return {"FINISHED"}


class ATF_OT_ClearPinnedTags(Operator):
    bl_idname = "atf.clear_pinned_tags"
    bl_label = "Clear Pinned Tags"

    def execute(self, context):
        _lib_ref, lib_path = get_active_asset_library_ref_and_path(context)

        if lib_path and not is_lib_writable(lib_path):
            self.report({"WARNING"}, "Library is read-only.")
            return {"CANCELLED"}

        success = clear_pinned_tags_for_lib(context)
        if not success:
            self.report({"WARNING"}, "Failed to clear pinned tags.")
        return {"FINISHED"}


def atf_popup_search_update(self, context):
    text = (self.search_filter or "").strip()
    set_asset_browser_search(text)


class ATF_OT_BrowseTagsPopup(Operator):
    bl_idname = "atf.browse_tags_popup"
    bl_label = "Browse Tags"
    bl_description = "Open a popup to browse and search all indexed tags"
    bl_options = {'REGISTER', 'UNDO'}

    search_filter: StringProperty(
        name="Search Filter",
        default="",
        update=atf_popup_search_update,
        options={'TEXTEDIT_UPDATE'},
    )

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=300)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        asset_count, tag_count, tags_full = read_library_json(context)
        props = context.scene.atf_props

        current_search = (get_asset_browser_search() or "").strip()
        active_tag = current_search if current_search in tags_full else ""

        row = layout.row(align=True)
        row.prop(self, "search_filter", text="", icon="VIEWZOOM")

        if active_tag:
            layout.label(text=f"{tag_count} tags | Active: {active_tag}", icon="INFO")
        else:
            layout.label(text=f"{tag_count} tags | Active: –", icon="INFO")

        if not tags_full:
            layout.label(text="No tags found.", icon="ERROR")
            return

        tags_set = set(tags_full)
        search = (self.search_filter or "").strip().lower()

        pinned_all = [t for t in get_pinned_tags_for_lib(context) if t in tags_set]
        pinned_display = pinned_all[:6]

        layout.separator(factor=0.1)
        hdr = layout.row(align=True)
        hdr.label(text="Pinned:", icon="HEART")
        act = hdr.row(align=False)
        act.alignment = 'RIGHT'
        act.operator("atf.pin_current_tag", text="", icon="PINNED")
        act.operator("atf.unpin_current_tag", text="", icon="X")

        if pinned_display:
            outer = layout.column(align=True)
            for idx, t in enumerate(pinned_display):
                if idx % 3 == 0:
                    row_p = outer.row(align=True)

                label = t if len(t) <= 18 else t[:17] + "…"
                op = row_p.operator(
                    "atf.filter_by_tag_direct", text=label,
                    depress=(t == active_tag)
                )
                op.tag = t

        recent_all = [t for t in get_recent_tags_for_lib(context, props) if t in tags_set]
        recent_display = recent_all[:6]

        if recent_display:
            layout.separator(factor=0.1)
            layout.label(text="Recent:", icon="RECOVER_LAST")

            outer = layout.column(align=True)
            for idx, t in enumerate(recent_display):
                if idx % 3 == 0:
                    row_r = outer.row(align=True)

                label = t if len(t) <= 18 else t[:17] + "…"
                op = row_r.operator(
                    "atf.filter_by_tag_direct", text=label,
                    depress=(t == active_tag)
                )
                op.tag = t

        base_tags = [t for t in tags_full if search in t.lower()] if search else list(tags_full)
        base_tags = sorted(base_tags, key=str.lower)

        exclude = set(pinned_all)
        base_tags = [t for t in base_tags if t not in exclude]
        base_tags = base_tags[:40]

        if not base_tags:
            layout.label(text="No tags match search.", icon="INFO")
            return

        layout.separator(factor=0.4)
        outer = layout.column(align=True)

        for idx, t in enumerate(base_tags):
            if idx % 2 == 0:
                row_g = outer.row(align=True)

            label = t if len(t) <= 24 else t[:23] + "…"

            op = row_g.operator(
                "atf.filter_by_tag_direct",
                text=label,
                depress=(t == active_tag),
            )
            op.tag = t


# ===================================================================
# UI DRAWING FUNCTION (Called by Main UI)
# ===================================================================

def draw_tag_filter_ui(layout, context):
    """
    Draws the Tag Filter UI into the provided layout.
    Compatible with the main addon panel.
    """
    props = context.scene.atf_props  # Access the properties

    asset_count, tag_count, _tags = read_library_json(context)
    lib_ref, lib_path = get_active_asset_library_ref_and_path(context)

    json_path = get_library_json_path(lib_path) if lib_path else None
    json_exists = bool(json_path and os.path.exists(json_path))

    # --- Tag Filter Section ---
    box = layout.box()

    # Dynamic Header Logic
    current = get_asset_browser_search().strip()
    if current:
        box.label(text=f"Tag Filter : {current}")
    else:
        box.label(text="Tag Filter")

    # 1. Type Filter Logic
    params = get_asset_params(context)
    filt = getattr(params, "filter_asset_id", None) if params else None

    current_active_props = []
    is_all_active = False

    if filt:
        all_bools = _rna_bool_props(filt, prefix="filter")
        for p_name in all_bools:
            if getattr(filt, p_name, False):
                current_active_props.append(p_name)
        if all_bools and len(current_active_props) == len(all_bools):
            is_all_active = True

    split = box.split(factor=0.2, align=True)
    split.label(text="Type:")

    row = split.row(align=True)
    row.operator("atf_type.all_types", text="All", icon='NONE', depress=is_all_active)

    for t, _label, icon in ASSET_TYPES:
        is_active = False
        if filt and not is_all_active:
            target_prop = None
            if _fast_mapping_available(filt):
                mp = KNOWN_TYPE_MAPPING.get(t)
                if mp and hasattr(filt, mp):
                    target_prop = mp
            if not target_prop:
                target_prop = _resolve_filter_attr(filt, t, _rna_bool_props(filt, prefix="filter"))
            if target_prop and target_prop in current_active_props:
                is_active = True

        op = row.operator("atf_type.set_asset_type", text="", icon=icon, depress=is_active)
        op.asset_type = t

    box.separator()

    # 2. Tag Filter UI (Buttons now stacked with a small separator)
    col = box.column(align=True)
    col.operator("atf.browse_tags_popup", text="Browse Tags…", icon="DOWNARROW_HLT")
    col.separator()
    col.operator("atf.clear_tag_filter", text="Clear", icon="X")

    layout.separator()

    # --- Collapsible Indexer Section (At Bottom, Wrapped in Box) ---
    box_indexer = layout.box()
    row = box_indexer.row(align=True)
    row.alignment = 'LEFT'
    # Draw the toggle arrow
    icon = "TRIA_DOWN" if props.show_indexer else "TRIA_RIGHT"
    row.prop(props, "show_indexer", text="Tag Indexer", icon=icon, emboss=False)

    if props.show_indexer:
        col = box_indexer.column(align=True)

        if not lib_ref or lib_ref in {"", "LOCAL", "ESSENTIALS", "ALL"} or not lib_path:
            col.label(text="Select a user Asset Library.", icon="INFO")
        else:
            if json_exists:
                col.label(text=f"Indexed: {asset_count} assets | {tag_count} tags", icon="CHECKMARK")
            else:
                col.label(text="Not indexed. Run Build Index.", icon="ERROR")

        col.separator()
        col.operator("atf.build_library_index", text="Build Tag Index", icon="ASSET_MANAGER")