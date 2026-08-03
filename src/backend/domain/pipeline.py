"""Dependency-aware orchestration after independent drawing reads."""

from __future__ import annotations

from backend.domain.arbitration import (
    MACHINIST_VERIFICATION,
    arbitrate_reader_batch,
    response_from_specialized_read,
)
from backend.domain.dimensions import interpretation_to_bounding_data
from backend.domain.machining import add_machining_allowance
from backend.domain.materials import resolve_material
from backend.domain.models import (
    AnalysisResponse,
    BoundingDimensions,
    DimensionEvidence,
    DimensionFieldResult,
    DimensionSource,
    DrawingInterpretation,
    FieldStatus,
    MaterialClassification,
    PresentationStatus,
    ReaderBatch,
    RecalculationRequest,
    RecalculationResponse,
    Shape,
    SpecializedReaderBatch,
    StockRecommendation,
    Units,
)
from backend.domain.pdf_evidence import PdfEvidence, validate_response_against_pdf
from backend.domain.stock import lookup_stock_size

DEPENDENT_OUTPUTS = [
    "machining allowance",
    "standard stock size",
    "cut length",
    "drop length",
    "12-foot bar yield",
]
INCH_TO_MM = 25.4


def build_recommendation(interpretation: DrawingInterpretation) -> dict:
    """Preserved deterministic shop math for one accepted interpretation."""

    bounding, warnings = interpretation_to_bounding_data(interpretation)
    adjusted = add_machining_allowance(
        bounding,
        interpretation.material_classification.value,
    )
    result = lookup_stock_size(adjusted, interpretation.material_callout_raw or "")
    result["Part_Basics"]["Part_No"] = interpretation.part_number or ""
    result["Part_Basics"]["Part_Name"] = interpretation.part_name or ""
    result["_analysis"] = {
        "drawing_interpretation": interpretation.model_dump(mode="json"),
        "warnings": warnings,
        "requires_machinist_verification": True,
    }
    return result


def _missing_dimension() -> DimensionEvidence:
    return DimensionEvidence(
        value=None,
        source=DimensionSource.NOT_FOUND,
        dimension_path=None,
        evidence=None,
        uncertainty=None,
        chain_terms=[],
    )


def _accepted_dimension(result: DimensionFieldResult) -> DimensionEvidence:
    if result.status is not FieldStatus.RESOLVED or result.value is None:
        return _missing_dimension()
    accepted_candidate = next(
        (
            candidate
            for candidate in result.candidates
            if candidate.value == result.value and candidate.units == result.units
        ),
        None,
    )
    return DimensionEvidence(
        value=result.value,
        source=result.source or DimensionSource.NOT_FOUND,
        dimension_path=result.dimension_path,
        evidence=accepted_candidate.evidence if accepted_candidate else None,
        uncertainty=None,
        chain_terms=accepted_candidate.chain_terms if accepted_candidate else [],
    )


def _required_dimension_results(response: AnalysisResponse) -> list[DimensionFieldResult]:
    if response.shape.value == Shape.ROUND.value:
        cross_section_resolved = all(
            item.status is FieldStatus.RESOLVED
            for item in (response.dimensions.thickness, response.dimensions.width)
        )
        if cross_section_resolved:
            return [
                response.dimensions.thickness,
                response.dimensions.width,
            ]
        return [response.dimensions.diameter]
    return [
        response.dimensions.thickness,
        response.dimensions.width,
    ]


def _blocked_reasons(response: AnalysisResponse) -> list[str]:
    reasons: list[str] = []
    if response.units.status is not FieldStatus.RESOLVED:
        reasons.append("primary units need review")
    if response.shape.status is not FieldStatus.RESOLVED:
        reasons.append("stock shape needs review")
    if response.material.status is not FieldStatus.RESOLVED:
        reasons.append("material identity needs review")
    elif response.material.allowance_class is None:
        reasons.append("machining-allowance material class is unresolved")
    if response.shape.status is FieldStatus.RESOLVED and any(
        result.status is not FieldStatus.RESOLVED
        for result in _required_dimension_results(response)
    ):
        reasons.append("required bounding dimensions need review")
    return reasons


