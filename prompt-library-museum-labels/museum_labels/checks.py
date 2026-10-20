"""Cheap deterministic checks for the rules in prompts/v2.txt.

The Opik test suite judges these rules with an LLM; these functions are an
offline cross-check that needs no model, handy for unit tests and for
spotting judge mistakes on the word-count rule.
"""

import re

WORD_LIMIT = 60


def word_count(label: str) -> int:
    return len(label.split())


def check_label(label: str, artefact: dict) -> dict[str, bool]:
    lines = [line.strip() for line in label.strip().splitlines() if line.strip()]
    last = lines[-1] if lines else ""
    body = label.lower()
    results = {
        "within_word_limit": word_count(label) <= WORD_LIMIT,
        "accession_line": last == f"Acc. no. {artefact['accession']}",
        "house_style": "!" not in label and not re.search(r"\byou(r|rs|rself)?\b", body),
    }
    if artefact["provenance"] is None:
        results["provenance_not_guessed"] = "provenance not recorded" in body
    else:
        results["provenance_reported"] = (
            "provenance not recorded" not in body and "provenance:" in body
        )
    return results
