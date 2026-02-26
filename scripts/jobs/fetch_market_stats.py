#!/usr/bin/env python3
"""ARES-INTEL · Bias-aware signal generator.

Fetch Binance 24h stats, maintain rolling metrics inside sqlite/Postgres,
and emit cognitive metrics (z-score, percentile, consecutive_count).
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
import statistics
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

try:
    import psycopg  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    psycopg = None
try:
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    requests = None

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

BINANCE_ENDPOINT = "https://api.binance.com/api/v3/ticker/24hr"
DEFAULT_SYMBOLS = os.getenv("MVP_SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT").split(",")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "mvp.yaml"
TMP_DIR = PROJECT_ROOT / "tmp"

# Ensure project root is importable when running as a script.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Optional: QMD v1 checkpointing (no LLM calls; heuristic distill)
try:
    from qmd import QMDManager
except ModuleNotFoundError:  # pragma: no cover
    QMDManager = None  # type: ignore
DEFAULT_DSN = os.getenv("MVP_PG_DSN", "sqlite:///tmp/mvp.db")
ROLLING_WINDOW = int(os.getenv("MVP_ROLLING_WINDOW", "7"))
BIAS_THRESHOLD = float(os.getenv("MVP_Z_THRESHOLD", "1.5"))


@dataclass
class Snapshot:
    symbol: str
    price: float
    volume_24h: float
    volume_rank: int
    realized_vol_1h: float
    high_price: float
    low_price: float
    trade_count: int
    fetched_at: datetime
    rolling_mean_7d: float
    rolling_std_7d: float
    z_score: float
    percentile: float
    consecutive_count: int
    snapshot_id: uuid.UUID


def load_config() -> Dict[str, Any]:
    if yaml is None:
        return {}
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file missing: {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def fetch_symbol_stats(symbol: str) -> Dict[str, Any]:
    symbol = symbol.upper()
    if requests is not None:
        resp = requests.get(BINANCE_ENDPOINT, params={"symbol": symbol}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    else:
        # Fallback: stdlib-only HTTP
        import urllib.parse
        import urllib.request

        url = BINANCE_ENDPOINT + "?" + urllib.parse.urlencode({"symbol": symbol})
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
    return {
        "symbol": data["symbol"],
        "lastPrice": float(data["lastPrice"]),
        "priceChangePercent": float(data.get("priceChangePercent", 0.0)),
        "quoteVolume": float(data["quoteVolume"]),
        "highPrice": float(data["highPrice"]),
        "lowPrice": float(data["lowPrice"]),
        "count": int(data["count"]),
    }


def compute_volume_ranks(payloads: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    sorted_by_volume = sorted(payloads, key=lambda item: item["quoteVolume"], reverse=True)
    return {item["symbol"]: idx + 1 for idx, item in enumerate(sorted_by_volume)}


def connect_storage(dsn: str) -> Tuple[Any, str, Path | None]:
    if dsn.startswith("sqlite:///"):
        rel_path = dsn.replace("sqlite:///", "", 1)
        rel_path = rel_path or "tmp/mvp.db"
        abs_path = (PROJECT_ROOT / rel_path).resolve() if not rel_path.startswith("/") else Path(rel_path)
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(abs_path))
        return conn, "sqlite", abs_path
    if psycopg is None:
        raise ModuleNotFoundError("psycopg is required for Postgres DSN; install psycopg or use sqlite:/// DSN")
    conn = psycopg.connect(dsn)
    conn.autocommit = True
    return conn, "postgres", None


def ensure_tables(conn: Any, backend: str) -> None:
    schema = {
        "market_snapshots": {
            "id": "TEXT" if backend == "sqlite" else "UUID",
            "symbol": "TEXT",
            "timestamp": "TEXT" if backend == "sqlite" else "TIMESTAMPTZ",
            "price": "REAL" if backend == "sqlite" else "NUMERIC",
            "vol_24h": "REAL" if backend == "sqlite" else "NUMERIC",
            "vol_rank": "INTEGER" if backend == "sqlite" else "INT",
            "realized_vol_1h": "REAL" if backend == "sqlite" else "NUMERIC",
            "high_price": "REAL" if backend == "sqlite" else "NUMERIC",
            "low_price": "REAL" if backend == "sqlite" else "NUMERIC",
            "trade_count": "INTEGER" if backend == "sqlite" else "INT",
            "rolling_mean_7d": "REAL" if backend == "sqlite" else "NUMERIC",
            "rolling_std_7d": "REAL" if backend == "sqlite" else "NUMERIC",
            "z_score": "REAL" if backend == "sqlite" else "NUMERIC",
            "percentile": "REAL" if backend == "sqlite" else "NUMERIC",
            "consecutive_count": "INTEGER" if backend == "sqlite" else "INT",
        }
    }

    intel_schema = {
        "intel_signals": {
            "id": "TEXT" if backend == "sqlite" else "UUID",
            "market_snapshot_id": "TEXT" if backend == "sqlite" else "UUID",
            "symbol": "TEXT",
            "created_at": "TEXT" if backend == "sqlite" else "TIMESTAMPTZ",
            "metric": "TEXT",
            "current_value": "REAL" if backend == "sqlite" else "NUMERIC",
            "rolling_mean_7d": "REAL" if backend == "sqlite" else "NUMERIC",
            "rolling_std_7d": "REAL" if backend == "sqlite" else "NUMERIC",
            "z_score": "REAL" if backend == "sqlite" else "NUMERIC",
            "percentile": "REAL" if backend == "sqlite" else "NUMERIC",
            "consecutive_count": "INTEGER" if backend == "sqlite" else "INT",
            "payload": "TEXT" if backend == "sqlite" else "JSONB",
        }
    }

    decision_schema = {
        "decision_log": {
            "id": "TEXT" if backend == "sqlite" else "UUID",
            "timestamp": "TEXT" if backend == "sqlite" else "TIMESTAMPTZ",
            "market_snapshot_id": "TEXT" if backend == "sqlite" else "UUID",
            "symbol": "TEXT",
            "your_decision": "TEXT",
            "thesis": "TEXT",
            "risk_level_at_time": "TEXT",
            "outcome_24h": "TEXT",
            "outcome_72h": "TEXT"
        }
    }

    def ensure_sqlite_columns(table: str, columns: Dict[str, str]) -> None:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        existing = {row[1] for row in cur.fetchall()}
        if not existing:
            cols_sql = ",".join(f"{name} {ctype}" for name, ctype in columns.items())
            cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols_sql})")
        else:
            for name, ctype in columns.items():
                if name not in existing:
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ctype}")
        conn.commit()

    if backend == "sqlite":
        for table, columns in {**schema, **intel_schema, **decision_schema}.items():
            ensure_sqlite_columns(table, columns)
    else:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS market_snapshots (
                  id UUID PRIMARY KEY,
                  symbol TEXT,
                  timestamp TIMESTAMPTZ,
                  price NUMERIC,
                  vol_24h NUMERIC,
                  vol_rank INT,
                  realized_vol_1h NUMERIC,
                  high_price NUMERIC,
                  low_price NUMERIC,
                  trade_count INT,
                  rolling_mean_7d NUMERIC,
                  rolling_std_7d NUMERIC,
                  z_score NUMERIC,
                  percentile NUMERIC,
                  consecutive_count INT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS intel_signals (
                  id UUID PRIMARY KEY,
                  market_snapshot_id UUID,
                  symbol TEXT,
                  created_at TIMESTAMPTZ,
                  metric TEXT,
                  current_value NUMERIC,
                  rolling_mean_7d NUMERIC,
                  rolling_std_7d NUMERIC,
                  z_score NUMERIC,
                  percentile NUMERIC,
                  consecutive_count INT,
                  payload JSONB
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS decision_log (
                  id UUID PRIMARY KEY,
                  timestamp TIMESTAMPTZ,
                  market_snapshot_id UUID,
                  symbol TEXT,
                  your_decision TEXT,
                  thesis TEXT,
                  risk_level_at_time TEXT,
                  outcome_24h TEXT,
                  outcome_72h TEXT
                )
                """
            )
            for table, columns in {**schema, **intel_schema, **decision_schema}.items():
                for column, col_type in columns.items():
                    cur.execute(
                        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}"
                    )


