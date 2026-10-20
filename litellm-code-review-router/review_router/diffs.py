"""Load the sample diffs from data/."""

from dataclasses import dataclass
from pathlib import Path

from .config import DATA_DIR


@dataclass(frozen=True)
class Diff:
    name: str
    text: str

    @property
    def files_touched(self) -> int:
        return sum(1 for line in self.text.splitlines() if line.startswith("--- a/"))


def load_diffs(directory: Path = DATA_DIR) -> list[Diff]:
    """Every *.diff file in the directory, sorted by file name."""
    return [Diff(p.stem, p.read_text()) for p in sorted(directory.glob("*.diff"))]
