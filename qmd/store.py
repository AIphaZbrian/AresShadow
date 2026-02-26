from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


@dataclass
class MemoryItem:
    type: str  # preferences|decisions|sop|safety_constraints|facts|checkpoint
    scope: str  # agent|project|thread
    confidence: float
    source: str
    tags: list[str]
    payload: Dict[str, Any]
    created_at: float
    ttl_seconds: Optional[int] = None


class JsonlStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, item: MemoryItem) -> None:
        line = json.dumps(asdict(item), ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def iter_items(self, limit: int = 5000) -> Iterable[Dict[str, Any]]:
        if not self.path.exists():
            return []
        items = []
        with self.path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return items


def now_ts() -> float:
    return time.time()
