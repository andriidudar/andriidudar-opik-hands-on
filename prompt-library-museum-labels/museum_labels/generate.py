import os
import pathlib

# Every trace, prompt, dataset and suite lands in this Opik project. Must be
# set before opik is imported, or the SDK falls back to "Default Project".
PROJECT_NAME = "prompt-library-museum-labels"
os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT_NAME)

import dotenv
import opik
from openai import OpenAI
from opik.integrations.openai import track_openai

from .data import describe, load_prompt

# Keys live in the repo-root .env (or a local .env).
dotenv.load_dotenv(pathlib.Path(__file__).resolve().parents[2] / ".env")
dotenv.load_dotenv()

MODEL = "gpt-4o-mini"

_client = None


def client():
    # Built lazily so importing the package (and the offline tests) needs no key.
    global _client
    if _client is None:
        # track_openai wraps the client: every completion becomes an llm span
        # with model, token usage and cost, nested under the calling trace.
        _client = track_openai(OpenAI(), project_name=PROJECT_NAME)
    return _client


def write_label(artefact: dict, system_prompt: str) -> str:
    response = client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": describe(artefact)},
        ],
    )
    return response.choices[0].message.content.strip()


# @opik.track opens the parent trace (one per label) so the llm span above
# nests inside it; the trace input shows which artefact was labelled.
@opik.track(name="write_label", project_name=PROJECT_NAME)
def write_label_local(artefact: dict, version: str) -> str:
    return write_label(artefact, load_prompt(version))
