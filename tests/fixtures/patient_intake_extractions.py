"""Reusable PatientIntakeExtraction fixtures for Sprint 2 tests."""

from app.schemas.intake import PatientIntakeExtraction, Severity


def minimal_valid() -> PatientIntakeExtraction:
    return PatientIntakeExtraction(chief_complaint="sore throat")


def rich_valid() -> PatientIntakeExtraction:
    return PatientIntakeExtraction(
        chief_complaint="sore throat",
        duration_days=3,
        severity=Severity.MODERATE,
        associated_symptoms=["pain when swallowing", "mild fever"],
        denied_symptoms=["chest pain", "shortness of breath"],
        current_medications=["ibuprofen"],
        allergies=["penicillin"],
        red_flags_detected=False,
        red_flag_symptoms=[],
    )


def missing_required() -> PatientIntakeExtraction:
    """Parses fine as an extraction, but lacks the summary anchor field."""
    return PatientIntakeExtraction(
        chief_complaint=None,
        associated_symptoms=["mild fever"],
    )


def contradicted() -> PatientIntakeExtraction:
    """'headache' is both reported and denied — must not be resolved."""
    return PatientIntakeExtraction(
        chief_complaint="dizziness",
        associated_symptoms=["headache", "nausea"],
        denied_symptoms=["headache"],
    )


def red_flag_case() -> PatientIntakeExtraction:
    return PatientIntakeExtraction(
        chief_complaint="chest pain",
        associated_symptoms=["chest pain"],
        red_flags_detected=True,
        red_flag_symptoms=["chest pain"],
    )
