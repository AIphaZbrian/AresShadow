#!/usr/bin/env python3
"""Generate 24h summary from logs/eth_monitor.jsonl.

Writes to tmp/eth_daily_summary_<YYYY-MM-DD>.json and prints markdown summary.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RECORDS_PATH = PROJECT_ROOT / "logs" / "eth_monitor.jsonl"
OUT_DIR = PROJECT_ROOT / "tmp"


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    if not RECORDS_PATH.exists():
        raise SystemExit(f"No records at {RECORDS_PATH}")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=int(args.hours))

    snapshots: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    with RECORDS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            ts = obj.get("ts")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                continue
            if dt < cutoff:
                continue
            if obj.get("type") == "snapshot":
                snapshots.append(obj)
            elif obj.get("type") == "error":
                errors.append(obj)

    if not snapshots and not errors:
        raise SystemExit("No data in the selected window")

    gas = [s.get("gas_util_pct") for s in snapshots if isinstance(s.get("gas_util_pct"), (int, float))]
    tpm = [s.get("txs_per_min") for s in snapshots if isinstance(s.get("txs_per_min"), (int, float))]
    net = [s.get("exchange_net_inflow_1h_eth") for s in snapshots if isinstance(s.get("exchange_net_inflow_1h_eth"), (int, float))]

    def stats(xs: List[float]) -> Dict[str, float]:
        if not xs:
            return {"min": 0.0, "max": 0.0, "avg": 0.0}
        return {"min": float(min(xs)), "max": float(max(xs)), "avg": float(sum(xs) / len(xs))}

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_hours": int(args.hours),
        "snapshots": len(snapshots),
        "errors": len(errors),
        "gas_util_pct": stats([float(x) for x in gas if x is not None]),
        "txs_per_min": stats([float(x) for x in tpm if x is not None]),
        "exchange_net_inflow_1h_eth": stats([float(x) for x in net if x is not None]),
        "large_transfers_ge_5000_total": int(sum(int(s.get("large_transfers_ge_5000", 0) or 0) for s in snapshots)),
    }

    out_path = OUT_DIR / f"eth_daily_summary_{datetime.now(timezone.utc).date().isoformat()}.json"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Print a small markdown report
    print(f"# ETH 链上监控 24h 摘要\n")
    print(f"- 生成时间（UTC）：{summary['generated_at']}")
    print(f"- 快照数：{summary['snapshots']} | 错误数：{summary['errors']}")
    print("\n## 指标概览")
    print(f"- Gas 使用率%：min={summary['gas_util_pct']['min']:.2f} max={summary['gas_util_pct']['max']:.2f} avg={summary['gas_util_pct']['avg']:.2f}")
    print(f"- 估算每分钟交易数：min={summary['txs_per_min']['min']:.2f} max={summary['txs_per_min']['max']:.2f} avg={summary['txs_per_min']['avg']:.2f}")
    print(f"- 交易所 1h 净流入（ETH）：min={summary['exchange_net_inflow_1h_eth']['min']:.2f} max={summary['exchange_net_inflow_1h_eth']['max']:.2f} avg={summary['exchange_net_inflow_1h_eth']['avg']:.2f}")
    print(f"- ≥5,000 ETH 大额转账总数（按块计数）：{summary['large_transfers_ge_5000_total']}")


if __name__ == "__main__":
    main()
