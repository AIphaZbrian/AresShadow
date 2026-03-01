# Ares Infrastructure — vNext (v0.2.1)

## Deliverable 1 — System Overall Architecture (Text Structure)

```text
[L0 Interfaces]
  - Telegram | Web | Discord | HTTP API | CLI
  - External Feeds: Market | Onchain | News | Research

[L1 Gateway + Identity]
  - Envelope Normalizer
  - Identity Map (org/user/workspace)
  - RBAC/ABAC + Capability Tokens
  - Session Router (threading, replay ids)

[L2 Event Bus + Scheduler]
  - Timers/Cron (heartbeat, daily, weekly)
  - Ingest (pollers, webhooks)
  - Queue (priority lanes)
  - Dedup + Idempotency
  - Retry + Backoff

[L3 Supervisor / Orchestrator]
  - Plan Graph Builder (DAG)
  - Execution Runner
  - Verification Layer (invariants/tests)
  - Risk Gate (approval-required ops)
  - Writeback Layer (artifacts + db)

[L4 Digital Employees (Workers)]
  - market_intel
  - onchain_watch
  - orderbook_core
  - research
  - ops
  - content_engine

[L5 Tool Runtime]
  - Data connectors (REST/WS)
  - Compute jobs (python)
  - Messaging (telegram)
  - Code/CI (git)
  - Trading (SIM default; LIVE behind gate)

[L6 Memory + Data Plane]
  - Structured DB: events/snapshots/signals/decisions/audits
  - Human memory: docs/runbooks/daily logs
  - Artifact store: reports/json/pdf

[L7 Observability + Security]
  - Metrics + traces
  - Audit + replay
  - Secret management
  - Isolation (egress policy)
```

---

## Deliverable 2 — Module Relationship Diagram

```mermaid
flowchart TB
  subgraph L0[Interfaces]
    TG[Telegram]
    WEB[Web]
    API[HTTP API/CLI]
    FEED[External Feeds]
  end

  subgraph L1[Gateway+Identity]
    ENV[Envelope Normalizer]
    IDM[Identity Map]
    CAP[Capability Tokens]
    SES[Session Router]
  end

  subgraph L2[Event Bus+Scheduler]
    BUS[Event Bus]
    Q[Priority Queues]
    DEDUP[Dedup/Idempotency]
    RETRY[Retry/Backoff]
    CRON[Cron/Timers]
  end

  subgraph L3[Supervisor]
    PLAN[Plan DAG]
    RUN[Execute]
    VERIFY[Verify]
    GATE[Risk Gate]
    WB[Writeback]
  end

  subgraph L4[Workers]
    W1[market_intel]
    W2[onchain_watch]
    W3[orderbook_core]
    W4[research]
    W5[ops]
    W6[content_engine]
  end

  subgraph L5[Tool Runtime]
    TDATA[Data APIs]
    TCOMP[Compute Jobs]
    TMSG[Telegram Sender]
    TCODE[Git/CI]
    TTRADE[Trading SIM/LIVE]
  end

  subgraph L6[Memory+Data]
    DB[(Structured DB)]
    ART[Artifacts]
    HM[Human Memory]
  end

  subgraph L7[Obs+Sec]
    OBS[Metrics/Traces]
    AUD[Audit/Replay]
    SEC[Secrets/Isolation]
  end

  TG-->ENV
  WEB-->ENV
  API-->ENV
  FEED-->ENV

  ENV-->IDM-->CAP-->SES-->BUS
  CRON-->BUS

  BUS-->Q-->DEDUP-->RETRY-->PLAN
  PLAN-->RUN-->VERIFY-->GATE-->WB

  RUN-->W1
  RUN-->W2
  RUN-->W3
  RUN-->W4
  RUN-->W5
  RUN-->W6

  W1-->TDATA
  W2-->TDATA
  W3-->TDATA
  W4-->TCOMP
  W5-->TCOMP
  W6-->TMSG

  WB-->DB
  WB-->ART
  WB-->HM

  BUS-->OBS
  RUN-->OBS
  WB-->AUD
  CAP-->SEC
  TDATA-->AUD
  TMSG-->AUD
```

---

## Deliverable 3 — Execution Flow Diagram (Plan→Execute→Verify→Writeback)

```mermaid
sequenceDiagram
  autonumber
  participant Trg as Trigger(Cron/Webhook/Manual)
  participant Gw as Gateway+Identity
  participant Bus as Event Bus
  participant Sup as Supervisor
  participant Wrk as Worker
  participant Tool as Tool Runtime
  participant Mem as Memory/DB
  participant Msg as Telegram

  Trg->>Gw: event
  Gw->>Gw: authz + capabilities
  Gw->>Bus: enqueue(event, priority, idem_key)
  Bus->>Bus: dedup + retry policy
  Bus->>Sup: dispatch
  Sup->>Sup: build plan DAG + token budget
  Sup->>Wrk: run step
  Wrk->>Tool: fetch/compute
  Tool-->>Wrk: result
  Wrk-->>Sup: structured output + evidence
  Sup->>Sup: verify invariants
  Sup->>Mem: writeback(db + artifacts + audit)
  alt threshold met
    Sup->>Msg: push alert (structured)
  else threshold not met
    Sup->>Sup: suppress (no-noise)
  end
```

---

## Deliverable 4 — Autonomous Evolution Loop Diagram

```mermaid
flowchart LR
  A[Run Completed] --> B[Telemetry Capture]
  B --> C[Distill: checkpoints + deltas]
  C --> D[Propose Patch Set]
  D --> E[Sandbox Validate: replay + tests]
  E -->|pass| F[Promote Version]
  E -->|fail| G[Reject + Log]
  F --> H[Canary Rollout]
  H --> I[Monitor Guardrails]
  I -->|regression| J[Auto Rollback]
  I -->|ok| K[Full Rollout]
```

---

## Deliverable 5 — Version + Upgrade Notes

### v0.2.1
- Formalized 7-layer architecture (L0–L7)
- Standardized Supervisor pipeline: PLAN/RUN/VERIFY/WRITEBACK
- Introduced capability-token gating model (design-level)
- Introduced idempotency + dedup + priority lanes (design-level)
- Introduced audit/replay as first-class cross-cutting module

---

## Deliverable 6 — Token Optimization Structure (Token Scheduler)

### Budget Lanes
- L0: 0-token rules (thresholds, dedup, caching)
- L1: low-token templates (fixed bilingual blocks)
- L2: medium-token synthesis (multi-source fusion)
- L3: high-token reasoning (only P0 severity + approved)

### Deterministic Output Strategy
- Always compute-first (numbers) → speak-later (language)
- Store raw facts in DB/JSONL; store only distilled decisions in long-term memory
- Cooldown windows + aggregation to suppress noise

### Degradation Policy
- cost cap hit ⇒ downgrade L2→L1→L0
- API failures ⇒ retry(3) w/ backoff; emit single incident record; no spam

---

## Guardrails (Security + Permissions)

- External write actions require: capability token + audit log + replay id
- Trading LIVE requires: explicit approval gate + limits + rollback plan
- Messaging spam control: strict thresholds + dedup keys + cooldown

