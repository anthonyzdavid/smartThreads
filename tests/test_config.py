from smartthreads.config import HarnessConfig


def test_local_defaults(monkeypatch):
    monkeypatch.delenv("SMARTTHREADS_PROVIDER", raising=False)
    monkeypatch.delenv("SMARTTHREADS_MODEL", raising=False)
    monkeypatch.delenv("SMARTTHREADS_BASE_URL", raising=False)

    config = HarnessConfig.from_env()

    assert config.normalized_provider == "local"
    assert config.model == "qwen3.5:0.8b"
    assert config.base_url == "http://localhost:11434"


def test_internet_defaults(monkeypatch):
    monkeypatch.setenv("SMARTTHREADS_PROVIDER", "internet")
    monkeypatch.delenv("SMARTTHREADS_MODEL", raising=False)
    monkeypatch.delenv("SMARTTHREADS_BASE_URL", raising=False)

    config = HarnessConfig.from_env()

    assert config.normalized_provider == "internet"
    assert config.model == "gpt-4o-mini"
    assert config.base_url == "https://api.openai.com/v1"


def test_explicit_values_win(monkeypatch):
    monkeypatch.setenv("SMARTTHREADS_PROVIDER", "local")
    monkeypatch.setenv("SMARTTHREADS_MODEL", "env-model")

    config = HarnessConfig.from_env(provider="openai", model="flag-model", timeout=10)

    assert config.normalized_provider == "internet"
    assert config.model == "flag-model"
    assert config.timeout == 10