def fetch_history(conn: Any, backend: str, symbol: str, limit: int) -> List[Dict[str, Any]]:
    if backend == "sqlite":
        cur = conn.cursor()
        cur.execute(
            "SELECT realized_vol_1h, rolling_mean_7d, rolling_std_7d, z_score, consecutive_count, price FROM market_snapshots WHERE symbol=? ORDER BY timestamp DESC LIMIT ?",
            (symbol, limit),
        )
        rows = cur.fetchall()
        return [
            {
                "realized_vol_1h": row[0],
                "rolling_mean_7d": row[1],
                "rolling_std_7d": row[2],
                "z_score": row[3],
                "consecutive_count": row[4],
                "price": row[5],
            }
            for row in rows
        ]
    else:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT realized_vol_1h, rolling_mean_7d, rolling_std_7d, z_score, consecutive_count, price FROM market_snapshots WHERE symbol=%s ORDER BY timestamp DESC LIMIT %s",
                (symbol, limit),
            )
            rows = cur.fetchall()
            return [
                {
                    "realized_vol_1h": row[0],
                    "rolling_mean_7d": row[1],
                    "rolling_std_7d": row[2],
                    "z_score": row[3],
                    "consecutive_count": row[4],
                    "price": row[5],
                }
                for row in rows
            ]


