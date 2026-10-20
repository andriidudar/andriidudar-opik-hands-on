"""Offline tests: a fake chat model stands in for OpenAI; Opik tracking is disabled."""
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from tutor import app as app_module
from tutor import chain as chain_module


def test_chain_is_string_in_string_out_and_remembers():
    chain = chain_module.build_chain(FakeListChatModel(responses=["¡Hola!", "Bien."]))
    cfg = {"configurable": {"session_id": "t1"}}
    reply = chain.invoke("hello", config=cfg)  # the plain string goes straight in
    assert reply == "¡Hola!"
    chain_module.remember("t1", "hello", reply)
    assert len(chain_module.HISTORIES["t1"]) == 2


def test_chat_endpoint_with_tracer_attached(monkeypatch):
    # The endpoint attaches an OpikTracer; with OPIK_TRACK_DISABLE=true it must stay out of the way.
    monkeypatch.setattr(app_module, "get_chain", lambda: chain_module.build_chain(FakeListChatModel(responses=["Sí."])))
    r = TestClient(app_module.app).post("/chat", json={"message": "ser o estar?", "session_id": "t2"})
    assert r.status_code == 200 and r.json() == {"reply": "Sí.", "session_id": "t2"}


def test_empty_message_rejected():
    r = TestClient(app_module.app).post("/chat", json={"message": "", "session_id": "x"})
    assert r.status_code == 422
