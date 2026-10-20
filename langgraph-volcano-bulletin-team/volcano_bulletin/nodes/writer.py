"""Agent 3: draft the weekly bulletin from the findings."""

from ..llm import get_llm
from ..state import BulletinState

SYSTEM = (
    "You write the Mount Tarrow Observatory weekly activity bulletin for the public "
    "and county officials. Use markdown: a two-sentence headline summary, one short "
    "section per finding (drop none), then a line stating the alert level and what "
    "would change it. Use only the notes below, keep every number and source file "
    "accurate. Under 400 words.\n\n"
)


def format_notes(findings: list[dict]) -> str:
    return "\n\n".join(
        f"### {f['question']}\n{f['answer']}\n(Sources: {', '.join(f['sources'])})" for f in findings
    )


def writer(state: BulletinState) -> dict:
    notes = format_notes(state["findings"])
    draft = get_llm().invoke([("system", SYSTEM + notes), ("user", state["brief"])])
    return {"bulletin": draft.content}
