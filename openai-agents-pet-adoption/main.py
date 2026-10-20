"""Animal-shelter front desk on the OpenAI Agents SDK, traced with Opik.

A triage agent hands off to adoption, foster and surrender specialists, whose
function tools read fictional shelter data from shelter.py.
"""

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
# Opik reads the project name from this variable when the first trace is created,
# so set it before anything logs.
os.environ["OPIK_PROJECT_NAME"] = "openai-agents-pet-adoption"

import opik
from agents import Agent, Runner, function_tool, set_trace_processors, trace
from opik.integrations.openai.agents import OpikTracingProcessor

import shelter

# Replaces the SDK's default OpenAI-dashboard exporter: agent, handoff, tool and
# llm spans now flow to Opik. Without it nothing shows up in the project.
set_trace_processors(processors=[OpikTracingProcessor()])

MODEL = "gpt-4o-mini"

# The SDK turns each decorated function into a tool; Opik records every call
# as a "tool" span with the arguments the model chose and the returned JSON.
find_animals = function_tool(shelter.find_animals)
reserve = function_tool(shelter.reserve)
list_foster_slots = function_tool(shelter.list_foster_slots)
book_surrender = function_tool(shelter.book_surrender)

adoption_agent = Agent(
    name="Adoption Specialist",
    handoff_description="Helps people find and reserve an animal to adopt.",
    instructions=(
        "You help adopters. Use find_animals to look up available animals, mention names and ages, "
        "and call reserve only when the user asks to reserve one, using the animal id and their name. "
        "If a tool returns an error, tell the user plainly. Keep replies short."
    ),
    model=MODEL,
    tools=[find_animals, reserve],
)

foster_agent = Agent(
    name="Foster Coordinator",
    handoff_description="Handles questions about fostering animals temporarily.",
    instructions="You explain foster options using list_foster_slots. Mention length and needs. Keep replies short.",
    model=MODEL,
    tools=[list_foster_slots],
)

surrender_agent = Agent(
    name="Surrender Intake",
    handoff_description="Handles people who need to give up an animal.",
    instructions=(
        "You are kind and non-judgmental. Book an intake appointment with book_surrender once you "
        "know the species, the day and the owner's name. Keep replies short."
    ),
    model=MODEL,
    tools=[book_surrender],
)

# Handoffs show up in Opik as a "Handoff" span between the agent spans.
triage_agent = Agent(
    name="Front Desk Triage",
    instructions=(
        "You are the front desk of an animal shelter. Decide whether the visitor wants to adopt, "
        "foster, or surrender an animal, and hand off to the matching specialist. Never answer directly."
    ),
    model=MODEL,
    handoffs=[adoption_agent, foster_agent, surrender_agent],
)

# Each conversation becomes one Opik thread. The last one is a trap: its second turn mixes a
# surrender booking with an adoption request, so the single specialist the triage picks has to
# stretch (in our run it misused book_surrender for the adoption; the tool span shows it).
DEMO_CONVERSATIONS = {
    "kid-friendly-dog": [
        "Hi, we have two small kids and want a dog. What do you have?",
        "Reserve Biscuit for Maya Okafor please.",
    ],
    "foster-kittens": [
        "Can I foster a kitten for a couple of months?",
    ],
    "rehome-and-mixup": [
        "I have to give up my rabbit. Can I bring him in on Monday? My name is Tomas Reyes.",
        "Ok, Tuesday then. Also, can I reserve Captain Whiskers for my sister Ana Reyes?",
    ],
}


def run_demo() -> None:
    for name, turns in DEMO_CONVERSATIONS.items():
        thread_id = f"{name}-{uuid.uuid4().hex[:8]}"
        print(f"\n=== {name} (thread {thread_id}) ===")
        history = []
        for message in turns:
            print(f"\nVisitor: {message}")
            history.append({"role": "user", "content": message})
            # One trace per turn; the shared group_id becomes the Opik thread id,
            # so the Threads tab stitches the turns into one conversation.
            with trace(workflow_name="Shelter front desk", group_id=thread_id):
                result = Runner.run_sync(triage_agent, history)
            print(f"{result.last_agent.name}: {result.final_output}")
            history = result.to_input_list()


if __name__ == "__main__":
    try:
        run_demo()
    finally:
        # Spans are sent from a background thread; flush so a short script doesn't exit first.
        opik.flush_tracker()
