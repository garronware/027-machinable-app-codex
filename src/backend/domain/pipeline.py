"""Explicit deterministic stages after the one drawing-interpretation call."""

from __future__ import annotations

from backend.domain.dimensions import interpretation_to_bounding_data
from backend.domain.machining import add_machining_allowance
from backend.domain.models import DrawingInterpretation
from backend.domain.stock import lookup_stock_size

MACHINIST_VERIFICATION = (
    "Verify every dimension, material, and stock recommendation against the "
    "original drawing before material is ordered or cut."
)


def build_recommendation(interpretation: DrawingInterpretation) -> dict:
    """Turn validated extracted facts into a stock recommendation."""

    bounding, warnings = interpretation_to_bounding_data(interpretation)
    adjusted = add_machining_allowance(
        bounding,
        interpretation.material_classification.value,
    )
    result = lookup_stock_size(adjusted, interpretation.material_name or "")
    result["Part_Basics"]["Part_No"] = interpretation.part_number or ""
    result["Part_Basics"]["Part_Name"] = interpretation.part_name or ""
    result["_analysis"] = {
        "drawing_interpretation": interpretation.model_dump(mode="json"),
        "warnings": warnings,
        "requires_machinist_verification": True,
        "verification_message": MACHINIST_VERIFICATION,
    }
    return result

