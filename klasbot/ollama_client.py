from __future__ import annotations

import json
import logging
from typing import AsyncIterator
from typing import Any

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
                    if response.is_error:
                        await response.aread()
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
        except httpx.HTTPStatusError as exc:
            message = _http_status_error_message(exc)
            logger.exception("Ollama HTTP status failure", extra={"model": model, "url": url})
            raise OllamaStreamError(message) from exc
        except httpx.HTTPError as exc:
            logger.exception("Ollama HTTP streaming failure", extra={"model": model, "url": url})
            raise OllamaStreamError(str(exc) or "Ollama HTTP streaming failure") from exc
        except json.JSONDecodeError as exc:
            logger.exception("Malformed JSON from Ollama stream", extra={"model": model})
            raise OllamaStreamError("Malformed JSON from Ollama stream") from exc

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        format: str | None = None,
    ) -> str:
        url = f"{self.base_url}/api/chat"
        payload: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
        if format:
            payload["format"] = format

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        message = data.get("message") or {}
        return str(message.get("content") or data.get("response") or "")

    async def status(self, model: str) -> dict:
        url = f"{self.base_url}/api/tags"
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        models = data.get("models", [])
        names = {item.get("name", "") for item in models}
        short_names = {name.split(":")[0] for name in names}
        model_available = model in names or model.split(":")[0] in short_names
        return {
            "ok": True,
            "base_url": self.base_url,
            "model": model,
            "model_available": model_available,
            "models": sorted(name for name in names if name),
        }


def _http_status_error_message(exc: httpx.HTTPStatusError) -> str:
    try:
        data = exc.response.json()
        if isinstance(data, dict) and data.get("error"):
            return str(data["error"])
    except (ValueError, httpx.ResponseNotRead):
        pass
    return f"Ollama returned HTTP {exc.response.status_code}"
