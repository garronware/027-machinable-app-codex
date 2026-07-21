"""Validate model-extracted facts and build explicit bounding-volume data."""

from __future__ import annotations

import math

from backend.domain.models import (
    DimensionEvidence,
    DimensionSource,
    DrawingInterpretation,
    MaterialClassification,
    Shape,
    Units,
)


class DrawingUncertainError(ValueError):
    """The drawing lacks safe, orderable facts."""


def _require_dimension(name: str, dimension: DimensionEvidence) -> float:
    if dimension.value is None or dimension.value <= 0:
        detail = dimension.uncertainty or "required value is missing"
        raise DrawingUncertainError(f"{name} cannot be determined safely: {detail}.")
    if dimension.source is DimensionSource.NOT_FOUND:
        raise DrawingUncertainError(f"{name} has no reliable drawing source.")
    if dimension.source is DimensionSource.INFERRED_OUTLINE:
        raise DrawingUncertainError(
            f"{name} is inferred from the outline alone. An explicit or dimensioned "
            "drawing path is required before stock can be sized."
        )
    if (
        dimension.source is DimensionSource.CHAINED_DIMENSIONS
        and not (dimension.dimension_path or "").strip()
    ):
        raise DrawingUncertainError(
            f"{name} was derived from chained dimensions but has no dimension path."
        )
    if dimension.source is DimensionSource.CHAINED_DIMENSIONS and not dimension.chain_terms:
        raise DrawingUncertainError(
            f"{name} was derived from chained dimensions but has no structured operands."
        )
    if dimension.uncertainty:
        raise DrawingUncertainError(f"{name} is uncertain: {dimension.uncertainty}.")
    return float(dimension.value)


def effective_round_diameter(
    interpretation: DrawingInterpretation,
) -> tuple[float, str | None]:
    """Return the containing diameter, including a prismatic cross-section."""

    diameter = interpretation.bounding.diameter
    direct = (
        _require_dimension("Diameter", diameter)
        if diameter.value is not None and diameter.source is not DimensionSource.NOT_FOUND
        else None
    )

    thickness = interpretation.bounding.thickness
    width = interpretation.bounding.width
    has_cross_section = thickness.value is not None and width.value is not None
    if not has_cross_section:
        if direct is None:
            raise DrawingUncertainError(
                "Round part needs a reliable diameter or a complete prismatic cross-section."
            )
        return direct, None

    cross_thickness = _require_dimension("Prismatic cross-section thickness", thickness)
    cross_width = _require_dimension("Prismatic cross-section width", width)
    circumscribed = round(math.hypot(cross_thickness, cross_width), 4)
    path = (
        f"sqrt({cross_thickness:g}² + {cross_width:g}²) = "
        f"{circumscribed:g} {interpretation.bounding.units.value}"
    )
    if direct is None or circumscribed > direct:
        return circumscribed, path
    return direct, None


def interpretation_to_bounding_data(
    interpretation: DrawingInterpretation,
) -> tuple[dict, list[str]]:
    """Convert validated drawing facts to the deterministic pipeline contract."""

    if interpretation.unsupported_reason:
        raise DrawingUncertainError(interpretation.unsupported_reason)
    if interpretation.conflicts:
        raise DrawingUncertainError(
            "Drawing conflicts require machinist review: " + "; ".join(interpretation.conflicts)
        )
    if interpretation.shape is Shape.UNKNOWN:
        raise DrawingUncertainError("Stock shape is ambiguous or missing.")
    if interpretation.bounding.units is Units.UNKNOWN:
        raise DrawingUncertainError("Drawing primary units are ambiguous or missing.")
    if (
        interpretation.material_classification is MaterialClassification.NOT_FOUND
        or not (interpretation.material_callout_raw or "").strip()
    ):
        raise DrawingUncertainError(
            "Material is missing or ambiguous; machining allowance cannot be selected."
        )

    units = "IMPERIAL (IN)" if interpretation.bounding.units is Units.IN else "METRIC (MM)"
    warnings = list(interpretation.warnings)

    if interpretation.shape is Shape.ROUND:
        diameter, derived_path = effective_round_diameter(interpretation)
        length = _require_dimension("Overall length", interpretation.bounding.length)
        data = {
            "Metric_or_Imperial": units,
            "Bounding_Cyl": {
                "Dia": diameter,
                "L": length,
                "Units": units,
                "Shape": "CYLINDER",
            },
        }
        if derived_path:
            warnings.append(
                "Round-stock diameter was deterministically circumscribed from the "
                f"prismatic cross-section: {derived_path}."
            )
        return data, warnings

    thickness = _require_dimension("Overall thickness", interpretation.bounding.thickness)
    width = _require_dimension("Overall width", interpretation.bounding.width)
    length = _require_dimension("Overall length", interpretation.bounding.length)
    return (
        {
            "Metric_or_Imperial": units,
            "Bounding_Cube": {
                "Thk": thickness,
                "W": width,
                "L": length,
                "Units": units,
                "Shape": "CUBE",
            },
        },
        warnings,
    )
