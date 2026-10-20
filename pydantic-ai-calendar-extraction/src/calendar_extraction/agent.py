import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import Agent

from .schema import CalendarEvent

# Provider keys come from the repo-root .env or a local one; nothing is hardcoded.
load_dotenv(Path(__file__).resolve().parents[3] / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

MODEL = os.getenv("CALENDAR_MODEL", "openai:gpt-4o-mini")

SYSTEM_PROMPT = (
    "You turn one email into one calendar event. Use the email's Date header "
    "to resolve words like 'tomorrow' or 'Friday'. Copy facts from the email; "
    "when a field is not stated, leave it null (an empty list for attendees)."
)

# defer_model_check lets the module import (and tests stub the model) without a key.
# The agent name becomes the span name in Opik ("invoke_agent calendar_extractor").
agent = Agent(
    MODEL,
    output_type=CalendarEvent,
    system_prompt=SYSTEM_PROMPT,
    defer_model_check=True,
    name="calendar_extractor",
)


def extract_event(email_text: str) -> CalendarEvent:
    return agent.run_sync(email_text).output
