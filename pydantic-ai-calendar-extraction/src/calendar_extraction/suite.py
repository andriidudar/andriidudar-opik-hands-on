"""An Opik test suite that checks extractions for invented field values."""

from typing import Any

import opik

from .agent import MODEL, extract_event
from .emails import load_emails, render_email
from .grounding import ungrounded_fields
from .tracing import PROJECT_NAME

# Rules every extraction must satisfy; an LLM judge scores each one per item.
GLOBAL_ASSERTIONS = [
    "No field is invented: every non-null value is stated in, or directly derivable from, the email",
    "Any of end_time, timezone, location or meeting_link that the email never states is null, not a plausible default "
    "(fields the email does state may of course be filled in)",
    "attendees only lists people named in the email, never generic roles or guesses",
    "ungrounded_fields is empty",
]


def build_items() -> list[dict[str, Any]]:
    # The item data is only what the agent sees. Expected values live in the assertions,
    # so the judge checks the output instead of reading answers out of the data.
    return [
        {"data": {"email_id": e["id"], "email": render_email(e)}, "assertions": e["assertions"]}
        for e in load_emails()
    ]


def extraction_task(item: dict[str, Any]) -> dict[str, Any]:
    event = extract_event(item["email"])
    output = event.model_dump()
    # The deterministic check rides along in the output, so the judge (and you, in the
    # experiment's item view) can see exactly which fields had no support in the email.
    output["ungrounded_fields"] = ungrounded_fields(event, item["email"])
    return {"input": item, "output": output}


def run_suite(client: opik.Opik) -> Any:
    # get_or_create_test_suite makes a named suite (shown under Test Suites) holding the
    # global assertions; items inserted below are deduplicated across re-runs.
    suite = client.get_or_create_test_suite(
        name=PROJECT_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
    )
    # get_or_create keeps the assertions the suite was first created with, so edits to
    # GLOBAL_ASSERTIONS would silently not apply; this pushes them as a new suite version.
    suite.update_test_settings(global_assertions=GLOBAL_ASSERTIONS)
    suite.insert(build_items())
    # run_tests extracts each email, has an LLM judge check every assertion, and records the
    # result as an experiment: one pass/fail row per email, with the judge's reasons.
    return opik.run_tests(
        test_suite=suite,
        task=extraction_task,
        experiment_name=f"extract-{MODEL.split(':')[-1]}",
        worker_threads=3,
        generate_report=False,
    )
