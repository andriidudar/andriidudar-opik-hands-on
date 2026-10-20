"""Model list, prompt, and environment loading."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_NAME = "litellm-code-review-router"

# LiteLLM model strings: the provider prefix picks the backend.
MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-haiku-4-5-20251001",
]

SYSTEM_PROMPT = (
    "You are a code reviewer. Given a unified diff, reply with exactly three "
    "lines: 'Summary:' (one sentence on what changed), 'Risk:' (low, medium or "
    "high, with a short reason), and 'Suggestion:' (one concrete improvement)."
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_env() -> None:
    """Load .env from the example folder, then the repo root; set the project name."""
    here = Path(__file__).resolve().parent.parent
    load_dotenv(here / ".env")
    load_dotenv(here.parent / ".env")
    os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT_NAME)


def short_name(model: str) -> str:
    """'openai/gpt-4o-mini' -> 'gpt-4o-mini'."""
    return model.split("/", 1)[-1]
