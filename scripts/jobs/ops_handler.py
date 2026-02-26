#!/usr/bin/env python3
"""ARES-OPS · Cognitive bias corrector (dry-run).

Reads cognitive metrics JSON and maps them to risk regimes, bias warnings,
and decision logs. No external transports yet; outputs structured JSON + log.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    # Config is currently reserved for future use; allow running without PyYAML
    yaml = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "mvp.yaml"
LOG_PATH = PROJECT_ROOT / "logs" / "ops_handler.log"

# Ensure project root is importable when running as a script.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Optional: QMD v1 checkpointing (no LLM calls; heuristic distill)
try:
    from qmd import QMDManager
except ModuleNotFoundError:  # pragma: no cover
    QMDManager = None  # type: ignore
DEFAULT_DSN = os.getenv("MVP_PG_DSN", "sqlite:///tmp/mvp.db")
BIAS_THRESHOLD = float(os.getenv("MVP_Z_THRESHOLD", "1.5"))


@dataclass
class Signal:
    symbol: str
    snapshot_id: str
    metric: str
    current_value: float
    rolling_mean_7d: float
    rolling_std_7d: float
    z_score: float
    percentile: float
    consecutive_count: int
    timestamp: str


@dataclass
class DecisionInput:
    decision: str
    thesis: str


RISK_MAP = (
    (1.0, "low"),
    (1.5, "medium"),
    (2.0, "elevated"),
    (float("inf"), "extreme"),
)

REGIME_MAP = {
    "low": "noise",
    "medium": "transitional",
    "elevated": "regime_shift",
    "extreme": "regime_shift",
}

ACTION_MAP = {
    "low": "observe",
    "medium": "observe",
    "elevated": "reduce leverage",
    "extreme": "reassess thesis",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ARES-OPS bias corrector (dry-run)")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path, default=None, help="JSON metrics from ARES-INTEL")
    parser.add_argument("--log", action="store_true")
    parser.add_argument("--decision", type=str, default=None, help="Manual decision text for elevated/extreme cases")
    parser.add_argument("--thesis", type=str, default=None, help="Thesis / rationale text")
    return parser.parse_args()


def load_config(path: Path) -> Dict[str, Any]:
    if yaml is None:
        return {}
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_signals(input_path: Path | None) -> List[Signal]:
    if input_path is None:
        demo = {
            "symbol": "BTCUSDT",
            "snapshot_id": str(uuid.uuid4()),
            "metric": "realized_vol_1h",
            "current_value": 0.05,
            "rolling_mean_7d": 0.02,
            "rolling_std_7d": 0.01,
            "z_score": 3.0,
            "percentile": 0.95,
            "consecutive_count": 2,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return [Signal(**demo)]
    with input_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        payload = [payload]
    signals: List[Signal] = []
    for item in payload:
        signals.append(Signal(
            symbol=item["symbol"],
            snapshot_id=item["market_snapshot_id"],
            metric=item["metric"],
            current_value=float(item["current_value"]),
            rolling_mean_7d=float(item.get("rolling_mean_7d", 0.0) or 0.0),
            rolling_std_7d=float(item.get("rolling_std_7d", 0.0) or 0.0),
            z_score=float(item.get("z_score", 0.0) or 0.0),
            percentile=float(item.get("percentile", 0.0) or 0.0),
            consecutive_count=int(item.get("consecutive_count", 0) or 0),
            timestamp=item.get("timestamp", datetime.now(timezone.utc).isoformat()),
        ))
    return signals


def map_risk_level(z_score: float) -> str:
    magnitude = abs(z_score)
    for threshold, label in RISK_MAP:
        if magnitude < threshold:
            return label
    return "extreme"


def infer_bias(z_score: float, consecutive_count: int) -> str:
    magnitude = abs(z_score)
    if magnitude >= 2.0:
        return "overconfidence"
    if consecutive_count >= 3 and magnitude >= BIAS_THRESHOLD:
        return "recency_bias"
    return "none"


def connect_storage(dsn: str) -> Tuple[Any, str, Path | None]:
    if dsn.startswith("sqlite:///"):
        rel_path = dsn.replace("sqlite:///", "", 1) or "tmp/mvp.db"
        abs_path = (PROJECT_ROOT / rel_path).resolve() if not rel_path.startswith("/") else Path(rel_path)
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(abs_path))
        return conn, "sqlite", abs_path
    conn = psycopg.connect(dsn)
    conn.autocommit = True
    return conn, "postgres", None


def ensure_decision_table(conn: Any, backend: str) -> None:
    if backend == "sqlite":
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS decision_log (
              id TEXT PRIMARY KEY,
              timestamp TEXT,
              market_snapshot_id TEXT,
              symbol TEXT,
              your_decision TEXT,
              thesis TEXT,
              risk_level_at_time TEXT,
              outcome_24h TEXT,
              outcome_72h TEXT
            )
            """
        )
        conn.commit()
    else:
        with conn.cursor() as cur:
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


