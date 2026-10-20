"""Prompt, parsing and scoring for the podcast genre classifier (no Opik here)."""

import json
import pathlib

GENRES = ["true-crime", "comedy", "science", "history", "business", "wellness", "sports", "fiction"]

# A deliberately loose first draft: genres are named in prose, nothing pins the
# answer format, and nothing says how to break ties on cross-genre episodes.
BASELINE_SYSTEM = """\
You help a podcast app file episodes. Read the episode description and say which
kind of show it is: crime, comedy, science, history, business, health, sports
or fiction."""

DATA_FILE = pathlib.Path(__file__).parent / "data" / "episodes.json"


def load_episodes() -> list[dict]:
    return json.loads(DATA_FILE.read_text())


def normalize(answer: str) -> str:
    """Lowercase and strip quotes/punctuation, so 'Comedy.' passes but 'It is a comedy' does not."""
    return answer.strip().lower().strip(".!\"'` *")


def genre_accuracy(dataset_item: dict, llm_output: str) -> float:
    """Exact match against the labeled genre: 1.0 or 0.0."""
    return 1.0 if normalize(llm_output) == dataset_item["genre"] else 0.0
