"""The chat assistant: a tool-calling loop on the plain OpenAI SDK."""

import opik
from openai import OpenAI
from opik import opik_context
from opik.integrations.openai import track_openai

from bikeshop.data import load_shop
from bikeshop.tools import SCHEMAS, run_tool

MODEL = "gpt-4o-mini"
MAX_TOOL_ROUNDS = 4


def system_prompt() -> str:
    shop = load_shop()
    return (
        f"You are the chat assistant for {shop['shop']}, a bike repair workshop. "
        "Answer questions about repair quotes, open service slots and parts. "
        "Always use the tools for prices, slots and stock; never guess numbers. "
        "If a part is out of stock, say so. Be brief and friendly. "
        f"Today is {shop['today']}. To answer which days are open, call "
        "check_service_slots with no date instead of guessing dates, and do not name weekdays. "
        f"Shop policy: {shop['policies']}"
    )


class Assistant:
    """One instance per conversation; keeps the message history."""

    def __init__(self, conversation_id: str, client: OpenAI | None = None):
        self.conversation_id = conversation_id
        # track_openai wraps the client: every completion becomes an llm span with
        # token usage and cost, nested under the current turn's trace.
        self.client = client or track_openai(OpenAI())
        self.messages = [{"role": "system", "content": system_prompt()}]
        self.last_trace_id: str | None = None

    # One call to answer() is one trace named "chat-turn": the llm and tool spans
    # of this turn hang under it, and its cost is the sum of those spans.
    @opik.track(name="chat-turn")
    def answer(self, user_message: str) -> str:
        # thread_id groups this turn with the rest of the conversation in the
        # Threads tab; without it every turn is an unrelated trace.
        opik_context.update_current_trace(thread_id=self.conversation_id)
        # Remember the trace id so feedback can be attached to this turn later.
        # With OPIK_TRACK_DISABLE=true there is no current trace, so guard it.
        trace = opik_context.get_current_trace_data()
        self.last_trace_id = trace.id if trace else None
        self.messages.append({"role": "user", "content": user_message})
        for _ in range(MAX_TOOL_ROUNDS):
            response = self.client.chat.completions.create(
                model=MODEL, messages=self.messages, tools=SCHEMAS
            )
            message = response.choices[0].message
            self.messages.append(message.model_dump(exclude_none=True))
            if not message.tool_calls:
                return message.content or ""
            for call in message.tool_calls:
                result = run_tool(call.function.name, call.function.arguments)
                self.messages.append(
                    {"role": "tool", "tool_call_id": call.id, "content": result}
                )
        return "Sorry, I could not finish that request."