def insert_decision(conn: Any, backend: str, snapshot_id: str, symbol: str, risk_level: str, decision: DecisionInput) -> str:
    record_id = uuid.uuid4()
    now = datetime.now(timezone.utc).isoformat() if backend == "sqlite" else datetime.now(timezone.utc)
    if backend == "sqlite":
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO decision_log
            (id, timestamp, market_snapshot_id, symbol, your_decision, thesis, risk_level_at_time, outcome_24h, outcome_72h)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(record_id),
                now,
                snapshot_id,
                symbol,
                decision.decision,
                decision.thesis,
                risk_level,
                None,
                None,
            ),
        )
        conn.commit()
    else:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO decision_log
                (id, timestamp, market_snapshot_id, symbol, your_decision, thesis, risk_level_at_time, outcome_24h, outcome_72h)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    record_id,
                    now,
                    uuid.UUID(snapshot_id),
                    symbol,
                    decision.decision,
                    decision.thesis,
                    risk_level,
                    None,
                    None,
                ),
            )
    return str(record_id)


def evaluate_signal(signal: Signal) -> Dict[str, Any]:
    risk_level = map_risk_level(signal.z_score)
    regime_type = REGIME_MAP[risk_level]
    bias_risk = infer_bias(signal.z_score, signal.consecutive_count)
    suggested_action = ACTION_MAP[risk_level]
    return {
        "symbol": signal.symbol,
        "market_snapshot_id": signal.snapshot_id,
        "metric": signal.metric,
        "z_score": signal.z_score,
        "risk_level": risk_level,
        "regime_type": regime_type,
        "bias_risk": bias_risk,
        "percentile": signal.percentile,
        "consecutive_count": signal.consecutive_count,
        "suggested_action": suggested_action,
        "timestamp": signal.timestamp,
    }


def prompt_decision_if_needed(risk_level: str, args: argparse.Namespace) -> DecisionInput | None:
    if risk_level not in {"elevated", "extreme"}:
        return None
    decision_text = args.decision or "[PENDING_DECISION]"
    thesis_text = args.thesis or "[PENDING_THESIS]"
    return DecisionInput(decision=decision_text, thesis=thesis_text)


def write_log(entries: List[Dict[str, Any]]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] ops_handler run\n")
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    config = load_config(args.config)  # reserved for future use
    signals = load_signals(args.input)

    evaluated: List[Dict[str, Any]] = []
    conn, backend, _ = connect_storage(DEFAULT_DSN)
    ensure_decision_table(conn, backend)

    for signal in signals:
        result = evaluate_signal(signal)
        decision_input = prompt_decision_if_needed(result["risk_level"], args)
        if decision_input:
            decision_id = insert_decision(conn, backend, result["market_snapshot_id"], signal.symbol, result["risk_level"], decision_input)
            result["decision_log_id"] = decision_id
            result["your_decision"] = decision_input.decision
            result["thesis"] = decision_input.thesis
        evaluated.append(result)

    print(json.dumps(evaluated, indent=2, ensure_ascii=False))
    if args.log:
        write_log(evaluated)
        print(f"[ops_handler] appended {len(evaluated)} entries to {LOG_PATH}")

    # QMD v1: write a lightweight checkpoint for continuity/audit (no token spend)
    if QMDManager is not None:
        qmd = QMDManager(project_root=PROJECT_ROOT, agent_name="aresops", thread_id="ares-ops:ops_handler")
        qmd.state.update(
            {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "config_path": str(args.config),
                "dsn": DEFAULT_DSN,
                "signals_input": str(args.input) if args.input else None,
            }
        )
        qmd.observe(f"Evaluated signals: {len(signals)}")
        elevated = [r for r in evaluated if r.get('risk_level') in {'elevated','extreme'}]
        qmd.observe(f"Elevated/extreme count: {len(elevated)}")
        if elevated:
            for r in elevated[:10]:
                qmd.observe(f"{r.get('symbol')} risk={r.get('risk_level')} bias={r.get('bias_warning')} action={r.get('suggested_action')}")
        qmd.end_run_checkpoint(
            goal="Evaluate intel signals and map to risk regimes / actions",
            constraints=["No auto-execution without approval", "Log decisions for elevated/extreme"],
            decisions=["Insert decision_log row when manual decision provided"],
            open_loops=["Add transport/notification when auto_execute approved", "Backtest regime mapping"],
            pointers=[str(LOG_PATH), str(args.config)],
        )

        # Long-term (approved): persist stable regime/action maps as reusable SOP.
        qmd.commit_longterm(
            type="sop",
            source="scripts/jobs/ops_handler.py",
            tags=["aresops", "ops", "risk_map"],
            payload={
                "agent": "aresops",
                "risk_map": list(RISK_MAP),
                "regime_map": REGIME_MAP,
                "action_map": ACTION_MAP,
                "bias_threshold": BIAS_THRESHOLD,
                "notes": "Risk/regime/action mapping for consistent ops behavior",
            },
        )

    conn.close()


if __name__ == "__main__":
    main()
