"""Customer feedback, logged to Opik as a score on the trace it is about."""

import opik

SCORE_NAME = "customer-satisfaction"


def build_score(trace_id: str, thumbs_up: bool, reason: str) -> dict:
    return {
        "id": trace_id,
        "name": SCORE_NAME,
        "value": 1.0 if thumbs_up else 0.0,
        "reason": reason,
    }


def log_feedback(scores: list[dict]) -> None:
    # Flush first so the traces exist server-side, then attach the scores. They
    # show up as a "customer-satisfaction" column in the traces table, which you
    # can sort and filter on to find the conversations that went badly.
    opik.flush_tracker()
    opik.Opik().log_traces_feedback_scores(scores)
