from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    """A calendar event as stated in an email. Unstated fields stay null."""

    title: str = Field(description="Short event title")
    date: str | None = Field(None, description="ISO date YYYY-MM-DD, only if the email pins one down")
    start_time: str | None = Field(None, description="24h HH:MM start, only if stated")
    end_time: str | None = Field(None, description="24h HH:MM end, only if stated")
    timezone: str | None = Field(None, description="Timezone exactly as written in the email, only if stated")
    location: str | None = Field(None, description="Physical place, only if stated")
    meeting_link: str | None = Field(None, description="Video-call URL, only if present")
    attendees: list[str] = Field(default_factory=list, description="People named in the email, by name")
