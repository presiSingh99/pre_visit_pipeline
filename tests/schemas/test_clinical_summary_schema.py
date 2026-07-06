"""Sprint 2 schema invariant tests (design section 5, schema tests 1–7)."""

import pytest
from pydantic import ValidationError

from app.schemas.clinical_summary import (
    ClinicalSummaryDraft,
    ClinicalSummaryResponse,
    ClinicalSummaryStatus,
    EvidenceRef,
    SummaryAtom,
    SummarySection,
    SummarySectionId,
    SummaryValidationIssue,
)

ATOM = SummaryAtom(text="Patient-stated chief concern: sore throat.", source_fields=["chief_complaint"])
ERROR = SummaryValidationIssue(code="X", message="boom", severity="error")


def make_draft(**overrides):
    base = dict(
        intake_id="intake_test",
        generated_at="2026-07-06T00:00:00Z",
        status=ClinicalSummaryStatus.draft,
        sections=[
            SummarySection(
                section_id=SummarySectionId.chief_concern,
                title="Chief concern",
                atoms=[ATOM],
            )
        ],
        source_schema_version="1.0.0",
    )
    base.update(overrides)
    return ClinicalSummaryDraft(**base)


def test_section_rejects_empty_atoms_without_omitted_reason():
    with pytest.raises(ValidationError):
        SummarySection(
            section_id=SummarySectionId.chief_concern, title="Chief concern", atoms=[]
        )
    # and passes with a reason
    SummarySection(
        section_id=SummarySectionId.chief_concern,
        title="Chief concern",
        atoms=[],
        omitted_reason="chief_complaint is missing",
    )


def test_draft_rejects_blocked_without_error_issue():
    with pytest.raises(ValidationError):
        make_draft(status=ClinicalSummaryStatus.blocked, validation_issues=[])
    make_draft(status=ClinicalSummaryStatus.blocked, validation_issues=[ERROR])


def test_response_rejects_ok_without_summary():
    with pytest.raises(ValidationError):
        ClinicalSummaryResponse(ok=True, summary=None)


def test_response_rejects_failure_without_errors():
    with pytest.raises(ValidationError):
        ClinicalSummaryResponse(ok=False, summary=None, errors=[])


def test_response_rejects_failure_with_nonblocked_summary():
    with pytest.raises(ValidationError):
        ClinicalSummaryResponse(ok=False, summary=make_draft(), errors=[ERROR])
    blocked = make_draft(
        status=ClinicalSummaryStatus.blocked, validation_issues=[ERROR]
    )
    ClinicalSummaryResponse(ok=False, summary=blocked, errors=[ERROR])


def test_evidence_confidence_bounds():
    with pytest.raises(ValidationError):
        EvidenceRef(field_path="chief_complaint", confidence=1.5)
    with pytest.raises(ValidationError):
        EvidenceRef(field_path="chief_complaint", confidence=-0.1)
    EvidenceRef(field_path="chief_complaint", confidence=0.9)


def test_evidence_span_must_be_valid_range():
    with pytest.raises(ValidationError):
        EvidenceRef(field_path="chief_complaint", transcript_span=(10, 5))
    with pytest.raises(ValidationError):
        EvidenceRef(field_path="chief_complaint", transcript_span=(-1, 5))


@pytest.mark.parametrize(
    "model,kwargs",
    [
        (SummaryAtom, dict(text="x", source_fields=["chief_complaint"])),
        (EvidenceRef, dict(field_path="chief_complaint")),
        (SummaryValidationIssue, dict(code="X", message="m", severity="error")),
    ],
)
def test_models_reject_unknown_keys(model, kwargs):
    with pytest.raises(ValidationError):
        model(**kwargs, unexpected_key="nope")
