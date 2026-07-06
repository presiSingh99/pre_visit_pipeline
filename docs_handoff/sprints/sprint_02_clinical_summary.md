# Sprint 2 — Clinical Summary Engine

## Goal

Convert a validated `PatientIntakeExtraction` object from Sprint 1 into a doctor-review draft summary.

The engine is deliberately conservative: it does not diagnose, recommend treatment, or infer facts that are not present in the validated extraction JSON. The summary is structured for review, auditability, and deterministic testing.

## Hard Constraints

- Do not diagnose.
- Do not recommend treatment.
- Do not infer facts not present in validated JSON.
- Only use extracted fields from `PatientIntakeExtraction`.
- Include missing and unresolved questions.
- Preserve source evidence references where available.
- Keep output structured and testable.
- Fail closed if required fields are missing or internally inconsistent.

## 1. New Pydantic Schemas

Add `app/schemas/clinical_summary.py` for all Sprint 2 output contracts. Every model must use `ConfigDict(extra="forbid")` so callers and tests can detect schema drift.

### Evidence and safety policy

```python
from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_path: str = Field(..., description="JSON pointer or dotted path into PatientIntakeExtraction")
    quote: str | None = Field(default=None, description="Verbatim source quote when available")
    transcript_span: tuple[int, int] | None = Field(default=None, description="Character offsets when available")
    speaker: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class SummarySafetyPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    no_diagnosis: Literal[True] = True
    no_treatment_recommendations: Literal[True] = True
    extracted_fields_only: Literal[True] = True
    fail_closed: Literal[True] = True
```

### Structured summary sections

```python
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
    omitted_reason: str | None = Field(default=None, description="Why section is empty, e.g. source field absent")

    @model_validator(mode="after")
    def section_has_atoms_or_omission(self):
        if not self.atoms and not self.omitted_reason:
            raise ValueError("SummarySection must contain atoms or an omitted_reason")
        return self
```

### Missing questions, validation issues, and result envelope

```python
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
    missing_or_unresolved_questions: list[MissingOrUnresolvedQuestion] = Field(default_factory=list)
    validation_issues: list[SummaryValidationIssue] = Field(default_factory=list)
    source_schema_name: Literal["PatientIntakeExtraction"] = "PatientIntakeExtraction"
    source_schema_version: str

    @model_validator(mode="after")
    def blocked_requires_error(self):
        has_error = any(issue.severity == "error" for issue in self.validation_issues)
        if self.status == ClinicalSummaryStatus.blocked and not has_error:
            raise ValueError("blocked summaries must include at least one error validation issue")
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
        if not self.ok and self.summary is not None and self.summary.status != ClinicalSummaryStatus.blocked:
            raise ValueError("failed responses may only include blocked summaries")
        return self
```

### Optional rendering request

Keep display formatting separate from clinical content generation.

```python
class ClinicalSummaryRenderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: Literal["markdown", "json"] = "markdown"
    include_evidence: bool = True
    include_missing_questions: bool = True
```

## 2. Service-Layer Design

### Modules

- `app/services/summary_field_access.py`: safe accessors for fields on `PatientIntakeExtraction`.
- `app/services/summary_validation.py`: input preflight checks and output invariant checks.
- `app/services/clinical_summary_engine.py`: deterministic transformation into `ClinicalSummaryResponse`.
- `app/services/summary_rendering.py`: optional markdown rendering from `ClinicalSummaryDraft`; no new clinical facts.

### Pipeline

1. **Preflight validation**
   - Require an already parsed `PatientIntakeExtraction` instance, or parse request JSON through the Sprint 1 schema before the service is called.
   - Confirm required metadata exists, including `intake_id` and `schema_version`.
   - Confirm the Sprint 1 extraction status indicates a validated/successful extraction if such a field exists.
   - Confirm required clinical anchor fields exist, at minimum chief concern or reason for visit depending on the Sprint 1 schema.

