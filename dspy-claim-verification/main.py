"""Fact-check claims about a fictional island nation with DSPy, and let an
Opik test suite show what BootstrapFewShot compilation is worth.

The same suite runs twice: against the raw ChainOfThought program and
against the compiled one. OpikCallback traces every DSPy call in between.
"""

import os
import pathlib

PROJECT_NAME = "dspy-claim-verification"
# Python SDK reads the project from this variable; set before opik is imported.
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME
# Talk to the public API even if the shell routes providers through a proxy.
for proxy_var in ("OPENAI_BASE_URL", "OPENAI_API_BASE"):
    os.environ.pop(proxy_var, None)

import dotenv
import dspy
import opik
from opik.integrations.dspy.callback import OpikCallback

dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")
dotenv.load_dotenv()

from verifier import ALMANAC, CLAIMS, ClaimVerifier, to_example, verdict_metric

MODEL = "openai/gpt-4o-mini"


def configure_dspy() -> None:
    # OpikCallback hooks DSPy's callback system: each module call becomes a
    # trace, nested module/predict/LM calls become spans. log_graph=True also
    # stores the module graph on the trace so the UI can draw it.
    # cache=False makes every run hit the model, so every run is traced.
    dspy.configure(
        lm=dspy.LM(MODEL, cache=False),
        callbacks=[OpikCallback(project_name=PROJECT_NAME, log_graph=True)],
    )


GLOBAL_ASSERTIONS = [
    "The answer is exactly one line of the form '<VERDICT> | evidence: <ID>', "
    "where VERDICT is SUPPORTED, REFUTED or NOT ENOUGH INFO and ID is an "
    "almanac line id such as L07, or the word none. No other text.",
]


def item_assertions(row: dict) -> list[str]:
    # Item-level checks are judged by an LLM against the actual answer.
    out = [f"The verdict is {row['verdict']}"]
    if row["evidence"] == "none":
        out.append("The evidence field is none, because no line settles the claim")
    else:
        out.append(f"The evidence field cites line {row['evidence']}")
    return out


def make_task(program: dspy.Module):
    # run_tests calls this once per suite item; the DSPy call inside is
    # captured by OpikCallback and attached to the run's trace.
    def task(item: dict) -> dict:
        prediction = program(claim=item["claim"])
        return {"input": {"claim": item["claim"]}, "output": prediction.verdict}

    return task


def run_suite(suite, program, name: str, compiled: bool):
    # run_tests creates an experiment (test-suite run) named `name`; running
    # it for both programs makes them comparable side by side in the UI.
    return opik.run_tests(
        test_suite=suite,
        task=make_task(program),
        experiment_name=name,
        experiment_config={"program": "ClaimVerifier(ChainOfThought)",
                           "compiled": compiled, "model": MODEL},
        worker_threads=4,
        generate_report=False,
    )


def main() -> None:
    configure_dspy()
    client = opik.Opik()
    program = ClaimVerifier()

    probe = CLAIMS["test"][0]["claim"]
    print(f"Claim: {probe}")
    print(f"Uncompiled answer: {program(claim=probe).verdict}\n")

    # One test suite, shared by both runs. The suite lives in the project
    # as a dataset with assertions; insert dedupes items on re-runs.
    suite = client.get_or_create_test_suite(
        name=PROJECT_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
    )
    suite.insert([
        {"data": {"claim": row["claim"]}, "assertions": item_assertions(row)}
        for row in CLAIMS["test"]
    ])

    print("Running the suite against the uncompiled program...")
    uncompiled = run_suite(suite, program, "uncompiled", compiled=False)

    # BootstrapFewShot runs the program over the trainset, keeps attempts the
    # metric accepts (reasoning included) and bakes them in as demos. These
    # teacher calls are traced too (standalone ClaimVerifier traces).
    print("\nCompiling with BootstrapFewShot...")
    optimizer = dspy.BootstrapFewShot(
        metric=verdict_metric,
        max_bootstrapped_demos=6,
        max_labeled_demos=6,
        max_rounds=1,
    )
    compiled_program = optimizer.compile(
        program, trainset=[to_example(r) for r in CLAIMS["train"]]
    )
    print(f"Compiled with {len(compiled_program.check.predict.demos)} demos.")

    print("\nRunning the suite against the compiled program...")
    compiled = run_suite(suite, compiled_program, "compiled", compiled=True)

    print("\n=== Uncompiled vs compiled ===")
    for name, result in [("uncompiled", uncompiled), ("compiled  ", compiled)]:
        print(f"{name}: {result.pass_rate:.0%} pass rate "
              f"({result.items_passed}/{result.items_total} items passed)")
    if compiled.experiment_url:
        print(f"\nView the runs: {compiled.experiment_url}")

    # Traces are sent from a background thread; flush so none are lost on exit.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
