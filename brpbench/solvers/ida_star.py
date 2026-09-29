"""Iterative-deepening A* for the container relocation problem.

Implementation of the algorithm in Zhu, Qin, Lim & Zhang (2012), *Iterative
deepening A* algorithms for the container relocation problem*, IEEE T-ASE
9(4):710-722.

The solver mirrors the paper's structure:

* iterative deepening on ``f = g + h``, where ``g`` counts confirmed relocations
  and ``h`` is one of the admissible lower bounds LB1/LB2/LB3;
* free retrievals are applied eagerly (the paper's "minimum equivalent layout"),
  so the search only branches over relocations;
* probe heuristics (PR1..PR4) complete promising frontier nodes to tighten the
  incumbent early.

Priorities are distinct and retrieved in ascending order. Only relocations are
counted (retrievals are free), so the reported value is comparable with the
other solvers in this benchmark. LB2 and LB3 are admissible for the restricted
variant only; the unrestricted solver falls back to LB1, which is much weaker,
so it is exact but may hit the time limit (returning a feasible ``best``) on
larger instances.
"""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Callable, Dict, List, Optional, Tuple

from ..instance import Instance
from ..results import STATUS_BEST, STATUS_ERROR, STATUS_OPTIMAL, STATUS_TIMEOUT
from .base import SolveOutcome, Solver

Layout = Tuple[Tuple[int, ...], ...]
Step = Tuple[int, Optional[int]]
StepFn = Callable[[List[List[int]], int, Layout], Step]

INF = 1 << 30
MAX_STEPS = 1_000_000


class _NoSolution(Exception):
    """Raised when no feasible retrieval sequence could be constructed."""


def _k_matrix(layout: Layout) -> Layout:
    """``k[s][j]`` is the smallest priority in stack ``s`` at or below tier ``j``."""
    rows = []
    for stack in layout:
        row: List[int] = []
        running = INF
        for value in stack:
            if value < running:
                running = value
            row.append(running)
        rows.append(tuple(row))
    return tuple(rows)


def _normalize(layout: Layout) -> Layout:
    """Retrieve every directly accessible target, in ascending order."""
    stacks = [list(s) for s in layout]
    while True:
        mins = [min(s) if s else INF for s in stacks]
        target = min(mins)
        if target >= INF:
            break
        src = mins.index(target)
        if stacks[src][-1] == target:
            stacks[src].pop()
        else:
            break
    return tuple(tuple(s) for s in stacks)


def _lb1(k: Layout) -> int:
    """Containers sitting above a smaller priority must be relocated once."""
    count = 0
    for row in k:
        for tier in range(1, len(row)):
            if row[tier - 1] == row[tier]:
                count += 1
    return count


def _lb2(layout: Layout, capacity: int, k: Layout) -> int:
    """LB1 plus blockers of the current target with no clean destination."""
    if not any(layout):
        return 0
    mins = [min(s) if s else INF for s in layout]
    target = min(mins)
    src = mins.index(target)
    tier = layout[src].index(target)
    count = 0
    for block in layout[src][tier + 1 :]:
        must_move = True
        for dest in range(len(layout)):
            if dest != src and len(layout[dest]) < capacity and block < mins[dest]:
                must_move = False
        if must_move:
            count += 1
    return count + _lb1(k)


def _lb3(layout: Layout, capacity: int, k: Layout) -> int:
    """LB2 applied over the whole retrieval sequence, target by target."""
    n_stacks = len(layout)
    count = 0
    heights = [len(s) for s in layout]
    mins = [k[s][heights[s] - 1] if heights[s] > 0 else INF for s in range(n_stacks)]
    while max(heights) != 0:
        target = min(mins)
        src = mins.index(target)
        tier = layout[src].index(target)
        for block in layout[src][tier + 1 : heights[src]]:
            must_move = True
            for dest in range(n_stacks):
                if dest != src and heights[dest] < capacity and block < mins[dest]:
                    must_move = False
            if must_move:
                count += 1
        heights[src] = tier
        mins[src] = k[src][tier - 1] if tier > 0 else INF
    return count + _lb1(k)


def _pr1(stacks: List[List[int]], capacity: int, k: Layout) -> Step:
    """Relocate to the shortest stack."""
    mins = [min(s) if s else INF for s in stacks]
    target = min(mins)
    src = mins.index(target)
    if stacks[src][-1] == target:
        return src, None
    best = INF
    dest = -1
    for d in range(len(stacks)):
        if d == src or len(stacks[d]) == capacity:
            continue
        if len(stacks[d]) < best:
            best = len(stacks[d])
            dest = d
    return src, dest


