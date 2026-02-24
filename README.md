# Aipha Brain Lab · Digital Employee Stack

Structured workspace for designing, simulating, and deploying "digital employees" (autonomous agents) that support Aipha Brain Lab's trading and intelligence operations.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `docs/` | Architecture specs, decision records, operating manuals. |
| `agents/` | Roadmaps, role definitions, playbooks for each digital employee. |
| `infra/` | Infrastructure-as-code, deployment manifests, integration scripts. |
| `scripts/` | Utility CLIs, data loaders, cron helpers. |
| `memory/` | (Optional) Runtime/state artifacts when agents persist context locally. |

## Current Focus (Feb 2026)

1. Define the first two digital employees (Intelligence Analyst & Ops/Execution).  
2. Lay down the orchestration spine (data ingestion → reasoning → action).  
3. Establish governance: risk controls, auditability, and human-in-the-loop entry points.

## Quick Start

1. `scripts/bootstrap_mvp.sh` — spawn a Python venv + install placeholder deps.  
2. Read `docs/digital-employee-architecture.md` (system map) and `docs/mvp-signal-loop.md` (first closed-loop scenario).  
3. Review Phase 1 breakdown in `agents/ROADMAP.md`.  
4. Run `scripts/jobs/fetch_market_stats.py` to fetch Binance 24h stats (prints JSON stub; DB wiring TBD).

## Status & Next Steps

- [x] Repository skeleton + documentation plan.  
- [x] Connect to remote Git hosting (deploy key active).  
- [x] Draft v1 architecture + MVP signal loop.  
- [x] Add roadmap with Phase 1 task breakdown.  
- [ ] Implement data pipeline + ops handler code.  
- [ ] Add Docker Compose + Infra modules.  
- [ ] Hook up CI/testing workflows.

---

_Contributor guidelines, CI, and automation hooks will follow once the architecture solidifies._
