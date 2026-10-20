import argparse

from .agent import MODEL, extract_event
from .emails import load_emails, render_email


def cmd_extract(args: argparse.Namespace) -> None:
    emails = [e for e in load_emails() if args.email in (None, e["id"])]
    print(f"Extracting {len(emails)} emails with {MODEL}\n")
    for email in emails:
        event = extract_event(render_email(email))
        print(f"[{email['id']}]\n{event.model_dump_json(indent=2)}\n")


def main() -> None:
    parser = argparse.ArgumentParser(prog="calendar-extraction")
    sub = parser.add_subparsers(dest="command", required=True)
    extract = sub.add_parser("extract", help="extract an event from each email and print it")
    extract.add_argument("--email", help="only this email id")
    extract.set_defaults(func=cmd_extract)
    args = parser.parse_args()
    args.func(args)
