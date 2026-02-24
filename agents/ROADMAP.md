# Digital Employee Roadmap

## Phase 0 – Repository & Planning (Done / In Progress)
- [x] Initialize repo skeleton (docs/, agents/, infra/, scripts/).  
- [x] Draft architecture document (`docs/digital-employee-architecture.md`).  
- [x] Connect to remote git origin (deploy key in place).  
- [ ] Finalize backlog + owner assignments (this doc, WIP).

## Phase 1 – MVP (Target: +2 weeks)
| Task | Owner | ETA | Notes |
| --- | --- | --- | --- |
| Select primary data source (Binance stats) & credentials | Ares | Day 1 | Fallback: Dune API. |
| Implement `fetch_market_stats.py` (cron job) | Ares | Day 2 | Writes to Postgres `market_snapshots`. |
| Scaffold lightweight Postgres + Redis via Docker Compose | Ares | Day 2 | Lives under `infra/compose-mvp.yml`. |
| Build `intel_evaluator` prompt + RAG hooks | Ares | Day 3 | Template + config YAML. |
| Persist signals + emit Redis stream | Ares | Day 3 | Schema defined in `docs/mvp-signal-loop.md`. |
| Create `ops_handler` CLI (manual confirm) | Ares | Day 4 | Write logs + chat webhook. |
| End-to-end dry run + logging | Ares + Liang | Day 5 | Document steps + capture screenshots/logs. |

## Phase 2 – Backbone (Target: +4–6 weeks)
1. Multi-source ingestion graph with health monitors (Prefect/Temporal).  
2. LangGraph (or chosen orchestrator) pipelines for both agents.  
3. Ops automation connectors (trading sandbox, reporting bots).  
4. Observability baseline: OTEL exporters, Grafana dashboards.  
5. Human-in-loop console + approval webhooks (Telegram/Slack commands).

## Phase 3 – Expansion (Target: +8 weeks)
1. Self-evaluation harness (prompt regression + action simulations).  
2. Governance dashboard (risk KPIs, audit explorer).  
3. Deployment blueprints (Terraform modules + CI workflows).  
4. Skill library for new digital employees (shared adapters, glossary).

## Backlog Candidates
- Glossary + localization package.  
- Secrets management wiring (Vault/Teller).  
- CI template (GitHub Actions) for lint/test/deploy.  
- Synthetic data generator for stress tests.  
- Web UI for signal triage.  
- Policy engine (OPA) integration for runtime guardrails.

---
_Update cadence: weekly at minimum; include status + blockers each update._
