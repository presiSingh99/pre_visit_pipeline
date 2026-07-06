"""Schema validation tests. No network or API key required."""

import pytest
from pydantic import ValidationError

from app.schemas.intake import (
    ExtractIntakeRequest,
    PatientIntakeExtraction,
    Severity,
)


def test_empty_extraction_is_valid_and_conservative():
    """A transcript with no clinical facts must yield a valid, empty record."""
    extraction = PatientIntakeExtraction()
    assert extraction.chief_complaint is None
    assert extraction.duration_days is None
    assert extraction.severity is Severity.UNKNOWN
    assert extraction.associated_symptoms == []
    assert extraction.denied_symptoms == []
    assert extraction.current_medications == []
    assert extraction.allergies == []
    assert extraction.red_flags_detected is False
    assert extraction.red_flag_symptoms == []


def test_full_extraction_round_trips():
    extraction = PatientIntakeExtraction(
        chief_complaint="sore throat",
        duration_days=3,
        severity="moderate",
        associated_symptoms=["pain when swallowing", "mild fever"],
        denied_symptoms=["chest pain", "shortness of breath"],
        current_medications=["ibuprofen"],
        allergies=["penicillin"],
        red_flags_detected=False,
        red_flag_symptoms=[],
    )
    dumped = extraction.model_dump()
    assert PatientIntakeExtraction.model_validate(dumped) == extraction


def test_extra_fields_are_rejected():
    """LLM output containing fields we didn't ask for must fail closed."""
    with pytest.raises(ValidationError):
        PatientIntakeExtraction.model_validate(
            {"chief_complaint": "sore throat", "suggested_diagnosis": "strep"}
        )


def test_invalid_severity_rejected():
    with pytest.raises(ValidationError):
        PatientIntakeExtraction(severity="catastrophic")


def test_negative_duration_rejected():
    with pytest.raises(ValidationError):
        PatientIntakeExtraction(duration_days=-1)


def test_request_requires_nonempty_transcript():
    with pytest.raises(ValidationError):
        ExtractIntakeRequest(transcript="")
    with pytest.raises(ValidationError):
        ExtractIntakeRequest.model_validate({})
