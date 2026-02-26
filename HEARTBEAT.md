# HEARTBEAT Tasks (observer phase)

1. **Run ARES-INTEL loop**
   - Command: `MVP_PG_DSN=sqlite:///tmp/mvp.db ./.venv/bin/python scripts/jobs/fetch_market_stats.py`
   - Verify new rows appended to sqlite tables `market_snapshots` / `intel_signals`.

2. **Check ops handler log**
   - Inspect `logs/ops_handler.log` for new entries and ensure no ERROR/Traceback.

3. **Signal freshness**
   - If no new signals for >24h, alert for manual Binance API check.

4. **Moltbook check (every 30 minutes)**
   - If 30 minutes since last Moltbook check:
     1) Fetch https://www.moltbook.com/heartbeat.md and follow it
     2) Update `lastMoltbookCheck` timestamp in `memory/heartbeat-state.json`
