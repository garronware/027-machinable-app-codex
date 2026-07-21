"""The live markdown index is the only dimensional evaluation truth."""

from backend.domain.models import (
    BoundingDimensions,
    DimensionEvidence,
    DimensionSource,
    DrawingInterpretation,
    MaterialClassification,
    Shape,
    Units,
)
from tests.evaluation.print_index import (
    PART_PRINTS_DIR,
    PRINT_INDEX_PATH,
    compare_interpretation,
    load_truth_cases,
    parse_dimension,
    parse_rows,
)


def _dimension(value: float | None) -> DimensionEvidence:
    return DimensionEvidence(
        value=value,
        source=(
            DimensionSource.EXPLICIT_OVERALL
            if value is not None
            else DimensionSource.NOT_FOUND
        ),
        dimension_path=None,
        evidence="test evidence" if value is not None else None,
        uncertainty=None,
    )


def test_every_copied_pdf_is_indexed_and_every_eval_case_exists():
    rows = parse_rows(PRINT_INDEX_PATH.read_text(encoding="utf-8"))
    indexed = {row.filename for row in rows}
    copied = {path.name for path in PART_PRINTS_DIR.glob("*.pdf")}
    assert copied
    assert copied <= indexed

    cases = load_truth_cases()
    assert cases
    for case in cases:
        assert (PART_PRINTS_DIR / case.filename).is_file()


def test_index_dimension_parser_uses_recorded_result_and_primary_units():
    assert parse_dimension("0.610 + 1.485 = 2.095") == 2.095
    assert parse_dimension("1.500/38.1") == 1.5
    assert parse_dimension("") is None


def test_mismatch_is_reported_without_normalizing_model_output():
    case = next(case for case in load_truth_cases() if case.shape is Shape.ROUND)
    interpretation = DrawingInterpretation(
        part_number=case.part_number,
        part_name=None,
        shape=Shape.ROUND,
        material_name="A2 Tool Steel",
        material_classification=MaterialClassification.TOOL_STEEL,
        projection="THIRD_ANGLE",
        bounding=BoundingDimensions(
            units=Units(case.units),
            diameter=_dimension(case.diameter),
            thickness=_dimension(None),
            width=_dimension(None),
            length=_dimension((case.length or 1.0) * 0.5),
        ),
        warnings=[],
        conflicts=[],
        unsupported_reason=None,
    )
    report = compare_interpretation(case, interpretation)
    length = next(
        dimension
        for dimension in report["dimensions"]
        if dimension["axis"] == "length"
    )
    assert length["actual"] == (case.length or 1.0) * 0.5
    assert length["bucket"] == "UNDER"

