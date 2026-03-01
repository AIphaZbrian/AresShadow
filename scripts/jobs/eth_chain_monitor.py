#!/usr/bin/env python3
"""ETH mainnet monitor (Etherscan) — safety version.

Design goals (per spec):
- Poll every 5 minutes (no tight loops)
- Use Etherscan API key from env: ETHERSCAN_API_KEY
- Cache/compare previous cycle to avoid duplicate pushes
- Only trigger Telegram-worthy alerts on strict rules
- Always log JSON locally; daily summary supported

This script is transport-agnostic: it outputs a machine-readable alert payload to stdout
(when an alert triggers) and writes logs/state to workspace.
OpenClaw (agent) can pick up stdout and forward to Telegram with required formatting.

Usage:
  ETHERSCAN_API_KEY=... python3 scripts/jobs/eth_chain_monitor.py --once

Files:
  - state:  tmp/eth_monitor_state.json
  - records: logs/eth_monitor.jsonl
  - latest alerts: tmp/eth_alerts_latest.json
  - watchlists: config/eth_watchlists.json (copy from example)
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = PROJECT_ROOT / "tmp" / "eth_monitor_state.json"
RECORDS_PATH = PROJECT_ROOT / "logs" / "eth_monitor.jsonl"
ALERTS_LATEST_PATH = PROJECT_ROOT / "tmp" / "eth_alerts_latest.json"
WATCHLIST_PATH = PROJECT_ROOT / "config" / "eth_watchlists.json"
WATCHLIST_EXAMPLE_PATH = PROJECT_ROOT / "config" / "eth_watchlists.example.json"

# Etherscan API V2 base (V1 deprecated since 2025-08-15)
ETHERSCAN_BASE = "https://api.etherscan.io/v2/api"
CHAIN_ID_ETH_MAINNET = "1"
WEI_PER_ETH = 10**18

# Spec thresholds
THRESH_SINGLE_ALERT_ETH = 10_000.0
THRESH_LARGE_XFER_ETH = 5_000.0
THRESH_NEW_ADDR_ETH = 10_000.0
THRESH_EXCHANGE_NET_INFLOW_1H_ETH = 30_000.0
THRESH_GAS_UTIL_PCT = 95.0
THRESH_TXN_SURGE_PCT = 40.0

DEFAULT_POLL_SECONDS = 300


@dataclass
class ApiResult:
    ok: bool
    data: Any
    error: Optional[str] = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def http_get_json(url: str, timeout: int = 20) -> ApiResult:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Aipha-ETH-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        return ApiResult(ok=True, data=json.loads(raw))
    except Exception as e:
        return ApiResult(ok=False, data=None, error=str(e))


def etherscan_call(params: Dict[str, str], api_key: str, retries: int = 3, chainid: str = CHAIN_ID_ETH_MAINNET) -> ApiResult:
    q = params.copy()
    q["chainid"] = chainid
    q["apikey"] = api_key
    url = ETHERSCAN_BASE + "?" + urllib.parse.urlencode(q)

    last_err = None
    for attempt in range(1, retries + 1):
        r = http_get_json(url)
        if r.ok:
            payload = r.data
            # Etherscan sometimes returns {status:'0', message:'NOTOK', result:'Max rate limit reached'}
            if isinstance(payload, dict) and payload.get("status") == "0" and payload.get("message") == "NOTOK":
                last_err = str(payload.get("result"))
            else:
                return r
        else:
            last_err = r.error
        # backoff
        time.sleep(min(2 * attempt, 6))

    return ApiResult(ok=False, data=None, error=last_err or "unknown error")


def hex_to_int(x: str) -> int:
    if not x:
        return 0
    return int(x, 16)


def wei_hex_to_eth(x: str) -> float:
    return hex_to_int(x) / WEI_PER_ETH


def eth_block_number(api_key: str) -> ApiResult:
    return etherscan_call({"module": "proxy", "action": "eth_blockNumber"}, api_key)


def eth_get_block_by_number(api_key: str, block_hex: str) -> ApiResult:
    return etherscan_call(
        {"module": "proxy", "action": "eth_getBlockByNumber", "tag": block_hex, "boolean": "true"},
        api_key,
    )


def normalize_addr(a: str) -> str:
    return (a or "").lower()


def load_watchlists() -> Dict[str, Any]:
    if not WATCHLIST_PATH.exists() and WATCHLIST_EXAMPLE_PATH.exists():
        # do not auto-copy; keep explicit for safety
        return load_json(WATCHLIST_EXAMPLE_PATH, {})
    return load_json(WATCHLIST_PATH, {})


def flatten_exchange_addresses(w: Dict[str, Any]) -> Dict[str, str]:
    """Return addr->label for all exchange addresses."""
    out: Dict[str, str] = {}
    ex = (w.get("exchanges") or {})
    if isinstance(ex, dict):
        for name, addrs in ex.items():
            if not isinstance(addrs, list):
                continue
            for a in addrs:
                na = normalize_addr(a)
                if na:
                    out[na] = f"exchange:{name}"
    return out


def set_from_list(lst: Any) -> set[str]:
    if not isinstance(lst, list):
        return set()
    return {normalize_addr(x) for x in lst if normalize_addr(x)}


def compute_gas_util_pct(block: Dict[str, Any]) -> float:
    gas_used = hex_to_int(block.get("gasUsed") or "0x0")
    gas_limit = hex_to_int(block.get("gasLimit") or "0x0")
    if gas_limit <= 0:
        return 0.0
    return (gas_used / gas_limit) * 100.0


def extract_transfers(block: Dict[str, Any]) -> List[Dict[str, Any]]:
    txs = block.get("transactions") or []
    out = []
    for tx in txs:
        # Native ETH transfers are those with non-zero value.
        value_eth = wei_hex_to_eth(tx.get("value") or "0x0")
        if value_eth <= 0:
            continue
        out.append(
            {
                "hash": tx.get("hash"),
                "from": normalize_addr(tx.get("from")),
                "to": normalize_addr(tx.get("to")),
                "value_eth": float(value_eth),
            }
        )
    return out


def impact_level(kind: str) -> str:
    if kind in {"single_transfer_ge_10000", "exchange_net_inflow_ge_30000_1h", "gas_util_ge_95", "tx_surge_ge_40pct"}:
        return "high"
    return "medium"


def possible_market_impact(kind: str) -> str:
    mapping = {
        "single_transfer_ge_10000": "单笔超大额转账可能预示资金调仓/OTC交割/交易所入金或冷钱包迁移，短期波动与情绪风险上升。",
        "exchange_net_inflow_ge_30000_1h": "交易所净流入显著上升通常与潜在抛压相关；需结合价格、OI、资金费率确认。",
        "gas_util_ge_95": "Gas 使用率极高代表链上拥堵，常见于热点交易/清算/铸造事件；可能伴随高波动与手续费冲击。",
        "tx_surge_ge_40pct": "链上交易活跃度短时激增可能对应市场事件或大规模资金移动，需警惕趋势加速或反转。",
    }
    return mapping.get(kind, "需结合更广泛的市场数据进一步判断。")


def build_alert(
    block_height: int,
    block_ts: int,
    kind: str,
    detail: Dict[str, Any],
    tx_hash: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.fromtimestamp(block_ts, tz=timezone.utc).isoformat(),
        "block_height": block_height,
        "anomaly_type": kind,
        "impact_level": impact_level(kind),
        "possible_market_impact": possible_market_impact(kind),
        "tx_hash": tx_hash,
        "detail": detail,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="ETH mainnet monitor via Etherscan (safety version)")
    ap.add_argument("--once", action="store_true", help="Run a single cycle and exit")
    ap.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    args = ap.parse_args()

    api_key = os.getenv("ETHERSCAN_API_KEY")
    if not api_key:
        raise SystemExit("Missing env ETHERSCAN_API_KEY")

    watch = load_watchlists()
    exchange_map = flatten_exchange_addresses(watch)
    whales = set_from_list(watch.get("whales_top20"))
    blacklist = set_from_list(watch.get("blacklist"))

    state = load_json(
        STATE_PATH,
        {
            "last_block": None,
            "last_block_ts": None,
            "last_txs_per_min": None,
            "hour_window": [],  # list of {ts, direction, amount_eth, tx_hash}
            "alerted": {},  # eventKey -> true
            "last_success": None,
        },
    )

    def cycle() -> Tuple[bool, List[Dict[str, Any]]]:
        meta: Dict[str, Any] = {
            "ts": utc_now_iso(),
            "source": "etherscan",
            "ok": False,
        }

        bn = eth_block_number(api_key)
        if not bn.ok:
            meta["error"] = bn.error
            append_jsonl(RECORDS_PATH, {"type": "error", **meta})
            return False, []

        block_hex = bn.data.get("result") if isinstance(bn.data, dict) else None
        if not isinstance(block_hex, str):
            append_jsonl(RECORDS_PATH, {"type": "error", **meta, "error": "invalid blockNumber response"})
            return False, []

        height = hex_to_int(block_hex)
        blk = eth_get_block_by_number(api_key, block_hex)
        if not blk.ok:
            meta["error"] = blk.error
            append_jsonl(RECORDS_PATH, {"type": "error", **meta})
            return False, []

        block = blk.data.get("result") if isinstance(blk.data, dict) else None
        if not isinstance(block, dict):
            append_jsonl(RECORDS_PATH, {"type": "error", **meta, "error": "invalid block response"})
            return False, []

        block_ts = hex_to_int(block.get("timestamp") or "0x0")
        txs = block.get("transactions") or []
        tx_count = len(txs) if isinstance(txs, list) else 0

        gas_util = compute_gas_util_pct(block)

        # tx/min estimation using previous block timestamp
        txs_per_min = None
        if state.get("last_block_ts") and block_ts and block_ts > int(state["last_block_ts"]):
            dt = block_ts - int(state["last_block_ts"])
            if dt > 0:
                txs_per_min = (tx_count / dt) * 60.0

        # Large ETH transfers in block
        transfers = extract_transfers(block)
        large_transfers = [t for t in transfers if t["value_eth"] >= THRESH_LARGE_XFER_ETH]

        # Whale watch: label transfers involving whales/blacklist/exchanges
        whale_events = []
        for t in large_transfers:
            frm = t["from"]
            to = t["to"]
            flags = []
            if frm in whales or to in whales:
                flags.append("whale_top20")
            if frm in blacklist or to in blacklist:
                flags.append("blacklist")
            if frm in exchange_map or to in exchange_map:
                flags.append("exchange")
            if flags:
                whale_events.append({**t, "flags": flags, "exchange_to": exchange_map.get(to), "exchange_from": exchange_map.get(frm)})

        # Update 1h window for exchange net inflow
        hour_window: List[Dict[str, Any]] = list(state.get("hour_window") or [])
        cutoff = block_ts - 3600
        hour_window = [e for e in hour_window if int(e.get("ts", 0)) >= cutoff]

        for t in large_transfers:
            frm = t["from"]
            to = t["to"]
            amt = float(t["value_eth"])
            direction = None
            if to in exchange_map and frm not in exchange_map:
                direction = "in"
            elif frm in exchange_map and to not in exchange_map:
                direction = "out"
            if direction:
                hour_window.append({"ts": block_ts, "direction": direction, "amount_eth": amt, "tx_hash": t.get("hash")})

        inflow = sum(e["amount_eth"] for e in hour_window if e.get("direction") == "in")
        outflow = sum(e["amount_eth"] for e in hour_window if e.get("direction") == "out")
        net_inflow = inflow - outflow

        # tx surge compare to last cycle's tx/min (not last block) — use cached last_txs_per_min
        tx_surge_pct = None
        if txs_per_min is not None and state.get("last_txs_per_min"):
            prev = float(state["last_txs_per_min"]) or 0.0
            if prev > 0:
                tx_surge_pct = ((txs_per_min - prev) / prev) * 100.0

        # Build alerts with dedupe keys
        alerts: List[Dict[str, Any]] = []
        alerted: Dict[str, bool] = dict(state.get("alerted") or {})

        def seen(key: str) -> bool:
            return bool(alerted.get(key))

        def mark(key: str) -> None:
            alerted[key] = True

        # Rule 1: single transfer >= 10,000 ETH
        for t in large_transfers:
            if t["value_eth"] >= THRESH_SINGLE_ALERT_ETH:
                key = f"tx:{t.get('hash')}:single_ge_10000"
                if not seen(key):
                    alerts.append(
                        build_alert(
                            height,
                            block_ts,
                            "single_transfer_ge_10000",
                            {
                                "from": t["from"],
                                "to": t["to"],
                                "value_eth": t["value_eth"],
                                "to_is_exchange": bool(exchange_map.get(t["to"])),
                                "exchange_label": exchange_map.get(t["to"]),
                                "from_is_exchange": bool(exchange_map.get(t["from"])),
                            },
                            tx_hash=t.get("hash"),
                        )
                    )
                    mark(key)

        # Rule 2: exchange net inflow >= 30,000 ETH / 1h
        if net_inflow >= THRESH_EXCHANGE_NET_INFLOW_1H_ETH:
            key = f"block:{height}:net_inflow_1h"
            if not seen(key):
                alerts.append(
                    build_alert(
                        height,
                        block_ts,
                        "exchange_net_inflow_ge_30000_1h",
                        {"net_inflow_1h_eth": net_inflow, "inflow_1h_eth": inflow, "outflow_1h_eth": outflow},
                        tx_hash=None,
                    )
                )
                mark(key)

        # Rule 3: gas util >= 95%
        if gas_util >= THRESH_GAS_UTIL_PCT:
            key = f"block:{height}:gas_util_ge_95"
            if not seen(key):
                alerts.append(build_alert(height, block_ts, "gas_util_ge_95", {"gas_util_pct": gas_util}, None))
                mark(key)

        # Rule 4: hourly tx surge >= 40% (approx by tx/min change)
        if tx_surge_pct is not None and tx_surge_pct >= THRESH_TXN_SURGE_PCT:
            key = f"block:{height}:tx_surge"
            if not seen(key):
                alerts.append(
                    build_alert(
                        height,
                        block_ts,
                        "tx_surge_ge_40pct",
                        {"txs_per_min": txs_per_min, "prev_txs_per_min": float(state.get("last_txs_per_min")), "surge_pct": tx_surge_pct},
                        None,
                    )
                )
                mark(key)

        # New large address heuristic: a single transfer >= 10k ETH to a previously unseen address
        # (We don't do full balance ranking; keep it safe and cheap.)
        known_large = set_from_list(state.get("known_large_addresses") or [])
        for t in large_transfers:
            if t["value_eth"] >= THRESH_NEW_ADDR_ETH:
                to_addr = t["to"]
                if to_addr and to_addr not in known_large and to_addr not in exchange_map:
                    known_large.add(to_addr)

        # Record cycle snapshot (always)
        snapshot = {
            "type": "snapshot",
            "ts": utc_now_iso(),
            "block_height": height,
            "block_timestamp": block_ts,
            "gas_util_pct": gas_util,
            "tx_count": tx_count,
            "txs_per_min": txs_per_min,
            "large_transfers_ge_5000": len(large_transfers),
            "whale_events": whale_events[:50],
            "exchange_net_inflow_1h_eth": net_inflow,
        }
        append_jsonl(RECORDS_PATH, snapshot)

        # Update state
        state["last_block"] = height
        state["last_block_ts"] = block_ts
        if txs_per_min is not None:
            state["last_txs_per_min"] = txs_per_min
        state["hour_window"] = hour_window
        state["alerted"] = alerted
        state["known_large_addresses"] = sorted(list(known_large))[:500]
        state["last_success"] = utc_now_iso()
        save_json(STATE_PATH, state)

        # Write latest alerts file for OpenClaw pick-up
        save_json(ALERTS_LATEST_PATH, {"ts": utc_now_iso(), "alerts": alerts})

        return True, alerts

    ok, alerts = cycle()
    if alerts:
        # stdout is reserved for downstream transport (OpenClaw to Telegram)
        print(json.dumps({"ts": utc_now_iso(), "alerts": alerts}, ensure_ascii=False, indent=2))

    if args.once:
        return

    # Poll mode: sleep between cycles (no infinite tight loop)
    while True:
        time.sleep(max(30, int(args.poll_seconds)))
        cycle()


if __name__ == "__main__":
    main()
