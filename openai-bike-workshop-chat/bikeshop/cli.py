"""Command line entry point: scripted demo or interactive chat."""

import argparse
import uuid

import opik

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from bikeshop.assistant import Assistant  # noqa: E402
from bikeshop.feedback import build_score, log_feedback  # noqa: E402

DEMO_CONVERSATIONS = {
    "commuter-brake-job": [
        "Hi! My road bike's disc brakes feel spongy. What would a brake bleed cost?",
        "Could you also swap the pads? What does the whole job come to?",
        "Is there a slot this week for it?",
    ],
    "mtb-full-service": [
        "I want a full service on my mountain bike. How much?",
        "Do you have a 11-34T cassette in stock, in case mine is worn?",
        "Which days are open in early November?",
    ],
}


# Simulated thumbs on each conversation's last answer: (thumbs_up, reason).
DEMO_VERDICTS = {
    "commuter-brake-job": (True, "Quote and slot were clear; pads flagged as out of stock."),
    "mtb-full-service": (False, "Customer wanted a firm date, got a list of open days."),
}


def run_demo() -> None:
    scores = []
    for conversation_id, turns in DEMO_CONVERSATIONS.items():
        print(f"\n=== Conversation: {conversation_id} ===")
        bot = Assistant(conversation_id)
        for text in turns:
            print(f"\nCustomer: {text}")
            print(f"Shop bot: {bot.answer(text)}")
        up, reason = DEMO_VERDICTS[conversation_id]
        scores.append(build_score(bot.last_trace_id, up, reason))
    log_feedback(scores)
    print(f"\nLogged {len(scores)} customer-satisfaction scores")


def run_interactive() -> None:
    bot = Assistant(f"interactive-{uuid.uuid4().hex[:8]}")
    print(f"Workshop chat (conversation {bot.conversation_id}). Ctrl+C to quit.")
    while True:
        text = input("\nYou: ").strip()
        if text:
            print(f"Shop bot: {bot.answer(text)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bike workshop chat assistant")
    parser.add_argument("--interactive", action="store_true", help="chat yourself")
    args = parser.parse_args()
    try:
        run_interactive() if args.interactive else run_demo()
    except KeyboardInterrupt:
        print("\nBye!")
    finally:
        # Traces are sent in the background; flush so none are lost on exit.
        opik.flush_tracker()


if __name__ == "__main__":
    main()
