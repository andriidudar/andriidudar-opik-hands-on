"""Command line entry point: `uv run bulletin`."""

import argparse
import pathlib

import os

PROJECT_NAME = "langgraph-volcano-bulletin-team"
# Set before opik is imported so @opik.track spans and the tracer share one project.
os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT_NAME)

import dotenv
import opik
from opik.integrations.langchain import OpikTracer

dotenv.load_dotenv(pathlib.Path(__file__).parents[2] / ".env")
dotenv.load_dotenv()

from .graph import build_graph  # noqa: E402
from .report import cost_by_agent, fetch_spans, format_table  # noqa: E402

DEFAULT_BRIEF = (
    "Draft this week's activity bulletin for Mount Tarrow (12-18 October): what the "
    "volcano did, whether the picture is changing, and what the public should know."
)


def run(brief: str) -> dict:
    app = build_graph()
    # Passing the graph makes Opik store its node/edge layout on the trace, which
    # powers the agent-graph view (the researcher loop is drawn). Without it the
    # trace still records spans but the graph panel stays empty.
    tracer = OpikTracer(graph=app.get_graph(xray=True), project_name=PROJECT_NAME,
                        tags=["volcano-bulletin"])
    # One invoke with the tracer as callback = ONE trace; each node pass becomes a
    # span and every ChatOpenAI call nests under it as an llm span with usage and cost.
    result = app.invoke({"brief": brief}, config={"callbacks": [tracer]})
    # Traces are sent from a background thread; flush so a short CLI run doesn't exit first.
    opik.flush_tracker()
    # created_traces() holds the one root trace this tracer opened for the invoke.
    result["trace_id"] = tracer.created_traces()[0].id
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft the weekly volcano bulletin")
    parser.add_argument("brief", nargs="?", default=DEFAULT_BRIEF)
    parser.add_argument("--no-report", action="store_true", help="skip the per-agent cost table")
    args = parser.parse_args()
    print(f"Editor's brief: {args.brief}\n")
    result = run(args.brief)
    print("Planner questions:")
    for i, q in enumerate(result["questions"], 1):
        print(f"  {i}. {q}")
    print(f"\nResearcher findings: {len(result['findings'])}\n\n{result['bulletin']}")
    if not args.no_report:
        # Read the trace back from Opik: llm spans hold the tokens and cost, and we
        # roll them up to the node that made the call.
        spans = fetch_spans(PROJECT_NAME, result["trace_id"])
        print(f"\nCost per agent (trace {result['trace_id']}):\n{format_table(cost_by_agent(spans))}")
