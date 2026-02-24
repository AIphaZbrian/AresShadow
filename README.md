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

1. `poetry install` (or your preferred env manager) — tooling definition coming in future commits.  
2. `make dev` (placeholder) to spin up local services once infra scripts land.  
3. Read `docs/digital-employee-architecture.md` for the high-level system map.  
4. Track execution milestones in `agents/ROADMAP.md`.

## Status & Next Steps

- [x] Repository skeleton + documentation plan.  
- [ ] Complete v1 architecture document (in progress).  
- [ ] Finalize MVP backlog & owner assignments.  
- [ ] Connect to remote Git hosting (awaiting preferred flow / credentials).

---

_Contributor guidelines, CI, and automation hooks will follow once the architecture solidifies._
