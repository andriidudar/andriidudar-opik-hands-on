"""The client side: loads submissions and starts one workflow per submission."""
import json
import uuid
from pathlib import Path

import opik
from opik import opik_context
from temporalio.client import Client

from screening.config import TASK_QUEUE
from screening.models import ScreeningInput, ScreeningResult, Submission
from screening.workflows import ScreenSubmission

DATA = Path(__file__).resolve().parent.parent / "data" / "submissions.json"


def load_submissions() -> list[Submission]:
    return [Submission(**row) for row in json.loads(DATA.read_text())]


# This @track opens the ROOT of the trace, in the starter process. ignore_arguments keeps the
# non-serialisable Temporal client out of the span input.
@opik.track(name="screen_submission", type="general", ignore_arguments=["client"])
async def screen(client: Client, sub: Submission) -> ScreeningResult:
    workflow_id = f"screen-{sub.id}-{uuid.uuid4().hex[:6]}"
    # Trace id + this span's id, serialised into the workflow input: the only thing that
    # crosses the process boundary. The worker's spans attach to this span.
    headers = dict(opik_context.get_distributed_trace_headers())
    opik_context.update_current_span(metadata={"workflow_id": workflow_id})
    return await client.execute_workflow(
        ScreenSubmission.run,
        ScreeningInput(submission=sub, trace_headers=headers),
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
