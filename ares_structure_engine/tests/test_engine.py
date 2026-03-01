#!/usr/bin/env python3
"""
ARES STRUCTURE ENGINE v1.0 — Test Suite

Run: python -m pytest tests/ -v
  or: python tests/test_engine.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ares.data.mock_provider import fetch_data
from ares.parser.metric_parser import parse_metrics
from ares.rules.interpreter import interpret
from ares.generator.content_generator import generate_content
from ares.formatter.output_formatter import format_all, format_twitter
from ares.scheduler.day_scheduler import get_today_info, get_full_week_schedule
from ares.engine import run_pipeline
from ares.utils.token_counter import estimate_tokens
from ares.utils.constants import CONTENT_SCHEDULE, TWITTER_CHAR_LIMIT


def test_all_content_types():
    """Test that all 7 content types produce valid output."""
    print("\n── Test: All Content Types ──")
    for day in range(1, 8):
        ct = CONTENT_SCHEDULE[day]
        data = fetch_data(ct, "2026-02-27")
        assert data["content_type"] == ct, f"Content type mismatch: {ct}"
        parsed = parse_metrics(data)
        assert "structural_signal" in parsed, f"Missing signal for {ct}"
        interpreted = interpret(parsed)
        assert "interpretation_en" in interpreted, f"Missing EN interpretation for {ct}"
        assert "interpretation_cn" in interpreted, f"Missing CN interpretation for {ct}"
        content = generate_content(interpreted)
        assert "hook_en" in content, f"Missing hook_en for {ct}"
        formatted = format_all(content)
        assert "twitter" in formatted, f"Missing twitter for {ct}"
        assert "telegram" in formatted, f"Missing telegram for {ct}"
        print(f"  ✓ Day {day}: {ct} → {parsed['structural_signal']}")
    print("  All content types passed.")


def test_twitter_char_limit():
    """Test that all Twitter outputs are under 280 characters."""
    print("\n── Test: Twitter Character Limit ──")
    for day in range(1, 8):
        ct = CONTENT_SCHEDULE[day]
        data = fetch_data(ct, "2026-02-27")
        parsed = parse_metrics(data)
        interpreted = interpret(parsed)
        content = generate_content(interpreted)
        formatted = format_all(content)
        tweet = formatted["twitter"]
        assert len(tweet) <= TWITTER_CHAR_LIMIT, (
            f"Day {day} tweet too long: {len(tweet)} chars"
        )
        print(f"  ✓ Day {day}: {len(tweet)} chars")
    print("  All tweets within limit.")


def test_token_budget():
    """Test that all outputs stay within 800 token budget."""
    print("\n── Test: Token Budget ──")
    for day in range(1, 8):
        ct = CONTENT_SCHEDULE[day]
        data = fetch_data(ct, "2026-02-27")
        parsed = parse_metrics(data)
        interpreted = interpret(parsed)
        content = generate_content(interpreted)
        formatted = format_all(content)
        assert formatted["within_budget"], (
            f"Day {day} exceeds budget: {formatted['token_count']} tokens"
        )
        print(f"  ✓ Day {day}: {formatted['token_count']} tokens")
    print("  All within budget.")


def test_scheduler():
    """Test scheduler for all 7 days."""
    print("\n── Test: Scheduler ──")
    for day in range(1, 8):
        info = get_today_info(force_day=day)
        assert info["day_number"] == day
        assert info["content_type"] == CONTENT_SCHEDULE[day]
        print(f"  ✓ Day {day}: {info['content_label']}")
    print("  Scheduler passed.")


def test_full_pipeline():
    """Test full pipeline execution for all 7 days."""
    print("\n── Test: Full Pipeline ──")
    for day in range(1, 8):
        output = run_pipeline(force_day=day, date_override="2026-02-27")
        assert output["meta"]["within_budget"], f"Day {day} budget exceeded"
        assert output["meta"]["twitter_chars"] <= TWITTER_CHAR_LIMIT
        assert output["signal"]["name"] is not None
        print(f"  ✓ Day {day}: {output['schedule']['content_label']} → "
              f"{output['signal']['name']} ({output['meta']['token_count']} tokens)")
    print("  Full pipeline passed.")


def test_deterministic_mock():
    """Test that mock data is deterministic for same date."""
    print("\n── Test: Deterministic Mock ──")
    for ct in CONTENT_SCHEDULE.values():
        d1 = fetch_data(ct, "2026-02-27")
        d2 = fetch_data(ct, "2026-02-27")
        assert d1 == d2, f"Non-deterministic mock data for {ct}"
        print(f"  ✓ {ct}: deterministic")
    print("  Deterministic mock passed.")


def test_no_forbidden_words():
    """Test that outputs contain no forbidden hype language."""
    print("\n── Test: No Forbidden Words ──")
    forbidden = ["bullish", "bearish", "moon", "dump", "pump", "prediction",
                 "forecast", "target", "will reach", "going to"]
    for day in range(1, 8):
        output = run_pipeline(force_day=day, date_override="2026-02-27")
        combined = (
            output["formatted"]["twitter"] +
            output["formatted"]["telegram"]
        ).lower()
        for word in forbidden:
            assert word not in combined, (
                f"Day {day} contains forbidden word: '{word}'"
            )
        print(f"  ✓ Day {day}: clean")
    print("  No forbidden words found.")


if __name__ == "__main__":
    test_all_content_types()
    test_twitter_char_limit()
    test_token_budget()
    test_scheduler()
    test_full_pipeline()
    test_deterministic_mock()
    test_no_forbidden_words()
    print(f"\n{'═'*50}")
    print(f"  ALL TESTS PASSED ✓")
    print(f"{'═'*50}")
