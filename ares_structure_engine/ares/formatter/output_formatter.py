"""
ARES STRUCTURE ENGINE v1.0 — Output Formatter

Formats generated content for:
  - Twitter/X (< 280 characters)
  - Telegram (structured 8–12 lines)
"""

from ares.utils.constants import (
    TWITTER_CHAR_LIMIT,
    BRAND_TAGLINE_EN,
    BRAND_TAGLINE_CN,
    CONTENT_LABELS_EN,
    ENGINE_NAME,
)
from ares.utils.token_counter import estimate_tokens, is_within_budget
from ares.utils.logger import get_logger

log = get_logger("ares.formatter")


def format_twitter(content: dict) -> str:
    """
    Format content for Twitter/X.
    Must be under 280 characters.
    """
    ct = content["content_type"]
    label = CONTENT_LABELS_EN.get(ct, ct)
    signal = content["signal_name"].replace("_", " ").title()

    # Build compact tweet
    tweet = (
        f"📐 {content['hook_en']}\n"
        f"\n"
        f"Signal: {signal}\n"
        f"{content['metric_line_en']}\n"
        f"\n"
        f"{BRAND_TAGLINE_EN}\n"
        f"— Ares Structure Intelligence"
    )

    # Truncate if needed while keeping under limit
    if len(tweet) > TWITTER_CHAR_LIMIT:
        # Shorter version without metric line
        tweet = (
            f"📐 {content['hook_en']}\n"
            f"\n"
            f"Signal: {signal}\n"
            f"\n"
            f"{BRAND_TAGLINE_EN}\n"
            f"— Ares SI"
        )

    if len(tweet) > TWITTER_CHAR_LIMIT:
        tweet = tweet[:TWITTER_CHAR_LIMIT - 3] + "..."

    log.info(f"Twitter format: {len(tweet)} chars")
    return tweet


def format_telegram(content: dict) -> str:
    """
    Format content for Telegram.
    Structured 8–12 lines with bilingual content.
    """
    ct = content["content_type"]
    label_en = CONTENT_LABELS_EN.get(ct, ct)
    signal = content["signal_name"].replace("_", " ").title()

    lines = [
        f"━━━━━━━━━━━━━━━━━━━━",
        f"📐 ARES STRUCTURE ENGINE",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"",
        f"🔹 {content['hook_en']}",
        f"🔹 {content['hook_cn']}",
        f"",
        f"📊 {content['metric_line_en']}",
        f"📊 {content['metric_line_cn']}",
        f"",
        f"🔍 Signal: {signal}",
        f"",
        f"EN: {content['insight_en']}",
        f"",
        f"CN: {content['insight_cn']}",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"📐 {BRAND_TAGLINE_EN}",
        f"📐 {BRAND_TAGLINE_CN}",
        f"━━━━━━━━━━━━━━━━━━━━",
    ]

    telegram_text = "\n".join(lines)
    tokens = estimate_tokens(telegram_text)
    log.info(f"Telegram format: {len(lines)} lines, ~{tokens} tokens")

    return telegram_text


def format_all(content: dict) -> dict:
    """
    Format content for all platforms.

    Returns:
        {
            twitter: str,
            telegram: str,
            token_count: int,
            within_budget: bool
        }
    """
    twitter = format_twitter(content)
    telegram = format_telegram(content)

    # Combined token count (both platforms)
    combined = twitter + "\n" + telegram
    tokens = estimate_tokens(combined)

    result = {
        "twitter": twitter,
        "telegram": telegram,
        "token_count": tokens,
        "within_budget": is_within_budget(combined),
        "content_type": content["content_type"],
        "date": content["date"],
        "signal_name": content["signal_name"],
    }

    log.info(
        f"Formatted output: {tokens} tokens | "
        f"Budget: {'OK' if result['within_budget'] else 'EXCEEDED'}"
    )
    return result
