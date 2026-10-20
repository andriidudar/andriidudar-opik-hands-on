"""Pure scoring functions: no Opik, no model, so they are easy to unit test."""

RANK = {"info": 0, "warning": 1, "critical": 2}


def severity_match(expected: str, got: str | None) -> dict:
    """1.0 for an exact match; 0.5 if off by one level; 0.0 if two levels off or unparseable."""
    if got not in RANK:
        return {"name": "severity_match", "value": 0.0, "reason": "no parsable SEVERITY line in the final answer"}
    gap = abs(RANK[expected] - RANK[got])
    value = {0: 1.0, 1: 0.5}.get(gap, 0.0)
    return {"name": "severity_match", "value": value, "reason": f"expected {expected}, agent said {got}"}


def page_policy(severity: str | None, paged: bool) -> dict:
    """The aquarist should be paged for warning/critical and left alone for info."""
    should_page = severity in ("warning", "critical")
    ok = should_page == paged
    return {
        "name": "page_policy",
        "value": 1.0 if ok else 0.0,
        "reason": f"severity={severity}, paged={paged}",
    }
