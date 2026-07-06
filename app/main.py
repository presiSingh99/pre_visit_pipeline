"""Application entrypoint.

Run locally:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.api.routes_intake import router as intake_router
from app.schemas.intake import SCHEMA_VERSION


def create_app() -> FastAPI:
    app = FastAPI(
        title="Pre-Visit Patient Intake — Clinical Extraction Service",
        version=SCHEMA_VERSION,
        description=(
            "Sprint 1: extracts strictly validated intermediate clinical "
            "JSON from unstructured patient\u2013AI intake transcripts. "
            "Extraction only — never diagnoses, prescribes, or advises."
        ),
    )
    app.include_router(intake_router)

    @app.get("/health", tags=["ops"])
    def health() -> dict[str, str]:
        return {"status": "ok", "schema_version": SCHEMA_VERSION}

    return app


app = create_app()
