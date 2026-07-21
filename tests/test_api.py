"""Offline API smoke tests; no real client or paid call is used."""

import httpx
import pymupdf
import pytest

from backend.domain.models import (
    BoundingDimensions,
    DimensionEvidence,
    DimensionSource,
    DrawingInterpretation,
    MaterialClassification,
    ReaderBatch,
    ReaderResult,
    Shape,
    Units,
)
from backend.main import app


def _pdf_bytes() -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "API-TEST API test pin A2 Tool Steel 0.378 1.5625 1.750",
    )
    payload = document.tobytes()
    document.close()
    return payload


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


def _interpretation() -> DrawingInterpretation:
    return DrawingInterpretation(
        part_number="API-TEST",
        part_name="API test pin",
        shape=Shape.ROUND,
        supplier_form_candidate="Round Bar",
        material_callout_raw="A2 Tool Steel",
        material_callout_evidence=["Title block material field"],
        material_classification=MaterialClassification.TOOL_STEEL,
        projection="THIRD_ANGLE",
        identified_views=["FRONT", "RIGHT_SIDE"],
        dimension_claims=[],
        drawing_stock_callout=None,
        tabulated_dimension_evidence=[],
        bounding=BoundingDimensions(
            units=Units.IN,
            diameter=_dimension(0.378),
            thickness=_dimension(None),
            width=_dimension(None),
            length=_dimension(1.5625),
        ),
        warnings=[],
        conflicts=[],
        unsupported_reason=None,
    )


@pytest.mark.asyncio
async def test_pdf_scope_and_missing_key_are_explicit():
    app.state.drawing_reader = None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/health")
        assert health.status_code == 200
        assert health.json()["input_scope"] == "digitally-generated-pdf"

        wrong_type = await client.post(
            "/analyze",
            files={"file": ("drawing.png", b"\x89PNG", "image/png")},
        )
        assert wrong_type.status_code == 415

        missing_key = await client.post(
            "/analyze",
            files={
                "file": (
                    "drawing.pdf",
                    _pdf_bytes(),
                    "application/pdf",
                )
            },
        )
        assert missing_key.status_code == 503


@pytest.mark.asyncio
async def test_pdf_analysis_runs_two_agreeing_reads_then_deterministic_steps():
    class FakeDrawingReader:
        calls = 0

        async def interpret_pdf(self, pdf_bytes: bytes, filename: str):
            self.calls += 1
            assert pdf_bytes.startswith(b"%PDF")
            assert filename == "drawing.pdf"
            interpretation = _interpretation()
            return ReaderBatch(
                reads=[
                    ReaderResult(
                        reader_model="gpt-5.6-sol",
                        interpretation=interpretation,
                    ),
                    ReaderResult(
                        reader_model="gpt-5.6-terra",
                        interpretation=interpretation.model_copy(deep=True),
                    ),
                ],
                failures=[],
            )

    fake = FakeDrawingReader()
    app.state.drawing_reader = fake
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/analyze",
            files={
                "file": (
                    "drawing.pdf",
                    _pdf_bytes(),
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200
    assert fake.calls == 1
    payload = response.json()
    assert payload["presentation_status"] == "COMPLETE"
    assert payload["part_number"]["value"] == "API-TEST"
    assert payload["recommendation"]["stock_shape"] == "Round"
    assert payload["requires_machinist_verification"] is True


@pytest.mark.asyncio
async def test_dimension_uncertainty_returns_partial_success_not_422():
    class FakeDrawingReader:
        async def interpret_pdf(self, pdf_bytes: bytes, filename: str):
            sol = _interpretation()
            terra = _interpretation()
            terra.bounding.length = _dimension(1.75)
            return ReaderBatch(
                reads=[
                    ReaderResult(reader_model="gpt-5.6-sol", interpretation=sol),
                    ReaderResult(reader_model="gpt-5.6-terra", interpretation=terra),
                ],
                failures=[],
            )

    app.state.drawing_reader = FakeDrawingReader()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/analyze",
            files={
                "file": (
                    "drawing.pdf",
                    _pdf_bytes(),
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["presentation_status"] == "PARTIAL_SUCCESS"
    assert payload["material"]["raw_callout"] == "A2 Tool Steel"
    assert payload["shape"]["value"] == "ROUND"
    assert payload["dimensions"]["length"]["status"] == "NEEDS_REVIEW"
    assert payload["recommendation"] is None


@pytest.mark.asyncio
async def test_recalculation_uses_confirmed_facts_without_model_calls():
    class FailingIfCalledReader:
        async def interpret_pdf(self, pdf_bytes: bytes, filename: str):
            raise AssertionError("Recalculation must not rerun drawing readers")

    app.state.drawing_reader = FailingIfCalledReader()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/recalculate",
            json={
                "analysis_id": "analysis-test-1",
                "part_number": "MANUAL-001",
                "part_name": "Corrected block",
                "units": "IN",
                "material_callout_raw": "6061-T6 Aluminum",
                "allowance_class": "ALUMINUM",
                "shape": "FLAT",
                "dimensions": {
                    "diameter": None,
                    "thickness": 0.5,
                    "width": 1.5,
                    "length": 2.0,
                },
                "corrected_fields": ["width", "length"],
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_id"] == "analysis-test-1"
    assert payload["user_corrected_fields"] == ["width", "length"]
    assert payload["recommendation"]["stock_shape"] == "Flat"
    assert "did not rerun" in payload["warnings"][0]
