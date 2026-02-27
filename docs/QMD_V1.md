# QMD v1 (Query Memory Distillation) — Execution Spec

## Objective
Minimize token burn while maximizing continuity and correctness.

We implement a **hybrid** strategy:
- **Thread memory (short-term):** keep a compact **State Block** + last few turns.
- **Checkpointing (distillation):** periodically compress noisy dialogue into a structured checkpoint.
- **Long-term memory:** only store reusable, approved, low-noise facts/SOPs/preferences.
- **Retrieval:** query-driven, top-k small, scoped to relevant memory types.

## Why hybrid
- Pure “stuff everything into context” → token cost grows linearly.
- Pure “vector memory only” → drift/false recall and repeated re-asking.
- Hybrid keeps **O(1)** thread state and **O(k)** relevant recalls.

## Thresholds
We use three tiers to avoid trim thrashing:
- `reserveTokensFloor` — always preserved core context.
- `softThresholdTokens` — triggers soft distill.
- `hardThresholdTokens` — triggers hard distill.

Recommended defaults in `config/qmd_v1.yaml`:
- reserve: 4200
- soft: 7500
- hard: 10500

## Distillation policies
### Soft distill
Keep:
- System constraints / safety
- Goal
- State Block (structured)
- Top retrieved memories (topK)
- Last `keepLastTurns`

Compress the remainder into a checkpoint (<= `checkpointMaxLines`).

### Hard distill
Keep only:
- State Block
- Constraints
- Minimal pointers to sources (file paths, URLs, commit hashes)
- Last few turns (<= `keepLastTurns`)

## Long-term memory write gate (anti-pollution)
Write to long-term only when one is true:
- User explicitly asks to remember
- Item is approved/confirmed
- SOP/decision reused >= 2 times

Every memory entry should include:
- `type` (preferences|decisions|sop|safety_constraints|facts)
- `scope` (agent|project|thread)
- `confidence`
- `source` pointer
- payload

## Checkpoint output format
Always output checkpoints in this fixed schema:
1. **Goal**
2. **Constraints**
3. **State** (key:value)
4. **Decisions** (date + short)
5. **Open Loops** (next actions)
6. **Pointers** (paths/urls/commits/message ids)

### Optional: Mindmap view (ultra-low token context)
Maintain a separate `memory/context_mindmap.md` using Mermaid `mindmap`.
- Store only stable nodes (facts/decisions/SOP pointers)
- Avoid raw chat logs
- Link to files instead of copying text

## Operational note
- External data cache (e.g., market stats) can remain at ~1m TTL.
- Conversation state cache should be much longer (45m+) to avoid unnecessary rebuild.
- Retrieval cache should be moderate (10m) to reduce repeat embedding/search.
