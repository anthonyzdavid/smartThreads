from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .config import HarnessConfig, SUPPORTED_PROVIDERS
from .providers import OpenAICompatibleProvider, OllamaProvider, ProviderError


class HarnessError(RuntimeError):
    """Raised when smartThreads cannot satisfy a model request."""


@dataclass(frozen=True)
class HarnessResult:
    provider: str
    model: str
    text: str
    raw: dict

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "text": self.text,
            "raw": self.raw,
        }


class AIHarness:
    def __init__(self, config: HarnessConfig | None = None):
        self.config = config or HarnessConfig.from_env()
        self.provider = self._build_provider(self.config)

    def ask(
        self,
        *,
        prompt: str,
        system: str | None = None,
        image_paths: Iterable[str] = (),
    ) -> HarnessResult:
        try:
            response = self.provider.generate(
                prompt=prompt,
                system=system,
                image_paths=tuple(image_paths),
            )
        except ProviderError as exc:
            raise HarnessError(str(exc)) from exc

        return HarnessResult(
            provider=response.provider,
            model=response.model,
            text=response.text,
            raw=response.raw,
        )

    def _build_provider(self, config: HarnessConfig):
        if config.provider not in SUPPORTED_PROVIDERS:
            supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
            raise HarnessError(f"unsupported provider '{config.provider}', expected one of: {supported}")

        if config.normalized_provider == "local":
            return OllamaProvider(config)
        if config.normalized_provider == "internet":
            return OpenAICompatibleProvider(config)

        raise HarnessError(f"unsupported provider '{config.provider}'")
