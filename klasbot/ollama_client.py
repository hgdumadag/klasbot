from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str, timeout_seconds: float = 180) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds

    async def stream_generate(self, model: str, prompt: str) -> AsyncIterator[str]:
        url = f"{self.base_url}/api/generate"
        payload = {"model": model, "prompt": prompt, "stream": True}

        logger.info("Opening Ollama stream", extra={"url": url, "model": model})

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError:
                    logger.exception(
                        "Ollama returned non-success status",
                        extra={"status_code": response.status_code, "model": model},
                    )
                    raise

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        logger.exception("Invalid JSON line received from Ollama stream", extra={"model": model})
                        raise

                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done"):
                        logger.info("Ollama stream reported completion", extra={"model": model})
                        break
