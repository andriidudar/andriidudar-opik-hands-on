"""The single chat model shared by all three agents."""

from langchain_openai import ChatOpenAI

MODEL = "gpt-4o-mini"


def make_llm() -> ChatOpenAI:
    return ChatOpenAI(model=MODEL, temperature=0)


llm = make_llm()
