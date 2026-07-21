"""Deterministic standard-stock lookup ported from the 015 prototype."""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path

INCH_TO_MM = 25.4
DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "stock"
DROP_OPTIONS_FT = [0.5, 1, 3, 6, 8]
EPSILON_IN = 0.0005
BAR_LENGTH_IN = 144.0
SAW_KERF_IN = 0.0625
BAR_END_TRIM_IN = 0.25


def _require_positive_dims(dims: dict[str, object]) -> None:
    for name, value in dims.items():
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(
                f"Bounding dimension {name} is missing or invalid ({value!r}). "
                "Stock cannot be sized safely."
            )


def _bar_yield(required_length_in: float) -> str:
    usable = BAR_LENGTH_IN - BAR_END_TRIM_IN
    if required_length_in > usable:
        return "0 parts - cut length exceeds a 12-ft bar (special order)"
    count = math.floor(usable / (required_length_in + SAW_KERF_IN))
    return (
        f"{count} parts (12-ft bar less 1/16 in kerf per cut and "
        "1/4 in end trim)"
    )


def load_flat_stock(path: Path | None = None) -> list[dict]:
    rows: list[dict] = []
    with (path or DATA_DIR / "flat_stock.csv").open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader)
        for row in reader:
            if len(row) >= 4:
                rows.append(
                    {
                        "t_dec": float(row[0].strip()),
                        "t_frac": row[1].strip(),
                        "w_dec": float(row[2].strip()),
                        "w_frac": row[3].strip(),
                    }
                )
    return rows


def load_round_stock(path: Path | None = None) -> list[dict]:
    rows: list[dict] = []
    with (path or DATA_DIR / "round_stock.csv").open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader)
        for row in reader:
            if len(row) >= 2:
                rows.append(
                    {
                        "d_dec": float(row[0].strip()),
                        "d_frac": row[1].strip(),
                    }
                )
    return rows


def lookup_stock_size(data: dict, material_name: str) -> dict:
    stock = data["Bndng_Plus_Mach_Stock"]
    is_metric = "METRIC" in str(stock.get("Units", "")).upper()
    if stock.get("Stock_Shape") == "FLAT":
        return _lookup_flat(data, stock, is_metric, material_name)
    if stock.get("Stock_Shape") == "ROUND":
        return _lookup_round(data, stock, is_metric, material_name)
    raise ValueError(f"Unknown Stock_Shape: {stock.get('Stock_Shape')!r}")


def _lookup_flat(
    data: dict, stock: dict, is_metric: bool, material_name: str
) -> dict:
    _require_positive_dims({key: stock.get(key) for key in ("Thk", "W", "L")})
    required_thickness = stock["Thk"] / INCH_TO_MM if is_metric else stock["Thk"]
    required_width = stock["W"] / INCH_TO_MM if is_metric else stock["W"]
    required_length = stock["L"] / INCH_TO_MM if is_metric else stock["L"]

    candidates = [
        row
        for row in load_flat_stock()
        if row["t_dec"] + EPSILON_IN >= required_thickness
        and row["w_dec"] + EPSILON_IN >= required_width
    ]
    if not candidates:
        raise ValueError(
            "Part exceeds the flat stock table "
            f"(needs Thk {required_thickness:.3f} in x W {required_width:.3f} in). "
            "Source oversized stock from a supplier."
        )
    candidates.sort(key=lambda row: (row["t_dec"] * row["w_dec"], row["t_dec"]))
    selected = candidates[0]
    description = (
        f"{material_name} Flat Bar/Plate, "
        f"Thk {_clean_fraction(selected['t_frac'])} in"
    )
    return _build_output(
        data,
        stock,
        material_name,
        {
            "Stock_Thk": _format_stock_dimension(
                selected["t_frac"], selected["t_dec"], is_metric
            ),
            "Stock_W": _format_stock_dimension(
                selected["w_frac"], selected["w_dec"], is_metric
            ),
            "Cut_L": _format_cut_length(
                required_length, stock["L"], is_metric
            ),
            "Closest_Drop_L": _format_drop_length(required_length),
            "12-Ft_Bar_Yields": _bar_yield(required_length),
            "Prod_Descr": re.sub(r"\s+", " ", description).strip(),
        },
    )


def _lookup_round(
    data: dict, stock: dict, is_metric: bool, material_name: str
) -> dict:
    _require_positive_dims({key: stock.get(key) for key in ("Dia", "L")})
    required_diameter = stock["Dia"] / INCH_TO_MM if is_metric else stock["Dia"]
    required_length = stock["L"] / INCH_TO_MM if is_metric else stock["L"]

    candidates = [
        row
        for row in load_round_stock()
        if row["d_dec"] + EPSILON_IN >= required_diameter
    ]
    if not candidates:
        raise ValueError(
            f"Part exceeds the round stock table (needs Dia {required_diameter:.3f} in). "
            "Source oversized stock from a supplier."
        )
    candidates.sort(key=lambda row: row["d_dec"])
    selected = candidates[0]
    description = (
        f"{material_name} Round Bar/Disc, "
        f"Dia {_clean_fraction(selected['d_frac'])} in"
    )
    return _build_output(
        data,
        stock,
        material_name,
        {
            "Stock_Dia": _format_stock_dimension(
                selected["d_frac"], selected["d_dec"], is_metric
            ),
            "Cut_L": _format_cut_length(
                required_length, stock["L"], is_metric
            ),
            "Closest_Drop_L": _format_drop_length(required_length),
            "12-Ft_Bar_Yields": _bar_yield(required_length),
            "Prod_Descr": re.sub(r"\s+", " ", description).strip(),
        },
    )


def _build_output(
    data: dict, stock: dict, material_name: str, raw_material_fields: dict
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
            "Stock_Shape": str(stock["Stock_Shape"]).capitalize(),
            "Stock_Form": "/".join(
                part.capitalize() for part in str(stock["Stock_Form"]).split("/")
            ),
            **raw_material_fields,
        },
    }


def _clean_fraction(value: str) -> str:
    if re.search(r"\d\s+\d", value):
        return re.sub(r"\s+", "-", value, count=1)
    return value


def _format_stock_dimension(
    fraction: str, decimal_in: float, is_metric: bool
) -> str:
    result = f"{_clean_fraction(fraction)} in"
    if is_metric:
        result += f" ({round(decimal_in * INCH_TO_MM, 2)} mm)"
    return result


def _format_cut_length(
    required_length_in: float, original_length: float, is_metric: bool
) -> str:
    if is_metric:
        return f"{required_length_in:.3f} in ({round(original_length, 3)} mm)"
    return f"{required_length_in:.3f}".rstrip("0").rstrip(".") + " in"


def _format_drop_length(required_length_in: float) -> str:
    required_feet = required_length_in / 12
    selected = next(
        (option for option in DROP_OPTIONS_FT if option >= required_feet), 12
    )
    return "1/2 ft" if selected == 0.5 else f"{selected} ft"

