"""Independent GPT-5.6 drawing readers through the OpenAI Responses API."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path

from openai import AsyncOpenAI

from backend.core.config import ReasoningEffort
from backend.domain.models import (
    DrawingInterpretation,
    ReaderBatch,
    ReaderFailure,
    ReaderResult,
)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "drawing_interpretation.md"


class ModelOutputError(RuntimeError):
    """The drawing readers did not return usable structured interpretations."""


class OpenAIVisionClient:
    """One full drawing reader; used twice with different GPT-5.6 models."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gpt-5.6-sol",
        reasoning_effort: ReasoningEffort = "high",
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=120.0)
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.prompt = PROMPT_PATH.read_text(encoding="utf-8")

    async def interpret_pdf(self, pdf_bytes: bytes, filename: str) -> DrawingInterpretation:
        encoded = base64.b64encode(pdf_bytes).decode("ascii")
        safe_filename = Path(filename).name
        response = await self._client.responses.parse(
            model=self.model,
            reasoning={"effort": self.reasoning_effort},
            store=False,
            input=[
                {
                    "role": "system",
                    "content": [
                        {"type": "input_text", "text": self.prompt},
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "filename": safe_filename,
                            "file_data": ("data:application/pdf;base64," + encoded),
                            "detail": "high",
                        },
                        {
                            "type": "input_text",
                            "text": (
                                "Independently interpret every requested field in this "
                                "digitally generated part drawing. Preserve evidence and "
                                "uncertainty; do not assume another reader will fill gaps."
                            ),
                        },
                    ],
                },
            ],
            text_format=DrawingInterpretation,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ModelOutputError(f"{self.model} returned no structured drawing interpretation.")
        return parsed


class OpenAIDualReaderClient:
    """Run Sol and Terra independently and preserve both typed results."""

    def __init__(
        self,
        *,
        api_key: str,
        sol_model: str = "gpt-5.6-sol",
        terra_model: str = "gpt-5.6-terra",
        reasoning_effort: ReasoningEffort = "high",
    ) -> None:
        self.readers = [
            OpenAIVisionClient(
                api_key=api_key,
                model=sol_model,
                reasoning_effort=reasoning_effort,
            ),
            OpenAIVisionClient(
                api_key=api_key,
                model=terra_model,
                reasoning_effort=reasoning_effort,
            ),
        ]

    async def interpret_pdf(self, pdf_bytes: bytes, filename: str) -> ReaderBatch:
        outcomes = await asyncio.gather(
            *(reader.interpret_pdf(pdf_bytes, filename) for reader in self.readers),
            return_exceptions=True,
        )
        reads: list[ReaderResult] = []
        failures: list[ReaderFailure] = []
        for reader, outcome in zip(self.readers, outcomes, strict=True):
            if isinstance(outcome, BaseException):
                failures.append(ReaderFailure(reader_model=reader.model, error=str(outcome)))
            else:
                reads.append(
                    ReaderResult(
                        reader_model=reader.model,
                        interpretation=outcome,
                    )
                )
        if not reads:
            detail = "; ".join(f"{failure.reader_model}: {failure.error}" for failure in failures)
            raise ModelOutputError(f"Both drawing readers failed. {detail}")
        return ReaderBatch(reads=reads, failures=failures)
