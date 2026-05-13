# 🛠️ UE PRODUCTION TOOLKIT (Maya MEL)

_UE Production Toolkit is a professional-grade script for Autodesk Maya designed to streamline the pipeline between Maya and Unreal Engine. It automates naming conventions, geometry cleanup, and scene auditing to ensure engine-ready assets._

---

## ✨ Key Features

### 1. Smart Rename (Auto-Prefix)

An intelligent algorithm that analyzes object hierarchy and construction history to rename objects automatically:

- **Prefix Detection:** Automatically assigns `SM_` for Static Meshes and `SK_` for Skeletal Meshes (detects `skinCluster` nodes).
    
- **Clutter Cleanup:** Strips production suffixes like `_final`, `_v01`, etc.
    
- **LOD & Variation Support:** Preserves technical suffixes such as `_LOD0` or `_A`.
    
- **Smart Indexing:** Applies clean padding (`01`, `02`...) when multiple objects share the same base name.
    

### 2. Scene Auditor

A quick verification system that scans your scene for objects failing to meet naming standards, automatically selecting them for immediate correction.

### 3. Mesh Finalizer

Batch processes essential cleanup operations before export:

- Delete History.
    
- Freeze Transformations.
    
- Center Pivot.
    

---

## 🚀 Installation & Usage

### Step-by-Step Guide

To ensure the tool runs correctly in your Maya session, follow these steps:

1. **Copy the Code:** Go to the `RenamingTool_Script.mel` file in this folder and copy the entire code block.
    
2. **Open Script Editor:** In Autodesk Maya, open the Script Editor (bottom right icon or `Windows > General Editors > Script Editor`).
    
3. **Paste in MEL Tab:** Make sure you are in a MEL tab (not Python). Paste the copied code into the lower panel.
    
4. **Execute:** Select all the text (`Ctrl+A`) and press `Numpad Enter` or click the Play (Execute) icon in the toolbar.
    

### Create a Shelf Button

To avoid pasting the code every time you restart Maya:

1. In the Script Editor, select the entire code.
    
2. With the **Middle Mouse Button**, drag the selected text onto your active Shelf.
    
3. Right-click the new icon, select **Edit**, and under the Shelves tab, set an "Icon Label" like `UE_v13`.
    

---

## 💻 Requirements

- **Autodesk Maya:** Compatible with 2024 and newer versions.
    
- **OS:** Windows, macOS, Linux.
    

---

## 📄 License

This project is licensed under the MIT License. Feel free to use, modify, and distribute it in your productions.


<img width="800" height="465" alt="Grabacin2026-04-29191259-ezgif com-video-to-gif-converter" src="https://github.com/user-attachments/assets/86d8a79f-08bd-4825-adb2-10bd5df2dd31" />


