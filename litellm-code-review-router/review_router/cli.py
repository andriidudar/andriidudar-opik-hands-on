"""Command line entry point: `uv run review-router`."""

import argparse

from .config import MODELS, load_env


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Route code-review summaries across models.")
    parser.add_argument("--models", nargs="+", default=MODELS, help="LiteLLM model strings")
    args = parser.parse_args(argv)

    load_env()

    # Imported after load_env so provider keys are in the environment first.
    from .config import PROJECT_NAME
    from .diffs import load_diffs
    from .report import format_table, samples_from_opik, summarize
    from .router import route_all
    from .tracing import flush, install_opik_logger

    install_opik_logger()

    diffs = load_diffs()
    print(f"Reviewing {len(diffs)} diffs with {len(args.models)} models")
    reviews = route_all(args.models, diffs)
    rows = summarize([(r.model, r.latency_s, r.cost_usd, r.tokens) for r in reviews])
    print()
    print(format_table(rows, "Local timings (from LiteLLM responses)"))

    flush()
    opik_samples = samples_from_opik(PROJECT_NAME, expected=len(reviews))
    print()
    print(format_table(summarize(opik_samples), f"Same comparison read back from Opik project '{PROJECT_NAME}'"))


if __name__ == "__main__":
    main()
