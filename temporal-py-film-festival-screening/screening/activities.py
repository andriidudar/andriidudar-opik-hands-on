"""Temporal activities: the steps that touch the outside world."""
import json

from openai import AsyncOpenAI
from temporalio import activity

from screening.config import MODEL
from screening.logic import check_eligibility as run_eligibility_rules
from screening.logic import decide, pick_screener
from screening.models import Eligibility, Screener, Submission, SynopsisScreen

openai_client = AsyncOpenAI()


@activity.defn
async def check_eligibility(sub: Submission) -> Eligibility:
    return run_eligibility_rules(sub)


@activity.defn
async def screen_synopsis(sub: Submission) -> SynopsisScreen:
    resp = await openai_client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a first-round reader for a small international film festival that "
                    "favours human, place-based stories. Reply with JSON: "
                    '{"genre": string, "themes": [string], "content_flags": [string], '
                    '"fit_score": integer 1-5, "pitch": one sentence a programmer could read aloud}.'
                ),
            },
            {"role": "user", "content": f"Title: {sub.title}\nSynopsis: {sub.synopsis}"},
        ],
    )
    data = json.loads(resp.choices[0].message.content or "{}")
    return SynopsisScreen(
        genre=str(data.get("genre", "unknown")),
        themes=[str(t) for t in data.get("themes", [])],
        content_flags=[str(t) for t in data.get("content_flags", [])],
        fit_score=int(data.get("fit_score", 1)),
        pitch=str(data.get("pitch", "")),
    )


@activity.defn
async def assign_screener(genre: str) -> Screener:
    # Deliberately flaky: the roster service "times out" on the first attempt of
    # every run, so Temporal's retry policy has something to retry.
    if activity.info().attempt == 1:
        raise ConnectionError("Screener roster service timed out (transient, succeeds on retry)")
    return pick_screener(genre)


@activity.defn
async def write_decision_letter(sub: Submission, screen: SynopsisScreen, screener: Screener | None) -> str:
    decision = decide(screen.fit_score)
    resp = await openai_client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You write short, kind decision letters for a film festival. Under 90 words, "
                    "no subject line. Mention the film title and the decision; for 'advance' name "
                    "the assigned screener as the next contact."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "title": sub.title,
                        "director": sub.director,
                        "decision": decision,
                        "pitch": screen.pitch,
                        "screener": screener.name if screener else None,
                    }
                ),
            },
        ],
    )
    return resp.choices[0].message.content or ""
