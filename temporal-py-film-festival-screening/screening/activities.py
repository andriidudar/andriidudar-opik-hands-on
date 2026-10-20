"""Temporal activities: the steps that touch the outside world."""
import functools
import json

import opik
from openai import AsyncOpenAI
from opik import opik_context
from opik.integrations.openai import track_openai
from temporalio import activity

from screening.config import MODEL
from screening.logic import check_eligibility as run_eligibility_rules
from screening.logic import decide, pick_screener
from screening.models import Eligibility, Screener, Submission, SynopsisScreen

@functools.cache
def get_client() -> AsyncOpenAI:
    # Built lazily so importing this module (and the offline tests) needs no API key.
    # track_openai wraps the client: every completion becomes an llm span (model, prompt,
    # response, token usage, cost) nested under whichever @track span is active.
    return track_openai(AsyncOpenAI())


def _headers(trace_headers: dict[str, str]) -> dict | None:
    # Opik's distributed-tracing headers (trace id + parent span id) arrive as plain
    # activity input. Handing them to a @track function makes its span a child of the
    # span the starter process opened, instead of starting a brand-new trace here.
    return dict(trace_headers) or None


def _tag_attempt() -> None:
    # Record the Temporal attempt number so a retried activity is easy to read in Opik.
    info = activity.info()
    opik_context.update_current_span(
        metadata={"temporal_attempt": info.attempt, "workflow_id": info.workflow_id}
    )


@opik.track(name="check_eligibility", type="tool")
async def _check_eligibility(sub: Submission) -> Eligibility:
    _tag_attempt()
    return run_eligibility_rules(sub)


@activity.defn
async def check_eligibility(sub: Submission, trace_headers: dict[str, str]) -> Eligibility:
    return await _check_eligibility(sub, opik_distributed_trace_headers=_headers(trace_headers))


@opik.track(name="screen_synopsis", type="general")
async def _screen_synopsis(sub: Submission) -> SynopsisScreen:
    _tag_attempt()
    resp = await get_client().chat.completions.create(
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
async def screen_synopsis(sub: Submission, trace_headers: dict[str, str]) -> SynopsisScreen:
    return await _screen_synopsis(sub, opik_distributed_trace_headers=_headers(trace_headers))


@opik.track(name="assign_screener", type="tool")
async def _assign_screener(genre: str) -> Screener:
    _tag_attempt()
    # Deliberately flaky: the roster service "times out" on the first attempt of
    # every run, so Temporal's retry policy has something to retry. @track records the
    # exception on this attempt's span, so the failure is visible in the trace.
    if activity.info().attempt == 1:
        raise ConnectionError("Screener roster service timed out (transient, succeeds on retry)")
    return pick_screener(genre)


@activity.defn
async def assign_screener(genre: str, trace_headers: dict[str, str]) -> Screener:
    return await _assign_screener(genre, opik_distributed_trace_headers=_headers(trace_headers))


@opik.track(name="write_decision_letter", type="general")
async def _write_decision_letter(sub: Submission, screen: SynopsisScreen, screener: Screener | None) -> str:
    _tag_attempt()
    decision = decide(screen.fit_score)
    resp = await get_client().chat.completions.create(
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


@activity.defn
async def write_decision_letter(
    sub: Submission, screen: SynopsisScreen, screener: Screener | None, trace_headers: dict[str, str]
) -> str:
    return await _write_decision_letter(sub, screen, screener, opik_distributed_trace_headers=_headers(trace_headers))
