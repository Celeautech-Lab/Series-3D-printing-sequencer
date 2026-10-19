# Series-3D-printing-sequencer

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Interface](https://img.shields.io/badge/interface-Tkinter-2E8B57)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/license-PolyForm_Noncommercial-orange.svg)](LICENSE)

A Python/Tkinter desktop application that builds a print series from several G-code files. It keeps the **Header** of the first file, chains the **Body** sections in the requested order and quantity, inserts a transition/ejection between each part, and keeps the **Footer** of the last file.

> **Repository:** [github.com/Celeautech-Lab/Series-3D-printing-sequencer](https://github.com/Celeautech-Lab/Series-3D-printing-sequencer)

## How it works

The application scans a folder, checks the markers in each G-code file, optionally reads `serie.csv`, shows the sequence in an editable table and generates a compiled G-code file.

### Header, Body and Footer

Each source file must contain exactly one start marker and one end marker:

```gcode
; BODYSTART
; ... part printing commands ...
; BODYEND
```

The composer then splits each file into three sections:

- **Header**: everything before `; BODYSTART` (startup, heating, homing, etc.);
- **Body**: everything between `; BODYSTART` and `; BODYEND` (the toolpath of the part);
- **Footer**: everything after `; BODYEND` (cooldown or end of program).

In the final file, the Header of the first expanded file is written once, the Bodies are concatenated in order, and the Footer of the last expanded file is written once. An ejection/transition sequence is inserted **after every printed part, including the very last one**. This rule also frees the last part, so you need to include a cooldown or a wait in the transition if your process requires it.

### Worked example: 7 cycles

The following plan is used:

```csv
Cycles,7
Rank,Filename,Occurrences
1,PART_1.gcode,4
2,PART_2.gcode,5
3,PART_3.gcode,6
```

One cycle therefore contains:

```text
4 × PART_1.gcode + 5 × PART_2.gcode + 6 × PART_3.gcode = 15 parts
```

The generated file follows this sequence:

```text
1 initial heating / homing (Header)
Cycle 1: 4 × PART_1 + 5 × PART_2 + 6 × PART_3, with an ejection after each part
Cycle 2: 4 × PART_1 + 5 × PART_2 + 6 × PART_3, with an ejection after each part
...
Cycle 7: 4 × PART_1 + 5 × PART_2 + 6 × PART_3, with an ejection after each part
1 final cooldown (Footer)
```

The result is **7 cycles of [4 × PART_1 + 5 × PART_2 + 6 × PART_3] = 105 parts and 105 ejections**, followed by a final cooldown. The global Header comes from the first expanded part and the global Footer from the last one. The last ejection does appear before the Footer.

> The occurrence count is the number of copies of a row in each cycle. An occurrence of `0` excludes the row. If all occurrences are `0`, generation is refused.

## Installation and launch

The project uses Python and its standard library, including Tkinter:

```bash
git clone https://github.com/Celeautech-Lab/Series-3D-printing-sequencer.git
cd Series-3D-printing-sequencer
python main.py
```

On Debian/Ubuntu, install Tkinter if needed:

```bash
sudo apt install python3-tk
```

The application starts from `main.py` and opens the graphical interface.

## Preparing G-code files in the slicer

### Required markers

In the exported G-code, the following lines delimit the Body:

```gcode
; BODYSTART
...
; BODYEND
```

The validator works line by line after stripping leading and trailing whitespace. A line is accepted if it **starts** with the marker, so it can include an extra comment after it. Each file must contain a single `; BODYSTART` and a single `; BODYEND`, in that order.

### PrusaSlicer

1. Open **Printer Settings → Custom G-code**.
2. Add `; BODYSTART` at the beginning of the part's **Start G-code**, after the shared heating/homing commands if those should stay in the Header.
3. Add `; BODYEND` in the part's **End G-code**, before the commands that should form the Footer.
4. Slice and export each part as `.gcode`.

For a series, check in an exported file that both comments appear only once and that the next file starts with the same positioning and extrusion assumptions.

### OrcaSlicer

1. Go to **Printer → Machine start G-code** for the shared commands, and to **Printer / Process → Custom G-code** depending on the version.
2. Place `; BODYSTART` where the part's toolpath actually begins.
3. Place `; BODYEND` right after the last move belonging to the part and before the Footer.
4. Export the files and inspect the generated text: menu names may vary by version and profile.

### Bambu Studio

1. Open the printer profile and the custom G-code fields under **Machine start G-code** and **Machine end G-code** (or **Printer settings**, depending on the version).
2. Add `; BODYSTART` and `; BODYEND` in the custom sections that surround the part-specific commands.
3. Check the exported `.gcode` file, because Bambu Studio may add machine commands before and after the custom commands.

If the Bambu profile does not let you place both markers cleanly around the Body only, do not use the file as is: the import will show the matching structure error.

### Cura

1. Open **Settings → Printer → Manage Printers → Machine Settings**.
2. Use the **Start G-code** and **End G-code** fields to place the markers at the start and end of the section to sequence.
3. Export the file and search for `; BODYSTART` and then `; BODYEND` in a text editor.

In every slicer, the markers are comments: they do not move the machine. They only serve as a splitting contract for the sequencer.

## Firmware Configuration & Hardware Requirements (Klipper / Marlin / RepRapFirmware)

This application cannot guess your printer's belt kinematics, pins, endstops, travel limits or pushing method. The ejection code depends on the hardware and firmware. Since no real conveyor belt is available here to test a specific ejection, the repository does not ship an untested universal ejection file: you must configure and validate the transition on the target machine.

Before a long series, test the transition without a part, with the nozzle clear, at low speed and with an emergency stop within reach. The examples below are templates to adapt. They are not ready-to-use commands for every board.

### Extruder between parts: `M82`, `M83` and `G92 E0`

- `M82` selects **absolute** extrusion: the `E` value accumulates throughout the file;
- `M83` selects **relative** extrusion: each `E` value is a relative move;
- `G92 E0` resets the extruder's logical position without pushing or retracting filament.

At the boundary between two Bodies, place `G92 E0` where it is consistent with the slicer, typically at the end of the transition or at the start of the next Body. This is essential when the slicer works in absolute mode: without this reset, a file that ends at `E2450` can cause the next small value to be interpreted as a huge retraction or excessive feed. Check the first and last `E` moves of the source files and keep a consistent policy.

Example of the principle:

```gcode
; end of previous Body / transition
G92 E0
; ejection sequence validated on the machine
; before the next Body
G90
M82                 ; or M83, exactly as in the slicer's G-code
G92 E0              ; if the start of the Body requires it
```

Do not blindly add `M82` or `M83`: the final mode must be the one the next file expects.

### Absolute positioning `G90` and relative positioning `G91`

`G90` enables absolute axis positioning and `G91` enables relative positioning. An ejection often uses `G91` to lift the nozzle by a controlled distance, then `G90` for an absolute position or sweep. The transition G-code must **always end in `G90`**, and must also restore `M82` or `M83` to the expected mode before the next Body starts:

```gcode
M400
G91
G1 Z15 F600
G90                 ; required before the next Body
G92 E0
M82                 ; or M83 depending on the slicer
```

Leaving the machine in `G91` can offset every coordinate of the next Body and cause a collision.

### Driving a conveyor belt or an auxiliary axis

The belt must have a validated direction, distance, speed, end stop and safety zone. It is better to call a dedicated macro than to insert a board-specific sequence into every file.

#### Klipper

Configure a properly calibrated `[manual_stepper belt]` in `printer.cfg`, or a dedicated G-code macro. The transition can call:

```gcode
EJECT_PART
G92 E0
G90
M82                 ; or M83, depending on the slicer
```

The `EJECT_PART` macro must contain the allowed moves, waits, limits and, if needed, endstops. With a `manual_stepper`, the principle can be:

```gcode
MANUAL_STEPPER STEPPER=belt MOVE=400 SPEED=50
```

This command is only valid if the `[manual_stepper belt]` section and its parameters actually exist in `printer.cfg`. Test the macro on its own before calling it from the series.

#### Marlin

Marlin can use a configured secondary axis (`U`, `V` or `W`), a second extruder `T1` configured without heating, or a GPIO pin. For an extruder used as a mechanical axis, cold extrusion protection must be handled according to the board configuration. `M302 S0` disables cold extrusion protection and should only be used if this is truly necessary and safe. A pin can be driven with `M42` if the pin and its levels have been documented.

```gcode
; Conceptual example: U/V/W axis, T1 or macro defined in Marlin
; EJECT_PART
; or axis command configured by the firmware
M42 P<pin> S<0-or-1>  ; only after validating the pin and level
G92 E0
G90
```

Do not assume `MANUAL_STEPPER` exists in Marlin. The exact command depends on the version, the board and `Configuration.h`/`Configuration_adv.h`.

#### RepRapFirmware (Duet)

Define the additional linear axis and its driver in `config.g`, with its steps/mm, limits, direction and endstops. A system macro can then be called from the transition:

```gcode
M98 P"eject.g"
G92 E0
G90
```

The path may be, for example, `0:/sys/macros/eject.g` depending on the setup. The macro file and the axis must be validated manually on the Duet. The driver name and syntax may vary with the configuration.

### Alternative without a belt: gantry push-off ejection

On a CoreXY or standard Cartesian printer fitted with a part pusher, lift the nozzle, wait for the bed to cool if needed, then perform a calibrated XY sweep:

```gcode
M400
G91
G1 Z15 F600
G90
M190 R30           ; wait for about 30 °C if the process requires it
; calibrated XY sweep/push here
G92 E0
G90
M190 S<bed_temperature>    ; reheat for the next part
M109 S<nozzle_temperature> ; if the process requires it
```

`M190 R30` is only an example: choose a temperature suited to the material. After ejection, keep or restore bed heating (`M190 S...`) and nozzle heating (`M109 S...`) before the next part. Check the limits, clips, probe, cables, nozzle and the actual part position. Never copy sweep coordinates without measuring them.

### Active motors, homing and idle time

Putting `M84` or `M18` in the transition G-code is **forbidden**: disabling the motors can cause lost steps and loss of the reference between two parts. On Klipper, set `[idle_timeout]` so that a cooldown or a long ejection does not unexpectedly turn off the motors. Also check the equivalent behavior of your firmware.

After a mechanical ejection, you can add the following if the machine allows it and the area is clear:

```gcode
G28 X Y
G90
G92 E0
```

`G28 X Y` is optional and depends on the machine. It can correct lost steps, but it does not replace mechanical tuning or testing the transition. A full homing can move mechanisms differently: only use it if you know it is safe.

### Pre-production check

Make sure that:

1. the transition ends in `G90` and in the correct `M82`/`M83` mode;
2. `G92 E0` is placed at a safe boundary;
3. the belt or sweep has reliable limits, speed and stop;
4. no `M84`/`M18` disables the motors, and the timeout does not cut motion;
5. the final file contains the expected number of Bodies, transitions and ejections, including the last one.

## Importing a folder into the application

1. Run `python main.py`.
2. Click **Select folder** (or the folder selection button shown in the interface).
3. Choose the folder that contains the `.gcode`, `.gco` or `.g` files.
4. The application only scans this folder, not its subfolders. Other extensions are ignored.
5. Valid files appear in the table. Invalid files are excluded from the sequence.
6. If a problem is detected, the **`Validation report`** dialog opens. Click **OK** to keep the valid files and continue.
7. Check the occurrences, order, number of cycles and transition G-code in the settings before generating.

If no supported G-code is found, the application shows a `No G-code files found in:` error and clears the folder selection.

## Creating or editing `serie.csv`

### From the interface

After importing a folder:

1. Change the number of cycles in the matching field.
2. Edit an occurrence directly in the table (double-click or numeric control, depending on the interface version).
3. Reorder the rows by drag and drop if needed.
4. Use **Save series** to write `serie.csv` to the selected folder.

The interface can also create the file automatically from the visible rows. When editing in the table, the value is limited to `0`–`999`, and a negative value entered in the interface is reset to `0`. When reading a CSV, however, any integer occurrence `>= 0` is accepted (there is no `999` cap), and a negative value causes a format error.

### With Excel or a text editor

Create a file named exactly `serie.csv`, UTF-8 encoded, with this exact structure: a `Cycles,<number>` line, then the `Rank,Filename,Occurrences` header, then one line per file.

```csv
Cycles,7
Rank,Filename,Occurrences
1,PART_1.gcode,4
2,PART_2.gcode,5
3,PART_3.gcode,6
```

`Cycles,7` means seven passes through the plan. The following lines mean 4, 5 and 6 copies per cycle, respectively. The parser requires the header on the second line. A file without it, such as plain data lines directly after `Cycles,7`, is invalid. Filenames must exactly match the files in the imported folder.

The parser reads the first two columns of the `Cycles` line and the first three columns of the header and data lines. It accepts a UTF-8 BOM and ignores completely empty lines. Ranks are numeric and are sorted before composition. The number of cycles must be an integer greater than or equal to `1`, and occurrences must be integers greater than or equal to `0`.

**Saving from the interface.** The **Save series** button creates or overwrites `serie.csv` in the selected folder (or in a folder you choose if none is loaded). It writes the same structure, with an empty trailing comma on the first line: `Cycles,7,`. The parser accepts this comma. If you want the exact format shown above, remove that trailing comma in a text editor after saving.

## G-code composition rules

For the expanded plan (cycles × rows × occurrences), the final file has this logical structure:

```text
Header of the first file
; BODYSTART
Body of part 1
transition / ejection after part 1
Body of part 2
...
Body of the last part
transition / ejection after the last part
; BODYEND
Footer of the last file
```

The transition is therefore inserted **between Bodies and after the last Body**. The block is stored inline in `settings.json` under the `transition_gcode` key and can be edited from the settings window. The current implementation does not look for a separate ejection file.

A built-in example might look like this, but it must be replaced or adapted to your machine:

```gcode
; --- TRANSITION TO ADAPT ---
M400
G91
G1 Z15 F600
G90
EJECT_PART
G92 E0
; --- END TRANSITION ---
```

Do not send this example without defining `EJECT_PART` and checking all the kinematics.

## Errors and troubleshooting

### `Validation report` dialog

When a folder is imported, the **`Validation report`** dialog can open as soon as a file has a marker problem or `serie.csv` contains an error. It is an informational report: clicking **OK** does not remove the valid files and does not cancel the import. The report lists the excluded files and the exact cause.

Common validation causes:

- `BODYSTART and BODYEND tags missing`: neither marker was found;
- `BODYSTART tag missing`: the start marker is missing;
- `BODYEND tag missing`: the end marker is missing;
- `BODYSTART tag duplicated` or `BODYEND tag duplicated`: repeated marker;
- `tag order reversed (BODYEND before BODYSTART)`: wrong order;
- `read failed (...)`: the file cannot be read.

An empty file is reported as missing both tags. The validator does not check the meaning of each G-code command, temperatures, mechanical limits or ejection safety.

### CSV errors

Check the exact name `serie.csv`, the UTF-8 encoding, the first line `Cycles,7`, numeric ranks, filenames and occurrences. The report may show, among others:

```text
CSV must have at least 2 rows (Cycles header and data header)
Row 1: Must start with 'Cycles'
Row 1: Cycles value is not an integer
Row 2: Headers must be 'Rank,Filename,Occurrences'
Row N: Must contain 3 columns
Row N: Filename is empty
Row N: Rank is not an integer
Row N: Occurrences is not an integer
Row N: Occurrences must be >= 0
```

If a CSV row references a missing or invalid file, it is listed in the same `Validation report`. If the CSV is unreadable or malformed, the import shows the error and then fills the table with the valid G-code files it found. Files not listed in a valid CSV get `0` occurrences, and the cycles field keeps its current value (initially `1`).

A missing `serie.csv` is not an error: the application can use the valid files found in the folder.

### Generation and save errors

| Situation | Expected message |
|---|---|
| No valid file loaded | `No file selected` |
| Cycles value not an integer | `Invalid cycles value` |
| All occurrences set to zero | `No parts selected (all occurrences are 0)` |
| Composition failure | `G-code composition failed:` followed by details |
| Write failure | `Save failed:` followed by the system error |
| Series save failure | `Series save failed:` followed by details |

If no G-code file is found, check the extension and the selected folder. If composition fails, reopen the report, fix the markers, CSV filenames and occurrences, then re-import the folder. Before printing, open the generated file and count the expected `; BODYSTART`, `; BODYEND`, transitions and ejection commands.

## Pre-generation checklist

1. Every planned file has exactly one `; BODYSTART` and one `; BODYEND` in the right order.
2. The imported folder does not contain old G-code files selected by mistake.
3. `serie.csv` contains the correct cycles, filenames, ranks and occurrences.
4. The transition has been adapted to the actual firmware and hardware.
5. `G92 E0`, `G90`, `M82`/`M83`, temperatures, limits and active motors have been checked.
6. The last part is ejected before the Footer/final cooldown.
7. The generated file has been inspected and tested using the printer's usual safety procedures.

The application validates the marker structure, file references and series plan. It does not validate machine compatibility, the meaning of G-code commands, travel limits, temperatures, speeds or physical safety.

## License & Commercial Use

This project is licensed under the **[PolyForm Noncommercial License 1.0.0](LICENSE)**.

- **Personal / hobby / educational use:** Free and encouraged.
- **Commercial use & derivatives:** Strictly prohibited without prior explicit agreement.

For commercial licensing, product integration or partnership inquiries:  
**Contact:** Antoine Navarro EI — [celeautech.contact@gmail.com](mailto:celeautech.contact@gmail.com)