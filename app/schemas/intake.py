"""Intermediate clinical intake schemas (Sprint 1).

`PatientIntakeExtraction` is the LLM-facing schema: every field is required
but nullable/empty-able, which satisfies OpenAI Structured Outputs strict
mode (all keys present, missing information expressed as null / []) and our
own clinical rule that missing data must never be invented.

`IntakeExtractionResult` wraps the extraction with server-side metadata for
auditability (Sprint 3) and forward-compatibility with FHIR mapping
(Sprint 4). The LLM never produces the metadata.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0.0"


class Severity(str, Enum):
    """Patient-stated severity. `unknown` when the patient did not state it."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    UNKNOWN = "unknown"


class PatientIntakeExtraction(BaseModel):
    """Structured clinical facts explicitly stated by the patient.

    Extraction-only contract:
    - No diagnosis, no prescribing, no medical advice.
    - Only facts the patient explicitly stated in the transcript.
    - Anything not stated stays null / empty / unknown.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    chief_complaint: str | None = Field(
        default=None,
        description=(
            "The patient's primary complaint in their own words, lightly "
            "normalized (e.g. 'sore throat'). Null if not stated."
        ),
    )
    duration_days: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Number of days the chief complaint has lasted, only if the "
            "patient stated a duration convertible to days. Null otherwise."
        ),
    )
    severity: Severity = Field(
        default=Severity.UNKNOWN,
        description=(
            "Severity only if the patient's own words map clearly to "
            "mild/moderate/severe; otherwise 'unknown'."
        ),
    )
    associated_symptoms: list[str] = Field(
        default_factory=list,
        description=(
            "Other symptoms the patient explicitly reported having. "
            "Do NOT include symptoms the patient explicitly denied."
        ),
    )
    denied_symptoms: list[str] = Field(
        default_factory=list,
        description=(
            "Symptoms the patient explicitly denied (e.g. 'no chest pain'). "
            "Pertinent negatives matter clinically and for red-flag review."
        ),
    )
    current_medications: list[str] = Field(
        default_factory=list,
        description="Medications the patient stated they are currently taking.",
    )
    allergies: list[str] = Field(
        default_factory=list,
        description="Allergies the patient explicitly reported.",
    )
    red_flags_detected: bool = Field(
        default=False,
        description=(
            "True only if the patient explicitly reported a red-flag symptom "
            "(e.g. chest pain, severe shortness of breath, stroke-like "
            "symptoms, uncontrolled bleeding, suicidal ideation)."
        ),
    )
    red_flag_symptoms: list[str] = Field(
        default_factory=list,
        description=(
            "The specific patient-stated symptoms that triggered "
            "red_flags_detected. Empty when red_flags_detected is false."
        ),
    )


class ExtractionMetadata(BaseModel):
    """Server-generated audit metadata. Never produced by the LLM."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION
    model: str
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class IntakeExtractionResult(BaseModel):
    """API response envelope: validated extraction + audit metadata."""

    model_config = ConfigDict(extra="forbid")

    extraction: PatientIntakeExtraction
    metadata: ExtractionMetadata


class ExtractIntakeRequest(BaseModel):
    """Request body for POST /extract-intake."""

    model_config = ConfigDict(extra="forbid")

    transcript: str = Field(
        min_length=1,
        max_length=50_000,
        description="Raw patient–AI intake conversation transcript.",
    )
