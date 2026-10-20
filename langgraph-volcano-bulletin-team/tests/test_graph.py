"""Run the real graph with a stubbed chat model: no keys, no network."""

from types import SimpleNamespace

import importlib

# nodes/__init__ re-exports functions named like the modules, so import modules by path.
planner_mod, researcher_mod, writer_mod = (
    importlib.import_module(f"volcano_bulletin.nodes.{n}") for n in ("planner", "researcher", "writer"))
from volcano_bulletin.nodes.planner import Plan
from volcano_bulletin.nodes.researcher import retrieve, route_research
from volcano_bulletin.nodes.writer import format_notes


class FakeLLM:
    def __init__(self):
        self.calls = []

    def with_structured_output(self, schema):
        return SimpleNamespace(invoke=lambda msgs: Plan(questions=["sulfur dioxide flux?", "ground uplift GNSS?"]))

    def invoke(self, msgs):
        self.calls.append(msgs)
        return SimpleNamespace(content=f"answer {len(self.calls)}")


def test_graph_loops_researcher_once_per_question(monkeypatch):
    fake = FakeLLM()
    for mod in (planner_mod, researcher_mod, writer_mod):
        monkeypatch.setattr(mod, "get_llm", lambda: fake)
    from volcano_bulletin.graph import build_graph

    # retrieve is a @opik.track(type="tool") function; with tracking disabled it is a plain call.
    out = build_graph().invoke({"brief": "weekly bulletin"})
    assert [f["question"] for f in out["findings"]] == ["sulfur dioxide flux?", "ground uplift GNSS?"]
    assert "gas-readings.md" in out["findings"][0]["sources"]
    assert out["bulletin"] == "answer 3"  # two researcher calls, then the writer
    assert len(fake.calls) == 3


def test_traced_retrieve_works_with_tracking_disabled():
    hits = retrieve("GNSS uplift millimetres")
    assert hits and hits[0]["source"] == "field-reports.md"


def test_route_research():
    assert route_research({"questions": ["a", "b"], "findings": [{}]}) == "researcher"
    assert route_research({"questions": ["a"], "findings": [{}]}) == "writer"


def test_format_notes_keeps_sources():
    notes = format_notes([{"question": "q", "answer": "a", "sources": ["x.md", "y.md"]}])
    assert "### q" in notes and "(Sources: x.md, y.md)" in notes
