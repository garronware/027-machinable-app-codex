"""Offline field-level arbitration and dependency-gate tests."""

from backend.domain.models import (
    BoundingDimensions,
    DimensionEvidence,
    DimensionSource,
    DrawingInterpretation,
    DrawingStockCallout,
    FieldStatus,
    GeometryInterpretation,
    GeometryReaderResult,
    MaterialClassification,
    PresentationStatus,
    ReaderBatch,
    ReaderResult,
    Shape,
    SpecializedReaderBatch,
    TitleBlockInterpretation,
    TitleBlockReaderResult,
    Units,
)
from backend.domain.pipeline import build_analysis_response


def _dimension(value: float | None) -> DimensionEvidence:
    return DimensionEvidence(
        value=value,
        source=(
            DimensionSource.EXPLICIT_OVERALL if value is not None else DimensionSource.NOT_FOUND
        ),
        dimension_path=None,
        evidence="Explicit overall dimension" if value is not None else None,
        uncertainty=None,
        chain_terms=[],
    )


def _read(
    *,
    length: float = 2.0,
    stock_callout: DrawingStockCallout | None = None,
) -> DrawingInterpretation:
    return DrawingInterpretation(
        part_number="FIELD-001",
        part_name="Field-level test block",
        shape=Shape.FLAT,
        supplier_form_candidate="Flat Bar/Plate",
        material_callout_raw="6061-T6 Aluminum",
        material_callout_evidence=["Title block MATERIAL field"],
        material_classification=MaterialClassification.ALUMINUM,
        bounding=BoundingDimensions(
            units=Units.IN,
            diameter=_dimension(None),
            thickness=_dimension(0.5),
            width=_dimension(1.5),
            length=_dimension(length),
        ),
        projection="THIRD_ANGLE",
        identified_views=["FRONT", "TOP", "RIGHT_SIDE"],
        dimension_claims=[],
        drawing_stock_callout=stock_callout,
        tabulated_dimension_evidence=[],
        warnings=[],
        conflicts=[],
        unsupported_reason=None,
    )


def _batch(sol: DrawingInterpretation, terra: DrawingInterpretation) -> ReaderBatch:
    return ReaderBatch(
        reads=[
            ReaderResult(reader_model="gpt-5.6-sol", interpretation=sol),
            ReaderResult(reader_model="gpt-5.6-terra", interpretation=terra),
        ],
        failures=[],
    )


def test_dimension_disagreement_preserves_material_and_shape():
    response = build_analysis_response(_batch(_read(length=2.0), _read(length=2.125)))

    assert response.presentation_status is PresentationStatus.PARTIAL_SUCCESS
    assert response.material.status is FieldStatus.RESOLVED
    assert response.material.raw_callout == "6061-T6 Aluminum"
    assert response.shape.status is FieldStatus.RESOLVED
    assert response.shape.value == "FLAT"
    assert response.dimensions.length.status is FieldStatus.NEEDS_REVIEW
    assert response.recommendation is not None
    assert response.recommendation.stock_thickness is not None
    assert response.recommendation.stock_width is not None
    assert response.recommendation.cut_length is None
    assert response.blocked_outputs == [
        "cut length",
        "drop length",
        "12-foot bar yield",
    ]


def test_agreement_releases_deterministic_recommendation():
    response = build_analysis_response(_batch(_read(), _read()))

    assert response.presentation_status is PresentationStatus.COMPLETE
    assert response.recommendation is not None
    assert response.recommendation.stock_shape == "Flat"
    assert response.blocked_outputs == []


def test_specialized_read_releases_shape_driven_stock_without_dual_agreement():
    batch = SpecializedReaderBatch(
        title=TitleBlockReaderResult(
            reader_model="gpt-5.6-terra",
            interpretation=TitleBlockInterpretation(
                material_callout_raw="6061-T6 Aluminum",
                material_callout_evidence=["Title block MATERIAL field"],
                material_name="6061-T6 Aluminum",
                material_classification=MaterialClassification.ALUMINUM,
                warnings=[],
            ),
        ),
        geometry=GeometryReaderResult(
            reader_model="gpt-5.6-sol",
            interpretation=GeometryInterpretation(
                shape=Shape.FLAT,
                bounding=BoundingDimensions(
                    units=Units.IN,
                    diameter=_dimension(None),
                    thickness=_dimension(0.5),
                    width=_dimension(1.5),
                    length=_dimension(None),
                ),
                drawing_stock_callout=None,
                projection="THIRD_ANGLE",
                identified_views=["FRONT", "TOP", "RIGHT_SIDE"],
                warnings=[],
                conflicts=[],
                unsupported_reason=None,
            ),
        ),
        failures=[],
    )

    response = build_analysis_response(batch)

    assert response.part_number.status is FieldStatus.MISSING
    assert response.part_name.status is FieldStatus.MISSING
    assert response.material.resolved_identity == "6061-T6 Aluminum"
    assert response.shape.value == "FLAT"
    assert response.recommendation is not None
    assert response.recommendation.dominant_machining_process == "MILL"
    assert response.recommendation.stock_thickness is not None
    assert response.recommendation.stock_width is not None
    assert response.recommendation.cut_length is None


