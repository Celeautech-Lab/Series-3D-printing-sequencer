"""Build standalone Print Series Generator binaries with PyInstaller.

Run from this directory with:  python build_exe.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
name = "PrintSeriesGenerator-Windows-x64" if sys.platform == "win32" else "PrintSeriesGenerator-Linux-x64"
sep = ";" if sys.platform == "win32" else ":"
pyinstaller = shutil.which("pyinstaller") or shutil.which("pyinstaller.exe")
if not pyinstaller:
    raise SystemExit("PyInstaller is not installed. Install it with: python -m pip install pyinstaller")

cmd = [
    pyinstaller, "--noconfirm", "--clean", "--onefile", "--windowed",
    "--name", name, "--paths", str(ROOT / "src"),
    "--add-data", f"{ROOT / 'src' / 'settings.json'}{sep}src",
    str(ROOT / "src" / "main.py"),
]
print("Running:", " ".join(map(str, cmd)))
subprocess.run(cmd, cwd=ROOT, check=True)
print(f"Built: {ROOT / 'dist' / (name + ('.exe' if sys.platform == 'win32' else ''))}")
