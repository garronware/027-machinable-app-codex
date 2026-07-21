"""Typed contracts at the model/domain boundary."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


class DimensionSource(StrEnum):
    EXPLICIT_OVERALL = "EXPLICIT_OVERALL"
    EXPLICIT_OUTERMOST_FEATURE = "EXPLICIT_OUTERMOST_FEATURE"
    RECONCILED_ACROSS_VIEWS = "RECONCILED_ACROSS_VIEWS"
    CHAINED_DIMENSIONS = "CHAINED_DIMENSIONS"
    INFERRED_OUTLINE = "INFERRED_OUTLINE"
    NOT_FOUND = "NOT_FOUND"


class DimensionEvidence(BaseModel):
    """One extracted dimension and the drawing evidence behind it."""

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


class BoundingDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    units: Units
    diameter: DimensionEvidence
    thickness: DimensionEvidence
    width: DimensionEvidence
    length: DimensionEvidence


class DrawingInterpretation(BaseModel):
    """Structured output from the one GPT-5.6 Sol PDF interpretation call."""

    model_config = ConfigDict(extra="forbid")

    part_number: str | None
    part_name: str | None
    shape: Shape
    material_name: str | None
    material_classification: MaterialClassification
    bounding: BoundingDimensions
    projection: Literal["THIRD_ANGLE", "FIRST_ANGLE", "OTHER", "UNKNOWN"]
    warnings: list[str]
    conflicts: list[str]
    unsupported_reason: str | None
