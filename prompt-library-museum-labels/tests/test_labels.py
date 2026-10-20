from museum_labels import suite
from museum_labels.checks import WORD_LIMIT, check_label, word_count
from museum_labels.data import describe, load_artefacts, load_prompt
from museum_labels.library import unified_diff

ARTEFACTS = {a["accession"]: a for a in load_artefacts()}
EWER = ARTEFACTS["1987.14.3"]  # no provenance
LANTERN = ARTEFACTS["1993.2.11"]  # has provenance

GOOD_EWER = (
    "Salt-glazed stoneware ewer with a cobalt wave pattern, c. 1740.\n"
    "Provenance not recorded.\nAcc. no. 1987.14.3"
)


def test_catalogue_is_complete():
    assert len(ARTEFACTS) == 5
    for a in ARTEFACTS.values():
        assert {"accession", "title", "date", "facts", "provenance"} <= a.keys()


def test_describe_marks_missing_provenance():
    assert "Provenance: (none recorded)" in describe(EWER)
    assert "Halloran family" in describe(LANTERN)


def test_good_label_passes_every_check():
    assert all(check_label(GOOD_EWER, EWER).values())


def test_rambling_label_fails_the_v2_rules():
    rambling = "Imagine you stand in the harbour! " + "word " * WORD_LIMIT
    checks = check_label(rambling, EWER)
    assert not any(checks.values())
    assert word_count(rambling) > WORD_LIMIT


def test_provenance_is_not_invented_or_denied():
    wrong = "A lantern.\nProvenance not recorded.\nAcc. no. 1993.2.11"
    assert check_label(wrong, LANTERN)["provenance_reported"] is False
    right = "A lantern.\nProvenance: Donated by the Halloran family, 1993.\nAcc. no. 1993.2.11"
    assert all(check_label(right, LANTERN).values())


def test_suite_items_carry_item_level_assertions():
    items = suite.build_items()
    assert len(items) == 5
    assert all(len(i["assertions"]) == 1 for i in items)
    assert sum("Provenance not recorded" in i["assertions"][0] for i in items) == 3


def test_prompt_versions_differ_and_diff_shows_added_rules():
    assert load_prompt("v1") != load_prompt("v2")
    diff = unified_diff(load_prompt("v1"), load_prompt("v2"))
    assert "+- Use at most 60 words" in diff


def test_traced_function_runs_with_tracking_disabled(monkeypatch):
    # @opik.track must not get in the way of unit tests: with
    # OPIK_TRACK_DISABLE=true the decorated function just runs.
    monkeypatch.setenv("OPIK_API_KEY", "")
    monkeypatch.setattr(suite, "get_version", lambda v: type("P", (), {"prompt": "sys", "commit": "abc"})())
    monkeypatch.setattr(suite, "write_label", lambda a, p: GOOD_EWER)
    assert suite.label_with_prompt(EWER, "v2") == GOOD_EWER
