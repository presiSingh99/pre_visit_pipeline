"""Safe accessors for fields on ``PatientIntakeExtraction``.

Centralizes field traversal, stable dotted-path normalization (e.g.
``associated_symptoms[0]``), and missing-field behavior. Sprint 2 must
never read raw transcript text; these helpers only expose validated
extraction fields.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.schemas.clinical_summary import EvidenceRef
from app.schemas.intake import PatientIntakeExtraction

_PATH_ITEM = re.compile(r"^(?P<name>[a-z_]+)(?:\[(?P<index>\d+)\])?$")


@dataclass(frozen=True)
class FieldAccess:
    """A resolved extraction field: value + stable path + evidence."""

    value: Any
    field_path: str
    evidence: list[EvidenceRef] = field(default_factory=list)

    @property
    def present(self) -> bool:
        if self.value is None:
            return False
        if isinstance(self.value, (list, str)) and len(self.value) == 0:
            return False
        return True


def get_field(extraction: PatientIntakeExtraction, path: str) -> FieldAccess:
    """Resolve a dotted/indexed path like ``allergies[1]`` on the extraction.

    Sprint 1 does not emit evidence quotes or transcript spans yet, so
    ``evidence`` is empty; the plumbing exists so Sprint 1 evidence can be
    attached here later without touching the engine.

    Raises:
        KeyError: the path does not exist on the extraction schema.
        IndexError: an index is out of range for a list field.
    """
    match = _PATH_ITEM.match(path)
    if not match:
        raise KeyError(f"Invalid field path: {path!r}")
    name, index = match.group("name"), match.group("index")
    if name not in type(extraction).model_fields:
        raise KeyError(f"Unknown extraction field: {name!r}")
    value = getattr(extraction, name)
    if index is not None:
        if not isinstance(value, list):
            raise KeyError(f"Field {name!r} is not indexable")
        value = value[int(index)]  # IndexError propagates by design
    return FieldAccess(value=value, field_path=path)


def field_path_exists(extraction: PatientIntakeExtraction, path: str) -> bool:
    """True if ``path`` resolves against this extraction instance."""
    try:
        get_field(extraction, path)
    except (KeyError, IndexError):
        return False
    return True


def list_item_paths(extraction: PatientIntakeExtraction, name: str) -> list[FieldAccess]:
    """Per-item accessors for a list field, e.g. ``allergies[0]``, ``allergies[1]``."""
    values = getattr(extraction, name)
    if not isinstance(values, list):
        raise KeyError(f"Field {name!r} is not a list field")
    return [
        FieldAccess(value=item, field_path=f"{name}[{i}]")
        for i, item in enumerate(values)
    ]
