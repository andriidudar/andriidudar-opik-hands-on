import argparse

from .data import load_artefacts
from .generate import write_label_local


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="museum_labels")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="write one label from a local prompt file")
    gen.add_argument("--version", default="v2", choices=["v1", "v2"])
    gen.add_argument("--accession", default=None)
    args = parser.parse_args(argv)

    if args.command == "generate":
        for artefact in load_artefacts():
            if args.accession in (None, artefact["accession"]):
                print(f"--- {artefact['title']} ---")
                print(write_label_local(artefact, args.version), "\n")
