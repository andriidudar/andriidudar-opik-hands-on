"""Print what landed in Opik for the project: traces, span shape, threads, usage."""
import collections
import opik

c = opik.Opik()
P = "openai-agents-pet-adoption"
traces = c.search_traces(project_name=P, max_results=100)
print("traces:", len(traces))
for t in sorted(traces, key=lambda t: t.start_time):
    spans = c.search_spans(project_name=P, trace_id=t.id, max_results=100)
    print(f"\n{t.name} thread={t.thread_id} spans={len(spans)}")
    for s in sorted(spans, key=lambda s: s.start_time):
        extra = ""
        if s.type == "tool":
            extra = f" in={str(s.input)[:90]} out={str(s.output)[:110]}"
        if s.type == "llm":
            extra = f" tokens={(s.usage or {}).get('total_tokens')} model={s.model} cost={s.total_estimated_cost}"
        print(f"  {s.type:8} {s.name}{extra}")
print("\nthreads:", collections.Counter(t.thread_id for t in traces))
