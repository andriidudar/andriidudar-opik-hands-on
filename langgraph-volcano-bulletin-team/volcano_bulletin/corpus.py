"""Offline corpus: observatory notes in data/, searched by rarity-weighted keywords."""

import math
import pathlib
import re
from collections import Counter

DATA_DIR = pathlib.Path(__file__).parents[1] / "data"

STOPWORDS = frozenset(
    "the a an and or of to in for is are was were be been what how why when which "
    "who did does do with on by as at it its if from that this these those not no "
    "week any some there their during over about than more most last this".split()
)


def load_corpus(data_dir: pathlib.Path = DATA_DIR) -> list[dict]:
    """One searchable entry per '##' section of every markdown file."""
    entries = []
    for path in sorted(data_dir.glob("*.md")):
        title, *sections = path.read_text().split("\n## ")
        for section in sections:
            entries.append({"source": path.name, "text": f"{title.strip()}\n\n## {section.strip()}"})
    return entries


def tokens(text: str) -> Counter:
    return Counter(w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS)


def search(query: str, corpus: list[dict], k: int = 3) -> list[dict]:
    """Rank sections by query terms they contain: rare and repeated terms count more."""
    terms = tokens(query)
    docs = [tokens(e["text"]) for e in corpus]

    def weight(term: str) -> float:
        n = sum(1 for d in docs if term in d)
        return math.log(len(corpus) / n) + 0.1 if n else 0.0

    scored = [(sum(weight(t) * (1 + math.log(d[t])) for t in terms if t in d), e) for d, e in zip(docs, corpus)]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [e for score, e in scored[:k] if score > 0]
