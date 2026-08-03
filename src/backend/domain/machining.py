"""Deterministic machining allowance rules ported from the 015 prototype."""

from __future__ import annotations

MILLING_ALLOWANCES_INCH = {
    "ALUMINUM": 0.015,
    "TITANIUM": 0.060,
    "MILD_STEEL": 0.045,
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
    "MILD_STEEL": 0.050,
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


def add_machining_allowance(data: dict, material_classification: str) -> dict:
    """Add per-side stock without using a model for arithmetic."""

    classification = material_classification.strip().upper()
    units = data.get("Metric_or_Imperial", "")
    is_metric = "METRIC" in units.upper()
    result = dict(data)

    if "Bounding_Cube" in data:
        if classification not in MILLING_ALLOWANCES_INCH:
            raise ValueError(
                f"No milling allowance is defined for {classification!r}."
            )
        allowance = MILLING_ALLOWANCES_INCH[classification]
        if is_metric:
            allowance *= INCH_TO_MM
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
        if classification not in TURNING_ALLOWANCES_INCH:
            raise ValueError(
                f"No turning allowance is defined for {classification!r}."
            )
        allowance = TURNING_ALLOWANCES_INCH[classification]
        face_allowance = LATHE_FACE_ALLOW_INCH
        if is_metric:
            allowance *= INCH_TO_MM
            face_allowance *= INCH_TO_MM
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
