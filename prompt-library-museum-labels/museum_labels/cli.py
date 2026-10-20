import argparse

import opik

from . import library
from .checks import check_label, word_count
from .data import load_artefacts


def cmd_generate(args) -> None:
    from .suite import label_with_prompt

    for artefact in load_artefacts():
        if args.accession in (None, artefact["accession"]):
            print(f"--- {artefact['title']} ---")
            print(label_with_prompt(artefact, args.version), "\n")


def cmd_publish(args) -> None:
    created = library.publish()
    print(f"created: {created or 'nothing (already published)'}")
    versions = library.client().get_prompt_history(
        library.PROMPT_NAME, project_name=library.PROJECT_NAME
    )
    print(f"{library.PROMPT_NAME} now has {len(versions)} versions")


def cmd_diff(args) -> None:
    old = library.get_version("v1").prompt
    new = library.get_version("v2").prompt
    print(library.unified_diff(old, new))


def cmd_suite(args) -> None:
    from .suite import get_suite, run_version

    library.publish()
    suite = get_suite()
    labels: dict = {}
    results = {v: run_version(suite, v, labels) for v in ("v1", "v2")}

    print("\n=== Same suite, two prompt versions ===")
    artefacts = {a["accession"]: a for a in load_artefacts()}
    for version, result in results.items():
        print(
            f"{library.PROMPT_NAME} {version}: {result.pass_rate:.0%} pass rate "
            f"({result.items_passed}/{result.items_total} items passed)"
        )
        for (v, acc), label in sorted(labels.items()):
            if v == version:
                checks = check_label(label, artefacts[acc])
                ok = sum(checks.values())
                print(f"  {acc}: {word_count(label):>3} words, offline checks {ok}/{len(checks)}")
    if results["v2"].experiment_url:
        print(f"\nView the runs: {results['v2'].experiment_url}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="museum_labels")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("publish", help="push v1 and v2 to the Opik prompt library").set_defaults(func=cmd_publish)
    sub.add_parser("diff", help="show the v1 -> v2 diff from the library").set_defaults(func=cmd_diff)
    sub.add_parser("suite", help="run the test suite against v1 and v2").set_defaults(func=cmd_suite)
    gen = sub.add_parser("generate", help="write labels with a prompt version from the library")
    gen.add_argument("--version", default="v2", choices=["v1", "v2"])
    gen.add_argument("--accession", default=None)
    gen.set_defaults(func=cmd_generate)
    args = parser.parse_args(argv)
    args.func(args)

    # Traces are sent in the background; flush so none are lost at exit.
    opik.flush_tracker()
