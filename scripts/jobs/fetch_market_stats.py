#!/usr/bin/env python3
"""MVP job: pull Binance 24h stats and persist to Postgres.
Currently acts as a stub that prints payload; DB wiring to be added.
"""

from __future__ import annotations

import os
import sys
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests

BINANCE_ENDPOINT = "https://api.binance.com/api/v3/ticker/24hr"
DEFAULT_SYMBOLS = os.getenv("MVP_SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT").split(",")


def fetch_symbol_stats(symbol: str) -> Dict[str, Any]:
    resp = requests.get(BINANCE_ENDPOINT, params={"symbol": symbol.upper()}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "symbol": data["symbol"],
        "price": float(data["lastPrice"]),
        "volume_24h": float(data["quoteVolume"]),
        "high_price": float(data["highPrice"]),
        "low_price": float(data["lowPrice"]),
        "count": int(data["count"]),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    payloads: List[Dict[str, Any]] = []
    for symbol in DEFAULT_SYMBOLS:
        symbol = symbol.strip()
        if not symbol:
            continue
        try:
            payloads.append(fetch_symbol_stats(symbol))
        except Exception as exc:  # noqa: BLE001
            print(f"[fetch] failed for {symbol}: {exc}", file=sys.stderr)
            continue
        time.sleep(0.2)

    print(json.dumps(payloads, indent=2))
    print("[fetch] TODO: persist payloads into Postgres (see docs/mvp-signal-loop.md)")


if __name__ == "__main__":
    main()
