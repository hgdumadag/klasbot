from __future__ import annotations


def test_ai_provider_defaults_to_ollama():
    from klasbot.ai_provider import create_ai_client, current_ai_model
    from klasbot.ollama_client import OllamaClient

    assert isinstance(create_ai_client("ollama"), OllamaClient)
    assert current_ai_model("ollama") == "gemma4:e2b"


def test_ai_provider_can_select_vertex_gemma():
    from klasbot.ai_provider import create_ai_client, current_ai_model
    from klasbot.vertex_gemma_client import VertexGemmaClient

    client = create_ai_client("vertex_gemma")

    assert isinstance(client, VertexGemmaClient)
    assert current_ai_model("vertex_gemma") == "google/gemma-4-26b-a4b-it-maas"


def test_vertex_gemma_model_name_is_normalized(monkeypatch):
    from klasbot.ai_provider import _vertex_model_name

    assert _vertex_model_name("gemma-4-26b-a4b-it-maas") == "google/gemma-4-26b-a4b-it-maas"
    assert _vertex_model_name("google/gemma-4-26b-a4b-it-maas") == "google/gemma-4-26b-a4b-it-maas"
