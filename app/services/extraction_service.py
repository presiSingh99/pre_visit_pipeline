"""Clinical intake extraction service (Sprint 1's single pipeline step).

`extract_intake` is a pure, stateless function: transcript in, validated
`IntakeExtractionResult` out. No HTTP, no storage side effects. This is the
shape a graph-orchestration node needs, so later sprints can wrap it
without modification (see app/pipeline/steps.py).
"""

from __future__ import annotations

import logging

from pydantic import ValidationError

from app.core.config import get_settings
from app.core.errors import ExtractionValidationError, LLMUnavailableError
from app.llm.client import call_extraction_model
from app.schemas.intake import (
    ExtractionMetadata,
    IntakeExtractionResult,
    PatientIntakeExtraction,
)

logger = logging.getLogger(__name__)


def _validate(raw: PatientIntakeExtraction) -> PatientIntakeExtraction:
    """Defensive re-validation + cross-field consistency checks.

    The SDK already validated the schema shape; here we treat the LLM
    output as untrusted input and enforce invariants the JSON schema
    cannot express.
    """
    try:
        extraction = PatientIntakeExtraction.model_validate(raw.model_dump())
    except ValidationError as exc:
        raise ExtractionValidationError(str(exc)) from exc

    # Invariant: the flag and its evidence list must agree.
    if extraction.red_flags_detected and not extraction.red_flag_symptoms:
        raise ExtractionValidationError(
            "red_flags_detected is true but red_flag_symptoms is empty."
        )
    if extraction.red_flag_symptoms and not extraction.red_flags_detected:
        # Evidence present but flag unset: fail closed by raising, so a
        # retry (or a human) resolves it rather than silently un-flagging.
        raise ExtractionValidationError(
            "red_flag_symptoms is non-empty but red_flags_detected is false."
        )
    return extraction


def extract_intake(transcript: str) -> IntakeExtractionResult:
    """Extract a validated intermediate clinical record from a transcript.

    Retries once (configurable) on validation failure, since a fresh
    sample usually resolves inconsistent output. Fails loudly rather than
    returning a partially trusted record.

    Raises:
        ConfigurationError, LLMUnavailableError, ExtractionValidationError
    """
    settings = get_settings()
    attempts = settings.llm_max_retries + 1
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            raw = call_extraction_model(transcript)
            extraction = _validate(raw)
            return IntakeExtractionResult(
                extraction=extraction,
                metadata=ExtractionMetadata(model=settings.openai_model),
            )
        except ExtractionValidationError as exc:
            last_error = exc
            logger.warning(
                "Extraction validation failed (attempt %d/%d): %s",
                attempt,
                attempts,
                exc,
            )
        except LLMUnavailableError as exc:
            last_error = exc
            logger.warning(
                "LLM unavailable (attempt %d/%d): %s", attempt, attempts, exc
            )

    assert last_error is not None
    raise last_error
