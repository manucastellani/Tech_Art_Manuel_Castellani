# 🛠️ UE Production Toolkit

**A Maya → Unreal Engine pipeline utility that enforces naming conventions, validates scenes and cleans geometry — so every asset lands engine-ready.**

![Maya](https://img.shields.io/badge/Maya-2022--2027-0696D7?logo=autodesk&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Qt](https://img.shields.io/badge/PySide-2%20%2F%206-41CD52?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

🌐 **English** · [Español](README.es.md)

<p align="center">
  <img src="docs/preview.png" alt="UE Production Toolkit UI" width="360">
</p>

---

## Overview

Exporting from Maya to Unreal breaks in predictable, boring ways: meshes without the right prefix, duplicate node names that overwrite each other on import, un-frozen transforms, leftover construction history. **UE Production Toolkit** turns those repetitive checks into one-click, artist-friendly actions inside a single PySide window — no console, no external dependencies.

The whole tool ships as **one self-contained `.py` file**: drag it into Maya, hit *Play*, done.

## ✨ Features

| Tool | What it does | Why it matters for Unreal |
|------|--------------|---------------------------|
| **Smart Rename** | Auto-detects `SM_` (Static Mesh), `SK_` (Skeletal Mesh) and `JNT_` (joint) prefixes, strips clutter (`_final`, `_v01`), preserves technical suffixes (`_LOD0`, `_A`) and adds padded indices (`_01`, `_02`) when names collide. | Consistent, engine-ready naming with zero manual typing. |
| **Scene Auditor** | Finds and selects every mesh that doesn't follow the `SM_`/`SK_` convention. | Catch naming violations before they reach the engine. |
| **Duplicate Name Check** | Detects non-unique short names across the scene and selects them. | Duplicate names silently overwrite each other on FBX import — this stops it. |
| **Mesh Finalizer** | Batch **Delete History · Freeze Transforms · Center Pivot**. | Clean, predictable transforms in Unreal. |

### Built for artists (UX highlights)

- 🔍 **Non-destructive preview** — Smart Rename shows an *old → new* table **before** touching anything; each new name is **editable by double-click**.
- 🧾 **Integrated log** — every action is timestamped in an in-window console (no popup spam).
- ↩️ **One-click Undo** — every batch is a single undo step, so one click (or `Ctrl+Z`) reverts the whole operation.
- 🦴 **Rig-safe** — meshes with a `skinCluster` are **skipped** by the finalizer (freezing them would break the bind) and reported.

## 🚀 Installation & Usage

**No installation. One file.**

1. Drag **`UE_Production_Toolkit.py`** into the Maya viewport (or paste it into the Script Editor → Python tab).
2. Press **Play / Execute**.
3. The window opens. That's it.

**Optional — make a shelf button:** in the Script Editor, select the code, middle-mouse-drag it onto your shelf.

> Requires Maya 2022–2027. The Qt binding (PySide6 or PySide2) is selected automatically.

## 🧠 Technical Highlights

A few engineering decisions worth calling out (this is a portfolio piece, after all):

- **Single-file, zero-dependency** — no `pip install`, no path setup. Runs anywhere Maya runs.
- **PySide6 / PySide2 auto-compat** — one binding shim keeps it working from Maya 2022 (Qt5) through 2027 (Qt6).
- **Non-destructive by design** — rename logic is split into `plan_rename()` (pure, computes a dry-run) and `apply_rename()` (mutates). The UI previews the plan before committing.
- **Safe hierarchy renaming** — renames are applied deepest-first so renaming a parent never invalidates a child's DAG path.
- **Atomic undo** — batch operations are wrapped in an `undoInfo` chunk context manager.
- **Tested logic** — the naming rules are validated against a suite of edge cases (LODs, variants, versioned/`_final` clutter, joint suffixes, index padding).

## 🗺️ Roadmap

- [ ] FBX export to Unreal with correct presets (smoothing groups, tangents) — one click.
- [ ] Collision naming helper (`UCX_` prefix).
- [ ] Lightmap UV audit (second UV channel check).
- [ ] Geometry validation (non-uniform/negative scale, n-gons, non-manifold).
- [ ] User-configurable prefix conventions.

## 📁 Project Structure

```
UE_Production_Toolkit/
├── UE_Production_Toolkit.py   # the tool — a single self-contained file
├── README.md                  # this file (English)
├── README.es.md               # Spanish version
├── LICENSE                    # MIT
├── docs/                      # screenshots / GIFs
└── legacy/
    └── UE_PRODUCTION_TOOLKIT.mel   # original MEL version (project origin)
```

> The `legacy/` folder keeps the original MEL prototype — the tool was later rewritten in Python + PySide with a modular, tested and non-destructive design.

## 📄 License

Released under the [MIT License](LICENSE).

## 👤 Author

**Manuel Castellani** — Technical Artist & 3D Modeler
<!-- Completá tus links antes de publicar -->
[LinkedIn](#) · [ArtStation](#) · [GitHub](https://github.com/manucastellani)