def calc_stats(current_value: float, history_values: Sequence[float]) -> Tuple[float, float, float, float]:
    window = history_values[-ROLLING_WINDOW:]
    if not window:
        return current_value, 0.0, 0.0, 0.5
    mean = statistics.fmean(window)
    std = statistics.pstdev(window) if len(window) > 1 else 0.0
    epsilon = 1e-6
    if std < epsilon:
        std = epsilon
    z = (current_value - mean) / std
    sorted_vals = sorted(window + [current_value])
    rank = sum(1 for val in sorted_vals if val <= current_value) - 1
    percentile = rank / (len(sorted_vals) - 1) if len(sorted_vals) > 1 else 0.5
    return mean, std, z, percentile


def derive_consecutive_count(prev_z: float | None, prev_count: int | None, current_z: float) -> int:
    if abs(current_z) <= BIAS_THRESHOLD:
        return 0
    if prev_z is not None and (prev_count or 0) > 0 and (prev_z * current_z) > 0 and abs(prev_z) > BIAS_THRESHOLD:
        return (prev_count or 0) + 1
    return 1


def persist_snapshot(conn: Any, backend: str, snap: Snapshot) -> None:
    if backend == "sqlite":
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO market_snapshots
            (id, symbol, timestamp, price, vol_24h, vol_rank, realized_vol_1h,
             high_price, low_price, trade_count, rolling_mean_7d, rolling_std_7d,
             z_score, percentile, consecutive_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(snap.snapshot_id),
                snap.symbol,
                snap.fetched_at.isoformat(),
                snap.price,
                snap.volume_24h,
                snap.volume_rank,
                snap.realized_vol_1h,
                snap.high_price,
                snap.low_price,
                snap.trade_count,
                snap.rolling_mean_7d,
                snap.rolling_std_7d,
                snap.z_score,
                snap.percentile,
                snap.consecutive_count,
            ),
        )
        conn.commit()
    else:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO market_snapshots
                (id, symbol, timestamp, price, vol_24h, vol_rank, realized_vol_1h,
                 high_price, low_price, trade_count, rolling_mean_7d, rolling_std_7d,
                 z_score, percentile, consecutive_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    snap.snapshot_id,
                    snap.symbol,
                    snap.fetched_at,
                    snap.price,
                    snap.volume_24h,
                    snap.volume_rank,
                    snap.realized_vol_1h,
                    snap.high_price,
                    snap.low_price,
                    snap.trade_count,
                    snap.rolling_mean_7d,
                    snap.rolling_std_7d,
                    snap.z_score,
                    snap.percentile,
                    snap.consecutive_count,
                ),
            )


