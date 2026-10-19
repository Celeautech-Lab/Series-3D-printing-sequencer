# sequencer.py — Compose the final G-code from an execution plan.

"""
Rules:
  - Header  = everything before the BODYSTART tag of the FIRST file.
  - Body    = everything strictly between BODYSTART and BODYEND (exclusive of tags).
  - Footer  = everything after the BODYEND tag of the LAST file.
  - The transition block is inserted after every body, including the final body, before BODYEND.
  - Single-material machine: temperatures/speeds come from the first file.
  - BODYSTART and BODYEND tags are added once, surrounding all bodies.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from .validator import BODYEND_TAG, BODYSTART_TAG
except ImportError:  # Supports direct execution from the src directory.
    from validator import BODYEND_TAG, BODYSTART_TAG


@dataclass
class GcodeParts:
    header: list[str]
    body: list[str]
    footer: list[str]


def _find_tag(lines: list[str], tag: str) -> int:
    """Find the line index of a tag."""
    for i, line in enumerate(lines):
        if line.strip() == tag:
            return i
    raise ValueError(f"tag '{tag}' not found")


def split_gcode(path: Path) -> GcodeParts:
    """
    Split a G-code file into header / body / footer.
    
    Header: lines before ; BODYSTART (exclusive)
    Body: lines between ; BODYSTART and ; BODYEND (exclusive of both tags)
    Footer: lines after ; BODYEND (exclusive)
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    start_idx = _find_tag(lines, BODYSTART_TAG)
    end_idx = _find_tag(lines, BODYEND_TAG)

    return GcodeParts(
        header=lines[:start_idx],
        body=lines[start_idx + 1:end_idx],
        footer=lines[end_idx + 1:],
    )


def compose(plan, transition: str) -> str:
    """
    Build the full G-code string from execution plan.

    plan       : ExecutionPlan object (repetitions, items)
    transition : G-code block inserted after every part

    Output structure:
    [header from first file]
    ; BODYSTART
    [body 1]
    [transition]
    [body 2]
    [transition]
    ...
    [body N]
    [transition]
    ; BODYEND
    [footer from last file]
    """
    if not plan.items:
        raise ValueError("empty plan: no items to print")

    # Collect all file paths in print order
    all_files = []
    for _ in range(plan.repetitions):
        for item in plan.items:
            for _ in range(item.count):
                all_files.append(item.path)

    if not all_files:
        raise ValueError("no parts in plan: all occurrence counts are zero")

    transition_lines = transition.splitlines()

    # Parse first and last files for header and footer
    first_parts = split_gcode(all_files[0])
    last_parts = split_gcode(all_files[-1])

    # Cache bodies to avoid re-reading files
    bodies: dict[Path, list[str]] = {}
    for item in plan.items:
        if item.path not in bodies:
            bodies[item.path] = split_gcode(item.path).body

    out: list[str] = []
    
    # Add header from first file
    out.extend(first_parts.header)
    
    # Add BODYSTART tag once
    out.append(BODYSTART_TAG)

    # Add all bodies with transitions between them
    for idx, file_path in enumerate(all_files):
        out.extend(bodies[file_path])
        
        # Insert transition after every body, including the last one.
        out.extend(transition_lines)

    # Add BODYEND tag once
    out.append(BODYEND_TAG)
    
    # Add footer from last file
    out.extend(last_parts.footer)

    return "\n".join(out) + "\n"


def count_parts(plan) -> int:
    """Total number of parts produced by the plan."""
    per_cycle = sum(item.count for item in plan.items)
    return per_cycle * plan.repetitions