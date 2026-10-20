"""The client side: loads submissions and starts one workflow per submission."""
import json
import uuid
from pathlib import Path

from temporalio.client import Client

from screening.config import TASK_QUEUE
from screening.models import ScreeningInput, ScreeningResult, Submission
from screening.workflows import ScreenSubmission

DATA = Path(__file__).resolve().parent.parent / "data" / "submissions.json"


def load_submissions() -> list[Submission]:
    return [Submission(**row) for row in json.loads(DATA.read_text())]


async def screen(client: Client, sub: Submission) -> ScreeningResult:
    return await client.execute_workflow(
        ScreenSubmission.run,
        ScreeningInput(submission=sub),
        id=f"screen-{sub.id}-{uuid.uuid4().hex[:6]}",
        task_queue=TASK_QUEUE,
    )
