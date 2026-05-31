# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Code Style and Language

**IMPORTANT**: Use British English throughout all code, comments, documentation, and commit messages. Examples:
- `sanitise` not `sanitize`
- `optimise` not `optimize`
- `colour` not `color`
- `cancelled` not `canceled`
- `realise` not `realize`

## Project Overview

EasyMesh Batch Exporter is a Blender add-on for batch exporting meshes, curves, and metaballs with advanced features like LOD generation and memory optimisation for large meshes (2M+ polygons). The addon is production-ready with comprehensive error handling, type safety, and Blender 4.5+ compatibility.

## Quick Reference

- **Full Technical Details**: See [ARCHITECTURE.md](ARCHITECTURE.md) for comprehensive system architecture
- **User Documentation**: See [README.md](README.md) for features and usage
- **Version**: 1.4.0 (defined in `blender_manifest.toml`)

## Commands

### Build the Extension
```bash
blender --command extension build
```
This creates a distributable `.zip` file in the current directory.

### Install for Development
```bash
# Link the addon to Blender's extensions directory for testing
ln -s "$(pwd)" "$HOME/Library/Application Support/Blender/4.2/extensions/.local/easymesh_batch_exporter"
```

### Version Management
The version is defined in `blender_manifest.toml`. When releasing a new version:
1. Update the version in `blender_manifest.toml`
2. Build the extension
3. Create release notes in the `releases/` directory named `v{version}.md`

## Architecture

### Module Structure
- `__init__.py`: Main addon registration, imports all modules and handles Blender registration
- `properties.py`: All export settings as Blender PropertyGroups with update callbacks
- `operators.py`: Core export logic (~2600 lines) with memory optimisation and type hints
- `panels.py`: UI panels (main + 5 sub-panels) in 3D viewport sidebar
- `export_indicators.py`: Timer-based visual feedback system with caching and weak reference validation

### Key Architectural Decisions

1. **Refactored Export Architecture**:
   - Main `execute()` method broken down into focused helper methods:
     - `_validate_export_setup()` - Input validation and path checking
     - `_process_batch_gltf_export()` - glTF batch export (combines multiple objects into single file)
     - `_process_lod_export()` - LOD-specific processing logic
     - `_process_single_export()` - Non-LOD export processing
     - `_generate_export_report()` - Result reporting and messaging
   - Each method has single responsibility and proper error handling
   - `execute()` checks for batch mode before per-object loop

2. **Memory Management System** (Adaptive & Configurable):
   - `MemoryManager` class with adaptive garbage collection
   - Configurable interval via `set_gc_interval(seconds)` (default: 5.0s)
   - Adaptive mode adjusts GC frequency based on mesh size:
     - 1M+ polygons: 2-3 second intervals (aggressive)
     - 500K-1M polygons: 3-4 second intervals (moderate)
     - <500K polygons: 5 second intervals (normal)
   - `MeshOperations` utility class for common mesh operations:
     - `update_mesh_data()` with optional memory cleanup
     - `safe_mode_set()` for object mode changes
     - `safe_operator_call()` for context-validated operator calls (prevents CLI crashes)
     - `update_view_layer()` with error handling
   - Automatic memory optimisation at 500K+ polygons

3. **Resource Management** (Leak Prevention):
   - Context managers for safe resource cleanup:
     - `temporary_mesh()` for mesh data with type hints
     - `temporary_object()` for Blender objects with type hints
     - `temporary_image_file()` for temp files with type hints
   - Guaranteed cleanup even when exceptions occur
   - **Critical Pattern**: Always pair `to_mesh()` with `to_mesh_clear()` in try/finally blocks
   - All `to_mesh()` calls use full signature: `to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)`

4. **Exception Handling Hierarchy** (Robust Error Recovery):
   - Custom exception types: `ValidationError`, `ResourceError`, `ProcessingError`, `ExportFormatError`
   - Specific error handling with user-friendly messages
   - Proper error recovery and logging
   - No bare exception handlers (all use specific exception types)

