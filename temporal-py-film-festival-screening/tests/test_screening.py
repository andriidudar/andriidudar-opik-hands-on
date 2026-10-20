"""Offline tests: no provider keys, no Temporal server, Opik tracking disabled."""
import pytest

from screening.logic import check_eligibility, decide, pick_screener
from screening.models import Submission
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
