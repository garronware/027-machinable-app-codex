"""Specialized GPT-5.6 drawing readers through the OpenAI Responses API."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from backend.core.config import ReasoningEffort
from backend.domain.models import (
    DimensionAxis,
    DimensionEvidence,
    DimensionRecoveryInterpretation,
    DimensionSource,
    GeometryInterpretation,
    GeometryReaderResult,
    ReaderFailure,
    Shape,
    SpecializedReaderBatch,
    TitleBlockInterpretation,
    TitleBlockReaderResult,
    Units,
)
from backend.domain.pdf_evidence import (
    PdfRegionCrop,
    render_dimension_recovery_crops,
)

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
TITLE_PROMPT_PATH = PROMPT_DIR / "title_material.md"
GEOMETRY_PROMPT_PATH = PROMPT_DIR / "shape_geometry.md"
RECOVERY_PROMPT_PATH = PROMPT_DIR / "dimension_recovery.md"
ParsedModel = TypeVar("ParsedModel", bound=BaseModel)

TITLE_TASK = "Return only the drawing's material purchasing facts."
GEOMETRY_TASK = "Return only stock shape and applicable finished bounding dimensions."


class ModelOutputError(RuntimeError):
    """The drawing readers did not return usable structured interpretations."""


class _FocusedPdfReader:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        reasoning_effort: ReasoningEffort,
        task: str,
        text_format: type[ParsedModel],
        prompt_path: Path,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=120.0)
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.task = task.strip()
        self.text_format = text_format
        self.prompt = prompt_path.read_text(encoding="utf-8")

    async def interpret_pdf(self, pdf_bytes: bytes, filename: str) -> ParsedModel:
        encoded = base64.b64encode(pdf_bytes).decode("ascii")
        response = await self._client.responses.parse(
            model=self.model,
            reasoning={"effort": self.reasoning_effort},
            store=False,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": self.prompt}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "filename": Path(filename).name,
                            "file_data": f"data:application/pdf;base64,{encoded}",
                            "detail": "high",
                        },
                        {"type": "input_text", "text": self.task},
                    ],
                },
            ],
            text_format=self.text_format,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ModelOutputError(f"{self.model} returned no structured interpretation.")
        return parsed


class _FocusedImageReader:
    """One conditional structured read over rendered PDF regions."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        reasoning_effort: ReasoningEffort,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=120.0)
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.prompt = RECOVERY_PROMPT_PATH.read_text(encoding="utf-8")

    async def interpret_images(
        self,
        crops: list[PdfRegionCrop],
        *,
        shape: Shape,
        units: Units,
        axes: list[DimensionAxis],
    ) -> DimensionRecoveryInterpretation:
        requested_axes = ", ".join(axis.value for axis in axes)
        content: list[dict[str, str]] = [
            {
                "type": "input_text",
                "text": (
                    f"Resolve only these axes: {requested_axes}. "
                    f"Stock shape is {shape.value}. Return values in "
                    f"{units.value if units is not Units.UNKNOWN else 'the drawing primary units'}."
                ),
            }
        ]
        for index, crop in enumerate(crops, start=1):
            encoded = base64.b64encode(crop.png_bytes).decode("ascii")
            content.extend(
                [
                    {
                        "type": "input_text",
                        "text": f"Crop {index} is from PDF page {crop.page_number}.",
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{encoded}",
                        "detail": "original",
                    },
                ]
            )
        response = await self._client.responses.parse(
            model=self.model,
            reasoning={"effort": self.reasoning_effort},
            store=False,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": self.prompt}],
                },
                {"role": "user", "content": content},
            ],
            text_format=DimensionRecoveryInterpretation,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ModelOutputError(f"{self.model} returned no structured dimension recovery.")
        return parsed


def _missing_stock_axes(geometry: GeometryInterpretation) -> list[DimensionAxis]:
    bounding = geometry.bounding
    if geometry.shape is Shape.FLAT:
        return [
            axis
            for axis, evidence in (
                (DimensionAxis.THICKNESS, bounding.thickness),
                (DimensionAxis.WIDTH, bounding.width),
            )
            if evidence.value is None
        ]
    if geometry.shape is Shape.ROUND:
        cross_section_available = (
            bounding.thickness.value is not None and bounding.width.value is not None
        )
        if bounding.diameter.value is None and not cross_section_available:
            return [DimensionAxis.DIAMETER]
    return []


def _recovery_anchor_texts(
    geometry: GeometryInterpretation,
    axes: list[DimensionAxis],
) -> list[str]:
    texts: list[str] = []
    for axis in axes:
        evidence = getattr(geometry.bounding, axis.value.lower())
        if evidence.evidence:
            texts.append(evidence.evidence)
        if evidence.uncertainty:
            texts.append(evidence.uncertainty)
    return texts


