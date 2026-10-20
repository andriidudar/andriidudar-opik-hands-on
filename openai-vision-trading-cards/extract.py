"""Read typed stats off a trading-card image with gpt-4o-mini vision."""

import base64
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

from openai import OpenAI  # noqa: E402

MODEL = "gpt-4o-mini"
client = OpenAI()

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


def extract_card(image_path: str) -> dict[str, Any]:
    """One extraction: card image in, ten typed fields out."""
    image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode()
    response = client.chat.completions.create(
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
