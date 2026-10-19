"""Persistent storage for the inter-part transition G-code.

A frozen PyInstaller application must not write beside ``__file__``: in a
one-file build that location is a temporary extraction directory.  Frozen
builds therefore read/write ``settings.json`` beside the executable, while
source runs continue to use ``src/settings.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _bundled_settings_candidates() -> list[Path]:
    """Return possible read-only settings locations inside a PyInstaller bundle."""
    meipass = getattr(sys, "_MEIPASS", None)
    if not meipass:
        return []
    root = Path(meipass)
    return [root / "settings.json", root / "src" / "settings.json"]


if getattr(sys, "frozen", False):
    # Persistent location for both --onefile and --onedir builds.
    SETTINGS_FILE = Path(sys.executable).resolve().parent / "settings.json"
    _DEFAULT_SETTINGS_FILES = _bundled_settings_candidates()
else:
    SETTINGS_FILE = Path(__file__).with_name("settings.json")
    _DEFAULT_SETTINGS_FILES = [SETTINGS_FILE]

# Backwards-compatible name used by earlier versions.
SETTINGS_PATH = SETTINGS_FILE

DEFAULT_TRANSITION = """; --- BELT TRANSITION ---
G91
G1 Z15 F600
G90
G28 X Y
MANUAL_STEPPER STEPPER=convoyeur MOVE=400 SPEED=50 STOP_ON_ENDSTOP=1
G28
; --- END BELT TRANSITION ---"""


def _read_settings(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = data.get("transition_gcode") if isinstance(data, dict) else None
    return value if isinstance(value, str) else None


def load_transition() -> str:
    """Return external settings, bundled defaults, or the built-in default."""
    # In a frozen app, an existing file beside the executable always wins.
    paths = [SETTINGS_FILE]
    if getattr(sys, "frozen", False):
        paths.extend(path for path in _DEFAULT_SETTINGS_FILES if path != SETTINGS_FILE)
    for path in paths:
        value = _read_settings(path)
        if value is not None:
            return value
    return DEFAULT_TRANSITION


def save_transition(gcode: str) -> None:
    """Persist transition G-code beside the executable or source module."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps({"transition_gcode": gcode}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def reset_transition() -> str:
    """Restore and persist the default transition G-code."""
    save_transition(DEFAULT_TRANSITION)
    return DEFAULT_TRANSITION
