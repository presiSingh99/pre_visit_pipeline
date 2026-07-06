"""Summary validation: input preflight, output invariants, language guardrails.

Fail-closed philosophy: any error-severity issue blocks the draft. Sprint 2
introduces no clinical judgment; these checks only enforce that the summary
is a faithful, source-grounded restatement of the Sprint 1 extraction.
"""

from __future__ import annotations

import re
from datetime import datetime

from app.schemas.clinical_summary import (
    ClinicalSummaryDraft,
    ClinicalSummaryResponse,
    ClinicalSummaryStatus,
    SummarySection,
    SummarySectionId,
    SummaryValidationIssue,
)
from app.schemas.intake import PatientIntakeExtraction, SCHEMA_VERSION
from app.services.summary_field_access import field_path_exists

# --- Prohibited generated-language guardrails (design section 4) ---------

DIAGNOSIS_PATTERNS = (
    "consistent with",
    "likely",
    "suggests",
    "diagnosis",
    "differential",
    "rule out",
    "probable",
)

TREATMENT_PATTERNS = (
    "should start",
    "recommend",
    "advise",
    "prescribe",
    "increase dose",
    "decrease dose",
    "refer to",
    "order labs",
    "imaging recommended",
)

_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def _compile(patterns: tuple[str, ...]) -> list[re.Pattern[str]]:
    return [re.compile(rf"\b{re.escape(p)}\b", re.IGNORECASE) for p in patterns]


_DIAGNOSIS_RES = _compile(DIAGNOSIS_PATTERNS)
_TREATMENT_RES = _compile(TREATMENT_PATTERNS)


def _source_text_corpus(extraction: PatientIntakeExtraction) -> str:
    """All patient-stated string values, lowercased, for verbatim allowances."""
    parts: list[str] = []
    for value in extraction.model_dump().values():
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
    return " \n ".join(parts).lower()


def _allowed_numbers(extraction: PatientIntakeExtraction) -> set[str]:
    """Numeric tokens permitted in atom text: numbers present in the source."""
    allowed: set[str] = set()
    for value in extraction.model_dump().values():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            allowed.add(str(value))
        texts = value if isinstance(value, list) else [value]
        for text in texts:
            if isinstance(text, str):
                allowed.update(_NUMBER.findall(text))
    return allowed


# --- Input preflight (design: input invariants) ---------------------------


def validate_summary_inputs(
    extraction: PatientIntakeExtraction,
) -> list[SummaryValidationIssue]:
    issues: list[SummaryValidationIssue] = []

    if not extraction.chief_complaint:
        issues.append(
            SummaryValidationIssue(
                code="MISSING_REQUIRED_FIELD",
                message=(
                    "chief_complaint is required to generate a doctor-review "
                    "draft summary"
                ),
                field_path="chief_complaint",
                severity="error",
            )
        )

    # Red-flag internal consistency (mirrors Sprint 1's fail-closed invariant;
    # re-checked here because the API accepts extraction JSON from callers).
    if extraction.red_flags_detected and not extraction.red_flag_symptoms:
        issues.append(
            SummaryValidationIssue(
                code="INCONSISTENT_RED_FLAGS",
                message="red_flags_detected is true but red_flag_symptoms is empty",
                field_path="red_flag_symptoms",
                severity="error",
            )
        )
    if extraction.red_flag_symptoms and not extraction.red_flags_detected:
        issues.append(
            SummaryValidationIssue(
                code="INCONSISTENT_RED_FLAGS",
                message="red_flag_symptoms is non-empty but red_flags_detected is false",
                field_path="red_flags_detected",
                severity="error",
            )
        )
    return issues


def find_contradicted_symptoms(extraction: PatientIntakeExtraction) -> list[str]:
    """Symptoms both reported and denied — Sprint 2 must not choose a side."""
    reported = {s.strip().lower() for s in extraction.associated_symptoms}
    denied = {s.strip().lower() for s in extraction.denied_symptoms}
    return sorted(reported & denied)


# --- Output invariants (design: output invariants) -------------------------


def validate_summary_output(
    draft: ClinicalSummaryDraft, extraction: PatientIntakeExtraction
) -> list[SummaryValidationIssue]:
    issues: list[SummaryValidationIssue] = []
    corpus = _source_text_corpus(extraction)
    allowed_numbers = _allowed_numbers(extraction)

    for section in draft.sections:
        if not section.atoms and not section.omitted_reason:
            issues.append(
                SummaryValidationIssue(
                    code="EMPTY_SECTION_WITHOUT_REASON",
                    message=f"section {section.section_id} is empty without omitted_reason",
                    field_path=None,
                    severity="error",
                )
            )
        for atom in section.atoms:
            for path in atom.source_fields:
                if not field_path_exists(extraction, path):
                    issues.append(
                        SummaryValidationIssue(
                            code="UNKNOWN_SOURCE_FIELD",
                            message=(
                                f"atom references source field {path!r} that does "
                                "not exist in the extraction"
                            ),
                            field_path=path,
                            severity="error",
                        )
                    )
            text_lower = atom.text.lower()
            for regex, code in (
                *((r, "DIAGNOSIS_LANGUAGE") for r in _DIAGNOSIS_RES),
                *((r, "TREATMENT_LANGUAGE") for r in _TREATMENT_RES),
            ):
                match = regex.search(text_lower)
                # Allowed only if the phrase appears verbatim in source values
                # (i.e. patient-stated), never as a Sprint 2 conclusion.
                if match and match.group(0).lower() not in corpus:
                    issues.append(
                        SummaryValidationIssue(
                            code=code,
                            message=(
                                f"prohibited phrase {match.group(0)!r} in atom text "
                                "not present in source extraction"
                            ),
                            field_path=None,
                            severity="error",
                        )
                    )
            for number in _NUMBER.findall(atom.text):
                if number not in allowed_numbers:
                    issues.append(
                        SummaryValidationIssue(
                            code="UNSUPPORTED_VALUE",
                            message=(
                                f"numeric value {number!r} in atom text is not "
                                "present in the source extraction"
                            ),
                            field_path=None,
                            severity="error",
                        )
                    )
    return issues


# --- Blocked response helper (shared by service and API tests) --------------


def blocked_response(
    extraction: PatientIntakeExtraction,
    issues: list[SummaryValidationIssue],
    *,
    intake_id: str,
    generated_at: datetime,
    sections: list[SummarySection] | None = None,
) -> ClinicalSummaryResponse:
    errors = [i for i in issues if i.severity == "error"]
    if sections is None:
        sections = [
            SummarySection(
                section_id=SummarySectionId.chief_concern,
                title="Chief concern",
                atoms=[],
                omitted_reason="summary generation was blocked by validation errors",
            )
        ]
    draft = ClinicalSummaryDraft(
        intake_id=intake_id,
        generated_at=generated_at,
        status=ClinicalSummaryStatus.blocked,
        sections=sections,
        validation_issues=issues,
        source_schema_version=SCHEMA_VERSION,
    )
    return ClinicalSummaryResponse(ok=False, summary=draft, errors=errors)
