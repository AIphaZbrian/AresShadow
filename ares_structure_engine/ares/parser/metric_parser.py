"""
ARES STRUCTURE ENGINE v1.0 — Metric Parser

Extracts structured signals from raw data:
{
    metric_change,
    leverage_shift,
    liquidity_state,
    structural_signal
}
"""

from ares.utils.logger import get_logger

log = get_logger("ares.parser")


def _classify_change(value: float, thresholds: tuple = (-3, 3)) -> str:
    """Classify a percentage change as down / flat / up."""
    low, high = thresholds
    if value <= low:
        return "down"
    elif value >= high:
        return "up"
    return "flat"


def _classify_funding(rate: float) -> str:
    """Classify funding rate."""
    if rate > 0.03:
        return "elevated"
    elif rate < -0.01:
        return "negative"
    return "neutral"


def parse_open_interest_funding(data: dict) -> dict:
    oi_dir = _classify_change(data["btc_oi_change_pct"], (-5, 5))
    funding_state = _classify_funding(data["btc_funding_rate"])
    price_dir = _classify_change(data["price_change_pct"], (-2, 2))

    if oi_dir == "down" and funding_state == "neutral":
        leverage_shift = "leverage_reset"
    elif oi_dir == "up" and funding_state == "elevated":
        leverage_shift = "leverage_buildup"
    elif oi_dir == "up" and funding_state == "neutral":
        leverage_shift = "organic_expansion"
    elif oi_dir == "down" and funding_state == "negative":
        leverage_shift = "capitulation_flush"
    else:
        leverage_shift = "stable"

    return {
        "content_type": data["content_type"],
        "date": data["date"],
        "metric_change": {
            "btc_oi_direction": oi_dir,
            "btc_oi_change_pct": data["btc_oi_change_pct"],
            "eth_oi_change_pct": data["eth_oi_change_pct"],
            "btc_funding_rate": data["btc_funding_rate"],
            "funding_state": funding_state,
            "price_direction": price_dir,
        },
        "leverage_shift": leverage_shift,
        "liquidity_state": data["oi_trend"],
        "structural_signal": leverage_shift,
    }


def parse_etf_flow(data: dict) -> dict:
    flow_dir = data["flow_direction"]
    price_dir = _classify_change(data["price_change_pct"], (-2, 2))
    magnitude = "strong" if abs(data["btc_etf_net_flow_m"]) > 300 else "moderate" if abs(data["btc_etf_net_flow_m"]) > 100 else "weak"

    if flow_dir == "inflow" and price_dir == "flat":
        signal = "accumulation"
    elif flow_dir == "inflow" and price_dir == "up":
        signal = "momentum_absorption"
    elif flow_dir == "outflow" and price_dir == "down":
        signal = "distribution"
    elif flow_dir == "outflow" and price_dir == "flat":
        signal = "passive_exit"
    else:
        signal = "divergence"

    return {
        "content_type": data["content_type"],
        "date": data["date"],
        "metric_change": {
            "btc_etf_net_flow_m": data["btc_etf_net_flow_m"],
            "eth_etf_net_flow_m": data["eth_etf_net_flow_m"],
            "flow_direction": flow_dir,
            "magnitude": magnitude,
            "consecutive_days": data["consecutive_days"],
            "price_direction": price_dir,
        },
        "leverage_shift": "n/a",
        "liquidity_state": f"etf_{flow_dir}_{magnitude}",
        "structural_signal": signal,
    }


def parse_liquidation_map(data: dict) -> dict:
    dominant = data["dominant_side"]
    total = data["total_liquidations_m"]
    ratio = data["liq_ratio"]
    leverage = data["leverage_state"]

    if total > 500 and dominant == "long":
        signal = "long_flush"
    elif total > 500 and dominant == "short":
        signal = "short_squeeze_reset"
    elif leverage == "overleveraged":
        signal = "fragile_structure"
    elif leverage == "deleveraged":
        signal = "clean_positioning"
    else:
        signal = "moderate_clearing"

    return {
        "content_type": data["content_type"],
        "date": data["date"],
        "metric_change": {
            "long_liquidations_m": data["long_liquidations_m"],
            "short_liquidations_m": data["short_liquidations_m"],
            "total_liquidations_m": total,
            "dominant_side": dominant,
            "liq_ratio": ratio,
            "cluster_distance_pct": data["cluster_distance_pct"],
        },
        "leverage_shift": leverage,
        "liquidity_state": "clearing" if total > 300 else "stable",
        "structural_signal": signal,
    }


