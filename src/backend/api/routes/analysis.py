"""Thin PDF upload route for the drawing-analysis workflow."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from openai import OpenAIError
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.clients.openai_vision import ModelOutputError
from backend.core.config import settings
from backend.domain.dimensions import DrawingUncertainError
from backend.domain.models import (
    AnalysisResponse,
    RecalculationRequest,
    RecalculationResponse,
)
from backend.domain.pdf_evidence import PdfEvidenceError, extract_pdf_evidence
from backend.domain.pipeline import (
    build_analysis_response,
    recalculate_from_confirmed_facts,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_drawing(
    request: Request,
    file: Annotated[UploadFile, File()],
) -> AnalysisResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No PDF selected.")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=415,
            detail="MVP input is limited to digitally generated PDF drawings.",
        )

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="The uploaded PDF is empty.")
    if len(pdf_bytes) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"PDF exceeds the {settings.max_file_size_mb} MB limit.",
        )
    if not pdf_bytes.lstrip().startswith(b"%PDF"):
        raise HTTPException(
            status_code=415,
            detail="The uploaded file does not contain a valid PDF signature.",
        )

    try:
        pdf_evidence = await run_in_threadpool(extract_pdf_evidence, pdf_bytes)
    except PdfEvidenceError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    drawing_reader = getattr(request.app.state, "drawing_reader", None)
    if drawing_reader is None:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured on the backend.",
        )

    try:
        reader_batch = await drawing_reader.interpret_pdf(pdf_bytes, file.filename)
    except (OpenAIError, ModelOutputError, ValidationError) as exc:
        logger.exception("GPT-5.6 drawing interpretation failed")
        raise HTTPException(
            status_code=502,
            detail="The drawing readers did not return a valid interpretation.",
        ) from exc
    response = build_analysis_response(reader_batch, pdf_evidence)
    logger.info(
        "Drawing analysis completed: presentation=%s shape=%s units=%s material=%s "
        "diameter=%s thickness=%s width=%s length=%s recommendation=%s",
        response.presentation_status.value,
        response.shape.status.value,
        response.units.status.value,
        response.material.status.value,
        response.dimensions.diameter.status.value,
        response.dimensions.thickness.status.value,
        response.dimensions.width.status.value,
        response.dimensions.length.status.value,
        response.recommendation is not None,
    )
    return response


@router.post("/recalculate", response_model=RecalculationResponse)
async def recalculate_stock(
    payload: RecalculationRequest,
) -> RecalculationResponse:
    try:
        return recalculate_from_confirmed_facts(payload)
    except (DrawingUncertainError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
