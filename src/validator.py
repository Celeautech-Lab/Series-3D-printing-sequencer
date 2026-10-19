"""
validator.py — Check for BODYSTART/BODYEND tags presence
in G-code files before sequence composition.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

BODYSTART_TAG = "; BODYSTART"
BODYEND_TAG = "; BODYEND"

@dataclass
class TagIssue:
    path: Path
    reason: str

def _positions(lines: list[str], tag: str) -> list[int]:
    """Find line indices where tag appears."""
    return [i for i, line in enumerate(lines) if line.strip() == tag]

def check_file(path: Path) -> TagIssue | None:
    """
    Validate single file for required tags.
    Returns TagIssue if invalid, None otherwise.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return TagIssue(path, f"read failed ({exc})")

    lines = text.splitlines()
    starts = _positions(lines, BODYSTART_TAG)
    ends = _positions(lines, BODYEND_TAG)

    if not starts and not ends:
        return TagIssue(path, "BODYSTART and BODYEND tags missing")
    if not starts:
        return TagIssue(path, "BODYSTART tag missing")
    if not ends:
        return TagIssue(path, "BODYEND tag missing")
    if len(starts) > 1:
        return TagIssue(path, "BODYSTART tag duplicated")
    if len(ends) > 1:
        return TagIssue(path, "BODYEND tag duplicated")
    if starts[0] > ends[0]:
        return TagIssue(path, "tag order reversed (BODYEND before BODYSTART)")
    if ends[0] == starts[0] + 1:
        return TagIssue(path, "empty body between BODYSTART and BODYEND")

    return None

def check_files(paths: list[Path]) -> list[TagIssue]:
    """
    Validate list of files.
    Returns list of files with errors only.
    """
    issues: list[TagIssue] = []
    for path in paths:
        issue = check_file(path)
        if issue is not None:
            issues.append(issue)
    return issues