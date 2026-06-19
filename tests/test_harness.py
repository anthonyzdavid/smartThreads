import pytest

from smartthreads.config import HarnessConfig
from smartthreads.harness import AIHarness, HarnessError
from smartthreads.providers import OllamaProvider, OpenAICompatibleProvider, ProviderError


def test_harness_selects_ollama_for_local():
    harness = AIHarness(HarnessConfig(provider="local"))

    assert isinstance(harness.provider, OllamaProvider)


def test_harness_selects_openai_compatible_for_internet():
    harness = AIHarness(HarnessConfig.from_env(provider="internet", api_key="token"))

    assert isinstance(harness.provider, OpenAICompatibleProvider)


def test_harness_wraps_provider_errors(monkeypatch):
    def fake_generate(self, prompt, system, image_paths):
        raise ProviderError("boom")

    monkeypatch.setattr(OllamaProvider, "generate", fake_generate)
    harness = AIHarness(HarnessConfig(provider="local"))

    with pytest.raises(HarnessError, match="boom"):
        harness.ask(prompt="ping")
