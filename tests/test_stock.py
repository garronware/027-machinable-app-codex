"""Regression checks for deterministic allowance and stock sizing."""

import pytest

from backend.domain.machining import add_machining_allowance
from backend.domain.stock import lookup_stock_size


def test_tool_steel_round_allowance_and_stock_lookup():
    bounding = {
        "Metric_or_Imperial": "IMPERIAL (IN)",
        "Bounding_Cyl": {
            "Dia": 0.378,
            "L": 1.5625,
            "Units": "IMPERIAL (IN)",
            "Shape": "CYLINDER",
        },
    }
    adjusted = add_machining_allowance(bounding, "TOOL_STEEL")
    assert adjusted["Bndng_Plus_Mach_Stock"]["Dia"] == pytest.approx(0.548)
    assert adjusted["Bndng_Plus_Mach_Stock"]["L"] == pytest.approx(1.6875)

    output = lookup_stock_size(adjusted, "A2 Tool Steel")
    assert output["Raw_Matl_Needed"]["Stock_Dia"]
    assert output["Raw_Matl_Needed"]["Cut_L"] == "1.688 in"


def test_missing_dimension_never_selects_stock():
    data = {
        "Metric_or_Imperial": "IMPERIAL (IN)",
        "Bounding_Cyl": {
            "Dia": 1.0,
            "L": 2.0,
            "Units": "IMPERIAL (IN)",
            "Shape": "CYLINDER",
        },
        "Bndng_Plus_Mach_Stock": {
            "Dia": None,
            "L": 2.125,
            "Units": "IMPERIAL (IN)",
            "Shape": "CYLINDER",
            "Lookup_Tbl": "ALLOY_STEEL",
            "Dominant_Machining_Process": "LATHE",
            "Stock_Shape": "ROUND",
            "Stock_Form": "BAR/DISC",
        },
    }
    with pytest.raises(ValueError, match="missing or invalid"):
        lookup_stock_size(data, "4140 Alloy Steel")

