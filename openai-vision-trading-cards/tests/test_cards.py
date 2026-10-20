import json
from pathlib import Path

import extract
from cardgen import draw_card, load_cards, render_all
from scoring import field_accuracy, field_matches
from suite import GLOBAL_ASSERTIONS, build_items

CARD = load_cards()[0]


def test_every_card_has_all_schema_fields():
    for card in load_cards():
        assert set(extract.FIELDS) <= set(card), card["id"]


def test_render_all_draws_one_png_per_card(tmp_path):
    paths = render_all(tmp_path)
    assert len(paths) == len(load_cards())
    assert all(p.stat().st_size > 5_000 for p in paths.values())


def test_smudge_changes_pixels():
    plain = draw_card({**CARD, "style": "clean"})
    smudged = draw_card({**CARD, "style": "smudged", "smudge": "defense"})
    assert plain.tobytes() != smudged.tobytes()


def test_scoring_treats_null_as_wrong_and_ignores_case():
    extracted = {name: CARD[name] for name in extract.FIELDS}
    extracted["name"] = CARD["name"].upper()
    extracted["defense"] = None
    matches = field_matches(extracted, CARD)
    assert matches["name"] and not matches["defense"]
    assert field_accuracy(extracted, CARD) == 0.9


def test_suite_items_carry_expected_values_in_assertions_only():
    items = build_items()
    assert len(items) == len(load_cards()) and GLOBAL_ASSERTIONS
    first = items[0]
    assert "hp" not in first["data"]
    assert f"hp is {CARD['hp']}" in first["assertions"][1]


def test_traced_extract_card_runs_with_stubbed_client(tmp_path, monkeypatch):
    # extract_card is @opik.track'd and the client is track_openai-wrapped; with
    # OPIK_TRACK_DISABLE=true both are inert, so a stub client works as usual.
    expected = {name: CARD[name] for name in extract.FIELDS}

    class Stub:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    content = kwargs["messages"][1]["content"]
                    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
                    msg = type("M", (), {"content": json.dumps(expected)})
                    return type("R", (), {"choices": [type("C", (), {"message": msg})]})

    monkeypatch.setattr(extract, "get_client", lambda: Stub)
    png = render_all(tmp_path)[CARD["id"]]
    assert extract.extract_card(str(png)) == expected
