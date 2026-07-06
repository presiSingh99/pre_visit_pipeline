"""Extraction service and API tests with the LLM mocked. No API key needed."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.errors import ExtractionValidationError, LLMUnavailableError
from app.main import app
from app.schemas.intake import PatientIntakeExtraction, Severity
from app.services.extraction_service import extract_intake

TRANSCRIPT = (
    "Patient reports a sharp sore throat for 3 days, pain when swallowing, "
    "mild fever, taking ibuprofen, allergic to penicillin, denies chest "
    "pain and shortness of breath."
)

MOCK_EXTRACTION = PatientIntakeExtraction(
    chief_complaint="sore throat",
    duration_days=3,
    severity=Severity.UNKNOWN,
    associated_symptoms=["pain when swallowing", "mild fever"],
    denied_symptoms=["chest pain", "shortness of breath"],
    current_medications=["ibuprofen"],
    allergies=["penicillin"],
    red_flags_detected=False,
    red_flag_symptoms=[],
)

MOCK_PATH = "app.services.extraction_service.call_extraction_model"


def test_extract_intake_returns_validated_result():
    with patch(MOCK_PATH, return_value=MOCK_EXTRACTION):
        result = extract_intake(TRANSCRIPT)
    assert result.extraction == MOCK_EXTRACTION
    assert result.metadata.schema_version == "1.0.0"
    assert result.metadata.model  # populated from settings


def test_red_flag_inconsistency_fails_closed():
    """Flag=true with no evidence must be rejected, not silently passed."""
    bad = MOCK_EXTRACTION.model_copy(
        update={"red_flags_detected": True, "red_flag_symptoms": []}
    )
    with patch(MOCK_PATH, return_value=bad):
        with pytest.raises(ExtractionValidationError):
            extract_intake(TRANSCRIPT)


def test_evidence_without_flag_fails_closed():
    bad = MOCK_EXTRACTION.model_copy(
        update={"red_flags_detected": False, "red_flag_symptoms": ["chest pain"]}
    )
    with patch(MOCK_PATH, return_value=bad):
        with pytest.raises(ExtractionValidationError):
            extract_intake(TRANSCRIPT)


def test_retry_recovers_from_one_bad_sample():
    bad = MOCK_EXTRACTION.model_copy(
        update={"red_flags_detected": True, "red_flag_symptoms": []}
    )
    with patch(MOCK_PATH, side_effect=[bad, MOCK_EXTRACTION]) as mock_call:
        result = extract_intake(TRANSCRIPT)
    assert mock_call.call_count == 2
    assert result.extraction == MOCK_EXTRACTION


def test_api_happy_path():
    client = TestClient(app)
    with patch(MOCK_PATH, return_value=MOCK_EXTRACTION):
        response = client.post("/extract-intake", json={"transcript": TRANSCRIPT})
    assert response.status_code == 200
    body = response.json()
    assert body["extraction"]["chief_complaint"] == "sore throat"
    assert body["extraction"]["duration_days"] == 3
    assert body["extraction"]["red_flags_detected"] is False
    assert body["metadata"]["schema_version"] == "1.0.0"


def test_api_maps_llm_failure_to_502():
    client = TestClient(app)
    with patch(MOCK_PATH, side_effect=LLMUnavailableError("boom")):
        response = client.post("/extract-intake", json={"transcript": TRANSCRIPT})
    assert response.status_code == 502


def test_api_rejects_empty_transcript():
    client = TestClient(app)
    response = client.post("/extract-intake", json={"transcript": ""})
    assert response.status_code == 422


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