def _accepted_interpretation(response: AnalysisResponse) -> DrawingInterpretation:
    assert response.units.value is not None
    assert response.shape.value is not None
    assert response.material.resolved_identity is not None
    assert response.material.allowance_class is not None
    return DrawingInterpretation(
        part_number=response.part_number.value,
        part_name=response.part_name.value,
        shape=Shape(response.shape.value),
        supplier_form_candidate=None,
        material_callout_raw=response.material.resolved_identity,
        material_callout_evidence=response.material.raw_callout_evidence,
        material_classification=response.material.allowance_class,
        bounding=BoundingDimensions(
            units=Units(response.units.value),
            diameter=_accepted_dimension(response.dimensions.diameter),
            thickness=_accepted_dimension(response.dimensions.thickness),
            width=_accepted_dimension(response.dimensions.width),
            length=_accepted_dimension(response.dimensions.length),
        ),
        projection="UNKNOWN",
        identified_views=[],
        dimension_claims=[],
        drawing_stock_callout=response.drawing_stock_callout.value,
        tabulated_dimension_evidence=[],
        warnings=response.warnings,
        conflicts=[],
        unsupported_reason=None,
    )


def clean_recommendation(raw: dict) -> StockRecommendation:
    basics = raw["Part_Basics"]
    material = raw["Raw_Matl_Needed"]
    return StockRecommendation(
        material_name=material["Matl_Name"],
        stock_shape=material["Stock_Shape"],
        stock_form=material["Stock_Form"],
        supplier_description=material["Prod_Descr"],
        stock_thickness=material.get("Stock_Thk"),
        stock_width=material.get("Stock_W"),
        stock_diameter=material.get("Stock_Dia"),
        cut_length=material.get("Cut_L"),
        closest_drop_length=material.get("Closest_Drop_L"),
        bar_yield=material.get("12-Ft_Bar_Yields"),
        dominant_machining_process=basics["Dominant_Machining_Process"],
        finished_dimensions=basics["Naked_Bounding_Dims"],
        adjusted_dimensions=basics["Naked_Dims_Plus_Machining_Alwnc"],
    )


def _dimension_in_inches(value: float, units: Units) -> float:
    return value / INCH_TO_MM if units is Units.MM else value


def _validate_drawing_stock_containment(response: AnalysisResponse) -> bool:
    callout_result = response.drawing_stock_callout
    recommendation = response.recommendation
    if (
        callout_result.status is not FieldStatus.RESOLVED
        or callout_result.value is None
        or recommendation is None
    ):
        return True
    callout = callout_result.value
    expected_shape = "ROUND" if recommendation.stock_shape.upper() == "ROUND" else "FLAT"
    problems: list[str] = []
    if callout.shape.value != expected_shape:
        problems.append("Drawing-specified stock shape differs from the calculated shape.")

    adjusted = recommendation.adjusted_dimensions
    adjusted_units = Units.MM if "METRIC" in str(adjusted.get("Units", "")) else Units.IN
    comparisons = (
        (("diameter", "Dia"), ("length", "L"))
        if expected_shape == "ROUND"
        else (("thickness", "Thk"), ("width", "W"), ("length", "L"))
    )
    for callout_name, adjusted_name in comparisons:
        callout_value = getattr(callout, callout_name)
        adjusted_value = adjusted.get(adjusted_name)
        if callout_value is None or not isinstance(adjusted_value, (int, float)):
            continue
        if _dimension_in_inches(callout_value, callout.units) + 1e-7 < _dimension_in_inches(
            float(adjusted_value), adjusted_units
        ):
            problems.append(
                f"Drawing-specified {callout_name} is smaller than the calculated minimum."
            )
    if not problems:
        response.validation_summary.append(
            "Drawing-specified stock contains the calculated minimum where comparable."
        )
        return True
    callout_result.status = FieldStatus.NEEDS_REVIEW
    callout_result.reasons.extend(problems)
    response.validation_summary.extend(problems)
    response.warnings.extend(problems)
    return False


