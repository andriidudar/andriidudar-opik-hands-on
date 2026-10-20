"""Prompt, parsing and scoring for the podcast genre classifier (no Opik here)."""

import json
import pathlib

GENRES = ["true-crime", "comedy", "science", "history", "business", "wellness", "sports", "fiction"]

# A deliberately loose first draft: it asks for a bare label but names the genres in
# everyday words ("crime", "health"), not the labels the dataset uses ("true-crime",
# "wellness"), and has no rule for episodes that straddle two genres.
BASELINE_SYSTEM = """\
You help a podcast app file episodes. Read the description and reply with just
the genre: crime, comedy, science, history, business, health, sports or fiction."""

DATA_FILE = pathlib.Path(__file__).parent / "data" / "episodes.json"


def load_episodes() -> list[dict]:
    return json.loads(DATA_FILE.read_text())


def normalize(answer: str) -> str:
    """Lowercase and strip quotes/punctuation, so 'Comedy.' passes but 'It is a comedy' does not."""
    return answer.strip().lower().strip(".!\"'` *")


def genre_accuracy(dataset_item: dict, llm_output: str) -> float:
    """Exact match against the labeled genre: 1.0 or 0.0."""
    return 1.0 if normalize(llm_output) == dataset_item["genre"] else 0.0


HELD_OUT = [
    "A detective-turned-podcaster re-examines the unsolved theft of a village church bell.",
    "Stand-up comics read their worst one-star reviews aloud and rate them out of ten.",
    "Why do some volcanoes erupt gently while others explode? A geologist maps the physics.",
]


def classify(client, system: str, description: str, model: str = "gpt-4o-mini") -> str:
    """One genre call. Plain function: wrapping and tracing are added in main.py."""
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": description}],
    )
    return resp.choices[0].message.content or ""


def explain(dataset_item: dict, llm_output: str) -> str:
    """Plain-language reason for the score, shown to the optimizer's prompt-writing model."""
    want, got = dataset_item["genre"], normalize(llm_output)
    if got == want:
        return f"correct: '{want}'"
    return f"expected exactly '{want}' but the model answered {llm_output.strip()[:80]!r}"
