"""Query Opik after a demo run and print the shape of each trace.

Run: uv run python verify.py   (reads the project from OPIK_PROJECT_NAME)
"""
import collections
import os
import time

import opik

PROJECT = os.environ.get("OPIK_PROJECT_NAME", "temporal-py-film-festival-screening")
client = opik.Opik()
time.sleep(2)  # let the last batch of spans land
traces = client.search_traces(project_name=PROJECT, max_results=100)
spans = client.search_spans(project_name=PROJECT, max_results=1000)
print(f"project={PROJECT} traces={len(traces)} spans={len(spans)}")
by_trace = collections.defaultdict(list)
for s in spans:
    by_trace[s.trace_id].append(s)
for t in sorted(traces, key=lambda t: t.start_time):
    ss = sorted(by_trace[t.id], key=lambda s: s.start_time)
    print(f"\ntrace {t.name} id={t.id} spans={len(ss)}")
    for s in ss:
        err = (s.error_info.exception_type if s.error_info else None)
        attempt = (s.metadata or {}).get("temporal_attempt")
        usage = (s.usage or {}).get("total_tokens")
        cost = s.total_estimated_cost
        print(f"  {s.type:<5} {s.name:<24} attempt={attempt} error={err} tokens={usage} cost={cost}")