def test_equivalent_dual_unit_note_is_not_user_facing():
    batch = SpecializedReaderBatch(
        title=TitleBlockReaderResult(
            reader_model="gpt-5.6-terra",
            interpretation=TitleBlockInterpretation(
                material_callout_raw="6061-T6 Aluminum",
                material_callout_evidence=["Title block MATERIAL field"],
                material_name="6061-T6 Aluminum",
                material_classification=MaterialClassification.ALUMINUM,
                warnings=[],
            ),
        ),
        geometry=GeometryReaderResult(
            reader_model="gpt-5.6-sol",
            interpretation=GeometryInterpretation(
                shape=Shape.FLAT,
                bounding=BoundingDimensions(
                    units=Units.MM,
                    diameter=_dimension(None),
                    thickness=_dimension(12.7),
                    width=_dimension(184.2),
                    length=_dimension(215.9),
                ),
                drawing_stock_callout=None,
                projection="THIRD_ANGLE",
                identified_views=["FRONT", "EDGE"],
                warnings=[
                    "The dimensions are dual-unit with unbracketed metric values "
                    "and bracketed inch equivalents; unbracketed metric values were "
                    "treated as primary."
                ],
                conflicts=[],
                unsupported_reason=None,
            ),
        ),
        failures=[],
    )

    response = build_analysis_response(batch)

    assert response.warnings == []
    assert all(summary.warnings == [] for summary in response.reader_summaries)


def test_material_identity_normalizes_across_equivalent_callout_wording():
    sol = _read().model_copy(
        update={
            "material_callout_raw": (
                "High-speed tool steel T1-T15 or M1-M62 per ASTM A600, "
                "or A2 alloy tool steel per ASTM A681"
            ),
            "material_callout_evidence": ["General note 2, upper left"],
            "material_classification": MaterialClassification.TOOL_STEEL,
        }
    )
    terra = _read().model_copy(
        update={
            "material_callout_raw": (
                "Tool steel: T1 through T15 or M1 through M62; alternatively A2 to ASTM-A-681"
            ),
            "material_callout_evidence": ["Upper-left material note 2"],
            "material_classification": MaterialClassification.TOOL_STEEL,
        }
    )

    response = build_analysis_response(_batch(sol, terra))

    assert response.material.status is FieldStatus.RESOLVED
    assert response.material.raw_callout is None
    assert response.material.resolved_identity == "A2 Tool Steel"
    assert response.material.canonical_grade == "A2"
    assert response.material.allowance_class is MaterialClassification.TOOL_STEEL
    assert response.recommendation is not None
    assert response.recommendation.material_name == "A2 Tool Steel"
    assert "material identity needs review" not in response.validation_summary


def test_deterministic_grade_mapping_recovers_one_reader_classification_gap():
    terra = _read().model_copy(
        update={
            "material_callout_raw": "Aluminum alloy 6061 T6",
            "material_classification": MaterialClassification.NOT_FOUND,
        }
    )

    response = build_analysis_response(_batch(_read(), terra))

    assert response.material.status is FieldStatus.RESOLVED
    assert response.material.resolved_identity == "6061-T6 Aluminum Alloy"
    assert response.material.allowance_class is MaterialClassification.ALUMINUM
    assert "The machining-allowance material class is unresolved." not in (
        response.material.ambiguities
    )


def test_undersized_drawing_stock_callout_is_displayed_and_flagged():
    sol_callout = DrawingStockCallout(
        raw_callout="STOCK 0.50 X 1.00",
        shape=Shape.FLAT,
        units=Units.IN,
        diameter=None,
        thickness=0.5,
        width=1.0,
        length=None,
        evidence="Sol: stock note",
    )
    terra_callout = sol_callout.model_copy(update={"evidence": "Terra: upper-left stock note"})

    response = build_analysis_response(
        _batch(
            _read(stock_callout=sol_callout),
            _read(stock_callout=terra_callout),
        )
    )

    assert response.presentation_status is PresentationStatus.PARTIAL_SUCCESS
    assert response.recommendation is not None
    assert response.drawing_stock_callout.value is not None
    assert response.drawing_stock_callout.status is FieldStatus.NEEDS_REVIEW
    assert any("smaller" in reason for reason in response.drawing_stock_callout.reasons)
