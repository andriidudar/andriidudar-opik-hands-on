"""Loads the fictional shop data from data/shop.json."""

import json
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "shop.json"


@lru_cache
def load_shop() -> dict:
    return json.loads(DATA_FILE.read_text())
