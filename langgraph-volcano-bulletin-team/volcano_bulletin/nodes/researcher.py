"""Agent 2: answer one open question per pass from the corpus."""

import opik

from ..corpus import load_corpus, search
from ..llm import get_llm
from ..state import BulletinState, Finding

CORPUS = load_corpus()

SYSTEM = (
    "You are an observatory researcher. Answer the question using only the excerpts "
    "below. Quote concrete numbers and name the source file for each claim. If the "
    "excerpts do not answer it, say so.\n\n"
)


# A named tool function makes retrieval show up as its own "tool" span under the
# researcher node, with the question as input and the hit sections as output.
@opik.track(name="search_notes", type="tool")
def retrieve(question: str) -> list[dict]:
    return search(question, CORPUS)


def researcher(state: BulletinState) -> dict:
    question = state["questions"][len(state["findings"])]
    hits = retrieve(question)
    excerpts = "\n\n---\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
    answer = get_llm().invoke([("system", SYSTEM + excerpts), ("user", question)])
    finding: Finding = {
        "question": question,
        "answer": answer.content,
        "sources": sorted({h["source"] for h in hits}),
    }
    return {"findings": state["findings"] + [finding]}


def route_research(state: BulletinState) -> str:
    """Loop back to the researcher until every question has a finding."""
    return "researcher" if len(state["findings"]) < len(state["questions"]) else "writer"
