# Product Vision

We are building an AI-powered healthcare operations copilot for pre-visit patient intake and post-visit monitoring.

The system allows patients to complete a conversational AI intake before seeing a doctor. The AI gathers symptoms, medical history, medications, allergies, timeline, and risk signals. It then extracts the conversation into structured clinical data and generates a physician-ready summary.

The doctor reviews the AI-prepared report and makes the final decision:

- Schedule appointment
- Telehealth visit
- Nurse follow-up
- Self-care guidance
- OTC recommendation under clinician approval
- Emergency escalation

After the doctor makes a decision, the AI continues monitoring the patient at home using follow-up questions triggered by the care plan.

The long-term platform becomes:

Patient app -> AI intake -> data pipeline -> FHIR -> AWS HealthLake -> doctor dashboard -> clinical summaries -> follow-up monitoring -> delta reports -> population health analytics.

## What Makes This Valuable

The product saves doctor time by moving repetitive information gathering before the visit. It gives clinicians clean summaries, red flags, deltas since last visit, and structured data that can later integrate with EHR systems.

## Important Boundary

The AI does not diagnose, prescribe, or make final clinical decisions. It acts as an intake assistant, data structuring engine, monitoring agent, and clinical operations copilot.
