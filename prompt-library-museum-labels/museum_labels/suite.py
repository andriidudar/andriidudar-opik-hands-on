"""The test suite: the same five artefacts and the same assertions for every prompt version."""

from .checks import check_label
from .data import describe, load_artefacts
from .generate import MODEL, PROJECT_NAME, opik, write_label
from .library import PROMPT_NAME, client, get_version

SUITE_NAME = "museum-label-rules"

# Plain-language rules judged by an LLM against each generated label.
ASSERTIONS = [
    "The label is 60 words or fewer, counting the accession line",
    "The label's final line is exactly 'Acc. no.' followed by the accession "
    "number given in the record",
    "The label is in the present tense, has no exclamation marks and never "
    "addresses the visitor as 'you'",
    "The label states only facts found in the record: it invents no story, "
    "past owner, voyage, famous person or place of origin",
]
NO_PROVENANCE = (
    "The label says 'Provenance not recorded.' instead of guessing where the "
    "object came from"
)

NOT_UNRECORDED = (
    "The label does not claim the provenance is unrecorded, because the record "
    "gives one"
)


def build_items() -> list[dict]:
    items = []
    for artefact in load_artefacts():
        item = {"data": artefact}
        if artefact["provenance"] is None:
            # Item-level assertions apply to one item only, here depending on the record's provenance.
            item["assertions"] = [NO_PROVENANCE]
        else:
            item["assertions"] = [NOT_UNRECORDED]
        items.append(item)
    return items


def get_suite():
    # A test suite is an Opik dataset plus assertions; global_assertions apply
    # to every item. Insert dedupes, so re-runs keep five items.
    suite = client().get_or_create_test_suite(
        name=SUITE_NAME,
        project_name=PROJECT_NAME,
        global_assertions=ASSERTIONS,
    )
    suite.insert(build_items())
    return suite


@opik.track(name="write_label_from_library", project_name=PROJECT_NAME)
def label_with_prompt(artefact: dict, version: str) -> str:
    prompt = get_version(version)
    label = write_label(artefact, prompt.prompt)
    # Metadata on the trace: which library version and commit wrote this
    # label, plus the offline checks, visible in the trace's metadata tab.
    opik.opik_context.update_current_trace(
        metadata={
            "prompt_name": PROMPT_NAME,
            "prompt_version": version,
            "prompt_commit": prompt.commit,
            "local_checks": check_label(label, artefact),
        }
    )
    return label


def run_version(suite, version: str, labels: dict):
    prompt = get_version(version)

    def task(item: dict) -> dict:
        label = label_with_prompt(item, version)
        labels[(version, item["accession"])] = label
        return {"input": {"record": describe(item)}, "output": label}

    # run_tests creates one experiment per call, scores every assertion with
    # an LLM judge, and links `prompts` so the run shows its prompt version.
    return opik.run_tests(
        test_suite=suite,
        task=task,
        experiment_name=f"{PROMPT_NAME}-{version}",
        experiment_config={
            "prompt_version": version,
            "prompt_commit": prompt.commit,
            "model": MODEL,
        },
        prompts=[prompt],
        model="openai/gpt-4o",
        worker_threads=5,
        generate_report=False,
    )
