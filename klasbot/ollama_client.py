from __future__ import annotations

import json
from typing import AsyncIterator

import httpx


class OllamaClient:
    def __init__(self, base_url: str, timeout_seconds: float = 180) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds

    async def stream_generate(self, model: str, prompt: str) -> AsyncIterator[str]:
        url = f"{self.base_url}/api/generate"
        payload = {"model": model, "prompt": prompt, "stream": True}

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
                        break

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
