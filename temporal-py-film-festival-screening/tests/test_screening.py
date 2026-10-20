"""Offline tests: no provider keys, no Temporal server, Opik tracking disabled."""
import dataclasses
import json
from types import SimpleNamespace

import pytest
from temporalio.testing import ActivityEnvironment

from screening import activities
from screening.logic import check_eligibility, decide, pick_screener
from screening.models import Screener, Submission, SynopsisScreen
from screening.starter import load_submissions


def sub(**overrides) -> Submission:
    base = dict(id="S1", title="T", director="D", year=2025, runtime_minutes=10,
                category="short", fee_paid=True, synopsis="x")
    return Submission(**{**base, **overrides})


def test_fixture_submissions_cover_both_outcomes():
    verdicts = {s.id: check_eligibility(s).eligible for s in load_submissions()}
    assert verdicts == {"SUB-2041": True, "SUB-2042": True, "SUB-2043": False}


def test_ineligible_lists_every_reason():
    result = check_eligibility(sub(year=2019, runtime_minutes=90, fee_paid=False))
    assert not result.eligible and len(result.reasons) == 3


@pytest.mark.parametrize("score,expected", [(5, "advance"), (4, "advance"), (3, "waitlist"), (1, "reject")])
def test_decide(score, expected):
    assert decide(score) == expected


def test_pick_screener_matches_specialty_with_fallback():
    assert pick_screener("Documentary").name == "Jonas Eriksen"
    assert pick_screener("polka opera").name == "Priya Raman"


async def test_traced_activity_runs_with_tracking_disabled():
    # @track-decorated functions behave like plain functions when OPIK_TRACK_DISABLE=true.
    env = ActivityEnvironment()
    result = await env.run(activities.check_eligibility, sub(), {})
    assert result.eligible


async def test_flaky_activity_fails_first_attempt_then_succeeds():
    env = ActivityEnvironment()
    env.info = dataclasses.replace(env.info, attempt=1)
    with pytest.raises(ConnectionError):
        await env.run(activities.assign_screener, "drama", {})
    env.info = dataclasses.replace(env.info, attempt=2)
    assert await env.run(activities.assign_screener, "drama", {}) == Screener("Priya Raman", "drama")


async def test_synopsis_activity_parses_stubbed_model_reply(monkeypatch):
    reply = json.dumps({"genre": "drama", "themes": ["grief"], "content_flags": [],
                        "fit_score": 4, "pitch": "A keeper answers the sea."})

    async def create(**kwargs):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=reply))])

    stub = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(activities, "get_client", lambda: stub)
    out = await ActivityEnvironment().run(activities.screen_synopsis, sub(), {})
    assert out == SynopsisScreen("drama", ["grief"], [], 4, "A keeper answers the sea.")
