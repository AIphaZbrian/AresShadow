from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = None


@dataclass(frozen=True)
class QMDConfig:
    # TTLs (minutes)
    convo_cache_minutes: int = 45
    retrieval_cache_minutes: int = 10
    external_data_cache_minutes: int = 1

    # Token budgets (approximate; we use heuristic token estimation)
    reserve_tokens_floor: int = 4200
    soft_threshold_tokens: int = 7500
    hard_threshold_tokens: int = 10500

    # Distill policy
    soft_keep_last_turns: int = 8
    soft_checkpoint_max_lines: int = 18
    hard_keep_last_turns: int = 3
    hard_checkpoint_max_lines: int = 12

    retrieval_top_k: int = 5


def _minutes(value: Any, default_minutes: int) -> int:
    if value is None:
        return default_minutes
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        s = value.strip().lower()
        if s.endswith("m"):
            return int(float(s[:-1]))
        if s.endswith("h"):
            return int(float(s[:-1]) * 60)
        return int(float(s))
    return default_minutes


def load_qmd_config(path: Path) -> QMDConfig:
    if not path.exists() or yaml is None:
        # If PyYAML isn't available, fall back to defaults.
        return QMDConfig()
    data: Dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    ttl = data.get("ttl", {})
    tb = data.get("tokenBudget", {})
    trim = data.get("trimPolicy", {})
    soft = (trim.get("softDistill") or {})
    hard = (trim.get("hardDistill") or {})
    retrieval = data.get("retrieval", {})

    return QMDConfig(
        convo_cache_minutes=_minutes(ttl.get("convoCache"), 45),
        retrieval_cache_minutes=_minutes(ttl.get("retrievalCache"), 10),
        external_data_cache_minutes=_minutes(ttl.get("externalDataCache"), 1),
        reserve_tokens_floor=int(tb.get("reserveTokensFloor", 4200)),
        soft_threshold_tokens=int(tb.get("softThresholdTokens", 7500)),
        hard_threshold_tokens=int(tb.get("hardThresholdTokens", 10500)),
        soft_keep_last_turns=int(soft.get("keepLastTurns", 8)),
        soft_checkpoint_max_lines=int(soft.get("checkpointMaxLines", 18)),
        hard_keep_last_turns=int(hard.get("keepLastTurns", 3)),
        hard_checkpoint_max_lines=int(hard.get("checkpointMaxLines", 12)),
        retrieval_top_k=int(retrieval.get("topK", 5)),
    )
