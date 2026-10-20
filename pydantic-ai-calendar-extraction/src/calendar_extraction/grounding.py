"""Deterministic grounding check: is each non-null field backed by words in the email?

This is the cheap, offline half of hallucination testing. It cannot say a value is
right, only that it is not made up out of thin air (a timezone the email never
mentions, an attendee nobody named, an end time nobody wrote).
"""

import re
import unicodedata

from .schema import CalendarEvent

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
RELATIVE = ("today", "tomorrow", "tonight")


def _fold(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text)
    return "".join(c for c in stripped if not unicodedata.combining(c)).casefold()


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", _fold(text)))


def time_is_grounded(value: str, text: str) -> bool:
    """True if the HH:MM value is written in the email in some common form (14:00, 2pm, 2:00 pm...)."""
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", value.strip())
    if not match:
        return False
    hour, minute = int(match.group(1)), int(match.group(2))
    body = _fold(text)
    forms = [rf"\b0?{hour}[:.]{minute:02d}\b"]
    hour12 = hour % 12 or 12
    suffix = "pm" if hour >= 12 else "am"
    forms.append(rf"\b{hour12}[:.]{minute:02d}\s*{suffix}\b")
    if minute == 0:
        forms.append(rf"\b{hour12}\s*{suffix}\b")
    if (hour, minute) == (12, 0):
        forms.append(r"\bnoon\b")
    return any(re.search(form, body) for form in forms)


def date_is_grounded(value: str, text: str) -> bool:
    """Lenient: the email names that day of the month, a weekday, or today/tomorrow."""
    match = re.fullmatch(r"\d{4}-\d{2}-(\d{2})", value.strip())
    if not match:
        return False
    body = _fold(text)
    day = int(match.group(1))
    return (
        re.search(rf"\b0?{day}(st|nd|rd|th)?\b", body) is not None
        or any(w in body for w in WEEKDAYS + RELATIVE)
    )


def phrase_is_grounded(value: str, text: str) -> bool:
    """Every word of the value appears somewhere in the email."""
    wanted = _tokens(value)
    return bool(wanted) and wanted <= _tokens(text)


def ungrounded_fields(event: CalendarEvent, email_text: str) -> list[str]:
    """Names of fields whose non-null value has no support in the email text."""
    bad: list[str] = []
    if event.date and not date_is_grounded(event.date, email_text):
        bad.append("date")
    for name in ("start_time", "end_time"):
        value = getattr(event, name)
        if value and not time_is_grounded(value, email_text):
            bad.append(name)
    for name in ("timezone", "location"):
        value = getattr(event, name)
        if value and not phrase_is_grounded(value, email_text):
            bad.append(name)
    if event.meeting_link and _fold(event.meeting_link) not in _fold(email_text):
        bad.append("meeting_link")
    for person in event.attendees:
        if not phrase_is_grounded(person, email_text):
            bad.append(f"attendees:{person}")
    return bad
