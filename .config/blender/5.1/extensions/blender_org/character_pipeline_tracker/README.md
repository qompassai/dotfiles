# Character Pipeline Tracker

**Organize, track, and automate your 3D character creation pipeline directly in Blender.**

This add-on is designed to help both beginners and professionals streamline the character modeling workflow—from high-poly sculpting to final export. It enforces a clean scene structure, validates naming conventions, checks for common mesh issues, and automates repetitive tasks like backups and exports.

---

## ✨ Features

- **Organize the correct structure of the scene.**
- **Track the stages of the work process.**  
  Saves the process and makes backups at the end of each stage.
- **Prepare the objects for export.**  
  Normalizes names and applies modifiers.
- **Check the geometry for errors.**  
  Checks the matching of name pairs. Analyzes the mesh for the presence  
  of non-manifold geometry (problem areas are recorded in Vertex Groups).
- **Set up a presentation Model Sheet.**  
  Creates a stage for the presentation of a character from different angles.  
  Simplifies the rendering process.
- **Export models depending on the stage.**  
  When exporting, the appropriate materials are automatically assigned  
  and transformations are applied.
  
## ⚠️ Important:

- Adhere to the structure of the created collections.  
  This will help you avoid unexpected mistakes.
- Try to follow the original order of the buttons, unless you went back  
  to the previous steps.
- Some Model Sheet settings are only available in the **Model Sheet scene**,  
  in the **Video Sequencer** window.
- The add-on allows you to work with **several characters in a scene at once**.  
  Some functions work relative to the root collection of the selected object.

Following these rules will ensure stable and automated work with characters.

---

## 🛠️ Requirements

- **Blender 5.0 or newer** (required for Extensions Platform support).
- Works with any character project—single or multiple assets per scene.

---

## 📦 Installation (via Extensions Platform)

1. Go to **Edit > Preferences > Extensions**.
2. Click **Install from Disk** and select the downloaded `.zip` file.
3. Enable the add-on.

> The add-on will appear in the **Pipeline** tab of the 3D Viewport sidebar (`N`-panel).

---

## 💡 Usage Tips

- Always **save your .blend file first**—many features (backups, exports) require a saved path.
- Let the add-on **create your base collections**—it ensures correct naming and hierarchy.
- Use the **Validate Pairs** button before baking to avoid missing UVs or mismatched geometry.
- Enable **Auto Backup** in Preferences to save progress automatically at each pipeline step.

---

## 📜 License

This add-on is licensed under the **GNU General Public License v3.0 (GPL-3.0-or-later)**.

> You are free to use, modify, and distribute this software, provided derivative works remain open-source under the same license.

---

## 🙋 Author

**Lisichik Evgeny**  
For questions or suggestions - md15.db@gmail.com.

*Happy modeling!*