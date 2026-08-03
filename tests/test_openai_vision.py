"""The specialized readers keep focused contracts and high-detail PDF input."""

from types import SimpleNamespace

import pytest

from backend.clients.openai_vision import OpenAISpecializedReaderClient
from backend.domain.models import (
    BoundingDimensions,
    DimensionAxis,
    DimensionEvidence,
    DimensionRecoveryInterpretation,
    DimensionSource,
    GeometryInterpretation,
    MaterialClassification,
    RecoveredDimension,
    Shape,
    TitleBlockInterpretation,
    Units,
)
from backend.domain.pdf_evidence import PdfRegionCrop
from tests.evaluation.evaluate_vision import build_reader_reports
from tests.evaluation.print_index import TruthCase


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


def _title() -> TitleBlockInterpretation:
    return TitleBlockInterpretation(
        material_callout_raw="A2 Tool Steel",
        material_callout_evidence=["Title block material field"],
        material_name="A2 Tool Steel",
        material_classification=MaterialClassification.TOOL_STEEL,
        warnings=[],
    )


def _geometry() -> GeometryInterpretation:
    return GeometryInterpretation(
        shape=Shape.ROUND,
        bounding=BoundingDimensions(
            units=Units.IN,
            diameter=_dimension(1.0),
            thickness=_dimension(None),
            width=_dimension(None),
            length=_dimension(2.0),
        ),
        drawing_stock_callout=None,
        projection="THIRD_ANGLE",
        identified_views=["FRONT"],
        warnings=[],
        conflicts=[],
        unsupported_reason=None,
    )


@pytest.mark.asyncio
async def test_material_call_uses_terra_focused_contract_and_high_detail_pdf():
    captured: dict = {}

    class FakeResponses:
        async def parse(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_parsed=_title())

    client = OpenAISpecializedReaderClient(api_key="test-key")
    client.title_reader._client = SimpleNamespace(responses=FakeResponses())

    result = await client.title_reader.interpret_pdf(b"%PDF-1.7\n", "drawing.pdf")

    assert result == _title()
    assert captured["model"] == "gpt-5.6-terra"
    assert captured["reasoning"] == {"effort": "high"}
    assert captured["store"] is False
    assert captured["text_format"] is TitleBlockInterpretation
    assert "material purchasing facts" in captured["input"][1]["content"][1]["text"]

    system_prompt = captured["input"][0]["content"][0]["text"]
    assert system_prompt == client.title_reader.prompt
    assert "Do not read or return part identity" in system_prompt
    assert "stock shape, or dimensions" in system_prompt
    assert "part number" not in system_prompt.lower()

    file_item = captured["input"][1]["content"][0]
    assert file_item["type"] == "input_file"
    assert file_item["filename"] == "drawing.pdf"
    assert file_item["detail"] == "high"
    assert file_item["file_data"].startswith("data:application/pdf;base64,")


@pytest.mark.asyncio
async def test_specialized_client_preserves_non_overlapping_results():
    class FakeReader:
        def __init__(self, model: str, result):
            self.model = model
            self.result = result

        async def interpret_pdf(self, pdf_bytes: bytes, filename: str):
            assert pdf_bytes.startswith(b"%PDF")
            assert filename == "drawing.pdf"
            return self.result

    client = OpenAISpecializedReaderClient(api_key="test-key")
    client.title_reader = FakeReader("gpt-5.6-terra", _title())
    client.geometry_reader = FakeReader("gpt-5.6-sol", _geometry())

    batch = await client.interpret_pdf(b"%PDF-1.7\n", "drawing.pdf")

    assert batch.title is not None
    assert batch.title.reader_model == "gpt-5.6-terra"
    assert batch.title.interpretation.material_name == "A2 Tool Steel"
    assert batch.geometry is not None
    assert batch.geometry.reader_model == "gpt-5.6-sol"
    assert batch.geometry.interpretation.shape is Shape.ROUND
    assert not batch.failures

    reports = build_reader_reports(
        TruthCase(
            filename="drawing.pdf",
            part_number="TEST",
            section="Test",
            shape=Shape.ROUND,
            units="IN",
            diameter=1.0,
            thickness=None,
            width=None,
            length=2.0,
            material="A2 Tool Steel",
            notes="",
        ),
        batch,
        title_model="gpt-5.6-terra",
        geometry_model="gpt-5.6-sol",
    )

    assert [report["task"] for report in reports] == [
        "TITLE_MATERIAL",
        "SHAPE_GEOMETRY",
    ]
    assert reports[0]["comparison"]["actual_material_name"] == "A2 Tool Steel"
    assert reports[1]["comparison"]["shape_match"] is True
    assert {dimension["bucket"] for dimension in reports[1]["comparison"]["dimensions"]} == {
        "MATCH"
    }


