from __future__ import annotations

from dataclasses import dataclass, field
from html import unescape
import json
import re
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from smartthreads.config import HarnessConfig
from smartthreads.costs import TokenUsage


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    model: str
    text: str
    raw: dict
    usage: TokenUsage = field(default_factory=TokenUsage)


class ProviderError(RuntimeError):
    pass


class BaseProvider:
    provider_name = "base"

    def __init__(self, config: HarnessConfig):
        self.config = config

    def generate(
        self,
        *,
        prompt: str,
        system: str | None,
        image_paths: Iterable[str],
    ) -> ProviderResponse:
        raise NotImplementedError

    def _post_json(
        self,
        url: str,
        payload: dict,
        headers: dict[str, str] | None = None,
    ) -> dict:
        body = json.dumps(payload).encode("utf-8")
        request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        request_headers.update(headers or {})

        request = Request(url, data=body, headers=request_headers, method="POST")
        try:
            with urlopen(request, timeout=self.config.timeout) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            details = _summarize_error_body(exc.read().decode("utf-8", errors="replace"))
            raise ProviderError(f"{self.provider_name} HTTP {exc.code} at {url}: {details}") from exc
        except URLError as exc:
            raise ProviderError(f"{self.provider_name} request failed: {exc.reason}") from exc

        try:
            return json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise ProviderError(f"{self.provider_name} returned invalid JSON") from exc


def _summarize_error_body(body: str) -> str:
    cleaned = body.strip()
    lowered = cleaned.lower()
    if "<html" in lowered:
        if "cf_chl" in lowered or "challenge-platform" in lowered or "enable javascript" in lowered:
            return (
                "received an HTML security challenge page instead of API JSON. "
                "Check the Base URL; for OpenAI use https://api.openai.com/v1, "
                "not platform.openai.com or ChatGPT URLs."
            )
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = unescape(cleaned)

    cleaned = " ".join(cleaned.split())
    if len(cleaned) > 500:
        return cleaned[:497] + "..."
    return cleaned
