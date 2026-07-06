"""Engine behavior tests (design section 5, engine tests 1–10)."""

from datetime import datetime, timezone

from app.schemas.clinical_summary import ClinicalSummaryStatus, SummarySectionId
from app.services.clinical_summary_engine import ClinicalSummaryEngine
from tests.fixtures.patient_intake_extractions import (
    contradicted,
    minimal_valid,
    missing_required,
    red_flag_case,
    rich_valid,
)

FROZEN = datetime(2026, 7, 6, 0, 0, 0, tzinfo=timezone.utc)


class FrozenClock:
    def utcnow(self) -> datetime:
        return FROZEN


def engine() -> ClinicalSummaryEngine:
    return ClinicalSummaryEngine(clock=FrozenClock())


def section(response, section_id):
    return next(
        s for s in response.summary.sections if s.section_id == section_id
    )


def test_minimal_valid_produces_draft():
    response = engine().build(minimal_valid())
    assert response.ok is True
    assert response.summary.status is ClinicalSummaryStatus.draft
    assert response.summary.generated_at == FROZEN


def test_chief_concern_maps_with_source_fields():
    response = engine().build(rich_valid())
    chief = section(response, SummarySectionId.chief_concern)
    assert chief.atoms[0].text == "Patient-stated chief concern: sore throat."
    assert chief.atoms[0].source_fields == ["chief_complaint"]


def test_symptom_atoms_are_factual_and_source_grounded():
    response = engine().build(rich_valid())
    symptoms = section(response, SummarySectionId.symptom_summary)
    texts = [a.text for a in symptoms.atoms]
    assert "Patient-reported duration: 3 day(s)." in texts
    assert "Patient-described severity: moderate." in texts
    assert "Patient reported: mild fever." in texts
    assert "Patient denied: chest pain." in texts
    assert all(a.source_fields for a in symptoms.atoms)


def test_missing_optional_fields_become_omissions_or_questions_not_facts():
    response = engine().build(minimal_valid())
    meds = section(response, SummarySectionId.medications_allergies)
    assert meds.atoms == [] and meds.omitted_reason
    question_fields = {
        f
        for q in response.summary.missing_or_unresolved_questions
        for f in q.related_source_fields
    }
    assert {"duration_days", "severity", "current_medications", "allergies"} <= (
        question_fields
    )


def test_contradicted_symptom_becomes_question_and_no_selected_fact():
    response = engine().build(contradicted())
    assert response.ok is True
    symptoms = section(response, SummarySectionId.symptom_summary)
    joined = " ".join(a.text for a in symptoms.atoms)
    assert "headache" not in joined  # neither reported nor denied is asserted
    assert "nausea" in joined  # non-contradicted facts survive
    assert any(
        "headache" in q.question
        for q in response.summary.missing_or_unresolved_questions
    )


def test_missing_required_anchor_blocks():
    response = engine().build(missing_required())
    assert response.ok is False
    assert response.summary.status is ClinicalSummaryStatus.blocked
    assert any(e.code == "MISSING_REQUIRED_FIELD" for e in response.errors)


def test_red_flags_surface_in_symptom_summary():
    response = engine().build(red_flag_case())
    symptoms = section(response, SummarySectionId.symptom_summary)
    assert any("red-flag" in a.text for a in symptoms.atoms)


def test_frozen_clock_makes_snapshots_stable():
    a = engine().build(rich_valid())
    b = engine().build(rich_valid())
    assert a.model_dump() == b.model_dump()


def test_determinism_apart_from_timestamp_without_frozen_clock():
    live = ClinicalSummaryEngine()
    a = live.build(rich_valid()).model_dump()
    b = live.build(rich_valid()).model_dump()
    a["summary"].pop("generated_at")
    b["summary"].pop("generated_at")
    assert a == b


def test_engine_input_carries_no_transcript():
    """The engine's only input type has no transcript field to read."""
    fields = set(type(rich_valid()).model_fields)
    assert "transcript" not in fields
    response = engine().build(rich_valid())
    dumped = response.model_dump_json().lower()
    assert "ai:" not in dumped and "patient:" not in dumped


def test_derived_intake_id_is_deterministic_and_overridable():
    a = engine().build(rich_valid()).summary.intake_id
    b = engine().build(rich_valid()).summary.intake_id
    assert a == b and a.startswith("intake_")
    custom = engine().build(rich_valid(), intake_id="intake_123").summary.intake_id
    assert custom == "intake_123"
