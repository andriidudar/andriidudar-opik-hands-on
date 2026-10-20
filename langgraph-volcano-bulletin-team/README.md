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
- A typical run is about 6 llm-bearing node passes and roughly 3,900 tokens for about $0.0011 on gpt-4o-mini. The researcher is the biggest line in total (four passes, about 2,300 tokens), the writer is the biggest single call.
- The terminal prints the same split, summed from the llm spans:

```
agent        passes   tokens   cost (USD)
planner           1      250     0.000072
researcher        4     2333     0.000639
writer            1     1365     0.000424
total             6     3948     0.001136
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
- Remove `graph=...` from the `OpikTracer(...)` call in `cli.py` and reload the trace: the spans stay, the graph panel is empty.
- Delete the `@opik.track` line on `retrieve` and see the `search_notes` tool span disappear from each researcher pass.
- Edit a number in `data/gas-readings.md` and check that it reaches the bulletin, and in the `search_notes` output.

## Gotchas we hit

None yet beyond the ones below.

## How it's put together

- `volcano_bulletin/state.py`: the shared `BulletinState` and `Finding` types.
- `volcano_bulletin/corpus.py`: loads `data/*.md` by section and ranks sections by rarity-weighted keyword match.
- `volcano_bulletin/nodes/`: one module per agent (`planner.py`, `researcher.py` with the loop router, `writer.py`).
- `volcano_bulletin/graph.py`: wires planner, researcher loop and writer.
- `volcano_bulletin/cli.py`: the entry point; creates the `OpikTracer`, runs the graph, flushes.
- `volcano_bulletin/report.py`: fetches the trace's spans and totals tokens and cost per agent.
- `tests/`: corpus ranking, the graph with a stubbed model, the per-agent roll-up, and a traced function called with tracking disabled.

*built with Opik · inspired by Opik's examples and documentation*
