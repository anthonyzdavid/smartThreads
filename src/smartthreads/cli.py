from __future__ import annotations

import argparse
import json
import sys

from .config import HarnessConfig
from .harness import AIHarness, HarnessError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smartthreads",
        description="Route prompts to local or internet LLM backends.",
    )
    parser.add_argument(
        "--provider",
        choices=("local", "ollama", "internet", "openai"),
        help="Backend provider. Defaults to SMARTTHREADS_PROVIDER or local.",
    )
    parser.add_argument("--model", help="Model name for the selected provider.")
    parser.add_argument("--base-url", help="Provider base URL.")
    parser.add_argument("--api-key", help="Bearer token for internet providers.")
    parser.add_argument("--timeout", type=float, help="HTTP request timeout in seconds.")
    parser.add_argument(
        "--system",
        default="You are smartThreads, a concise AI routing harness.",
        help="System prompt.",
    )
    parser.add_argument("--prompt", help="User prompt. If omitted, stdin is used.")
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        help="Optional image path. May be repeated.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable result envelope.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    prompt = args.prompt
    if prompt is None:
        prompt = sys.stdin.read().strip()

    if not prompt:
        parser.error("a prompt is required via --prompt or stdin")

    try:
        config = HarnessConfig.from_env(
            provider=args.provider,
            model=args.model,
            base_url=args.base_url,
            api_key=args.api_key,
            timeout=args.timeout,
        )
        result = AIHarness(config).ask(
            prompt=prompt,
            system=args.system,
            image_paths=args.image,
        )
    except HarnessError as exc:
        print(f"smartthreads: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(result.text)
    return 0
