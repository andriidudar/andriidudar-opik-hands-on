from types import SimpleNamespace as S

from volcano_bulletin.report import cost_by_agent, format_table


def span(id, name, parent=None, type="general", cost=None, tokens=None):
    return S(id=id, name=name, parent_span_id=parent, type=type, total_estimated_cost=cost,
             usage={"total_tokens": tokens} if tokens else None)


def test_llm_cost_rolls_up_to_owning_agent():
    spans = [
        span("1", "planner"), span("2", "RunnableSequence", "1"), span("3", "ChatOpenAI", "2", "llm", 0.0001, 100),
        span("4", "researcher"), span("5", "ChatOpenAI", "4", "llm", 0.0002, 300),
        span("6", "researcher"), span("7", "ChatOpenAI", "6", "llm", 0.0003, 400),
        span("8", "writer"), span("9", "ChatOpenAI", "8", "llm", 0.0005, 900),
    ]
    totals = cost_by_agent(spans)
    assert totals["researcher"]["passes"] == 2 and totals["researcher"]["tokens"] == 700
    assert round(totals["researcher"]["cost"], 6) == 0.0005
    assert totals["planner"]["tokens"] == 100


def test_table_lists_every_agent_and_total():
    table = format_table({"planner": {"passes": 1, "tokens": 10, "cost": 0.1}, "writer": {"passes": 1, "tokens": 5, "cost": 0.2}})
    assert "planner" in table and "writer" in table and "0.300000" in table
