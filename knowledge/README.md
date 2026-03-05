# Aipha Knowledge & Memory Layer (v1)

Goal: **fast capture** + **decision traceability** + **permanent retention**.

## What goes where

- `inbox/` — raw notes, copy-pastes, chat dumps. No structure required.
- `daily/` — daily log (what happened / decisions made / next actions).
- `decisions/` — ADRs (Decision Records). **Any “we decided …” must become an ADR.**
- `kb/` — reusable knowledge (glossary, runbooks, templates, policies).
- `projects/` — project-specific docs and links.
- `artifacts/` — generated outputs (reports, signal dumps, engine outputs).
- `index/` — machine-readable index for search / later vectorization.

## Operating rules (minimum)

1. **Capture first**: if unsure, drop it into `inbox/`.
2. **Decision > discussion**: once a decision is made, create an ADR in `decisions/`.
3. **Link evidence**: ADRs must link to artifacts, data, logs, or message context.

## 2-minute workflow

- New idea / snippet → `inbox/`
- End of day → summarize into `daily/YYYY-MM-DD.md`
- Any decision → `scripts/new_adr.sh "Title"` (creates an ADR stub)

## Search & traceability

- Every ADR has an id: `ADR-YYYYMMDD-NNN`
- `index/adr_index.jsonl` is the append-only ledger for ADR metadata.
