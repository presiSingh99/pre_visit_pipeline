# Pre-Visit Patient Intake — Sprint 1: Clinical Extraction Service

Takes an unstructured patient–AI intake conversation transcript and returns strictly validated intermediate clinical JSON (Pydantic v2). Extraction only: the service never diagnoses, never prescribes, never gives medical advice, and never invents facts the patient did not state. Missing information stays null, empty, or `unknown`.

## Architecture (Sprint 1 slice)

```
transcript ──> POST /extract-intake ──> extraction_service.extract_intake()
                                            │
                                            ├─ llm/client.py    OpenAI Structured Outputs
                                            ├─ llm/prompts.py   guardrailed extraction prompt
                                            └─ schemas/intake.py  Pydantic v2 validation
                                                        │
                                                        └─> IntakeExtractionResult (JSON)
```

- `app/services/extraction_service.py` is a **pure step**: `transcript -> IntakeExtractionResult`, no HTTP or storage coupling. It is registered in `app/pipeline/steps.py`, the seam where graph-based workflow orchestration plugs in during later sprints (cleaning → extraction → summary → FHIR mapping as nodes).
- LLM output is treated as untrusted input: it is grammar-constrained by OpenAI Structured Outputs, then re-validated server-side with cross-field invariants (e.g. `red_flags_detected` must agree with `red_flag_symptoms`). Inconsistent output fails closed and is retried once.
- `metadata` (schema version, model, timestamp) is generated server-side, never by the LLM, in preparation for Sprint 3 audit logging and Sprint 4 FHIR mapping.

## Run it (backend + demo UI)

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OpenAI API key

# Terminal 1 — backend (FastAPI + auto Swagger UI at /docs)
uvicorn app.main:app --reload

# Terminal 2 — Sprint 1 demo UI (thin client, no extraction logic)
streamlit run demo/streamlit_demo.py
```

- API: http://127.0.0.1:8000 — interactive Swagger UI at http://127.0.0.1:8000/docs
- Demo UI: http://localhost:8501 — transcript in, validated JSON out. Point it at a remote backend with `INTAKE_API_URL=https://host streamlit run demo/streamlit_demo.py`.

The demo is deliberately a pure API client (`demo/streamlit_demo.py`): it holds zero extraction/validation logic and is **not** the doctor dashboard (Sprint 6). Deleting the `demo/` folder changes nothing about the backend.

## Try it

```bash
python test_request.py
# or
curl -s http://127.0.0.1:8000/extract-intake \
  -H 'Content-Type: application/json' \
  -d "{\"transcript\": $(python -c 'import json,pathlib;print(json.dumps(pathlib.Path("data/sample_transcripts/sore_throat.txt").read_text()))')}"
```

Expected shape for the sample sore-throat transcript:

```json
{
  "extraction": {
    "chief_complaint": "sore throat",
    "duration_days": 3,
    "severity": "unknown",
    "associated_symptoms": ["pain when swallowing", "mild fever"],
    "denied_symptoms": ["chest pain", "trouble breathing"],
    "current_medications": ["ibuprofen"],
    "allergies": ["penicillin"],
    "red_flags_detected": false,
    "red_flag_symptoms": []
  },
  "metadata": {
    "schema_version": "1.0.0",
    "model": "gpt-4o",
    "extracted_at": "..."
  }
}
```

## Tests

All tests run offline (LLM mocked, no API key required):

```bash
pytest -q
```

## Regenerate the Graphify graph

`graphify-out/` is committed on purpose — assistants read the graph instead of re-reading the repo. After code changes:

```bash
pip install graphifyy          # once
graphify update .              # code-only rebuild, tree-sitter, no LLM, no API key
```

Inside an AI coding assistant (Claude Code, Cursor, Codex…), run `/graphify --update` instead — that also refreshes doc/semantic nodes and community names via your assistant's model. Optional: `graphify hook install` rebuilds the graph on every commit and sets up a union-merge driver for `graph.json`.

Quick queries: `graphify explain "extract_intake"` · `graphify path "post_extract_intake" "PatientIntakeExtraction"`

## Git / GitHub

```bash
git init -b main
git add .
git commit -m "Sprint 1: clinical intake extraction service (FastAPI + Pydantic v2 + Streamlit demo)"
git remote add origin git@github.com:<you>/pre-visit-intake.git
git push -u origin main
```

`.gitignore` excludes `.env` (never commit keys) and caches; `graphify-out/` is tracked so teammates and assistants pull the graph.

## Success criteria (from sprint doc)

- Given a raw transcript, the system returns validated structured JSON ✅
- Missing details remain null/empty/unknown ✅ (enforced by prompt + schema defaults + tests)
- No diagnosis or treatment is generated ✅ (prompt guardrails; `extra="forbid"` rejects any extra fields such as a diagnosis)

## What connects to Sprint 2

Sprint 2 (Clinical Summary) consumes `IntakeExtractionResult` and renders a physician-ready report. Recommended first change there: add per-field source quotes (the transcript sentence each fact came from) to satisfy the "separate patient-stated facts from AI interpretation" requirement.
