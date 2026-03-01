"""
ARES STRUCTURE ENGINE v1.0 — Rule-Based Structure Interpreter

Contains 20+ structural interpretation rules.
Each rule maps a combination of parsed signals to a bilingual structural interpretation.
"""

from ares.utils.logger import get_logger

log = get_logger("ares.rules")


# ── Interpretation Templates ─────────────────────────────────
# Each entry: (signal_key, interpretation_en, interpretation_cn)

INTERPRETATIONS = {
    # ── Open Interest + Funding Rules ────────────────────────
    "leverage_reset": (
        "Leverage is resetting. Open interest declining with neutral funding indicates forced or voluntary position reduction.",
        "杠杆正在重置。持仓量下降且资金费率中性，表明头寸正在被动或主动缩减。",
    ),
    "leverage_buildup": (
        "Leverage is building. Rising open interest with elevated funding signals aggressive positioning. Structure is fragile.",
        "杠杆正在累积。持仓量上升且资金费率偏高，表明仓位激进。结构脆弱。",
    ),
    "organic_expansion": (
        "Organic expansion detected. Open interest rising with neutral funding suggests genuine market participation.",
        "检测到有机扩张。持仓量上升但资金费率中性，表明市场参与真实。",
    ),
    "capitulation_flush": (
        "Capitulation flush observed. Open interest collapsing with negative funding — forced exits are clearing the structure.",
        "观察到投降式冲洗。持仓量暴跌且资金费率为负——强制平仓正在清理结构。",
    ),
    "stable": (
        "Structure is stable. No significant leverage shift detected in current cycle.",
        "结构稳定。当前周期未检测到显著杠杆变化。",
    ),

    # ── ETF Flow Rules ───────────────────────────────────────
    "accumulation": (
        "Institutional accumulation pattern. ETF inflows persist while price remains range-bound. Capital is being absorbed quietly.",
        "机构吸筹模式。ETF持续流入但价格维持区间震荡。资金正在被静默吸收。",
    ),
    "momentum_absorption": (
        "Momentum absorption in progress. ETF inflows align with price movement — institutional flow is reinforcing direction.",
        "动量吸收进行中。ETF流入与价格走势一致——机构资金正在强化方向。",
    ),
    "distribution": (
        "Distribution pattern emerging. ETF outflows coincide with price weakness. Institutional exits are visible.",
        "分配模式显现。ETF流出与价格走弱同步。机构退出信号可见。",
    ),
    "passive_exit": (
        "Passive exit detected. ETF outflows with flat price suggest quiet institutional repositioning.",
        "检测到被动退出。ETF流出但价格平稳，表明机构正在静默调仓。",
    ),
    "divergence": (
        "Flow-price divergence. ETF flow direction conflicts with price action. Structure is ambiguous.",
        "流量-价格背离。ETF资金流向与价格走势矛盾。结构模糊。",
    ),

    # ── Liquidation Map Rules ────────────────────────────────
    "long_flush": (
        "Long-side flush complete. Significant long liquidations cleared overleveraged positions. Structure is lighter.",
        "多头冲洗完成。大量多头清算清除了过度杠杆仓位。结构更轻。",
    ),
    "short_squeeze_reset": (
        "Short-side reset. Heavy short liquidations indicate a squeeze event. Positioning has been forcibly rebalanced.",
        "空头重置。大量空头清算表明发生了逼空事件。仓位已被强制再平衡。",
    ),
    "fragile_structure": (
        "Fragile structure detected. Market remains overleveraged. Liquidation clusters are close to current price.",
        "检测到脆弱结构。市场仍处于过度杠杆状态。清算集群距当前价格较近。",
    ),
    "clean_positioning": (
        "Clean positioning. Leverage has been flushed. The structure is reset and ready for the next regime.",
        "仓位清洁。杠杆已被冲洗。结构已重置，准备进入下一阶段。",
    ),
    "moderate_clearing": (
        "Moderate clearing. Liquidations are within normal range. No structural disruption observed.",
        "适度清理。清算量在正常范围内。未观察到结构性破坏。",
    ),

    # ── Whale Movement Rules ─────────────────────────────────
    "strategic_accumulation": (
        "Strategic accumulation by large holders. Coins moving to cold storage. Supply is being removed from circulation.",
        "大户战略性吸筹。代币转入冷钱包。供应正从流通中撤出。",
    ),
    "distribution_pressure": (
        "Distribution pressure from whales. Exchange inflows elevated. Large holders are repositioning toward exits.",
        "巨鲸分配压力。交易所流入增加。大户正在向退出方向调仓。",
    ),
    "dormant_reactivation": (
        "Dormant coins reactivated. Long-held supply is moving for the first time in years. Structural shift in holder behavior.",
        "沉睡代币被激活。长期持有的供应首次移动。持有者行为发生结构性转变。",
    ),
    "neutral_flow": (
        "Whale flow is neutral. No significant directional movement from large holders. Structure is in equilibrium.",
        "巨鲸流量中性。大户无显著方向性移动。结构处于均衡状态。",
    ),
    "repositioning": (
        "Whale repositioning detected. Significant movement without clear directional bias. Watch for follow-through.",
        "检测到巨鲸调仓。有显著移动但无明确方向偏好。关注后续动作。",
    ),

    # ── Stablecoin Supply Rules ──────────────────────────────
    "sidelined_liquidity": (
        "Sidelined liquidity growing. Stablecoin supply rising but not entering derivatives. Capital is waiting on the sidelines.",
        "场外流动性增长。稳定币供应上升但未进入衍生品市场。资金在场外等待。",
    ),
    "liquidity_deployment": (
        "Liquidity deployment in progress. Stablecoin supply and open interest both rising. Capital is entering the structure.",
        "流动性部署进行中。稳定币供应和持仓量同步上升。资金正在进入结构。",
    ),
    "liquidity_withdrawal": (
        "Liquidity withdrawal detected. Stablecoin supply contracting. Capital is leaving the ecosystem.",
        "检测到流动性撤出。稳定币供应收缩。资金正在离开生态系统。",
    ),
    "dry_powder_accumulation": (
        "Dry powder accumulating. Stablecoins are minted but remain undeployed. Potential energy is building.",
        "弹药积累中。稳定币已铸造但未部署。势能正在积聚。",
    ),
    "stable_liquidity": (
        "Liquidity is stable. No significant change in stablecoin supply or deployment patterns.",
        "流动性稳定。稳定币供应和部署模式无显著变化。",
    ),

    # ── Orderbook Void Rules ─────────────────────────────────
    "liquidity_vacuum": (
        "Liquidity vacuum detected. Order book is thinning with significant imbalance. Price may move sharply through void zones.",
        "检测到流动性真空。订单簿变薄且存在显著失衡。价格可能在空白区域剧烈移动。",
    ),
    "fragile_depth": (
        "Fragile depth. Order book is thinning but balanced. Structure can absorb small moves but not large ones.",
        "深度脆弱。订单簿变薄但保持平衡。结构可以吸收小幅波动但无法承受大幅波动。",
    ),
    "structural_support": (
        "Structural support forming. Order book depth is increasing with balanced bids and asks. Foundation is strengthening.",
        "结构性支撑正在形成。订单簿深度增加，买卖盘平衡。基础正在加强。",
    ),
    "synthetic_depth": (
        "Synthetic depth detected. Spoofing patterns visible in the order book. Displayed liquidity may not be genuine.",
        "检测到合成深度。订单簿中可见挂单欺诈模式。显示的流动性可能不真实。",
    ),
    "balanced_book": (
        "Order book is balanced. Depth is adequate and evenly distributed. No structural anomalies detected.",
        "订单簿平衡。深度充足且分布均匀。未检测到结构异常。",
    ),

    # ── Weekly Summary Rules ─────────────────────────────────
    "structural_compression": (
        "Structural compression this week. Multiple metrics converging toward neutral. A regime change may follow.",
        "本周结构压缩。多项指标趋向中性。可能随后发生制度转换。",
    ),
    "regime_transition": (
        "Regime transition underway. The structural character of the market shifted this week across multiple dimensions.",
        "制度转换进行中。市场的结构特征本周在多个维度发生了变化。",
    ),
}

# Fallback for unknown signals
_FALLBACK = (
    "Structure is in transition. Current signals do not match established patterns. Monitoring continues.",
    "结构处于过渡期。当前信号不匹配已建立的模式。持续监控中。",
)


def interpret(parsed: dict) -> dict:
    """
    Apply rule-based interpretation to parsed signals.

    Returns a dict with:
        interpretation_en, interpretation_cn, signal_name
    """
    signal = parsed.get("structural_signal", "unknown")
    interp = INTERPRETATIONS.get(signal, _FALLBACK)

    result = {
        "content_type": parsed["content_type"],
        "date": parsed["date"],
        "signal_name": signal,
        "leverage_shift": parsed.get("leverage_shift", "n/a"),
        "liquidity_state": parsed.get("liquidity_state", "unknown"),
        "interpretation_en": interp[0],
        "interpretation_cn": interp[1],
        "metric_change": parsed.get("metric_change", {}),
    }

    log.info(f"Interpreted signal '{signal}' for {parsed['content_type']}")
    return result
