from smartthreads.costs import usage_from_openai


def test_usage_from_openai_estimates_gpt_4o_mini_cost():
    usage = usage_from_openai(
        "gpt-4o-mini",
        {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500},
    )

    assert usage.input_tokens == 1000
    assert usage.output_tokens == 500
    assert usage.total_tokens == 1500
    assert usage.estimated_cost_usd == 0.00045


def test_usage_from_openai_unknown_model_has_no_cost():
    usage = usage_from_openai(
        "unknown-model",
        {"prompt_tokens": 1000, "completion_tokens": 500},
    )

    assert usage.total_tokens == 1500
    assert usage.estimated_cost_usd is None
