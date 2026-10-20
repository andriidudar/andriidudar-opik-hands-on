"""The tutor chain: string in -> string out."""
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_openai import ChatOpenAI

from tutor.notes import find_notes

load_dotenv()  # example .env, then the repo-root .env if present
load_dotenv("../.env")

SYSTEM_PROMPT = """You are Luz, a friendly Spanish tutor chatting in a small widget.
Keep replies to 2-4 short sentences. Give Spanish with an English gloss, and end
with one tiny practice question. Prefer the teacher's notes below when they apply.

Teacher's notes:
{notes}"""

# session_id -> list of messages (the tutor's memory)
HISTORIES: dict[str, list] = {}


def gather_context(message: str, config: RunnableConfig) -> dict:
    """Look up this learner's history and the matching lesson notes."""
    session_id = config["configurable"]["session_id"]
    return {
        "history": HISTORIES.setdefault(session_id, []),
        "notes": find_notes(message),
        "message": message,
    }


prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), MessagesPlaceholder("history"), ("human", "{message}")]
)


def build_chain(llm=None):
    llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    return RunnableLambda(gather_context) | prompt | llm | StrOutputParser()


def remember(session_id: str, message: str, reply: str) -> None:
    HISTORIES[session_id] += [HumanMessage(message), AIMessage(reply)]
