from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import QMDConfig, load_qmd_config
from .distill import Checkpoint, distill_lines, estimate_tokens
from .store import JsonlStore, MemoryItem, now_ts


class QMDManager:
    """Low-token memory manager.

    - Maintains a compact per-agent state block
    - Appends checkpoints (distilled summaries) to jsonl
    - Optionally appends long-term items when explicitly approved

    This implementation avoids LLM calls; distillation is heuristic.
    """

    def __init__(
        self,
        project_root: Path,
        agent_name: str,
        thread_id: str,
        config_path: Optional[Path] = None,
    ) -> None:
        self.project_root = project_root
        self.agent_name = agent_name
        self.thread_id = thread_id
        self.config = load_qmd_config(config_path or (project_root / "config" / "qmd_v1.yaml"))

        self.memory_dir = project_root / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.state_path = self.memory_dir / f"qmd_state_{agent_name}.json"
        self.checkpoints = JsonlStore(self.memory_dir / "qmd_checkpoints.jsonl")
        self.longterm = JsonlStore(self.memory_dir / "qmd_longterm.jsonl")

        self._turn_lines: List[str] = []
        self._approx_tokens: int = 0

        self.state: Dict[str, Any] = self._load_state()
        self.state.setdefault("agent_name", agent_name)
        self.state.setdefault("thread_id", thread_id)
        self.state.setdefault("updated_at", None)

    def _load_state(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            return {}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def save_state(self) -> None:
        self.state["updated_at"] = now_ts()
        tmp = self.state_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(self.state_path)

    def observe(self, text: str) -> None:
        self._turn_lines.append(text)
        self._approx_tokens += estimate_tokens(text)

    def maybe_distill(self, goal: str, constraints: List[str], decisions: List[str], open_loops: List[str], pointers: List[str]) -> Optional[Checkpoint]:
        if self._approx_tokens < self.config.soft_threshold_tokens:
            return None

        hard = self._approx_tokens >= self.config.hard_threshold_tokens
        max_lines = self.config.hard_checkpoint_max_lines if hard else self.config.soft_checkpoint_max_lines

        summary = distill_lines(self._turn_lines, max_lines=max_lines)
        cp = Checkpoint(
            goal=goal,
            constraints=constraints,
            state=self.state,
            decisions=decisions,
            open_loops=open_loops,
            pointers=pointers,
            summary_lines=summary,
        )
        self.append_checkpoint(cp, hard=hard)

        # Reset observed turns to keep context small
        self._turn_lines = []
        self._approx_tokens = 0

        # In hard mode, keep only state & pointers (turn buffer cleared already)
        return cp

    def append_checkpoint(self, cp: Checkpoint, hard: bool = False) -> None:
        item = MemoryItem(
            type="checkpoint",
            scope="thread",
            confidence=0.9,
            source=f"qmd:{self.agent_name}:{self.thread_id}",
            tags=["qmd", "checkpoint", "hard" if hard else "soft"],
            payload={
                "agent": self.agent_name,
                "thread": self.thread_id,
                "hard": hard,
                "checkpoint": {
                    "goal": cp.goal,
                    "constraints": cp.constraints,
                    "state": cp.state,
                    "decisions": cp.decisions,
                    "open_loops": cp.open_loops,
                    "pointers": cp.pointers,
                    "summary_lines": cp.summary_lines,
                },
            },
            created_at=now_ts(),
        )
        self.checkpoints.append(item)

    def _policy_longterm_approved(self) -> bool:
        # Global policy file allows user-level approval without extra LLM turns.
        policy_path = self.project_root / "memory" / "qmd_policy.json"
        if not policy_path.exists():
            return False
        try:
            obj = json.loads(policy_path.read_text(encoding="utf-8"))
        except Exception:
            return False
        return bool(obj.get("longtermApproved"))

    def commit_longterm(self, *, type: str, payload: Dict[str, Any], source: str, tags: Optional[List[str]] = None, approved: bool = False, confidence: float = 0.75) -> bool:
        """Write to long-term store only when approved (anti-pollution).

        Approval can be passed explicitly (approved=True) or granted globally
        via memory/qmd_policy.json (longtermApproved=true).
        """
        if not (approved or self._policy_longterm_approved()):
            return False
        item = MemoryItem(
            type=type,
            scope="project",
            confidence=confidence,
            source=source,
            tags=tags or ["qmd", "longterm"],
            payload=payload,
            created_at=now_ts(),
        )
        self.longterm.append(item)
        return True

    def end_run_checkpoint(self, goal: str, constraints: List[str], decisions: List[str], open_loops: List[str], pointers: List[str], extra_lines: Optional[List[str]] = None) -> Checkpoint:
        # Always write a small checkpoint per run (cheap audit trail)
        lines = list(self._turn_lines)
        if extra_lines:
            lines.extend(extra_lines)
        summary = distill_lines(lines, max_lines=12)
        cp = Checkpoint(
            goal=goal,
            constraints=constraints,
            state=self.state,
            decisions=decisions,
            open_loops=open_loops,
            pointers=pointers,
            summary_lines=summary,
        )
        self.append_checkpoint(cp, hard=False)
        self._turn_lines = []
        self._approx_tokens = 0
        self.save_state()
        return cp
