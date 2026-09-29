"""Adapter for the compiled Tanaka branch-and-bound / IP solvers.

Each solver is a native binary that reads an instance file and writes machine
readable lines to stderr:

    opt=<value>      optimal solution found
    best=<value>     best feasible solution (time limit reached)
    time=<seconds>   reported CPU time
    threads=<n>      worker threads (OpenMP builds only)

The bay capacity is enforced through the solver flags:

* ``capacity_mode="T"`` passes ``-T <tiers>`` (used by the duplicate-priority
  solver, which only exposes a stack-height flag).
* ``capacity_mode="E"`` passes ``-E <tiers - initial_height>`` (used by the
  distinct-priority solvers; ``-E 0`` for the Zhu instances, whose stacks are
  filled up to the capacity).
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

from ..instance import Instance
from ..results import STATUS_BEST, STATUS_ERROR, STATUS_OPTIMAL, STATUS_TIMEOUT
from .base import SolveOutcome, Solver

OPT_RE = re.compile(r"\bopt=(\d+)")
BEST_RE = re.compile(r"\bbest=(\d+)")
TIME_RE = re.compile(r"\btime=([\d.]+)")
THREADS_RE = re.compile(r"\bthreads=(\d+)")

HARD_TIMEOUT_SLACK_S = 30.0


class TanakaSolver(Solver):
    kind = "exact"

    def __init__(
        self,
        name: str,
        binary: os.PathLike | str,
        capacity_mode: str,
        priority_kind: str = "any",
        description: str = "",
    ):
        if capacity_mode not in {"T", "E"}:
            raise ValueError("capacity_mode must be 'T' or 'E'")
        self.name = name
        self.binary = Path(binary)
        self.capacity_mode = capacity_mode
        self.priority_kind = priority_kind
        self.description = description

    @property
    def available(self) -> bool:
        return self.binary.exists() and os.access(self.binary, os.X_OK)

    def _capacity_args(self, inst: Instance) -> list:
        if self.capacity_mode == "T":
            return ["-T", str(inst.max_tier)]
        return ["-E", str(max(0, inst.max_tier - inst.initial_height))]

    def solve(
        self,
        inst: Instance,
        time_limit: Optional[float] = None,
        path: Optional[Path] = None,
    ) -> SolveOutcome:
        if not self.available:
            return SolveOutcome(None, STATUS_ERROR, extra={"error": f"binary not found: {self.binary}"})

        args = [str(self.binary)] + self._capacity_args(inst)
        if time_limit is not None:
            args += ["-t", str(max(1, int(time_limit)))]

        tmp = None
        start = time.perf_counter()
        try:
            if path is not None:
                args.append(str(path))
                proc = self._run(args, time_limit)
            else:
                with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
                    fh.write(inst.to_text())
                    tmp = fh.name
                args.append(tmp)
                proc = self._run(args, time_limit)
        finally:
            if tmp is not None:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

        stderr = proc.stderr or ""
        stdout = proc.stdout or ""
        wall_s = time.perf_counter() - start
        combined = stderr + "\n" + stdout
        value = None
        status = STATUS_ERROR
        if OPT_RE.search(combined):
            value = int(OPT_RE.search(combined).group(1))
            status = STATUS_OPTIMAL
        elif BEST_RE.search(combined):
            value = int(BEST_RE.search(combined).group(1))
            status = STATUS_BEST
        if proc.returncode is not None and proc.returncode < 0:
            status = STATUS_TIMEOUT

        reported = TIME_RE.search(combined)
        threads = THREADS_RE.search(combined)
        return SolveOutcome(
            value=value,
            status=status,
            time_s=float(reported.group(1)) if reported else wall_s,
            threads=int(threads.group(1)) if threads else None,
            extra={"returncode": proc.returncode, "wall_s": wall_s, "stderr": stderr[-2000:]},
        )

    def _run(self, args, time_limit):
        hard = None if time_limit is None else time_limit + HARD_TIMEOUT_SLACK_S
        try:
            return subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=hard,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            class _P:
                returncode = -1
                stdout = (exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
                stderr = (exc.stderr or b"").decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")

            return _P()
