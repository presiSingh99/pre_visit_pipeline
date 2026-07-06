# Data Pipeline Before HealthLake

HealthLake should not be the first stop. The intake conversation is messy, unstructured patient language.

Pipeline:

1. Patient chat transcript
2. Raw transcript storage
3. Cleaning and normalization
4. Clinical extraction
5. Pydantic validation
6. Intermediate structured JSON
7. Audit logging and versioning
8. FHIR mapping
9. FHIR bundle validation
10. AWS HealthLake ingestion

## Why This Matters

Patient text like:

"My throat hurts bad and I took Advil. Started maybe 3 days ago. No breathing problems."

Must become structured data like:

- Chief complaint: sore throat
- Duration: 3 days
- Severity: moderate or unknown depending on stated language
- Medication: Advil / ibuprofen
- Red flags: false if no breathing issues/chest pain reported

Only after validation should data move toward FHIR and HealthLake.
