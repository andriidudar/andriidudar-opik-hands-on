# langgraph-volcano-bulletin-team

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue) ![LangGraph](https://img.shields.io/badge/LangGraph-agent%20team-green) ![Opik 2.2.105](https://img.shields.io/badge/Opik-2.2.105-orange)

Three agents draft a volcano observatory's weekly bulletin, and Opik shows the whole run as one trace with the researcher loop drawn as a graph and the token bill split per agent.

## The problem

A multi-agent run is hard to read from logs. Which agent spent the tokens? Did the researcher really loop four times, or three? When the bulletin comes out thin, was it the plan, the retrieval or the writing? If every LLM call lands in Opik as an unrelated top-level trace, you can't answer any of that. This example shows the setup that keeps the run together: one trace, one span per node pass, LLM calls nested under their node, and the graph layout attached so Opik can draw it.

## What you'll build

An offline team for the fictional Mount Tarrow Observatory. It reads four invented documents in `data/` (seismograph summaries, gas and thermal readings, field reports, alert-level guidance) and works in three steps:

1. `planner` splits the editor's request into 3 to 4 questions.
2. `researcher` runs once per question, retrieves the best-matching sections from the notes and answers from them. LangGraph loops this node until every question has a finding.
3. `writer` turns the findings into a markdown bulletin.

After the run, the CLI reads the trace back from Opik and prints tokens and cost per agent.

## See it in Opik

Open the `langgraph-volcano-bulletin-team` project, Traces tab. One run gives exactly one trace, named `LangGraph`, with the planner, four researcher passes and the writer as spans. Inside it:

- The agent graph panel on the trace page draws planner, researcher, writer and the researcher-to-researcher loop edge. It appears because the tracer is given the compiled graph.
- Each `researcher` span holds a `search_notes` tool span (retrieval, with the question as input and the matched sections as output) and a `ChatOpenAI` llm span with tokens and cost.
- The verified run has 22 spans: 6 node spans (planner, researcher x4, writer) plus their children, 6 `ChatOpenAI` llm spans and 4 `search_notes` tool spans. It used 3,796 tokens for about $0.0011 on gpt-4o-mini. The researcher is the biggest line in total (four passes, 2,261 tokens); the writer is the biggest single call (1,286 tokens).
- The trace metadata carries a `_opik_graph_definition` entry: that is the graph layout the agent-graph panel reads.
- The terminal prints the same split, summed from the llm spans:

```
agent        passes   tokens   cost (USD)
planner           1      249     0.000072
researcher        4     2261     0.000597
writer            1     1286     0.000409
total             6     3796     0.001077
```

## Run it yourself

1. Put `OPENAI_API_KEY` in a `.env` at the repo root (or in this folder, see `.env.example`). Opik is read from `~/.opik.config`; for a local instance it needs `url_override = http://localhost:5173/api/`.
2. From this folder: `uv sync`
3. `uv run bulletin` (or `uv run main.py`). It takes about 20 seconds.
4. Pass your own brief: `uv run bulletin "Which of this week's readings would justify raising the alert level?"`
5. Skip the cost table with `--no-report`.
6. Tests, with no keys and tracking off: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Change the brief in step 4 and watch how many questions the planner produces and how many researcher spans appear.
- Open the trace's metadata and find `_opik_graph_definition`, then compare it with the edges declared in `graph.py`.
- Delete the `@opik.track` line on `retrieve` and see the `search_notes` tool span disappear from each researcher pass.
- Edit a number in `data/gas-readings.md` and check that it reaches the bulletin, and in the `search_notes` output.

## Gotchas we hit

**`OpenAIError: Missing credentials` when you only import the package.** The chat model was created at import time, and `ChatOpenAI(...)` raises without `OPENAI_API_KEY`, so `uv run pytest` with keys unset failed during collection. Build it on first use instead, as in `llm.py`:

```python
@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(model=MODEL, temperature=0)
```

**The cost column is empty on the `planner` and `researcher` spans.** Only the nested `ChatOpenAI` llm spans carry usage and cost; the LangGraph node spans above them show none (`total_estimated_cost` is `None`). To get a per-agent figure, walk each llm span's parents up to the node, as `report.agent_of` does, and sum there.

## How it's put together

- `volcano_bulletin/state.py`: the shared `BulletinState` and `Finding` types.
- `volcano_bulletin/corpus.py`: loads `data/*.md` by section and ranks sections by rarity-weighted keyword match.
- `volcano_bulletin/nodes/`: one module per agent (`planner.py`, `researcher.py` with the loop router, `writer.py`).
- `volcano_bulletin/graph.py`: wires planner, researcher loop and writer.
- `volcano_bulletin/cli.py`: the entry point; creates the `OpikTracer`, runs the graph, flushes.
- `volcano_bulletin/report.py`: fetches the trace's spans and totals tokens and cost per agent.
- `tests/`: corpus ranking, the graph with a stubbed model, the per-agent roll-up, and a traced function called with tracking disabled.

*built with Opik · inspired by Opik's examples and documentation*
