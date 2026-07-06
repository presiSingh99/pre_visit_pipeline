"""Typed application errors.

The service layer raises these; the API layer maps them to HTTP responses.
Keeping the mapping at the edge keeps `extract_intake` reusable as a plain
pipeline step (and later as a graph node) with no HTTP coupling.
"""


class IntakeError(Exception):
    """Base class for intake pipeline errors."""


class ConfigurationError(IntakeError):
    """Missing or invalid configuration (e.g. no API key)."""


class LLMUnavailableError(IntakeError):
    """The upstream LLM API failed (network, auth, rate limit, 5xx)."""


class ExtractionValidationError(IntakeError):
    """The LLM output could not be validated against the intake schema."""
