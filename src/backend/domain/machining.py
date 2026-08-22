"""Deterministic machining allowance rules ported from the 015 prototype."""

from __future__ import annotations

MILLING_ALLOWANCES_INCH = {
    "ALUMINUM": 0.015,
    "TITANIUM": 0.060,
    "CARBON_STEEL": 0.045,
    "ALLOY_STEEL": 0.045,
    "STAINLESS_STEEL": 0.060,
    "TOOL_STEEL": 0.075,
    "BRASS": 0.020,
    "COPPER": 0.020,
    "POLYMER": 0.010,
    "CERAMIC": 0.020,
    "COMPOSITE": 0.015,
    "CAST_IRON": 0.060,
    "CAST_ALUMINUM": 0.030,
}

TURNING_ALLOWANCES_INCH = {
    "ALUMINUM": 0.020,
    "TITANIUM": 0.070,
    "CARBON_STEEL": 0.050,
    "ALLOY_STEEL": 0.050,
    "STAINLESS_STEEL": 0.070,
    "TOOL_STEEL": 0.085,
    "BRASS": 0.025,
    "COPPER": 0.025,
    "POLYMER": 0.015,
    "CERAMIC": 0.020,
    "COMPOSITE": 0.015,
    "CAST_IRON": 0.070,
    "CAST_ALUMINUM": 0.035,
}

INCH_TO_MM = 25.4
LATHE_FACE_ALLOW_INCH = 0.125
GENERAL_MILLING_ALLOWANCE_INCH = 0.045
GENERAL_TURNING_ALLOWANCE_INCH = 0.050


def _allowance_in_drawing_units(
    allowances: dict[str, float],
    material_classification: str,
    *,
    is_metric: bool,
    process: str,
) -> float:
    classification = material_classification.strip().upper()
    if classification not in allowances:
        raise ValueError(f"No {process} allowance is defined for {classification!r}.")
    allowance = allowances[classification]
    return allowance * INCH_TO_MM if is_metric else allowance


def milling_allowance_in_drawing_units(
    material_classification: str, *, is_metric: bool
) -> float:
    """Return the existing per-side milling allowance in the drawing's units."""

    return _allowance_in_drawing_units(
        MILLING_ALLOWANCES_INCH,
        material_classification,
        is_metric=is_metric,
        process="milling",
    )


def turning_allowance_in_drawing_units(
    material_classification: str, *, is_metric: bool
) -> float:
    """Return the existing radial turning allowance in the drawing's units."""

    return _allowance_in_drawing_units(
        TURNING_ALLOWANCES_INCH,
        material_classification,
        is_metric=is_metric,
        process="turning",
    )


def lathe_face_allowance_in_drawing_units(*, is_metric: bool) -> float:
    """Return the existing total face allowance in the drawing's units."""

    return LATHE_FACE_ALLOW_INCH * INCH_TO_MM if is_metric else LATHE_FACE_ALLOW_INCH


def general_milling_allowance_in_drawing_units(*, is_metric: bool) -> float:
    """Return the one material-independent per-side milling allowance."""

    return (
        GENERAL_MILLING_ALLOWANCE_INCH * INCH_TO_MM
        if is_metric
        else GENERAL_MILLING_ALLOWANCE_INCH
    )


def general_turning_allowance_in_drawing_units(*, is_metric: bool) -> float:
    """Return the one material-independent radial turning allowance."""

    return (
        GENERAL_TURNING_ALLOWANCE_INCH * INCH_TO_MM
        if is_metric
        else GENERAL_TURNING_ALLOWANCE_INCH
    )


def add_general_machining_allowance(data: dict) -> dict:
    """Add one fixed shop allowance without inspecting the material."""

    units = data.get("Metric_or_Imperial", "")
    is_metric = "METRIC" in units.upper()
    result = dict(data)

    if "Bounding_Cube" in data:
        allowance = general_milling_allowance_in_drawing_units(is_metric=is_metric)
        cube = data["Bounding_Cube"]
        length = cube.get("L")
        result["Bndng_Plus_Mach_Stock"] = {
            "Thk": cube["Thk"] + (2 * allowance),
            "W": cube["W"] + (2 * allowance),
            "L": length + (2 * allowance) if isinstance(length, (int, float)) else None,
            "Units": units,
            "Shape": "CUBE",
            "Lookup_Tbl": "GENERAL",
            "Dominant_Machining_Process": "MILL",
            "Stock_Shape": "FLAT",
            "Stock_Form": "BAR/PLATE",
        }
        return result

    if "Bounding_Cyl" in data:
        allowance = general_turning_allowance_in_drawing_units(is_metric=is_metric)
        face_allowance = lathe_face_allowance_in_drawing_units(is_metric=is_metric)
        cylinder = data["Bounding_Cyl"]
        length = cylinder.get("L")
        result["Bndng_Plus_Mach_Stock"] = {
            "Dia": cylinder["Dia"] + (2 * allowance),
            "L": length + face_allowance if isinstance(length, (int, float)) else None,
            "Units": units,
            "Shape": "CYLINDER",
            "Lookup_Tbl": "GENERAL",
            "Dominant_Machining_Process": "LATHE",
            "Stock_Shape": "ROUND",
            "Stock_Form": "BAR/DISC",
        }
        return result

    raise ValueError("No validated bounding volume is available.")


def add_machining_allowance(data: dict, material_classification: str) -> dict:
    """Add per-side stock without using a model for arithmetic."""

    classification = material_classification.strip().upper()
    units = data.get("Metric_or_Imperial", "")
    is_metric = "METRIC" in units.upper()
    result = dict(data)

    if "Bounding_Cube" in data:
        allowance = milling_allowance_in_drawing_units(
            classification,
            is_metric=is_metric,
        )
        cube = data["Bounding_Cube"]
        length = cube.get("L")
        result["Bndng_Plus_Mach_Stock"] = {
            "Thk": cube["Thk"] + (2 * allowance),
            "W": cube["W"] + (2 * allowance),
            "L": length + (2 * allowance) if isinstance(length, (int, float)) else None,
            "Units": units,
            "Shape": "CUBE",
            "Lookup_Tbl": classification,
            "Dominant_Machining_Process": "MILL",
            "Stock_Shape": "FLAT",
            "Stock_Form": "BAR/PLATE",
        }
        return result

    if "Bounding_Cyl" in data:
        allowance = turning_allowance_in_drawing_units(
            classification,
            is_metric=is_metric,
        )
        face_allowance = lathe_face_allowance_in_drawing_units(is_metric=is_metric)
        cylinder = data["Bounding_Cyl"]
        length = cylinder.get("L")
        result["Bndng_Plus_Mach_Stock"] = {
            "Dia": cylinder["Dia"] + (2 * allowance),
            "L": length + face_allowance if isinstance(length, (int, float)) else None,
            "Units": units,
            "Shape": "CYLINDER",
            "Lookup_Tbl": classification,
            "Dominant_Machining_Process": "LATHE",
            "Stock_Shape": "ROUND",
            "Stock_Form": "BAR/DISC",
        }
        return result

    raise ValueError("No validated bounding volume is available.")
