from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
import mimetypes
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import webbrowser

from smartthreads.config import HarnessConfig
from smartthreads.harness import AIHarness, HarnessError
from smartthreads.providers import ProviderError
from smartthreads.providers.openai_compatible import normalize_openai_compatible_base_url


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_BODY_BYTES = 2 * 1024 * 1024


def config_from_payload(payload: dict) -> HarnessConfig:
    provider = _empty_to_none(payload.get("force_provider")) or _empty_to_none(payload.get("provider"))
    model = _empty_to_none(payload.get("model"))
    base_url = _empty_to_none(payload.get("base_url"))
    if provider in ("internet", "openai") and payload.get("force_provider"):
        model = _empty_to_none(payload.get("internet_model")) or model
        base_url = _empty_to_none(payload.get("internet_base_url")) or base_url

    timeout = payload.get("timeout")
    if timeout in ("", None):
        timeout = None

    return HarnessConfig.from_env(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=_empty_to_none(payload.get("api_key")),
        timeout=float(timeout) if timeout is not None else None,
        internet_model=_empty_to_none(payload.get("internet_model")),
        internet_base_url=_empty_to_none(payload.get("internet_base_url")),
    )


def config_payload(config: HarnessConfig) -> dict:
    body = asdict(config)
    body["api_key"] = ""
    body["has_api_key"] = bool(config.api_key)
    body["provider"] = config.normalized_provider
    return body


def create_handler(
    harness_factory: Callable[[HarnessConfig], AIHarness] = AIHarness,
) -> type[BaseHTTPRequestHandler]:
    class SmartThreadsHandler(BaseHTTPRequestHandler):
        server_version = "smartThreads/0.1"

        def do_GET(self) -> None:
            if self.path == "/api/config":
                self._send_json(config_payload(HarnessConfig.from_env()))
                return

            if self.path in ("/", "/index.html"):
                self._send_static("index.html")
                return
            if self.path == "/app.js":
                self._send_static("app.js")
                return
            if self.path == "/style.css":
                self._send_static("style.css")
                return

            self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            if self.path != "/api/chat":
                if self.path == "/api/models":
                    self._handle_models()
                    return
                self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
                return

            try:
                payload = self._read_json()
                prompt = str(payload.get("prompt", "")).strip()
                if not prompt:
                    self._send_json({"error": "prompt is required"}, status=HTTPStatus.BAD_REQUEST)
                    return

                config = config_from_payload(payload)
                result = harness_factory(config).ask(
                    prompt=prompt,
                    system=_empty_to_none(payload.get("system")),
                    image_paths=payload.get("image_paths") or (),
                )
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            except HarnessError as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_GATEWAY)
                return

            self._send_json(result.to_dict())

        def _handle_models(self) -> None:
            try:
                payload = self._read_json()
                config = config_from_payload(payload)
                self._send_json(discover_models(config))
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            except HarnessError as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_GATEWAY)

        def log_message(self, format: str, *args) -> None:
            return

        def _read_json(self) -> dict:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length > MAX_BODY_BYTES:
                raise ValueError("request body is too large")

            body = self.rfile.read(content_length)
            try:
                decoded = body.decode("utf-8")
                payload = json.loads(decoded) if decoded else {}
            except json.JSONDecodeError as exc:
                raise ValueError("request body must be valid JSON") from exc

            if not isinstance(payload, dict):
                raise ValueError("request body must be a JSON object")
            return payload

        def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status.value)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_static(self, filename: str) -> None:
            static_file = resources.files("smartthreads.web").joinpath("static", filename)
            if not static_file.is_file():
                self._send_json({"error": "asset not found"}, status=HTTPStatus.NOT_FOUND)
                return

            body = static_file.read_bytes()
            content_type, _ = mimetypes.guess_type(filename)
            self.send_response(HTTPStatus.OK.value)
            self.send_header("Content-Type", content_type or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return SmartThreadsHandler


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, open_browser: bool = False) -> None:
    server = ThreadingHTTPServer((host, port), create_handler())
    url = f"http://{host}:{server.server_port}"
    print(f"smartThreads web app running at {url}")
    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nsmartThreads web app stopped")
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the smartThreads local web app.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--open", action="store_true", help="Open the app in the default browser.")
    args = parser.parse_args(argv)

    serve(host=args.host, port=args.port, open_browser=args.open)
    return 0


def _empty_to_none(value):
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value


def discover_models(config: HarnessConfig) -> dict:
    local = _discover_ollama(config)
    internet_config = HarnessConfig.from_env(
        provider="internet",
        model=config.internet_model,
        base_url=config.internet_base_url,
        api_key=config.api_key,
        timeout=config.timeout,
    )
    internet = _discover_openai_compatible(internet_config)
    return {
        "local": local,
        "internet": internet,
    }


def _discover_ollama(config: HarnessConfig) -> dict:
    try:
        raw = _get_json(f"{config.base_url}/api/tags", timeout=config.timeout)
    except HarnessError as exc:
        return {
            "verified": False,
            "error": str(exc),
            "models": [],
        }

    models = []
    for item in raw.get("models", []):
        name = item.get("name") or item.get("model")
        if name:
            models.append(
                {
                    "id": name,
                    "size": item.get("size"),
                    "modified_at": item.get("modified_at"),
                }
            )

    return {
        "verified": True,
        "models": models,
    }


def _discover_openai_compatible(config: HarnessConfig) -> dict:
    if not config.api_key:
        return {
            "verified": False,
            "error": "API key is required to verify internet models.",
            "models": [],
        }

    try:
        base_url = normalize_openai_compatible_base_url(config.base_url)
        raw = _get_json(
            f"{base_url}/models",
            timeout=config.timeout,
            headers={"Authorization": f"Bearer {config.api_key}"},
        )
    except (HarnessError, ProviderError) as exc:
        return {
            "verified": False,
            "error": str(exc),
            "models": [],
        }

    models = []
    for item in raw.get("data", []):
        model_id = item.get("id")
        if model_id:
            models.append({"id": model_id, "owner": item.get("owned_by")})

    return {
        "verified": True,
        "models": models,
    }


def _get_json(url: str, *, timeout: float, headers: dict[str, str] | None = None) -> dict:
    request_headers = {"Accept": "application/json"}
    request_headers.update(headers or {})
    request = Request(url, headers=request_headers, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        from smartthreads.providers.base import _summarize_error_body

        details = _summarize_error_body(exc.read().decode("utf-8", errors="replace"))
        raise HarnessError(f"model discovery HTTP {exc.code} at {url}: {details}") from exc
    except URLError as exc:
        raise HarnessError(f"model discovery failed: {exc.reason}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise HarnessError("model discovery returned invalid JSON") from exc
