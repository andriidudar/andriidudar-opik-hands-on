"""Tiny keyword retriever over the lesson notes in data/lessons.md."""
import re
from pathlib import Path

NOTES_PATH = Path(__file__).resolve().parent.parent / "data" / "lessons.md"


def load_sections(path: Path = NOTES_PATH) -> dict[str, str]:
    """Split the markdown file into {heading: body}."""
    sections: dict[str, str] = {}
    title, lines = None, []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if title:
                sections[title] = "\n".join(lines).strip()
            title, lines = line[3:].strip(), []
        elif title:
            lines.append(line)
    if title:
        sections[title] = "\n".join(lines).strip()
    return sections


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"\w+", text.lower()) if len(w) > 2}


def find_notes(question: str, k: int = 2, sections: dict[str, str] | None = None) -> str:
    """Return the k lesson sections sharing the most words with the question."""
    sections = sections if sections is not None else load_sections()
    q = _words(question)
    scored = sorted(
        ((len(q & _words(f"{t} {b}")), t) for t, b in sections.items()), reverse=True
    )
    hits = [t for score, t in scored[:k] if score > 0]
    return "\n\n".join(f"### {t}\n{sections[t]}" for t in hits) or "(no matching lesson notes)"
