"""POST /api/v1/clinical-summary — Sprint 2 endpoint.

HTTP semantics per design:
- 200: body parsed as PatientIntakeExtraction and summary generation succeeded
- 400: malformed JSON, or body/intake cannot parse as PatientIntakeExtraction
- 422: extraction parsed, but the engine failed closed (blocked summary)

The body is parsed manually (Request -> json -> Pydantic) because FastAPI's
default maps body validation errors to 422, while the design reserves 422
for blocked summaries and uses 400 for parse failures.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.schemas.clinical_summary import (
    ClinicalSummaryAPIResponse,
    ClinicalSummaryRequest,
)
from app.schemas.intake import PatientIntakeExtraction
from app.services.clinical_summary_engine import ClinicalSummaryEngine
from app.services.summary_rendering import render_markdown

router = APIRouter(prefix="/api/v1", tags=["clinical-summary"])

_engine = ClinicalSummaryEngine()


@router.post("/clinical-summary", response_model=ClinicalSummaryAPIResponse)
async def post_clinical_summary(request: Request) -> JSONResponse:
    try:
        body = json.loads(await request.body())
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"detail": "Malformed JSON"})

    try:
        payload = ClinicalSummaryRequest.model_validate(body)
        extraction = PatientIntakeExtraction.model_validate(payload.intake)
    except ValidationError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Body could not be parsed as a clinical summary request "
                "with a valid PatientIntakeExtraction",
                "errors": json.loads(exc.json()),
            },
        )

    result = _engine.build(extraction, intake_id=payload.intake_id)
    rendered = None
    if result.summary is not None and payload.render.format == "markdown":
        rendered = render_markdown(result.summary, payload.render)
    response = ClinicalSummaryAPIResponse(
        ok=result.ok,
        summary=result.summary,
        errors=result.errors,
        rendered_markdown=rendered,
    )
    status_code = 200 if result.ok else 422
    return JSONResponse(
        status_code=status_code,
        content=json.loads(response.model_dump_json()),
    )