def parse_whale_movement(data: dict) -> dict:
    direction = data["flow_direction"]
    net = data["net_flow_btc"]
    acc_score = data["whale_accumulation_score"]
    dormant = data["dormant_coins_moved"]

    if direction == "to_wallet" and acc_score > 60:
        signal = "strategic_accumulation"
    elif direction == "to_exchange" and acc_score < 30:
        signal = "distribution_pressure"
    elif dormant:
        signal = "dormant_reactivation"
    elif abs(net) < 500:
        signal = "neutral_flow"
    else:
        signal = "repositioning"

    return {
        "content_type": data["content_type"],
        "date": data["date"],
        "metric_change": {
            "net_flow_btc": net,
            "flow_direction": direction,
            "large_txns_24h": data["large_txns_24h"],
            "accumulation_score": acc_score,
            "dormant_coins_moved": dormant,
            "dormant_age_years": data["dormant_age_years"],
        },
        "leverage_shift": "n/a",
        "liquidity_state": direction,
        "structural_signal": signal,
    }


def parse_stablecoin_supply(data: dict) -> dict:
    supply_dir = _classify_change(data["supply_change_7d_pct"], (-1, 1))
    oi_dir = _classify_change(data["oi_change_pct"], (-3, 3))
    deployment = data["deployment_state"]

    if supply_dir == "up" and oi_dir == "flat":
        signal = "sidelined_liquidity"
    elif supply_dir == "up" and oi_dir == "up":
        signal = "liquidity_deployment"
    elif supply_dir == "down":
        signal = "liquidity_withdrawal"
    elif deployment == "sidelined":
        signal = "dry_powder_accumulation"
    else:
        signal = "stable_liquidity"

    return {
        "content_type": data["content_type"],
        "date": data["date"],
        "metric_change": {
            "total_supply_b": data["total_stablecoin_supply_b"],
            "supply_change_7d_pct": data["supply_change_7d_pct"],
            "usdt_supply_b": data["usdt_supply_b"],
            "usdc_supply_b": data["usdc_supply_b"],
            "mint_burn_net_m": data["mint_burn_net_m"],
            "oi_direction": oi_dir,
        },
        "leverage_shift": "n/a",
        "liquidity_state": deployment,
        "structural_signal": signal,
    }


def parse_orderbook_void(data: dict) -> dict:
    imbalance = data["bid_ask_imbalance_pct"]
    depth_trend = data["depth_trend"]
    void_above = data["void_zone_above_pct"]
    void_below = data["void_zone_below_pct"]

    if depth_trend == "thinning" and abs(imbalance) > 20:
        signal = "liquidity_vacuum"
    elif depth_trend == "thinning":
        signal = "fragile_depth"
    elif depth_trend == "thickening" and abs(imbalance) < 10:
        signal = "structural_support"
    elif data["spoofing_detected"]:
        signal = "synthetic_depth"
    else:
        signal = "balanced_book"

    return {
        "content_type": data["content_type"],
        "date": data["date"],
        "metric_change": {
            "bid_depth_1pct_m": data["bid_depth_1pct_m"],
            "ask_depth_1pct_m": data["ask_depth_1pct_m"],
            "imbalance_pct": imbalance,
            "void_above_pct": void_above,
            "void_below_pct": void_below,
            "spread_bps": data["spread_bps"],
        },
        "leverage_shift": "n/a",
        "liquidity_state": depth_trend,
        "structural_signal": signal,
    }


def parse_weekly_summary(data: dict) -> dict:
    return {
        "content_type": data["content_type"],
        "date": data["date"],
        "metric_change": {
            "week_oi_change_pct": data["week_oi_change_pct"],
            "week_etf_net_flow_m": data["week_etf_net_flow_m"],
            "week_liquidations_total_m": data["week_liquidations_total_m"],
            "week_whale_net_flow_btc": data["week_whale_net_flow_btc"],
            "week_stablecoin_change_pct": data["week_stablecoin_change_pct"],
            "week_orderbook_depth_change_pct": data["week_orderbook_depth_change_pct"],
        },
        "leverage_shift": "mixed",
        "liquidity_state": data["structural_clarity"],
        "structural_signal": data["dominant_theme"],
    }


# ── Dispatcher ───────────────────────────────────────────────
PARSERS = {
    "open_interest_funding": parse_open_interest_funding,
    "etf_flow": parse_etf_flow,
    "liquidation_map": parse_liquidation_map,
    "whale_movement": parse_whale_movement,
    "stablecoin_supply": parse_stablecoin_supply,
    "orderbook_void": parse_orderbook_void,
    "weekly_summary": parse_weekly_summary,
}


def parse_metrics(data: dict) -> dict:
    """Parse raw data into structured signals."""
    content_type = data.get("content_type")
    parser = PARSERS.get(content_type)
    if not parser:
        raise ValueError(f"No parser for content type: {content_type}")
    result = parser(data)
    log.info(f"Parsed signal: {result['structural_signal']}")
    return result
