# Version Roadmap

## Version 1 — AI Intake MVP

Goal: Replace paper intake forms and generate structured clinical intake data.

### Sprint 1 — AI Patient Interview
Build an AI-assisted intake flow that captures patient complaint, history, medications, allergies, symptoms, and relevant background.

### Sprint 2 — Clinical Summary
Generate a physician-ready report: chief complaint, HPI, meds, allergies, timeline, red flags, and unresolved questions.

### Sprint 3 — Healthcare Data Pipeline
Create raw transcript storage, cleaning, validation, extraction, structured JSON, audit logs, and record versioning.

---

## Version 2 — Interoperability

Goal: Make the system compatible with enterprise healthcare infrastructure.

### Sprint 4 — FHIR Clinical Structuring
Map intermediate JSON to HL7 FHIR R4 resources such as Patient, Encounter, Observation, Condition, MedicationStatement, AllergyIntolerance, QuestionnaireResponse, and CarePlan.

### Sprint 5 — AWS HealthLake Integration
Send FHIR bundles to AWS HealthLake, retrieve longitudinal patient records, and query patient history.

### Sprint 6 — Doctor Dashboard
Create a clinician-facing dashboard for summaries, patient timeline, HealthLake data, previous visits, meds, allergies, and search.

---

## Version 3 — Clinical Intelligence

Goal: Help doctors quickly identify what matters.

### Sprint 7 — Delta Engine
Show what is new, worsened, improved, resolved, or unchanged since the last visit.

### Sprint 8 — Clinical Flagging Engine
Create red/yellow/green priority logic using rules plus AI. Red flags are surfaced immediately to the clinician.

### Sprint 9 — AI Decision Support
Provide draft suggestions for clinician review, such as possible questions to ask, possible labs to consider, and guideline reminders. No autonomous diagnosis or prescription.

---

## Version 4 — Continuous Care

Goal: Monitor patients after clinician decisions.

### Sprint 10 — Doctor-Controlled Follow-up Plans
Follow-up workflows are triggered by the doctor’s decision: self-care, medication monitoring, post-procedure check, PT check-in, etc.

### Sprint 11 — Longitudinal Patient Monitoring
Collect daily/weekly symptoms, medication adherence, pain scores, side effects, photos, and optionally wearables.

### Sprint 12 — Population Health Dashboard
Show practice-level insights: improving patients, high-risk patients, missed follow-ups, medication adherence, and patients needing outreach.

---

## Version 5 — Enterprise Platform

Goal: Scale to clinics and hospitals.

Future capabilities:

- Multi-clinic support
- Role-based access control
- EHR integration
- Scheduling integration
- Labs and imaging integration
- Referral workflows
- Insurance workflows
- Audit trails
- Quality review
- Predictive risk scoring