2. **Safe field access**
   - Use field access helpers that return `(value, field_path, evidence_refs)`.
   - Normalize nested source paths into stable dotted paths such as `symptoms[0].duration`.
   - Never read raw transcript text in Sprint 2.
   - Never call an LLM for uncontrolled summary generation. Sprint 2 should be deterministic first.

3. **Build summary atoms**
   - Convert extracted fields into short factual statements.
   - Every atom must include at least one source field.
   - Attach evidence references whenever Sprint 1 provides quote, transcript span, speaker, or confidence.
   - Do not choose a side for contradicted or unresolved fields.

4. **Build stable sections**
   - Group atoms into stable sections in a fixed order.
   - Empty sections must carry an explicit `omitted_reason`.
   - Missing and unresolved questions are first-class structured objects and should also appear in the missing/unresolved section.

5. **Post-build validation**
   - Enforce source field existence.
   - Enforce no unsupported clinical values.
   - Enforce prohibited diagnosis and treatment recommendation phrase guardrails.
   - Return `ok=False` with a blocked draft if validation fails.

### Deterministic builder interface

```python
class ClinicalSummaryEngine:
    def __init__(self, clock: Clock | None = None):
        self.clock = clock or SystemClock()

    def build(self, extraction: PatientIntakeExtraction) -> ClinicalSummaryResponse:
        issues = validate_summary_inputs(extraction)
        if any(issue.severity == "error" for issue in issues):
            return blocked_response(extraction, issues, generated_at=self.clock.utcnow())

        missing_questions = build_missing_questions(extraction)
        draft = ClinicalSummaryDraft(
            intake_id=extraction.intake_id,
            generated_at=self.clock.utcnow(),
            status=ClinicalSummaryStatus.draft,
            source_schema_version=extraction.schema_version,
            sections=[
                build_patient_context(extraction),
                build_chief_concern(extraction),
                build_symptom_summary(extraction),
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
            return ClinicalSummaryResponse(ok=False, summary=blocked, errors=output_issues)

        return ClinicalSummaryResponse(ok=True, summary=draft)
```

## 3. API Endpoint Design

### Endpoint

`POST /api/v1/clinical-summary`

### Request shape

```json
{
  "intake": { "...": "PatientIntakeExtraction JSON" },
  "render": {
    "format": "json",
    "include_evidence": true,
    "include_missing_questions": true
  }
}
```

### HTTP semantics

- `200 OK`: request parsed as `PatientIntakeExtraction` and summary generation succeeded.
- `400 Bad Request`: malformed JSON or body cannot parse as `PatientIntakeExtraction`.
- `422 Unprocessable Entity`: request parsed as an extraction, but the summary engine failed closed because required summary fields are missing or inconsistent.

### Success response example

```json
{
  "ok": true,
  "summary": {
    "intake_id": "intake_123",
    "generated_at": "2026-07-06T00:00:00Z",
    "status": "draft",
    "safety_policy": {
      "no_diagnosis": true,
      "no_treatment_recommendations": true,
      "extracted_fields_only": true,
      "fail_closed": true
    },
    "sections": [],
    "missing_or_unresolved_questions": [],
    "validation_issues": [],
    "source_schema_name": "PatientIntakeExtraction",
    "source_schema_version": "1.0.0"
  },
  "errors": []
}
```

### Blocked response example

```json
{
  "ok": false,
  "summary": {
    "intake_id": "intake_123",
    "generated_at": "2026-07-06T00:00:00Z",
    "status": "blocked",
    "sections": [
      {
        "section_id": "chief_concern",
        "title": "Chief concern",
        "atoms": [],
        "omitted_reason": "chief_concern is missing"
      }
    ],
    "missing_or_unresolved_questions": [],
    "validation_issues": [
      {
        "code": "MISSING_REQUIRED_FIELD",
        "message": "chief_concern is required to generate a doctor-review draft summary",
        "field_path": "chief_concern",
        "severity": "error"
      }
    ],
    "source_schema_name": "PatientIntakeExtraction",
    "source_schema_version": "1.0.0"
  },
  "errors": [
    {
      "code": "MISSING_REQUIRED_FIELD",
      "message": "chief_concern is required to generate a doctor-review draft summary",
      "field_path": "chief_concern",
      "severity": "error"
    }
  ]
}
```

