"""Plain dataclasses that cross the Temporal boundary (they are JSON-serialised)."""
from dataclasses import dataclass, field


@dataclass
class Submission:
    id: str
    title: str
    director: str
    year: int
    runtime_minutes: int
    category: str
    fee_paid: bool
    synopsis: str


@dataclass
class Eligibility:
    eligible: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class SynopsisScreen:
    genre: str
    themes: list[str]
    content_flags: list[str]
    fit_score: int  # 1 (poor fit) .. 5 (strong fit)
    pitch: str


@dataclass
class Screener:
    name: str
    specialty: str


@dataclass
class ScreeningInput:
    submission: Submission
    # Opik trace-propagation headers; empty when tracing is not wired in.
    trace_headers: dict[str, str] = field(default_factory=dict)


@dataclass
class ScreeningResult:
    submission_id: str
    decision: str  # "reject", "waitlist" or "advance"
    screener: str | None
    letter: str
