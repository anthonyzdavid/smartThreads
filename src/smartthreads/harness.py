from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
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
    route_reason: str | None = None
    attempted_providers: tuple[str, ...] = ()
    usage: dict | None = None

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "text": self.text,
            "raw": self.raw,
            "route_reason": self.route_reason,
            "attempted_providers": list(self.attempted_providers),
            "usage": self.usage or {},
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
        image_paths = tuple(image_paths)
        if self.config.normalized_provider == "auto":
            return self._ask_auto(prompt=prompt, system=system, image_paths=image_paths)

        try:
            response = self.provider.generate(
                prompt=prompt,
                system=system,
                image_paths=image_paths,
            )
        except ProviderError as exc:
            raise HarnessError(str(exc)) from exc

        return HarnessResult(
            provider=response.provider,
            model=response.model,
            text=response.text,
            raw=response.raw,
            attempted_providers=(response.provider,),
            usage=response.usage.to_dict(),
        )

    def _build_provider(self, config: HarnessConfig):
        if config.provider not in SUPPORTED_PROVIDERS:
            supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
            raise HarnessError(f"unsupported provider '{config.provider}', expected one of: {supported}")

        if config.normalized_provider == "local":
            return OllamaProvider(config)
        if config.normalized_provider == "internet":
            return OpenAICompatibleProvider(config)
        if config.normalized_provider == "auto":
            return OllamaProvider(replace(config, provider="local"))

        raise HarnessError(f"unsupported provider '{config.provider}'")

    def _ask_auto(
        self,
        *,
        prompt: str,
        system: str | None,
        image_paths: tuple[str, ...],
    ) -> HarnessResult:
        local_config = replace(self.config, provider="local")
        internet_config = replace(
            self.config,
            provider="internet",
            model=self.config.internet_model,
            base_url=self.config.internet_base_url,
        )
        attempted = ["local"]

        try:
            local_response = OllamaProvider(local_config).generate(
                prompt=prompt,
                system=system,
                image_paths=image_paths,
            )
        except ProviderError as exc:
            return self._ask_internet_after_local_failure(
                internet_config=internet_config,
                prompt=prompt,
                system=system,
                image_paths=image_paths,
                local_error=exc,
                attempted=attempted,
            )

        escalation_reason = should_escalate(prompt, local_response.text)
        if escalation_reason:
            attempted.append("internet")
            try:
                internet_response = OpenAICompatibleProvider(internet_config).generate(
                    prompt=prompt,
                    system=system,
                    image_paths=image_paths,
                )
            except ProviderError as exc:
                return HarnessResult(
                    provider=local_response.provider,
                    model=local_response.model,
                    text=local_response.text,
                    raw={
                        "local": local_response.raw,
                        "internet_error": str(exc),
                    },
                    route_reason=f"Kept local answer; internet fallback failed after: {escalation_reason}",
                    attempted_providers=tuple(attempted),
                    usage=local_response.usage.to_dict(),
                )

            return HarnessResult(
                provider=internet_response.provider,
                model=internet_response.model,
                text=internet_response.text,
                raw={
                    "local": local_response.raw,
                    "internet": internet_response.raw,
                },
                route_reason=f"Escalated from local: {escalation_reason}",
                attempted_providers=tuple(attempted),
                usage=internet_response.usage.to_dict(),
            )

        return HarnessResult(
            provider=local_response.provider,
            model=local_response.model,
            text=local_response.text,
            raw=local_response.raw,
            route_reason="Local answer looked sufficient",
            attempted_providers=tuple(attempted),
            usage=local_response.usage.to_dict(),
        )

    def _ask_internet_after_local_failure(
        self,
        *,
        internet_config: HarnessConfig,
        prompt: str,
        system: str | None,
        image_paths: tuple[str, ...],
        local_error: ProviderError,
        attempted: list[str],
    ) -> HarnessResult:
        attempted.append("internet")
        try:
            internet_response = OpenAICompatibleProvider(internet_config).generate(
                prompt=prompt,
                system=system,
                image_paths=image_paths,
            )
        except ProviderError as exc:
            raise HarnessError(
                f"local failed ({local_error}); internet fallback failed ({exc})"
            ) from exc

        return HarnessResult(
            provider=internet_response.provider,
            model=internet_response.model,
            text=internet_response.text,
            raw={
                "local_error": str(local_error),
                "internet": internet_response.raw,
            },
            route_reason=f"Escalated because local failed: {local_error}",
            attempted_providers=tuple(attempted),
            usage=internet_response.usage.to_dict(),
        )


def should_escalate(prompt: str, response_text: str) -> str | None:
    normalized_response = response_text.lower().strip()
    normalized_prompt = prompt.lower()
    weak_markers = (
        "i don't know",
        "i do not know",
        "i can't",
        "i cannot",
        "unable to",
        "not enough context",
        "insufficient context",
        "as an ai language model",
        "i'm not sure",
        "i am not sure",
    )
    for marker in weak_markers:
        if marker in normalized_response:
            return f"local response contained '{marker}'"

    complex_markers = (
        "analyze",
        "architecture",
        "debug",
        "explain",
        "implement",
        "plan",
        "refactor",
        "review",
        "summarize",
    )
    if len(prompt) > 240 and len(response_text.strip()) < 80:
        if any(marker in normalized_prompt for marker in complex_markers):
            return "local response was very short for a complex prompt"

    if len(prompt) > 1800 and len(response_text.strip()) < 180:
        return "local response was too short for a large prompt"

    return None