### Idempotency and traceability

- Responses should be deterministic for identical inputs except `generated_at`.
- Unit and API tests should inject a frozen clock.
- If the app already uses request IDs, include request IDs in logs but not in clinical atoms.
- Do not include raw transcript text in summary responses unless it already appears as a Sprint 1 evidence quote.

## 4. Validation Invariants

### Input invariants

- Input must parse as `PatientIntakeExtraction`.
- `intake_id` and `schema_version` must be present.
- Required clinical anchor field must be present, such as `chief_concern` or the Sprint 1 equivalent.
- Sprint 1 status must indicate successful validated extraction if the schema exposes a status field.
- Contradicted or unresolved Sprint 1 fields must become missing/unresolved questions; Sprint 2 must not choose one side.
- Evidence references must point to valid extraction field paths.
- Evidence transcript spans, if present, must be valid non-negative ranges.

### Output invariants

- Every `SummaryAtom` has non-empty `source_fields`.
- Every `SummaryAtom.source_fields` path exists in the source extraction.
- Empty sections have an `omitted_reason`.
- Successful responses have `ok=True`, `status=draft`, and no error issues.
- Blocked responses have `ok=False`, `status=blocked`, and at least one error issue.
- Summary text contains no diagnosis or treatment recommendation language introduced by Sprint 2.
- Summary text contains no unsupported medications, allergies, symptoms, durations, numbers, or dates.
- Rendering never adds clinical facts beyond section labels and atom text already present in the summary.

### Prohibited generated-language guardrails

Diagnosis pattern examples:

- `consistent with`
- `likely`
- `suggests`
- `diagnosis`
- `differential`
- `rule out`
- `probable`

Treatment recommendation pattern examples:

- `should start`
- `recommend`
- `advise`
- `prescribe`
- `increase dose`
- `decrease dose`
- `refer to`
- `order labs`
- `imaging recommended`

These checks are guardrails. Allow such wording only if it appears verbatim in an extracted source field and the atom clearly attributes it as patient-reported or prior-clinician-reported rather than a Sprint 2 conclusion.

## 5. Test Cases

### Schema tests

1. `SummarySection` rejects empty `atoms` when `omitted_reason` is absent.
2. `ClinicalSummaryDraft` rejects `blocked` status without an error issue.
3. `ClinicalSummaryResponse` rejects `ok=True` without `summary`.
4. `ClinicalSummaryResponse` rejects `ok=False` without `errors`.
5. `ClinicalSummaryResponse` rejects failed responses that include a non-blocked summary.
6. `EvidenceRef` rejects `confidence` outside `[0.0, 1.0]`.
7. All Sprint 2 summary models reject unknown extra keys.

### Engine behavior tests

1. Minimal valid extraction produces `ok=True` and `status=draft`.
2. Chief concern maps into the chief concern section with source fields and evidence references.
3. Symptom fields produce factual atoms without diagnosis or recommendations.
4. Missing optional fields create section omissions or helpful missing questions, not fabricated facts.
5. Contradicted fields create unresolved questions and no selected fact.
6. Missing required anchor field returns a blocked service result.
7. Evidence spans from Sprint 1 are preserved exactly.
8. Frozen clock makes response snapshots stable.
9. Same extraction produces identical summaries apart from timestamp when clock is not frozen.
10. Engine does not read raw transcript fields during summary generation.

### Safety tests

1. Output validation rejects generated atoms with diagnosis phrases absent from source extraction.
2. Output validation rejects generated atoms with treatment recommendation phrases absent from source extraction.
3. Output validation rejects atoms referencing source field paths absent from the extraction.
4. Output validation rejects unsupported medication, allergy, duration, date, or numeric values.
5. Renderer output contains only section headings, labels, atom text, evidence metadata, and missing question text from `ClinicalSummaryDraft`.

### API tests

