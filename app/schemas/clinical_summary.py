"""Sprint 2 output contracts: clinical summary schemas.

Implements the schemas from
docs_handoff/sprints/sprint_02_clinical_summary.md verbatim where possible.
Every model uses ``extra="forbid"`` so callers and tests detect schema drift.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_path: str = Field(
        ..., description="JSON pointer or dotted path into PatientIntakeExtraction"
    )
    quote: str | None = Field(
        default=None, description="Verbatim source quote when available"
    )
    transcript_span: tuple[int, int] | None = Field(
        default=None, description="Character offsets when available"
    )
    speaker: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def span_is_valid_range(self):
        if self.transcript_span is not None:
            start, end = self.transcript_span
            if start < 0 or end < start:
                raise ValueError("transcript_span must be a valid non-negative range")
        return self


class SummarySafetyPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    no_diagnosis: Literal[True] = True
    no_treatment_recommendations: Literal[True] = True
    extracted_fields_only: Literal[True] = True
    fail_closed: Literal[True] = True


class SummarySectionId(str, Enum):
    patient_context = "patient_context"
    chief_concern = "chief_concern"
    symptom_summary = "symptom_summary"
    history_context = "history_context"
    medications_allergies = "medications_allergies"
    social_context = "social_context"
    care_goals_or_preferences = "care_goals_or_preferences"
    missing_or_unresolved = "missing_or_unresolved"
    evidence = "evidence"


class SummaryAtom(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1)
    source_fields: list[str] = Field(..., min_length=1)
    evidence: list[EvidenceRef] = Field(default_factory=list)


class SummarySection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: SummarySectionId
    title: str
    atoms: list[SummaryAtom] = Field(default_factory=list)
    omitted_reason: str | None = Field(
        default=None, description="Why section is empty, e.g. source field absent"
    )

    @model_validator(mode="after")
    def section_has_atoms_or_omission(self):
        if not self.atoms and not self.omitted_reason:
            raise ValueError("SummarySection must contain atoms or an omitted_reason")
        return self


class MissingQuestionSeverity(str, Enum):
    required_for_summary = "required_for_summary"
    helpful_for_review = "helpful_for_review"


class MissingOrUnresolvedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    related_source_fields: list[str] = Field(default_factory=list)
    severity: MissingQuestionSeverity


class ClinicalSummaryStatus(str, Enum):
    draft = "draft"
    blocked = "blocked"


class SummaryValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    field_path: str | None = None
    severity: Literal["error", "warning"]


class ClinicalSummaryDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intake_id: str
    generated_at: datetime
    status: ClinicalSummaryStatus
    safety_policy: SummarySafetyPolicy = Field(default_factory=SummarySafetyPolicy)
    sections: list[SummarySection]
    missing_or_unresolved_questions: list[MissingOrUnresolvedQuestion] = Field(
        default_factory=list
    )
    validation_issues: list[SummaryValidationIssue] = Field(default_factory=list)
    source_schema_name: Literal["PatientIntakeExtraction"] = "PatientIntakeExtraction"
    source_schema_version: str

    @model_validator(mode="after")
    def blocked_requires_error(self):
        has_error = any(issue.severity == "error" for issue in self.validation_issues)
        if self.status == ClinicalSummaryStatus.blocked and not has_error:
            raise ValueError(
                "blocked summaries must include at least one error validation issue"
            )
        return self


class ClinicalSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    summary: ClinicalSummaryDraft | None = None
    errors: list[SummaryValidationIssue] = Field(default_factory=list)

    @model_validator(mode="after")
    def exactly_one_success_or_errors(self):
        if self.ok and self.summary is None:
            raise ValueError("ok responses must include summary")
        if not self.ok and not self.errors:
            raise ValueError("failed responses must include errors")
        if (
            not self.ok
            and self.summary is not None
            and self.summary.status != ClinicalSummaryStatus.blocked
        ):
            raise ValueError("failed responses may only include blocked summaries")
        return self


class ClinicalSummaryRenderRequest(BaseModel):
    """Display formatting options — kept separate from clinical content."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["markdown", "json"] = "markdown"
    include_evidence: bool = True
    include_missing_questions: bool = True


class ClinicalSummaryRequest(BaseModel):
    """Request body for POST /api/v1/clinical-summary.

    ``intake`` is intentionally a raw dict: the route parses it through
    ``PatientIntakeExtraction`` itself so that parse failures map to 400
    (per the design's HTTP semantics) rather than FastAPI's default 422.

    ``intake_id`` is optional; the engine derives a deterministic id from
    the extraction content when absent (Sprint 1 does not carry one).
    """

    model_config = ConfigDict(extra="forbid")

    intake: dict
    render: ClinicalSummaryRenderRequest = Field(
        default_factory=ClinicalSummaryRenderRequest
    )
    intake_id: str | None = None


class ClinicalSummaryAPIResponse(ClinicalSummaryResponse):
    """API edge envelope: design response + optional rendered markdown.

    Documented deviation: the design keeps rendering separate from clinical
    content but requests render options in the API body. To honor render
    options without mutating the designed ``ClinicalSummaryResponse``
    (e.g. suppressing evidence in the display must not strip it from the
    JSON summary), the API returns this superset with a display-only field.
    """

    rendered_markdown: str | None = None