5. **Performance Optimisations**:
   - Cached object lists in `export_indicators.py` with weak reference validation
   - Refreshes every 10 seconds, filters deleted objects automatically
   - Throttled memory cleanup to prevent stutters
   - In-memory image processing with proper temp file management
   - Progressive LOD building (60% faster, 50% less memory)

6. **Property System**:
   - Settings stored in `context.scene.mesh_exporter`
   - LOD settings integrated into main property group
   - Uses Blender's property update callbacks for UI reactivity

7. **Code Quality Standards**:
   - Type hints on 15+ critical functions
   - All magic numbers extracted to documented constants
   - Google-style docstrings with examples
   - Inline comments for complex regex patterns
   - Consistent British English throughout

### Important Patterns

1. **Modern Resource Management**:
   - Use context managers for temporary resources: `with temporary_object(obj) as temp_obj:`
   - Use `MemoryManager.request_cleanup(poly_count=count)` instead of direct `gc.collect()`
   - Use `MeshOperations.update_mesh_data(obj, with_memory_cleanup=True)` for mesh updates
   - Always validate inputs with custom exception types
   - **Critical**: Always use try/finally for `to_mesh()` / `to_mesh_clear()` pairs

2. **Error Handling Best Practices**:
   - Catch specific exceptions: `ValidationError`, `ResourceError`, `ProcessingError`
   - Use `self.report()` with appropriate error levels
   - Always include error context in log messages
   - Return `{'CANCELLED'}` for user errors, `{'FINISHED'}` for success
   - Track and report skipped objects with reasons

3. **Performance Considerations**:
   - Cache frequently accessed data (e.g., object lists in indicators)
   - Use `MeshOperations.safe_mode_set()` instead of direct mode changes
   - Use `MeshOperations.safe_operator_call()` for all operator invocations
   - Batch memory cleanup operations using `MemoryManager`
   - Monitor polygon counts and apply optimisations at thresholds
   - Pass `poly_count` to `request_cleanup()` for adaptive GC

4. **Modifier and Mesh Processing**:
   - Create object copies to preserve originals using `create_export_copy()`
   - Apply modifiers based on mode (None/Visible/Render) via `apply_mesh_modifiers()`
   - Special handling for curves/metaballs (auto-convert to mesh)
   - Use `MeshOperations.update_view_layer()` after significant changes
   - Use `MeshOperations.safe_operator_call()` for all `bpy.ops` calls

5. **Type Safety**:
   - Add type hints to all new public functions
   - Use `Optional[Type]` for nullable parameters
   - Document return types with `-> ReturnType`
   - Example: `def sanitise_filename(name: str) -> str:`

### Development Tips

- Use the utility classes (`MemoryManager`, `MeshOperations`) instead of direct Blender API calls
- Test with large meshes (2M+ polygons) to verify memory optimisation works
- Check console output - extensive logging via Python's logging module
- UI panels only show in Object mode in 3D viewport
- Export formats have specific requirements (e.g., STL needs triangulation)
- When adding new functionality, follow the established patterns for error handling and resource management
- **Never use bare `except:` clauses** - always specify exception types
- **Always wrap operator calls** in `MeshOperations.safe_operator_call()` for context validation

## Key Constants

### Memory Management Thresholds
```python
LARGE_MESH_THRESHOLD = 500000          # Triggers basic optimisation
VERY_LARGE_MESH_THRESHOLD = 1000000    # Triggers aggressive GC
DEFAULT_GC_INTERVAL = 5.0              # Default GC throttle (seconds)
CACHE_UPDATE_INTERVAL = 10.0           # Cache refresh interval (seconds)
```

**Rationale**: Based on typical workstation memory (16-32GB) and observed performance characteristics. At 500K+ polygons, memory fragmentation becomes noticeable. At 1M+ polygons, aggressive GC prevents OOM errors.

### File Naming Constants
```python
MAX_FILENAME_LENGTH = 100              # Conservative cross-platform limit
FILENAME_TRUNCATE_SUFFIX = "..."       # Suffix for truncated names
UNREAL_KNOWN_PREFIXES = {              # UE asset type prefixes
    'SM', 'SK', 'BP', 'M', 'T', 'MT',
    'MI', 'A', 'S', 'E', 'W', 'P'
}
```

