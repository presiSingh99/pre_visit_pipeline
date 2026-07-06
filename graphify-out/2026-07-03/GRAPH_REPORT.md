# Graph Report - pre_visit_pipeline  (2026-07-03)

## Corpus Check
- 40 files · ~4,718 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 163 nodes · 211 edges · 33 communities (18 shown, 15 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_test_extraction.py|test_extraction.py]]
- [[_COMMUNITY_intake.py|intake.py]]
- [[_COMMUNITY_Version Roadmap|Version Roadmap]]
- [[_COMMUNITY_client.py|client.py]]
- [[_COMMUNITY_routes_intake.py|routes_intake.py]]
- [[_COMMUNITY_Pre-Visit Patient Intake — Sprint 1 Clinical Extraction Service|Pre-Visit Patient Intake — Sprint 1: Clinical Extraction Service]]
- [[_COMMUNITY_steps.py|steps.py]]
- [[_COMMUNITY_System Architecture|System Architecture]]
- [[_COMMUNITY_FHIR as the Technical Moat|FHIR as the Technical Moat]]
- [[_COMMUNITY_Product Vision|Product Vision]]
- [[_COMMUNITY_Data Pipeline Before HealthLake|Data Pipeline Before HealthLake]]
- [[_COMMUNITY_Clinical Safety Guardrails|Clinical Safety Guardrails]]
- [[_COMMUNITY_sprint_01_ai_patient_interview|sprint_01_ai_patient_interview.md]]
- [[_COMMUNITY_sprint_02_clinical_summary|sprint_02_clinical_summary.md]]
- [[_COMMUNITY_sprint_03_healthcare_data_pipeline|sprint_03_healthcare_data_pipeline.md]]
- [[_COMMUNITY_sprint_04_fhir_clinical_structuring|sprint_04_fhir_clinical_structuring.md]]
- [[_COMMUNITY_sprint_05_aws_healthlake_integration|sprint_05_aws_healthlake_integration.md]]
- [[_COMMUNITY_sprint_06_doctor_dashboard|sprint_06_doctor_dashboard.md]]
- [[_COMMUNITY_sprint_07_delta_engine|sprint_07_delta_engine.md]]
- [[_COMMUNITY_sprint_08_clinical_flagging_engine|sprint_08_clinical_flagging_engine.md]]
- [[_COMMUNITY_sprint_09_ai_decision_support|sprint_09_ai_decision_support.md]]
- [[_COMMUNITY_sprint_10_doctor_controlled_followups|sprint_10_doctor_controlled_followups.md]]
- [[_COMMUNITY_sprint_11_longitudinal_monitoring|sprint_11_longitudinal_monitoring.md]]
- [[_COMMUNITY_sprint_12_population_dashboard|sprint_12_population_dashboard.md]]
- [[_COMMUNITY_test_request.py|test_request.py]]

## God Nodes (most connected - your core abstractions)
1. `extract_intake()` - 15 edges
2. `PatientIntakeExtraction` - 13 edges
3. `LLMUnavailableError` - 9 edges
4. `ExtractionValidationError` - 9 edges
5. `call_extraction_model()` - 9 edges
6. `Pre-Visit Patient Intake — Sprint 1: Clinical Extraction Service` - 8 edges
7. `get_settings()` - 7 edges
8. `IntakeExtractionResult` - 7 edges
9. `ExtractIntakeRequest` - 7 edges
10. `IntakeError` - 6 edges

## Surprising Connections (you probably didn't know these)
- `test_api_maps_llm_failure_to_502()` --calls--> `LLMUnavailableError`  [EXTRACTED]
  tests/test_extraction.py → app/core/errors.py
- `test_evidence_without_flag_fails_closed()` --indirect_call--> `ExtractionValidationError`  [INFERRED]
  tests/test_extraction.py → app/core/errors.py
- `test_red_flag_inconsistency_fails_closed()` --indirect_call--> `ExtractionValidationError`  [INFERRED]
  tests/test_extraction.py → app/core/errors.py
- `test_full_extraction_round_trips()` --calls--> `PatientIntakeExtraction`  [EXTRACTED]
  tests/test_schema.py → app/schemas/intake.py
- `test_invalid_severity_rejected()` --calls--> `PatientIntakeExtraction`  [EXTRACTED]
  tests/test_schema.py → app/schemas/intake.py

