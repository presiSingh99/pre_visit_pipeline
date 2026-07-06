"""API tests for POST /api/v1/clinical-summary (design section 5)."""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.clinical_summary import ClinicalSummaryAPIResponse
from tests.fixtures.patient_intake_extractions import (
    minimal_valid,
    missing_required,
    rich_valid,
)

client = TestClient(app)
URL = "/api/v1/clinical-summary"


def post(intake, **extra):
    return client.post(URL, json={"intake": intake, **extra})


def test_valid_extraction_returns_200():
    response = post(rich_valid().model_dump(mode="json"))
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["summary"]["status"] == "draft"


def test_malformed_json_returns_400():
    response = client.post(
        URL, content=b"{not json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400


def test_unparseable_extraction_returns_400():
    response = post({"chief_complaint": "x", "suggested_diagnosis": "strep"})
    assert response.status_code == 400


def test_blocked_summary_returns_422():
    response = post(missing_required().model_dump(mode="json"))
    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["summary"]["status"] == "blocked"
    assert body["errors"]


def test_response_validates_against_schema():
    response = post(minimal_valid().model_dump(mode="json"))
    ClinicalSummaryAPIResponse.model_validate(response.json())


def test_evidence_included_by_default_render_can_suppress_display_only():
    intake = rich_valid().model_dump(mode="json")
    with_evidence = post(intake).json()
    suppressed = post(
        intake, render={"format": "markdown", "include_evidence": False}
    ).json()
    # Display suppression must not strip evidence from the JSON summary.
    assert with_evidence["summary"]["sections"] == suppressed["summary"]["sections"]
    assert suppressed["rendered_markdown"] is not None
    assert "evidence:" not in suppressed["rendered_markdown"]


def test_json_format_skips_markdown_rendering():
    response = post(
        rich_valid().model_dump(mode="json"), render={"format": "json"}
    ).json()
    assert response["rendered_markdown"] is None


def test_custom_intake_id_is_honored():
    response = post(minimal_valid().model_dump(mode="json"), intake_id="intake_123")
    assert response.json()["summary"]["intake_id"] == "intake_123"
