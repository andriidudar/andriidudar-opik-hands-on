"""Shared state that flows through the graph."""

from typing_extensions import TypedDict


class Finding(TypedDict):
    question: str
    answer: str
    sources: list[str]


class BulletinState(TypedDict, total=False):
    brief: str  # the editor's request for this week
    questions: list[str]  # planner output
    findings: list[Finding]  # researcher output, one per question
    bulletin: str  # writer output
