import json

import main
import shelter


def test_find_animals_filters_by_kids_and_status():
    names = [a["name"] for a in json.loads(shelter.find_animals("dog", True))]
    assert names == ["Biscuit"]
    # the only cat that is good with kids and still available
    assert [a["name"] for a in json.loads(shelter.find_animals("cat", True))] == ["Mochi"]


def test_reserve_rejects_adopted_and_unknown():
    assert "already adopted" in json.loads(shelter.reserve("A-202", "Ana"))["error"]
    assert "unknown" in json.loads(shelter.reserve("Z-9", "Ana"))["error"]
    assert json.loads(shelter.reserve("A-101", "Maya"))["code"].startswith("ADOPT-")


def test_surrender_days():
    assert "available_days" in json.loads(shelter.book_surrender("rabbit", "Monday", "Tomas"))
    assert json.loads(shelter.book_surrender("rabbit", "tuesday", "Tomas"))["status"] == "booked"


def test_foster_slots():
    assert json.loads(shelter.list_foster_slots("kitten"))[0]["id"] == "F-3"


def test_agents_wired_with_tracking_disabled():
    # Importing main installs the Opik processor; with OPIK_TRACK_DISABLE it must stay harmless.
    assert {h.name for h in main.triage_agent.handoffs} == {
        "Adoption Specialist", "Foster Coordinator", "Surrender Intake"}
    assert len(main.adoption_agent.tools) == 2