def _merge_dimension_recovery(
    geometry: GeometryInterpretation,
    recovery: DimensionRecoveryInterpretation,
    requested_axes: list[DimensionAxis],
) -> list[DimensionAxis]:
    recovered: list[DimensionAxis] = []
    for claim in recovery.dimensions:
        if claim.axis not in requested_axes or claim.value is None:
            continue
        if (
            geometry.bounding.units is not Units.UNKNOWN
            and claim.units is not geometry.bounding.units
        ):
            geometry.conflicts.append(
                f"Focused {claim.axis.value.lower()} recovery returned "
                f"{claim.units.value}, not {geometry.bounding.units.value}."
            )
            continue
        if geometry.bounding.units is Units.UNKNOWN:
            geometry.bounding.units = claim.units
        current: DimensionEvidence = getattr(
            geometry.bounding,
            claim.axis.value.lower(),
        )
        if current.value is not None:
            continue
        setattr(
            geometry.bounding,
            claim.axis.value.lower(),
            DimensionEvidence(
                value=claim.value,
                source=claim.source,
                dimension_path=None,
                evidence=(
                    f"Focused crop recovery: {claim.evidence}"
                    if claim.evidence
                    else "Focused crop recovery."
                ),
                uncertainty=claim.uncertainty,
                chain_terms=[],
            ),
        )
        if not claim.uncertainty and claim.source is not DimensionSource.NOT_FOUND:
            recovered.append(claim.axis)
    return recovered


class OpenAISpecializedReaderClient:
    """Run Terra title/material and Sol geometry reads in parallel."""

    def __init__(
        self,
        *,
        api_key: str,
        sol_model: str = "gpt-5.6-sol",
        terra_model: str = "gpt-5.6-terra",
        reasoning_effort: ReasoningEffort = "high",
    ) -> None:
        self.title_reader = _FocusedPdfReader(
            api_key=api_key,
            model=terra_model,
            reasoning_effort=reasoning_effort,
            task=TITLE_TASK,
            text_format=TitleBlockInterpretation,
            prompt_path=TITLE_PROMPT_PATH,
        )
        self.geometry_reader = _FocusedPdfReader(
            api_key=api_key,
            model=sol_model,
            reasoning_effort=reasoning_effort,
            task=GEOMETRY_TASK,
            text_format=GeometryInterpretation,
            prompt_path=GEOMETRY_PROMPT_PATH,
        )
        self.recovery_reader = _FocusedImageReader(
            api_key=api_key,
            model=sol_model,
            reasoning_effort=reasoning_effort,
        )

    async def interpret_pdf(self, pdf_bytes: bytes, filename: str) -> SpecializedReaderBatch:
        title_outcome, geometry_outcome = await asyncio.gather(
            self.title_reader.interpret_pdf(pdf_bytes, filename),
            self.geometry_reader.interpret_pdf(pdf_bytes, filename),
            return_exceptions=True,
        )
        failures: list[ReaderFailure] = []
        title_result: TitleBlockReaderResult | None = None
        geometry_result: GeometryReaderResult | None = None
        model_calls_attempted = 2

        if isinstance(title_outcome, BaseException):
            failures.append(
                ReaderFailure(
                    reader_model=self.title_reader.model,
                    error=str(title_outcome),
                )
            )
        else:
            title_result = TitleBlockReaderResult(
                reader_model=self.title_reader.model,
                interpretation=title_outcome,
            )

        if isinstance(geometry_outcome, BaseException):
            failures.append(
                ReaderFailure(
                    reader_model=self.geometry_reader.model,
                    error=str(geometry_outcome),
                )
            )
        else:
            missing_axes = _missing_stock_axes(geometry_outcome)
            recovered_axes: list[DimensionAxis] = []
            if missing_axes:
                model_calls_attempted += 1
                try:
                    crops = await asyncio.to_thread(
                        render_dimension_recovery_crops,
                        pdf_bytes,
                        _recovery_anchor_texts(geometry_outcome, missing_axes),
                    )
                    recovery = await self.recovery_reader.interpret_images(
                        crops,
                        shape=geometry_outcome.shape,
                        units=geometry_outcome.bounding.units,
                        axes=missing_axes,
                    )
                    recovered_axes = _merge_dimension_recovery(
                        geometry_outcome,
                        recovery,
                        missing_axes,
                    )
                except BaseException as exc:
                    failures.append(
                        ReaderFailure(
                            reader_model=self.recovery_reader.model,
                            error=f"Focused dimension recovery failed: {exc}",
                        )
                    )
            geometry_result = GeometryReaderResult(
                reader_model=self.geometry_reader.model,
                interpretation=geometry_outcome,
                recovered_axes=recovered_axes,
            )

        if title_result is None and geometry_result is None:
            detail = "; ".join(f"{failure.reader_model}: {failure.error}" for failure in failures)
            raise ModelOutputError(f"Both specialized readers failed. {detail}")
        return SpecializedReaderBatch(
            title=title_result,
            geometry=geometry_result,
            failures=failures,
            model_calls_attempted=model_calls_attempted,
        )
