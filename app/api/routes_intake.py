"""HTTP edge for the intake extraction service."""

from fastapi import APIRouter, HTTPException

from app.core.errors import (
    ConfigurationError,
    ExtractionValidationError,
    LLMUnavailableError,
)
from app.schemas.intake import ExtractIntakeRequest, IntakeExtractionResult
from app.services.extraction_service import extract_intake

router = APIRouter(tags=["intake"])


@router.post("/extract-intake", response_model=IntakeExtractionResult)
def post_extract_intake(payload: ExtractIntakeRequest) -> IntakeExtractionResult:
    """Extract validated intermediate clinical JSON from a raw transcript.

    Extraction only — no diagnosis, no prescribing, no medical advice.
    Missing information stays null / empty / unknown.
    """
    try:
        return extract_intake(payload.transcript)
    except ConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ExtractionValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Extraction failed validation and was rejected: {exc}",
        ) from exc
