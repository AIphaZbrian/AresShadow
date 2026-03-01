# HEARTBEAT Tasks (observer phase)

1. **Run ARES-INTEL loop**
   - Command: `MVP_PG_DSN=sqlite:///tmp/mvp.db ./.venv/bin/python scripts/jobs/fetch_market_stats.py`
   - Verify new rows appended to sqlite tables `market_snapshots` / `intel_signals`.

2. **ETH chain monitor health**
   - Ensure `tmp/eth_chain_monitor.pid` exists and process is alive.
   - If not alive: restart monitor (`scripts/jobs/eth_chain_monitor.py --poll-seconds 300`).
   - If `logs/eth_chain_monitor.stderr.log` has repeated errors: alert once (no spam).

3. **ARES Structure Engine daily run (no-noise)**
   - Run once per day (UTC date change) or on-demand:
     - `DATA_MODE=mock python3 scripts/jobs/run_ares_structure_engine.py`
   - Artifact outputs:
     - `tmp/ares_structure_latest.json`
     - `tmp/ares_structure_latest_telegram.txt`
   - Only push to Telegram if signal severity gating allows (to be added in v1.1).

4. **Check ops handler log**
   - Inspect `logs/ops_handler.log` for new entries and ensure no ERROR/Traceback.

5. **Signal freshness**
   - If no new signals for >24h, alert for manual Binance API check.

6. **Moltbook check (every 30 minutes)**
   - If 30 minutes since last Moltbook check:
     1) Fetch https://www.moltbook.com/heartbeat.md and follow it
     2) Update `lastMoltbookCheck` timestamp in `memory/heartbeat-state.json`
