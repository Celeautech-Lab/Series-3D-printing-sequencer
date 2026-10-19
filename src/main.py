"""
main.py — Entry point.
GUI → tag validation → sequence composition → file export.
"""

from __future__ import annotations

try:
    from .gui import run_gui
except ImportError:  # Supports ``python src/main.py``.
    from gui import run_gui


def main() -> None:
    """Main entry point."""
    plan, output_path = run_gui()

    if plan is None:
        print("No sequence generated (cancelled or empty/invalid folder).")
        return

    print("Generated sequence:")
    print(f"  Mode: {plan.mode}")
    print(f"  Series repetitions: {plan.repetitions}")
    print("  Items (selected order):")
    for item in plan.items:
        print(f"    - {item.path.name} x{item.count}")
    print(f"  Output file: {output_path}")


if __name__ == "__main__":
    main()