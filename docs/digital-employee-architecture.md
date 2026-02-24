# Digital Employee Architecture · Aipha Brain Lab

_Last updated: 2026-02-24_

## 1. Purpose & Principles

- **Autonomy with guardrails**: Digital employees own end-to-end loops but expose deterministic checkpoints for human override.  
- **Composable intelligence**: Each employee is a graph of skills (perception → reasoning → action) that can be remixed per project.  
- **Language-agnostic interface**: Core logic runs in structured protocols (JSON/GraphQL/Events). Natural language is a presentation layer that can switch between English / 中文 / others per stakeholder.  
- **Audit-first**: Every decision, prompt, and action emits structured logs for replay, compliance, and RLHF-style refinement.

## 2. Roles Overview

| Role | Codename | Mission | Primary Inputs | Outputs |
| --- | --- | --- | --- | --- |
| Intelligence Analyst Agent | `ARES-INTEL` | Continuous intelligence coverage and signal synthesis. | On-/off-chain feeds, social firehose, research docs. | Prioritized insights, risk/opp flags, briefings. |
| Operations & Execution Agent | `ARES-OPS` | Turn validated signals into actions, enforce process discipline. | Intel outputs, strategy templates, operator commands. | Task executions (orders, reports, alerts), state updates, exception tickets. |

### 2.1 Intelligence Analyst Agent (`ARES-INTEL`)
- **Functions**  
  - Multi-source ingestion (APIs, RSS, GraphQL, scraping) with schema normalization.  
  - Feature extraction: sentiment, entity linking, anomaly detection.  
  - Hypothesis engine: run strategy rules, matching signals to playbooks.  
  - Publishing layer: generate concise briefs, dashboards, or API payloads.
- **Language Strategy**  
  - Stores source text in native language; reasoning happens on English-normalized embeddings; outputs auto-localize based on subscriber preferences.  
  - Translation handled via deterministic glossary + LLM translation fallback.
- **Guardrails**  
  - Rate limits per source, PII scrubbing, fact-check workflow before high-risk alerts.

### 2.2 Operations & Execution Agent (`ARES-OPS`)
- **Functions**  
  - Receives tasks via queue (Kafka/SQS) or API; validates preconditions.  
  - Interfaces with trading/order systems, notification services, document automation.  
  - Tracks SLAs, escalates anomalies to humans with recommended actions.  
  - Maintains runbooks; can request clarification from humans or other agents.  
- **Language Strategy**  
  - Machine interfaces remain structured; human comms auto-localize (English default, 中文 for HK/CN partners).  
- **Guardrails**  
  - Policy engine enforces risk thresholds, approval matrices, and dry-run vs live toggles.  
  - Immutable action logs with hash-chain for tamper evidence.

## 3. System Architecture

```
┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────────┐
│ Data Ingest │→→│ Intel Agent   │→→│ Ops Agent      │→→│ External Acts │
│ (ETL, APIs) │   │ (ARES-INTEL) │   │ (ARES-OPS)     │   │ (trade, comm)│
└─────────────┘   └──────────────┘   └───────────────┘   └──────────────┘
        ↑                │                    │                   │
        │        Human-in-loop Nodes   Risk Engine / Audit  Observability
```

### 3.1 Data Layer
- **Sources**: Binance/on-chain indexers, Dune queries, Nansen, Twitter/X, Telegram, internal notebooks.  
- **Pipelines**: Prefect / Airflow for scheduled jobs; WebSocket listeners for real-time.  
- **Storage**:  
  - Hot: Redis Streams / Kafka for events.  
  - Warm: PostgreSQL for structured facts.  
  - Cold: S3/MinIO for raw dumps + parquet.  
  - Semantic: Vector DB (Milvus/Qdrant) for memory + retrieval.

### 3.2 Intelligence Layer
- Graph orchestration (LangGraph / custom) orchestrates skills:  
  1. Ingest → Clean → Embed.  
  2. Retrieval-Augmented Reasoning (prompt templates w/ tools).  
  3. Insight packaging: JSON schema with `signal_id`, `confidence`, `lang`, `ttl`.  
- Memory: multi-tier (scratchpad per task, short-term conversation, long-term knowledge base).  
- Evaluation: automated tests (backtests, heuristics) before promoting insights.

### 3.3 Operations Layer
- Workflow engine (Temporal / Durable Functions) to run multi-step playbooks.  
- Integrations: Trading APIs, messaging (Telegram/Slack), ticketing (Linear/Jira), docs (Notion/Confluence).  
- Human touchpoints:  
  - `approve(signal_id)` hooks in chat.  
  - Ops console for queue management + overrides.  
- Safety: feature flags, canary mode, rollback scripts.

### 3.4 Observability & Governance
- Central log stack (OpenTelemetry → Loki/Elastic).  
- Metrics dashboards (Grafana) for latency, accuracy, coverage.  
- Policy store (OPA) for runtime decisions.  
- Identity & secrets via Vault / AWS KMS.

## 4. Language & Localization Strategy
- **Core**: All structured protocols in English to avoid encoding drift.  
- **Presentation**: Use locale tags per consumer; translation microservice (NLLB / GPT-4o) applied at delivery.  
- **Prompt discipline**: Keep multilingual examples in prompt library; use adapters for domain-specific terminology.  
- **Documentation**: Dual-language headers where needed; maintain glossary file shared across agents.

## 5. Build Phases & Deliverables

| Phase | Duration | Goals | Key Deliverables |
| --- | --- | --- | --- |
| MVP | 2 weeks | Single feed → intel loop → manual ops action. | Minimal pipelines, prompt templates, CLI trigger. |
| Backbone | 4-6 weeks | Multi-feed coverage, automated ops execution w/ approvals. | LangGraph flows, vector memory, ops playbooks. |
| Expansion | 8+ weeks | Self-learning, CI/CD, cross-project reuse. | Model eval harness, governance dashboard, deployment recipes. |

## 6. Human Collaboration Points
- Daily digest (auto-sent) with top 5 signals + pending actions.  
- Approval channel for high-impact trades.  
- Exception tickets auto-opened with reproduction context.  
- Ops team can drop new playbooks via YAML/JSON templates; agents auto-ingest after validation.

## 7. Open Questions / Next Decisions
1. Final choice of orchestration runtime (LangGraph vs custom).  
2. Hosting stack (AWS + ECS? GCP? On-prem?).  
3. Preferred CI/CD (GitHub Actions vs other).  
4. Secrets management baseline.  
5. Initial KPIs (coverage %, latency, accuracy) + evaluation dataset.

---
_This document will evolve into a fuller system design once tooling choices are locked._