## Import Cycles
- None detected.

## Communities (33 total, 15 thin omitted)

### Community 0 - "test_extraction.py"
Cohesion: 0.13
Nodes (20): ExtractionValidationError, IntakeError, LLMUnavailableError, Typed application errors.  The service layer raises these; the API layer maps th, Base class for intake pipeline errors., The upstream LLM API failed (network, auth, rate limit, 5xx)., The LLM output could not be validated against the intake schema., extract_intake() (+12 more)

### Community 1 - "intake.py"
Cohesion: 0.13
Nodes (21): ExtractIntakeRequest, ExtractionMetadata, PatientIntakeExtraction, Intermediate clinical intake schemas (Sprint 1).  `PatientIntakeExtraction` is t, Server-generated audit metadata. Never produced by the LLM., Request body for POST /extract-intake., Patient-stated severity. `unknown` when the patient did not state it., Structured clinical facts explicitly stated by the patient.      Extraction-only (+13 more)

### Community 2 - "Version Roadmap"
Cohesion: 0.11
Nodes (18): Sprint 10 — Doctor-Controlled Follow-up Plans, Sprint 11 — Longitudinal Patient Monitoring, Sprint 12 — Population Health Dashboard, Sprint 1 — AI Patient Interview, Sprint 2 — Clinical Summary, Sprint 3 — Healthcare Data Pipeline, Sprint 4 — FHIR Clinical Structuring, Sprint 5 — AWS HealthLake Integration (+10 more)

### Community 3 - "client.py"
Cohesion: 0.17
Nodes (15): get_settings(), Application configuration loaded from environment / .env., Environment-driven settings.      OPENAI_API_KEY is required at call time (not i, Settings, ConfigurationError, Missing or invalid configuration (e.g. no API key)., call_extraction_model(), _get_client() (+7 more)

### Community 4 - "routes_intake.py"
Cohesion: 0.27
Nodes (8): post_extract_intake(), HTTP edge for the intake extraction service., Extract validated intermediate clinical JSON from a raw transcript.      Extract, create_app(), Application entrypoint.  Run locally:     uvicorn app.main:app --reload, IntakeExtractionResult, API response envelope: validated extraction + audit metadata., FastAPI

### Community 5 - "Pre-Visit Patient Intake — Sprint 1: Clinical Extraction Service"
Cohesion: 0.22
Nodes (8): Architecture (Sprint 1 slice), Graphify, Pre-Visit Patient Intake — Sprint 1: Clinical Extraction Service, Setup, Success criteria (from sprint doc), Tests, Try it, What connects to Sprint 2

### Community 6 - "steps.py"
Cohesion: 0.50
Nodes (4): get_step(), Pipeline step registry — the seam for future graph orchestration.  Sprint 1 has, A named, pure pipeline step (a future graph node)., Step

### Community 7 - "System Architecture"
Cohesion: 0.40
Nodes (4): Early Sprint Architecture, High-Level Flow, Later Enterprise Architecture, System Architecture

### Community 8 - "FHIR as the Technical Moat"
Cohesion: 0.50
Nodes (3): FHIR as the Technical Moat, Strategy, Target FHIR Resources

### Community 9 - "Product Vision"
Cohesion: 0.50
Nodes (3): Important Boundary, Product Vision, What Makes This Valuable

## Knowledge Gaps
- **41 isolated node(s):** `Architecture (Sprint 1 slice)`, `Setup`, `Try it`, `Tests`, `Graphify` (+36 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PatientIntakeExtraction` connect `intake.py` to `test_extraction.py`, `client.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `extract_intake()` connect `test_extraction.py` to `intake.py`, `client.py`, `routes_intake.py`, `steps.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `LLMUnavailableError` connect `test_extraction.py` to `client.py`, `routes_intake.py`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `ExtractionValidationError` (e.g. with `test_evidence_without_flag_fails_closed()` and `test_red_flag_inconsistency_fails_closed()`) actually correct?**
  _`ExtractionValidationError` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `HTTP edge for the intake extraction service.`, `Extract validated intermediate clinical JSON from a raw transcript.      Extract`, `Application configuration loaded from environment / .env.` to the rest of the system?**
  _72 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_extraction.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12923076923076923 - nodes in this community are weakly interconnected._
- **Should `intake.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13043478260869565 - nodes in this community are weakly interconnected._