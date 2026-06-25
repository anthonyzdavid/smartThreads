# smartThreads

`smartThreads` is a lightweight Python AI harness for switching between local
LLMs and internet-hosted LLMs without changing the calling code.

The first supported backends are:

- `auto`: local-first routing that escalates to internet models when local fails
  or returns a weak answer.
- `local` / `ollama`: Ollama's local `/api/chat` endpoint.
- `internet` / `openai`: OpenAI-compatible `/v1/chat/completions` endpoints.

## Quick Start
https://www.youtube.com/watch?v=1a1VXDdIyrk

Run the local web app:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python3 -m smartthreads.web
```

Then open:

```text
http://127.0.0.1:8765
```

For a quick no-install dev run from the repo root:

```bash
PYTHONPATH=src python3 -m smartthreads.web
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

For OpenAI specifically, use `https://api.openai.com/v1`. Do not use
`platform.openai.com` or ChatGPT URLs; those are websites and will return browser
challenge pages instead of API JSON.

## CLI

```bash
python3 -m smartthreads --help
```

Useful flags:

- `--provider`: `auto`, `local`, `ollama`, `internet`, or `openai`.
- `--model`: model name for the selected provider.
- `--base-url`: backend base URL.
- `--internet-model`: internet fallback model for auto mode.
- `--internet-base-url`: internet fallback base URL for auto mode.
- `--api-key`: bearer token for internet providers.
- `--prompt`: user prompt. If omitted, stdin is used.
- `--image`: optional image path. May be repeated.
- `--json`: print a structured response envelope.

## Web App

```bash
smartthreads-web --host 127.0.0.1 --port 8765
```

The web app provides a provider selector, model and base URL controls, API key
entry for internet providers, internet fallback controls for auto mode, a system
prompt field, and a chat thread backed by the same harness used by the CLI. Auto
mode tries the local model first, then escalates when the local call fails or the
answer looks too weak for the task. The Internet button bypasses auto routing
for one prompt.

The top-left theme button switches between the default Emerald theme and a dark
Bronze theme.

Each answer shows token usage when the backend returns it, including input
tokens, output tokens, total tokens, token speed, and estimated cost. Local
Ollama calls are shown as $0.00 API cost. Internet calls show estimated dollars
when pricing is configured for the model; `gpt-4o-mini` defaults to OpenAI's
published pricing of $0.15 per 1M input tokens and $0.60 per 1M output tokens.

Use **Check Models** in the sidebar to ask local Ollama for installed models and
to verify the internet API key against the provider's `/models` endpoint. The
returned model names are buttons, so you can click a discovered local or internet
model instead of typing it by hand.

## Environment Variables

- `SMARTTHREADS_PROVIDER`
- `SMARTTHREADS_MODEL`
- `SMARTTHREADS_BASE_URL`
- `SMARTTHREADS_API_KEY`
- `SMARTTHREADS_TIMEOUT`
- `SMARTTHREADS_INTERNET_MODEL`
- `SMARTTHREADS_INTERNET_BASE_URL`

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```
