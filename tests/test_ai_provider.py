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
    assert current_ai_model("vertex_gemma") == "gemma-4-26b-a4b-it-maas"
