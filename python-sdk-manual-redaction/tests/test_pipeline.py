import json
from types import SimpleNamespace

import opik
import pipeline


def test_redact_longest_first():
    labels = [{"text": "Mara", "category": "identity"}, {"text": "Mara Venkataram", "category": "identity"}]
    out, n = pipeline.redact_text("Mara Venkataram called. Mara left.", labels)
    assert out == "[IDENTITY] called. [IDENTITY] left."
    assert n == 2


def test_redact_unknown_category_falls_back():
    out, _ = pipeline.redact_text("call 555-0142", [{"text": "555-0142", "category": "weird"}])
    assert out == "call [IDENTITY]"


def test_leak_check():
    assert pipeline.leak_check("hi [CONTACT], mail a@b.test", ["a@b.test", "555"]) == ["a@b.test"]


class FakeCompletions:
    def create(self, **kw):
        msg = SimpleNamespace(content=json.dumps({"entities": []}))
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=2, total_tokens=12)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=usage, model="gpt-4o-mini-test")


def test_chat_json_and_traced_span_with_tracking_disabled():
    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    res = pipeline.chat_json(client, "sys", "user")
    assert res.usage["total_tokens"] == 12
    # Hand-built spans still work as no-ops when tracking is disabled.
    trace = opik.Opik(project_name="tests").trace(name="t")
    span = pipeline.llm_span(trace, "chat", "s", "u", res, 0.0)
    assert span is not None
