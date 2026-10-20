"""Prompt library: publish prompts/v1.txt and v2.txt as two Opik prompt versions."""

import difflib

from .data import load_prompt
from .generate import PROJECT_NAME, opik

PROMPT_NAME = "museum-label-writer"

CHANGES = {
    "v1": "Initial version: engaging tone, no constraints.",
    "v2": "Add hard rules: 60-word limit, house style, record facts only "
    "(say 'Provenance not recorded.'), closing accession line.",
}

_client = None


def client() -> "opik.Opik":
    global _client
    if _client is None:
        _client = opik.Opik()
    return _client


def publish() -> list[str]:
    """Create v1 and v2 in the prompt library, idempotently.

    create_prompt skips a version only when the text equals the *latest*
    version, so re-publishing v1 after v2 exists would add a v3. We compare
    against the full history instead and only create what is missing.
    """
    existing = {
        p.prompt for p in client().get_prompt_history(PROMPT_NAME, project_name=PROJECT_NAME)
    }
    created = []
    for version in ("v1", "v2"):
        text = load_prompt(version)
        if text in existing:
            continue
        # Each create_prompt with new text adds an immutable version
        # (v1, v2, ...) to the prompt library entry, with a change description.
        client().create_prompt(
            name=PROMPT_NAME,
            prompt=text,
            project_name=PROJECT_NAME,
            change_description=CHANGES[version],
        )
        created.append(version)
    return created


def get_version(version: str):
    # Fetching by version label pins the exact immutable text; the returned
    # Prompt carries the commit hash we log and link to experiments.
    prompt = client().get_prompt(
        PROMPT_NAME, version=version, project_name=PROJECT_NAME
    )
    if prompt is None:
        raise SystemExit(f"Prompt {PROMPT_NAME} {version} not found. Run `publish` first.")
    return prompt


def unified_diff(old: str, new: str) -> str:
    return "".join(
        difflib.unified_diff(
            (old + "\n").splitlines(keepends=True),
            (new + "\n").splitlines(keepends=True),
            fromfile="v1",
            tofile="v2",
        )
    )
