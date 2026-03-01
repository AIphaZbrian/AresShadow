"""
ARES STRUCTURE ENGINE v1.0 — Bilingual Content Generator

Produces structured bilingual content from interpreted signals.
Output: hook_en, hook_cn, insight_en, insight_cn, framework lines.
"""

from ares.utils.constants import (
    BRAND_TAGLINE_EN,
    BRAND_TAGLINE_CN,
    CONTENT_LABELS_EN,
    CONTENT_LABELS_CN,
    ENGINE_NAME,
)
from ares.utils.logger import get_logger

log = get_logger("ares.generator")


# ── Hook Templates ───────────────────────────────────────────
# Keyed by content_type → (hook_en_template, hook_cn_template)

HOOK_TEMPLATES = {
    "open_interest_funding": (
        "OI + Funding Structure | {date}",
        "持仓量 + 资金费率结构 | {date}",
    ),
    "etf_flow": (
        "ETF Flow Structure | {date}",
        "ETF 资金流结构 | {date}",
    ),
    "liquidation_map": (
        "Liquidation Structure | {date}",
        "清算结构 | {date}",
    ),
    "whale_movement": (
        "Whale Flow Structure | {date}",
        "巨鲸流动结构 | {date}",
    ),
    "stablecoin_supply": (
        "Stablecoin Supply Structure | {date}",
        "稳定币供应结构 | {date}",
    ),
    "orderbook_void": (
        "Orderbook Depth Structure | {date}",
        "订单簿深度结构 | {date}",
    ),
    "weekly_summary": (
        "Weekly Structure Summary | {date}",
        "周度结构总结 | {date}",
    ),
}


# ── Metric Summary Builders ──────────────────────────────────

def _build_metric_summary_en(content_type: str, metrics: dict) -> str:
    """Build a concise English metric summary line."""
    builders = {
        "open_interest_funding": lambda m: (
            f"BTC OI: {m.get('btc_oi_change_pct', 0):+.1f}% | "
            f"Funding: {m.get('btc_funding_rate', 0):.4f} ({m.get('funding_state', 'n/a')})"
        ),
        "etf_flow": lambda m: (
            f"BTC ETF Net: ${m.get('btc_etf_net_flow_m', 0):+.0f}M | "
            f"Streak: {m.get('consecutive_days', 0)}d {m.get('flow_direction', 'n/a')}"
        ),
        "liquidation_map": lambda m: (
            f"Liquidated: ${m.get('total_liquidations_m', 0):.0f}M | "
            f"Long: ${m.get('long_liquidations_m', 0):.0f}M · Short: ${m.get('short_liquidations_m', 0):.0f}M"
        ),
        "whale_movement": lambda m: (
            f"Net flow: {m.get('net_flow_btc', 0):+,.0f} BTC | "
            f"Large txns: {m.get('large_txns_24h', 0)} | "
            f"Direction: {m.get('flow_direction', 'n/a')}"
        ),
        "stablecoin_supply": lambda m: (
            f"Total: ${m.get('total_supply_b', 0):.1f}B | "
            f"7d change: {m.get('supply_change_7d_pct', 0):+.2f}% | "
            f"Net mint/burn: ${m.get('mint_burn_net_m', 0):+.0f}M"
        ),
        "orderbook_void": lambda m: (
            f"Bid depth: ${m.get('bid_depth_1pct_m', 0):.0f}M | "
            f"Ask depth: ${m.get('ask_depth_1pct_m', 0):.0f}M | "
            f"Imbalance: {m.get('imbalance_pct', 0):+.1f}%"
        ),
        "weekly_summary": lambda m: (
            f"OI: {m.get('week_oi_change_pct', 0):+.1f}% | "
            f"ETF: ${m.get('week_etf_net_flow_m', 0):+.0f}M | "
            f"Liq: ${m.get('week_liquidations_total_m', 0):.0f}M"
        ),
    }
    builder = builders.get(content_type, lambda m: "")
    return builder(metrics)


