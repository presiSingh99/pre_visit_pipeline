"""Pipeline step registry — the seam for future graph orchestration.

Sprint 1 has exactly one step, so introducing a graph engine now would be
premature. Instead, every pipeline-capable operation is registered here as
a named, typed, pure callable. When later sprints add cleaning, summary
generation (Sprint 2), audit logging (Sprint 3), and FHIR mapping
(Sprint 4), an orchestrator can consume this registry as its node set
without refactoring the services.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.services.extraction_service import extract_intake


@dataclass(frozen=True)
class Step:
    """A named, pure pipeline step (a future graph node)."""

    name: str
    description: str
    func: Callable[..., Any]


STEPS: dict[str, Step] = {
    "extract_intake": Step(
        name="extract_intake",
        description=(
            "Raw patient\u2013AI transcript -> validated intermediate "
            "clinical JSON (IntakeExtractionResult)."
        ),
        func=extract_intake,
    ),
}


def get_step(name: str) -> Step:
    try:
        return STEPS[name]
    except KeyError as exc:
        raise KeyError(
            f"Unknown pipeline step '{name}'. Available: {sorted(STEPS)}"
        ) from exc
