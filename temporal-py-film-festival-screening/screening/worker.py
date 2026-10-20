"""The Temporal worker: runs as its own OS process, separate from the starter."""
import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from screening import activities
from screening.config import TASK_QUEUE, TEMPORAL_ADDRESS
from screening.workflows import ScreenSubmission


async def main() -> None:
    client = await Client.connect(TEMPORAL_ADDRESS)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ScreenSubmission],
        activities=[
            activities.check_eligibility,
            activities.screen_synopsis,
            activities.assign_screener,
            activities.write_decision_letter,
        ],
    )
    print("WORKER_READY", flush=True)
    await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:  # the demo stops the worker with SIGINT
        pass
