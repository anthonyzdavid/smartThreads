from smartthreads.config import HarnessConfig


def test_auto_defaults(monkeypatch):
    monkeypatch.delenv("SMARTTHREADS_PROVIDER", raising=False)
    monkeypatch.delenv("SMARTTHREADS_MODEL", raising=False)
    monkeypatch.delenv("SMARTTHREADS_BASE_URL", raising=False)
    monkeypatch.delenv("SMARTTHREADS_INTERNET_MODEL", raising=False)
    monkeypatch.delenv("SMARTTHREADS_INTERNET_BASE_URL", raising=False)

    config = HarnessConfig.from_env()

    assert config.normalized_provider == "auto"
    assert config.model == "qwen3.5:0.8b"
    assert config.base_url == "http://localhost:11434"
    assert config.internet_model == "gpt-4o-mini"
    assert config.internet_base_url == "https://api.openai.com/v1"


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


def test_internet_fallback_values_can_be_set(monkeypatch):
    monkeypatch.setenv("SMARTTHREADS_INTERNET_MODEL", "cloud-model")
    monkeypatch.setenv("SMARTTHREADS_INTERNET_BASE_URL", "https://cloud.example/v1")

    config = HarnessConfig.from_env(provider="auto")

    assert config.internet_model == "cloud-model"
    assert config.internet_base_url == "https://cloud.example/v1"
