"""Deterministic lookup against a small set of common raw-stock sizes."""

from __future__ import annotations

import json
import math
from fractions import Fraction
from functools import cache
from pathlib import Path

from backend.domain.models import DrawingStockCallout, Shape, StockForm, Units

INCH_TO_MM = 25.4
DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "stock"
COMMON_STOCK_PATH = DATA_DIR / "common_stock.json"
EPSILON_IN = 0.0005


def _positive_number(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"Common stock setting {label!r} must be a positive number.")
    return float(value)


def _positive_list(value: object, label: str) -> list[float]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"Common stock setting {label!r} must be a non-empty list.")
    numbers = [_positive_number(item, label) for item in value]
    if numbers != sorted(set(numbers)):
        raise ValueError(f"Common stock setting {label!r} must be sorted and unique.")
    return numbers


def _validate_common_stock(catalog: object) -> dict:
    if not isinstance(catalog, dict):
        raise ValueError("Common stock data must be a JSON object.")
    required_sections = {
        "supported_material_families",
        "bar_defaults",
        "round_bar",
        "flat_bar",
        "plate",
    }
    missing = required_sections - catalog.keys()
    if missing:
        raise ValueError(f"Common stock data is missing: {', '.join(sorted(missing))}.")

    families = catalog["supported_material_families"]
    if (
        not isinstance(families, list)
        or not families
        or any(not isinstance(item, str) or not item for item in families)
        or len(families) != len(set(families))
    ):
        raise ValueError("Supported material families must be unique names.")

    bar = catalog["bar_defaults"]
    if not isinstance(bar, dict):
        raise ValueError("Bar defaults must be a JSON object.")
    for key in (
        "standard_length_in",
        "saw_kerf_in",
        "starting_end_trim_in",
        "custom_length_step_in",
    ):
        _positive_number(bar.get(key), f"bar_defaults.{key}")
    _positive_list(bar.get("drop_lengths_ft"), "bar_defaults.drop_lengths_ft")

    round_bar = catalog["round_bar"]
    if not isinstance(round_bar, dict):
        raise ValueError("Round-bar settings must be a JSON object.")
    _positive_list(round_bar.get("diameters_in"), "round_bar.diameters_in")
    bands = round_bar.get("custom_diameter_bands")
    if not isinstance(bands, list) or not bands:
        raise ValueError("Round-bar custom diameter bands must be a non-empty list.")
    previous_limit = 0.0
    for index, band in enumerate(bands):
        if not isinstance(band, dict):
            raise ValueError("Each custom diameter band must be a JSON object.")
        _positive_number(band.get("step_in"), f"custom_diameter_bands[{index}].step_in")
        limit = band.get("through_in")
        if limit is None:
            if index != len(bands) - 1:
                raise ValueError("Only the final custom diameter band may be open-ended.")
            continue
        numeric_limit = _positive_number(limit, f"custom_diameter_bands[{index}].through_in")
        if numeric_limit <= previous_limit:
            raise ValueError("Custom diameter band limits must increase.")
        previous_limit = numeric_limit

    flat_bar = catalog["flat_bar"]
    if not isinstance(flat_bar, dict):
        raise ValueError("Flat-bar settings must be a JSON object.")
    _positive_number(
        flat_bar.get("plate_width_to_thickness_ratio"),
        "flat_bar.plate_width_to_thickness_ratio",
    )
    _positive_number(
        flat_bar.get("custom_dimension_step_in"),
        "flat_bar.custom_dimension_step_in",
    )
    rows = flat_bar.get("pairs_in")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Flat-bar pairs must be a non-empty list.")
    prior_thickness = 0.0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError("Each flat-bar pair row must be a JSON object.")
        thickness = _positive_number(
            row.get("thickness_in"), f"flat_bar.pairs_in[{index}].thickness_in"
        )
        widths = _positive_list(row.get("widths_in"), f"flat_bar.pairs_in[{index}].widths_in")
        if thickness <= prior_thickness:
            raise ValueError("Flat-bar thickness rows must increase.")
        if any(width + EPSILON_IN < thickness for width in widths):
            raise ValueError("Flat-bar width cannot be smaller than its thickness.")
        prior_thickness = thickness

    plate = catalog["plate"]
    if not isinstance(plate, dict):
        raise ValueError("Plate settings must be a JSON object.")
    _positive_list(plate.get("thicknesses_in"), "plate.thicknesses_in")
    for key in ("custom_thickness_step_in", "custom_panel_step_in"):
        _positive_number(plate.get(key), f"plate.{key}")
    panels = plate.get("panels_in")
    if not isinstance(panels, list) or not panels:
        raise ValueError("Plate panels must be a non-empty list.")
    prior_area = 0.0
    for index, panel in enumerate(panels):
        if not isinstance(panel, list) or len(panel) != 2:
            raise ValueError("Each plate panel must contain width and length.")
        width = _positive_number(panel[0], f"plate.panels_in[{index}][0]")
        length = _positive_number(panel[1], f"plate.panels_in[{index}][1]")
        if width > length:
            raise ValueError("Plate panel width cannot exceed its length.")
        area = width * length
        if area < prior_area:
            raise ValueError("Plate panels must be ordered from smallest to largest.")
        prior_area = area
    return catalog


