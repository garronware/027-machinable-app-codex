"""Offline checks for uncertainty handling and deterministic pipeline stages."""

import pytest

from backend.domain.dimensions import DrawingUncertainError
from backend.domain.models import (
    BoundingDimensions,
    DimensionEvidence,
    DimensionSource,
    DrawingInterpretation,
    MaterialClassification,
    Shape,
    Units,
)
from backend.domain.pipeline import build_recommendation


def _dimension(
    value: float | None,
    *,
    source: DimensionSource = DimensionSource.EXPLICIT_OVERALL,
    path: str | None = None,
    uncertainty: str | None = None,
) -> DimensionEvidence:
    return DimensionEvidence(
        value=value,
        source=source if value is not None else DimensionSource.NOT_FOUND,
        dimension_path=path,
        evidence="front/top/right views reconciled" if value is not None else None,
        uncertainty=uncertainty,
    )


def _flat_interpretation() -> DrawingInterpretation:
    return DrawingInterpretation(
        part_number="TEST-001",
        part_name="Test block",
        shape=Shape.FLAT,
        material_name="6061-T6 Aluminum",
        material_classification=MaterialClassification.ALUMINUM,
        projection="THIRD_ANGLE",
        bounding=BoundingDimensions(
            units=Units.IN,
            diameter=_dimension(None),
            thickness=_dimension(0.5),
            width=_dimension(1.5),
            length=_dimension(2.0),
        ),
        warnings=[],
        conflicts=[],
        unsupported_reason=None,
    )


def test_flat_pipeline_preserves_extracted_axes_and_dimensions():
    result = build_recommendation(_flat_interpretation())
    naked = result["Part_Basics"]["Naked_Bounding_Dims"]
    assert naked["Thk"] == 0.5
    assert naked["W"] == 1.5
    assert naked["L"] == 2.0
    assert result["Raw_Matl_Needed"]["Stock_Shape"] == "Flat"
    assert result["_analysis"]["requires_machinist_verification"] is True


def test_chained_dimension_requires_visible_arithmetic_path():
    interpretation = _flat_interpretation()
    interpretation.bounding.length = _dimension(
        2.095,
        source=DimensionSource.CHAINED_DIMENSIONS,
        path=None,
    )
    with pytest.raises(DrawingUncertainError, match="no dimension path"):
        build_recommendation(interpretation)


def test_conflicting_views_stop_before_stock_selection():
    interpretation = _flat_interpretation()
    interpretation.conflicts = [
        "Front view gives 2.000 IN; section view gives 2.125 IN."
    ]
    with pytest.raises(DrawingUncertainError, match="machinist review"):
        build_recommendation(interpretation)


def test_outline_only_dimension_is_not_orderable():
    interpretation = _flat_interpretation()
    interpretation.bounding.width = _dimension(
        1.5, source=DimensionSource.INFERRED_OUTLINE
    )
    with pytest.raises(DrawingUncertainError, match="outline alone"):
        build_recommendation(interpretation)


def test_round_prismatic_cross_section_is_circumscribed_with_path():
    interpretation = DrawingInterpretation(
        part_number="TEST-ROUND",
        part_name="Prismatic turned part",
        shape=Shape.ROUND,
        material_name="7075-T6 Aluminum",
        material_classification=MaterialClassification.ALUMINUM,
        projection="THIRD_ANGLE",
        bounding=BoundingDimensions(
            units=Units.IN,
            diameter=_dimension(None),
            thickness=_dimension(2.03),
            width=_dimension(2.03),
            length=_dimension(9.0),
        ),
        warnings=[],
        conflicts=[],
        unsupported_reason=None,
    )
    result = build_recommendation(interpretation)
    naked = result["Part_Basics"]["Naked_Bounding_Dims"]
    assert naked["Dia"] == pytest.approx(2.8709)
    assert any(
        "sqrt(2.03² + 2.03²)" in warning
        for warning in result["_analysis"]["warnings"]
    )

