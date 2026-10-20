from tutor.notes import find_notes, load_sections


def test_sections_load():
    assert "Ser vs estar" in load_sections()


def test_retrieval_picks_matching_section():
    assert "DOCTOR" in find_notes("when do I use ser or estar?", k=1)


def test_no_match():
    assert find_notes("xyzzy qwerty") == "(no matching lesson notes)"
