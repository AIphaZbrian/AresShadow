"""
ARES STRUCTURE ENGINE v1.0 — Constants & Configuration
"""

import os
from pathlib import Path

# ── Engine Identity ──────────────────────────────────────────
ENGINE_NAME = "ARES STRUCTURE ENGINE"
ENGINE_VERSION = "1.0"
BRAND_IDENTITY = "Ares Structure Intelligence"
BRAND_TAGLINE_EN = "We read structure, not candles."
BRAND_TAGLINE_CN = "我们读结构，不读K线。"

# ── Content Type Rotation (1-indexed, Monday = 1) ───────────
CONTENT_SCHEDULE = {
    1: "open_interest_funding",
    2: "etf_flow",
    3: "liquidation_map",
    4: "whale_movement",
    5: "stablecoin_supply",
    6: "orderbook_void",
    7: "weekly_summary",
}

CONTENT_LABELS_EN = {
    "open_interest_funding": "Open Interest + Funding",
    "etf_flow": "ETF Flow",
    "liquidation_map": "Liquidation Map",
    "whale_movement": "Whale Movement",
    "stablecoin_supply": "Stablecoin Supply",
    "orderbook_void": "Orderbook Void",
    "weekly_summary": "Weekly Summary",
}

CONTENT_LABELS_CN = {
    "open_interest_funding": "持仓量 + 资金费率",
    "etf_flow": "ETF 资金流",
    "liquidation_map": "清算地图",
    "whale_movement": "巨鲸动向",
    "stablecoin_supply": "稳定币供应",
    "orderbook_void": "订单簿空白区",
    "weekly_summary": "周度总结",
}

# ── Token Budget ─────────────────────────────────────────────
MAX_TOKENS_PER_DAY = int(os.getenv("MAX_TOKENS_PER_DAY", "800"))

# ── Twitter Character Limit ──────────────────────────────────
TWITTER_CHAR_LIMIT = 280

# ── Paths ────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(PROJECT_ROOT / "outputs")))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Data Mode ────────────────────────────────────────────────
DATA_MODE = os.getenv("DATA_MODE", "mock")

# ── Timezone ─────────────────────────────────────────────────
TIMEZONE = os.getenv("TIMEZONE", "UTC")
