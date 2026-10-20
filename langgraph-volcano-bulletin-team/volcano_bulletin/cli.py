"""Command line entry point: `uv run bulletin`."""

import argparse
import pathlib

import dotenv

dotenv.load_dotenv(pathlib.Path(__file__).parents[2] / ".env")
dotenv.load_dotenv()

from .graph import build_graph  # noqa: E402

DEFAULT_BRIEF = (
    "Draft this week's activity bulletin for Mount Tarrow (12-18 October): what the "
    "volcano did, whether the picture is changing, and what the public should know."
)


def run(brief: str) -> dict:
    return build_graph().invoke({"brief": brief})


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft the weekly volcano bulletin")
    parser.add_argument("brief", nargs="?", default=DEFAULT_BRIEF)
    args = parser.parse_args()
    print(f"Editor's brief: {args.brief}\n")
    result = run(args.brief)
    print("Planner questions:")
    for i, q in enumerate(result["questions"], 1):
        print(f"  {i}. {q}")
    print(f"\nResearcher findings: {len(result['findings'])}\n\n{result['bulletin']}")
