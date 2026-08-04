"""Regression checks for deterministic allowance and stock sizing."""

import pytest

from backend.domain.machining import add_machining_allowance
from backend.domain.stock import lookup_stock_size


def _flat_stock_data(
    thickness: float,
    width: float,
    length: float | None = 10.0,
    *,
    units: str = "IMPERIAL (IN)",
    material_class: str = "ALUMINUM",
) -> dict:
    return {
        "Metric_or_Imperial": units,
        "Bounding_Cube": {
            "Thk": thickness,
            "W": width,
            "L": length,
            "Units": units,
            "Shape": "CUBE",
        },
        "Bndng_Plus_Mach_Stock": {
            "Thk": thickness,
            "W": width,
            "L": length,
            "Units": units,
            "Shape": "CUBE",
            "Lookup_Tbl": material_class,
            "Dominant_Machining_Process": "MILL",
            "Stock_Shape": "FLAT",
            "Stock_Form": "BAR/PLATE",
        },
    }


def _round_stock_data(
    diameter: float,
    length: float | None = 10.0,
    *,
    units: str = "IMPERIAL (IN)",
    material_class: str = "ALUMINUM",
) -> dict:
    return {
        "Metric_or_Imperial": units,
        "Bounding_Cyl": {
            "Dia": diameter,
            "L": length,
            "Units": units,
            "Shape": "CYLINDER",
        },
        "Bndng_Plus_Mach_Stock": {
            "Dia": diameter,
            "L": length,
            "Units": units,
            "Shape": "CYLINDER",
            "Lookup_Tbl": material_class,
            "Dominant_Machining_Process": "LATHE",
            "Stock_Shape": "ROUND",
            "Stock_Form": "BAR/DISC",
        },
    }


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


def test_flat_bar_rounds_thickness_then_width_from_approved_pairs():
    output = lookup_stock_size(_flat_stock_data(0.2, 0.6), "6061-T6 Aluminum")
    material = output["Raw_Matl_Needed"]

    assert material["Stock_Form"] == "Bar"
    assert material["Stock_Thk"] == "1/4 in"
    assert material["Stock_W"] == "3/4 in"
    assert material["Stock_Note"] is None


def test_flat_bar_normalizes_smaller_side_as_thickness():
    output = lookup_stock_size(_flat_stock_data(2.0, 0.5), "6061-T6 Aluminum")
    material = output["Raw_Matl_Needed"]

    assert material["Stock_Thk"] == "1/2 in"
    assert material["Stock_W"] == "2 in"


def test_large_thick_section_returns_coarse_custom_flat_bar():
    output = lookup_stock_size(_flat_stock_data(3.2, 5.3), "6061-T6 Aluminum")
    material = output["Raw_Matl_Needed"]

    assert material["Stock_Form"] == "Bar"
    assert material["Stock_Thk"] == "4 in"
    assert material["Stock_W"] == "6 in"
    assert material["Stock_Note"] == ("Custom stock needed — approximately 4 in Thk × 6 in W.")


def test_wide_section_uses_standard_plate_panel():
    output = lookup_stock_size(_flat_stock_data(0.8, 15.0, 30.0), "A36 Carbon Steel")
    material = output["Raw_Matl_Needed"]

    assert material["Stock_Form"] == "Plate"
    assert material["Stock_Thk"] == "1 in"
    assert material["Stock_W"] == "24 in"
    assert material["Stock_L"] == "48 in"
    assert material["Cut_L"] == "30 in"
    assert material["Closest_Drop_L"] == "Not applicable for Plate."
    assert material["12-Ft_Bar_Yields"] == "Not applicable for Plate."
    assert material["Stock_Note"] is None


def test_oversized_plate_returns_coarse_custom_size():
    output = lookup_stock_size(_flat_stock_data(2.1, 50.0, 121.0), "6061-T6 Aluminum")
    material = output["Raw_Matl_Needed"]

    assert material["Stock_Form"] == "Plate"
    assert material["Stock_Thk"] == "2-1/2 in"
    assert material["Stock_W"] == "60 in"
    assert material["Stock_L"] == "132 in"
    assert material["Stock_Note"] == (
        "Custom stock needed — approximately 2-1/2 in Thk × 60 in W × 132 in L."
    )


@pytest.mark.parametrize(
    ("required_diameter", "expected"),
    [(12.1, "14 in"), (20.1, "24 in"), (28.1, "32 in"), (32.1, "33 in")],
)
def test_custom_round_bar_uses_approved_coarse_steps(required_diameter: float, expected: str):
    output = lookup_stock_size(_round_stock_data(required_diameter), "4140 Alloy Steel")
    material = output["Raw_Matl_Needed"]

    assert material["Stock_Dia"] == expected
    assert material["Stock_Note"].startswith("Custom stock needed — approximately")


def test_bar_drop_and_yield_use_new_shop_defaults():
    output = lookup_stock_size(_round_stock_data(1.0, 48.1), "4140 Alloy Steel")
    material = output["Raw_Matl_Needed"]

    assert material["Closest_Drop_L"] == "6 ft"
    assert material["12-Ft_Bar_Yields"] == (
        "2 parts (allows 1/8 in saw kerf for each cut and 1 in starting-end trim)"
    )


def test_length_over_twelve_feet_returns_custom_length_and_no_bar_yield():
    output = lookup_stock_size(_round_stock_data(1.0, 145.0), "4140 Alloy Steel")
    material = output["Raw_Matl_Needed"]

    assert material["Closest_Drop_L"] == "None — custom length required."
    assert material["12-Ft_Bar_Yields"] == ("None — part length is longer than 12 ft.")
    assert "156 in L" in material["Stock_Note"]


def test_metric_display_is_imperial_first_with_one_decimal_metric_values():
    output = lookup_stock_size(
        _flat_stock_data(63.0, 151.0, 315.0, units="METRIC (MM)"),
        "6061-T6 Aluminum",
    )
    material = output["Raw_Matl_Needed"]

    assert material["Stock_Thk"] == "2-1/2 in (63.5 mm)"
    assert material["Stock_W"] == "6 in (152.4 mm)"
    assert material["Cut_L"] == "12.402 in (315.0 mm)"
    assert material["Closest_Drop_L"] == "2 ft (609.6 mm)"
