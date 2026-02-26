"""QMD v1 (Query Memory Distillation) package.

Hybrid short-term state + checkpointing + long-term memory store.
Designed to be *LLM-optional*: distillation can be heuristic to avoid token spend.
"""

from .manager import QMDManager  # noqa: F401
