# smartThreads

`smartThreads` is a lightweight Python AI harness for switching between local
LLMs and internet-hosted LLMs without changing the calling code.

The first supported backends are:

- `local` / `ollama`: Ollama's local `/api/chat` endpoint.
- `internet` / `openai`: OpenAI-compatible `/v1/chat/completions` endpoints.

## Quick Start
https://www.youtube.com/watch?v=1a1VXDdIyrk

Run the local web app:

```bash
python3 -m smartthreads.web
```

Then open:

```text
http://127.0.0.1:8765
```

Run against local Ollama:

```bash
python3 -m smartthreads --provider local --model qwen3.5:0.8b \
  --prompt "Give me a one-line project status."
```

Run against an internet provider:

```bash
export SMARTTHREADS_PROVIDER=internet
export SMARTTHREADS_API_KEY="..."
export SMARTTHREADS_MODEL="gpt-4o-mini"

python3 -m smartthreads --prompt "Give me a one-line project status."
```

Use any OpenAI-compatible service by changing the base URL:

```bash
export SMARTTHREADS_BASE_URL="https://api.example.com/v1"
```

## CLI

```bash
python3 -m smartthreads --help
```

Useful flags:

- `--provider`: `local`, `ollama`, `internet`, or `openai`.
- `--model`: model name for the selected provider.
- `--base-url`: backend base URL.
- `--api-key`: bearer token for internet providers.
- `--prompt`: user prompt. If omitted, stdin is used.
- `--image`: optional image path. May be repeated.
- `--json`: print a structured response envelope.

## Web App

```bash
smartthreads-web --host 127.0.0.1 --port 8765
```

The web app provides a provider selector, model and base URL controls, API key
entry for internet providers, a system prompt field, and a chat thread backed by
the same harness used by the CLI.

## Environment Variables

- `SMARTTHREADS_PROVIDER`
- `SMARTTHREADS_MODEL`
- `SMARTTHREADS_BASE_URL`
- `SMARTTHREADS_API_KEY`
- `SMARTTHREADS_TIMEOUT`

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```
