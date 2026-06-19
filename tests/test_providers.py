import base64

import pytest

from smartthreads.config import HarnessConfig
from smartthreads.providers import OllamaProvider, OpenAICompatibleProvider, ProviderError


def test_ollama_payload_includes_base64_image(monkeypatch, tmp_path):
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"jpg-bytes")
    seen = {}

    def fake_post(self, url, payload, headers=None):
        seen["url"] = url
        seen["payload"] = payload
        return {"message": {"content": "TRACKING"}}

    monkeypatch.setattr(OllamaProvider, "_post_json", fake_post)

    provider = OllamaProvider(HarnessConfig())
    response = provider.generate(prompt="scan", system="sys", image_paths=[str(image)])

    assert response.text == "TRACKING"
    assert seen["url"] == "http://localhost:11434/api/chat"
    assert seen["payload"]["messages"][1]["images"] == [
        base64.b64encode(b"jpg-bytes").decode("ascii")
    ]


def test_openai_compatible_payload(monkeypatch):
    seen = {}

    def fake_post(self, url, payload, headers=None):
        seen["url"] = url
        seen["payload"] = payload
        seen["headers"] = headers
        return {"choices": [{"message": {"content": "clear"}}]}

    monkeypatch.setattr(OpenAICompatibleProvider, "_post_json", fake_post)

    config = HarnessConfig.from_env(
        provider="internet",
        model="model-a",
        base_url="https://llm.example/v1",
        api_key="token",
    )
    provider = OpenAICompatibleProvider(config)
    response = provider.generate(prompt="scan", system=None, image_paths=[])

    assert response.text == "clear"
    assert seen["url"] == "https://llm.example/v1/chat/completions"
    assert seen["payload"] == {
        "model": "model-a",
        "messages": [{"role": "user", "content": "scan"}],
    }
    assert seen["headers"] == {"Authorization": "Bearer token"}


def test_openai_requires_api_key():
    config = HarnessConfig.from_env(provider="internet", api_key=None)
    provider = OpenAICompatibleProvider(config)

    with pytest.raises(ProviderError, match="API_KEY"):
        provider.generate(prompt="scan", system=None, image_paths=[])
