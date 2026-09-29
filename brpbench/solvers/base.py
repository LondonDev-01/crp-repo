"""Solver abstraction shared by all benchmarked algorithms."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from ..instance import Instance


@dataclass
class SolveOutcome:
    value: Optional[int]
    status: str
    time_s: Optional[float] = None
    threads: Optional[int] = None
    extra: Dict = field(default_factory=dict)


class Solver(ABC):
    name: str = "solver"
    kind: str = "exact"
    priority_kind: str = "any"

    def supports(self, inst: Instance) -> bool:
        if self.priority_kind == "distinct":
            return inst.distinct_priorities
        if self.priority_kind == "duplicate":
            return not inst.distinct_priorities
        return True

    @abstractmethod
    def solve(
        self,
        inst: Instance,
        time_limit: Optional[float] = None,
        path: Optional[Path] = None,
    ) -> SolveOutcome:
        raise NotImplementedError

    @property
    def available(self) -> bool:
        return True
