# Graph Report - repo_main  (2026-07-06)

## Corpus Check
- 57 files · ~11,438 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 347 nodes · 700 edges · 40 communities (25 shown, 15 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 38 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c171136f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

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
- [[_COMMUNITY_streamlit_demo.py|streamlit_demo.py]]
- [[_COMMUNITY_test_summary_safety.py|test_summary_safety.py]]

## God Nodes (most connected - your core abstractions)
1. `PatientIntakeExtraction` - 46 edges
2. `ClinicalSummaryEngine` - 24 edges
3. `SummarySection` - 22 edges
4. `rich_valid()` - 22 edges
5. `SummaryAtom` - 19 edges
6. `ClinicalSummaryDraft` - 17 edges
7. `validate_summary_output()` - 17 edges
8. `ClinicalSummaryResponse` - 15 edges
9. `extract_intake()` - 15 edges
10. `Clock` - 14 edges

## Surprising Connections (you probably didn't know these)
- `FrozenClock` --uses--> `SummarySectionId`  [INFERRED]
  tests/services/test_clinical_summary_engine.py → app/schemas/clinical_summary.py
- `test_section_rejects_empty_atoms_without_omitted_reason()` --calls--> `SummarySection`  [EXTRACTED]
  tests/schemas/test_clinical_summary_schema.py → app/schemas/clinical_summary.py
- `FrozenClock` --uses--> `ClinicalSummaryStatus`  [INFERRED]
  tests/services/test_clinical_summary_engine.py → app/schemas/clinical_summary.py
- `test_full_extraction_round_trips()` --calls--> `PatientIntakeExtraction`  [EXTRACTED]
  tests/test_schema.py → app/schemas/intake.py
- `test_invalid_severity_rejected()` --calls--> `PatientIntakeExtraction`  [EXTRACTED]
  tests/test_schema.py → app/schemas/intake.py

## Import Cycles
- None detected.

## Communities (40 total, 15 thin omitted)

### Community 0 - "test_extraction.py"
Cohesion: 0.10
Nodes (34): ClinicalSummaryAPIResponse, ClinicalSummaryDraft, ClinicalSummaryRequest, ClinicalSummaryResponse, ClinicalSummaryStatus, EvidenceRef, MissingOrUnresolvedQuestion, MissingQuestionSeverity (+26 more)

### Community 1 - "intake.py"
Cohesion: 0.10
Nodes (24): post_clinical_summary(), POST /api/v1/clinical-summary — Sprint 2 endpoint.  HTTP semantics per design: -, post_extract_intake(), HTTP edge for the intake extraction service., Extract validated intermediate clinical JSON from a raw transcript.      Extract, create_app(), Application entrypoint.  Run locally:     uvicorn app.main:app --reload, ExtractIntakeRequest (+16 more)

### Community 2 - "Version Roadmap"
Cohesion: 0.11
Nodes (18): Sprint 10 — Doctor-Controlled Follow-up Plans, Sprint 11 — Longitudinal Patient Monitoring, Sprint 12 — Population Health Dashboard, Sprint 1 — AI Patient Interview, Sprint 2 — Clinical Summary, Sprint 3 — Healthcare Data Pipeline, Sprint 4 — FHIR Clinical Structuring, Sprint 5 — AWS HealthLake Integration (+10 more)

### Community 3 - "client.py"
Cohesion: 0.07
Nodes (41): get_settings(), Application configuration loaded from environment / .env., Environment-driven settings.      OPENAI_API_KEY is required at call time (not i, Settings, ConfigurationError, ExtractionValidationError, IntakeError, LLMUnavailableError (+33 more)

### Community 4 - "routes_intake.py"
Cohesion: 0.11
Nodes (36): SummarySection, PatientIntakeExtraction, Structured clinical facts explicitly stated by the patient.      Extraction-only, build_care_goals_or_preferences(), build_chief_concern(), build_history_context(), build_medications_allergies(), build_missing_or_unresolved_section() (+28 more)

### Community 5 - "Pre-Visit Patient Intake — Sprint 1: Clinical Extraction Service"
Cohesion: 0.18
Nodes (10): Architecture (Sprint 1 slice), Git / GitHub, Pre-Visit Patient Intake — Sprint 1: Clinical Extraction Service, Regenerate the Graphify graph, Run it (backend + demo UI), Sprint 2 — Clinical Summary Engine, Success criteria (from sprint doc), Tests (+2 more)

### Community 6 - "steps.py"
Cohesion: 0.11
Nodes (34): post(), API tests for POST /api/v1/clinical-summary (design section 5)., test_blocked_summary_returns_422(), test_custom_intake_id_is_honored(), test_evidence_included_by_default_render_can_suppress_display_only(), test_json_format_skips_markdown_rendering(), test_malformed_json_returns_400(), test_response_validates_against_schema() (+26 more)

### Community 7 - "System Architecture"
Cohesion: 0.40
Nodes (4): Early Sprint Architecture, High-Level Flow, Later Enterprise Architecture, System Architecture

### Community 8 - "FHIR as the Technical Moat"
Cohesion: 0.50
Nodes (3): FHIR as the Technical Moat, Strategy, Target FHIR Resources

### Community 9 - "Product Vision"
Cohesion: 0.50
Nodes (3): Important Boundary, Product Vision, What Makes This Valuable

### Community 13 - "sprint_02_clinical_summary.md"
Cohesion: 0.06
Nodes (34): 1. New Pydantic Schemas, 2. Service-Layer Design, 3. API Endpoint Design, 4. Validation Invariants, 5. Test Cases, 6. File-by-File Implementation Plan, 7. Streamlit Demo Work for Claude Afterward, API tests (+26 more)

### Community 34 - "test_summary_safety.py"
Cohesion: 0.28
Nodes (19): ClinicalSummaryRenderRequest, Display formatting options — kept separate from clinical content., SummaryAtom, Markdown rendering of a ``ClinicalSummaryDraft``.  Display only: output is limit, render_markdown(), validate_summary_output(), rich_valid(), codes() (+11 more)

## Knowledge Gaps
- **69 isolated node(s):** `Architecture (Sprint 1 slice)`, `Run it (backend + demo UI)`, `Try it`, `Tests`, `Regenerate the Graphify graph` (+64 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PatientIntakeExtraction` connect `routes_intake.py` to `test_extraction.py`, `intake.py`, `test_summary_safety.py`, `client.py`, `steps.py`?**
  _High betweenness centrality (0.156) - this node is a cross-community bridge._
- **Why does `ClinicalSummaryEngine` connect `test_extraction.py` to `intake.py`, `test_summary_safety.py`, `client.py`, `routes_intake.py`, `steps.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `rich_valid()` connect `test_summary_safety.py` to `routes_intake.py`, `steps.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `PatientIntakeExtraction` (e.g. with `ClinicalSummaryEngine` and `Clock`) actually correct?**
  _`PatientIntakeExtraction` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ClinicalSummaryEngine` (e.g. with `Step` and `ClinicalSummaryDraft`) actually correct?**
  _`ClinicalSummaryEngine` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `SummarySection` (e.g. with `ClinicalSummaryEngine` and `Clock`) actually correct?**
  _`SummarySection` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `SummaryAtom` (e.g. with `ClinicalSummaryEngine` and `Clock`) actually correct?**
  _`SummaryAtom` has 3 INFERRED edges - model-reasoned connections that need verification._