"""
ARES STRUCTURE ENGINE v1.0 — Core Pipeline Orchestrator

Orchestrates the full pipeline:
  Data → Parse → Interpret → Generate → Format → Output
"""

import json
from datetime import datetime
from pathlib import Path

from ares.data.provider import fetch_data
from ares.parser.metric_parser import parse_metrics
from ares.rules.interpreter import interpret
from ares.generator.content_generator import generate_content
from ares.formatter.output_formatter import format_all
from ares.scheduler.day_scheduler import get_today_info
from ares.utils.constants import OUTPUT_DIR, ENGINE_NAME, ENGINE_VERSION
from ares.utils.logger import get_logger

log = get_logger("ares.engine")


def run_pipeline(force_day: int = None, date_override: str = None) -> dict:
    """
    Execute the full ARES pipeline for a single day.

    Args:
        force_day: Override day of week (1-7). None = auto-detect.
        date_override: Override date string (YYYY-MM-DD). None = today.

    Returns:
        Complete output dict with all formatted content.
    """
    log.info(f"{'='*50}")
    log.info(f"{ENGINE_NAME} v{ENGINE_VERSION} — Pipeline Start")
    log.info(f"{'='*50}")

    # ── Step 1: Determine content type ───────────────────────
    schedule = get_today_info(force_day=force_day)
    content_type = schedule["content_type"]
    date_str = date_override or schedule["date_str"]

    log.info(f"Content type: {schedule['content_label']} ({content_type})")
    log.info(f"Date: {date_str}")

    # ── Step 2: Fetch data ───────────────────────────────────
    raw_data = fetch_data(content_type, date_str)
    log.info(f"Data fetched: {len(raw_data)} fields")

    # ── Step 3: Parse metrics ────────────────────────────────
    parsed = parse_metrics(raw_data)
    log.info(f"Parsed signal: {parsed['structural_signal']}")

    # ── Step 4: Interpret structure ──────────────────────────
    interpreted = interpret(parsed)
    log.info(f"Interpretation complete")

    # ── Step 5: Generate bilingual content ───────────────────
    content = generate_content(interpreted)
    log.info(f"Content generated")

    # ── Step 6: Format for platforms ─────────────────────────
    formatted = format_all(content)
    log.info(f"Formatting complete | Tokens: {formatted['token_count']}")

    # ── Assemble final output ────────────────────────────────
    output = {
        "engine": f"{ENGINE_NAME} v{ENGINE_VERSION}",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "schedule": schedule,
        "signal": {
            "name": formatted["signal_name"],
            "leverage_shift": interpreted["leverage_shift"],
            "liquidity_state": interpreted["liquidity_state"],
        },
        "content": content,
        "formatted": {
            "twitter": formatted["twitter"],
            "telegram": formatted["telegram"],
        },
        "meta": {
            "token_count": formatted["token_count"],
            "within_budget": formatted["within_budget"],
            "twitter_chars": len(formatted["twitter"]),
        },
    }

    log.info(f"{'='*50}")
    log.info(f"Pipeline complete | Signal: {formatted['signal_name']}")
    log.info(f"{'='*50}")

    return output


def save_output(output: dict, directory: Path = None) -> Path:
    """Save pipeline output to JSON file."""
    if directory is None:
        directory = OUTPUT_DIR
    directory.mkdir(parents=True, exist_ok=True)

    date_str = output["schedule"]["date_str"]
    content_type = output["schedule"]["content_type"]
    filename = f"ares_{date_str}_{content_type}.json"
    filepath = directory / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    log.info(f"Output saved: {filepath}")
    return filepath


def save_formatted_text(output: dict, directory: Path = None) -> dict:
    """Save formatted text outputs (Twitter + Telegram) to separate files."""
    if directory is None:
        directory = OUTPUT_DIR
    directory.mkdir(parents=True, exist_ok=True)

    date_str = output["schedule"]["date_str"]
    content_type = output["schedule"]["content_type"]
    paths = {}

    # Twitter
    tw_path = directory / f"ares_{date_str}_{content_type}_twitter.txt"
    with open(tw_path, "w", encoding="utf-8") as f:
        f.write(output["formatted"]["twitter"])
    paths["twitter"] = tw_path

    # Telegram
    tg_path = directory / f"ares_{date_str}_{content_type}_telegram.txt"
    with open(tg_path, "w", encoding="utf-8") as f:
        f.write(output["formatted"]["telegram"])
    paths["telegram"] = tg_path

    log.info(f"Text outputs saved: {tw_path.name}, {tg_path.name}")
    return paths
