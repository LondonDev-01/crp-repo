"""Simple constructive heuristic for the restricted BRP (reference baseline).

At each step the algorithm targets the smallest remaining retrieval priority.
If an accessible block has that priority it is retrieved; otherwise the top
block of the most promising stack is relocated onto the stack whose top block
leaves latest (empty stacks first). This is a deterministic, fast upper bound,
not a state-of-the-art method.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import List, Optional

from ..instance import Instance
from ..results import STATUS_ERROR, STATUS_FEASIBLE
from .base import SolveOutcome, Solver

MAX_STEPS = 1_000_000


class GreedySolver(Solver):
    name = "greedy"
    kind = "heuristic"
    priority_kind = "any"

    def solve(self, inst: Instance, time_limit: Optional[float] = None, path: Optional[Path] = None) -> SolveOutcome:
        start = perf_counter()
        outcome = self._solve(inst)
        outcome.time_s = perf_counter() - start
        return outcome

    def _solve(self, inst: Instance) -> SolveOutcome:
        stacks: List[List[int]] = [list(s) for s in inst.stacks]
        capacity = inst.max_tier
        n = len(stacks)
        remaining = Counter(p for s in stacks for p in s)
        relocations = 0

        for _ in range(MAX_STEPS):
            if not remaining:
                return SolveOutcome(relocations, STATUS_FEASIBLE)
            target = min(remaining)
            sources = [c for c in range(n) if target in stacks[c]]
            if not sources:
                return SolveOutcome(relocations, STATUS_ERROR, extra={"error": "target vanished"})
            source = min(sources, key=lambda c: _blockers_above(stacks[c], target))
            if stacks[source][-1] == target:
                block = stacks[source].pop()
                remaining[block] -= 1
                if remaining[block] == 0:
                    del remaining[block]
                continue
            dests = [d for d in range(n) if d != source and len(stacks[d]) < capacity]
            if not dests:
                return SolveOutcome(None, STATUS_ERROR, extra={"error": "dead end: no free slot"})
            dest = min(dests, key=lambda d: _dest_key(stacks[d]))
            stacks[dest].append(stacks[source].pop())
            relocations += 1
        return SolveOutcome(None, STATUS_ERROR, extra={"error": "step limit reached"})

    @property
    def available(self) -> bool:
        return True


def _blockers_above(stack: List[int], target: int) -> int:
    idx = max(i for i, p in enumerate(stack) if p == target)
    return len(stack) - idx - 1


def _dest_key(stack: List[int]):
    top = stack[-1] if stack else float("inf")
    return (-top, len(stack))
