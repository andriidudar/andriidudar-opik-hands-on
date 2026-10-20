"""The agent's three tools, all over the fictional files in data/."""
import json
from pathlib import Path

from beeai_framework.tools import StringToolOutput, tool

DATA = Path(__file__).resolve().parent.parent / "data"

# Pages sent during this process; the "pager" is just a list so the demo is offline.
PAGES_SENT: list[dict] = []


def _load(name: str) -> dict:
    return json.loads((DATA / name).read_text())


def read_tank_log_data(tank_id: str, last_n: int = 4) -> dict:
    tanks = _load("tanks.json")
    if tank_id not in tanks:
        return {"error": f"unknown tank '{tank_id}'", "known_tanks": sorted(tanks)}
    tank = tanks[tank_id]
    return {"tank": tank["name"], "species": tank["species"], "log": tank["log"][-last_n:]}


def species_tolerance_data(species: str) -> dict:
    table = _load("species.json")
    key = species.strip().lower()
    if key not in table:
        return {"error": f"no tolerance data for '{species}'", "known_species": sorted(table)}
    return {"species": key, **table[key]}


def page_aquarist_data(tank_id: str, severity: str, message: str) -> dict:
    if severity not in ("warning", "critical"):
        return {"error": "only warning or critical alerts may page the on-call aquarist"}
    page = {"tank": tank_id, "severity": severity, "message": message, "to": "on-call aquarist"}
    PAGES_SENT.append(page)
    return {"status": "paged", **page}


@tool
def read_tank_log(tank_id: str, last_n: int = 4) -> StringToolOutput:
    """Read the most recent sensor log entries (temperature, pH, ammonia, salinity) and the
    species list for a tank. tank_id is one of: reef-3, kelp-1, touch-2, jelly-4."""
    return StringToolOutput(json.dumps(read_tank_log_data(tank_id, last_n)))


@tool
def lookup_species_tolerance(species: str) -> StringToolOutput:
    """Look up the safe water-quality ranges (temp_c, ph, ammonia_ppm_max, salinity_ppt)
    for one species, for example 'clownfish' or 'sea star'."""
    return StringToolOutput(json.dumps(species_tolerance_data(species)))


@tool
def page_aquarist(tank_id: str, severity: str, message: str) -> StringToolOutput:
    """Page the on-call aquarist. Only for severity 'warning' or 'critical'. Never page for 'info'."""
    return StringToolOutput(json.dumps(page_aquarist_data(tank_id, severity, message)))
