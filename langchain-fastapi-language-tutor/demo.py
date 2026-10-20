"""Scripted demo: two multi-turn learners hit POST /chat through FastAPI's TestClient."""
from fastapi.testclient import TestClient

from tutor.app import app

CONVERSATIONS = {
    "learner-ser-vs-estar": [
        "When do I use ser and when do I use estar?",
        "So which one is right for 'I am tired'?",
        "And for 'I am from Mexico'?",
    ],
    "learner-cafe-trip": [
        "I'm going to a cafe in Madrid. How do I order a coffee politely?",
        "How do I ask for the bill afterwards?",
        "What time do people usually eat dinner there?",
    ],
}


def main() -> None:
    with TestClient(app) as client:
        for session_id, turns in CONVERSATIONS.items():
            print(f"\n=== {session_id} ===")
            for message in turns:
                r = client.post("/chat", json={"message": message, "session_id": session_id})
                r.raise_for_status()
                print(f"\nYou: {message}\nLuz: {r.json()['reply']}")


if __name__ == "__main__":
    main()
