from __future__ import annotations

import base64
import json
import time
from typing import Any, AsyncIterator

import httpx
import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import service_account


class VertexGemmaStreamError(RuntimeError):
    """Raised when Vertex Gemma streaming fails at transport or payload level."""


class VertexGemmaClient:
    def __init__(
        self,
        project_id: str,
        location: str,
        model: str,
        timeout_seconds: float = 180,
    ) -> None:
        self.project_id = project_id
        self.location = location
        self.model = model
        self.timeout = timeout_seconds
        self._credentials = None
        self._token = ""
        self._token_expiry = 0.0

    @property
    def base_url(self) -> str:
        if self.location == "global":
            return (
                "https://aiplatform.googleapis.com/v1/"
                f"projects/{self.project_id}/locations/global/endpoints/openapi/chat/completions"
            )
        return (
            f"https://{self.location}-aiplatform.googleapis.com/v1/"
            f"projects/{self.project_id}/locations/{self.location}/endpoints/openapi/chat/completions"
        )

    async def stream_generate(self, model: str, prompt: str) -> AsyncIterator[str]:
        messages = [{"role": "user", "content": prompt}]
        payload = self._payload(model or self.model, messages, stream=True)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", self.base_url, headers=self._headers(), json=payload) as response:
                    if response.is_error:
                        await response.aread()
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        token = self._stream_line_token(line)
                        if token:
                            yield token
        except httpx.HTTPStatusError as exc:
            raise VertexGemmaStreamError(_http_status_error_message(exc)) from exc
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise VertexGemmaStreamError(str(exc) or "Vertex Gemma streaming failure") from exc

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        format: str | None = None,
    ) -> str:
        payload = self._payload(model or self.model, self._normalize_messages(messages), stream=False)
        if format == "json":
            payload["response_format"] = {"type": "json_object"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.base_url, headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        return str(message.get("content") or "")

    async def status(self, model: str) -> dict:
        self._access_token()
        return {
            "ok": True,
            "provider": "vertex_gemma",
            "provider_label": "Vertex Gemma",
            "base_url": self.base_url,
            "model": model or self.model,
            "model_available": True,
            "models": [model or self.model],
        }

    def _payload(self, model: str, messages: list[dict[str, Any]], *, stream: bool) -> dict[str, Any]:
        return {
            "model": model,
            "messages": messages,
            "max_tokens": 8192,
            "stream": stream,
        }

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token()}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _access_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expiry - 60:
            return self._token
        credentials = self._load_credentials()
        credentials.refresh(Request())
        self._token = credentials.token or ""
        expiry = credentials.expiry.timestamp() if credentials.expiry else now + 300
        self._token_expiry = expiry
        return self._token

    def _load_credentials(self):
        if self._credentials is not None:
            return self._credentials
        encoded = _credential_json_base64()
        if encoded:
            info = json.loads(base64.b64decode(encoded).decode("utf-8"))
            self._credentials = service_account.Credentials.from_service_account_info(
                info,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            return self._credentials
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        self._credentials = credentials
        return self._credentials

    def _normalize_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        system_text: list[str] = []
        for message in messages:
            role = str(message.get("role") or "user")
            content = str(message.get("content") or "")
            if role == "system":
                system_text.append(content)
                continue
            normalized.append(
                {
                    "role": role if role in {"user", "assistant"} else "user",
                    "content": _message_content(content, message.get("images") or []),
                }
            )
        if system_text:
            prefix = "System instructions:\n" + "\n\n".join(system_text).strip()
            if normalized and normalized[0]["role"] == "user":
                normalized[0]["content"] = _prepend_text(prefix, normalized[0]["content"])
            else:
                normalized.insert(0, {"role": "user", "content": prefix})
        return normalized or [{"role": "user", "content": ""}]

    def _stream_line_token(self, line: str) -> str:
        if not line or not line.startswith("data:"):
            return ""
        data = line.removeprefix("data:").strip()
        if not data or data == "[DONE]":
            return ""
        chunk = json.loads(data)
        choice = (chunk.get("choices") or [{}])[0]
        delta = choice.get("delta") or {}
        return str(delta.get("content") or "")


def _credential_json_base64() -> str:
    import os

    return os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64", "").strip()


def _message_content(text: str, images: list[str]) -> str | list[dict[str, Any]]:
    if not images:
        return text
    parts: list[dict[str, Any]] = []
    if text:
        parts.append({"type": "text", "text": text})
    for image in images:
        image_text = str(image or "").strip()
        if not image_text:
            continue
        parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_text}"}})
    return parts or text


def _prepend_text(prefix: str, content: str | list[dict[str, Any]]) -> str | list[dict[str, Any]]:
    if isinstance(content, str):
        return f"{prefix}\n\n{content}".strip()
    if content and content[0].get("type") == "text":
        content[0]["text"] = f"{prefix}\n\n{content[0].get('text', '')}".strip()
        return content
    return [{"type": "text", "text": prefix}, *content]


def _http_status_error_message(exc: httpx.HTTPStatusError) -> str:
    try:
        data = exc.response.json()
        if isinstance(data, dict):
            error = data.get("error")
            if isinstance(error, dict) and error.get("message"):
                return str(error["message"])
            if error:
                return str(error)
    except (ValueError, httpx.ResponseNotRead):
        pass
    return f"Vertex Gemma returned HTTP {exc.response.status_code}"
