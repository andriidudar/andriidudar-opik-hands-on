"""Per-model comparison table."""

import statistics
from dataclasses import dataclass


@dataclass
class Row:
    model: str
    calls: int
    tokens: int
    total_cost: float
    mean_latency_s: float


def summarize(samples: list[tuple[str, float, float, int]]) -> list[Row]:
    """samples: (model, latency_s, cost_usd, tokens) per call -> one Row per model."""
    by_model: dict[str, list[tuple[float, float, int]]] = {}
    for model, latency, cost, tokens in samples:
        by_model.setdefault(model, []).append((latency, cost, tokens))
    rows = []
    for model, runs in by_model.items():
        lats, costs, toks = zip(*runs)
        rows.append(Row(model, len(runs), sum(toks), sum(costs), statistics.mean(lats)))
    return rows


def format_table(rows: list[Row], title: str) -> str:
    lines = [
        title,
        f"{"Model":<26} {'Calls':>5} {'Tokens':>7} {'Total cost':>11} {'$/call':>10} {'Mean latency':>13}",
        "-" * 78,
    ]
    for r in rows:
        lines.append(
            f"{r.model:<26} {r.calls:>5} {r.tokens:>7} ${r.total_cost:>10.6f} "
            f"${r.total_cost / r.calls:>9.6f} {r.mean_latency_s:>12.2f}s"
        )
    return "\n".join(lines)


def trace_to_sample(trace) -> tuple[str, float, float, int]:
    """One Opik trace -> (model, latency_s, cost_usd, tokens), using the columns the Traces table shows."""
    usage = trace.usage or {}
    return (
        (trace.metadata or {}).get("model", "unknown"),
        (trace.duration or 0.0) / 1000.0,
        float(trace.total_estimated_cost or 0.0),
        int(usage.get("total_tokens", 0)),
    )


def samples_from_opik(project_name: str, expected: int, timeout_s: float = 30.0) -> list[tuple[str, float, float, int]]:
    """Read the traces back from Opik, one sample per review_diff trace.

    The model comes from the trace metadata we set, cost and tokens are the totals Opik
    aggregated from the child llm span, and latency is the trace duration. Ingestion is
    asynchronous, so poll until every expected trace has its cost.
    """
    import time

    import opik

    client = opik.Opik(project_name=project_name)
    deadline = time.time() + timeout_s
    while True:
        traces = client.search_traces(project_name=project_name, max_results=1000)
        ready = [t for t in traces if t.total_estimated_cost is not None]
        if len(ready) >= expected or time.time() > deadline:
            break
        time.sleep(1.5)
    return [trace_to_sample(t) for t in ready]
