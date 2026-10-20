"""The durable screening workflow. Must stay deterministic: no I/O in here."""
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from screening.logic import decide
    from screening.models import ScreeningInput, ScreeningResult
    from screening import activities as acts


@workflow.defn
class ScreenSubmission:
    @workflow.run
    async def run(self, inp: ScreeningInput) -> ScreeningResult:
        sub = inp.submission
        opts = {"start_to_close_timeout": timedelta(seconds=60)}

        eligibility = await workflow.execute_activity(acts.check_eligibility, sub, **opts)
        if not eligibility.eligible:
            return ScreeningResult(sub.id, "reject", None, "Ineligible: " + "; ".join(eligibility.reasons))

        screen = await workflow.execute_activity(acts.screen_synopsis, sub, **opts)
        # Flaky step: the first attempt fails, the retry (after ~1 s) succeeds.
        screener = await workflow.execute_activity(
            acts.assign_screener,
            screen.genre,
            retry_policy=RetryPolicy(initial_interval=timedelta(seconds=1), maximum_attempts=4),
            **opts,
        )
        letter = await workflow.execute_activity(acts.write_decision_letter, args=[sub, screen, screener], **opts)
        return ScreeningResult(sub.id, decide(screen.fit_score), screener.name if screener else None, letter)
