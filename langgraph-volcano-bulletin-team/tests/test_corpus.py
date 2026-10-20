from volcano_bulletin.corpus import load_corpus, search


def test_corpus_has_one_entry_per_section():
    corpus = load_corpus()
    assert len(corpus) == 12
    assert {e["source"] for e in corpus} == {
        "alert-levels.md", "field-reports.md", "gas-readings.md", "seismic-summaries.md"}


def test_gas_question_finds_gas_section():
    top = search("sulfur dioxide flux tonnes per day", load_corpus())[0]
    assert top["source"] == "gas-readings.md" and "920" in top["text"]


def test_alert_question_finds_alert_guidance():
    assert search("criteria for raising to orange alert", load_corpus())[0]["source"] == "alert-levels.md"
