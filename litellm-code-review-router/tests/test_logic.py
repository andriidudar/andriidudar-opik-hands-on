import os
from types import SimpleNamespace

os.environ["OPIK_TRACK_DISABLE"] = "true"

import litellm  # noqa: E402

from review_router.config import short_name  # noqa: E402
from review_router.diffs import load_diffs  # noqa: E402
from review_router.report import format_table, summarize, trace_to_sample  # noqa: E402
from review_router.router import build_messages, review_diff  # noqa: E402


def test_sample_diffs_load():
    diffs = load_diffs()
    assert len(diffs) == 5
    assert all(d.text.startswith("--- a/") for d in diffs)
    assert next(d for d in diffs if d.name == "04-rename-config").files_touched == 2


def test_short_name_strips_provider():
    assert short_name("anthropic/claude-haiku-4-5-20251001") == "claude-haiku-4-5-20251001"


def test_build_messages_contains_diff():
    diff = load_diffs()[0]
    messages = build_messages(diff)
    assert messages[0]["role"] == "system"
    assert diff.text in messages[1]["content"]


def test_summarize_groups_by_model():
    rows = summarize([("a", 1.0, 0.01, 10), ("a", 3.0, 0.03, 20), ("b", 2.0, 0.5, 5)])
    a = next(r for r in rows if r.model == "a")
    assert (a.calls, a.tokens, a.mean_latency_s) == (2, 30, 2.0)
    assert abs(a.total_cost - 0.04) < 1e-9
    assert "a" in format_table(rows, "title")


def test_trace_to_sample_reads_opik_columns():
    trace = SimpleNamespace(
        metadata={"model": "gpt-4o-mini"}, duration=1500.0, total_estimated_cost=0.0002, usage={"total_tokens": 250}
    )
    assert trace_to_sample(trace) == ("gpt-4o-mini", 1.5, 0.0002, 250)


def test_traced_review_diff_runs_with_tracking_disabled(monkeypatch):
    fake = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Summary: ok"))],
        usage=SimpleNamespace(total_tokens=42),
        _hidden_params={"response_cost": 0.001},
    )
    monkeypatch.setattr(litellm, "completion", lambda **kwargs: fake)
    review = review_diff("openai/gpt-4o-mini", load_diffs()[0])
    assert (review.model, review.tokens, review.cost_usd) == ("gpt-4o-mini", 42, 0.001)
