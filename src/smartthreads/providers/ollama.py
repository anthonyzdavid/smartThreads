from __future__ import annotations

import time
from typing import Iterable

from smartthreads.costs import usage_from_ollama

from .base import BaseProvider, ProviderError, ProviderResponse
from .images import read_image_base64


class OllamaProvider(BaseProvider):
    provider_name = "local"

    def generate(
        self,
        *,
        prompt: str,
        system: str | None,
        image_paths: Iterable[str],
    ) -> ProviderResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})

        user_message = {"role": "user", "content": prompt}
        images = [read_image_base64(path) for path in image_paths]
        if images:
            user_message["images"] = images
        messages.append(user_message)

        start = time.monotonic()
        raw = self._post_json(
            f"{self.config.base_url}/api/chat",
            {
                "model": self.config.model,
                "messages": messages,
                "stream": False,
                "keep_alive": "15m",
            },
        )
        elapsed_seconds = time.monotonic() - start
        text = raw.get("message", {}).get("content", "").strip()
        if not text:
            raise ProviderError("local provider returned an empty response")

        return ProviderResponse(
            provider=self.provider_name,
            model=self.config.model,
            text=text,
            raw=raw,
            usage=usage_from_ollama(raw, elapsed_seconds),
        )