@pytest.mark.asyncio
async def test_missing_flat_thickness_triggers_focused_crop_recovery(monkeypatch):
    geometry = GeometryInterpretation(
        shape=Shape.FLAT,
        bounding=BoundingDimensions(
            units=Units.MM,
            diameter=_dimension(None),
            thickness=DimensionEvidence(
                value=None,
                source=DimensionSource.NOT_FOUND,
                dimension_path=None,
                evidence="Edge view",
                uncertainty="Nearby 6.36 and 12.700 callouts require visual tracing.",
                chain_terms=[],
            ),
            width=_dimension(184.2),
            length=_dimension(215.9),
        ),
        drawing_stock_callout=None,
        projection="THIRD_ANGLE",
        identified_views=["EDGE", "FRONT"],
        warnings=[],
        conflicts=[],
        unsupported_reason=None,
    )

    class FakeReader:
        def __init__(self, model: str, result):
            self.model = model
            self.result = result

        async def interpret_pdf(self, pdf_bytes: bytes, filename: str):
            return self.result

    class FakeRecoveryReader:
        model = "gpt-5.6-sol"

        async def interpret_images(self, crops, *, shape, units, axes):
            assert crops[0].png_bytes == b"png"
            assert shape is Shape.FLAT
            assert units is Units.MM
            assert axes == [DimensionAxis.THICKNESS]
            return DimensionRecoveryInterpretation(
                dimensions=[
                    RecoveredDimension(
                        axis=DimensionAxis.THICKNESS,
                        value=12.7,
                        units=Units.MM,
                        source=DimensionSource.EXPLICIT_OUTERMOST_FEATURE,
                        evidence=("12.700 [.5000] THRU leader terminates on the plate surfaces."),
                        uncertainty=None,
                    )
                ]
            )

    monkeypatch.setattr(
        "backend.clients.openai_vision.render_dimension_recovery_crops",
        lambda *_args, **_kwargs: [PdfRegionCrop(page_number=1, region=None, png_bytes=b"png")],
    )
    client = OpenAISpecializedReaderClient(api_key="test-key")
    client.title_reader = FakeReader("gpt-5.6-terra", _title())
    client.geometry_reader = FakeReader("gpt-5.6-sol", geometry)
    client.recovery_reader = FakeRecoveryReader()

    batch = await client.interpret_pdf(b"%PDF-1.7\n", "drawing.pdf")

    assert batch.model_calls_attempted == 3
    assert batch.geometry is not None
    assert batch.geometry.recovered_axes == [DimensionAxis.THICKNESS]
    recovered = batch.geometry.interpretation.bounding.thickness
    assert recovered.value == 12.7
    assert recovered.uncertainty is None
    assert recovered.evidence is not None
    assert recovered.evidence.startswith("Focused crop recovery:")


@pytest.mark.asyncio
async def test_recovery_images_use_original_detail():
    captured: dict = {}

    class FakeResponses:
        async def parse(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_parsed=DimensionRecoveryInterpretation(dimensions=[]))

    client = OpenAISpecializedReaderClient(api_key="test-key")
    client.recovery_reader._client = SimpleNamespace(responses=FakeResponses())

    await client.recovery_reader.interpret_images(
        [PdfRegionCrop(page_number=1, region=None, png_bytes=b"png")],
        shape=Shape.FLAT,
        units=Units.MM,
        axes=[DimensionAxis.THICKNESS],
    )

    image_item = next(
        item for item in captured["input"][1]["content"] if item["type"] == "input_image"
    )
    assert image_item["detail"] == "original"
    assert image_item["image_url"].startswith("data:image/png;base64,")
