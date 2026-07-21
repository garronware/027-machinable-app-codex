"""Environment-backed configuration for the MVP."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env")

ReasoningEffort = Literal["none", "low", "medium", "high", "xhigh", "max"]


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_sol_model: str
    openai_terra_model: str
    openai_reasoning_effort: ReasoningEffort
    allowed_origins: tuple[str, ...]
    max_file_size_mb: int = 50


def load_settings() -> Settings:
    effort = os.getenv("OPENAI_REASONING_EFFORT", "high").strip().lower()
    allowed_efforts = {"none", "low", "medium", "high", "xhigh", "max"}
    if effort not in allowed_efforts:
        raise RuntimeError(
            "OPENAI_REASONING_EFFORT must be one of "
            f"{', '.join(sorted(allowed_efforts))}; got {effort!r}"
        )

    origins = tuple(
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000",
        ).split(",")
        if origin.strip()
    )
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_sol_model=os.getenv("OPENAI_SOL_MODEL", "gpt-5.6-sol").strip(),
        openai_terra_model=os.getenv("OPENAI_TERRA_MODEL", "gpt-5.6-terra").strip(),
        openai_reasoning_effort=cast(ReasoningEffort, effort),
        allowed_origins=origins,
    )


settings = load_settings()
