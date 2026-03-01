#!/usr/bin/env python3
"""
ARES STRUCTURE ENGINE v1.0 — Main Entry Point

Usage:
    python main.py                    # Auto-detect day, run pipeline
    python main.py --day 3            # Force day 3 (Liquidation Map)
    python main.py --day 1 --date 2026-02-27
    python main.py --all              # Generate all 7 days
    python main.py --schedule         # Print weekly schedule
    python main.py --demo             # Run demo for all 7 days with output
"""

import argparse
import sys
import os
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from ares.engine import run_pipeline, save_output, save_formatted_text
from ares.scheduler.day_scheduler import get_today_info, get_full_week_schedule
from ares.utils.constants import ENGINE_NAME, ENGINE_VERSION
from ares.utils.logger import get_logger

log = get_logger("ares.main")


def print_banner():
    """Print the engine banner."""
    banner = f"""
╔══════════════════════════════════════════════════╗
║          {ENGINE_NAME} v{ENGINE_VERSION}          ║
║                                                  ║
║   Automated Bilingual Market Structure Engine    ║
║   We read structure, not candles.                ║
║   我们读结构，不读K线。                            ║
╚══════════════════════════════════════════════════╝
"""
    print(banner)


def print_schedule():
    """Print the 7-day content rotation schedule."""
    schedule = get_full_week_schedule()
    print(f"\n{'─'*50}")
    print(f"  7-Day Content Rotation Schedule")
    print(f"{'─'*50}")
    for entry in schedule:
        print(f"  Day {entry['day_number']} ({entry['day_name']:>9s}): {entry['content_label']}")
    print(f"{'─'*50}\n")


def run_single(day: int = None, date: str = None, quiet: bool = False):
    """Run pipeline for a single day."""
    output = run_pipeline(force_day=day, date_override=date)

    # Save outputs
    json_path = save_output(output)
    text_paths = save_formatted_text(output)

    if not quiet:
        print(f"\n{'━'*50}")
        print(f"  Day {output['schedule']['day_number']}: "
              f"{output['schedule']['content_label']}")
        print(f"  Signal: {output['signal']['name']}")
        print(f"  Tokens: {output['meta']['token_count']} | "
              f"Budget: {'✓' if output['meta']['within_budget'] else '✗'}")
        print(f"{'━'*50}")
        print(f"\n── Twitter ({output['meta']['twitter_chars']} chars) ──")
        print(output["formatted"]["twitter"])
        print(f"\n── Telegram ──")
        print(output["formatted"]["telegram"])
        print(f"\n  Saved: {json_path.name}")

    return output


def run_all(date: str = None):
    """Run pipeline for all 7 days."""
    results = []
    for day in range(1, 8):
        output = run_single(day=day, date=date or "2026-02-27", quiet=True)
        results.append(output)
        print(f"  ✓ Day {day}: {output['schedule']['content_label']} → "
              f"{output['signal']['name']} ({output['meta']['token_count']} tokens)")
    return results


def run_demo():
    """Run full demo with output for all 7 days."""
    print_banner()
    print_schedule()

    print(f"\n{'═'*60}")
    print(f"  GENERATING ALL 7 DAYS — DEMO MODE")
    print(f"{'═'*60}\n")

    for day in range(1, 8):
        output = run_single(day=day, date="2026-02-27")
        print(f"\n{'═'*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description=f"{ENGINE_NAME} v{ENGINE_VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--day", type=int, choices=range(1, 8), metavar="N",
        help="Force day of week (1=Mon, 7=Sun)",
    )
    parser.add_argument(
        "--date", type=str, metavar="YYYY-MM-DD",
        help="Override date string",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Generate content for all 7 days",
    )
    parser.add_argument(
        "--schedule", action="store_true",
        help="Print weekly content schedule",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run full demo for all 7 days with output",
    )

    args = parser.parse_args()

    print_banner()

    if args.schedule:
        print_schedule()
    elif args.demo:
        run_demo()
    elif args.all:
        print(f"\n  Generating all 7 days...\n")
        run_all(date=args.date)
    else:
        run_single(day=args.day, date=args.date)


if __name__ == "__main__":
    main()
