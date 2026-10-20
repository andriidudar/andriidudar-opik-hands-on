"""Test-suite content: format rules for every card, expected values per card.

The expected values come from the same data/cards.json that cardgen.py draws,
so the answer key can never drift from the pixels.
"""

from typing import Any

from cardgen import load_cards

# Rules every extraction must satisfy, judged from the output alone.
GLOBAL_ASSERTIONS = [
    "The output has all ten fields (name, set_number, rarity, card_type, hp, "
    "attack_name, attack_damage, defense, ability_name, ability_text)",
    "hp, attack_damage and defense are whole numbers or null, never strings",
    "set_number, when present, looks like NNN/120",
]


def build_items() -> list[dict[str, Any]]:
    """One suite item per card. The item data names only the image; the expected
    values live in the assertions, so the LLM judge checks output against them."""
    items = []
    for card in load_cards():
        items.append(
            {
                "data": {"card_id": card["id"], "style": card["style"]},
                "assertions": [
                    f"The name is {card['name']}, the set number is {card['set_number']}, "
                    f"the rarity is {card['rarity']} and the card type is {card['card_type']}",
                    f"hp is {card['hp']}, the attack {card['attack_name']} does "
                    f"{card['attack_damage']} damage, and defense is {card['defense']}",
                    f"The ability is named {card['ability_name']} and its text says: "
                    f"\"{card['ability_text']}\"",
                ],
            }
        )
    return items
