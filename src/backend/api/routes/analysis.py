"""Thin PDF upload route for the drawing-analysis workflow."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from openai import OpenAIError
from pydantic import ValidationError

from backend.clients.openai_vision import ModelOutputError
from backend.core.config import settings
from backend.domain.dimensions import DrawingUncertainError
from backend.domain.pipeline import build_recommendation

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze")
async def analyze_drawing(
    request: Request,
    file: Annotated[UploadFile, File()],
) -> dict:
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

    vision_client = getattr(request.app.state, "vision_client", None)
    if vision_client is None:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured on the backend.",
        )

    try:
        interpretation = await vision_client.interpret_pdf(
            pdf_bytes, file.filename
        )
    except (OpenAIError, ModelOutputError, ValidationError) as exc:
        logger.exception("GPT-5.6 drawing interpretation failed")
        raise HTTPException(
            status_code=502,
            detail=(
                "The drawing model did not return a valid interpretation. "
                "No stock recommendation was produced."
            ),
        ) from exc

    try:
        return build_recommendation(interpretation)
    except (DrawingUncertainError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
