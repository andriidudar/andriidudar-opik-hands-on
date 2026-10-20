import opik

from classifier import BASELINE_SYSTEM, classify


class StubClient:
    """Stands in for OpenAI: records the messages and returns a canned label."""

    def __init__(self, answer: str):
        self.answer, self.messages = answer, None
        self.chat = self
        self.completions = self

    def create(self, model, temperature, messages):
        self.messages = messages
        msg = type("M", (), {"content": self.answer})
        return type("R", (), {"choices": [type("C", (), {"message": msg})]})


def test_classify_sends_system_and_blurb():
    stub = StubClient("comedy")
    assert classify(stub, BASELINE_SYSTEM, "Two friends rank sandwiches.") == "comedy"
    assert [m["role"] for m in stub.messages] == ["system", "user"]


def test_traced_classify_still_works_with_tracking_disabled(monkeypatch):
    # The same opik.track wrapper main.py applies; with OPIK_TRACK_DISABLE it is a pass-through.
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")
    traced = opik.track(name="classify_episode")(classify)
    assert traced(StubClient("sports"), BASELINE_SYSTEM, "Cup final recap.") == "sports"
