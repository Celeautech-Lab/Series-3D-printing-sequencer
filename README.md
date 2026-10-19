# Print Series Generator

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Interface](https://img.shields.io/badge/interface-Tkinter-2E8B57)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/license-PolyForm_Noncommercial-orange.svg)](LICENSE)

A Python/Tkinter desktop application for building a print series from several G-code files. It keeps the **Header** of the first expanded file, chains the **Body** sections in the requested order and quantity, inserts a configurable transition after every part, and keeps the **Footer** of the last expanded file.

> **Repository:** [Celeautech-Lab/Series-3D-printing-sequencer](https://github.com/Celeautech-Lab/Series-3D-printing-sequencer)

## Download (recommended)

For most users, download a ready-to-run executable from the repository's [**GitHub Releases**](https://github.com/Celeautech-Lab/Series-3D-printing-sequencer/releases) page. The release workflow publishes platform-specific assets when a release is created:

- `PrintSeriesGenerator-Windows-x64.exe` — Windows x64;
- `PrintSeriesGenerator-Linux-x64` — Linux x64;
- `PrintSeriesGenerator-macOS-AppleSilicon.tar.gz` — macOS Apple Silicon application archive.

Download only from the project's GitHub repository, and inspect the release notes and asset name before running a file. On Linux, make the downloaded executable runnable if necessary:

```bash
chmod +x PrintSeriesGenerator-Linux-x64
./PrintSeriesGenerator-Linux-x64
```

On macOS, extract the archive, then open the application bundle. Depending on macOS security settings, you may need to approve the application in **System Settings → Privacy & Security**. The binaries are produced by the repository's GitHub Actions workflow; verify the release provenance and your local security policy before use.

## How it works

The application scans one selected folder for supported G-code files, validates their markers, optionally loads `serie.csv`, displays the plan in an editable table, and exports a compiled G-code file. It does not select or validate a universal mechanical ejection method: the transition block must be adapted and tested on the target printer.

### Header, Body, and Footer

Each source file must contain exactly one start marker and one end marker, on lines that are exactly these comments after leading and trailing whitespace are removed:

```gcode
; BODYSTART
; ... part-printing commands ...
; BODYEND
```

The composer splits each file into:

- **Header**: everything before `; BODYSTART`;
- **Body**: everything between `; BODYSTART` and `; BODYEND`, excluding both markers;
- **Footer**: everything after `; BODYEND`.

The generated file contains the Header of the first expanded part once, one shared `; BODYSTART` marker, all Bodies in the selected order, a transition after every Body—including the last one—then one shared `; BODYEND` marker and the Footer of the last expanded part. The last transition therefore appears before the final Footer. If your process needs a cooldown, wait, or reheating step, include it in the transition and validate it on the machine.

### Worked example: seven cycles

```csv
Cycles,7
Rank,Filename,Occurrences
1,PART_1.gcode,4
2,PART_2.gcode,5
3,PART_3.gcode,6
```

One cycle contains `4 + 5 + 6 = 15` parts. Seven cycles produce:

```text
7 cycles × 15 parts per cycle = 105 parts
105 transitions (one after every part, including the last)
```

The expanded order is seven repetitions of `4 × PART_1.gcode`, followed by `5 × PART_2.gcode`, followed by `6 × PART_3.gcode`, with the configured transition after each part. An occurrence count of `0` excludes a row; generation is refused if all occurrences are zero.

## Use the application

1. Download and launch a release binary, or launch from source as described below.
2. Click **Select folder** and choose the folder containing the source G-code files.
3. The application scans that folder only (not subfolders) and recognizes `.gcode`, `.gco`, and `.g` files.
4. Files with valid markers appear in the sequence table. Invalid files are excluded and listed in **Validation report**.
5. If the selected folder contains `serie.csv`, it is loaded after file validation. Missing or invalid references are reported.
6. Edit **Occurrences** by double-clicking a row, drag rows to change their order, and set **Cycles**.
7. Open **Settings** to inspect or edit the inter-part transition G-code.
8. Click **Generate G-code** and choose the output path. The save dialog uses `serie.gcode` as its default filename.

Use **Save series** to create or overwrite `serie.csv` in the selected folder. If no folder is loaded, the application asks where to save it. Cancelling the interface does not generate a sequence.

## Preparing source G-code

### Required markers

Add these comments to every source file:

```gcode
; BODYSTART
...
; BODYEND
```

The current validator requires:

1. exactly one `; BODYSTART`;
2. exactly one `; BODYEND`;
3. `BODYSTART` before `BODYEND`;
4. at least one line between the markers.

A line such as `; BODYSTART extra text` is **not** accepted. The markers are comments and do not move the machine; they define the splitting contract used by the sequencer. Inspect the exported G-code and confirm that each marker appears once.

Place `; BODYSTART` where the part-specific toolpath begins, after any shared startup commands that should remain in the Header. Place `; BODYEND` after the last part-specific command and before commands that should remain in the Footer. Exact slicer menu names vary by version and profile, but the exported text is authoritative.

Typical locations include:

- **PrusaSlicer:** printer settings and custom start/end G-code fields;
- **OrcaSlicer:** machine start G-code and the profile's custom G-code fields;
- **Bambu Studio:** machine start/end G-code or printer settings, depending on the profile;
- **Cura:** printer management and Machine Settings start/end G-code fields.

## `serie.csv` format

The file name must be exactly `serie.csv`:

```csv
Cycles,7
Rank,Filename,Occurrences
1,PART_1.gcode,4
2,PART_2.gcode,5
3,PART_3.gcode,6
```

The parser:

- expects `Cycles` and the cycle count in row 1;
- expects `Rank,Filename,Occurrences` in row 2;
- accepts a UTF-8 BOM and ignores completely empty rows;
- requires cycles and ranks to be integers of at least `1`;
- requires occurrences to be an integer of at least `0`;
- rejects duplicate ranks and sorts entries by rank;
- requires referenced filenames to match valid files in the selected folder.

The interface limits direct occurrence editing to `0–999`; the CSV parser accepts any non-negative integer. When the interface saves the file, it writes the first row as `Cycles,<value>,` with a trailing empty column; this is accepted by the parser.

## Transition and printer safety

The default transition in `settings.json` is an example, not a universal, ready-to-run ejection routine:

```gcode
; --- BELT TRANSITION ---
G91
G1 Z15 F600
G90
G28 X Y
MANUAL_STEPPER STEPPER=convoyeur MOVE=400 SPEED=50 STOP_ON_ENDSTOP=1
G28
; --- END BELT TRANSITION ---
```

The name `convoyeur`, distances, speeds, endstops, axes, temperatures, and positions depend on the firmware, electronics, and mechanics. The application inserts the configured block as-is after every Body and does not semantically validate it or look for a separate ejection file.

Before production, test the transition without a part where possible, with the nozzle clear, at low speed, and with an emergency stop within reach. Verify travel limits, endstops, collision risks, cables, clips, the probe, bed temperature, nozzle temperature, and the actual part position.

### Firmware-specific checks

- **Klipper:** define and calibrate the `manual_stepper` or a dedicated macro such as `EJECT_PART` in `printer.cfg` before calling it.
- **Marlin:** use only a configured and documented auxiliary axis, macro, extruder, or output. Do not assume that `MANUAL_STEPPER` exists.
- **RepRapFirmware/Duet:** define the additional axis, driver, steps/mm, direction, limits, and endstops in `config.g`, then call a validated macro.
- **Gantry push-off:** calibrate the lift, XY sweep, and any cooling or reheating waits independently.

### Motion and extrusion state

The transition must leave the machine in the state expected by the next source file:

- `G90` is absolute positioning; `G91` is relative positioning;
- `M82` is absolute extrusion; `M83` is relative extrusion;
- `G92 E0` resets the extruder's logical position without extruding.

Do not blindly add `M82` or `M83`; match the slicer's assumptions. A transition that leaves `G91` active can offset every subsequent coordinate. In absolute extrusion mode, inconsistent `E` values can cause unexpected extrusion or retraction. Avoid `M84` or `M18` in the transition unless your machine-specific procedure explicitly requires it: disabling motors can cause lost steps and loss of reference.

The software validates marker structure and the file plan only. It does not validate firmware commands, kinematics, temperatures, travel limits, or physical safety.

## Security and operational precautions

G-code is executable machine instruction, not harmless document data. Treat source files, `serie.csv`, transition settings, and downloaded binaries as untrusted until reviewed.

- Download releases only from the official [repository](https://github.com/Celeautech-Lab/Series-3D-printing-sequencer) and [Releases page](https://github.com/Celeautech-Lab/Series-3D-printing-sequencer/releases).
- Review the Header, every Body, the transition, and the final Footer before sending output to a printer.
- Confirm that the transition does not exceed axis limits, trigger an unexpected endstop, disable required motors, or move through a pinch or collision zone.
- Run a dry test or single-part test before a long series, and keep the emergency stop accessible.
- Do not rely on marker validation as a safety check: a structurally valid file can still contain unsafe G-code.
- Keep backups of original G-code and printer configuration files. Generate output into a separate path when testing.

## Launch from source

The source entry point is `main.py` in the application source directory. In the repository layout used by the release workflow, run from the repository root:

```bash
git clone https://github.com/Celeautech-Lab/Series-3D-printing-sequencer.git
cd Series-3D-printing-sequencer
python src/main.py
```

The application uses Python's standard library, including Tkinter. On Debian/Ubuntu, install Tkinter if it is not already available:

```bash
sudo apt install python3-tk
```

If you are working with a source export in which `main.py`, `gui.py`, and the other application modules are directly in the current directory rather than under `src/`, run:

```bash
python main.py
```

The GUI entry point handles the source-tree import fallback used by the application. No `requirements.txt` file is required for the source run; PyInstaller is needed only for the optional executable build below.

## Troubleshooting

### No G-code files found

Confirm that the selected folder contains files ending in `.gcode`, `.gco`, or `.g`. The scan is not recursive.

### A file is excluded by validation

Open the file as text and check for exactly one `; BODYSTART`, exactly one `; BODYEND`, the correct order, and at least one line between them. Remove extra marker occurrences and avoid adding text after the marker on the same line.

### `serie.csv` is not loaded

Confirm the exact filename and the two header rows. Check that every referenced filename exists in the selected folder and passes marker validation. Read the **Validation report** for the specific CSV error.

### Generation errors

- `No file selected`: no valid source file is loaded.
- `Invalid cycles value`: the cycle field is not an integer.
- `No parts selected (all occurrences are 0)`: every occurrence count is zero.
- `G-code composition failed:`: a source file could not be split or composed.
- `Save failed:`: the output file could not be written.
- `Series save failed:`: `serie.csv` could not be written.

### The executable does not start

Check that you downloaded the asset for the correct operating system and architecture. On Linux, add execute permission. On macOS, extract the archive and review the system's application security prompt. If launching from source, verify that Tkinter is installed and that you are using the intended Python interpreter.

## Optional: build an executable

The repository includes `build_exe.py` for a local PyInstaller build. This is optional; downloading a release is the recommended path. Run it from the repository root:

```bash
python -m pip install pyinstaller
python build_exe.py --asset PrintSeriesGenerator-Linux-x64
```

If `--asset` is omitted, the script chooses a platform-specific default. The build configuration uses:

- `PrintSeriesGenerator-Windows-x64.exe` on Windows;
- `PrintSeriesGenerator-Linux-x64` on Linux;
- `PrintSeriesGenerator-macOS-AppleSilicon` for macOS, packaged as `PrintSeriesGenerator-macOS-AppleSilicon.tar.gz`.

The script includes `src/settings.json`, uses a single executable on Windows/Linux, and creates a macOS application bundle archive. It removes prior `build/` and `dist/` directories before building and removes the intermediate `build/` directory afterward. Build on the target operating system; PyInstaller is not a cross-compiler.

## License

This project is distributed under the **[PolyForm Noncommercial License 1.0.0](LICENSE)**. Personal, hobby, or educational use and commercial use are governed by the terms and restrictions of that license. Read the repository's `LICENSE` file before using, modifying, or redistributing the software. For commercial licensing, integration, or partnership requests, contact **Antoine Navarro EI — [celeautech.contact@gmail.com](mailto:celeautech.contact@gmail.com)**.
