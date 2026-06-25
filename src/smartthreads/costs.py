from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    tokens_per_second: float | None = None
    generation_seconds: float | None = None
    estimated_cost_usd: float | None = None
    cost_note: str = ""

    def to_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "tokens_per_second": self.tokens_per_second,
            "generation_seconds": self.generation_seconds,
            "estimated_cost_usd": self.estimated_cost_usd,
            "cost_note": self.cost_note,
        }


USD_PER_1M_TOKENS = {
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
    },
}


def usage_from_openai(
    model: str,
    usage: dict | None,
    elapsed_seconds: float | None = None,
) -> TokenUsage:
    usage = usage or {}
    input_tokens = _int_or_none(usage.get("prompt_tokens") or usage.get("input_tokens"))
    output_tokens = _int_or_none(usage.get("completion_tokens") or usage.get("output_tokens"))
    total_tokens = _int_or_none(usage.get("total_tokens"))
    if total_tokens is None:
        total_tokens = _sum_optional(input_tokens, output_tokens)

    return _with_cost(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        generation_seconds=elapsed_seconds,
    )


def usage_from_ollama(raw: dict, elapsed_seconds: float | None = None) -> TokenUsage:
    input_tokens = _int_or_none(raw.get("prompt_eval_count"))
    output_tokens = _int_or_none(raw.get("eval_count"))
    total_tokens = _sum_optional(input_tokens, output_tokens)
    generation_seconds = _duration_seconds(raw.get("eval_duration")) or elapsed_seconds
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        tokens_per_second=_tokens_per_second(output_tokens, generation_seconds),
        generation_seconds=generation_seconds,
        estimated_cost_usd=0.0 if total_tokens is not None else None,
        cost_note="Local model: no API token charge.",
    )


def _with_cost(
    *,
    model: str,
    input_tokens: int | None,
    output_tokens: int | None,
    total_tokens: int | None,
    generation_seconds: float | None,
) -> TokenUsage:
    price = USD_PER_1M_TOKENS.get(model)
    if not price or input_tokens is None or output_tokens is None:
        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            tokens_per_second=_tokens_per_second(output_tokens, generation_seconds),
            generation_seconds=generation_seconds,
            cost_note="Token usage shown; add pricing for this model to estimate dollars.",
        )

    cost = ((input_tokens * price["input"]) + (output_tokens * price["output"])) / 1_000_000
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        tokens_per_second=_tokens_per_second(output_tokens, generation_seconds),
        generation_seconds=generation_seconds,
        estimated_cost_usd=cost,
        cost_note="Estimated from configured per-token pricing.",
    )


def _int_or_none(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _sum_optional(left: int | None, right: int | None) -> int | None:
    if left is None and right is None:
        return None
    return (left or 0) + (right or 0)


def _duration_seconds(value) -> float | None:
    if value is None:
        return None
    try:
        duration = float(value)
    except (TypeError, ValueError):
        return None
    if duration <= 0:
        return None
    return duration / 1_000_000_000


def _tokens_per_second(tokens: int | None, seconds: float | None) -> float | None:
    if tokens is None or seconds is None or seconds <= 0:
        return None
    return tokens / seconds
