# Sprint 3 — Healthcare Data Pipeline

Goal: Build the production-style pipeline before FHIR and HealthLake.

Pipeline:

Raw transcript -> cleaning -> extraction -> validation -> structured JSON -> audit log -> storage.

Deliverables:

- Raw transcript table/store
- Structured extraction table/store
- Validation errors table/log
- Audit trail
- Record versioning
- Reprocessing ability

Success Criteria:

- Same transcript can be reprocessed with improved extraction logic.
- Raw source is preserved.
