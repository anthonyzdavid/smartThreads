import pytest

from smartthreads.config import HarnessConfig
from smartthreads.harness import AIHarness, HarnessError, should_escalate
from smartthreads.providers import (
    OllamaProvider,
    OpenAICompatibleProvider,
    ProviderError,
    ProviderResponse,
)


def test_harness_selects_ollama_for_local():
    harness = AIHarness(HarnessConfig(provider="local"))

    assert isinstance(harness.provider, OllamaProvider)


def test_harness_selects_openai_compatible_for_internet():
    harness = AIHarness(HarnessConfig.from_env(provider="internet", api_key="token"))

    assert isinstance(harness.provider, OpenAICompatibleProvider)


def test_harness_selects_ollama_for_auto():
    harness = AIHarness(HarnessConfig(provider="auto"))

    assert isinstance(harness.provider, OllamaProvider)


def test_harness_wraps_provider_errors(monkeypatch):
    def fake_generate(self, prompt, system, image_paths):
        raise ProviderError("boom")

    monkeypatch.setattr(OllamaProvider, "generate", fake_generate)
    harness = AIHarness(HarnessConfig(provider="local"))

    with pytest.raises(HarnessError, match="boom"):
        harness.ask(prompt="ping")


def test_auto_keeps_sufficient_local_answer(monkeypatch):
    def fake_local(self, prompt, system, image_paths):
        return ProviderResponse("local", "local-model", "This is a useful local answer.", {"ok": True})

    monkeypatch.setattr(OllamaProvider, "generate", fake_local)
    harness = AIHarness(HarnessConfig(provider="auto", api_key="token"))

    result = harness.ask(prompt="small question")

    assert result.provider == "local"
    assert result.attempted_providers == ("local",)
    assert result.route_reason == "Local answer looked sufficient"


def test_auto_escalates_weak_local_answer(monkeypatch):
    def fake_local(self, prompt, system, image_paths):
        return ProviderResponse("local", "local-model", "I don't know.", {"local": True})

    def fake_internet(self, prompt, system, image_paths):
        return ProviderResponse("internet", "cloud-model", "Cloud answer", {"cloud": True})

    monkeypatch.setattr(OllamaProvider, "generate", fake_local)
    monkeypatch.setattr(OpenAICompatibleProvider, "generate", fake_internet)
    config = HarnessConfig(
        provider="auto",
        api_key="token",
        internet_model="cloud-model",
        internet_base_url="https://cloud.example/v1",
    )

    result = AIHarness(config).ask(prompt="Analyze this tricky thing")

    assert result.provider == "internet"
    assert result.model == "cloud-model"
    assert result.text == "Cloud answer"
    assert result.attempted_providers == ("local", "internet")
    assert "Escalated from local" in result.route_reason


def test_auto_raises_when_both_providers_fail(monkeypatch):
    def fake_local(self, prompt, system, image_paths):
        raise ProviderError("local down")

    def fake_internet(self, prompt, system, image_paths):
        raise ProviderError("cloud down")

    monkeypatch.setattr(OllamaProvider, "generate", fake_local)
    monkeypatch.setattr(OpenAICompatibleProvider, "generate", fake_internet)
    harness = AIHarness(HarnessConfig(provider="auto", api_key="token"))

    with pytest.raises(HarnessError, match="local failed"):
        harness.ask(prompt="ping")


def test_should_escalate_for_weak_marker():
    assert should_escalate("question", "I cannot help with that") is not None
