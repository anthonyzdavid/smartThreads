from smartthreads.cli import main
from smartthreads.harness import HarnessResult


def test_cli_prints_text(monkeypatch, capsys):
    def fake_ask(self, prompt, system=None, image_paths=()):
        return HarnessResult(provider="local", model="m", text="hello", raw={"ok": True})

    monkeypatch.setattr("smartthreads.cli.AIHarness.ask", fake_ask)

    assert main(["--prompt", "ping"]) == 0

    captured = capsys.readouterr()
    assert captured.out == "hello\n"


def test_cli_prints_json(monkeypatch, capsys):
    def fake_ask(self, prompt, system=None, image_paths=()):
        return HarnessResult(provider="local", model="m", text="hello", raw={"ok": True})

    monkeypatch.setattr("smartthreads.cli.AIHarness.ask", fake_ask)

    assert main(["--prompt", "ping", "--json"]) == 0

    captured = capsys.readouterr()
    assert '"provider": "local"' in captured.out
    assert '"text": "hello"' in captured.out
