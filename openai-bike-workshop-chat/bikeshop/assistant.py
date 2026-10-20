"""The chat assistant: a tool-calling loop on the plain OpenAI SDK."""

from openai import OpenAI

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
        f"Shop policy: {shop['policies']}"
    )


class Assistant:
    """One instance per conversation; keeps the message history."""

    def __init__(self, conversation_id: str, client: OpenAI | None = None):
        self.conversation_id = conversation_id
        self.client = client or OpenAI()
        self.messages = [{"role": "system", "content": system_prompt()}]

    def answer(self, user_message: str) -> str:
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
