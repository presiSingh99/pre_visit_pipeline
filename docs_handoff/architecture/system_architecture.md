# System Architecture

## High-Level Flow

Patient Mobile/Web App
-> AI Intake Conversation
-> Raw Transcript Store
-> Clinical Extraction Service
-> Structured Intake JSON
-> Validation Layer
-> FHIR Mapper
-> AWS HealthLake
-> Doctor Dashboard
-> Doctor Decision
-> Follow-up Workflow Engine
-> Patient Monitoring
-> Delta Reports

## Early Sprint Architecture

For Version 1:

- Frontend: Streamlit or React
- Backend: FastAPI
- LLM: OpenAI or Anthropic
- Validation: Pydantic v2
- Storage: Local JSON first, then Postgres/Supabase
- API testing: requests/httpx

## Later Enterprise Architecture

- Auth: Cognito/Auth0
- Database: Postgres/Aurora
- Object Storage: S3
- Queue/Event Bus: SQS/EventBridge
- Clinical Data Store: AWS HealthLake
- Analytics: Athena/QuickSight
- Deployment: Docker + ECS/Fargate or Kubernetes
- IaC: Terraform
