import os

os.environ["OPIK_TRACK_DISABLE"] = "true"

import dspy
import pytest

import main
from verifier import ALMANAC, CLAIMS, ClaimVerifier, parse_answer, to_example, verdict_metric


def test_parse_accepts_strict_format():
    assert parse_answer("SUPPORTED | evidence: L07") == ("SUPPORTED", "L07")
    assert parse_answer(" NOT ENOUGH INFO | evidence: none\n") == ("NOT ENOUGH INFO", "none")


@pytest.mark.parametrize("bad", [
    "Supported | evidence: L07",
    "SUPPORTED, see L07",
    "SUPPORTED | evidence: L7",
    "REFUTED | evidence: L03 because the currency is the shilling",
    "The claim is SUPPORTED | evidence: L01",
])
def test_parse_rejects_prose(bad):
    assert parse_answer(bad) is None


def test_metric_needs_format_verdict_and_evidence():
    ex = to_example({"claim": "c", "verdict": "REFUTED", "evidence": "L03"})
    assert verdict_metric(ex, dspy.Prediction(verdict="REFUTED | evidence: L03"))
    assert not verdict_metric(ex, dspy.Prediction(verdict="REFUTED | evidence: L04"))
    assert not verdict_metric(ex, dspy.Prediction(verdict="SUPPORTED | evidence: L03"))
    assert not verdict_metric(ex, dspy.Prediction(verdict="The claim is refuted (L03)."))


def test_data_is_consistent():
    ids = {line.split()[0] for line in ALMANAC.splitlines()}
    for row in CLAIMS["train"] + CLAIMS["test"]:
        assert (row["evidence"] == "none") == (row["verdict"] == "NOT ENOUGH INFO")
        assert row["evidence"] == "none" or row["evidence"] in ids
    assert {r["claim"] for r in CLAIMS["train"]}.isdisjoint(r["claim"] for r in CLAIMS["test"])


def test_traced_task_runs_with_tracking_disabled():
    # The module and the run_tests task wrapper run unchanged when Opik
    # tracking is off; a DummyLM stands in for gpt-4o-mini.
    lm = dspy.utils.DummyLM([{"reasoning": "L07 says so", "verdict": "SUPPORTED | evidence: L07"}])
    with dspy.context(lm=lm):
        out = main.make_task(ClaimVerifier())({"claim": "x"})
    assert out["output"] == "SUPPORTED | evidence: L07"
    assert out["input"] == {"claim": "x"}
