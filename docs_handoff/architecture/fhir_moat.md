# FHIR as the Technical Moat

FHIR is the interoperability layer that makes the product valuable beyond a simple chatbot.

If the system can produce clean HL7 FHIR R4 resources, it can later integrate with major EHR systems and AWS HealthLake.

## Target FHIR Resources

- Patient
- Encounter
- Observation
- Condition
- MedicationStatement
- AllergyIntolerance
- QuestionnaireResponse
- CarePlan

## Strategy

Do not map directly from raw transcript to FHIR.

Instead:

Raw transcript -> Intermediate clinical JSON -> Validated JSON -> FHIR resources -> HealthLake

The intermediate JSON keeps the system easier to test, audit, and evolve.
