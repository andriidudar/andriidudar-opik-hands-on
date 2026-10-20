"""Shared constants and environment loading for the starter and the worker."""
import os

from dotenv import find_dotenv, load_dotenv

# Walks up from this folder, so the repo-root .env is found without copying it.
load_dotenv(find_dotenv(usecwd=False))

TEMPORAL_PORT = 7241
TEMPORAL_UI_PORT = 8241
TEMPORAL_ADDRESS = os.environ.get("TEMPORAL_ADDRESS", f"localhost:{TEMPORAL_PORT}")
TASK_QUEUE = "festival-screening"
MODEL = "gpt-4o-mini"
PROJECT_NAME = os.environ.get("OPIK_PROJECT_NAME", "temporal-py-film-festival-screening")
