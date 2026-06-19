from __future__ import annotations

from dataclasses import dataclass
import os


LOCAL_PROVIDERS = {"local", "ollama"}
INTERNET_PROVIDERS = {"internet", "openai"}
AUTO_PROVIDERS = {"auto"}
SUPPORTED_PROVIDERS = LOCAL_PROVIDERS | INTERNET_PROVIDERS | AUTO_PROVIDERS


@dataclass(frozen=True)
class HarnessConfig:
    provider: str = "auto"
    model: str = "qwen3.5:0.8b"
    base_url: str = "http://localhost:11434"
    api_key: str | None = None
    timeout: float = 120.0
    internet_model: str = "gpt-4o-mini"
    internet_base_url: str = "https://api.openai.com/v1"

    @classmethod
    def from_env(
        cls,
        *,
        provider: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
        internet_model: str | None = None,
        internet_base_url: str | None = None,
    ) -> "HarnessConfig":
        selected_provider = (provider or os.getenv("SMARTTHREADS_PROVIDER") or "auto").lower()
        selected_timeout = timeout
        if selected_timeout is None and os.getenv("SMARTTHREADS_TIMEOUT"):
            selected_timeout = float(os.environ["SMARTTHREADS_TIMEOUT"])

        selected_model = model or os.getenv("SMARTTHREADS_MODEL")
        selected_base_url = base_url or os.getenv("SMARTTHREADS_BASE_URL")
        selected_internet_model = internet_model or os.getenv("SMARTTHREADS_INTERNET_MODEL")
        selected_internet_base_url = internet_base_url or os.getenv("SMARTTHREADS_INTERNET_BASE_URL")

        if selected_provider in LOCAL_PROVIDERS or selected_provider in AUTO_PROVIDERS:
            selected_model = selected_model or "qwen3.5:0.8b"
            selected_base_url = selected_base_url or "http://localhost:11434"
        elif selected_provider in INTERNET_PROVIDERS:
            selected_model = selected_model or "gpt-4o-mini"
            selected_base_url = selected_base_url or "https://api.openai.com/v1"

        selected_internet_model = selected_internet_model or "gpt-4o-mini"
        selected_internet_base_url = selected_internet_base_url or "https://api.openai.com/v1"

        return cls(
            provider=selected_provider,
            model=selected_model or "qwen3.5:0.8b",
            base_url=(selected_base_url or "http://localhost:11434").rstrip("/"),
            api_key=api_key or os.getenv("SMARTTHREADS_API_KEY"),
            timeout=selected_timeout if selected_timeout is not None else 120.0,
            internet_model=selected_internet_model,
            internet_base_url=selected_internet_base_url.rstrip("/"),
        )

    @property
    def normalized_provider(self) -> str:
        if self.provider == "ollama":
            return "local"
        if self.provider == "openai":
            return "internet"
        return self.provider
