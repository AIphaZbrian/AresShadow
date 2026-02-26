from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


def estimate_tokens(text: str) -> int:
    # Very cheap heuristic: ~4 chars per token for English-ish text.
    # For CJK, this overestimates slightly but stays safe for budgeting.
    return max(1, int(len(text) / 4))


@dataclass
class Checkpoint:
    goal: str
    constraints: List[str]
    state: Dict[str, Any]
    decisions: List[str]
    open_loops: List[str]
    pointers: List[str]
    summary_lines: List[str]

    def to_markdown(self) -> str:
        def bullets(items: List[str]) -> str:
            return "\n".join(f"- {x}" for x in items) if items else "- (none)"

        state_lines = [f"- {k}: {v}" for k, v in (self.state or {}).items()]
        state_md = "\n".join(state_lines) if state_lines else "- (empty)"

        return (
            f"Goal\n{self.goal}\n\n"
            f"Constraints\n{bullets(self.constraints)}\n\n"
            f"State\n{state_md}\n\n"
            f"Decisions\n{bullets(self.decisions)}\n\n"
            f"OpenLoops\n{bullets(self.open_loops)}\n\n"
            f"Pointers\n{bullets(self.pointers)}\n"
        )


def distill_lines(lines: List[str], max_lines: int) -> List[str]:
    # Heuristic distillation: keep last max_lines, but drop blank lines.
    compact = [ln.strip() for ln in lines if ln.strip()]
    if len(compact) <= max_lines:
        return compact
    return compact[-max_lines:]
