"""Persistent store for benchmark results (one JSON object per line)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

STATUS_OPTIMAL = "optimal"
STATUS_BEST = "best"
STATUS_FEASIBLE = "feasible"
STATUS_ERROR = "error"
STATUS_TIMEOUT = "timeout"

ResultKey = Tuple[str, Optional[str], str, str, str]


@dataclass
class Result:
    dataset: str
    klass: str
    instance: str
    solver: str
    value: Optional[int]
    status: str
    time_s: Optional[float] = None
    threads: Optional[int] = None
    time_limit_s: Optional[float] = None
    alpha: Optional[str] = None
    source: str = "run"
    timestamp: Optional[str] = None
    objective: str = "relocations"
    objectives: Optional[List[str]] = None
    points: Optional[List[List[float]]] = None
    extra: Dict = field(default_factory=dict)

    @property
    def key(self) -> ResultKey:
        return (self.dataset, self.alpha, self.klass, self.instance, self.solver)

    @property
    def is_multi_objective(self) -> bool:
        return bool(self.objectives)

    @property
    def front_size(self) -> int:
        return len(self.points) if self.points else 0

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_json(cls, line: str) -> "Result":
        data = json.loads(line)
        known = {f for f in cls.__dataclass_fields__}
        extra = {k: v for k, v in data.items() if k not in known}
        payload = {k: v for k, v in data.items() if k in known}
        payload.setdefault("extra", {})
        payload["extra"].update(extra)
        return cls(**payload)


class ResultStore:
    """Append-only JSONL store with in-memory upsert by ``(instance, solver)``."""

    def __init__(self, path: os.PathLike | str):
        self.path = Path(path)
        self._results: Dict[ResultKey, Result] = {}

    def __len__(self) -> int:
        return len(self._results)

    def load(self) -> "ResultStore":
        self._results.clear()
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    result = Result.from_json(line)
                    self._results[result.key] = result
        return self

    def upsert(self, result: Result) -> None:
        self._results[result.key] = result

    def has(self, dataset: str, alpha: Optional[str], klass: str, instance: str, solver: str) -> bool:
        return (dataset, alpha, klass, instance, solver) in self._results

    def values(self) -> Iterable[Result]:
        return self._results.values()

    def write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            for result in sorted(self._results.values(), key=lambda r: r.key):
                fh.write(result.to_json() + "\n")
        tmp.replace(self.path)
