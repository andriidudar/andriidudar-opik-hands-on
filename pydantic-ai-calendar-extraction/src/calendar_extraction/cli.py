import argparse

import opik

from .agent import MODEL, extract_event
from .emails import load_emails, render_email
from .suite import run_suite
from .tracing import flush_tracing, setup_tracing


def cmd_extract(args: argparse.Namespace) -> None:
    setup_tracing()
    emails = [e for e in load_emails() if args.email in (None, e["id"])]
    print(f"Extracting {len(emails)} emails with {MODEL}\n")
    for email in emails:
        event = extract_event(render_email(email))
        print(f"[{email['id']}]\n{event.model_dump_json(indent=2)}\n")
    flush_tracing()


def cmd_suite(args: argparse.Namespace) -> None:
    setup_tracing()
    client = opik.Opik()
    print(f"Running the hallucination suite with {MODEL}...\n")
    result = run_suite(client)
    print(f"\nPass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} emails)")
    for item_result in result.item_results.values():
        task_output = item_result.test_results[0].test_case.task_output
        status = "PASS" if item_result.passed else "FAIL"
        extra = task_output["output"]["ungrounded_fields"]
        print(f"  [{status}] {task_output['input']['email_id']}" + (f"  ungrounded: {extra}" if extra else ""))
    print(f"\nExperiment: {result.experiment_name} ({result.experiment_url})")
    # Flush both pipelines: spans (OTLP batch processor) and the Opik client's queued writes.
    flush_tracing()
    client.flush()


def main() -> None:
    parser = argparse.ArgumentParser(prog="calendar-extraction")
    sub = parser.add_subparsers(dest="command", required=True)
    extract = sub.add_parser("extract", help="extract an event from each email and print it")
    extract.add_argument("--email", help="only this email id")
    extract.set_defaults(func=cmd_extract)
    suite = sub.add_parser("suite", help="run the Opik test suite that hunts for invented values")
    suite.set_defaults(func=cmd_suite)
    args = parser.parse_args()
    args.func(args)