## Key Export Format Considerations

### Format-Specific Limitations
- **GLTF/USD**: Scale parameter is ignored (format limitation) - see `setup_export_object()`
- **STL**: Requires triangulation; automatically enabled
- **FBX**: Supports most features including smoothing and modifiers
- **OBJ**: Basic format, supports smoothing but limited material support

### Texture Handling
- FBX supports embedded or external textures via `mesh_export_embed_textures`
- GLTF: GLB always embeds textures, JSON exports separately
- USD/OBJ/STL: No texture embedding support

### Memory Thresholds
- 500K polygons: Basic memory optimisation triggers
- 1M+ polygons: Aggressive memory management with adaptive GC (2-3s intervals)
- 2M+ polygons: All optimisations active, frequent GC, pre-cleanup operations
- LOD generation uses progressive building (60% faster, 50% less memory)

## Naming Conventions

The addon supports game engine specific naming conventions via `mesh_export_naming_convention`:

- **DEFAULT**: Keep original naming with basic sanitisation
- **GODOT**: snake_case naming (my_mesh_name) - all lowercase with underscores
- **UNITY**: Capitalised_Words_With_Underscores - capitalise each word, join with underscores
- **UNREAL**: PascalCase naming (MyMeshName) - capitalise words, no spaces, preserves known prefixes (SM_, SK_, BP_, etc.)

Apply via `apply_naming_convention(name, convention)` in `operators.py`. All conventions handle illegal filename characters appropriately for their target engine.

**Implementation Details**:
- Complex regex patterns are fully documented with inline comments
- Examples in docstrings show transformations for each convention
- Character class explanations for maintainability
- See ARCHITECTURE.md for detailed regex breakdowns

## LOD Hierarchy Export

For game engines, the addon supports exporting LODs as hierarchical FBX files:

1. **Individual Object Processing**: Each selected object gets its own LOD hierarchy (not merged)
2. **Processing Pipeline**: Each LOD follows same pipeline as regular export (setup_export_object → modifiers → triangulation)
3. **Export Structure**: Creates `{ObjectName}_LODGroup.fbx` with parent empty containing all LOD levels
4. **LOD Naming**: Objects within hierarchy follow `{basename}_LOD00`, `{basename}_LOD01` pattern

Key function: `_process_object_hierarchy_export()` in operators.py

## glTF Batch Export (Godot Workflow)

The addon supports combining multiple meshes into a single glTF file (ideal for Godot imports):

1. **Batch Mode**: Enabled by default for glTF format via `mesh_export_gltf_batch_mode` property
2. **Collection-Based Naming**: Uses shared collection name for filename, or first object name as fallback
3. **Processing Pipeline**: Each object processed individually (modifiers, triangulation), then combined for export
4. **LOD Support**: Compatible with LOD generation - all objects and their LODs exported as single file
5. **Memory Efficient**: Reuses existing memory optimisation strategies for large batches

**Key Functions:**
- `get_batch_export_filename(objects, scene_props)` - Determines batch filename from collection membership
- `_process_batch_gltf_export(objects, context, scene_props, export_base_path)` - Main batch export logic

**Filename Resolution Logic:**
1. Find common collection across all selected objects
2. If common collection exists → use collection name
3. If no common collection → use first object's name
4. Apply prefix, suffix, and naming convention
5. Sanitise and truncate to max length

**Example:**
```python
# Objects from "Trees" collection with Godot convention
# Output: trees.glb (all trees combined)

# Objects from different collections
# Output: rock1.glb (uses first object name)
```

**Incompatibilities:**
- Batch mode automatically disabled when LOD Hierarchy export is enabled (FBX-specific feature)
- Only available for glTF format (GLB or JSON)

## Object Type Handling

### Metaballs
- Automatically converted to mesh via `to_mesh()` evaluation
- **Modern Smooth Shading** (Blender 4.1+ compatible):
  ```python
  for poly in mesh_obj.data.polygons:
      poly.use_smooth = True
  ```
- Inherently smooth objects get proper surface normals for game engines
- **Note**: Deprecated `bpy.ops.object.shade_auto_smooth()` has been replaced with direct polygon flags

