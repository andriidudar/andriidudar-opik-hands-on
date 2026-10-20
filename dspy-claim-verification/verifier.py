"""The claim-verification program, its strict output format and its metric.

Pure DSPy plus the standard library: nothing here touches Opik, so the
parsing and scoring logic can be unit-tested offline.
"""

import json
import pathlib
import re

import dspy

DATA = pathlib.Path(__file__).parent / "data"
ALMANAC = (DATA / "almanac.txt").read_text()
CLAIMS = json.loads((DATA / "claims.json").read_text())

VERDICTS = ("SUPPORTED", "REFUTED", "NOT ENOUGH INFO")

# The strict house format: one line, nothing else.
#   SUPPORTED | evidence: L07      NOT ENOUGH INFO | evidence: none
ANSWER_FORMAT = re.compile(
    r"^(SUPPORTED|REFUTED|NOT ENOUGH INFO) \| evidence: (L\d{2}|none)$"
)


class VerifyClaim(dspy.Signature):
    """Decide whether the claim is supported by the fact sheet."""

    fact_sheet: str = dspy.InputField(desc="numbered lines of an almanac")
    claim: str = dspy.InputField()
    verdict: str = dspy.OutputField()


class ClaimVerifier(dspy.Module):
    """One ChainOfThought step. Wrapping it in a Module gives the Opik trace
    a named root (ClaimVerifier) above the ChainOfThought, Predict and LM spans."""

    def __init__(self) -> None:
        super().__init__()
        # The signature never mentions the output format: the uncompiled
        # program has to guess it, and only compiled demos teach it.
        self.check = dspy.ChainOfThought(VerifyClaim)

    def forward(self, claim: str, fact_sheet: str = ALMANAC) -> dspy.Prediction:
        return self.check(fact_sheet=fact_sheet, claim=claim)


def parse_answer(text: str) -> tuple[str, str] | None:
    """Return (verdict, evidence) when `text` matches the format exactly."""
    match = ANSWER_FORMAT.match(text.strip())
    return (match.group(1), match.group(2)) if match else None


def to_example(row: dict) -> dspy.Example:
    gold = f"{row['verdict']} | evidence: {row['evidence']}"
    return dspy.Example(
        fact_sheet=ALMANAC, claim=row["claim"], verdict=gold,
        gold_verdict=row["verdict"], gold_evidence=row["evidence"],
    ).with_inputs("fact_sheet", "claim")


def verdict_metric(example: dspy.Example, prediction, trace=None) -> bool:
    """Compile-time metric: exact format, right verdict, right evidence line.
    Purely programmatic, so compiling spends no judge tokens."""
    parsed = parse_answer(prediction.verdict)
    return parsed == (example.gold_verdict, example.gold_evidence)