def insert_signal(conn: Any, backend: str, snapshot: Snapshot, metric_payload: Dict[str, Any]) -> str:
    signal_id = uuid.uuid4()
    serialized = json.dumps(metric_payload)
    if backend == "sqlite":
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO intel_signals
            (id, market_snapshot_id, symbol, created_at, metric, current_value,
             rolling_mean_7d, rolling_std_7d, z_score, percentile, consecutive_count, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(signal_id),
                str(snapshot.snapshot_id),
                snapshot.symbol,
                datetime.now(timezone.utc).isoformat(),
                metric_payload["metric"],
                metric_payload["current_value"],
                metric_payload["rolling_mean_7d"],
                metric_payload["rolling_std_7d"],
                metric_payload["z_score"],
                metric_payload["percentile"],
                metric_payload["consecutive_count"],
                serialized,
            ),
        )
        conn.commit()
    else:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO intel_signals
                (id, market_snapshot_id, symbol, created_at, metric, current_value,
                 rolling_mean_7d, rolling_std_7d, z_score, percentile, consecutive_count, payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    signal_id,
                    snapshot.snapshot_id,
                    snapshot.symbol,
                    datetime.now(timezone.utc),
                    metric_payload["metric"],
                    metric_payload["current_value"],
                    metric_payload["rolling_mean_7d"],
                    metric_payload["rolling_std_7d"],
                    metric_payload["z_score"],
                    metric_payload["percentile"],
                    metric_payload["consecutive_count"],
                    serialized,
                ),
            )
    return str(signal_id)


def build_snapshot(symbol: str, payload: Dict[str, Any], vol_rank: int, history: List[Dict[str, Any]]) -> Snapshot:
    realized_vol = abs(payload["priceChangePercent"]) / 100.0
    values = [item["realized_vol_1h"] for item in history if item["realized_vol_1h"] is not None]
    mean, std, z, percentile = calc_stats(realized_vol, values)
    prev = history[0] if history else {"z_score": None, "consecutive_count": 0}
    consecutive = derive_consecutive_count(prev.get("z_score"), prev.get("consecutive_count"), z)
    return Snapshot(
        symbol=symbol,
        price=payload["lastPrice"],
        volume_24h=payload["quoteVolume"],
        volume_rank=vol_rank,
        realized_vol_1h=realized_vol,
        high_price=payload["highPrice"],
        low_price=payload["lowPrice"],
        trade_count=payload["count"],
        fetched_at=datetime.now(timezone.utc),
        rolling_mean_7d=mean,
        rolling_std_7d=std,
        z_score=z,
        percentile=percentile,
        consecutive_count=consecutive,
        snapshot_id=uuid.uuid4(),
    )


def format_metric(snapshot: Snapshot) -> Dict[str, Any]:
    return {
        "symbol": snapshot.symbol,
        "market_snapshot_id": str(snapshot.snapshot_id),
        "metric": "realized_vol_1h",
        "current_value": snapshot.realized_vol_1h,
        "rolling_mean_7d": snapshot.rolling_mean_7d,
        "rolling_std_7d": snapshot.rolling_std_7d,
        "z_score": snapshot.z_score,
        "percentile": snapshot.percentile,
        "consecutive_count": snapshot.consecutive_count,
        "timestamp": snapshot.fetched_at.isoformat(),
    }


