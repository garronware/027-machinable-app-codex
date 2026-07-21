"""Offline API smoke tests; no real client or paid call is used."""

import httpx
import pytest

from backend.domain.models import (
    BoundingDimensions,
    DimensionEvidence,
    DimensionSource,
    DrawingInterpretation,
    MaterialClassification,
    Shape,
    Units,
)
from backend.main import app


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


def _interpretation() -> DrawingInterpretation:
    return DrawingInterpretation(
        part_number="API-TEST",
        part_name="API test pin",
        shape=Shape.ROUND,
        material_name="A2 Tool Steel",
        material_classification=MaterialClassification.TOOL_STEEL,
        projection="THIRD_ANGLE",
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
    app.state.vision_client = None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
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
                    b"%PDF-1.7\n%%EOF",
                    "application/pdf",
                )
            },
        )
        assert missing_key.status_code == 503


@pytest.mark.asyncio
async def test_pdf_analysis_runs_one_fake_interpretation_then_deterministic_steps():
    class FakeVisionClient:
        calls = 0

        async def interpret_pdf(self, pdf_bytes: bytes, filename: str):
            self.calls += 1
            assert pdf_bytes.startswith(b"%PDF")
            assert filename == "drawing.pdf"
            return _interpretation()

    fake = FakeVisionClient()
    app.state.vision_client = fake
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/analyze",
            files={
                "file": (
                    "drawing.pdf",
                    b"%PDF-1.7\n%%EOF",
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200
    assert fake.calls == 1
    payload = response.json()
    assert payload["Part_Basics"]["Part_No"] == "API-TEST"
    assert payload["_analysis"]["requires_machinist_verification"] is True

