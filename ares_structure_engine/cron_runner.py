#!/usr/bin/env python3
"""
ARES STRUCTURE ENGINE v1.0 — Cron Runner

Designed to be called by cron or systemd timer once per day.
Runs the pipeline, saves output, and optionally publishes to Telegram/Twitter.

Usage:
    python cron_runner.py
    python cron_runner.py --publish    # Also publish to Telegram + Twitter

Cron example (daily at 08:00 UTC):
    0 8 * * * cd /opt/ares_structure_engine && /usr/bin/python3 cron_runner.py --publish >> /var/log/ares.log 2>&1
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from ares.engine import run_pipeline, save_output, save_formatted_text
from ares.utils.logger import get_logger

log = get_logger("ares.cron")


def main():
    parser = argparse.ArgumentParser(description="ARES Cron Runner")
    parser.add_argument("--publish", action="store_true", help="Publish to Telegram + Twitter")
    args = parser.parse_args()

    log.info("Cron runner started")

    # Run pipeline (auto-detect day)
    output = run_pipeline()

    # Save files
    save_output(output)
    save_formatted_text(output)

    log.info(
        f"Generated: {output['schedule']['content_label']} | "
        f"Signal: {output['signal']['name']} | "
        f"Tokens: {output['meta']['token_count']}"
    )

    # Publish if requested
    if args.publish:
        try:
            from ares.integrations.telegram_bot import publish_daily_content as tg_publish
            tg_result = tg_publish(output)
            log.info(f"Telegram publish: {tg_result.get('ok', False)}")
        except Exception as e:
            log.error(f"Telegram publish failed: {e}")

        try:
            from ares.integrations.twitter_poster import publish_daily_content as tw_publish
            tw_result = tw_publish(output)
            log.info(f"Twitter publish: {tw_result.get('ok', False)}")
        except Exception as e:
            log.error(f"Twitter publish failed: {e}")

    log.info("Cron runner complete")


if __name__ == "__main__":
    main()
