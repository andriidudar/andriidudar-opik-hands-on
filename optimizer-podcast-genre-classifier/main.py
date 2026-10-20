"""Score the baseline genre prompt on every labeled episode with plain OpenAI calls."""

import os
import pathlib

os.environ.pop("OPENAI_BASE_URL", None)  # talk to the public API, not a local proxy
os.environ.pop("OPENAI_API_BASE", None)

import dotenv
from openai import OpenAI

from classifier import BASELINE_SYSTEM, genre_accuracy, load_episodes

dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")

MODEL = "gpt-4o-mini"


def classify(client: OpenAI, system: str, description: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": description}],
    )
    return resp.choices[0].message.content or ""


def main() -> None:
    client = OpenAI()
    episodes = load_episodes()
    total = 0.0
    for ep in episodes:
        out = classify(client, BASELINE_SYSTEM, ep["description"])
        score = genre_accuracy(ep, out)
        total += score
        print(f"{ep['id']} want={ep['genre']:<10} score={score:.0f} got={out!r}")
    print(f"\nbaseline accuracy: {total / len(episodes):.3f}")


if __name__ == "__main__":
    main()
