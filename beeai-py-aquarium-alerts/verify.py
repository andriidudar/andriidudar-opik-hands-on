"""Read back what the last run left in Opik (run it through the lock if the stack is shared)."""
import opik
from collections import Counter

from aquarium.tracing import PROJECT

client = opik.Opik(project_name=PROJECT)
traces = client.search_traces(project_name=PROJECT, max_results=100)
spans = client.search_spans(project_name=PROJECT, max_results=1000)
print(f"traces: {len(traces)}  spans: {len(spans)}")
print("span shape:", dict(Counter((s.type, s.name) for s in spans)))
for t in sorted(traces, key=lambda t: t.start_time):
    scores = {s.name: s.value for s in (t.feedback_scores or [])}
    print(f"  {str(t.input)[30:80]!r:55} usage={t.usage} cost={t.total_estimated_cost} scores={scores}")
llm = [s for s in spans if s.type == "llm"]
print("llm spans:", len(llm), "with provider:", sum(1 for s in llm if s.provider), "with cost:", sum(1 for s in llm if s.total_estimated_cost), "zero usage:", sum(1 for s in llm if not (s.usage or {}).get("total")))
ds = client.get_dataset("aquarium-alerts")
print("dataset items:", len(ds.get_items()))
