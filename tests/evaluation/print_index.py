"""Parse and score against the live authoritative print index."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

from backend.domain.models import DrawingInterpretation, Shape

REPO_ROOT = Path(__file__).resolve().parents[2]
PART_PRINTS_DIR = REPO_ROOT / "part-prints"
PRINT_INDEX_PATH = PART_PRINTS_DIR / "print-index.md"

INCH_TO_MM = 25.4
RELATIVE_TOLERANCE = 0.005
ABSOLUTE_TOLERANCE_IN = 0.005
SHAPE_MAP = {"CYL": Shape.ROUND, "CUBE": Shape.FLAT}


@dataclass(frozen=True)
class IndexRow:
    filename: str
    part_number: str
    section: str
    shape_cell: str
    units_cell: str
    diameter_cell: str
    thickness_cell: str
    width_cell: str
    length_cell: str
    material: str
    notes: str


@dataclass(frozen=True)
class TruthCase:
    filename: str
    part_number: str
    section: str
    shape: Shape
    units: str
    diameter: float | None
    thickness: float | None
    width: float | None
    length: float | None
    material: str
    notes: str


def parse_dimension(cell: str) -> float | None:
    """Read a primary nominal value without creating a second truth source."""

    candidate = cell.strip()
    if not candidate:
        return None
    if "=" in candidate:
        candidate = candidate.rsplit("=", 1)[1]
    if "/" in candidate:
        candidate = candidate.split("/", 1)[0]
    match = re.search(r"\d+(?:\.\d+)?", candidate)
    return float(match.group()) if match else None


def is_excluded(section: str, notes: str) -> bool:
    blob = f"{section} {notes}".upper().replace("-", " ")
    return any(
        marker in blob
        for marker in ("DO NOT PROCESS", "DO NOT USE", "PARKED")
    )


def parse_rows(text: str) -> list[IndexRow]:
    rows: list[IndexRow] = []
    section = ""
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 10:
            continue
        if cells[0] == "File" or set(cells[0]) <= set("-: "):
            continue
        rows.append(
            IndexRow(
                filename=cells[0],
                part_number=cells[1],
                section=section,
                shape_cell=cells[2].upper(),
                units_cell=cells[3].upper().replace(" ", ""),
                diameter_cell=cells[4],
                thickness_cell=cells[5],
                width_cell=cells[6],
                length_cell=cells[7],
                material=cells[8],
                notes=cells[9],
            )
        )
    return rows


def truth_cases(text: str) -> list[TruthCase]:
    cases: list[TruthCase] = []
    for row in parse_rows(text):
        if is_excluded(row.section, row.notes):
            continue
        if row.shape_cell not in SHAPE_MAP:
            continue
        primary_units = row.units_cell.split("+", 1)[0]
        if primary_units not in {"IN", "MM"}:
            continue
        cases.append(
            TruthCase(
                filename=row.filename,
                part_number=row.part_number,
                section=row.section,
                shape=SHAPE_MAP[row.shape_cell],
                units=primary_units,
                diameter=parse_dimension(row.diameter_cell),
                thickness=parse_dimension(row.thickness_cell),
                width=parse_dimension(row.width_cell),
                length=parse_dimension(row.length_cell),
                material=row.material,
                notes=row.notes,
            )
        )
    return cases


def load_truth_cases(path: Path = PRINT_INDEX_PATH) -> list[TruthCase]:
    return truth_cases(path.read_text(encoding="utf-8"))


def _convert(
    value: float | None, source_units: str, target_units: str
) -> float | None:
    if value is None or source_units == target_units:
        return value
    if source_units == "IN" and target_units == "MM":
        return value * INCH_TO_MM
    if source_units == "MM" and target_units == "IN":
        return value / INCH_TO_MM
    return None


def _bucket(
    expected: float | None, actual: float | None, units: str
) -> str:
    if expected is None:
        return "NO_TRUTH"
    if actual is None:
        return "NO_READ"
    absolute = (
        ABSOLUTE_TOLERANCE_IN
        if units == "IN"
        else ABSOLUTE_TOLERANCE_IN * INCH_TO_MM
    )
    tolerance = max(RELATIVE_TOLERANCE * expected, absolute)
    difference = actual - expected
    if abs(difference) <= tolerance:
        return "MATCH"
    return "OVER" if difference > 0 else "UNDER"


def _effective_extracted_diameter(
    interpretation: DrawingInterpretation,
) -> tuple[float | None, str | None]:
    bounding = interpretation.bounding
    diameter = bounding.diameter.value
    if bounding.thickness.value is None or bounding.width.value is None:
        return diameter, bounding.diameter.dimension_path
    circumscribed = round(
        math.hypot(bounding.thickness.value, bounding.width.value), 4
    )
    if diameter is None or circumscribed > diameter:
        return (
            circumscribed,
            f"sqrt({bounding.thickness.value:g}² + "
            f"{bounding.width.value:g}²) = {circumscribed:g} "
            f"{bounding.units.value}",
        )
    return diameter, bounding.diameter.dimension_path


def compare_interpretation(
    case: TruthCase, interpretation: DrawingInterpretation
) -> dict:
    """Report live extraction/index differences without normalizing either."""

    report = {
        "file": case.filename,
        "part_number": case.part_number,
        "expected_shape": case.shape.value,
        "actual_shape": interpretation.shape.value,
        "shape_match": interpretation.shape is case.shape,
        "expected_units": case.units,
        "actual_units": interpretation.bounding.units.value,
        "conflicts": list(interpretation.conflicts),
        "warnings": list(interpretation.warnings),
        "dimensions": [],
    }
    if interpretation.shape is not case.shape:
        return report

    actual_units = interpretation.bounding.units.value
    if case.shape is Shape.ROUND:
        diameter, diameter_path = _effective_extracted_diameter(interpretation)
        dimensions = [
            (
                "diameter",
                case.diameter,
                diameter,
                diameter_path,
                interpretation.bounding.diameter.evidence,
            ),
            (
                "length",
                case.length,
                interpretation.bounding.length.value,
                interpretation.bounding.length.dimension_path,
                interpretation.bounding.length.evidence,
            ),
        ]
    else:
        dimensions = [
            (
                "thickness",
                case.thickness,
                interpretation.bounding.thickness.value,
                interpretation.bounding.thickness.dimension_path,
                interpretation.bounding.thickness.evidence,
            ),
            (
                "width",
                case.width,
                interpretation.bounding.width.value,
                interpretation.bounding.width.dimension_path,
                interpretation.bounding.width.evidence,
            ),
            (
                "length",
                case.length,
                interpretation.bounding.length.value,
                interpretation.bounding.length.dimension_path,
                interpretation.bounding.length.evidence,
            ),
        ]

    for axis, expected, raw_actual, dimension_path, evidence in dimensions:
        actual = _convert(raw_actual, actual_units, case.units)
        report["dimensions"].append(
            {
                "axis": axis,
                "expected": expected,
                "actual": actual,
                "actual_before_unit_conversion": raw_actual,
                "bucket": _bucket(expected, actual, case.units),
                "dimension_path": dimension_path,
                "evidence": evidence,
            }
        )
    return report

