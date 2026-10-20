"""PII redaction pipeline: detect -> classify -> redact -> verify.

Every trace and span is created with the low-level Opik client. No @track, no
integration wrapper: the OpenAI call is the plain `openai` client and its token
usage is copied onto the span by hand.
"""
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import opik
from openai import OpenAI

MODEL = "gpt-4o-mini"
PROJECT = "python-sdk-manual-redaction"
CATEGORIES = {"identity", "contact", "financial", "health", "location"}

DETECT_PROMPT = (
    "You find personal data in a document. Return JSON: "
    '{"entities": [{"text": "<exact substring>", "kind": "<name|phone|email|address|date|card|id>"}]}. '
    "Include only real-person data; skip company names, products and places that are not home addresses."
)
CLASSIFY_PROMPT = (
    "Classify each entity into one category of: identity, contact, financial, health, location. "
    'Return JSON: {"labels": [{"text": "...", "category": "..."}]}. Use the document for context.'
)
VERIFY_PROMPT = (
    "You audit a redacted document. List any remaining personal data about private individuals "
    "(names, first names, phones, emails, addresses, ids, card numbers) that was NOT replaced by a [TAG] placeholder. "
    "Ignore the placeholders themselves, companies, products, weekdays and other non-personal text. "
    'Return JSON: {"leaks": ["..."], "confidence": <0..1 that no personal data remains>}.'
)


def now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class LLMResult:
    data: dict
    usage: dict
    model: str


def chat_json(client: OpenAI, system: str, user: str) -> LLMResult:
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return LLMResult(
        data=json.loads(resp.choices[0].message.content),
        usage={
            "prompt_tokens": resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "total_tokens": resp.usage.total_tokens,
        },
        model=resp.model,
    )


def redact_text(text: str, labels: list[dict]) -> tuple[str, int]:
    """Replace each labelled entity with [CATEGORY]; longest first so substrings don't clobber."""
    count = 0
    for item in sorted(labels, key=lambda x: -len(x.get("text", ""))):
        needle = item.get("text", "")
        category = item.get("category", "identity")
        if category not in CATEGORIES:
            category = "identity"
        if needle and needle in text:
            count += text.count(needle)
            text = text.replace(needle, f"[{category.upper()}]")
    return text, count


def leak_check(redacted: str, originals: list[str]) -> list[str]:
    """Deterministic check: which detected strings still appear verbatim."""
    return [o for o in originals if o and o in redacted]


def llm_span(parent, name: str, system: str, user: str, result: LLMResult, start: datetime | None = None):
    """Hand-build an llm span under `parent`, sent complete (input, output, usage, end_time) in one call."""
    # type="llm" plus model/provider/usage is what lets Opik compute cost; omit usage and cost is blank.
    span = parent.span(
        name=name,
        type="llm",
        input={"system": system, "user": user},
        model=result.model,
        provider="openai",
        usage=result.usage,
        output=result.data,
        start_time=start,
        end_time=now(),
    )
    return span


def process_document(opik_client: opik.Opik, oai: OpenAI, path: Path) -> dict:
    text = path.read_text()
    trace_start = now()
    # One trace per document: the root of the hand-built tree, with tags for filtering.
    trace = opik_client.trace(
        name="redact-document",
        input={"file": path.name, "chars": len(text)},
        tags=["pii-redaction"],
        metadata={"model": MODEL},
        start_time=trace_start,
    )

    # Each stage span is created once, already complete (output + start/end time). Calling span.end()
    # right after creation makes the SDK warn that the batched update may be lost, so we avoid it.
    # The llm span is a child of the stage span, so the stage and the model call show as separate rows.
    t = now()
    detected = chat_json(oai, DETECT_PROMPT, text)
    entities = detected.data.get("entities", [])
    stage = trace.span(name="detect", type="general", input={"text": text}, output={"entities": entities}, start_time=t, end_time=now())
    llm_span(stage, f"chat {MODEL}", DETECT_PROMPT, text, detected, t)

    t = now()
    payload = json.dumps({"document": text, "entities": entities})
    classified = chat_json(oai, CLASSIFY_PROMPT, payload)
    labels = classified.data.get("labels", [])
    stage = trace.span(name="classify", type="general", input={"entities": entities}, output={"labels": labels}, start_time=t, end_time=now())
    llm_span(stage, f"chat {MODEL}", CLASSIFY_PROMPT, payload, classified, t)

    # redact is plain code, so it is a "tool" span with no model or usage.
    t = now()
    redacted, replaced = redact_text(text, labels)
    trace.span(name="redact", type="tool", input={"labels": labels}, output={"redacted": redacted, "replacements": replaced}, start_time=t, end_time=now())

    # verify is a "guardrail" span carrying the pass/fail verdict; its child llm span is the audit call.
    t = now()
    audit = chat_json(oai, VERIFY_PROMPT, redacted)
    verbatim = leak_check(redacted, [e.get("text", "") for e in entities])
    llm_leaks = audit.data.get("leaks", [])
    confidence = float(audit.data.get("confidence", 0))
    passed = not verbatim and not llm_leaks
    stage = trace.span(
        name="verify", type="guardrail", input={"redacted": redacted},
        output={"passed": passed, "verbatim_leaks": verbatim, "llm_leaks": llm_leaks}, start_time=t, end_time=now(),
    )
    llm_span(stage, f"chat {MODEL}", VERIFY_PROMPT, redacted, audit, t)

    # Feedback scores live on the trace: filterable columns in the traces table.
    trace.log_feedback_score(name="redaction_confidence", value=confidence, reason=f"{len(llm_leaks)} leak(s) reported by auditor")
    trace.log_feedback_score(name="leak_check", value=1.0 if passed else 0.0, reason="no verbatim or audited leaks" if passed else f"leaks: {verbatim + llm_leaks}")

    # Re-sending the trace with the same id and an output/end_time updates the row; trace.end() would
    # emit the same update but the SDK warns that an end() right after creation can be lost when batched.
    opik_client.trace(
        id=trace.id, name="redact-document", input={"file": path.name, "chars": len(text)}, output={"redacted": redacted, "passed": passed},
        tags=["pii-redaction"], metadata={"model": MODEL}, start_time=trace_start, end_time=now(),
    )
    return {"file": path.name, "entities": len(entities), "replaced": replaced, "passed": passed, "confidence": confidence}


def main(skip_flush: bool = False) -> None:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    load_dotenv()
    oai = OpenAI()
    # project_name routes every trace to one project; the client batches and sends them in the background.
    client = opik.Opik(project_name=PROJECT)
    for path in sorted(Path(__file__).parent.joinpath("data").glob("*.txt")):
        r = process_document(client, oai, path)
        print(f"{r['file']:22} entities={r['entities']} replaced={r['replaced']} passed={r['passed']} confidence={r["confidence"]:.2f}", flush=True)
    if skip_flush:
        # Simulates a killed worker: exits without flush() or the atexit hooks.
        os._exit(0)
    # flush() blocks until the background queue is delivered; a hard-killed process loses whatever is still queued.
    client.flush()


if __name__ == "__main__":
    import sys

    main(skip_flush="--skip-flush" in sys.argv)