1. `POST /api/v1/clinical-summary` returns `200` for valid extraction.
2. Endpoint returns `400` for malformed JSON.
3. Endpoint returns `400` for JSON that cannot parse as `PatientIntakeExtraction`.
4. Endpoint returns `422` for parseable extraction missing required summary fields.
5. Response validates against `ClinicalSummaryResponse`.
6. Evidence references are included by default.
7. Render options can suppress evidence in markdown display without removing evidence from JSON summary.

## 6. File-by-File Implementation Plan

1. `app/schemas/clinical_summary.py`
   - Add all summary, evidence, missing-question, issue, render, draft, and response schemas.
   - Use `extra="forbid"` everywhere.

2. `app/services/summary_field_access.py`
   - Add safe accessors for Sprint 1 extraction fields.
   - Return normalized field path, value, and evidence references.
   - Centralize nested field traversal and missing field behavior.

3. `app/services/summary_validation.py`
   - Add input preflight validation.
   - Add output validation and source-field allowlist checks.
   - Add prohibited generated-language checks.
   - Add blocked-response helper if shared by service and API tests.

4. `app/services/clinical_summary_engine.py`
   - Add deterministic section builders.
   - Add `ClinicalSummaryEngine.build()`.
   - Accept an injectable clock for deterministic tests.
   - Return `ClinicalSummaryResponse`, never a raw dict.

5. `app/services/summary_rendering.py`
   - Add markdown rendering for demo and clinician readability.
   - Keep renderer content limited to labels, headings, atoms, evidence metadata, and missing questions from the draft.

6. `app/api/routes/clinical_summary.py`
   - Add `POST /api/v1/clinical-summary`.
   - Parse request body through `PatientIntakeExtraction`.
   - Map parse errors to `400` and blocked summaries to `422`.

7. `app/main.py` or existing router registration module
   - Register the clinical summary route.

8. `tests/schemas/test_clinical_summary_schema.py`
   - Add schema invariant tests.

9. `tests/services/test_clinical_summary_engine.py`
   - Add deterministic build tests, missing-field tests, contradiction tests, evidence preservation tests, and frozen-clock tests.

10. `tests/services/test_summary_safety.py`
    - Add prohibited phrase, source-grounding, unsupported-value, and raw-transcript access tests.

11. `tests/api/test_clinical_summary_api.py`
    - Add success, malformed request, blocked response, response schema, and render option tests.

12. `tests/fixtures/patient_intake_extractions.py`
    - Add minimal valid, rich valid, missing required, and contradicted extraction fixtures.

## 7. Streamlit Demo Work for Claude Afterward

Claude should implement the demo only after backend schemas, services, endpoint, and tests are merged.

### Demo UX additions

- Add a new **Clinical Summary** step after Sprint 1 extraction.
- Display the validated `PatientIntakeExtraction` JSON first.
- Add a **Generate doctor-review draft** button.
- Show summary status prominently: `Draft generated` or `Blocked`.
- Render structured sections in stable order.
- Add an expandable **Evidence** panel for each summary atom.
- Add a persistent **Missing / unresolved questions** panel.
- If blocked, show validation errors and do not show a clinician-style draft summary.

### Demo safety copy

Display this notice near the summary action and output:

> Draft for clinician review only. This summary does not diagnose, recommend treatment, or add facts beyond the validated intake extraction.

### Demo implementation notes

- Call the backend summary endpoint rather than duplicating summary logic in Streamlit.
- Do not pass raw transcript directly to the summary step.
- Do not use an LLM in the Streamlit layer for rewriting or polishing the summary.
- Preserve and display evidence references from the JSON response.
- Add sample fixtures for successful draft, blocked missing required field, and unresolved contradiction.

### Demo acceptance criteria

- The demo can generate a summary from a valid extraction fixture.
- The demo shows blocked state for invalid or incomplete extraction fixture.
- Evidence references are visible without expanding raw transcript by default.
- Missing/unresolved questions are visible in both successful and blocked flows.
- No diagnosis or treatment recommendation text is introduced by the UI.
