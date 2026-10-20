"""Opik wiring for the router."""

import logging
import warnings

import litellm
from litellm.integrations.opik.opik import OpikLogger
import opik

_installed = False


def install_opik_logger() -> None:
    """Register LiteLLM's OpikLogger once.

    With the callback in litellm.callbacks, every litellm.completion() is sent to Opik
    as an llm span carrying model, provider, token usage and estimated cost. Without it
    LiteLLM calls are invisible to Opik.
    """
    global _installed
    if not _installed:
        # Outside an event loop OpikLogger logs a scary but harmless "no running event
        # loop" traceback and falls back to synchronous sending; mute it for construction.
        logger = logging.getLogger("LiteLLM")
        previous = logger.level
        logger.setLevel(logging.CRITICAL)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            litellm.callbacks = [OpikLogger()]
        logger.setLevel(previous)
        _installed = True


def llm_metadata(model_tag: str) -> dict:
    """Metadata for litellm.completion() that nests its llm span under the open review_diff span.

    current_span_data is what attaches LiteLLM's span to the surrounding @opik.track trace;
    leave it out and the llm call becomes a separate, parentless trace. The tag lands on
    the llm span so the Opik spans table can be filtered per model.
    """
    return {
        "opik": {
            "current_span_data": opik.opik_context.get_current_span_data(),
            "tags": [model_tag],
        }
    }


def label_trace(model_tag: str, diff_name: str) -> None:
    """Tag the enclosing trace with the model so the Traces table can be filtered and compared per model."""
    opik.opik_context.update_current_trace(
        tags=[model_tag],
        metadata={"model": model_tag, "diff": diff_name},
    )


def flush() -> None:
    """Block until queued traces are sent; scripts that exit early would otherwise drop them."""
    opik.flush_tracker()
