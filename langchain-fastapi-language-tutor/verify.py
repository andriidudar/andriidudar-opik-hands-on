"""Print what the demo left in Opik: traces, threads, span shape, usage and cost."""
import opik

PROJECT = "langchain-fastapi-language-tutor"
client = opik.Opik()
traces = client.search_traces(project_name=PROJECT, max_results=100)
print(f"{len(traces)} traces, {len({t.thread_id for t in traces})} threads")
for t in sorted(traces, key=lambda t: (t.thread_id, t.start_time)):
    print(f"[{t.thread_id}] {t.name}: {t.input['input'][:50]!r} -> {t.output['output'][:50]!r}")
spans = client.search_spans(project_name=PROJECT, trace_id=traces[0].id)
for s in spans:
    print(f"  span {s.name:20} type={s.type:8} cost={s.total_estimated_cost} tokens={(s.usage or {}).get('total_tokens')}")
