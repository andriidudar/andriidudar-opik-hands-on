from classifier import GENRES, genre_accuracy, load_episodes, normalize


def test_dataset_is_labeled_with_known_genres():
    eps = load_episodes()
    assert len(eps) >= 24
    assert {e["genre"] for e in eps} == set(GENRES)


def test_normalize_and_metric():
    item = {"genre": "comedy"}
    assert normalize(' "Comedy." ') == "comedy"
    assert genre_accuracy(item, "Comedy.") == 1.0
    assert genre_accuracy(item, "It is a comedy") == 0.0
