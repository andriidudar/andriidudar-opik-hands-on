"""The triage agent: one BeeAI ReActAgent plus a small parser for its final answer."""
import os
import re

from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend import ChatModel
from beeai_framework.memory import UnconstrainedMemory

from aquarium.tools import PAGES_SENT, lookup_species_tolerance, page_aquarist, read_tank_log

SEVERITIES = ("info", "warning", "critical")

INSTRUCTIONS = """You triage water-quality alerts for a public aquarium.
For every alert: read the tank log, look up the tolerance of the species in that tank that is
most sensitive to the reading in question, compare the two, then decide a severity:
- info: readings are inside every species' safe range.
- warning: a reading is outside a safe range or trending toward one, animals are not yet at risk.
- critical: a reading is well outside a safe range and animals are at risk now.
Page the aquarist (page_aquarist) for warning and critical, never for info.
Finish with exactly one line in this form: SEVERITY: <info|warning|critical> | ACTION: <short action>"""


def build_agent() -> ReActAgent:
    model = os.environ.get("AQUARIUM_MODEL", "openai:gpt-4o-mini")
    return ReActAgent(
        llm=ChatModel.from_name(model),
        tools=[read_tank_log, lookup_species_tolerance, page_aquarist],
        memory=UnconstrainedMemory(),
        templates={"system": lambda t: t.update(defaults={"instructions": INSTRUCTIONS})},
    )


def parse_verdict(answer: str) -> dict:
    """Pull severity and action out of the agent's final line; severity is None if absent."""
    m = re.search(r"SEVERITY:\s*(info|warning|critical)\s*\|\s*ACTION:\s*(.+)", answer, re.I)
    if not m:
        return {"severity": None, "action": answer.strip()[:200]}
    return {"severity": m.group(1).lower(), "action": m.group(2).strip()}


async def triage(agent: ReActAgent, alert: dict) -> dict:
    pages_before = len(PAGES_SENT)
    prompt = f"Alert {alert['id']}: {alert['text']}"
    result = await agent.run(prompt, execution={"max_iterations": 8, "max_retries_per_step": 2, "total_max_retries": 3})
    return {
        "alert": alert["id"],
        "expected": alert["expected_severity"],
        "paged": len(PAGES_SENT) > pages_before,
        **parse_verdict(result.last_message.text),
    }
