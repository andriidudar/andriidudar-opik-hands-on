"""The assistant's tools: quotes, service slots and parts lookup.

Each tool returns plain dicts so results can be fed straight back to the model.
"""

import json

import opik

from bikeshop.data import load_shop


# type="tool" makes this a tool span, nested under the turn that called it, with
# its arguments as input and the returned dict as output.
@opik.track(type="tool")
def get_repair_quote(services: list[str], bike_type: str = "road") -> dict:
    shop = load_shop()
    items, unknown, parts_missing = [], [], []
    total = 0.0
    for name in services:
        svc = shop["services"].get(name.lower().strip())
        if svc is None:
            unknown.append(name)
            continue
        labor = svc["hours"] * shop["labor_rate_per_hour"]
        parts_cost = 0.0
        for pid in svc["parts"]:
            part = shop["parts"][pid]
            parts_cost += part["price"]
            if part["stock"] == 0:
                parts_missing.append(part["name"])
        items.append({"service": name, "labor": labor, "parts": parts_cost})
        total += labor + parts_cost
    surcharge = shop["bike_surcharge"].get(bike_type.lower(), 0)
    if items:
        total += surcharge
    return {
        "items": items,
        "bike_surcharge": surcharge if items else 0,
        "total": round(total, 2),
        "unknown_services": unknown,
        "parts_out_of_stock": parts_missing,
        "known_services": sorted(shop["services"]) if unknown else None,
    }


# type="tool" makes this a tool span, nested under the turn that called it, with
# its arguments as input and the returned dict as output.
@opik.track(type="tool")
def check_service_slots(date: str | None = None) -> dict:
    slots = load_shop()["slots"]
    if date:
        return {"date": date, "open_slots": slots.get(date, [])}
    return {"open_slots": {d: s for d, s in slots.items() if s}}


# type="tool" makes this a tool span, nested under the turn that called it, with
# its arguments as input and the returned dict as output.
@opik.track(type="tool")
def lookup_part(query: str) -> dict:
    words = query.lower().split()
    hits = [
        {"id": pid, **p}
        for pid, p in load_shop()["parts"].items()
        if all(w in (p["name"] + " " + pid).lower() for w in words)
    ]
    return {"query": query, "matches": hits}


REGISTRY = {
    "get_repair_quote": get_repair_quote,
    "check_service_slots": check_service_slots,
    "lookup_part": lookup_part,
}

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_repair_quote",
            "description": "Price a list of repair services for a bike type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "services": {"type": "array", "items": {"type": "string"}},
                    "bike_type": {"type": "string", "enum": ["road", "mountain", "ebike"]},
                },
                "required": ["services"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_service_slots",
            "description": "List open workshop slots, for one date (YYYY-MM-DD) or all dates.",
            "parameters": {
                "type": "object",
                "properties": {"date": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_part",
            "description": "Find parts by keyword and report price and stock.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
]


def run_tool(name: str, arguments: str) -> str:
    """Execute a tool call from the model; arguments arrive as a JSON string."""
    func = REGISTRY.get(name)
    if func is None:
        return json.dumps({"error": f"unknown tool {name}"})
    try:
        return json.dumps(func(**json.loads(arguments or "{}")))
    except (TypeError, ValueError) as exc:
        return json.dumps({"error": str(exc)})