def _pr2(stacks: List[List[int]], capacity: int, k: Layout) -> Step:
    """Relocate onto the stack with the highest minimum priority."""
    mins = [min(s) if s else INF for s in stacks]
    target = min(mins)
    src = mins.index(target)
    if stacks[src][-1] == target:
        return src, None
    mins = list(mins)
    for d in range(len(stacks)):
        if len(stacks[d]) == capacity:
            mins[d] = 0
    return src, mins.index(max(mins))


def _pr3(stacks: List[List[int]], capacity: int, k: Layout) -> Step:
    """Clean destination with the lowest minimum, else the highest minimum."""
    mins = [k[s][-1] if stacks[s] else INF for s in range(len(stacks))]
    target = min(mins)
    src = mins.index(target)
    top = stacks[src][-1]
    if top == target:
        return src, None
    first = [m if m > top else 20000 for m in mins]
    for d in range(len(stacks)):
        if len(stacks[d]) == capacity:
            first[d] = 20000
    lowest = min(first)
    if lowest != 20000:
        return src, first.index(lowest)
    second = [m if m < top else 0 for m in mins]
    for d in range(len(stacks)):
        if len(stacks[d]) == capacity:
            second[d] = 0
    return src, second.index(max(second))


def _pr4(stacks: List[List[int]], capacity: int, k: Layout) -> Step:
    """PR3 with an extra check when the only option is a nearly full stack."""
    mins = [k[s][-1] if stacks[s] else INF for s in range(len(stacks))]
    target = min(mins)
    src = mins.index(target)
    top = stacks[src][-1]
    if top == target:
        return src, None
    first = [m if m > top else 20000 for m in mins]
    for d in range(len(stacks)):
        if len(stacks[d]) == capacity:
            first[d] = 20000
    lowest = min(first)
    if lowest != 20000:
        return src, first.index(lowest)
    second_smallest = sorted(stacks[src])[1]
    second = [m if m < top else 0 for m in mins]
    for d in range(len(stacks)):
        if len(stacks[d]) == capacity or d == src:
            second[d] = -1
    ranked = sorted(second, reverse=True)
    highest = ranked[0]
    second_highest = ranked[1] if len(ranked) > 1 else -1
    dest_highest = second.index(highest)
    if second_smallest != top and len(stacks[dest_highest]) == capacity - 1 and second_highest != -1:
        return src, second.index(second_highest)
    return src, dest_highest


_STEP_FNS: Dict[str, StepFn] = {"PR1": _pr1, "PR2": _pr2, "PR3": _pr3, "PR4": _pr4}


def _run_steps(layout: Layout, capacity: int, step_fn: StepFn) -> Optional[int]:
    """Apply ``step_fn`` until the bay is empty, returning relocations used."""
    stacks = [list(s) for s in layout]
    relocations = 0
    for _ in range(MAX_STEPS):
        if not any(stacks):
            return relocations
        k = _k_matrix(tuple(tuple(s) for s in stacks))
        src, dest = step_fn(stacks, capacity, k)
        if src is None or src < 0 or not stacks[src]:
            return None
        block = stacks[src].pop()
        if dest is not None:
            if dest < 0 or dest >= len(stacks) or dest == src or len(stacks[dest]) >= capacity:
                return None
            stacks[dest].append(block)
            relocations += 1
    return None


def _run_probe(layout: Layout, capacity: int, name: str) -> Optional[int]:
    """Best relocation count over the requested probe heuristic(s)."""
    if name == "PR_plus":
        results = [_run_steps(layout, capacity, fn) for fn in (_pr1, _pr2, _pr3, _pr4)]
        feasible = [r for r in results if r is not None]
        return min(feasible) if feasible else None
    return _run_steps(layout, capacity, _STEP_FNS[name])


