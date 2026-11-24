# The Powder Toy — Russian Localization (Early Alpha)

![Status](https://img.shields.io/badge/status-Early_Alpha_(Very_Buggy)-red)
![Platform](https://img.shields.io/badge/platform-Windows_x64_(Steam)-blue)

A Russian localization mod for **The Powder Toy** (Steam x64, v100+).

> [!WARNING]
> **Early Alpha / Experimental Build:** This release is **very buggy** and unfinished. Expect rough edges, untranslated UI parts, search quirks, or visual/layout issues depending on your setup. Use at your own risk and back up your files first.

---

## Installation (Drop-in ZIP)

1. Go to **[Releases](https://github.com/ciell11/the-powder-toy-rus/releases)** and download **`Powder_Toy_RUS_v0.9.0-alpha.zip`**.
2. Open your game directory (typically `C:\Program Files (x86)\Steam\steamapps\common\Powder`).
3. Extract the archive contents (`autorun.lua` and the `userdata` folder) into the game directory, **overwriting existing files** if prompted.
4. Launch the game normally.

> No modified `Powder.exe` is included in the release archive.  
> If you want to experiment with translating hardcoded engine strings (walls, bottom bar, settings, dialogs), an optional binary patcher [`patch_powder.py`](patch_powder.py) is included in the repository.

### Uninstall
Delete `autorun.lua` from the game root folder and from `userdata/`. If you used the optional binary patcher, verify game files in Steam.

---

## Features (Work in Progress)

- **194 Elements**: Russian 4-letter button labels and translated descriptions via `autorun.lua`.
- **Element Search**: Supports searching by Russian names and original English codes (`DUST`, `WATR`, `ACID`, etc.).
- **In-Game Help (`F1`)**: Built-in Russian controls & shortcuts overlay (`[РУС] Справка` button in the top-left).
- **Display & FPS**: Sets fullscreen mode and 144 FPS cap on startup.

---

## Known Issues (Early Alpha)

- Hardcoded C++ engine UI (walls, categories, settings, confirmation dialogs) remains in English unless you manually run the experimental [`patch_powder.py`](patch_powder.py) script.
- Text layout, clipping, or overlapping may occur on certain UI elements or resolutions.
- Element search case-sensitivity and Cyrillic input behavior can still be inconsistent in edge cases.
- Optional [`patch_powder.py`](patch_powder.py) targets a specific Steam x64 binary (`8,666,278` bytes) and will break after game updates.
