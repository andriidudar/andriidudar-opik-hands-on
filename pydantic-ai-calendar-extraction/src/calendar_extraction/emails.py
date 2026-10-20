import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "emails.json"


def load_emails() -> list[dict]:
    return json.loads(DATA_FILE.read_text())


def render_email(email: dict) -> str:
    """Flatten an email record into the plain text the agent sees (no expected answers)."""
    lines = [f"Date: {email['date']}", f"From: {email['from']}", f"To: {email['to']}"]
    if email.get("cc"):
        lines.append(f"Cc: {email['cc']}")
    lines += [f"Subject: {email['subject']}", "", email["body"]]
    return "\n".join(lines)
