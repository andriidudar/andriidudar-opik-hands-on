import json

import logfire
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart

from calendar_extraction.agent import agent
from calendar_extraction.emails import load_emails, render_email
from calendar_extraction.suite import GLOBAL_ASSERTIONS, build_items, extraction_task


def _fake_model(payload: dict) -> FunctionModel:
    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        tool = info.output_tools[0]
        return ModelResponse(parts=[ToolCallPart(tool.name, json.dumps(payload))])

    return FunctionModel(respond)


def test_render_email_hides_expected_answers():
    email = load_emails()[0]
    text = render_email(email)
    assert email["subject"] in text and email["body"] in text
    assert "assertions" not in text


def test_every_item_carries_its_own_assertions_and_only_email_data():
    items = build_items()
    assert len(items) == len(load_emails()) == 6
    assert all(i["assertions"] and set(i["data"]) == {"email_id", "email"} for i in items)
    assert len(GLOBAL_ASSERTIONS) == 4


def test_instrumented_agent_still_runs_with_a_stubbed_model():
    # instrument_pydantic_ai() is what makes Opik traces; with no exporter attached
    # (as in tests) the same instrumented agent must run untouched.
    logfire.configure(send_to_logfire=False, console=False)
    logfire.instrument_pydantic_ai()
    payload = {"title": "lunch", "start_time": "12:30", "attendees": []}
    with agent.override(model=_fake_model(payload)):
        out = extraction_task({"email_id": "x", "email": "lunch friday 12:30 at Cafe Orlo"})
    assert out["output"]["start_time"] == "12:30"
    assert out["output"]["ungrounded_fields"] == []


def test_task_reports_an_invented_timezone():
    payload = {"title": "lunch", "start_time": "12:30", "timezone": "CET", "attendees": []}
    with agent.override(model=_fake_model(payload)):
        out = extraction_task({"email_id": "x", "email": "lunch friday 12:30"})
    assert out["output"]["ungrounded_fields"] == ["timezone"]
