# csv_parser.py — Parse and write serie.csv (Excel format exported to CSV)

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SerieItem:
    rank: int
    filename: str
    occurrences: int


@dataclass
class SerieConfig:
    cycles: int
    items: list[SerieItem]


class CSVFormatError(Exception):
    """Raised when serie.csv format is invalid."""
    pass


def parse_serie_csv(csv_path: Path) -> SerieConfig:
    """
    Parse serie.csv file.
    Row 1: Cycles,<value>,
    Row 2: Rank,Filename,Occurrences
    Row 3+: Data rows
    """
    if not csv_path.exists():
        raise CSVFormatError(f"File not found: {csv_path.name}")

    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            all_rows = list(reader)

        if len(all_rows) < 2:
            raise CSVFormatError(
                "CSV must have at least 2 rows (Cycles header and data header)"
            )

        # Row 1: Extract cycles value
        row1 = all_rows[0]
        if not row1 or row1[0].strip().lower() != "cycles":
            raise CSVFormatError("Row 1: Must start with 'Cycles'")

        cycles_str = None
        if len(row1) >= 2 and row1[1].strip():
            cycles_str = row1[1].strip()
        else:
            raise CSVFormatError("Row 1: Cycles value missing (expected in column 2)")

        try:
            cycles = int(cycles_str)
        except ValueError:
            raise CSVFormatError(f"Row 1: Cycles value '{cycles_str}' is not an integer")

        if cycles < 1:
            raise CSVFormatError("Row 1: Cycles value must be >= 1")

        # Row 2: Data header
        row2 = all_rows[1]
        if len(row2) < 3:
            raise CSVFormatError("Row 2: Must contain 3 columns (Rank, Filename, Occurrences)")

        expected_headers = ["rank", "filename", "occurrences"]
        actual_headers = [c.strip().lower() for c in row2[:3]]
        if actual_headers != expected_headers:
            raise CSVFormatError(
                "Row 2: Headers must be 'Rank,Filename,Occurrences' "
                f"(found: {','.join(row2[:3])})"
            )

        # Row 3+: Data rows
        items: list[SerieItem] = []
        for line_no, row in enumerate(all_rows[2:], start=3):
            # Skip fully empty rows
            if not row or all(not c.strip() for c in row):
                continue

            if len(row) < 3:
                raise CSVFormatError(f"Row {line_no}: Must contain 3 columns")

            rank_str = row[0].strip()
            filename = row[1].strip()
            occurrences_str = row[2].strip()

            if not filename:
                raise CSVFormatError(f"Row {line_no}: Filename is empty")

            try:
                rank = int(rank_str)
            except ValueError:
                raise CSVFormatError(f"Row {line_no}: Rank '{rank_str}' is not an integer")

            try:
                occurrences = int(occurrences_str)
            except ValueError:
                raise CSVFormatError(
                    f"Row {line_no}: Occurrences '{occurrences_str}' is not an integer"
                )

            if rank < 1:
                raise CSVFormatError(f"Row {line_no}: Rank must be >= 1")
            if occurrences < 0:
                raise CSVFormatError(f"Row {line_no}: Occurrences must be >= 0")
            if any(item.rank == rank for item in items):
                raise CSVFormatError(f"Row {line_no}: Rank {rank} is duplicated")

            items.append(SerieItem(rank=rank, filename=filename, occurrences=occurrences))

        # Sort by rank to enforce declared order
        items.sort(key=lambda it: it.rank)

        return SerieConfig(cycles=cycles, items=items)

    except CSVFormatError:
        raise
    except OSError as exc:
        raise CSVFormatError(f"Cannot read {csv_path.name}: {exc}")


def write_serie_csv(csv_path: Path, config: SerieConfig) -> Path:
    """
    Write (create or overwrite) serie.csv using the same layout as parse_serie_csv.

    Row 1: Cycles,<value>,
    Row 2: Rank,Filename,Occurrences
    Row 3+: <rank>,<filename>,<occurrences>

    Returns the absolute path of the written file.
    """
    cycles = config.cycles if config.cycles >= 1 else 1

    try:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Cycles", str(cycles), ""])
            writer.writerow(["Rank", "Filename", "Occurrences"])
            for item in config.items:
                writer.writerow([str(item.rank), item.filename, str(item.occurrences)])
    except OSError as exc:
        raise CSVFormatError(f"Cannot write {csv_path.name}: {exc}")

    return csv_path.resolve()