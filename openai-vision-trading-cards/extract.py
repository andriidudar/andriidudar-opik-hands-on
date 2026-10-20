"""Read typed stats off a trading-card image with gpt-4o-mini vision."""

import base64
import functools
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

HERE = Path(__file__).parent

# Secrets live in the repo-root .env (a local .env works too).
load_dotenv(HERE.parent / ".env")
load_dotenv(HERE / ".env")

# Use the public OpenAI API even if the shell points OPENAI_BASE_URL elsewhere.
os.environ.pop("OPENAI_BASE_URL", None)

PROJECT_NAME = "openai-vision-trading-cards"
# Every trace and span lands in this Opik project (Opik reads the env var at import).
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

import opik  # noqa: E402
from openai import OpenAI  # noqa: E402
from opik import Attachment, opik_context  # noqa: E402
from opik.integrations.openai import track_openai  # noqa: E402

MODEL = "gpt-4o-mini"


@functools.cache
def get_client() -> OpenAI:
    """Built on first use, so importing this module (and the offline tests) needs no key."""
    # track_openai wraps the client: every completion becomes an llm span nested under
    # the calling trace, with token usage (image tokens included) and cost.
    return track_openai(OpenAI(), project_name=PROJECT_NAME)


SYSTEM_PROMPT = """\
You read photos of fictional trading cards and copy their printed stats into
JSON. Report only what you can actually read on the image.

- name, set_number (like 034/120), rarity, card_type (the word before "type").
- hp, attack_damage, defense: integers.
- attack_name, ability_name, ability_text: copied exactly as printed.
- If a value is smudged, cut off or too faint to read, return null for it.
  A null is always better than a guess."""

_STR = {"type": "string"}
_INT_OR_NULL = {"type": ["integer", "null"]}
_STR_OR_NULL = {"type": ["string", "null"]}

FIELDS = {
    "name": _STR_OR_NULL,
    "set_number": _STR_OR_NULL,
    "rarity": _STR_OR_NULL,
    "card_type": _STR_OR_NULL,
    "hp": _INT_OR_NULL,
    "attack_name": _STR_OR_NULL,
    "attack_damage": _INT_OR_NULL,
    "defense": _INT_OR_NULL,
    "ability_name": _STR_OR_NULL,
    "ability_text": _STR_OR_NULL,
}

CARD_SCHEMA = {
    "type": "object",
    "properties": FIELDS,
    "required": list(FIELDS),
    "additionalProperties": False,
}


# @opik.track makes each call one trace (input: image path, output: the fields) with
# the llm span inside; without it the completion would be a lone, parentless trace.
@opik.track(project_name=PROJECT_NAME)
def extract_card(image_path: str) -> dict[str, Any]:
    """One extraction: card image in, ten typed fields out."""
    # Attachment uploads the PNG to Opik's file store: the trace's Attachments tab shows
    # the exact pixels the model saw next to the fields it claimed to read.
    opik_context.update_current_trace(
        attachments=[Attachment(data=image_path, content_type="image/png")]
    )
    image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode()
    response = get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the stats from this card."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}", "detail": "high"},
                    },
                ],
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "card_stats", "strict": True, "schema": CARD_SCHEMA},
        },
    )
    return json.loads(response.choices[0].message.content)
