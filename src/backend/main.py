"""FastAPI entry point for the Machinable pilot."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.analysis import router as analysis_router
from backend.clients.openai_vision import OpenAISpecializedReaderClient
from backend.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.drawing_reader = (
        OpenAISpecializedReaderClient(
            api_key=settings.openai_api_key,
            sol_model=settings.openai_sol_model,
            terra_model=settings.openai_terra_model,
            reasoning_effort=settings.openai_reasoning_effort,
        )
        if settings.openai_api_key
        else None
    )
    yield


app = FastAPI(
    title="Machinable",
    description="PDF-first raw-stock recommendation pilot.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(analysis_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "models": f"{settings.openai_sol_model},{settings.openai_terra_model}",
        "input_scope": "digitally-generated-pdf",
    }
