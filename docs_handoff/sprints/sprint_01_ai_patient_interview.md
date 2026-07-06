# Sprint 1 — AI Patient Interview

Goal: Build an AI intake interview that collects patient information without diagnosing or prescribing.

Deliverables:

- Patient starts intake session
- AI asks one question at a time
- Captures chief complaint
- Captures symptom timeline
- Captures associated symptoms
- Captures medications and allergies
- Captures past/family/social history where relevant
- Stores raw transcript
- Produces initial structured extraction JSON

Tech:

- Python 3.11
- FastAPI
- Pydantic v2
- OpenAI/Anthropic structured outputs
- Local JSON or Postgres later

Success Criteria:

- Given a raw transcript, the system returns validated structured JSON.
- Missing details remain null/empty.
- No diagnosis or treatment is generated.
