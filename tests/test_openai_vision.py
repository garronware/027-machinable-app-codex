"""The required prompt and PDF settings are applied at the model call."""

from types import SimpleNamespace

import pytest

from backend.clients.openai_vision import OpenAIDualReaderClient, OpenAIVisionClient
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
            DimensionSource.EXPLICIT_OVERALL if value is not None else DimensionSource.NOT_FOUND
        ),
        dimension_path=None,
        evidence="explicit overall dimension" if value is not None else None,
        uncertainty=None,
        chain_terms=[],
    )


@pytest.mark.asyncio
async def test_call_uses_one_authoritative_prompt_and_high_detail_pdf():
    interpretation = DrawingInterpretation(
        part_number="TEST",
        part_name=None,
        shape=Shape.ROUND,
        supplier_form_candidate="Round Bar",
        material_callout_raw="A2 Tool Steel",
        material_callout_evidence=["Title block material field"],
        material_classification=MaterialClassification.TOOL_STEEL,
        projection="THIRD_ANGLE",
        identified_views=["FRONT"],
        dimension_claims=[],
        drawing_stock_callout=None,
        tabulated_dimension_evidence=[],
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
    assert captured["reasoning"] == {"effort": "high"}
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


@pytest.mark.asyncio
async def test_dual_reader_preserves_independent_sol_and_terra_results():
    interpretation = DrawingInterpretation(
        part_number="TEST",
        part_name=None,
        shape=Shape.ROUND,
        supplier_form_candidate="Round Bar",
        material_callout_raw="A2 Tool Steel",
        material_callout_evidence=["Title block material field"],
        material_classification=MaterialClassification.TOOL_STEEL,
        bounding=BoundingDimensions(
            units=Units.IN,
            diameter=_dimension(1.0),
            thickness=_dimension(None),
            width=_dimension(None),
            length=_dimension(2.0),
        ),
        projection="THIRD_ANGLE",
        identified_views=["FRONT"],
        dimension_claims=[],
        drawing_stock_callout=None,
        tabulated_dimension_evidence=[],
        warnings=[],
        conflicts=[],
        unsupported_reason=None,
    )

    class FakeReader:
        def __init__(self, model: str):
            self.model = model

        async def interpret_pdf(self, pdf_bytes: bytes, filename: str):
            assert pdf_bytes.startswith(b"%PDF")
            assert filename == "drawing.pdf"
            return interpretation.model_copy(deep=True)

    client = OpenAIDualReaderClient(api_key="test-key")
    client.readers = [
        FakeReader("gpt-5.6-sol"),
        FakeReader("gpt-5.6-terra"),
    ]

    batch = await client.interpret_pdf(b"%PDF-1.7\n", "drawing.pdf")

    assert [read.reader_model for read in batch.reads] == [
        "gpt-5.6-sol",
        "gpt-5.6-terra",
    ]
    assert not batch.failures
