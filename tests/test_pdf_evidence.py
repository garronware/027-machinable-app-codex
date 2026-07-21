"""Synthetic, offline checks for deterministic digital-PDF evidence."""

import pymupdf

from backend.domain.models import (
    BoundingDimensions,
    DimensionEvidence,
    DimensionSource,
    DrawingInterpretation,
    FieldStatus,
    MaterialClassification,
    ReaderBatch,
    ReaderResult,
    Shape,
    Units,
)
from backend.domain.pdf_evidence import (
    contains_numeric,
    extract_pdf_evidence,
    find_text,
    render_pdf_page,
)
from backend.domain.pipeline import build_analysis_response


def _pdf(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page(width=612, height=792)
    page.insert_text((72, 72), text)
    payload = document.tobytes()
    document.close()
    return payload


def _dimension(value: float | None) -> DimensionEvidence:
    return DimensionEvidence(
        value=value,
        source=(
            DimensionSource.EXPLICIT_OVERALL
            if value is not None
            else DimensionSource.NOT_FOUND
        ),
        dimension_path=None,
        evidence="Explicit overall dimension" if value is not None else None,
        uncertainty=None,
        chain_terms=[],
    )


def _interpretation() -> DrawingInterpretation:
    return DrawingInterpretation(
        part_number="PDF-001",
        part_name="Evidence block",
        shape=Shape.FLAT,
        supplier_form_candidate="Flat Bar/Plate",
        material_callout_raw="6061-T6",
        material_callout_evidence=["Title block MATERIAL field"],
        material_classification=MaterialClassification.ALUMINUM,
        bounding=BoundingDimensions(
            units=Units.IN,
            diameter=_dimension(None),
            thickness=_dimension(0.5),
            width=_dimension(1.5),
            length=_dimension(2.0),
        ),
        projection="THIRD_ANGLE",
        identified_views=["FRONT", "TOP", "RIGHT_SIDE"],
        dimension_claims=[],
        drawing_stock_callout=None,
        tabulated_dimension_evidence=[],
        warnings=[],
        conflicts=[],
        unsupported_reason=None,
    )


def test_extracts_raw_tokens_coordinates_numbers_and_render():
    pdf_bytes = _pdf("PART PDF-001 MATERIAL 6061-T6 0.610 + 1.485 = 2.095")
    evidence = extract_pdf_evidence(pdf_bytes)

    assert evidence.page_count == 1
    assert evidence.tokens
    assert evidence.tokens[0].page_number == 1
    assert evidence.tokens[0].x1 > evidence.tokens[0].x0
    assert find_text(evidence, "6061-T6") == [1]
    assert contains_numeric(evidence, 0.610)
    assert contains_numeric(evidence, 1.485)
    assert contains_numeric(evidence, 2.095)
    assert render_pdf_page(pdf_bytes, 0, dpi=144).startswith(b"\x89PNG")


def test_missing_pdf_token_downgrades_only_the_affected_dimension():
    evidence = extract_pdf_evidence(
        _pdf("PDF-001 Evidence block 6061-T6 0.500 1.500")
    )
    interpretation = _interpretation()
    batch = ReaderBatch(
        reads=[
            ReaderResult(
                reader_model="gpt-5.6-sol",
                interpretation=interpretation,
            ),
            ReaderResult(
                reader_model="gpt-5.6-terra",
                interpretation=interpretation.model_copy(deep=True),
            ),
        ],
        failures=[],
    )

    response = build_analysis_response(batch, evidence)

    assert response.material.status is FieldStatus.RESOLVED
    assert response.shape.status is FieldStatus.RESOLVED
    assert response.dimensions.thickness.status is FieldStatus.RESOLVED
    assert response.dimensions.width.status is FieldStatus.RESOLVED
    assert response.dimensions.length.status is FieldStatus.NEEDS_REVIEW
    assert response.recommendation is None


def test_material_grade_survives_equivalent_nonverbatim_reader_wording():
    evidence = extract_pdf_evidence(
        _pdf(
            "PDF-001 MATERIAL: A2 PER ASTM A681 TOOL STEEL 0.500 1.500 2.000"
        )
    )
    sol = _interpretation().model_copy(
        update={
            "material_callout_raw": (
                "High speed tool steel T1-T15 or M1-M62 ASTM A600; "
                "A2 alloy tool steel ASTM A681"
            ),
            "material_classification": MaterialClassification.TOOL_STEEL,
        }
    )
    terra = sol.model_copy(
        update={
            "material_callout_raw": (
                "Tool steel ranges T1 through T15 and M1 through M62, "
                "or A2 per ASTM-A-681"
            )
        }
    )
    batch = ReaderBatch(
        reads=[
            ReaderResult(reader_model="gpt-5.6-sol", interpretation=sol),
            ReaderResult(reader_model="gpt-5.6-terra", interpretation=terra),
        ],
        failures=[],
    )

    response = build_analysis_response(batch, evidence)

    assert response.material.status is FieldStatus.RESOLVED
    assert response.material.resolved_identity == "A2 Tool Steel"
    assert response.material.allowance_class is MaterialClassification.TOOL_STEEL
    assert response.recommendation is not None


def test_explicit_title_block_units_resolve_dual_dimension_reader_disagreement():
    evidence = extract_pdf_evidence(
        _pdf(
            "PDF-001 6061-T6 DIMENSIONS ARE IN INCHES "
            "0.500 12.700 1.500 38.100 2.000 50.800"
        )
    )
    inch_read = _interpretation()
    metric_read = inch_read.model_copy(
        update={
            "bounding": inch_read.bounding.model_copy(
                update={
                    "units": Units.MM,
                    "thickness": _dimension(12.7),
                    "width": _dimension(38.1),
                    "length": _dimension(50.8),
                }
            )
        }
    )
    batch = ReaderBatch(
        reads=[
            ReaderResult(reader_model="gpt-5.6-sol", interpretation=metric_read),
            ReaderResult(reader_model="gpt-5.6-terra", interpretation=inch_read),
        ],
        failures=[],
    )

    response = build_analysis_response(batch, evidence)

    assert response.units.status is FieldStatus.RESOLVED
    assert response.units.value == "IN"
    assert response.dimensions.thickness.value == 0.5
    assert response.dimensions.width.value == 1.5
    assert response.dimensions.length.value == 2.0
    assert response.recommendation is not None


def test_pdf_without_searchable_text_does_not_reject_visual_reader_results():
    evidence = extract_pdf_evidence(_pdf(""))
    interpretation = _interpretation()
    batch = ReaderBatch(
        reads=[
            ReaderResult(reader_model="gpt-5.6-sol", interpretation=interpretation),
            ReaderResult(
                reader_model="gpt-5.6-terra",
                interpretation=interpretation.model_copy(deep=True),
            ),
        ],
        failures=[],
    )

    response = build_analysis_response(batch, evidence)

    assert response.part_number.status is FieldStatus.RESOLVED
    assert response.material.status is FieldStatus.RESOLVED
    assert response.recommendation is not None
    assert any("no searchable text layer" in item for item in response.validation_summary)
