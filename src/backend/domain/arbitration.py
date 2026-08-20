"""Field-by-field comparison of independent drawing-reader results."""

from __future__ import annotations

import math
import re
import uuid
from collections.abc import Callable

from backend.domain.models import (
    AnalysisResponse,
    DimensionCandidate,
    DimensionEvidence,
    DimensionFieldResult,
    DimensionFieldResults,
    DimensionSource,
    DrawingInterpretation,
    DrawingStockCalloutCandidate,
    DrawingStockCalloutResult,
    FieldCandidate,
    FieldResult,
    FieldStatus,
    MaterialCandidate,
    MaterialClassification,
    MaterialResult,
    PresentationStatus,
    ReaderBatch,
    ReaderStatus,
    ReaderSummary,
    Shape,
    SpecializedReaderBatch,
    Units,
)

INCH_TO_MM = 25.4
DIMENSION_TOLERANCE_IN = 0.0001
MACHINIST_VERIFICATION = (
    "Verify every dimension, material, and stock recommendation against the "
    "original drawing before material is ordered or cut."
)


def _normalize_text(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return re.sub(r"[^A-Z0-9]+", "", value.upper())


def _field_evidence(interpretation: DrawingInterpretation, field_name: str) -> list[str]:
    if field_name == "material_callout_raw":
        return interpretation.material_callout_evidence
    return []


def _resolve_text_field(
    batch: ReaderBatch,
    getter: Callable[[DrawingInterpretation], str | None],
    *,
    field_name: str,
) -> FieldResult:
    candidates = [
        FieldCandidate(
            reader_model=read.reader_model,
            value=getter(read.interpretation),
            evidence=_field_evidence(read.interpretation, field_name),
            uncertainty=None,
        )
        for read in batch.reads
    ]
    present = [candidate for candidate in candidates if _normalize_text(candidate.value)]
    if not present:
        return FieldResult(
            status=FieldStatus.MISSING,
            value=None,
            candidates=candidates,
            reasons=[f"Neither reader resolved {field_name.replace('_', ' ')}."],
        )
    if len(present) < 2 or batch.failures:
        return FieldResult(
            status=FieldStatus.NEEDS_REVIEW,
            value=None,
            candidates=candidates,
            reasons=[f"Only one reader resolved {field_name.replace('_', ' ')}."],
        )
    normalized = {_normalize_text(candidate.value) for candidate in present}
    if len(normalized) == 1:
        return FieldResult(
            status=FieldStatus.RESOLVED,
            value=present[0].value,
            candidates=candidates,
            reasons=[],
        )
    return FieldResult(
        status=FieldStatus.NEEDS_REVIEW,
        value=None,
        candidates=candidates,
        reasons=[f"Readers disagree on {field_name.replace('_', ' ')}."],
    )


def _resolve_enum_field(
    batch: ReaderBatch,
    getter: Callable[[DrawingInterpretation], Shape | Units],
    *,
    field_name: str,
    unknown: Shape | Units,
) -> FieldResult:
    return _resolve_text_field(
        batch,
        lambda interpretation: (
            None if getter(interpretation) == unknown else getter(interpretation).value
        ),
        field_name=field_name,
    )


def _resolve_material(batch: ReaderBatch) -> MaterialResult:
    candidates = [
        MaterialCandidate(
            reader_model=read.reader_model,
            raw_callout=read.interpretation.material_callout_raw,
            allowance_class=read.interpretation.material_classification,
            evidence=read.interpretation.material_callout_evidence,
        )
        for read in batch.reads
    ]
    raw_values = [
        candidate for candidate in candidates if _normalize_text(candidate.raw_callout) is not None
    ]
    ambiguities: list[str] = []
    if not raw_values:
        status = FieldStatus.MISSING
        accepted_raw = None
        ambiguities.append("Neither reader found an explicit material callout.")
    elif len(raw_values) < 2 or batch.failures:
        status = FieldStatus.NEEDS_REVIEW
        accepted_raw = None
        ambiguities.append("Only one reader found the material callout.")
    elif len({_normalize_text(candidate.raw_callout) for candidate in raw_values}) == 1:
        status = FieldStatus.RESOLVED
        accepted_raw = raw_values[0].raw_callout
    else:
        status = FieldStatus.NEEDS_REVIEW
        accepted_raw = None
        ambiguities.append("Readers disagree on the exact material callout.")

    classes = [candidate.allowance_class for candidate in candidates]
    allowance_class: MaterialClassification | None = None
    class_agreement = (
        len(classes) == 2
        and not batch.failures
        and all(item is not MaterialClassification.NOT_FOUND for item in classes)
        and len(set(classes)) == 1
    )
    if class_agreement:
        allowance_class = classes[0]
    else:
        ambiguities.append("The machining-allowance material class is unresolved.")

    evidence = [item for candidate in candidates for item in candidate.evidence]
    return MaterialResult(
        status=status,
        raw_callout=accepted_raw,
        raw_callout_evidence=evidence,
        canonical_grade=None,
        standard_system=None,
        material_family=(allowance_class.value if allowance_class else None),
        temper_or_condition=None,
        specification=None,
        resolved_identity=accepted_raw,
        supplier_description=accepted_raw,
        supplier_search_terms={},
        allowance_class=allowance_class,
        resolution_basis=(
            "Independent readers agree on the material class."
            if class_agreement and status is not FieldStatus.RESOLVED
            else "Independent readers agree on the drawing callout."
            if status is FieldStatus.RESOLVED
            else None
        ),
        resolution_confidence=(
            "HIGH" if status is FieldStatus.RESOLVED else "MEDIUM" if class_agreement else "UNKNOWN"
        ),
        ambiguities=ambiguities,
        temper_source=None,
        temper_confirmation_required=False,
        sources=[],
        candidates=candidates,
    )


def _dimension_candidate(
    reader_model: str, units: Units, evidence: DimensionEvidence
) -> DimensionCandidate:
    return DimensionCandidate(
        reader_model=reader_model,
        value=evidence.value,
        units=units,
        source=evidence.source,
        dimension_path=evidence.dimension_path,
        evidence=evidence.evidence,
        uncertainty=evidence.uncertainty,
        chain_terms=evidence.chain_terms,
    )


def _candidate_problem(candidate: DimensionCandidate) -> str | None:
    if candidate.value is None or candidate.value <= 0:
        return candidate.uncertainty or "value is missing"
    if candidate.units is Units.UNKNOWN:
        return "units are missing"
    if candidate.source is DimensionSource.NOT_FOUND:
        return "no reliable drawing source"
    if candidate.source is DimensionSource.INFERRED_OUTLINE:
        return "value is inferred from the outline alone"
    if candidate.uncertainty:
        return candidate.uncertainty
    if candidate.source is DimensionSource.CHAINED_DIMENSIONS:
        if not (candidate.dimension_path or "").strip():
            return "chained value has no arithmetic path"
        if not candidate.chain_terms:
            return "chained value has no structured operands"
    return None


def _dimension_in_inches(candidate: DimensionCandidate) -> float:
    assert candidate.value is not None
    return candidate.value / INCH_TO_MM if candidate.units is Units.MM else candidate.value


def _chain_signature(candidate: DimensionCandidate) -> tuple[tuple[float, Units], ...]:
    return tuple((term.value, term.units) for term in candidate.chain_terms)


def _resolve_dimension(batch: ReaderBatch, axis: str) -> DimensionFieldResult:
    candidates = [
        _dimension_candidate(
            read.reader_model,
            read.interpretation.bounding.units,
            getattr(read.interpretation.bounding, axis),
        )
        for read in batch.reads
    ]
    usable = [candidate for candidate in candidates if _candidate_problem(candidate) is None]
    reasons = [
        f"{candidate.reader_model}: {problem}."
        for candidate in candidates
        if (problem := _candidate_problem(candidate)) is not None
    ]
    if not usable:
        status = (
            FieldStatus.NEEDS_REVIEW
            if any(candidate.value is not None for candidate in candidates)
            else FieldStatus.MISSING
        )
        return DimensionFieldResult(
            status=status,
            value=None,
            units=None,
            source=None,
            dimension_path=None,
            candidates=candidates,
            reasons=reasons or [f"Neither reader resolved {axis}."],
        )
    if len(usable) < 2 or batch.failures:
        return DimensionFieldResult(
            status=FieldStatus.NEEDS_REVIEW,
            value=None,
            units=None,
            source=None,
            dimension_path=None,
            candidates=candidates,
            reasons=reasons + [f"Only one reader safely resolved {axis}."],
        )
    if not math.isclose(
        _dimension_in_inches(usable[0]),
        _dimension_in_inches(usable[1]),
        rel_tol=0.0,
        abs_tol=DIMENSION_TOLERANCE_IN,
    ):
        return DimensionFieldResult(
            status=FieldStatus.NEEDS_REVIEW,
            value=None,
            units=None,
            source=None,
            dimension_path=None,
            candidates=candidates,
            reasons=[f"Readers disagree on {axis}."],
        )
    if all(
        candidate.source is DimensionSource.CHAINED_DIMENSIONS for candidate in usable
    ) and _chain_signature(usable[0]) != _chain_signature(usable[1]):
        return DimensionFieldResult(
            status=FieldStatus.NEEDS_REVIEW,
            value=None,
            units=None,
            source=None,
            dimension_path=None,
            candidates=candidates,
            reasons=[f"Readers reached the same {axis} using different chain operands."],
        )
    accepted = usable[0]
    return DimensionFieldResult(
        status=FieldStatus.RESOLVED,
        value=accepted.value,
        units=accepted.units,
        source=accepted.source,
        dimension_path=accepted.dimension_path,
        candidates=candidates,
        reasons=[],
    )


def _resolve_stock_callout(batch: ReaderBatch) -> DrawingStockCalloutResult:
    candidates = [
        DrawingStockCalloutCandidate(
            reader_model=read.reader_model,
            value=read.interpretation.drawing_stock_callout,
        )
        for read in batch.reads
        if read.interpretation.drawing_stock_callout is not None
    ]
    if not candidates:
        return DrawingStockCalloutResult(
            status=FieldStatus.MISSING,
            value=None,
            candidates=[],
            reasons=["No explicit drawing-specified stock size was found."],
        )
    if len(candidates) < 2 or batch.failures:
        return DrawingStockCalloutResult(
            status=FieldStatus.NEEDS_REVIEW,
            value=None,
            candidates=candidates,
            reasons=["Only one reader found an explicit stock-size callout."],
        )
    comparable = {
        (
            _normalize_text(candidate.value.raw_callout),
            candidate.value.shape,
            candidate.value.stock_form,
            candidate.value.units,
            candidate.value.diameter,
            candidate.value.thickness,
            candidate.value.width,
            candidate.value.length,
        )
        for candidate in candidates
    }
    if len(comparable) == 1:
        return DrawingStockCalloutResult(
            status=FieldStatus.RESOLVED,
            value=candidates[0].value,
            candidates=candidates,
            reasons=[],
        )
    return DrawingStockCalloutResult(
        status=FieldStatus.NEEDS_REVIEW,
        value=None,
        candidates=candidates,
        reasons=["Readers disagree on the drawing-specified stock size."],
    )


def arbitrate_reader_batch(batch: ReaderBatch) -> AnalysisResponse:
    """Compare readers without allowing one disputed field to erase another."""

    part_number = _resolve_text_field(
        batch, lambda item: item.part_number, field_name="part_number"
    )
    part_name = _resolve_text_field(batch, lambda item: item.part_name, field_name="part_name")
    units = _resolve_enum_field(
        batch,
        lambda item: item.bounding.units,
        field_name="units",
        unknown=Units.UNKNOWN,
    )
    shape = _resolve_enum_field(
        batch,
        lambda item: item.shape,
        field_name="shape",
        unknown=Shape.UNKNOWN,
    )
    material = _resolve_material(batch)
    dimensions = DimensionFieldResults(
        diameter=_resolve_dimension(batch, "diameter"),
        thickness=_resolve_dimension(batch, "thickness"),
        width=_resolve_dimension(batch, "width"),
        length=_resolve_dimension(batch, "length"),
    )
    stock_callout = _resolve_stock_callout(batch)
    summaries = [
        ReaderSummary(
            reader_model=read.reader_model,
            status=ReaderStatus.SUCCEEDED,
            warnings=read.interpretation.warnings,
            conflicts=read.interpretation.conflicts,
            error=None,
        )
        for read in batch.reads
    ] + [
        ReaderSummary(
            reader_model=failure.reader_model,
            status=ReaderStatus.FAILED,
            warnings=[],
            conflicts=[],
            error=failure.error,
        )
        for failure in batch.failures
    ]
    warnings = [warning for read in batch.reads for warning in read.interpretation.warnings]
    warnings.extend(
        f"{failure.reader_model} reader failed: {failure.error}" for failure in batch.failures
    )
    unsupported = [
        read.interpretation.unsupported_reason
        for read in batch.reads
        if read.interpretation.unsupported_reason
    ]
    if unsupported and len(unsupported) == len(batch.reads) and not batch.failures:
        presentation = PresentationStatus.UNSUPPORTED
    else:
        presentation = PresentationStatus.PARTIAL_SUCCESS

    resolved_count = sum(
        result.status is FieldStatus.RESOLVED
        for result in (part_number, part_name, units, shape, material)
    )
    validation = [f"{resolved_count} top-level drawing fields agreed between readers."]
    if unsupported:
        validation.extend(unsupported)
    return AnalysisResponse(
        analysis_id=str(uuid.uuid4()),
        presentation_status=presentation,
        part_number=part_number,
        part_name=part_name,
        units=units,
        material=material,
        shape=shape,
        dimensions=dimensions,
        drawing_stock_callout=stock_callout,
        recommendation=None,
        blocked_outputs=[],
        reader_summaries=summaries,
        validation_summary=validation,
        warnings=warnings,
        verification_message=MACHINIST_VERIFICATION,
    )


def _focused_text_result(
    value: str | None,
    *,
    reader_model: str,
    evidence: list[str] | None = None,
) -> FieldResult:
    if value and value.strip():
        return FieldResult(
            status=FieldStatus.RESOLVED,
            value=value.strip(),
            candidates=[
                FieldCandidate(
                    reader_model=reader_model,
                    value=value.strip(),
                    evidence=evidence or [],
                    uncertainty=None,
                )
            ],
            reasons=[],
        )
    return FieldResult(
        status=FieldStatus.MISSING,
        value=None,
        candidates=[],
        reasons=[],
    )


def _focused_dimension_result(
    evidence: DimensionEvidence,
    *,
    units: Units,
    reader_model: str,
) -> DimensionFieldResult:
    candidate = _dimension_candidate(reader_model, units, evidence)
    if evidence.value is None:
        return DimensionFieldResult(
            status=FieldStatus.MISSING,
            value=None,
            units=None,
            source=None,
            dimension_path=None,
            candidates=[candidate],
            reasons=[],
        )
    problem = _candidate_problem(candidate)
    if problem:
        return DimensionFieldResult(
            status=FieldStatus.NEEDS_REVIEW,
            value=None,
            units=None,
            source=None,
            dimension_path=None,
            candidates=[candidate],
            reasons=[problem],
        )
    return DimensionFieldResult(
        status=FieldStatus.RESOLVED,
        value=evidence.value,
        units=units,
        source=evidence.source,
        dimension_path=evidence.dimension_path,
        candidates=[candidate],
        reasons=[],
    )


def response_from_specialized_read(batch: SpecializedReaderBatch) -> AnalysisResponse:
    """Combine non-overlapping Terra and Sol duties without agreement gating."""

    part_number = _focused_text_result(None, reader_model="not-requested")
    part_name = _focused_text_result(None, reader_model="not-requested")
    if batch.title is None:
        material = MaterialResult(
            status=FieldStatus.MISSING,
            raw_callout=None,
            raw_callout_evidence=[],
            canonical_grade=None,
            standard_system=None,
            material_family=None,
            temper_or_condition=None,
            specification=None,
            resolved_identity=None,
            supplier_description=None,
            supplier_search_terms={},
            allowance_class=None,
            resolution_basis=None,
            resolution_confidence="UNKNOWN",
            ambiguities=[],
            temper_source=None,
            temper_confirmation_required=False,
            sources=[],
            candidates=[],
        )
    else:
        title = batch.title.interpretation
        material_value = title.material_name or title.material_callout_raw
        material_resolved = bool(
            material_value and title.material_classification is not MaterialClassification.NOT_FOUND
        )
        material = MaterialResult(
            status=FieldStatus.RESOLVED if material_resolved else FieldStatus.MISSING,
            raw_callout=title.material_callout_raw,
            raw_callout_evidence=title.material_callout_evidence,
            canonical_grade=None,
            standard_system=None,
            material_family=(title.material_classification.value if material_resolved else None),
            temper_or_condition=None,
            specification=None,
            resolved_identity=material_value if material_resolved else None,
            supplier_description=material_value if material_resolved else None,
            supplier_search_terms={},
            allowance_class=(title.material_classification if material_resolved else None),
            resolution_basis="Focused Terra material read.",
            resolution_confidence="HIGH" if material_resolved else "UNKNOWN",
            ambiguities=[],
            temper_source=None,
            temper_confirmation_required=False,
            sources=[],
            candidates=[
                MaterialCandidate(
                    reader_model=batch.title.reader_model,
                    raw_callout=title.material_callout_raw,
                    allowance_class=title.material_classification,
                    evidence=title.material_callout_evidence,
                )
            ],
        )

    if batch.geometry is None:
        units = _focused_text_result(None, reader_model="gpt-5.6-sol")
        shape = _focused_text_result(None, reader_model="gpt-5.6-sol")
        missing_dimension = DimensionFieldResult(
            status=FieldStatus.MISSING,
            value=None,
            units=None,
            source=None,
            dimension_path=None,
            candidates=[],
            reasons=[],
        )
        dimensions = DimensionFieldResults(
            diameter=missing_dimension.model_copy(deep=True),
            thickness=missing_dimension.model_copy(deep=True),
            width=missing_dimension.model_copy(deep=True),
            length=missing_dimension.model_copy(deep=True),
        )
        stock_callout = DrawingStockCalloutResult(
            status=FieldStatus.MISSING,
            value=None,
            candidates=[],
            reasons=[],
        )
    else:
        geometry = batch.geometry.interpretation
        units = _focused_text_result(
            (None if geometry.bounding.units is Units.UNKNOWN else geometry.bounding.units.value),
            reader_model=batch.geometry.reader_model,
        )
        shape = _focused_text_result(
            None if geometry.shape is Shape.UNKNOWN else geometry.shape.value,
            reader_model=batch.geometry.reader_model,
        )
        dimensions = DimensionFieldResults(
            diameter=_focused_dimension_result(
                geometry.bounding.diameter,
                units=geometry.bounding.units,
                reader_model=batch.geometry.reader_model,
            ),
            thickness=_focused_dimension_result(
                geometry.bounding.thickness,
                units=geometry.bounding.units,
                reader_model=batch.geometry.reader_model,
            ),
            width=_focused_dimension_result(
                geometry.bounding.width,
                units=geometry.bounding.units,
                reader_model=batch.geometry.reader_model,
            ),
            length=_focused_dimension_result(
                geometry.bounding.length,
                units=geometry.bounding.units,
                reader_model=batch.geometry.reader_model,
            ),
        )
        stock_callout = DrawingStockCalloutResult(
            status=(
                FieldStatus.RESOLVED
                if geometry.drawing_stock_callout is not None
                else FieldStatus.MISSING
            ),
            value=geometry.drawing_stock_callout,
            candidates=(
                [
                    DrawingStockCalloutCandidate(
                        reader_model=batch.geometry.reader_model,
                        value=geometry.drawing_stock_callout,
                    )
                ]
                if geometry.drawing_stock_callout is not None
                else []
            ),
            reasons=[],
        )

    def actionable_warnings(items: list[str]) -> list[str]:
        kept: list[str] = []
        for item in items:
            normalized = item.casefold()
            harmless_dual_units = (
                ("dual-unit" in normalized or "bracketed" in normalized)
                and ("treated as primary" in normalized or "equivalent" in normalized)
                and not any(
                    marker in normalized
                    for marker in ("disagree", "mismatch", "ambiguous", "unclear")
                )
            )
            if not harmless_dual_units:
                kept.append(item)
        return kept

    summaries: list[ReaderSummary] = []
    warnings: list[str] = []
    if batch.title is not None:
        title_warnings = actionable_warnings(batch.title.interpretation.warnings)
        warnings.extend(title_warnings)
        summaries.append(
            ReaderSummary(
                reader_model=batch.title.reader_model,
                status=ReaderStatus.SUCCEEDED,
                warnings=title_warnings,
                conflicts=[],
                error=None,
            )
        )
    if batch.geometry is not None:
        geometry_warnings = actionable_warnings(batch.geometry.interpretation.warnings)
        warnings.extend(geometry_warnings)
        summaries.append(
            ReaderSummary(
                reader_model=batch.geometry.reader_model,
                status=ReaderStatus.SUCCEEDED,
                warnings=geometry_warnings,
                conflicts=batch.geometry.interpretation.conflicts,
                error=None,
            )
        )
    for failure in batch.failures:
        summaries.append(
            ReaderSummary(
                reader_model=failure.reader_model,
                status=ReaderStatus.FAILED,
                warnings=[],
                conflicts=[],
                error=failure.error,
            )
        )

    unsupported_reason = (
        batch.geometry.interpretation.unsupported_reason if batch.geometry is not None else None
    )
    return AnalysisResponse(
        analysis_id=str(uuid.uuid4()),
        presentation_status=(
            PresentationStatus.UNSUPPORTED
            if unsupported_reason
            else PresentationStatus.PARTIAL_SUCCESS
        ),
        part_number=part_number,
        part_name=part_name,
        units=units,
        material=material,
        shape=shape,
        dimensions=dimensions,
        drawing_stock_callout=stock_callout,
        recommendation=None,
        blocked_outputs=[],
        reader_summaries=summaries,
        validation_summary=([unsupported_reason] if unsupported_reason is not None else []),
        warnings=warnings,
        verification_message=MACHINIST_VERIFICATION,
    )