def main() -> None:
    start_time = time.time()
    config = load_config()

    symbols = [sym.strip().upper() for sym in DEFAULT_SYMBOLS if sym.strip()]
    raw_payloads: List[Dict[str, Any]] = []
    errors: Dict[str, str] = {}

    for symbol in symbols:
        try:
            raw_payloads.append(fetch_symbol_stats(symbol))
        except Exception as exc:  # noqa: BLE001
            errors[symbol] = str(exc)

    if not raw_payloads:
        print("[ARES-INTEL] No successful API responses.", file=sys.stderr)
        sys.exit(1)

    vol_ranks = compute_volume_ranks(raw_payloads)
    dsn = DEFAULT_DSN
    conn, backend, db_path = connect_storage(dsn)
    ensure_tables(conn, backend)

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    outputs: List[Dict[str, Any]] = []

    for payload in raw_payloads:
        symbol = payload["symbol"].upper()
        history = fetch_history(conn, backend, symbol, ROLLING_WINDOW)
        snapshot = build_snapshot(symbol, payload, vol_ranks[symbol], history)
        persist_snapshot(conn, backend, snapshot)
        metric_payload = format_metric(snapshot)
        insert_signal(conn, backend, snapshot, metric_payload)
        outputs.append(metric_payload)

    signals_path = TMP_DIR / "intel_signals_latest.json"
    with signals_path.open("w", encoding="utf-8") as handle:
        json.dump(outputs, handle, indent=2)

    runtime = time.time() - start_time

    print("=== ARES-INTEL RUN REPORT v1.0 (Bias Edition) ===")
    print(f"Binance API success: {len(raw_payloads)} / {len(symbols)} | failures: {len(errors)}")
    if errors:
        print("Failures:")
        for symbol, message in errors.items():
            print(f"  - {symbol}: {message}")
    for entry in outputs:
        print(
            f"{entry['symbol']}: current={entry['current_value']:.4f} mean7d={entry['rolling_mean_7d']:.4f} "
            f"z={entry['z_score']:.2f} percentile={entry['percentile']:.2%} consecutive={entry['consecutive_count']}"
        )
    print(f"Signals saved: {len(outputs)} → {signals_path}")
    print(f"Storage backend: {backend} ({db_path if db_path else dsn})")
    print(f"Runtime: {runtime:.2f}s")

    # QMD v1: write a lightweight checkpoint for continuity/audit (no token spend)
    if QMDManager is not None:
        qmd = QMDManager(project_root=PROJECT_ROOT, agent_name="aresintel", thread_id="ares-intel:fetch_market_stats")
        qmd.state.update(
            {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "storage_backend": backend,
                "dsn": dsn,
                "symbols": symbols,
                "rolling_window": ROLLING_WINDOW,
                "bias_threshold": BIAS_THRESHOLD,
            }
        )
        qmd.observe(f"Binance API success {len(raw_payloads)}/{len(symbols)}; failures={len(errors)}")
        if errors:
            qmd.observe(f"Failures: {errors}")
        qmd.observe(f"Signals saved: {len(outputs)} -> {signals_path}")
        # Keep only a compact per-symbol line
        for entry in outputs:
            qmd.observe(
                f"{entry['symbol']} z={entry['z_score']:.2f} pct={entry['percentile']:.2%} cons={entry['consecutive_count']}"
            )
        qmd.end_run_checkpoint(
            goal="Fetch market stats and emit bias-aware intel signals",
            constraints=["No auto-execution (dry-run)", "Append-only snapshot + signal tables"],
            decisions=["Persist snapshot + signal for each symbol"],
            open_loops=["Review signals for regime shifts", "Tune thresholds if too noisy"],
            pointers=[str(signals_path), str(CONFIG_PATH)],
        )

        # Long-term (approved): persist stable run configuration as reusable memory.
        qmd.commit_longterm(
            type="sop",
            source="scripts/jobs/fetch_market_stats.py",
            tags=["aresintel", "intel", "config"],
            payload={
                "agent": "aresintel",
                "dsn": dsn,
                "symbols": symbols,
                "rolling_window": ROLLING_WINDOW,
                "bias_threshold": BIAS_THRESHOLD,
                "notes": "Run config snapshot for reproducibility",
            },
        )

    conn.close()


if __name__ == "__main__":
    main()
