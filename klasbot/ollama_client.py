from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx

logger = logging.getLogger(__name__)


class OllamaStreamError(RuntimeError):
    """Raised when Ollama streaming fails at transport or payload level."""


class OllamaClient:
    def __init__(self, base_url: str, timeout_seconds: float = 180) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds

    async def stream_generate(self, model: str, prompt: str) -> AsyncIterator[str]:
        url = f"{self.base_url}/api/generate"
        payload = {"model": model, "prompt": prompt, "stream": True}

        logger.info("Opening Ollama stream", extra={"url": url, "model": model})

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        data = json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield token
                        if data.get("done"):
                            logger.info("Ollama stream reported completion", extra={"model": model})
                            break
        except httpx.HTTPError as exc:
            logger.exception("Ollama HTTP streaming failure", extra={"model": model, "url": url})
            raise OllamaStreamError("Ollama HTTP streaming failure") from exc
        except json.JSONDecodeError as exc:
            logger.exception("Malformed JSON from Ollama stream", extra={"model": model})
            raise OllamaStreamError("Malformed JSON from Ollama stream") from exc
