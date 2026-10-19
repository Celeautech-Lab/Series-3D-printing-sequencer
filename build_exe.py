#!/usr/bin/env python3
"""Build the application with PyInstaller on Windows, Linux, or macOS.

Run from the repository root, for example::

    python build_exe.py --asset PrintSeriesGenerator-Linux-x64

The asset name defaults to a platform-appropriate name when ``--asset`` is
omitted.  macOS produces a ``.app`` bundle inside a ``.tar.gz`` archive;
Windows and Linux produce a single executable.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
ENTRY_POINT = SRC / "main.py"
SETTINGS = SRC / "settings.json"
DIST = ROOT / "dist"
BUILD = ROOT / "build"


def default_asset() -> str:
    """Return the default CI asset name for the host platform."""
    if sys.platform == "win32":
        return "PrintSeriesGenerator-Windows-x64.exe"
    if sys.platform == "darwin":
        return "PrintSeriesGenerator-macOS-AppleSilicon"
    return "PrintSeriesGenerator-Linux-x64"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--asset",
        default=default_asset(),
        help="Output asset name (defaults to the current platform).",
    )
    return parser.parse_args()


def remove_previous_builds() -> None:
    """Remove PyInstaller's prior build products before starting."""
    shutil.rmtree(BUILD, ignore_errors=True)
    shutil.rmtree(DIST, ignore_errors=True)


def build(asset: str) -> Path:
    if not ENTRY_POINT.is_file():
        raise FileNotFoundError(f"Missing entry point: {ENTRY_POINT}")
    if not SETTINGS.is_file():
        raise FileNotFoundError(f"Missing settings file: {SETTINGS}")

    is_macos = sys.platform == "darwin"
    output_name = Path(asset).stem if sys.platform == "win32" else asset
    data_separator = os.pathsep  # ';' on Windows, ':' on Unix.
    mode = "--onedir" if is_macos else "--onefile"

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        mode,
        "--windowed",
        "--name",
        output_name,
        "--paths",
        "src",
        "--add-data",
        f"src/settings.json{data_separator}src",
        "src/main.py",
    ]
    subprocess.run(command, cwd=ROOT, check=True)

    if is_macos:
        app_bundle = DIST / f"{output_name}.app"
        archive = DIST / f"{asset}.tar.gz"
        if not app_bundle.is_dir():
            raise FileNotFoundError(f"PyInstaller did not create {app_bundle}")
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(app_bundle, arcname=app_bundle.name)
        return archive

    executable = DIST / output_name
    if sys.platform == "win32" and executable.suffix.lower() != ".exe":
        executable = executable.with_suffix(".exe")
    if not executable.is_file():
        raise FileNotFoundError(f"PyInstaller did not create {executable}")
    return executable


def main() -> int:
    args = parse_args()
    remove_previous_builds()
    try:
        output = build(args.asset)
        print(f"Created {output.relative_to(ROOT)}")
        return 0
    finally:
        # PyInstaller's intermediate directory is not a release artifact.
        shutil.rmtree(BUILD, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
