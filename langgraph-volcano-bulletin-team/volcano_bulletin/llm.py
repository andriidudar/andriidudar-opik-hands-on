"""The single chat model shared by all three agents."""

from functools import lru_cache

from langchain_openai import ChatOpenAI

MODEL = "gpt-4o-mini"


# Built on first use, not at import: ChatOpenAI raises without OPENAI_API_KEY, which
# would make `import volcano_bulletin` (and the offline tests) fail before any code runs.
@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(model=MODEL, temperature=0)
