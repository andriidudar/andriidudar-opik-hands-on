import asyncio
import types

from aquarium import agent as agent_mod
from aquarium.agent import parse_verdict
from aquarium.scoring import page_policy, severity_match
from aquarium.tools import PAGES_SENT, page_aquarist_data, read_tank_log_data, species_tolerance_data


def test_read_tank_log_returns_last_entries_and_rejects_unknown_tank():
    data = read_tank_log_data("reef-3", last_n=2)
    assert [e["time"] for e in data["log"]] == ["10:00", "12:00"]
    assert "clownfish" in data["species"]
    assert "known_tanks" in read_tank_log_data("nope")


def test_species_lookup_is_case_insensitive():
    assert species_tolerance_data("Sea Star")["ammonia_ppm_max"] == 0.05
    assert "error" in species_tolerance_data("kraken")


def test_info_alerts_cannot_page():
    before = len(PAGES_SENT)
    assert "error" in page_aquarist_data("kelp-1", "info", "fine")
    assert len(PAGES_SENT) == before
    assert page_aquarist_data("reef-3", "critical", "too hot")["status"] == "paged"


def test_parse_verdict():
    assert parse_verdict("SEVERITY: Warning | ACTION: check filter") == {"severity": "warning", "action": "check filter"}
    assert parse_verdict("no idea")["severity"] is None


def test_scores():
    assert severity_match("critical", "critical")["value"] == 1.0
    assert severity_match("warning", "critical")["value"] == 0.5
    assert severity_match("info", "critical")["value"] == 0.0
    assert severity_match("info", None)["value"] == 0.0
    assert page_policy("info", paged=True)["value"] == 0.0
    assert page_policy("critical", paged=True)["value"] == 1.0


def test_triage_with_a_stubbed_agent():
    class FakeAgent:
        async def run(self, prompt, **kwargs):
            page_aquarist_data("touch-2", "warning", "ammonia")
            return types.SimpleNamespace(last_message=types.SimpleNamespace(text="SEVERITY: warning | ACTION: page"))

    alert = {"id": "A3", "text": "ammonia spike", "expected_severity": "warning"}
    result = asyncio.run(agent_mod.triage(FakeAgent(), alert))
    assert result == {"alert": "A3", "expected": "warning", "paged": True, "severity": "warning", "action": "page"}
