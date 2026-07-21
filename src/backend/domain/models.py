"""Typed contracts for drawing readers, arbitration, and API responses."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class Shape(StrEnum):
    ROUND = "ROUND"
    FLAT = "FLAT"
    UNKNOWN = "UNKNOWN"


class Units(StrEnum):
    IN = "IN"
    MM = "MM"
    UNKNOWN = "UNKNOWN"


class MaterialClassification(StrEnum):
    ALUMINUM = "ALUMINUM"
    TITANIUM = "TITANIUM"
    MILD_STEEL = "MILD_STEEL"
    ALLOY_STEEL = "ALLOY_STEEL"
    STAINLESS_STEEL = "STAINLESS_STEEL"
    TOOL_STEEL = "TOOL_STEEL"
    BRASS = "BRASS"
    COPPER = "COPPER"
    POLYMER = "POLYMER"
    CERAMIC = "CERAMIC"
    COMPOSITE = "COMPOSITE"
    CAST_IRON = "CAST_IRON"
    CAST_ALUMINUM = "CAST_ALUMINUM"
    NOT_FOUND = "NOT_FOUND"


class DimensionAxis(StrEnum):
    DIAMETER = "DIAMETER"
    THICKNESS = "THICKNESS"
    WIDTH = "WIDTH"
    LENGTH = "LENGTH"


class DimensionSource(StrEnum):
    EXPLICIT_OVERALL = "EXPLICIT_OVERALL"
    EXPLICIT_OUTERMOST_FEATURE = "EXPLICIT_OUTERMOST_FEATURE"
    RECONCILED_ACROSS_VIEWS = "RECONCILED_ACROSS_VIEWS"
    CHAINED_DIMENSIONS = "CHAINED_DIMENSIONS"
    INFERRED_OUTLINE = "INFERRED_OUTLINE"
    NOT_FOUND = "NOT_FOUND"


class FieldStatus(StrEnum):
    RESOLVED = "RESOLVED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    MISSING = "MISSING"
    UNSUPPORTED = "UNSUPPORTED"


class PresentationStatus(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    UNSUPPORTED = "UNSUPPORTED"


class ReaderStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class ChainTerm(BaseModel):
    """One visible operand in a derived overall dimension."""

    model_config = ConfigDict(extra="forbid")

    raw_text: str
    value: float
    units: Units
    evidence: str


class DimensionEvidence(BaseModel):
    """One proposed bounding dimension and its drawing evidence."""

    model_config = ConfigDict(extra="forbid")

    value: float | None = Field(
        description="Nominal dimension in bounding.units, or null when not reliably known."
    )
    source: DimensionSource
    dimension_path: str | None = Field(
        description=(
            "For CHAINED_DIMENSIONS, the complete same-axis arithmetic path, including "
            "segments, result, and units. Otherwise null unless a concise path helps."
        )
    )
    evidence: str | None = Field(
        description="View, note, title-block field, or callout that supports the value."
    )
    uncertainty: str | None = Field(
        description="Conflict or ambiguity affecting this dimension, otherwise null."
    )
    chain_terms: list[ChainTerm] = Field(
        description="Numeric operands for a chained dimension; empty for direct dimensions."
    )


class DimensionClaim(BaseModel):
    """A compact auditable dimension claim made by one reader."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str
    axis: DimensionAxis
    value: float | None
    units: Units
    source: DimensionSource
    view: str | None
    evidence: str | None
    uncertainty: str | None
    chain_terms: list[ChainTerm]
    arithmetic: str | None


class BoundingDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    units: Units
    diameter: DimensionEvidence
    thickness: DimensionEvidence
    width: DimensionEvidence
    length: DimensionEvidence


class DrawingStockCallout(BaseModel):
    """Stock size explicitly specified by the drawing, not a calculated envelope."""

    model_config = ConfigDict(extra="forbid")

    raw_callout: str
    shape: Shape
    units: Units
    diameter: float | None
    thickness: float | None
    width: float | None
    length: float | None
    evidence: str


class TabulatedDimensionEvidence(BaseModel):
    """How a reader selected and interpreted one tabulated-drawing row."""

    model_config = ConfigDict(extra="forbid")

    selector_type: Literal["PART_NUMBER", "ITEM_NUMBER", "SIZE_CODE", "DASH_NUMBER", "OTHER"]
    selector: str
    key_column_header: str
    selected_row: str
    letter_value_mappings: list[str]
    evidence: str