def _build_metric_summary_cn(content_type: str, metrics: dict) -> str:
    """Build a concise Chinese metric summary line."""
    builders = {
        "open_interest_funding": lambda m: (
            f"BTC持仓量: {m.get('btc_oi_change_pct', 0):+.1f}% | "
            f"资金费率: {m.get('btc_funding_rate', 0):.4f} ({m.get('funding_state', 'n/a')})"
        ),
        "etf_flow": lambda m: (
            f"BTC ETF净流: ${m.get('btc_etf_net_flow_m', 0):+.0f}M | "
            f"连续{m.get('consecutive_days', 0)}日{m.get('flow_direction', 'n/a')}"
        ),
        "liquidation_map": lambda m: (
            f"清算总量: ${m.get('total_liquidations_m', 0):.0f}M | "
            f"多头: ${m.get('long_liquidations_m', 0):.0f}M · 空头: ${m.get('short_liquidations_m', 0):.0f}M"
        ),
        "whale_movement": lambda m: (
            f"净流量: {m.get('net_flow_btc', 0):+,.0f} BTC | "
            f"大额交易: {m.get('large_txns_24h', 0)}笔 | "
            f"方向: {m.get('flow_direction', 'n/a')}"
        ),
        "stablecoin_supply": lambda m: (
            f"总量: ${m.get('total_supply_b', 0):.1f}B | "
            f"7日变化: {m.get('supply_change_7d_pct', 0):+.2f}% | "
            f"净铸造/销毁: ${m.get('mint_burn_net_m', 0):+.0f}M"
        ),
        "orderbook_void": lambda m: (
            f"买盘深度: ${m.get('bid_depth_1pct_m', 0):.0f}M | "
            f"卖盘深度: ${m.get('ask_depth_1pct_m', 0):.0f}M | "
            f"失衡: {m.get('imbalance_pct', 0):+.1f}%"
        ),
        "weekly_summary": lambda m: (
            f"持仓量: {m.get('week_oi_change_pct', 0):+.1f}% | "
            f"ETF: ${m.get('week_etf_net_flow_m', 0):+.0f}M | "
            f"清算: ${m.get('week_liquidations_total_m', 0):.0f}M"
        ),
    }
    builder = builders.get(content_type, lambda m: "")
    return builder(metrics)


def generate_content(interpreted: dict) -> dict:
    """
    Generate bilingual content from interpreted signals.

    Returns:
        {
            hook_en, hook_cn,
            metric_line_en, metric_line_cn,
            insight_en, insight_cn,
            framework_en, framework_cn,
            signal_name, content_type, date
        }
    """
    ct = interpreted["content_type"]
    date = interpreted["date"]
    metrics = interpreted.get("metric_change", {})

    # Hooks
    hook_en, hook_cn = HOOK_TEMPLATES.get(ct, ("Structure Update | {date}", "结构更新 | {date}"))
    hook_en = hook_en.format(date=date)
    hook_cn = hook_cn.format(date=date)

    # Metric summaries
    metric_line_en = _build_metric_summary_en(ct, metrics)
    metric_line_cn = _build_metric_summary_cn(ct, metrics)

    # Insights (from interpreter)
    insight_en = interpreted["interpretation_en"]
    insight_cn = interpreted["interpretation_cn"]

    result = {
        "content_type": ct,
        "date": date,
        "signal_name": interpreted["signal_name"],
        "hook_en": hook_en,
        "hook_cn": hook_cn,
        "metric_line_en": metric_line_en,
        "metric_line_cn": metric_line_cn,
        "insight_en": insight_en,
        "insight_cn": insight_cn,
        "framework_en": BRAND_TAGLINE_EN,
        "framework_cn": BRAND_TAGLINE_CN,
    }

    log.info(f"Generated bilingual content for {ct} on {date}")
    return result
