"""Agent 1: split the editor's request into focused questions."""

from pydantic import BaseModel, Field

from ..llm import llm
from ..state import BulletinState


class Plan(BaseModel):
    questions: list[str] = Field(description="3 to 4 questions that together cover the week")


SYSTEM = (
    "You are the planning editor at a volcano observatory. The team can only use "
    "the observatory's own notes: seismograph summaries, gas and thermal readings, "
    "field reports on deformation, and alert-level guidance. Split the editor's "
    "request into 3 to 4 concrete questions, each answerable from those notes. "
    "Cover seismicity, gas, ground deformation and the alert level."
)


def planner(state: BulletinState) -> dict:
    plan = llm.with_structured_output(Plan).invoke([("system", SYSTEM), ("user", state["brief"])])
    return {"questions": plan.questions, "findings": []}
