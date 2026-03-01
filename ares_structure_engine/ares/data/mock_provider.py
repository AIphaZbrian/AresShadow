"""
ARES STRUCTURE ENGINE v1.0 — Mock Data Provider

Generates realistic mock market structure data for all 7 content types.
Each function returns a normalized dictionary of metrics.
"""

import random
import hashlib
from datetime import datetime, timedelta


def _seed_from_date(date_str: str, salt: str = "") -> None:
    """Deterministic seed from date string for reproducible mock data."""
    h = int(hashlib.md5((date_str + salt).encode()).hexdigest(), 16)
    random.seed(h % (2**32))


def _pct(low: float = -15.0, high: float = 15.0) -> float:
    return round(random.uniform(low, high), 2)


def _val(low: float = 0.0, high: float = 100.0) -> float:
    return round(random.uniform(low, high), 2)


def fetch_open_interest_funding(date_str: str) -> dict:
    """Open Interest + Funding Rate metrics."""
    _seed_from_date(date_str, "oi")
    return {
        "content_type": "open_interest_funding",
        "date": date_str,
        "btc_oi_change_pct": _pct(-12, 12),
        "eth_oi_change_pct": _pct(-15, 15),
        "btc_oi_total_b": round(random.uniform(14, 22), 2),
        "eth_oi_total_b": round(random.uniform(6, 12), 2),
        "btc_funding_rate": round(random.uniform(-0.03, 0.06), 4),
        "eth_funding_rate": round(random.uniform(-0.04, 0.07), 4),
        "funding_trend": random.choice(["rising", "falling", "neutral"]),
        "oi_trend": random.choice(["expanding", "contracting", "flat"]),
        "price_change_pct": _pct(-5, 5),
    }


def fetch_etf_flow(date_str: str) -> dict:
    """ETF Flow metrics."""
    _seed_from_date(date_str, "etf")
    net_flow = round(random.uniform(-500, 800), 1)
    return {
        "content_type": "etf_flow",
        "date": date_str,
        "btc_etf_net_flow_m": net_flow,
        "eth_etf_net_flow_m": round(random.uniform(-200, 300), 1),
        "btc_etf_cumulative_b": round(random.uniform(15, 40), 2),
        "flow_direction": "inflow" if net_flow > 0 else "outflow",
        "consecutive_days": random.randint(1, 12),
        "price_change_pct": _pct(-5, 5),
        "volume_change_pct": _pct(-20, 30),
    }


def fetch_liquidation_map(date_str: str) -> dict:
    """Liquidation Map metrics."""
    _seed_from_date(date_str, "liq")
    long_liq = round(random.uniform(50, 600), 1)
    short_liq = round(random.uniform(50, 600), 1)
    return {
        "content_type": "liquidation_map",
        "date": date_str,
        "long_liquidations_m": long_liq,
        "short_liquidations_m": short_liq,
        "total_liquidations_m": round(long_liq + short_liq, 1),
        "dominant_side": "long" if long_liq > short_liq else "short",
        "liq_ratio": round(long_liq / max(short_liq, 0.1), 2),
        "btc_largest_cluster_price": round(random.uniform(55000, 105000), 0),
        "cluster_distance_pct": _pct(2, 15),
        "leverage_state": random.choice(["overleveraged", "moderate", "deleveraged"]),
    }


def fetch_whale_movement(date_str: str) -> dict:
    """Whale Movement metrics."""
    _seed_from_date(date_str, "whale")
    exchange_inflow = round(random.uniform(500, 8000), 0)
    exchange_outflow = round(random.uniform(500, 8000), 0)
    return {
        "content_type": "whale_movement",
        "date": date_str,
        "btc_exchange_inflow": exchange_inflow,
        "btc_exchange_outflow": exchange_outflow,
        "net_flow_btc": round(exchange_inflow - exchange_outflow, 0),
        "flow_direction": "to_exchange" if exchange_inflow > exchange_outflow else "to_wallet",
        "large_txns_24h": random.randint(5, 80),
        "whale_accumulation_score": _val(0, 100),
        "dormant_coins_moved": random.choice([True, False]),
        "dormant_age_years": round(random.uniform(1, 8), 1) if random.random() > 0.5 else 0,
    }


def fetch_stablecoin_supply(date_str: str) -> dict:
    """Stablecoin Supply metrics."""
    _seed_from_date(date_str, "stable")
    return {
        "content_type": "stablecoin_supply",
        "date": date_str,
        "usdt_supply_b": round(random.uniform(80, 140), 2),
        "usdc_supply_b": round(random.uniform(25, 55), 2),
        "total_stablecoin_supply_b": round(random.uniform(120, 200), 2),
        "supply_change_7d_pct": _pct(-3, 5),
        "exchange_stablecoin_ratio": round(random.uniform(0.05, 0.25), 4),
        "mint_burn_net_m": round(random.uniform(-500, 1000), 1),
        "oi_change_pct": _pct(-10, 10),
        "deployment_state": random.choice(["deployed", "sidelined", "mixed"]),
    }


def fetch_orderbook_void(date_str: str) -> dict:
    """Orderbook Void / Depth metrics."""
    _seed_from_date(date_str, "ob")
    return {
        "content_type": "orderbook_void",
        "date": date_str,
        "bid_depth_1pct_m": round(random.uniform(20, 200), 1),
        "ask_depth_1pct_m": round(random.uniform(20, 200), 1),
        "bid_ask_imbalance_pct": _pct(-40, 40),
        "void_zone_above_pct": _pct(1, 8),
        "void_zone_below_pct": _pct(1, 8),
        "spread_bps": round(random.uniform(0.5, 5.0), 2),
        "depth_trend": random.choice(["thinning", "thickening", "stable"]),
        "spoofing_detected": random.choice([True, False]),
    }


def fetch_weekly_summary(date_str: str) -> dict:
    """Weekly Summary — aggregated metrics."""
    _seed_from_date(date_str, "weekly")
    return {
        "content_type": "weekly_summary",
        "date": date_str,
        "week_oi_change_pct": _pct(-15, 15),
        "week_etf_net_flow_m": round(random.uniform(-1000, 2000), 1),
        "week_liquidations_total_m": round(random.uniform(200, 3000), 1),
        "week_whale_net_flow_btc": round(random.uniform(-5000, 5000), 0),
        "week_stablecoin_change_pct": _pct(-3, 5),
        "week_orderbook_depth_change_pct": _pct(-20, 20),
        "dominant_theme": random.choice([
            "leverage_reset", "accumulation", "distribution",
            "liquidity_vacuum", "structural_compression", "regime_transition",
        ]),
        "structural_clarity": random.choice(["high", "moderate", "low"]),
    }


# ── Dispatcher ───────────────────────────────────────────────
FETCHERS = {
    "open_interest_funding": fetch_open_interest_funding,
    "etf_flow": fetch_etf_flow,
    "liquidation_map": fetch_liquidation_map,
    "whale_movement": fetch_whale_movement,
    "stablecoin_supply": fetch_stablecoin_supply,
    "orderbook_void": fetch_orderbook_void,
    "weekly_summary": fetch_weekly_summary,
}


def fetch_data(content_type: str, date_str: str) -> dict:
    """Fetch data for a given content type and date."""
    fetcher = FETCHERS.get(content_type)
    if not fetcher:
        raise ValueError(f"Unknown content type: {content_type}")
    return fetcher(date_str)
