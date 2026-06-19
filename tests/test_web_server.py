import http.client
import json
import threading
from http.server import ThreadingHTTPServer

from smartthreads.config import HarnessConfig
from smartthreads.harness import HarnessResult
from smartthreads.web.server import config_from_payload, create_handler


def test_config_from_payload_uses_provider_defaults(monkeypatch):
    monkeypatch.delenv("SMARTTHREADS_MODEL", raising=False)
    config = config_from_payload({"provider": "internet", "timeout": "8"})

    assert config.normalized_provider == "internet"
    assert config.model == "gpt-4o-mini"
    assert config.timeout == 8


def test_get_index_serves_app():
    with run_test_server() as server:
        connection = http.client.HTTPConnection(server.host, server.port)
        connection.request("GET", "/")
        response = connection.getresponse()
        body = response.read().decode("utf-8")

    assert response.status == 200
    assert "smartThreads" in body
    assert "Chat Router" in body


def test_post_chat_routes_to_harness():
    seen = {}

    class FakeHarness:
        def __init__(self, config: HarnessConfig):
            seen["config"] = config

        def ask(self, prompt, system=None, image_paths=()):
            seen["prompt"] = prompt
            seen["system"] = system
            return HarnessResult(provider="local", model="m", text="done", raw={"ok": True})

    with run_test_server(FakeHarness) as server:
        connection = http.client.HTTPConnection(server.host, server.port)
        connection.request(
            "POST",
            "/api/chat",
            body=json.dumps({"provider": "local", "prompt": "hello", "system": "sys"}),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        body = json.loads(response.read().decode("utf-8"))

    assert response.status == 200
    assert body["text"] == "done"
    assert seen["prompt"] == "hello"
    assert seen["system"] == "sys"
    assert seen["config"].normalized_provider == "local"


class run_test_server:
    def __init__(self, harness_factory=None):
        handler = create_handler(harness_factory) if harness_factory else create_handler()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.host, self.port = self.server.server_address
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
