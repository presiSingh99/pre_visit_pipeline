"""Deterministic clinical summary engine (Sprint 2).

Transforms a validated ``PatientIntakeExtraction`` into a
``ClinicalSummaryResponse``. Deliberately deterministic: no LLM, no raw
transcript access, no clinical judgment. Every atom cites its source
fields; contradicted facts become unresolved questions rather than picked
sides; anything the design's sections need but Sprint 1 does not capture
is omitted with an explicit reason.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Protocol

from app.schemas.clinical_summary import (
    ClinicalSummaryDraft,
    ClinicalSummaryResponse,
    ClinicalSummaryStatus,
    MissingOrUnresolvedQuestion,
    MissingQuestionSeverity,
    SummaryAtom,
    SummarySection,
    SummarySectionId,
)
from app.schemas.intake import PatientIntakeExtraction, SCHEMA_VERSION, Severity
from app.services.summary_field_access import list_item_paths
from app.services.summary_validation import (
    blocked_response,
    find_contradicted_symptoms,
    validate_summary_inputs,
    validate_summary_output,
)

_NOT_CAPTURED = (
    "not captured by PatientIntakeExtraction schema v{v} (Sprint 1)".format(
        v=SCHEMA_VERSION
    )
)


class Clock(Protocol):
    def utcnow(self) -> datetime: ...


class SystemClock:
    def utcnow(self) -> datetime:
        return datetime.now(timezone.utc)


def derive_intake_id(extraction: PatientIntakeExtraction) -> str:
    """Deterministic id from extraction content (Sprint 1 has no intake_id).

    Keeps the design's idempotency invariant: identical inputs produce
    identical summaries apart from ``generated_at``.
    """
    canonical = json.dumps(extraction.model_dump(mode="json"), sort_keys=True)
    return "intake_" + hashlib.sha256(canonical.encode()).hexdigest()[:12]


# --- Section builders -------------------------------------------------------


def build_patient_context(extraction: PatientIntakeExtraction) -> SummarySection:
    return SummarySection(
        section_id=SummarySectionId.patient_context,
        title="Patient context",
        omitted_reason=_NOT_CAPTURED,
    )


def build_chief_concern(extraction: PatientIntakeExtraction) -> SummarySection:
    atoms = []
    if extraction.chief_complaint:
        atoms.append(
            SummaryAtom(
                text=f"Patient-stated chief concern: {extraction.chief_complaint}.",
                source_fields=["chief_complaint"],
            )
        )
    return SummarySection(
        section_id=SummarySectionId.chief_concern,
        title="Chief concern",
        atoms=atoms,
        omitted_reason=None if atoms else "chief_complaint is missing",
    )


def build_symptom_summary(
    extraction: PatientIntakeExtraction, contradicted: list[str]
) -> SummarySection:
    atoms: list[SummaryAtom] = []
    contradicted_set = set(contradicted)

    if extraction.duration_days is not None:
        atoms.append(
            SummaryAtom(
                text=f"Patient-reported duration: {extraction.duration_days} day(s).",
                source_fields=["duration_days"],
            )
        )
    if extraction.severity is not Severity.UNKNOWN:
        atoms.append(
            SummaryAtom(
                text=f"Patient-described severity: {extraction.severity.value}.",
                source_fields=["severity"],
            )
        )
    for item in list_item_paths(extraction, "associated_symptoms"):
        if item.value.strip().lower() in contradicted_set:
            continue  # contradicted: surfaced as unresolved question instead
        atoms.append(
            SummaryAtom(
                text=f"Patient reported: {item.value}.",
                source_fields=[item.field_path],
            )
        )
    for item in list_item_paths(extraction, "denied_symptoms"):
        if item.value.strip().lower() in contradicted_set:
            continue
        atoms.append(
            SummaryAtom(
                text=f"Patient denied: {item.value}.",
                source_fields=[item.field_path],
            )
        )
    if extraction.red_flags_detected and extraction.red_flag_symptoms:
        atoms.append(
            SummaryAtom(
                text=(
                    "Patient reported red-flag symptom(s): "
                    + ", ".join(extraction.red_flag_symptoms)
                    + "."
                ),
                source_fields=["red_flags_detected", "red_flag_symptoms"],
            )
        )
    return SummarySection(
        section_id=SummarySectionId.symptom_summary,
        title="Symptom summary",
        atoms=atoms,
        omitted_reason=None if atoms else "no symptom details were stated",
    )


def build_history_context(extraction: PatientIntakeExtraction) -> SummarySection:
    return SummarySection(
        section_id=SummarySectionId.history_context,
        title="History and context",
        omitted_reason=_NOT_CAPTURED,
    )


def build_medications_allergies(
    extraction: PatientIntakeExtraction,
) -> SummarySection:
    atoms: list[SummaryAtom] = []
    for item in list_item_paths(extraction, "current_medications"):
        atoms.append(
            SummaryAtom(
                text=f"Patient-reported current medication: {item.value}.",
                source_fields=[item.field_path],
            )
        )
    for item in list_item_paths(extraction, "allergies"):
        atoms.append(
            SummaryAtom(
                text=f"Patient-reported allergy: {item.value}.",
                source_fields=[item.field_path],
            )
        )
    return SummarySection(
        section_id=SummarySectionId.medications_allergies,
        title="Medications and allergies",
        atoms=atoms,
        omitted_reason=(
            None if atoms else "no medications or allergies were stated"
        ),
    )


def build_social_context(extraction: PatientIntakeExtraction) -> SummarySection:
    return SummarySection(
        section_id=SummarySectionId.social_context,
        title="Social context",
        omitted_reason=_NOT_CAPTURED,
    )


def build_care_goals_or_preferences(
    extraction: PatientIntakeExtraction,
) -> SummarySection:
    return SummarySection(
        section_id=SummarySectionId.care_goals_or_preferences,
        title="Care goals or preferences",
        omitted_reason=_NOT_CAPTURED,
    )


def build_missing_questions(
    extraction: PatientIntakeExtraction, contradicted: list[str]
) -> list[MissingOrUnresolvedQuestion]:
    questions: list[MissingOrUnresolvedQuestion] = []
    for symptom in contradicted:
        questions.append(
            MissingOrUnresolvedQuestion(
                question=(
                    f"The intake both reports and denies '{symptom}'. "
                    "Which is correct?"
                ),
                reason="contradicted field: symptom appears as reported and denied",
                related_source_fields=["associated_symptoms", "denied_symptoms"],
                severity=MissingQuestionSeverity.helpful_for_review,
            )
        )
    if extraction.duration_days is None:
        questions.append(
            MissingOrUnresolvedQuestion(
                question="How long has the chief concern been present?",
                reason="duration_days was not stated",
                related_source_fields=["duration_days"],
                severity=MissingQuestionSeverity.helpful_for_review,
            )
        )
    if extraction.severity is Severity.UNKNOWN:
        questions.append(
            MissingOrUnresolvedQuestion(
                question="How severe does the patient consider the chief concern?",
                reason="severity was not stated or did not map to mild/moderate/severe",
                related_source_fields=["severity"],
                severity=MissingQuestionSeverity.helpful_for_review,
            )
        )
    if not extraction.current_medications:
        questions.append(
            MissingOrUnresolvedQuestion(
                question=(
                    "Is the patient taking any medications? (none were stated; "
                    "the intake cannot distinguish 'none' from 'not asked')"
                ),
                reason="current_medications is empty",
                related_source_fields=["current_medications"],
                severity=MissingQuestionSeverity.helpful_for_review,
            )
        )
    if not extraction.allergies:
        questions.append(
            MissingOrUnresolvedQuestion(
                question=(
                    "Does the patient have any allergies? (none were stated; "
                    "the intake cannot distinguish 'none' from 'not asked')"
                ),
                reason="allergies is empty",
                related_source_fields=["allergies"],
                severity=MissingQuestionSeverity.helpful_for_review,
            )
        )
    return questions


def build_missing_or_unresolved_section(
    questions: list[MissingOrUnresolvedQuestion],
) -> SummarySection:
    atoms = [
        SummaryAtom(
            text=question.question,
            source_fields=question.related_source_fields or ["chief_complaint"],
        )
        for question in questions
    ]
    return SummarySection(
        section_id=SummarySectionId.missing_or_unresolved,
        title="Missing or unresolved",
        atoms=atoms,
        omitted_reason=None if atoms else "no missing or unresolved items identified",
    )


# --- Engine -----------------------------------------------------------------


class ClinicalSummaryEngine:
    """Deterministic builder: PatientIntakeExtraction -> ClinicalSummaryResponse."""

    def __init__(self, clock: Clock | None = None):
        self.clock = clock or SystemClock()

    def build(
        self,
        extraction: PatientIntakeExtraction,
        intake_id: str | None = None,
    ) -> ClinicalSummaryResponse:
        intake_id = intake_id or derive_intake_id(extraction)
        issues = validate_summary_inputs(extraction)
        if any(issue.severity == "error" for issue in issues):
            return blocked_response(
                extraction,
                issues,
                intake_id=intake_id,
                generated_at=self.clock.utcnow(),
            )

        contradicted = find_contradicted_symptoms(extraction)
        missing_questions = build_missing_questions(extraction, contradicted)
        draft = ClinicalSummaryDraft(
            intake_id=intake_id,
            generated_at=self.clock.utcnow(),
            status=ClinicalSummaryStatus.draft,
            source_schema_version=SCHEMA_VERSION,
            sections=[
                build_patient_context(extraction),
                build_chief_concern(extraction),
                build_symptom_summary(extraction, contradicted),
                build_history_context(extraction),
                build_medications_allergies(extraction),
                build_social_context(extraction),
                build_care_goals_or_preferences(extraction),
                build_missing_or_unresolved_section(missing_questions),
            ],
            missing_or_unresolved_questions=missing_questions,
            validation_issues=issues,
        )

        output_issues = validate_summary_output(draft, extraction)
        if any(issue.severity == "error" for issue in output_issues):
            blocked = draft.model_copy(
                update={
                    "status": ClinicalSummaryStatus.blocked,
                    "validation_issues": [*draft.validation_issues, *output_issues],
                }
            )
            return ClinicalSummaryResponse(
                ok=False, summary=blocked, errors=output_issues
            )

        return ClinicalSummaryResponse(ok=True, summary=draft)