class _Search:
    """Single IDA* run over an immutable layout."""

    def __init__(
        self,
        layout: Layout,
        capacity: int,
        restricted: bool,
        lower_bound: str,
        probe: str,
        time_limit: Optional[float],
        start: float,
    ):
        self.layout = layout
        self.capacity = capacity
        self.restricted = restricted
        self.lower_bound = lower_bound if restricted else "LB1"
        self.probe = probe
        self.time_limit = time_limit
        self.start = start
        self.best = 0
        self.best_lb = 0
        self.nodes = 0

    def run(self) -> Tuple[int, bool]:
        root = _normalize(self.layout)
        initial = _run_probe(root, self.capacity, "PR_plus")
        self.best = initial if initial is not None else INF
        self.best_lb = self._lb(root)
        threshold = self.best_lb
        while self.best > self.best_lb:
            root_lb = self._dfs(root, 0, threshold)
            if root_lb >= INF:
                raise _NoSolution("no feasible retrieval sequence exists")
            if root_lb > self.best_lb:
                self.best_lb = root_lb
            if self._timed_out():
                break
            threshold += 1
        if self.best >= INF:
            return INF, False
        return self.best, self.best_lb >= self.best

    def _lb(self, layout: Layout) -> int:
        if self.lower_bound == "LB1":
            return _lb1(_k_matrix(layout))
        if self.lower_bound == "LB2":
            return _lb2(layout, self.capacity, _k_matrix(layout))
        return _lb3(layout, self.capacity, _k_matrix(layout))

    def _timed_out(self) -> bool:
        return self.time_limit is not None and (perf_counter() - self.start) > self.time_limit

    def _children(self, layout: Layout):
        if self.restricted:
            mins = [min(s) if s else INF for s in layout]
            src = mins.index(min(mins))
            for dest in range(len(layout)):
                if dest == src or len(layout[dest]) >= self.capacity:
                    continue
                stacks = [list(s) for s in layout]
                stacks[dest].append(stacks[src].pop())
                yield tuple(tuple(s) for s in stacks)
        else:
            for src in range(len(layout)):
                if not layout[src]:
                    continue
                for dest in range(len(layout)):
                    if dest == src or len(layout[dest]) >= self.capacity:
                        continue
                    stacks = [list(s) for s in layout]
                    stacks[dest].append(stacks[src].pop())
                    yield tuple(tuple(s) for s in stacks)

    def _dfs(self, layout: Layout, g: int, threshold: int) -> int:
        self.nodes += 1
        if self._timed_out() or self.best_lb >= self.best:
            return 0
        estimate = g + self._lb(layout)
        if estimate > threshold:
            if estimate <= (self.best_lb + self.best) // 2:
                probe = _run_probe(layout, self.capacity, self.probe)
                if probe is not None and g + probe < self.best:
                    self.best = g + probe
            return estimate
        if estimate >= self.best:
            return estimate
        if not any(layout):
            if g < self.best:
                self.best = g
            return g
        min_child = INF
        for child in self._children(layout):
            child_lb = self._dfs(_normalize(child), g + 1, threshold)
            if child_lb < min_child:
                min_child = child_lb
        return INF if min_child == INF else max(estimate, min_child)


class ZhuIdaStarSolver(Solver):
    """Zhu et al. (2012) IDA* for the restricted or unrestricted CRP."""

    kind = "exact"
    priority_kind = "distinct"
    objective = "relocations"

    def __init__(
        self,
        name: str,
        restricted: bool = True,
        lower_bound: str = "LB3",
        probe: str = "PR3",
        description: str = "",
    ):
        if lower_bound not in {"LB1", "LB2", "LB3"}:
            raise ValueError("lower_bound must be LB1, LB2 or LB3")
        if probe not in _STEP_FNS and probe != "PR_plus":
            raise ValueError("probe must be PR1..PR4 or PR_plus")
        self.name = name
        self.restricted = restricted
        self.lower_bound = lower_bound
        self.probe = probe
        self.description = description

    def solve(
        self,
        inst: Instance,
        time_limit: Optional[float] = None,
        path: Optional[Path] = None,
    ) -> SolveOutcome:
        start = perf_counter()
        if not inst.distinct_priorities:
            return SolveOutcome(
                None,
                STATUS_ERROR,
                time_s=perf_counter() - start,
                extra={"error": "IDA* requires distinct priorities"},
            )
        layout = tuple(tuple(s) for s in inst.stacks)
        search = _Search(
            layout=layout,
            capacity=inst.max_tier,
            restricted=self.restricted,
            lower_bound=self.lower_bound,
            probe=self.probe,
            time_limit=time_limit,
            start=start,
        )
        try:
            value, proved = search.run()
        except _NoSolution as exc:
            return SolveOutcome(
                None,
                STATUS_ERROR,
                time_s=perf_counter() - start,
                extra={"error": str(exc), "nodes": search.nodes},
            )
        if value >= INF:
            return SolveOutcome(
                None,
                STATUS_TIMEOUT,
                time_s=perf_counter() - start,
                extra={"nodes": search.nodes, "lower_bound": search.lower_bound, "probe": search.probe},
            )
        return SolveOutcome(
            value,
            STATUS_OPTIMAL if proved else STATUS_BEST,
            time_s=perf_counter() - start,
            extra={
                "proved": proved,
                "nodes": search.nodes,
                "lower_bound": search.lower_bound,
                "probe": search.probe,
            },
        )

    @property
    def available(self) -> bool:
        return True
