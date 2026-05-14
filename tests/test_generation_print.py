from __future__ import annotations

import httpx

from tests.conftest import login


class FakeOllama:
    async def stream_generate(self, model, prompt):
        yield "Line one\nLine two"


class BrokenOllama:
    async def stream_generate(self, model, prompt):
        if False:
            yield ""
        raise httpx.ConnectError("offline")

    async def status(self, model):
        raise httpx.ConnectError("offline")


class StatusOllama:
    async def status(self, model):
        return {
            "ok": True,
            "base_url": "http://127.0.0.1:11434",
            "model": model,
            "model_available": True,
            "models": [model],
        }


class UnreadStream(httpx.AsyncByteStream):
    async def __aiter__(self):
        yield b'{"error":"unread"}'


def test_generation_sse_preserves_multiline_tokens(client, monkeypatch):
    from klasbot import main

    login(client)
    monkeypatch.setattr(main, "ollama_client", FakeOllama())

    with client.stream(
        "GET",
        "/api/generate/stream?kind=lesson_plan&format=DLP&subject=Math&topic=Fractions",
    ) as response:
        body = response.read().decode()

    assert response.status_code == 200
    assert "data: Line one\ndata: Line two" in body
    assert "event: done" in body


def test_ollama_status_reports_connection(client, monkeypatch):
    from klasbot import main

    login(client)
    monkeypatch.setattr(main, "ollama_client", StatusOllama())

    response = client.get("/api/ollama/status")

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["model_available"] is True


def test_ollama_status_handles_connection_failure(client, monkeypatch):
    from klasbot import main

    login(client)
    monkeypatch.setattr(main, "ollama_client", BrokenOllama())

    response = client.get("/api/ollama/status")

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert response.json()["model_available"] is False


def test_generation_empty_input_validation(client):
    login(client)

    with client.stream("GET", "/api/generate/stream?subject=Math") as response:
        body = response.read().decode()

    assert "Please enter both subject and topic" in body
    assert "event: done" in body


def test_prompt_preview_disabled_by_default(client):
    login(client)

    assert client.get("/api/dev/prompt-preview/enabled").json() == {"enabled": False}
    response = client.post(
        "/api/dev/prompt-preview",
        json={
            "kind": "lesson_plan",
            "format": "DLP",
            "subject": "Science",
            "topic": "MATERIALS",
            "grade_level": "Grade 3",
            "quarter": 1,
            "grade_levels": ["Grade 3"],
            "resources": [],
        },
    )

    assert response.status_code == 404


def test_prompt_preview_enabled_for_admin(client, monkeypatch):
    from klasbot import main

    login(client)
    monkeypatch.setattr(main, "PROMPT_PREVIEW_ENABLED", True)
    monkeypatch.setattr(main.curriculum, "build_curriculum_context", lambda inputs: "Science context")

    response = client.post(
        "/api/dev/prompt-preview",
        json={
            "kind": "lesson_plan",
            "format": "DLP",
            "subject": "Science",
            "topic": "MATERIALS",
            "grade_level": "Grade 3",
            "quarter": 1,
            "grade_levels": ["Grade 3"],
            "resources": ["paper"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "Science context" in data["prompt"]
    assert data["prompt_chars"] == len(data["prompt"])


def test_generation_fallback_when_ollama_unavailable(client, monkeypatch):
    from klasbot import main

    login(client)
    monkeypatch.setattr(main, "ollama_client", BrokenOllama())

    with client.stream(
        "GET",
        "/api/generate/stream?kind=lesson_plan&format=DLP&subject=Math&topic=Fractions",
    ) as response:
        body = response.read().decode()

    assert "Ollama generation failed" in body
    assert "# Draft Lesson Plan" in body


def test_ollama_error_message_reads_buffered_stream_error():
    from klasbot.main import _ollama_error_message

    request = httpx.Request("POST", "http://127.0.0.1:11434/api/generate")
    response = httpx.Response(
        500,
        json={"error": "model requires more system memory"},
        request=request,
    )
    exc = httpx.HTTPStatusError("server error", request=request, response=response)

    assert _ollama_error_message(exc) == "model requires more system memory"


def test_ollama_error_message_handles_unread_stream_error():
    from klasbot.main import _ollama_error_message

    request = httpx.Request("POST", "http://127.0.0.1:11434/api/generate")

    response = httpx.Response(500, stream=UnreadStream(), request=request)
    exc = httpx.HTTPStatusError("server error", request=request, response=response)

    assert _ollama_error_message(exc) == "Ollama returned HTTP 500"


def test_stream_generate_wraps_http_status_errors(monkeypatch):
    from klasbot.ollama_client import OllamaClient, OllamaStreamError

    class FakeStream:
        async def __aenter__(self):
            request = httpx.Request("POST", "http://ollama.test/api/generate")
            return httpx.Response(500, json={"error": "model is unavailable"}, request=request)

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        def stream(self, method, url, json):
            return FakeStream()

    import pytest
    import anyio

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    client = OllamaClient("http://ollama.test")
    with pytest.raises(OllamaStreamError, match="model is unavailable"):
        async def run():
            async for _ in client.stream_generate("gemma4:e2b", "hello"):
                pass

        anyio.run(run)


def test_print_success_and_fallback(client, monkeypatch):
    from klasbot import main

    login(client)
    monkeypatch.setattr(main, "print_html", lambda html: {"printed": True, "fallback": False, "reason": "ok"})
    response = client.post(
        "/api/print",
        json={"content_md": "# Title", "metadata": {"subject": "Math", "topic": "Fractions"}},
    )
    assert response.status_code == 200
    assert response.json()["printed"] is True

    monkeypatch.setattr(
        main,
        "print_html",
        lambda html: {"printed": False, "fallback": True, "reason": "missing"},
    )
    response = client.post(
        "/api/print",
        json={"content_md": "# Title", "metadata": {"subject": "Math", "topic": "Fractions"}},
    )
    assert response.status_code == 200
    assert response.json()["fallback"] is True
    assert "<html" in response.json()["html"]


def test_print_markdown_tables_render_as_tables():
    from klasbot.print_utils import markdown_to_html

    html = markdown_to_html(
        """# Plan

| Procedure Step | Teacher Activity | Learner Activity |
| --- | --- | --- |
| Review | Ask questions | Answer orally |
| Activity | Give materials | Work in groups |
"""
    )

    assert "<table>" in html
    assert "<th>Procedure Step</th>" in html
    assert "<td>Give materials</td>" in html
    assert "| --- |" not in html


def test_print_html_preserves_latex_for_katex_and_fallback():
    from klasbot.print_utils import markdown_to_html, render_print_html

    body = markdown_to_html("Example: $\\triangle ABC$ and $\\frac{1}{2}mv^2$.")
    page = render_print_html("Example: $\\triangle ABC$ and $\\frac{1}{2}mv^2$.", {"topic": "Energy"})

    assert 'data-latex="\\triangle ABC"' in body
    assert "triangle ABC" in body
    assert "/static/vendor/katex/katex.min.js" in page
    assert "/static/vendor/katex/katex.min.css" in page


def test_print_rejects_missing_output(client):
    login(client)

    response = client.post("/api/print", json={"output_id": 999})

    assert response.status_code == 404