@cache
def load_common_stock(path: Path | None = None) -> dict:
    source = path or COMMON_STOCK_PATH
    try:
        catalog = json.loads(source.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Common stock data could not be loaded from {source}: {exc}") from exc
    return _validate_common_stock(catalog)


# Validate the developer-maintained stock data when the backend starts.
COMMON_STOCK = load_common_stock()


def _require_positive_dims(dims: dict[str, object]) -> None:
    for name, value in dims.items():
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(
                f"Bounding dimension {name} is missing or invalid ({value!r}). "
                "Stock cannot be sized safely."
            )


def _round_up(value: float, step: float) -> float:
    return round(math.ceil((value - EPSILON_IN) / step) * step, 6)


def _first_at_least(options: list[float], required: float) -> float | None:
    return next((option for option in options if option + EPSILON_IN >= required), None)


def _mixed_fraction(value: float) -> str:
    fraction = Fraction(value).limit_denominator(64)
    whole, remainder = divmod(fraction.numerator, fraction.denominator)
    if remainder == 0:
        return str(whole)
    if whole:
        return f"{whole}-{remainder}/{fraction.denominator}"
    return f"{remainder}/{fraction.denominator}"


def _decimal(value: float, places: int = 3) -> str:
    return f"{value:.{places}f}".rstrip("0").rstrip(".")


def _format_stock_dimension(decimal_in: float, is_metric: bool) -> str:
    result = f"{_mixed_fraction(decimal_in)} in"
    if is_metric:
        result += f" ({decimal_in * INCH_TO_MM:.1f} mm)"
    return result


def _format_length(decimal_in: float, is_metric: bool) -> str:
    result = f"{_decimal(decimal_in)} in"
    if is_metric:
        result += f" ({decimal_in * INCH_TO_MM:.1f} mm)"
    return result


def _format_cut_length(required_length_in: float, is_metric: bool) -> str:
    return _format_length(required_length_in, is_metric)


def _format_drop_length(required_length_in: float, is_metric: bool, bar: dict) -> str:
    standard_length = float(bar["standard_length_in"])
    standard_feet = _decimal(standard_length / 12)
    if required_length_in > standard_length + EPSILON_IN:
        return "None — custom length required."
    selected = _first_at_least(
        [float(option) for option in bar["drop_lengths_ft"]],
        required_length_in / 12,
    )
    if selected is None:
        return f"None — order a {standard_feet}-ft bar."
    feet = _decimal(selected)
    result = f"{feet} ft"
    if is_metric:
        result += f" ({selected * 12 * INCH_TO_MM:.1f} mm)"
    return result


def _bar_yield(required_length_in: float, bar: dict) -> str:
    standard_length = float(bar["standard_length_in"])
    standard_feet = _decimal(standard_length / 12)
    if required_length_in > standard_length + EPSILON_IN:
        return f"None — part length is longer than {standard_feet} ft."
    end_trim = float(bar["starting_end_trim_in"])
    saw_kerf = float(bar["saw_kerf_in"])
    usable = standard_length - end_trim
    count = math.floor(usable / (required_length_in + saw_kerf))
    noun = "part" if count == 1 else "parts"
    return (
        f"{count} {noun} (allows {_mixed_fraction(saw_kerf)} in saw kerf "
        f"for each cut and {_mixed_fraction(end_trim)} in starting-end trim)"
    )


def _custom_length(required_length_in: float | None, bar: dict) -> float | None:
    if required_length_in is None:
        return None
    if required_length_in <= float(bar["standard_length_in"]) + EPSILON_IN:
        return None
    return _round_up(required_length_in, float(bar["custom_length_step_in"]))


def _availability_note(stock: dict, material_name: str, catalog: dict) -> str | None:
    material_family = str(stock.get("Lookup_Tbl", "")).upper()
    if material_family in catalog["supported_material_families"]:
        return None
    return f"Availability not covered for {material_name}."


def _notes(*values: str | None) -> str | None:
    notes = [value for value in values if value]
    return " ".join(notes) if notes else None


def lookup_stock_size(data: dict, material_name: str, catalog: dict | None = None) -> dict:
    stock = data["Bndng_Plus_Mach_Stock"]
    common_stock = catalog or COMMON_STOCK
    is_metric = "METRIC" in str(stock.get("Units", "")).upper()
    if stock.get("Stock_Shape") == "FLAT":
        return _lookup_flat(data, stock, is_metric, material_name, common_stock)
    if stock.get("Stock_Shape") == "ROUND":
        return _lookup_round(data, stock, is_metric, material_name, common_stock)
    raise ValueError(f"Unknown Stock_Shape: {stock.get('Stock_Shape')!r}")


def _required_length_in(stock: dict, is_metric: bool) -> float | None:
    stock_length = stock.get("L")
    if not isinstance(stock_length, (int, float)) or stock_length <= 0:
        return None
    return stock_length / INCH_TO_MM if is_metric else float(stock_length)


def _bar_length_fields(
    required_length: float | None, is_metric: bool, bar: dict
) -> dict[str, str | None]:
    if required_length is None:
        return {"Cut_L": None, "Closest_Drop_L": None, "12-Ft_Bar_Yields": None}
    return {
        "Cut_L": _format_cut_length(required_length, is_metric),
        "Closest_Drop_L": _format_drop_length(required_length, is_metric, bar),
        "12-Ft_Bar_Yields": _bar_yield(required_length, bar),
    }


def _custom_stock_note(
    *,
    thickness: float | None = None,
    width: float | None = None,
    diameter: float | None = None,
    length: float | None = None,
    is_metric: bool,
) -> str:
    parts: list[str] = []
    if diameter is not None:
        parts.append(f"{_format_stock_dimension(diameter, is_metric)} Dia")
    if thickness is not None:
        parts.append(f"{_format_stock_dimension(thickness, is_metric)} Thk")
    if width is not None:
        parts.append(f"{_format_stock_dimension(width, is_metric)} W")
    if length is not None:
        parts.append(f"{_format_length(length, is_metric)} L")
    return f"Custom stock needed — approximately {' × '.join(parts)}."


def _select_flat_pair(
    required_thickness: float, required_width: float, flat_bar: dict
) -> tuple[float, float] | None:
    for row in flat_bar["pairs_in"]:
        thickness = float(row["thickness_in"])
        if thickness + EPSILON_IN < required_thickness:
            continue
        width = _first_at_least([float(option) for option in row["widths_in"]], required_width)
        if width is not None:
            return thickness, width
    return None


def _select_plate_panel(
    required_width: float, required_length: float, plate: dict
) -> tuple[float, float] | None:
    short_side, long_side = sorted((required_width, required_length))
    candidates = [
        (float(panel[0]), float(panel[1]))
        for panel in plate["panels_in"]
        if float(panel[0]) + EPSILON_IN >= short_side and float(panel[1]) + EPSILON_IN >= long_side
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda panel: (panel[0] * panel[1], panel[0]))


def _lookup_flat(
    data: dict,
    stock: dict,
    is_metric: bool,
    material_name: str,
    catalog: dict,
) -> dict:
    _require_positive_dims({key: stock.get(key) for key in ("Thk", "W")})
    conversion = INCH_TO_MM if is_metric else 1.0
    required_thickness, required_width = sorted(
        (float(stock["Thk"]) / conversion, float(stock["W"]) / conversion)
    )
    required_length = _required_length_in(stock, is_metric)
    bar = catalog["bar_defaults"]
    selected = _select_flat_pair(required_thickness, required_width, catalog["flat_bar"])
    availability_note = _availability_note(stock, material_name, catalog)

    if selected is not None:
        thickness, width = selected
        custom_length = _custom_length(required_length, bar)
        custom_note = (
            _custom_stock_note(
                thickness=thickness,
                width=width,
                length=custom_length,
                is_metric=is_metric,
            )
            if custom_length is not None
            else None
        )
        return _build_output(
            data,
            stock,
            material_name,
            stock_shape="FLAT",
            stock_form="BAR",
            raw_material_fields={
                "Stock_Thk": _format_stock_dimension(thickness, is_metric),
                "Stock_W": _format_stock_dimension(width, is_metric),
                "Stock_L": None,
                **_bar_length_fields(required_length, is_metric, bar),
                "Stock_Note": _notes(custom_note, availability_note),
                "Prod_Descr": f"{material_name} Flat Bar",
            },
        )

    ratio = float(catalog["flat_bar"]["plate_width_to_thickness_ratio"])
    if required_width <= (required_thickness * ratio) + EPSILON_IN:
        step = float(catalog["flat_bar"]["custom_dimension_step_in"])
        thickness = _round_up(required_thickness, step)
        width = _round_up(required_width, step)
        custom_length = _custom_length(required_length, bar)
        return _build_output(
            data,
            stock,
            material_name,
            stock_shape="FLAT",
            stock_form="BAR",
            raw_material_fields={
                "Stock_Thk": _format_stock_dimension(thickness, is_metric),
                "Stock_W": _format_stock_dimension(width, is_metric),
                "Stock_L": None,
                **_bar_length_fields(required_length, is_metric, bar),
                "Stock_Note": _notes(
                    _custom_stock_note(
                        thickness=thickness,
                        width=width,
                        length=custom_length,
                        is_metric=is_metric,
                    ),
                    availability_note,
                ),
                "Prod_Descr": f"{material_name} Flat Bar",
            },
        )

    return _lookup_plate(
        data,
        stock,
        is_metric,
        material_name,
        catalog,
        required_thickness,
        required_width,
        required_length,
        availability_note,
    )


def _lookup_plate(
    data: dict,
    stock: dict,
    is_metric: bool,
    material_name: str,
    catalog: dict,
    required_thickness: float,
    required_width: float,
    required_length: float | None,
    availability_note: str | None,
) -> dict:
    plate = catalog["plate"]
    thickness = _first_at_least(
        [float(option) for option in plate["thicknesses_in"]], required_thickness
    )
    custom_thickness = thickness is None
    if thickness is None:
        thickness = _round_up(required_thickness, float(plate["custom_thickness_step_in"]))

    selected_panel = (
        _select_plate_panel(required_width, required_length, plate)
        if required_length is not None
        else None
    )
    custom_panel = required_length is not None and selected_panel is None
    if selected_panel is not None:
        panel_width, panel_length = selected_panel
    elif required_length is not None:
        short_side, long_side = sorted((required_width, required_length))
        panel_step = float(plate["custom_panel_step_in"])
        panel_width = _round_up(short_side, panel_step)
        panel_length = _round_up(long_side, panel_step)
    else:
        panel_width = None
        panel_length = None

    is_custom = custom_thickness or custom_panel
    custom_note = (
        _custom_stock_note(
            thickness=thickness,
            width=panel_width,
            length=panel_length,
            is_metric=is_metric,
        )
        if is_custom
        else None
    )
    return _build_output(
        data,
        stock,
        material_name,
        stock_shape="FLAT",
        stock_form="PLATE",
        raw_material_fields={
            "Stock_Thk": _format_stock_dimension(thickness, is_metric),
            "Stock_W": (
                _format_stock_dimension(panel_width, is_metric) if panel_width is not None else None
            ),
            "Stock_L": (
                _format_length(panel_length, is_metric) if panel_length is not None else None
            ),
            "Cut_L": (
                _format_cut_length(required_length, is_metric)
                if required_length is not None
                else None
            ),
            "Closest_Drop_L": "Not applicable for Plate.",
            "12-Ft_Bar_Yields": "Not applicable for Plate.",
            "Stock_Note": _notes(custom_note, availability_note),
            "Prod_Descr": f"{material_name} Plate",
        },
    )


def _custom_round_diameter(required_diameter: float, round_bar: dict) -> float:
    for band in round_bar["custom_diameter_bands"]:
        limit = band["through_in"]
        if limit is None or required_diameter <= float(limit) + EPSILON_IN:
            return _round_up(required_diameter, float(band["step_in"]))
    raise ValueError("Round-bar custom diameter bands are incomplete.")


def _lookup_round(
    data: dict,
    stock: dict,
    is_metric: bool,
    material_name: str,
    catalog: dict,
) -> dict:
    _require_positive_dims({"Dia": stock.get("Dia")})
    required_diameter = float(stock["Dia"]) / INCH_TO_MM if is_metric else float(stock["Dia"])
    required_length = _required_length_in(stock, is_metric)
    round_bar = catalog["round_bar"]
    diameter = _first_at_least(
        [float(option) for option in round_bar["diameters_in"]], required_diameter
    )
    custom_diameter = diameter is None
    if diameter is None:
        diameter = _custom_round_diameter(required_diameter, round_bar)
    bar = catalog["bar_defaults"]
    custom_length = _custom_length(required_length, bar)
    custom_note = (
        _custom_stock_note(
            diameter=diameter,
            length=custom_length,
            is_metric=is_metric,
        )
        if custom_diameter or custom_length is not None
        else None
    )
    availability_note = _availability_note(stock, material_name, catalog)
    return _build_output(
        data,
        stock,
        material_name,
        stock_shape="ROUND",
        stock_form="BAR",
        raw_material_fields={
            "Stock_Dia": _format_stock_dimension(diameter, is_metric),
            "Stock_L": None,
            **_bar_length_fields(required_length, is_metric, bar),
            "Stock_Note": _notes(custom_note, availability_note),
            "Prod_Descr": f"{material_name} Round Bar",
        },
    )


def _build_output(
    data: dict,
    stock: dict,
    material_name: str,
    *,
    stock_shape: str,
    stock_form: str,
    raw_material_fields: dict,
) -> dict:
    shape_key = "Bounding_Cube" if "Bounding_Cube" in data else "Bounding_Cyl"
    adjusted_keys = {"Thk", "W", "L", "Dia", "Units", "Shape", "Lookup_Tbl"}
    adjusted = {key: value for key, value in stock.items() if key in adjusted_keys}
    return {
        "Part_Basics": {
            "Dominant_Machining_Process": stock["Dominant_Machining_Process"],
            "Naked_Bounding_Dims": data[shape_key],
            "Naked_Dims_Plus_Machining_Alwnc": adjusted,
        },
        "Raw_Matl_Needed": {
            "Matl_Name": material_name,
            "Stock_Shape": stock_shape.capitalize(),
            "Stock_Form": stock_form.capitalize(),
            **raw_material_fields,
        },
    }


def recommendation_from_drawing_stock(
    callout: DrawingStockCallout,
    *,
    material_name: str,
    finished_dimensions: dict[str, float | str | None],
    adjusted_dimensions: dict[str, float | str | None],
    dominant_machining_process: str,
    catalog: dict | None = None,
) -> dict:
    """Build the normal output fields from a validated drawing stock callout."""

    common_stock = catalog or COMMON_STOCK
    is_metric = callout.units is Units.MM
    conversion = INCH_TO_MM if is_metric else 1.0

    def stock_dimension(value: float | None) -> str | None:
        return (
            _format_stock_dimension(float(value) / conversion, is_metric)
            if value is not None
            else None
        )

    def stock_length(value: float | None) -> str | None:
        return _format_length(float(value) / conversion, is_metric) if value is not None else None

    adjusted_length = _required_length_in(adjusted_dimensions, is_metric)
    if callout.stock_form is StockForm.BAR:
        length_fields = _bar_length_fields(
            adjusted_length,
            is_metric,
            common_stock["bar_defaults"],
        )
    else:
        form_name = callout.stock_form.value.capitalize()
        length_fields = {
            "Cut_L": (
                _format_cut_length(adjusted_length, is_metric)
                if adjusted_length is not None
                else None
            ),
            "Closest_Drop_L": f"Not applicable for {form_name}.",
            "12-Ft_Bar_Yields": f"Not applicable for {form_name}.",
        }

    stock_form = callout.stock_form.value.capitalize()
    description_form = (
        "Round Bar"
        if callout.shape is Shape.ROUND and callout.stock_form is StockForm.BAR
        else "Flat Bar"
        if callout.shape is Shape.FLAT and callout.stock_form is StockForm.BAR
        else stock_form
    )
    return {
        "Part_Basics": {
            "Dominant_Machining_Process": dominant_machining_process,
            "Naked_Bounding_Dims": finished_dimensions,
            "Naked_Dims_Plus_Machining_Alwnc": adjusted_dimensions,
        },
        "Raw_Matl_Needed": {
            "Matl_Name": material_name,
            "Stock_Shape": callout.shape.value.capitalize(),
            "Stock_Form": stock_form,
            "Stock_Thk": stock_dimension(callout.thickness),
            "Stock_W": stock_dimension(callout.width),
            "Stock_L": stock_length(callout.length),
            "Stock_Dia": stock_dimension(callout.diameter),
            **length_fields,
            "Stock_Note": "Stock size is specified on the drawing.",
            "Prod_Descr": f"{material_name} {description_form}".strip(),
        },
    }
