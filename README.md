# Print Series Generator

A Python/Tkinter desktop application for composing a repeatable 3D-printing series from tagged G-code files. It validates the body boundaries, lets you define an ordered plan with per-cycle occurrences, inserts a configurable inter-part transition, and exports one compiled G-code file.

> **Repository:** [Celeautech-Lab/Series-3D-printing-sequencer](https://github.com/Celeautech-Lab/Series-3D-printing-sequencer)

The application prepares text; it does not validate that a generated file is safe for a particular printer. The transition block, firmware state, motion limits, temperatures, and ejection hardware remain the operator's responsibility.

## Contents

- [Download a release](#download-a-release)
- [Run from source](#run-from-source)
- [Quick start](#quick-start)
- [How composition works](#how-composition-works)
- [Prepare source G-code](#prepare-source-g-code)
- [`serie.csv` format](#seriecsv-format)
- [Transition G-code and machine safety](#transition-g-code-and-machine-safety)
- [Validation, errors, and limitations](#validation-errors-and-limitations)
- [Build from source (optional)](#build-from-source-optional)
- [License](#license)

## Download a release

The repository has a [v1.0.0 release](https://github.com/Celeautech-Lab/Series-3D-printing-sequencer/releases/tag/v1.0.0). Its release notes list these standalone assets:

- `PrintSeriesGenerator-Windows.exe` — Windows;
- `PrintSeriesGenerator-Linux` — Linux;
- `PrintSeriesGenerator-macOS-AppleSilicon.tar.gz` — macOS Apple Silicon.

These are compiled binaries, not the Python source tree. Download them from the repository's [Releases page](https://github.com/Celeautech-Lab/Series-3D-printing-sequencer/releases), inspect the release notes and asset name, and follow your organization's software policy before running them. The release page is the authority for currently published assets; the names above are the names attested in `v1.0.0` release notes.

On Linux, the release notes provide:

```bash
chmod +x PrintSeriesGenerator-Linux
./PrintSeriesGenerator-Linux
```

On macOS, extract `PrintSeriesGenerator-macOS-AppleSilicon.tar.gz` and open the application bundle. macOS may require an approval in **System Settings → Privacy & Security**, depending on local security settings. The release notes identify Apple Silicon; they do not establish support for Intel macOS.

## Run from source

The repository source layout uses `src/` and the entry point is `src/main.py`:

```bash
git clone https://github.com/Celeautech-Lab/Series-3D-printing-sequencer.git
cd Series-3D-printing-sequencer
python src/main.py
```

The application uses Python's standard library and Tkinter. On Debian/Ubuntu, install Tkinter if it is not already available:

```bash
sudo apt install python3-tk
```

A graphical desktop session is required. The source entry point opens the Tkinter interface; cancelling the interface does not generate a sequence.

## Quick start

1. Launch the release binary or run `python src/main.py`.
2. Click **Select folder** and choose the folder that directly contains the source G-code files. Subfolders are not scanned.
3. The application recognizes `.gcode`, `.gco`, and `.g` files, case-insensitively. Other extensions are ignored.
4. Review the validation report. Files with invalid markers are excluded; valid files are loaded into the table.
5. If the folder contains `serie.csv`, review its imported cycles, order, and occurrences.
6. Double-click an **Occurrences** value to edit it (`0`–`999` in the GUI), or drag rows to change their order.
7. Set **Cycles**. The displayed totals are parts per cycle and total planned parts.
8. Open **Settings** and review the inter-part transition G-code. Adapt it to the target machine.
9. Click **Generate G-code**, choose an output path, and inspect the saved file before sending it to a printer.

![Print sequence overview](docs/images/print-sequence-overview.png)

*Review the print order, occurrences, cycle count, and generated totals before composing the series.*

The **Save series** button creates or overwrites `serie.csv` in the selected folder. If no folder is selected, it asks for a destination folder.

## How composition works

### Header, Body, and Footer

Each source file must contain exactly one of each marker, in this order, with at least one line between them:

```gcode
; BODYSTART
; part-specific printing commands
; BODYEND
```

The composer splits every source file as follows:

- **Header:** all lines before `; BODYSTART`;
- **Body:** all lines strictly between `; BODYSTART` and `; BODYEND`;
- **Footer:** all lines after `; BODYEND`.

For the final file, the composer writes:

```text
Header of the first expanded file
; BODYSTART
Body 1
transition
Body 2
...
Body N
transition after Body N
; BODYEND
Footer of the last expanded file
```

The source marker lines are not copied for every part. One shared `; BODYSTART` and one shared `; BODYEND` are written around the combined bodies. The transition is inserted **after every body, including the final body**, so the final transition appears before the last footer.

The expanded order is produced by repeating the selected table order for each cycle. Within one cycle, a row is repeated by its occurrence count before moving to the next row. A row with `0` occurrences contributes no body. Generation is refused when all occurrence counts are zero.

### Example: seven cycles

```csv
Cycles,7
Rank,Filename,Occurrences
1,PART_1.gcode,4
2,PART_2.gcode,5
3,PART_3.gcode,6
```

One cycle contains `4 + 5 + 6 = 15` parts. Seven cycles produce 105 parts and 105 transitions. The sequence is seven repetitions of:

```text
PART_1.gcode × 4, then PART_2.gcode × 5, then PART_3.gcode × 6
```

The first file in the fully expanded order supplies the single output header; the last file in that order supplies the single output footer.

## Prepare source G-code

The validator reads each file as UTF-8 with replacement for decoding errors and compares each line after `strip()`. A marker is accepted only when the complete stripped line is exactly the marker. For example, `; BODYSTART extra text` is **not** accepted.

Every file intended for the sequence must have:

1. exactly one `; BODYSTART`;
2. exactly one `; BODYEND`;
3. `BODYSTART` before `BODYEND`;
4. at least one line between the markers.

The markers are comments: they do not move the printer. Place them around the part-specific commands you want to repeat. Commands before `; BODYSTART` become the first file's header; commands after `; BODYEND` become the last file's footer. Inspect each exported file rather than relying only on slicer menu labels.

Typical slicer locations include custom start/end G-code in PrusaSlicer, machine/profile custom G-code in OrcaSlicer, machine start/end fields in Bambu Studio, and Machine Settings in Cura. Exact menu names vary by version and profile; the exported G-code is authoritative.

## `serie.csv` format

The repository includes an example at [`examples/serie.csv`](https://github.com/Celeautech-Lab/Series-3D-printing-sequencer/blob/main/examples/serie.csv). The file name loaded by the application must be exactly `serie.csv` and must be in the selected folder.

Required layout:

```csv
Cycles,7
Rank,Filename,Occurrences
1,PART_1.gcode,4
2,PART_2.gcode,5
3,PART_3.gcode,6
```

The parser requires:

- row 1 to start with `Cycles` (case-insensitive), with an integer of at least `1` in column 2;
- row 2's first three columns to be `Rank,Filename,Occurrences` (case-insensitive; surrounding whitespace is ignored);
- each non-empty data row to have at least three columns;
- a non-empty filename, an integer rank of at least `1`, and a non-negative integer occurrence count;
- unique rank values.

It accepts a UTF-8 BOM, ignores completely empty rows, sorts rows by rank, and ignores columns after the first three. Filenames are matched by exact filename against valid files in the selected folder. Missing names and tag-invalid names are reported. Files not listed in a usable CSV row remain available in the table with `0` occurrences. A malformed CSV is reported and the application can continue with the valid files it found.

The GUI's inline occurrence editor is limited to `0`–`999`; the CSV parser itself accepts any non-negative integer. **Save series** writes UTF-8 with a BOM and a first row that includes a trailing empty field (`Cycles,7,`), which the parser accepts.

## Transition G-code and machine safety

The transition is editable in **Settings** and persisted under the `transition_gcode` key in `settings.json`. The supplied default is:

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

![Inter-part transition settings](docs/images/inter-part-transition-settings.png)

*The inter-part transition is editable and persistent; it must be adapted to the target printer and firmware.*

This block is an example, not a universal or machine-ready ejection routine. `MANUAL_STEPPER`, the `convoyeur` name, distances, speeds, endstops, axes, positions, and temperature behavior depend on the firmware, electronics, mechanics, and configuration. The application inserts the current text as-is after every body and does not semantically validate G-code.

Before a production series:

- test the transition without a part where possible, with the nozzle clear, at reduced speed, and with an emergency stop accessible;
- verify the belt or pusher direction, travel distance, speed, endstops, limits, pinch points, cables, clips, probe, nozzle, and actual part position;
- ensure the transition restores the positioning and extrusion state expected by the next body;
- check `G90`/`G91`, `M82`/`M83`, and `G92 E0` behavior against the slicer's output;
- inspect heating, cooling, waits, and the final transition before the footer;
- do not assume a Klipper command works on Marlin or RepRapFirmware/Duet. Configure and test firmware-specific macros or axes separately;
- avoid `M84` or `M18` in a transition unless a documented machine-specific procedure explicitly requires it, because disabling motors can lose position.

G-code is executable machine instruction, not harmless document data. Treat source G-code, `serie.csv`, transition settings, and downloaded binaries as untrusted until reviewed. The software does not check for collisions, unsafe temperatures, firmware compatibility, kinematics, travel limits, pin assignments, or physical safety.

## Validation, errors, and limitations

![G-code validation report](docs/images/gcode-validation-report.png)

*Files with invalid body markers are reported and excluded from the sequence.*

The validation report can contain these code-defined conditions:

- `BODYSTART and BODYEND tags missing`;
- `BODYSTART tag missing` or `BODYEND tag missing`;
- `BODYSTART tag duplicated` or `BODYEND tag duplicated`;
- `tag order reversed (BODYEND before BODYSTART)`;
- `empty body between BODYSTART and BODYEND`;
- a file read failure;
- a malformed `serie.csv`;
- a CSV filename that is missing or tag-invalid.

Invalid G-code files are excluded from the table. A folder must contain at least one supported G-code file to be accepted. Generation then refuses or reports an error when no valid file is available, cycles are invalid, or all occurrences are zero. Composition can still fail if a file cannot be read or split at generation time; inspect the displayed error and the source files.

The validator is deliberately limited: it checks readability and marker structure only. It does not parse or simulate G-code. It does not prove that bodies share compatible coordinates, temperatures, tool state, extrusion mode, homing assumptions, or firmware syntax. Review the complete generated file—header, every body, every transition, the final `; BODYEND`, and footer—before machine use.

## Build from source (optional)

Most users should use a published release or run from source. For an optional local build, the repository provides `build_exe.py` and expects the `src/` layout. Install PyInstaller first:

```bash
python -m pip install pyinstaller
python build_exe.py --asset PrintSeriesGenerator-Linux-x64
```

The script selects the platform-specific mode and includes `src/settings.json`:

- Windows: one executable, normally named `PrintSeriesGenerator-Windows-x64.exe`;
- Linux: one executable, normally named `PrintSeriesGenerator-Linux-x64`;
- macOS: an `.app` bundle archived as `PrintSeriesGenerator-macOS-AppleSilicon.tar.gz`.

Build on the target operating system; this is not a cross-compilation procedure. The script removes previous `build/` and `dist/` directories before building. The workflow also documents Python 3.11 and a Linux Tkinter installation, but a local build still depends on the host's Python, Tkinter, PyInstaller, and platform environment. A build completing is not a hardware-safety or cross-platform compatibility test.

## License

This project is distributed under the **[PolyForm Noncommercial License 1.0.0](LICENSE)**. The repository's `LICENSE` file contains the governing terms and the required notice:

```text
Required Notice: Copyright (c) 2026 Antoine Navarro EI
```

The license permits noncommercial purposes as defined in its text. Commercial use, distribution, resale, or integration into a commercial product or service requires an explicit written agreement from the author. Read the complete [`LICENSE`](LICENSE) before using, modifying, or distributing the project.

For commercial licensing or partnership inquiries, the license names **Antoine Navarro EI** at [celeautech.contact@gmail.com](mailto:celeautech.contact@gmail.com).
