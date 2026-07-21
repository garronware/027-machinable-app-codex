"""One high-detail PDF interpretation call through the OpenAI Responses API."""

from __future__ import annotations

import base64
from pathlib import Path

from openai import AsyncOpenAI

from backend.core.config import ReasoningEffort
from backend.domain.models import DrawingInterpretation

PROMPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "prompts"
    / "drawing_interpretation.md"
)


class ModelOutputError(RuntimeError):
    """The model did not return the required structured interpretation."""


class OpenAIVisionClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gpt-5.6-sol",
        reasoning_effort: ReasoningEffort = "medium",
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=120.0)
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.prompt = PROMPT_PATH.read_text(encoding="utf-8")

    async def interpret_pdf(
        self, pdf_bytes: bytes, filename: str
    ) -> DrawingInterpretation:
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
                            "file_data": (
                                "data:application/pdf;base64," + encoded
                            ),
                            "detail": "high",
                        },
                        {
                            "type": "input_text",
                            "text": (
                                "Interpret this digitally generated part drawing "
                                "using the required evidence and precedence rules."
                            ),
                        },
                    ],
                },
            ],
            text_format=DrawingInterpretation,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ModelOutputError(
                "GPT-5.6 Sol returned no structured drawing interpretation."
            )
        return parsed