class DrawingInterpretation(BaseModel):
    """Shared structured output produced independently by each drawing reader."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    part_number: str | None
    part_name: str | None
    shape: Shape
    supplier_form_candidate: str | None
    material_callout_raw: str | None = Field(
        validation_alias=AliasChoices("material_callout_raw", "material_name")
    )
    material_callout_evidence: list[str]
    material_classification: MaterialClassification
    bounding: BoundingDimensions
    projection: Literal["THIRD_ANGLE", "FIRST_ANGLE", "OTHER", "UNKNOWN"]
    identified_views: list[str]
    dimension_claims: list[DimensionClaim]
    drawing_stock_callout: DrawingStockCallout | None
    tabulated_dimension_evidence: list[TabulatedDimensionEvidence]
    warnings: list[str]
    conflicts: list[str]
    unsupported_reason: str | None


class ReaderResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reader_model: str
    interpretation: DrawingInterpretation


class ReaderFailure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reader_model: str
    error: str


class ReaderBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reads: list[ReaderResult]
    failures: list[ReaderFailure]


class FieldCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reader_model: str
    value: str | None
    evidence: list[str]
    uncertainty: str | None


class FieldResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: FieldStatus
    value: str | None
    candidates: list[FieldCandidate]
    reasons: list[str]
    user_corrected: bool = False


class MaterialCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reader_model: str
    raw_callout: str | None
    allowance_class: MaterialClassification
    evidence: list[str]


class MaterialResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: FieldStatus
    raw_callout: str | None
    raw_callout_evidence: list[str]
    canonical_grade: str | None
    standard_system: str | None
    material_family: str | None
    temper_or_condition: str | None
    specification: str | None
    resolved_identity: str | None
    supplier_description: str | None
    supplier_search_terms: dict[str, str]
    allowance_class: MaterialClassification | None
    resolution_basis: str | None
    resolution_confidence: Literal["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    ambiguities: list[str]
    temper_source: str | None
    temper_confirmation_required: bool
    sources: list[str]
    candidates: list[MaterialCandidate]
    user_corrected: bool = False


class DimensionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reader_model: str
    value: float | None
    units: Units
    source: DimensionSource
    dimension_path: str | None
    evidence: str | None
    uncertainty: str | None
    chain_terms: list[ChainTerm]


class DimensionFieldResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: FieldStatus
    value: float | None
    units: Units | None
    source: DimensionSource | None
    dimension_path: str | None
    candidates: list[DimensionCandidate]
    reasons: list[str]
    user_corrected: bool = False


class DimensionFieldResults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diameter: DimensionFieldResult
    thickness: DimensionFieldResult
    width: DimensionFieldResult
    length: DimensionFieldResult


class DrawingStockCalloutCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reader_model: str
    value: DrawingStockCallout


class DrawingStockCalloutResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: FieldStatus
    value: DrawingStockCallout | None
    candidates: list[DrawingStockCalloutCandidate]
    reasons: list[str]
    user_corrected: bool = False


class StockRecommendation(BaseModel):
    """Clean API representation of the preserved deterministic shop math."""

    model_config = ConfigDict(extra="forbid")

    material_name: str
    stock_shape: str
    stock_form: str
    supplier_description: str
    stock_thickness: str | None
    stock_width: str | None
    stock_diameter: str | None
    cut_length: str
    closest_drop_length: str
    bar_yield: str
    dominant_machining_process: str
    finished_dimensions: dict[str, float | str]
    adjusted_dimensions: dict[str, float | str]


class RecalculationDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diameter: float | None
    thickness: float | None
    width: float | None
    length: float | None


CorrectionField = Literal[
    "part_number",
    "part_name",
    "units",
    "material",
    "shape",
    "diameter",
    "thickness",
    "width",
    "length",
]


class RecalculationRequest(BaseModel):
    """Browser-held accepted facts plus explicit user corrections."""

    model_config = ConfigDict(extra="forbid")

    analysis_id: str
    part_number: str | None
    part_name: str | None
    units: Units
    material_callout_raw: str
    allowance_class: MaterialClassification
    shape: Shape
    dimensions: RecalculationDimensions
    corrected_fields: list[CorrectionField]


class RecalculationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: str
    recommendation: StockRecommendation
    user_corrected_fields: list[CorrectionField]
    warnings: list[str]
    requires_machinist_verification: Literal[True] = True
    verification_message: str


class ReaderSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reader_model: str
    status: ReaderStatus
    warnings: list[str]
    conflicts: list[str]
    error: str | None


class AnalysisResponse(BaseModel):
    """Field-level API response; partial success is a normal HTTP 200 result."""

    model_config = ConfigDict(extra="forbid")

    analysis_id: str
    presentation_status: PresentationStatus
    part_number: FieldResult
    part_name: FieldResult
    units: FieldResult
    material: MaterialResult
    shape: FieldResult
    dimensions: DimensionFieldResults
    drawing_stock_callout: DrawingStockCalloutResult
    recommendation: StockRecommendation | None
    blocked_outputs: list[str]
    reader_summaries: list[ReaderSummary]
    validation_summary: list[str]
    warnings: list[str]
    requires_machinist_verification: Literal[True] = True
    verification_message: str
