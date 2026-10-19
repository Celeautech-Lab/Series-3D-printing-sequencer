# gui.py — Print series generator interface

from __future__ import annotations

import tkinter as tk
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    from . import csv_parser, sequencer, settings
    from .validator import check_files
except ImportError:  # Supports direct execution from the src directory.
    import csv_parser
    import sequencer
    import settings
    from validator import check_files

GCODE_EXTENSIONS = {".gcode", ".gco", ".g"}
DOC_URL = "https://github.com/CelestinSegesse/Celeauprinter/blob/main/README_TAGS.md"
SERIE_CSV_NAME = "serie.csv"


@dataclass
class PlanItem:
    path: Path
    count: int


@dataclass
class ExecutionPlan:
    mode: str
    repetitions: int
    items: list[PlanItem]


class SeriesGeneratorUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.selected_folder: Path | None = None
        self.valid_files: list[Path] = []
        self.invalid_files: list[Path] = []
        self.issues: list = []
        self.plan: ExecutionPlan | None = None
        self.cycles_var = tk.StringVar(value="1")
        self.edit_item = None
        self.spinbox_widget = None
        self.drag_source = None
        self.transition_gcode = settings.load_transition()
        self.output_path: Path | None = None

        self._setup_ui()

    def _setup_ui(self):
        """Configure the user interface."""
        self.root.title("Print series generator")
        self.root.geometry("700x680")

        # ============ TOP FRAME: FOLDER SELECTION ============
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top_frame, text="Folder:").pack(side=tk.LEFT)
        self.folder_label = ttk.Label(top_frame, text="No folder selected", foreground="gray")
        self.folder_label.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            top_frame,
            text="Settings",
            command=self.open_settings
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            top_frame,
            text="Select folder",
            command=self.select_folder
        ).pack(side=tk.RIGHT)

        # ============ TABLE FRAME: VALID FILES ============
        table_frame = ttk.LabelFrame(self.root, text="Print sequence:", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Frame containing treeview and scrollbar
        tree_container = ttk.Frame(table_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        columns = ("N°", "File", "Occurrences")
        self.tree = ttk.Treeview(tree_container, columns=columns, height=15, show="headings")

        self.tree.column("N°", width=40, anchor=tk.CENTER)
        self.tree.column("File", width=400, anchor=tk.W)
        self.tree.column("Occurrences", width=80, anchor=tk.CENTER)

        self.tree.heading("N°", text="N°")
        self.tree.heading("File", text="File")
        self.tree.heading("Occurrences", text="Occurrences")

        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bindings: edition and drag & drop
        self.tree.bind("<Double-1>", lambda e: self.edit_occurrence())
        self.tree.bind("<ButtonPress-1>", self._on_drag_start)
        self.tree.bind("<B1-Motion>", self._on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self._on_drag_end)

        # ============ PER-CYCLE TOTAL DISPLAY ============
        per_cycle_frame = ttk.Frame(self.root, padding=10)
        per_cycle_frame.pack(fill=tk.X, padx=10, pady=0)

        self.per_cycle_label = tk.Label(
            per_cycle_frame,
            text="",
            font=("TkDefaultFont", 9),
            foreground="black"
        )
        self.per_cycle_label.pack(anchor=tk.E, padx=5, pady=2)

        # ============ CYCLES INPUT FRAME ============
        cycles_frame = ttk.Frame(self.root, padding=10)
        cycles_frame.pack(fill=tk.X, padx=10, pady=0)

        ttk.Label(cycles_frame, text="Cycles:").pack(side=tk.LEFT, padx=5)
        self.cycles_spinbox = ttk.Spinbox(
            cycles_frame,
            from_=1,
            to=100,
            textvariable=self.cycles_var,
            width=5
        )
        self.cycles_spinbox.pack(side=tk.LEFT, padx=5)
        self.cycles_spinbox.bind("<KeyRelease>", lambda e: self._update_totals())

        # ============ CYCLES TOTALS DISPLAY FRAME ============
        cycles_totals_frame = ttk.Frame(self.root, padding=10)
        cycles_totals_frame.pack(fill=tk.X, padx=10, pady=0)

        self.cycles_totals_label = tk.Label(
            cycles_totals_frame,
            text="",
            font=("TkDefaultFont", 9),
            foreground="black"
        )
        self.cycles_totals_label.pack(anchor=tk.E, padx=5, pady=2)

        # ============ FRAME BUTTONS (CANCEL / GENERATE / SAVE SERIES) ============
        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.pack(fill=tk.X)

        # Packed right-to-left: Cancel, then Generate, then Save series
        # so that "Save series" ends up on the LEFT of "Generate G-code".
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="Generate G-code", command=self.generate_gcode).pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="Save series", command=self.save_series).pack(side=tk.RIGHT, padx=2)

        # ============ STATUS BAR ============
        self.status_label = ttk.Label(
            self.root,
            text="",
            relief=tk.SUNKEN,
            padding=5
        )
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

    # ============================================================
    # SETTINGS WINDOW
    # ============================================================

    def open_settings(self):
        """Open the transition G-code editor."""
        self._close_spinbox()

        dialog = tk.Toplevel(self.root)
        dialog.title("Inter-part transition G-code")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        dialog.grab_set()

        # Header
        tk.Label(
            dialog,
            text="Inter-part transition G-code",
            font=("Arial", 12, "bold")
        ).pack(pady=10)

        hint = tk.Label(
            dialog,
            text="This block is inserted between two consecutive parts.\n"
                 "Adjust it to match the final machine (belt distance, speed, endstop).",
            font=("Arial", 9),
            fg="gray"
        )
        hint.pack(padx=10, pady=5)

        # Text widget
        text_widget = tk.Text(dialog, height=20, width=80, wrap=tk.WORD)
        text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", self.transition_gcode)

        # Button frame
        button_frame = ttk.Frame(dialog, padding=10)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def do_save():
            content = text_widget.get("1.0", tk.END)
            self.transition_gcode = content
            settings.save_transition(content)
            messagebox.showinfo("Settings", "Transition G-code saved.", parent=dialog)
            dialog.destroy()

        def do_reset():
            if messagebox.askyesno("Reset", "Restore the default transition G-code?", parent=dialog):
                default = settings.reset_transition()
                self.transition_gcode = default
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", default)

        ttk.Button(button_frame, text="Restore default", command=do_reset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save", command=do_save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    # ============================================================
    # FOLDER SELECTION & CSV LOADING
    # ============================================================

    def _scan_gcode_files(self) -> list[Path]:
        """Return every supported G-code file in the selected folder."""
        if self.selected_folder is None:
            return []
        return sorted(
            f for f in self.selected_folder.glob("*")
            if f.is_file() and f.suffix.lower() in GCODE_EXTENSIONS
        )

    def select_folder(self):
        """Select folder, load CSV if present, validate files."""
        folder = filedialog.askdirectory(title="Select folder")
        if not folder:
            return

        self.selected_folder = Path(folder)
        self.folder_label.config(text=str(self.selected_folder), foreground="black")

        # Collect supported G-code files; serie.gcode is not treated specially.
        gcode_files = self._scan_gcode_files()

        if not gcode_files:
            messagebox.showerror(
                "Error",
                f"No G-code files found in:\n{self.selected_folder}"
            )
            self.selected_folder = None
            self.folder_label.config(text="No folder selected", foreground="gray")
            return

        # Validate tags
        self.issues = check_files(gcode_files)
        invalid_paths = {issue.path for issue in self.issues}
        self.valid_files = [f for f in gcode_files if f not in invalid_paths]
        self.invalid_files = [f for f in gcode_files if f in invalid_paths]

        # Load serie.csv if present
        csv_path = self.selected_folder / SERIE_CSV_NAME
        csv_config = None
        csv_errors = []

        if csv_path.exists():
            try:
                csv_config = csv_parser.parse_serie_csv(csv_path)

                # Check that CSV files exist
                valid_names = {f.name for f in self.valid_files}
                invalid_names = {f.name for f in self.invalid_files}

                missing = []
                excluded = []
                kept_items = []

                for item in csv_config.items:
                    if item.filename in valid_names:
                        kept_items.append(item)
                    elif item.filename in invalid_names:
                        excluded.append(item.filename)
                    else:
                        missing.append(item.filename)

                csv_config = csv_parser.SerieConfig(
                    cycles=csv_config.cycles,
                    items=kept_items
                )

                if missing:
                    csv_errors.append(("Files listed in serie.csv but not found", missing))
                if excluded:
                    csv_errors.append(("Files listed in serie.csv but tag-invalid", excluded))

            except csv_parser.CSVFormatError as exc:
                csv_config = None
                csv_errors.append(("serie.csv format error", [str(exc)]))

        # Show dialog if issues, otherwise populate directly
        if self.issues or csv_errors:
            self._show_issues_dialog(csv_config, csv_errors)
        else:
            self._populate_table(csv_config)
            self.status_label.config(
                text=f"✓ {len(self.valid_files)} valid file(s) | ⚠ 0 excluded"
            )

    def _show_issues_dialog(self, csv_config, csv_errors):
        """Display excluded files and CSV problems."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Validation report")
        dialog.geometry("600x480")
        dialog.transient(self.root)
        dialog.grab_set()

        total_issues = len(self.issues) + sum(len(items) for _, items in csv_errors)

        title_label = tk.Label(
            dialog,
            text=f"✕ {total_issues} file(s) excluded:",
            font=("Arial", 11, "bold"),
            fg="darkred"
        )
        title_label.pack(pady=10)

        # Text area for errors
        text_widget = tk.Text(dialog, height=12, width=65, wrap=tk.WORD)
        text_widget.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        # Tag errors
        if self.issues:
            text_widget.insert(tk.END, "Tag validation errors:\n")
            for issue in self.issues:
                text_widget.insert(tk.END, f"• {issue.path.name}\n   → {issue.reason}\n\n")

        # CSV errors
        if csv_errors:
            if self.issues:
                text_widget.insert(tk.END, "\nSerie.csv issues:\n")
            else:
                text_widget.insert(tk.END, "Serie.csv issues:\n")
            for error_type, items in csv_errors:
                text_widget.insert(tk.END, f"{error_type}:\n")
                for item in items:
                    text_widget.insert(tk.END, f"  • {item}\n")
                text_widget.insert(tk.END, "\n")

        text_widget.config(state=tk.DISABLED)

        # Button frame
        button_frame = ttk.Frame(dialog, padding=10)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        github_link = tk.Label(
            button_frame,
            text="View documentation on GitHub",
            fg="blue",
            cursor="hand2",
            font=("Arial", 10, "underline")
        )
        github_link.pack(side=tk.LEFT, padx=5)
        github_link.bind("<Button-1>", lambda e: webbrowser.open(DOC_URL))

        def on_close():
            self._populate_table(csv_config)
            self.status_label.config(
                text=f"✓ {len(self.valid_files)} valid file(s) | ⚠ {len(self.issues)} excluded"
            )
            dialog.destroy()

        tk.Button(
            button_frame,
            text="OK",
            command=on_close
        ).pack(side=tk.RIGHT, padx=5)

    def _populate_table(self, csv_config: csv_parser.SerieConfig | None):
        """Fill the table from valid files + CSV when available."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Map: filename -> occurrences (from CSV when available)
        csv_map = {}
        ordered_files = []

        if csv_config:
            for csv_item in csv_config.items:
                csv_map[csv_item.filename] = csv_item.occurrences
                for f in self.valid_files:
                    if f.name == csv_item.filename:
                        ordered_files.append(f)
                        break
            self.cycles_var.set(str(csv_config.cycles))

        # Append files not listed in the CSV
        for f in self.valid_files:
            if f not in ordered_files:
                ordered_files.append(f)

        # Insert into the table
        for idx, file in enumerate(ordered_files, start=1):
            occurrences = csv_map.get(file.name, 0)
            self.tree.insert("", "end", values=(idx, file.name, str(occurrences)))

        self._update_totals()

    # ============================================================
    # TABLE EDITING
    # ============================================================

    def _close_spinbox(self):
        """Close the inline spinbox if open."""
        if self.spinbox_widget:
            self.spinbox_widget.destroy()
            self.spinbox_widget = None
            self.edit_item = None

    def edit_occurrence(self):
        """Edit the occurrence count (double-click)."""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item, "values")
        current_value = int(values[2])

        self._close_spinbox()

        bbox = self.tree.bbox(item, "Occurrences")
        if not bbox:
            return

        x, y, w, h = bbox

        var = tk.StringVar(value=str(current_value))
        spin = ttk.Spinbox(self.tree, from_=0, to=999, textvariable=var, width=5)
        spin.place(x=x, y=y, width=w, height=h)
        spin.focus_set()
        spin.selection_range(0, tk.END)

        self.spinbox_widget = spin
        self.edit_item = item

        def commit(event=None):
            try:
                new_value = int(var.get())
                if new_value < 0:
                    new_value = 0
            except ValueError:
                new_value = current_value

            row_values = list(self.tree.item(item, "values"))
            row_values[2] = str(new_value)
            self.tree.item(item, values=tuple(row_values))

            self._close_spinbox()
            self._update_totals()

        def cancel(event=None):
            self._close_spinbox()

        spin.bind("<Return>", commit)
        spin.bind("<KP_Enter>", commit)
        spin.bind("<FocusOut>", commit)
        spin.bind("<Escape>", cancel)

    # ============================================================
    # DRAG & DROP
    # ============================================================

    def _on_drag_start(self, event):
        """Start drag and drop."""
        self._close_spinbox()
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            self.drag_source = None
            return
        self.drag_source = self.tree.identify_row(event.y)

    def _on_drag_motion(self, event):
        """Move the dragged row."""
        if not self.drag_source:
            return
        target = self.tree.identify("item", event.x, event.y)
        if target and target != self.drag_source:
            all_items = self.tree.get_children()
            target_index = all_items.index(target)
            self.tree.move(self.drag_source, "", target_index)

    def _on_drag_end(self, event):
        """End drag and drop."""
        self.drag_source = None
        self._renumber_rows()
        self._update_totals()

    def _renumber_rows(self):
        """Renumber rows after movement."""
        for idx, item in enumerate(self.tree.get_children(), start=1):
            values = list(self.tree.item(item, "values"))
            values[0] = str(idx)
            self.tree.item(item, values=tuple(values))

    def _update_totals(self):
        """Update totals display."""
        try:
            cycles = int(self.cycles_var.get())
        except ValueError:
            cycles = 1

        per_cycle = 0
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            per_cycle += int(values[2])

        total = per_cycle * cycles

        if per_cycle == 0:
            self.per_cycle_label.config(text="")
            self.cycles_totals_label.config(text="")
        else:
            self.per_cycle_label.config(text=f"{per_cycle} parts per cycle")
            text = f"{cycles} cycles × {per_cycle} parts per cycle = {total} parts total"
            self.cycles_totals_label.config(text=text)

    # ============================================================
    # SERIES SAVING (serie.csv)
    # ============================================================

    def _current_cycles(self) -> int:
        """Return the cycles value from the spinbox, clamped to >= 1."""
        try:
            cycles = int(self.cycles_var.get())
        except ValueError:
            cycles = 1
        return cycles if cycles >= 1 else 1

    def _collect_serie_items(self) -> list[csv_parser.SerieItem]:
        """Build SerieItem list from the current table content (display order)."""
        items: list[csv_parser.SerieItem] = []
        for rank, row in enumerate(self.tree.get_children(), start=1):
            values = self.tree.item(row, "values")
            filename = str(values[1])
            try:
                occurrences = int(values[2])
            except (ValueError, IndexError):
                occurrences = 0
            items.append(
                csv_parser.SerieItem(
                    rank=rank,
                    filename=filename,
                    occurrences=occurrences,
                )
            )
        return items

    def save_series(self):
        """
        Export the table content (rank, filename, occurrences) to serie.csv.

        - Target folder: the currently selected folder.
        - Creates serie.csv if missing, updates it otherwise.
        - Works even when the table is empty.
        """
        self._close_spinbox()

        # Determine target folder
        if self.selected_folder is not None:
            target_folder = self.selected_folder
        else:
            chosen = filedialog.askdirectory(title="Select folder to save serie.csv")
            if not chosen:
                return
            target_folder = Path(chosen)

        csv_path = target_folder / SERIE_CSV_NAME

        config = csv_parser.SerieConfig(
            cycles=self._current_cycles(),
            items=self._collect_serie_items(),
        )

        try:
            written_path = csv_parser.write_serie_csv(csv_path, config)
        except csv_parser.CSVFormatError as exc:
            messagebox.showerror("Error", f"Series save failed:\n{exc}")
            return
        except OSError as exc:
            messagebox.showerror("Error", f"Series save failed:\n{exc}")
            return

        messagebox.showinfo("Series saved", f"Series saved: {written_path}")
        self.status_label.config(text=f"✓ Series saved: {written_path}")

    # ============================================================
    # G-CODE GENERATION
    # ============================================================

    def generate_gcode(self):
        """Generate the compiled G-code."""
        self._close_spinbox()

        if not self.valid_files:
            messagebox.showerror("Error", "No file selected")
            return

        try:
            cycles = int(self.cycles_var.get())
            if cycles < 1:
                cycles = 1
        except ValueError:
            messagebox.showerror("Error", "Invalid cycles value")
            return

        # Build the plan
        items = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            filename = values[1]
            count = int(values[2])

            if count > 0:
                for f in self.valid_files:
                    if f.name == filename:
                        items.append(PlanItem(f, count))
                        break

        if not items:
            messagebox.showerror("Error", "No parts selected (all occurrences are 0)")
            return

        plan = ExecutionPlan(mode="normal", repetitions=cycles, items=items)

        # Compose the G-code
        try:
            content = sequencer.compose(plan, self.transition_gcode)
        except Exception as exc:
            messagebox.showerror("Error", f"G-code composition failed:\n{str(exc)}")
            return

        # Ask for output path
        target = filedialog.asksaveasfilename(
            title="Save compiled G-code",
            defaultextension=".gcode",
            initialdir=str(self.selected_folder) if self.selected_folder else None,
            initialfile="serie.gcode"
        )
        if not target:
            return

        # Save
        try:
            Path(target).write_text(content, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Error", f"Save failed:\n{str(exc)}")
            return

        # Success feedback
        total_parts = sequencer.count_parts(plan)
        messagebox.showinfo(
            "Success",
            f"G-code generated successfully:\n{Path(target).name}\n\n{total_parts} parts"
        )

        self.plan = plan
        self.output_path = Path(target)
        self.root.quit()

    def cancel(self):
        """Cancel and close."""
        self._close_spinbox()
        self.plan = None
        self.output_path = None
        self.root.quit()


def run_gui():
    """Run the interface and return (plan, output_path)."""
    root = tk.Tk()
    app = SeriesGeneratorUI(root)
    root.mainloop()
    return app.plan, app.output_path