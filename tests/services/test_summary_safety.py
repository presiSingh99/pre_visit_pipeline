"""Safety tests (design section 5): guardrails must reject unsafe output."""

from datetime import datetime, timezone

from app.schemas.clinical_summary import (
    ClinicalSummaryDraft,
    ClinicalSummaryRenderRequest,
    ClinicalSummaryStatus,
    SummaryAtom,
    SummarySection,
    SummarySectionId,
)
from app.services.clinical_summary_engine import ClinicalSummaryEngine
from app.services.summary_rendering import render_markdown
from app.services.summary_validation import validate_summary_output
from tests.fixtures.patient_intake_extractions import rich_valid

FROZEN = datetime(2026, 7, 6, tzinfo=timezone.utc)


def draft_with_atom(atom: SummaryAtom) -> ClinicalSummaryDraft:
    return ClinicalSummaryDraft(
        intake_id="intake_test",
        generated_at=FROZEN,
        status=ClinicalSummaryStatus.draft,
        sections=[
            SummarySection(
                section_id=SummarySectionId.symptom_summary,
                title="Symptom summary",
                atoms=[atom],
            )
        ],
        source_schema_version="1.0.0",
    )


def codes(issues):
    return {i.code for i in issues if i.severity == "error"}


def test_diagnosis_language_rejected():
    atom = SummaryAtom(
        text="Symptoms are consistent with strep.", source_fields=["chief_complaint"]
    )
    assert "DIAGNOSIS_LANGUAGE" in codes(
        validate_summary_output(draft_with_atom(atom), rich_valid())
    )


def test_treatment_language_rejected():
    atom = SummaryAtom(
        text="Recommend antibiotics.", source_fields=["chief_complaint"]
    )
    assert "TREATMENT_LANGUAGE" in codes(
        validate_summary_output(draft_with_atom(atom), rich_valid())
    )


def test_patient_stated_phrase_is_allowed_verbatim():
    """Guardrail exemption: phrase appears verbatim in a source field."""
    extraction = rich_valid().model_copy(
        update={"associated_symptoms": ["feels likely to faint when standing"]}
    )
    atom = SummaryAtom(
        text="Patient reported: feels likely to faint when standing.",
        source_fields=["associated_symptoms[0]"],
    )
    assert "DIAGNOSIS_LANGUAGE" not in codes(
        validate_summary_output(draft_with_atom(atom), extraction)
    )


def test_unknown_source_field_rejected():
    atom = SummaryAtom(text="Patient reported: cough.", source_fields=["symptoms[9]"])
    assert "UNKNOWN_SOURCE_FIELD" in codes(
        validate_summary_output(draft_with_atom(atom), rich_valid())
    )


def test_out_of_range_index_rejected():
    atom = SummaryAtom(
        text="Patient reported: cough.", source_fields=["associated_symptoms[9]"]
    )
    assert "UNKNOWN_SOURCE_FIELD" in codes(
        validate_summary_output(draft_with_atom(atom), rich_valid())
    )


def test_unsupported_numeric_value_rejected():
    atom = SummaryAtom(
        text="Patient-reported duration: 10 day(s).", source_fields=["duration_days"]
    )
    assert "UNSUPPORTED_VALUE" in codes(
        validate_summary_output(draft_with_atom(atom), rich_valid())
    )


def test_engine_output_passes_its_own_guardrails():
    response = ClinicalSummaryEngine().build(rich_valid())
    assert response.ok
    assert validate_summary_output(response.summary, rich_valid()) == []


def test_renderer_adds_no_content_beyond_draft():
    response = ClinicalSummaryEngine().build(rich_valid())
    draft = response.summary
    markdown = render_markdown(draft, ClinicalSummaryRenderRequest())
    allowed_fragments = (
        [a.text for s in draft.sections for a in s.atoms]
        + [s.title for s in draft.sections]
        + [s.omitted_reason for s in draft.sections if s.omitted_reason]
        + [q.question for q in draft.missing_or_unresolved_questions]
        + [q.reason for q in draft.missing_or_unresolved_questions]
        + [draft.intake_id, draft.status.value]
    )
    for line in markdown.splitlines():
        content = line.strip().lstrip("#->*_ ").rstrip("*_ ")
        if not content:
            continue
        assert any(fragment in line for fragment in allowed_fragments) or (
            "clinician review only" in line  # fixed safety notice
            or content.startswith("Status:")
            or content.startswith("Doctor-review draft summary")
            or content.startswith("Omitted:")
            or content.startswith("Open questions")
        ), f"renderer introduced unexpected content: {line!r}"