### Curves
- Converted to mesh via `convert_curve_to_mesh_object()`
- Supports NURBS curves and Bezier curves with automatic mesh generation
- Uses full `to_mesh()` signature with data layer preservation

### Mesh Objects
- Direct processing with modifier application and LOD generation
- Memory optimisation for large meshes (2M+ polygons)
- Automatic detection and adaptive GC strategies

## Recent Improvements (v1.4.0)

### Critical Fixes
1. **Memory Leak Elimination**:
   - Fixed 3 `to_mesh_clear()` memory leaks with try/finally blocks
   - Added BMesh cleanup guarantees with context managers
   - Memory usage reduced by 60% for repeated exports

2. **Blender 4.5+ Compatibility**:
   - Replaced deprecated `shade_auto_smooth` operator
   - All API calls updated to modern equivalents
   - No deprecated functions remaining

3. **Logger Handler Fix**:
   - Eliminated handler accumulation on addon reload
   - Added `logger.handlers.clear()` and `propagate = False`
   - Prevents duplicate log messages

4. **Context Validation**:
   - New `MeshOperations.safe_operator_call()` method
   - Validates context before all operator calls
   - Prevents crashes in CLI/background mode

### Code Quality Improvements
1. **Type Hints**: Added to 15+ critical functions
2. **Extracted Constants**: All magic numbers now named constants with rationale
3. **Documentation**: Inline comments for complex regex, docstring examples
4. **Error Messages**: Improved user-facing messages with skip tracking
5. **Exception Handling**: Eliminated all bare `except:` clauses

### Performance Enhancements
1. **Adaptive GC**: Interval adjusts based on mesh size
2. **Configurable Intervals**: `MemoryManager.set_gc_interval()`
3. **Robust Caching**: Weak reference validation in export indicators
4. **Memory Optimisation**: Progressive cleanup during operations

## Testing Guidelines

### Large Mesh Testing
- **500K-1M polygons**: Verify basic optimisation triggers
- **1M-2M polygons**: Verify aggressive GC with 2-3s intervals
- **2M+ polygons**: Verify all optimisations active, no OOM errors

### Edge Case Testing
- Empty collections (should show clear error)
- Collection instances (should skip with warning)
- Curves and metaballs (auto-conversion)
- Invalid export paths (clear error message)
- Addon reload (no logger duplication)
- CLI mode (no operator crashes)

### Memory Leak Testing
1. Export same large mesh 10 times
2. Monitor memory in console logs
3. Verify memory returns to baseline
4. Check no "Memory optimisation" warnings persist

## Contributing

### Before Submitting Code
- ✓ Add type hints to new functions
- ✓ Extract magic numbers to constants with comments
- ✓ Use Google-style docstrings with examples
- ✓ Add inline comments for complex logic
- ✓ Use specific exception types (no bare except)
- ✓ Wrap operator calls in `safe_operator_call()`
- ✓ Test with large meshes (1M+ polygons)
- ✓ Verify no memory leaks in console
- ✓ Update ARCHITECTURE.md if architecture changes

### Code Review Checklist
- [ ] British English throughout
- [ ] Type hints on public functions
- [ ] Constants instead of magic numbers
- [ ] try/finally for resource cleanup
- [ ] Context managers for temporary resources
- [ ] Specific exception types
- [ ] User-friendly error messages
- [ ] Logger statements at appropriate levels
- [ ] Performance tested with large meshes
- [ ] No deprecated Blender API calls

## References

- **Architecture Document**: [ARCHITECTURE.md](ARCHITECTURE.md) - Comprehensive technical details
- **User Guide**: [README.md](README.md) - Features and usage instructions
- **Blender Python API**: https://docs.blender.org/api/current/
- **Blender 4.5 API Docs**: https://docs.blender.org/api/4.5/
- **Extension Repository**: https://extensions.blender.org/add-ons/easymesh-batch-exporter/

---

**Last Updated**: 2025-01-08
**Addon Version**: 1.4.0
**Blender Compatibility**: 4.2+, optimised for 4.5+
