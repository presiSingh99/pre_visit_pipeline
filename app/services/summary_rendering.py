"""Markdown rendering of a ``ClinicalSummaryDraft``.

Display only: output is limited to section headings, labels, atom text,
evidence metadata, and missing-question text already present in the draft.
The renderer never introduces new clinical facts.
"""

from __future__ import annotations

from app.schemas.clinical_summary import (
    ClinicalSummaryDraft,
    ClinicalSummaryRenderRequest,
)

SAFETY_NOTICE = (
    "> Draft for clinician review only. This summary does not diagnose, "
    "recommend treatment, or add facts beyond the validated intake extraction."
)


def render_markdown(
    draft: ClinicalSummaryDraft,
    options: ClinicalSummaryRenderRequest | None = None,
) -> str:
    options = options or ClinicalSummaryRenderRequest()
    lines: list[str] = [
        f"# Doctor-review draft summary — {draft.intake_id}",
        "",
        f"Status: **{draft.status.value}**",
        "",
        SAFETY_NOTICE,
        "",
    ]
    for section in draft.sections:
        if not options.include_missing_questions and section.section_id.value == (
            "missing_or_unresolved"
        ):
            continue
        lines.append(f"## {section.title}")
        if section.atoms:
            for atom in section.atoms:
                lines.append(f"- {atom.text}")
                if options.include_evidence:
                    for ref in atom.evidence:
                        detail = f"  - evidence: `{ref.field_path}`"
                        if ref.quote:
                            detail += f' — "{ref.quote}"'
                        lines.append(detail)
        else:
            lines.append(f"_Omitted: {section.omitted_reason}_")
        lines.append("")
    if options.include_missing_questions and draft.missing_or_unresolved_questions:
        lines.append("## Open questions for the visit")
        for question in draft.missing_or_unresolved_questions:
            lines.append(f"- {question.question} ({question.reason})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
