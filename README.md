# Pre-Visit Patient Intake — Clinical Extraction Service

Takes an unstructured patient–AI intake conversation transcript and returns strictly validated intermediate clinical JSON (Pydantic v2). Extraction only: the service never diagnoses, never prescribes, never gives medical advice, and never invents facts the patient did not state. Missing information stays null, empty, or `unknown`.

## Architecture

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
- `metadata` (schema version, model, timestamp) is generated server-side, never by the LLM, in preparation for audit logging and FHIR mapping.

## Prerequisites

- Docker Desktop or Docker Engine with Docker Compose v2.24+ (the compose file uses the optional `env_file` syntax).
- A copy of `.env` created from `.env.example` — needed only for real extraction calls. `docker compose up`, `/health`, and the test suite all work without it.
- An OpenAI API key for real extraction calls. Tests mock the LLM and do not require a key.

## Environment variables

Copy the example file and set local values:

```bash
cp .env.example .env
```

Required/recognized variables:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | Required for real `/extract-intake` calls | empty | API key used by the extraction model client. Never commit real secrets. |
| `OPENAI_MODEL` | No | `gpt-4o` | Model name used for clinical extraction. |
| `LLM_TIMEOUT_SECONDS` | No | `60` | Timeout for LLM requests. |
| `LLM_MAX_RETRIES` | No | `1` | Retry count for malformed/invalid LLM output. |
| `INTAKE_API_URL` | Streamlit only | `http://127.0.0.1:8000` | Backend URL used by the demo UI. Compose sets this to `http://backend:8000`. |

Secrets are loaded at runtime through `.env`; they are excluded from Docker build context by `.dockerignore` and must not be baked into images.

## Docker development workflow

Build and run the FastAPI backend plus the Streamlit demo:

```bash
docker compose up --build
```

- FastAPI: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Streamlit demo: http://localhost:8501

The project directory is mounted into both containers, so code changes hot reload during development. Streamlit waits for the backend's `/health` check to pass before starting. Host ports are bound to `127.0.0.1` so dev containers are not reachable from your LAN; change the mapping in `docker-compose.yml` if you need to expose them.

Stop and remove containers:

```bash
docker compose down
```

Run tests inside the same container image:

```bash
docker compose run --rm backend pytest -q
```

Run a one-off shell inside the backend container:

```bash
docker compose run --rm backend bash
```

## Local Python workflow (optional)

If you are not using Docker:

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OpenAI API key for real extraction calls
uvicorn app.main:app --reload
```

In another terminal:

```bash
streamlit run demo/streamlit_demo.py
```

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

Docker equivalent:

```bash
docker compose run --rm backend pytest -q
```

## Troubleshooting

- **`OPENAI_API_KEY` errors during manual extraction:** verify `.env` exists and contains a real key. Unit tests do not need this key.
- **Port already in use:** stop the conflicting process or change the host port mapping in `docker-compose.yml`.
- **Docker changes are not reflected:** confirm the service is running through Compose; the project directory is mounted at `/app` and Uvicorn uses `--reload`.
- **Dependency changes are not available:** rebuild the image with `docker compose up --build` after editing `requirements.txt`.
- **Streamlit cannot reach the API:** inside Compose it uses `http://backend:8000`; outside Compose set `INTAKE_API_URL` to the backend URL.
- **`env file .env not found`:** your Docker Compose is older than v2.24; either upgrade or create `.env` from `.env.example`.

## Deploying beyond dev (ECS/Fargate)

`docker-compose.yml` is development-only. The image itself is already Fargate-friendly: it runs as a non-root user, takes all configuration from environment variables, logs to stdout, and its default `CMD` runs Uvicorn without `--reload`. When writing the task definition: inject `OPENAI_API_KEY` from AWS Secrets Manager or SSM Parameter Store (never bake it into the image or task JSON), map container port 8000, and reuse the compose health check command (`python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"`) as the container health check, since the slim image ships no curl.

## Regenerate the Graphify graph

`graphify-out/` is committed on purpose — assistants read the graph instead of re-reading the repo. After code changes:

```bash
pip install graphifyy          # once
graphify update .              # code-only rebuild, tree-sitter, no LLM, no API key
```

Inside an AI coding assistant (Claude Code, Cursor, Codex…), run `/graphify --update` instead — that also refreshes doc/semantic nodes and community names via your assistant's model. Optional: `graphify hook install` rebuilds the graph on every commit and sets up a union-merge driver for `graph.json`.

Quick queries: `graphify explain "extract_intake"` · `graphify path "post_extract_intake" "PatientIntakeExtraction"`

## Git / GitHub

`.gitignore` excludes `.env` (never commit keys) and caches; `graphify-out/` is tracked so teammates and assistants pull the graph.

## Success criteria

- Given a raw transcript, the system returns validated structured JSON ✅
- Missing details remain null/empty/unknown ✅ (enforced by prompt + schema defaults + tests)
- No diagnosis or treatment is generated ✅ (prompt guardrails; `extra="forbid"` rejects any extra fields such as a diagnosis)
