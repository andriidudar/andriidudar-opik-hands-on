"""Read the finished trace back from Opik and total tokens and cost per agent."""

import time
from collections import defaultdict

import opik

AGENTS = ("planner", "researcher", "writer")


def agent_of(span, by_id: dict) -> str | None:
    """Walk up the span tree to the LangGraph node (planner/researcher/writer) that owns it."""
    while span is not None:
        if span.name in AGENTS:
            return span.name
        span = by_id.get(span.parent_span_id)
    return None


def cost_by_agent(spans: list) -> dict[str, dict]:
    """Sum tokens, cost and pass count per agent. Only llm spans carry usage and cost;
    the node spans above them carry none, so we attribute llm spans to their node."""
    by_id = {s.id: s for s in spans}
    totals = defaultdict(lambda: {"passes": 0, "tokens": 0, "cost": 0.0})
    for s in spans:
        if s.name in AGENTS:
            totals[s.name]["passes"] += 1
        if s.type == "llm":
            agent = agent_of(s, by_id)
            if agent:
                totals[agent]["tokens"] += (s.usage or {}).get("total_tokens", 0)
                totals[agent]["cost"] += s.total_estimated_cost or 0.0
    return dict(totals)


def fetch_spans(project_name: str, trace_id: str, attempts: int = 10) -> list:
    """Spans are ingested asynchronously, so poll until the writer's llm span shows up."""
    client = opik.Opik(project_name=project_name)
    spans = []
    for _ in range(attempts):
        spans = client.search_spans(project_name=project_name, trace_id=trace_id, max_results=500)
        if any(s.name == "writer" for s in spans) and any(
            s.type == "llm" and s.total_estimated_cost for s in spans if agent_of(s, {x.id: x for x in spans}) == "writer"
        ):
            break
        time.sleep(1.5)
    return spans


def format_table(totals: dict[str, dict]) -> str:
    lines = [f"{'agent':<12}{'passes':>7}{'tokens':>9}{'cost (USD)':>13}"]
    for agent in AGENTS:
        t = totals.get(agent)
        if t:
            lines.append(f"{agent:<12}{t['passes']:>7}{t['tokens']:>9}{t['cost']:>13.6f}")
    lines.append(f"{'total':<12}{sum(t['passes'] for t in totals.values()):>7}"
                 f"{sum(t['tokens'] for t in totals.values()):>9}{sum(t['cost'] for t in totals.values()):>13.6f}")
    return "\n".join(lines)
