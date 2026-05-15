from __future__ import annotations

from typing import Any

from klasbot.config import (
    KLASBOT_AI_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
    VERTEX_GEMMA_MODEL,
    VERTEX_LOCATION,
    VERTEX_PROJECT_ID,
)
from klasbot.ollama_client import OllamaClient
from klasbot.vertex_gemma_client import VertexGemmaClient


def current_ai_model(provider: str | None = None) -> str:
    selected = (provider or KLASBOT_AI_PROVIDER).strip().lower()
    if selected == "vertex_gemma":
        return _vertex_model_name(VERTEX_GEMMA_MODEL)
    return OLLAMA_MODEL


def create_ai_client(provider: str | None = None) -> Any:
    selected = (provider or KLASBOT_AI_PROVIDER).strip().lower()
    if selected == "vertex_gemma":
        return VertexGemmaClient(
            project_id=VERTEX_PROJECT_ID,
            location=VERTEX_LOCATION,
            model=_vertex_model_name(VERTEX_GEMMA_MODEL),
            timeout_seconds=OLLAMA_TIMEOUT_SECONDS,
        )
    return OllamaClient(OLLAMA_BASE_URL, OLLAMA_TIMEOUT_SECONDS)


def _vertex_model_name(model: str) -> str:
    clean_model = model.strip()
    if "/" in clean_model:
        return clean_model
    return f"google/{clean_model}"
