#!/usr/bin/env python3
"""Run ARES STRUCTURE ENGINE inside OpenClaw workspace.

- Produces latest JSON + Telegram text artifacts.
- Does NOT directly send Telegram via Bot API (OpenClaw handles messaging/audit).

Env:
  DATA_MODE=mock|live (default mock)
  FORCE_DAY=1..7 (optional)
  TIMEZONE=UTC (engine default)

Outputs:
  tmp/ares_structure_latest.json
  tmp/ares_structure_latest_telegram.txt
  tmp/ares_structure_latest_twitter.txt
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENGINE_ROOT = PROJECT_ROOT / "ares_structure_engine"
OUT_JSON = PROJECT_ROOT / "tmp" / "ares_structure_latest.json"
OUT_TG = PROJECT_ROOT / "tmp" / "ares_structure_latest_telegram.txt"
OUT_X = PROJECT_ROOT / "tmp" / "ares_structure_latest_twitter.txt"


def main() -> None:
    if not ENGINE_ROOT.exists():
        raise SystemExit(f"Missing engine at {ENGINE_ROOT}")

    # Ensure engine package import path
    sys.path.insert(0, str(ENGINE_ROOT))

    from ares.engine import run_pipeline  # type: ignore

    force_day = os.getenv("FORCE_DAY")
    force_day_i = int(force_day) if force_day and force_day.isdigit() else None

    output = run_pipeline(force_day=force_day_i)

    PROJECT_ROOT.joinpath("tmp").mkdir(parents=True, exist_ok=True)

    OUT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_TG.write_text(output.get("formatted", {}).get("telegram", ""), encoding="utf-8")
    OUT_X.write_text(output.get("formatted", {}).get("twitter", ""), encoding="utf-8")

    print(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "engine": output.get("engine"),
                "content_type": output.get("schedule", {}).get("content_type"),
                "signal": output.get("signal", {}).get("name"),
                "token_count": output.get("meta", {}).get("token_count"),
                "within_budget": output.get("meta", {}).get("within_budget"),
                "artifacts": {
                    "json": str(OUT_JSON),
                    "telegram": str(OUT_TG),
                    "twitter": str(OUT_X),
                },
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
