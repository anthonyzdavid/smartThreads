"""Provider-agnostic AI harness for local and internet LLMs."""

from .config import HarnessConfig
from .harness import AIHarness, HarnessResult

__all__ = ["AIHarness", "HarnessConfig", "HarnessResult"]
