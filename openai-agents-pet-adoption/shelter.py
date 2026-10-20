"""Fictional shelter data and the plain-Python logic behind the agents' tools."""

import json
import uuid

ANIMALS = [
    {"id": "A-101", "name": "Biscuit", "species": "dog", "age_years": 3, "good_with_kids": True, "status": "available"},
    {"id": "A-102", "name": "Juniper", "species": "dog", "age_years": 7, "good_with_kids": False, "status": "available"},
    {"id": "A-201", "name": "Mochi", "species": "cat", "age_years": 1, "good_with_kids": True, "status": "available"},
    {"id": "A-202", "name": "Captain Whiskers", "species": "cat", "age_years": 9, "good_with_kids": True, "status": "adopted"},
    {"id": "A-301", "name": "Pip", "species": "rabbit", "age_years": 2, "good_with_kids": True, "status": "available"},
]

FOSTER_SLOTS = [
    {"id": "F-1", "species": "dog", "weeks": 4, "needs": "fenced yard"},
    {"id": "F-2", "species": "cat", "weeks": 2, "needs": "quiet room"},
    {"id": "F-3", "species": "kitten", "weeks": 8, "needs": "bottle feeding every 3 hours"},
]

# Surrender appointments are only offered on these days.
SURRENDER_DAYS = ["Tuesday", "Thursday", "Saturday"]


def find_animals(species: str, kid_friendly: bool) -> str:
    matches = [
        a for a in ANIMALS
        if a["species"] == species.lower() and a["status"] == "available"
        and (a["good_with_kids"] or not kid_friendly)
    ]
    return json.dumps(matches if matches else {"error": "no matching animals"})


def reserve(animal_id: str, adopter_name: str) -> str:
    animal = next((a for a in ANIMALS if a["id"] == animal_id), None)
    if animal is None:
        return json.dumps({"error": f"unknown animal id {animal_id}"})
    if animal["status"] != "available":
        return json.dumps({"error": f"{animal['name']} is already {animal['status']}"})
    return json.dumps({
        "status": "reserved", "animal": animal["name"], "adopter": adopter_name,
        "code": f"ADOPT-{uuid.uuid4().hex[:6].upper()}",
    })


def list_foster_slots(species: str) -> str:
    matches = [s for s in FOSTER_SLOTS if species.lower() in s["species"]]
    return json.dumps(matches if matches else {"error": "no foster slots for that species"})


def book_surrender(species: str, day: str, owner_name: str) -> str:
    if day.capitalize() not in SURRENDER_DAYS:
        return json.dumps({"error": f"no surrender appointments on {day}", "available_days": SURRENDER_DAYS})
    return json.dumps({
        "status": "booked", "owner": owner_name, "species": species, "day": day.capitalize(),
        "confirmation": f"SURR-{uuid.uuid4().hex[:6].upper()}",
    })
