from __future__ import annotations

import time
from typing import Iterable

from smartthreads.costs import usage_from_openai

from .base import BaseProvider, ProviderError, ProviderResponse
from .images import image_data_url


class OpenAICompatibleProvider(BaseProvider):
    provider_name = "internet"

    def generate(
        self,
        *,
        prompt: str,
        system: str | None,
        image_paths: Iterable[str],
    ) -> ProviderResponse:
        if not self.config.api_key:
            raise ProviderError("SMARTTHREADS_API_KEY or --api-key is required for internet providers")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": self._user_content(prompt, image_paths)})

        start = time.monotonic()
        raw = self._post_json(
            f"{self.config.base_url}/chat/completions",
            {"model": self.config.model, "messages": messages},
            {"Authorization": f"Bearer {self.config.api_key}"},
        )
        elapsed_seconds = time.monotonic() - start

        try:
            text = raw["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("internet provider response did not include message content") from exc
        if not text:
            raise ProviderError("internet provider returned an empty response")

        return ProviderResponse(
            provider=self.provider_name,
            model=self.config.model,
            text=text,
            raw=raw,
            usage=usage_from_openai(self.config.model, raw.get("usage"), elapsed_seconds),
        )

    def _user_content(self, prompt: str, image_paths: Iterable[str]) -> str | list[dict]:
        image_paths = tuple(image_paths)
        if not image_paths:
            return prompt

        content: list[dict] = [{"type": "text", "text": prompt}]
        for path in image_paths:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{image_data_url(path)}"},
                }
            )
        return content
