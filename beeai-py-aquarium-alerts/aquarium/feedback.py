"""Opik side of the lesson: a dataset of alerts plus feedback scores on the agent's own traces."""
import time

import opik

from aquarium.scoring import page_policy, severity_match
from aquarium.tracing import PROJECT

DATASET = "aquarium-alerts"


def sync_dataset(client: opik.Opik, alerts: list[dict]) -> None:
    """Put the scripted alerts and their expected severities in an Opik dataset (items are deduplicated,
    so re-running does not double them). It appears under Datasets and can be reused for experiments."""
    ds = client.get_or_create_dataset(DATASET, description="Aquarium sensor alerts with the severity an aquarist would assign")
    ds.insert([{"alert_id": a["id"], "input": a["text"], "expected_severity": a["expected_severity"]} for a in alerts])


def find_trace_id(client: opik.Opik, alert_id: str, since_ms: int, tries: int = 15) -> str | None:
    """OTLP ingestion is asynchronous and the agent run does not hand back a trace id, so find the trace by
    its input text. Retries because the trace can take a few seconds to become searchable."""
    for _ in range(tries):
        found = client.search_traces(
            project_name=PROJECT, filter_string=f'input contains "Alert {alert_id}:"', max_results=10
        )
        found = [t for t in found if t.start_time and t.start_time.timestamp() * 1000 >= since_ms]
        if found:
            return max(found, key=lambda t: t.start_time).id
        time.sleep(2)
    return None


def attach_scores(client: opik.Opik, results: list[dict], since_ms: int) -> list[dict]:
    """Score each triage and write the scores onto that alert's trace as feedback scores (they show up as
    columns in the Traces table and let you filter for the alerts the agent got wrong)."""
    scores = []
    for r in results:
        trace_id = find_trace_id(client, r["alert"], since_ms)
        if trace_id is None:
            print(f"  could not find the trace for {r['alert']}; scores skipped")
            continue
        for s in (severity_match(r["expected"], r["severity"]), page_policy(r["severity"], r["paged"])):
            scores.append({"id": trace_id, "project_name": PROJECT, **s})
    if scores:
        client.log_traces_feedback_scores(scores)
    return scores
