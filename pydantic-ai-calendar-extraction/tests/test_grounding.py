import pytest

from calendar_extraction.grounding import (
    date_is_grounded,
    phrase_is_grounded,
    time_is_grounded,
    ungrounded_fields,
)
from calendar_extraction.schema import CalendarEvent

EMAIL = (
    "Date: Mon, 2 Mar 2026 16:40\nFrom: Priyanka Desai <p@quillmont.example>\n"
    "Subject: call\n\nQuick call tomorrow 9am PST. Zoom: https://zoom.example/j/884201177. "
    "Me, Rafael Quist and Hal from legal. Maybe Cafe Orlo after, 12:30."
)


@pytest.mark.parametrize(
    "value,expected",
    [("09:00", True), ("12:30", True), ("21:00", False), ("10:00", False), ("9am", False)],
)
def test_time_is_grounded(value, expected):
    assert time_is_grounded(value, EMAIL) is expected


def test_time_accepts_24h_and_noon_forms():
    assert time_is_grounded("14:00", "starts at 14:00 sharp")
    assert time_is_grounded("12:00", "meet at noon")
    assert time_is_grounded("16:00", "from 4pm to 5:30pm")


def test_date_needs_a_day_number_weekday_or_relative_word():
    assert date_is_grounded("2026-03-10", "Tuesday 10 March")
    assert date_is_grounded("2026-03-03", "see you tomorrow")
    assert not date_is_grounded("2026-03-20", "sometime next week")


def test_phrase_ignores_accents_and_case():
    assert phrase_is_grounded("cafe orlo", "Meet at Café Orlo")
    assert not phrase_is_grounded("Orlo Plaza", "Meet at Cafe Orlo")


def test_invented_timezone_and_attendee_are_flagged():
    event = CalendarEvent(
        title="call",
        date="2026-03-03",
        start_time="09:00",
        end_time="10:00",
        timezone="UTC",
        meeting_link="https://zoom.example/j/884201177",
        attendees=["Rafael Quist", "Hal", "Morgan Reyes"],
    )
    assert ungrounded_fields(event, EMAIL) == ["end_time", "timezone", "attendees:Morgan Reyes"]


def test_faithful_event_has_no_ungrounded_fields():
    event = CalendarEvent(title="call", date="2026-03-03", start_time="09:00", timezone="PST")
    assert ungrounded_fields(event, EMAIL) == []
