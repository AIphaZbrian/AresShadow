# MVP Signal Loop

Goal: prove end-to-end viability using a single, high-signal source and a deterministic ops action.

## Scenario
- **Source**: Binance Spot 24h volume + price volatility (via public REST).  
- **Trigger**: When 1h volatility exceeds configured threshold AND 24h volume rank is top 20, raise signal.  
- **Ops Action**: Send structured alert to operations queue + draft hedging checklist.

## Flow
1. `fetch_market_stats` (cron or webhook) → stores latest price/volume in Postgres table `market_snapshots`.  
2. `intel_evaluator` job pulls latest snapshot, runs rule-based check + LLM reasoning to contextualize (news sentiment).  
3. Successful signal persisted to `intel_signals` table and emitted via Redis Stream `signals.raw`.  
4. `ops_handler` consumes stream, checks human-approval flag; if auto-approved, posts to Slack/Telegram + writes runbook entry.

## Schemas
```sql
CREATE TABLE market_snapshots (
  id UUID PRIMARY KEY,
  symbol TEXT,
  timestamp TIMESTAMPTZ,
  price NUMERIC,
  vol_24h NUMERIC,
  vol_rank INT,
  realized_vol_1h NUMERIC
);

CREATE TABLE intel_signals (
  id UUID PRIMARY KEY,
  symbol TEXT,
  created_at TIMESTAMPTZ,
  confidence NUMERIC,
  lang TEXT DEFAULT 'en',
  payload JSONB
);
```

## Human-in-loop Points
- Threshold tuning stored in config repo → ops can edit YAML without redeploy.  
- Approval toggle per symbol/subscriber (e.g., `auto_execute: false` for new markets).  
- Exception path auto-opens Linear ticket with context payload.

## Next Steps
1. Implement `scripts/jobs/fetch_market_stats.py` (requests + DB insert).  
2. Create prompt template for `intel_evaluator` (RAG + deterministic summary).  
3. Implement `ops_handler` with dry-run + logging.  
4. Add tests to simulate threshold crossing and verify alerts.
