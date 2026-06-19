from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from smartthreads.config import HarnessConfig


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    model: str
    text: str
    raw: dict


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
            details = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"{self.provider_name} HTTP {exc.code}: {details}") from exc
        except URLError as exc:
            raise ProviderError(f"{self.provider_name} request failed: {exc.reason}") from exc

        try:
            return json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise ProviderError(f"{self.provider_name} returned invalid JSON") from exc
