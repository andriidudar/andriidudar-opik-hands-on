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
        f"{'Model':<24} {'Calls':>5} {'Tokens':>7} {'Total cost':>11} {'$/call':>10} {'Mean latency':>13}",
        "-" * 76,
    ]
    for r in rows:
        lines.append(
            f"{r.model:<24} {r.calls:>5} {r.tokens:>7} ${r.total_cost:>10.6f} "
            f"${r.total_cost / r.calls:>9.6f} {r.mean_latency_s:>12.2f}s"
        )
    return "\n".join(lines)
