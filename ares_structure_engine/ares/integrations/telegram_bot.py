"""
ARES STRUCTURE ENGINE v1.0 — Telegram Bot Integration

Sends formatted content to a Telegram channel via Bot API.
Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID in environment.
"""

import os
import json
from urllib.request import Request, urlopen
from urllib.error import URLError

from ares.utils.logger import get_logger

log = get_logger("ares.telegram")

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"


def send_telegram_message(text: str, parse_mode: str = "HTML") -> dict:
    """
    Send a message to the configured Telegram channel.

    Args:
        text: Message text to send.
        parse_mode: Telegram parse mode (HTML or Markdown).

    Returns:
        Telegram API response dict.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "")

    if not token or not channel_id:
        log.warning("Telegram credentials not configured. Skipping send.")
        return {"ok": False, "error": "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID"}

    url = f"{TELEGRAM_API_BASE.format(token=token)}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = Request(url, data=data, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            log.info(f"Telegram message sent: {result.get('ok', False)}")
            return result
    except URLError as e:
        log.error(f"Telegram send failed: {e}")
        return {"ok": False, "error": str(e)}


def publish_daily_content(output: dict) -> dict:
    """
    Publish the daily ARES output to Telegram.

    Args:
        output: Full pipeline output dict.

    Returns:
        Telegram API response.
    """
    telegram_text = output.get("formatted", {}).get("telegram", "")
    if not telegram_text:
        log.warning("No Telegram content to publish.")
        return {"ok": False, "error": "Empty content"}

    return send_telegram_message(telegram_text, parse_mode="HTML")