def build_analysis_response(
    batch: ReaderBatch | SpecializedReaderBatch,
    pdf_evidence: PdfEvidence | None = None,
) -> AnalysisResponse:
    """Return every determinable shop output without optional-field gating."""

    if isinstance(batch, SpecializedReaderBatch):
        response = response_from_specialized_read(batch)
    else:
        response = arbitrate_reader_batch(batch)
        response.material = resolve_material(response.material, response.shape)
    if pdf_evidence is not None:
        validate_response_against_pdf(response, pdf_evidence)
    if response.presentation_status is PresentationStatus.UNSUPPORTED:
        response.blocked_outputs = DEPENDENT_OUTPUTS.copy()
        return response

    reasons = _blocked_reasons(response)
    if reasons:
        response.blocked_outputs = DEPENDENT_OUTPUTS.copy()
        response.validation_summary.extend(reasons)
        response.presentation_status = PresentationStatus.PARTIAL_SUCCESS
        return response

    try:
        raw = build_recommendation(_accepted_interpretation(response))
    except ValueError as exc:
        response.blocked_outputs = DEPENDENT_OUTPUTS.copy()
        response.validation_summary.append(str(exc))
        response.warnings.append(str(exc))
        response.presentation_status = PresentationStatus.PARTIAL_SUCCESS
        return response

    response.recommendation = clean_recommendation(raw)
    stock_callout_safe = _validate_drawing_stock_containment(response)
    has_cut_outputs = response.recommendation.cut_length is not None
    response.presentation_status = (
        PresentationStatus.COMPLETE
        if stock_callout_safe and has_cut_outputs
        else PresentationStatus.PARTIAL_SUCCESS
    )
    response.blocked_outputs = (
        [] if has_cut_outputs else ["cut length", "drop length", "12-foot bar yield"]
    )
    return response


def _confirmed_dimension(value: float | None) -> DimensionEvidence:
    return DimensionEvidence(
        value=value,
        source=(
            DimensionSource.EXPLICIT_OVERALL
            if value is not None
            else DimensionSource.NOT_FOUND
        ),
        dimension_path=None,
        evidence="User-confirmed value for deterministic recalculation",
        uncertainty=None,
        chain_terms=[],
    )


def recalculate_from_confirmed_facts(
    request: RecalculationRequest,
) -> RecalculationResponse:
    """Rerun only deterministic math using browser-supplied facts."""

    if request.units is Units.UNKNOWN:
        raise ValueError("Primary units must be confirmed before recalculation.")
    if request.shape is Shape.UNKNOWN:
        raise ValueError("Stock shape must be confirmed before recalculation.")
    if request.allowance_class is MaterialClassification.NOT_FOUND:
        raise ValueError("Material class must be confirmed before recalculation.")
    interpretation = DrawingInterpretation(
        part_number=request.part_number,
        part_name=request.part_name,
        shape=request.shape,
        supplier_form_candidate=None,
        material_callout_raw=request.material_callout_raw,
        material_callout_evidence=["User-confirmed for recalculation"],
        material_classification=request.allowance_class,
        bounding=BoundingDimensions(
            units=request.units,
            diameter=_confirmed_dimension(request.dimensions.diameter),
            thickness=_confirmed_dimension(request.dimensions.thickness),
            width=_confirmed_dimension(request.dimensions.width),
            length=_confirmed_dimension(request.dimensions.length),
        ),
        projection="UNKNOWN",
        identified_views=[],
        dimension_claims=[],
        drawing_stock_callout=None,
        tabulated_dimension_evidence=[],
        warnings=[],
        conflicts=[],
        unsupported_reason=None,
    )
    recommendation = clean_recommendation(build_recommendation(interpretation))
    corrected_fields = list(dict.fromkeys(request.corrected_fields))
    return RecalculationResponse(
        analysis_id=request.analysis_id,
        recommendation=recommendation,
        user_corrected_fields=corrected_fields,
        warnings=[
            "Unverified estimate uses browser-supplied values and did not rerun the "
            "drawing readers. Verify every value against the drawing before ordering."
        ],
        verification_message=MACHINIST_VERIFICATION,
    )
