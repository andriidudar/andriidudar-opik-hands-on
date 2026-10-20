"""Offline, deterministic scoring: compare extracted fields with the card definition."""

from typing import Any

from extract import FIELDS


def _norm(value: Any) -> Any:
    return " ".join(value.lower().split()).rstrip(".") if isinstance(value, str) else value


def field_matches(extracted: dict[str, Any], card: dict[str, Any]) -> dict[str, bool]:
    """Per-field exact match (case and whitespace insensitive). A null never matches."""
    return {name: _norm(extracted.get(name)) == _norm(card[name]) for name in FIELDS}


def field_accuracy(extracted: dict[str, Any], card: dict[str, Any]) -> float:
    matches = field_matches(extracted, card)
    return sum(matches.values()) / len(matches)
