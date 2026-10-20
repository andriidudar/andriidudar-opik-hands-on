"""Pure, offline business rules: no Temporal, no LLM."""
from screening.models import Eligibility, Screener, Submission

MAX_RUNTIME = {"short": 40, "feature": 180}
MIN_YEAR = 2024

ROSTER = [
    Screener("Priya Raman", "drama"),
    Screener("Jonas Eriksen", "documentary"),
    Screener("Lucía Ferrer", "fantasy"),
    Screener("Dmitri Volkov", "experimental"),
]


def check_eligibility(sub: Submission) -> Eligibility:
    reasons = []
    if sub.category not in MAX_RUNTIME:
        reasons.append(f"unknown category '{sub.category}'")
    elif sub.runtime_minutes > MAX_RUNTIME[sub.category]:
        reasons.append(f"runtime {sub.runtime_minutes} min exceeds the {sub.category} limit")
    if sub.year < MIN_YEAR:
        reasons.append(f"completed in {sub.year}; festival accepts {MIN_YEAR} or later")
    if not sub.fee_paid:
        reasons.append("submission fee not paid")
    return Eligibility(eligible=not reasons, reasons=reasons)


def pick_screener(genre: str) -> Screener:
    for s in ROSTER:
        if s.specialty in genre.lower() or genre.lower() in s.specialty:
            return s
    return ROSTER[0]


def decide(fit_score: int) -> str:
    if fit_score >= 4:
        return "advance"
    if fit_score == 3:
        return "waitlist"
    return "reject"
