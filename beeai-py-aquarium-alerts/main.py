"""Run the triage agent over the scripted alerts in data/alerts.json."""
import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads ./.env if present; the repo-level .env is picked up by the shell

from aquarium.agent import build_agent, triage  # noqa: E402
from aquarium.tools import PAGES_SENT  # noqa: E402

ALERTS = json.loads((Path(__file__).parent / "data" / "alerts.json").read_text())


async def main() -> None:
    agent = build_agent()
    for alert in ALERTS:
        agent.memory.reset()  # each alert is triaged on its own, no carry-over between alerts
        verdict = await triage(agent, alert)
        print(f"{alert['id']} {alert['tank']:8} expected={alert['expected_severity']:9} got={verdict['severity']}  {verdict['action']}")
    print(f"pages sent: {len(PAGES_SENT)}")


if __name__ == "__main__":
    asyncio.run(main())
