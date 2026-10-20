"""Send one diff to one model through LiteLLM."""

import time
from dataclasses import dataclass

import litellm

from .config import SYSTEM_PROMPT, short_name
from .diffs import Diff


@dataclass
class Review:
    diff: str
    model: str
    text: str
    latency_s: float
    cost_usd: float
    tokens: int


def build_messages(diff: Diff) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Review this diff ({diff.name}):\n\n{diff.text}"},
    ]


def review_diff(model: str, diff: Diff) -> Review:
    start = time.perf_counter()
    response = litellm.completion(model=model, messages=build_messages(diff), max_tokens=300)
    latency = time.perf_counter() - start
    return Review(
        diff=diff.name,
        model=short_name(model),
        text=response.choices[0].message.content or "",
        latency_s=latency,
        cost_usd=response._hidden_params.get("response_cost") or 0.0,
        tokens=response.usage.total_tokens,
    )


def route_all(models: list[str], diffs: list[Diff]) -> list[Review]:
    reviews = []
    for model in models:
        for diff in diffs:
            review = review_diff(model, diff)
            print(f"  {review.model:<24} {diff.name:<18} {review.latency_s:5.2f}s ${review.cost_usd:.6f}")
            reviews.append(review)
    return reviews
