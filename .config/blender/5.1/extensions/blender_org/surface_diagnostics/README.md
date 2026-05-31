# Surface Diagnostics

**Author:** Josef Ludvík Böhm
**Blender Version:** 4.5+
**Addon Version:** 1.4.3

A set of tools for diagnosing surface quality for technical surfacing in Blender. This addon provides various visualization modes like Zebra Stripes, Isoangle Lines, Curvature Combs, and more to help you create high-quality, smooth surfaces.

---

## Features

*   **Material Overlays:** Instantly apply diagnostic materials to your objects.
    *   **Zebra Stripes:** Visualize surface continuity.
    *   **Isoangle Lines:** Display lines of constant angle to a reference vector.
    *   **Curvature & Radius:** Visualize surface curvature and minimum/maximum radius.
    *   **Draft Angle:** Check drafting angles of your object for manufacturing, pick an empty for directional vector.
    *   **Proximity:** Check the distance to another object.
*   **Graph Visualizations:** Generate geometry to analyze edge flow and curvature.
    *   **Curvature Graph (Comb):** Creates a curvature comb on selected edges.
    *   **Angle Graph:** Visualizes the angle between selected edges.
*   **Sectioning Tools:**
    *   **Sections:** Create 2D cross-section slices of your geometry as curves - fully dynamic.
    *   **Cut:** Dynamically cut your model with a plane for inspection and comparison with other objects.
*   **Non-destructive Workflow:** All tools are implemented using Geometry Nodes modifiers, which can be toggled, adjusted, and removed without affecting your original mesh.
*   **Efficient Management:** Easily toggle visibility for all diagnostics at once or remove them all with a single click.

---

## Installation

1.  Download the latest `.zip` file for the addon.
2.  In Blender, go to `Edit > Preferences...`.
3.  Navigate to the **Extensions** tab.
4.  Click the `Install...` button at the top.
5.  Find and select the `.zip` file you downloaded.
6.  The addon will appear in your list of extensions. Find "Surface Diagnostics" and make sure it is enabled (the checkbox on the left should be ticked).
7.  The addon panel will now be available in the 3D Viewport.

---

## How to Use

1.  Select an object you want to analyze.
2.  Open the 3D View's Sidebar by pressing the `N` key.
3.  Go to the **Surf Ace** tab.
4.  You will see the **SurfAce Diagnostics** panel.

### Main Operations

*   **Buttons Grid:** The main buttons (Zebra, Isoangle, Curvature, etc.) will add the corresponding diagnostic tool to your selected object(s).
*   **Settings Panels:** Once a tool is active on an object, a new panel will appear below the main buttons. Here you can fine-tune all the parameters for that specific tool (e.g., scale, colors, angles).
*   **Delete All:** This button at the top of the panel will remove every diagnostic element (modifiers, helper objects, attributes) created by this addon from your entire scene.
*   **Toggle Visibility (Eye Icon):** This globally hides or shows all diagnostic elements in the viewport.

---

## Support and Documentation

*   **Product Page:** Support Surface Diagnostics on Super Hive Market https://superhivemarket.com/products/surface-diagnostics
*   **Community & Support:** Join our Discord Server https://discord.gg/cWVT9a6sNe

---

## License

This addon is licensed under the **GNU General Public License v3.0 or later**.

See the `LICENSE` file for more details, or visit https://www.gnu.org/licenses/gpl-3.0.html.

---

## Changelog

### Version 1.4.0
    - Complete refactor for the extensions platform.
    - 2 new diagnostic tools: Geometry Sections and Geometry Cut.
    - Polished UI: Collapsible sub-panels, global and local hide toggle.
    - Legacy Sections and Cut: The material-based versions from previous releases are still available via Add-on Preferences.
    - Debug mode: Available in Add-on Preferences with logging.
    - Many bugs and papercuts squashed.
### Version 1.4.1
    - Updated from __name__ to __package__.
    - Cleaned up asset blend file.
    - Icons are now svg instead of png.
### Version 1.4.2
    - Zebra Vector transform changed from "World" to "Object".
    - Fill Material as input for Slice modifier
    - Fill Tolerance input for Slice modifier. (merging slice curves).
    - Fixed UVMap around slice area for Slice modifier. (UVMap name as modifier input). 
### Version 1.4.3
    - Added option to realize instances for slice tool-