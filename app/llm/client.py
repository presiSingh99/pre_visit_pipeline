"""Thin OpenAI client wrapper for structured extraction.

Isolates the vendor SDK behind one function so the service layer stays
vendor-neutral (swapping to Anthropic tool use later touches only this
module).
"""

from __future__ import annotations

from openai import APIError, OpenAI, OpenAIError

from app.core.config import get_settings
from app.core.errors import ConfigurationError, LLMUnavailableError
from app.llm.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_user_prompt
from app.schemas.intake import PatientIntakeExtraction

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    settings = get_settings()
    if not settings.openai_api_key:
        raise ConfigurationError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    if _client is None:
        _client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.llm_timeout_seconds,
        )
    return _client


def call_extraction_model(transcript: str) -> PatientIntakeExtraction:
    """One LLM call: transcript -> schema-constrained extraction.

    Uses OpenAI Structured Outputs (`chat.completions.parse`) so the model
    is grammar-constrained to the schema. The returned object has already
    passed Pydantic validation inside the SDK; the service layer re-validates
    defensively anyway.

    Raises:
        ConfigurationError: no API key configured.
        LLMUnavailableError: upstream API failure.
    """
    settings = get_settings()
    client = _get_client()
    try:
        completion = client.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": build_extraction_user_prompt(transcript)},
            ],
            response_format=PatientIntakeExtraction,
            temperature=0,
        )
    except (APIError, OpenAIError) as exc:
        raise LLMUnavailableError(f"LLM request failed: {exc}") from exc

    message = completion.choices[0].message
    if message.refusal:
        raise LLMUnavailableError(f"Model refused extraction: {message.refusal}")
    if message.parsed is None:
        raise LLMUnavailableError("Model returned no parsed output.")
    return message.parsed
