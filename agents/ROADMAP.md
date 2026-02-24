# Digital Employee Roadmap

## Phase 0 – Repository & Planning (Done / In Progress)
- [x] Initialize repo skeleton (docs/, agents/, infra/, scripts/).  
- [x] Draft architecture document (`docs/digital-employee-architecture.md`).  
- [ ] Finalize backlog + owner assignments.  
- [ ] Connect to remote git origin (pending secure credentials setup).

## Phase 1 – MVP (Target: +2 weeks)
1. **Intel Feed Prototype**  
   - Integrate single high-signal data source (e.g., Dune query or Binance stream).  
   - Normalize + persist in Postgres-lite.  
2. **ARES-INTEL Loop v0**  
   - Retrieval-augmented prompt template.  
   - Output JSON + localized summary.  
3. **Manual Ops Hand-off**  
   - CLI / chat command to request Ops action.  
   - Capture action logs.

## Phase 2 – Backbone (Target: +4–6 weeks)
1. Multi-source ingestion graph + health monitors.  
2. LangGraph (or chosen orchestrator) pipelines for both agents.  
3. Ops execution automations (trading API sandbox, reporting).  
4. Observability baseline: logging, metrics, alerting.  
5. Human-in-loop console + approval webhooks.

## Phase 3 – Expansion (Target: +8 weeks)
1. Self-evaluation harness (regression tests for prompts + actions).  
2. Governance dashboard (risk KPIs, audit explorer).  
3. Deployment blueprints (dev/stage/prod).  
4. Knowledge distillation + skill reuse across new digital employees.

## Backlog Candidates
- Glossary + localization package.  
- Secrets management wiring (Vault/Teller).  
- CI template (GitHub Actions) for lint/test/deploy.  
- Synthetic data generator for stress tests.  
- Web UI for signal triage.

---
_Update cadence: weekly at minimum; include status + blockers each update._
