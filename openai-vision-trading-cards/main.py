"""Draw the fictional cards, send each one to gpt-4o-mini, print the stats."""

import opik

from cardgen import load_cards, render_all
from extract import MODEL, extract_card


def main() -> None:
    paths = render_all()
    print(f"Extracting stats from {len(paths)} generated cards with {MODEL}...\n")
    for card in load_cards():
        fields = extract_card(str(paths[card["id"]]))
        print(f"  {card['id']} ({card['style']})")
        print(f"    -> {fields}\n")

    # Traces are sent from a background thread; flush so they all land before exit.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
