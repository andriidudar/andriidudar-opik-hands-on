import pathlib

import dotenv
from openai import OpenAI

from .data import describe, load_prompt

# Keys live in the repo-root .env (or a local .env).
dotenv.load_dotenv(pathlib.Path(__file__).resolve().parents[2] / ".env")
dotenv.load_dotenv()

MODEL = "gpt-4o-mini"

client = OpenAI()


def write_label(artefact: dict, system_prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": describe(artefact)},
        ],
    )
    return response.choices[0].message.content.strip()


def write_label_local(artefact: dict, version: str) -> str:
    return write_label(artefact, load_prompt(version))
