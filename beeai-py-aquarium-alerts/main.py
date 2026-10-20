"""Run the triage agent over the scripted alerts in data/alerts.json."""
import asyncio
import json
import time
from pathlib import Path

import opik
from dotenv import load_dotenv

load_dotenv()  # reads ./.env if present; the repo-level .env is picked up by the shell

from aquarium.feedback import attach_scores, sync_dataset  # noqa: E402
from aquarium.tracing import PROJECT, flush_tracing, setup_tracing  # noqa: E402
from aquarium.agent import build_agent, triage  # noqa: E402
from aquarium.tools import PAGES_SENT  # noqa: E402

ALERTS = json.loads((Path(__file__).parent / "data" / "alerts.json").read_text())


async def main() -> None:
    setup_tracing()  # must run before the agent is built so the instrumentor sees it
    agent = build_agent()
    started_ms = int(time.time() * 1000)
    results = []
    for alert in ALERTS:
        agent.memory.reset()  # each alert is triaged on its own, no carry-over between alerts
        verdict = await triage(agent, alert)
        results.append(verdict)
        print(f"{alert['id']} {alert['tank']:8} expected={verdict['expected']:9} got={verdict['severity']}  {verdict['action']}")
    flush_tracing()  # spans must be exported before we can look the traces up and score them
    client = opik.Opik(project_name=PROJECT)  # SDK client for the dataset and feedback scores, same project as the OTLP traces
    sync_dataset(client, ALERTS)
    scores = attach_scores(client, results, started_ms)
    client.flush()  # the SDK batches feedback scores in the background; flush so they are sent before exit
    print(f"feedback scores written: {len(scores)}")
    print(f"pages sent: {len(PAGES_SENT)}")


if __name__ == "__main__":
    asyncio.run(main())
