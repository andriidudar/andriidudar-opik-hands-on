import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_artefacts() -> list[dict]:
    return json.loads((ROOT / "data" / "artefacts.json").read_text())


def load_prompt(version: str) -> str:
    """Read a prompt version ("v1" or "v2") from prompts/<version>.txt."""
    return (ROOT / "prompts" / f"{version}.txt").read_text().strip()


def describe(artefact: dict) -> str:
    """Render one catalogue record as the user message."""
    provenance = artefact["provenance"] or "(none recorded)"
    return (
        f"Accession number: {artefact['accession']}\n"
        f"Title: {artefact['title']}\n"
        f"Date: {artefact['date']}\n"
        f"Maker: {artefact['maker']}\n"
        f"Medium: {artefact['medium']}\n"
        f"Dimensions: {artefact['dimensions']}\n"
        f"Facts: {artefact['facts']}\n"
        f"Provenance: {provenance}"
    )
