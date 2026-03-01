"""
ARES STRUCTURE ENGINE v1.0 — Token Counter Utility

Lightweight token estimator that avoids heavy dependencies.
Uses a simple heuristic: ~4 characters per English token, ~2 characters per CJK token.
"""

import re


def estimate_tokens(text: str) -> int:
    """Estimate token count for a mixed EN/CN text string."""
    # Separate CJK characters from Latin text
    cjk_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
    non_cjk = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf]', '', text)
    # English tokens: roughly 1 token per 4 chars or per word
    en_tokens = len(non_cjk.split())
    # CJK tokens: roughly 1 token per 1.5 characters
    cn_tokens = int(cjk_chars / 1.5) + 1 if cjk_chars > 0 else 0
    return en_tokens + cn_tokens


def is_within_budget(text: str, budget: int = 800) -> bool:
    """Check if text is within token budget."""
    return estimate_tokens(text) <= budget
