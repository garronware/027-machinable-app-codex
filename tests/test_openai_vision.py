"""The required prompt and PDF settings are applied at the model call."""

from types import SimpleNamespace

import pytest

from backend.clients.openai_vision import OpenAIVisionClient
from backend.domain.models import (
    BoundingDimensions,
    DimensionEvidence,
    DimensionSource,
    DrawingInterpretation,
    MaterialClassification,
    Shape,
    Units,
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
        evidence="explicit overall dimension" if value is not None else None,
        uncertainty=None,
    )


@pytest.mark.asyncio
async def test_call_uses_one_authoritative_prompt_and_high_detail_pdf():
    interpretation = DrawingInterpretation(
        part_number="TEST",
        part_name=None,
        shape=Shape.ROUND,
        material_name="A2 Tool Steel",
        material_classification=MaterialClassification.TOOL_STEEL,
        projection="THIRD_ANGLE",
        bounding=BoundingDimensions(
            units=Units.IN,
            diameter=_dimension(1.0),
            thickness=_dimension(None),
            width=_dimension(None),
            length=_dimension(2.0),
        ),
        warnings=[],
        conflicts=[],
        unsupported_reason=None,
    )

    captured: dict = {}

    class FakeResponses:
        async def parse(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_parsed=interpretation)

    client = OpenAIVisionClient(api_key="test-key")
    client._client = SimpleNamespace(responses=FakeResponses())

    result = await client.interpret_pdf(b"%PDF-1.7\n", "drawing.pdf")
    assert result is interpretation
    assert captured["model"] == "gpt-5.6-sol"
    assert captured["reasoning"] == {"effort": "medium"}
    assert captured["store"] is False
    assert captured["text_format"] is DrawingInterpretation

    system_prompt = captured["input"][0]["content"][0]["text"]
    assert system_prompt == client.prompt
    assert "Assume third-angle projection" in system_prompt
    assert "clear vector/text content" in system_prompt
    assert "Every derived overall" in system_prompt
    assert "do not silently swap axes" in system_prompt.lower()

    file_item = captured["input"][1]["content"][0]
    assert file_item["type"] == "input_file"
    assert file_item["filename"] == "drawing.pdf"
    assert file_item["detail"] == "high"
    assert file_item["file_data"].startswith("data:application/pdf;base64,")

