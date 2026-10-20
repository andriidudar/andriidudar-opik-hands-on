"""Draw the fictional cards, extract their stats with gpt-4o-mini, and grade the
extractions with an Opik test suite that is allowed to fail."""

from typing import Any

import opik

from cardgen import load_cards, render_all
from extract import MODEL, PROJECT_NAME, extract_card
from scoring import field_accuracy, field_matches
from suite import GLOBAL_ASSERTIONS, build_items


def main() -> None:
    paths = render_all()
    cards = {card["id"]: card for card in load_cards()}
    print(f"Drew {len(paths)} cards. Extracting stats with {MODEL}...\n")

    # A test suite is an Opik dataset whose items carry plain-language assertions
    # (global ones apply to every item). Re-inserting identical items is a no-op.
    client = opik.Opik()
    suite = client.get_or_create_test_suite(
        name=PROJECT_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
    )
    suite.insert(build_items())

    def extraction_task(item: dict[str, Any]) -> dict[str, Any]:
        # run_tests opens one trace per item; extract_card (@opik.track) nests inside it,
        # so the card PNG is attached to that trace and the judge spans sit beside it.
        return {"input": item, "output": extract_card(str(paths[item["card_id"]]))}

    # run_tests runs the task on every item, then an LLM judge grades each
    # assertion. The result is an experiment in the Opik UI with pass/fail per item.
    result = opik.run_tests(
        test_suite=suite,
        task=extraction_task,
        experiment_name="gpt-4o-mini-card-stats",
        worker_threads=3,
        generate_report=False,
    )

    print(f"Suite pass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} cards)\n")
    for item_result in result.item_results.values():
        task_output = item_result.test_results[0].test_case.task_output
        card = cards[task_output["input"]["card_id"]]
        extracted = task_output["output"]
        wrong = [name for name, ok in field_matches(extracted, card).items() if not ok]
        status = "PASS" if item_result.passed else "FAIL"
        print(
            f"  [{status}] {card['id']:<11} {card['style']:<21} "
            f"fields {field_accuracy(extracted, card):.0%}"
            + (f"  wrong: {', '.join(wrong)}" if wrong else "")
        )
    print(f"\nExperiment: {result.experiment_name} ({result.experiment_url})")

    # Flush so the traces, attachments and experiment finish uploading before exit.
    opik.flush_tracker()
    client.flush()


if __name__ == "__main__":
    main()
