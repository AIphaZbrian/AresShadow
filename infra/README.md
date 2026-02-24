# Infra Blueprint

This directory will host infrastructure-as-code (IaC) and deployment manifests for the Ares Shadow digital employees.

## Target Stack (draft)

| Layer | Tooling (candidate) | Notes |
| --- | --- | --- |
| Container runtime | Docker + ECS / K8s | Local dev uses Docker Compose. |
| Task orchestration | Temporal / LangGraph runtime | Keeps intelligence + ops flows observable. |
| Messaging | Redis Streams / Kafka | Event bus between agents. |
| Storage | Postgres, S3/MinIO, Vector DB (Qdrant) | Split hot/warm/cold tiers. |
| Secrets | HashiCorp Vault / AWS KMS | All API keys/SSH tokens centrally managed. |
| Observability | OpenTelemetry + Loki/Grafana | Unified traces/logs/metrics. |

## Immediate TODO

1. Add Docker Compose for local MVP (LLM proxy, Postgres, Redis).  
2. Define Terraform modules (networking, databases, agent services).  
3. Wire CI/CD to run IaC plan/apply in review environments.
