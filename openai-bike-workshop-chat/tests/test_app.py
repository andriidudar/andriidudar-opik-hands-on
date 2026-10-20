import json
from types import SimpleNamespace

from bikeshop.assistant import Assistant
from bikeshop.feedback import build_score
from bikeshop.tools import check_service_slots, get_repair_quote, lookup_part, run_tool


def test_quote_adds_labor_parts_and_surcharge():
    q = get_repair_quote(["brake bleed"], "mountain")
    assert q["total"] == 60 + 9.5 + 10
    assert q["parts_out_of_stock"] == []


def test_quote_flags_out_of_stock_and_unknown():
    q = get_repair_quote(["brake pad swap", "paint job"])
    assert q["parts_out_of_stock"] == ["Disc brake pads (pair)"]
    assert q["unknown_services"] == ["paint job"]
    assert "full service" in q["known_services"]


def test_slots_and_parts():
    assert check_service_slots("2026-11-03")["open_slots"] == []
    assert "2026-11-03" not in check_service_slots()["open_slots"]
    assert lookup_part("cassette")["matches"][0]["stock"] == 2


def test_run_tool_handles_bad_input():
    assert "error" in json.loads(run_tool("nope", "{}"))
    assert "error" in json.loads(run_tool("lookup_part", '{"wrong": 1}'))


class StubClient:
    """Replies with one tool call, then a final answer."""

    def __init__(self):
        self.calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            call = SimpleNamespace(
                id="c1",
                function=SimpleNamespace(name="lookup_part", arguments='{"query": "chain"}'),
            )
            msg = SimpleNamespace(
                content=None,
                tool_calls=[call],
                model_dump=lambda **_: {"role": "assistant", "tool_calls": []},
            )
        else:
            msg = SimpleNamespace(
                content="A chain is $32.",
                tool_calls=None,
                model_dump=lambda **_: {"role": "assistant", "content": "A chain is $32."},
            )
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def test_traced_turn_runs_with_tracking_disabled():
    # @opik.track and the tool decorators must not get in the way of unit tests.
    bot = Assistant("t1", client=StubClient())
    assert bot.answer("How much is a chain?") == "A chain is $32."
    assert any(m["role"] == "tool" for m in bot.messages)


def test_build_score():
    s = build_score("tid", False, "slow")
    assert s == {"id": "tid", "name": "customer-satisfaction", "value": 0.0, "reason": "slow"}
