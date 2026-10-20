"""One command: dev server + worker process + starter, then clean shutdown."""
import asyncio
import os
import signal
import socket
import subprocess
import sys
import time

import opik
from temporalio.client import Client

from screening.config import TEMPORAL_ADDRESS, TEMPORAL_PORT, TEMPORAL_UI_PORT
from screening.starter import load_submissions, screen


def wait_for_port(port: int, timeout: float = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.3)
    raise TimeoutError(f"port {port} never opened")


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()


async def run() -> None:
    server = subprocess.Popen(
        ["temporal", "server", "start-dev", "--headless", "--port", str(TEMPORAL_PORT),
         "--ui-port", str(TEMPORAL_UI_PORT)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    worker = None
    try:
        wait_for_port(TEMPORAL_PORT)
        # The worker is a genuinely separate OS process.
        worker = subprocess.Popen([sys.executable, "-m", "screening.worker"], env=os.environ.copy(),
                                  stdout=subprocess.PIPE, text=True)
        assert worker.stdout is not None
        for line in worker.stdout:
            if "WORKER_READY" in line:
                break
        client = await Client.connect(TEMPORAL_ADDRESS)
        for sub in load_submissions():
            result = await screen(client, sub)
            print(f"{sub.id} {sub.title!r}: {result.decision} (screener: {result.screener})")
            print(f"  {result.letter[:160]!r}")
    finally:
        # Flush the starter's spans before exiting; they are sent from a background thread.
        opik.flush_tracker()
        if worker:
            stop(worker)
        stop(server)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
