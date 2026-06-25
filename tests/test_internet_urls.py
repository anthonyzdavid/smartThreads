from smartthreads.config import HarnessConfig
from smartthreads.providers import ProviderError
from smartthreads.providers.openai_compatible import normalize_openai_compatible_base_url
from smartthreads.web.server import discover_models


def test_openai_rejects_website_base_url():
    try:
        normalize_openai_compatible_base_url("https://platform.openai.com/chat")
    except ProviderError as exc:
        assert "api.openai.com/v1" in str(exc)
    else:
        raise AssertionError("expected website URL to be rejected")


def test_openai_normalizes_pasted_endpoint_url():
    assert (
        normalize_openai_compatible_base_url("https://api.openai.com/v1/chat/completions")
        == "https://api.openai.com/v1"
    )


def test_openai_normalizes_missing_v1_for_official_api():
    assert normalize_openai_compatible_base_url("https://api.openai.com") == "https://api.openai.com/v1"


def test_discover_models_rejects_openai_website_url():
    result = discover_models(
        HarnessConfig(
            provider="internet",
            api_key="token",
            internet_base_url="https://platform.openai.com/chat",
        )
    )

    assert result["internet"]["verified"] is False
    assert "api.openai.com/v1" in result["internet"]["error"]
