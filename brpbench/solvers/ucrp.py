"""Adapter for the Jin & Tanaka (2023) unrestricted CRP branch-and-bound.

Binary ``main-solve``, vendored from https://github.com/jinboszu/ucrp-idbb
(official ``main`` branch, GPL-3.0). Reference:

    B. Jin, S. Tanaka. An exact algorithm for the unrestricted container
    relocation problem with new lower bounds and dominance rules.
    European Journal of Operational Research 304(2):494-514, 2023.

Two things differ from the Tanaka solvers (``tanaka.py``):

* **Input format.** ``main-solve`` reads ``n_stacks n_tiers n_blocks`` as its
  header -- the bay capacity is *explicit* in the file, unlike the standard
  Zhu/Tanaka format where it comes from the class directory. The instance is
  therefore serialized here rather than via ``Instance.to_text()``.
* **Output.** It writes to stdout a start/end report per run::

      [end] best_lb = 7 @ 0.000 / best_ub = 7 @ 0.000 / time = 0.000 / ...

  ``best_ub`` is the best feasible relocation count; ``best_lb == best_ub``
  means optimality was proven, otherwise the run hit the time limit.
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

LB_RE = re.compile(r"\bbest_lb\s*=\s*(\d+)")
UB_RE = re.compile(r"\bbest_ub\s*=\s*(\d+)")
TIME_RE = re.compile(r"\btime\s*=\s*([\d.]+)")

INT_MAX = 2_147_483_647
HARD_TIMEOUT_SLACK_S = 30.0


def _last(pattern: re.Pattern, text: str) -> Optional[int]:
    matches = pattern.findall(text)
    return int(matches[-1]) if matches else None


class JinTanakaSolver(Solver):
    kind = "exact"
    priority_kind = "distinct"

    def __init__(
        self,
        name: str,
        binary: os.PathLike | str,
        description: str = "",
    ):
        self.name = name
        self.binary = Path(binary)
        self.description = description

    @property
    def available(self) -> bool:
        return self.binary.exists() and os.access(self.binary, os.X_OK)

    @staticmethod
    def _serialize(inst: Instance) -> str:
        lines = [f"{inst.num_stacks} {inst.max_tier} {inst.num_blocks}"]
        for stack in inst.stacks:
            lines.append(" ".join(str(p) for p in (len(stack),) + tuple(stack)))
        return "\n".join(lines) + "\n"

    def solve(
        self,
        inst: Instance,
        time_limit: Optional[float] = None,
        path: Optional[Path] = None,
    ) -> SolveOutcome:
        if not self.available:
            return SolveOutcome(None, STATUS_ERROR, extra={"error": f"binary not found: {self.binary}"})

        tmp = None
        start = time.perf_counter()
        try:
            if path is not None:
                input_path = str(path)
            else:
                with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
                    fh.write(self._serialize(inst))
                    tmp = fh.name
                input_path = tmp
            args = [str(self.binary), "-i", input_path]
            if time_limit is not None:
                args += ["-t", str(max(1, int(time_limit)))]
            proc = self._run(args, time_limit)
        finally:
            if tmp is not None:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

        combined = (proc.stderr or "") + "\n" + (proc.stdout or "")
        wall_s = time.perf_counter() - start
        lb = _last(LB_RE, combined)
        ub = _last(UB_RE, combined)
        value = ub if (ub is not None and ub < INT_MAX) else None

        if value is None:
            status = STATUS_ERROR
        elif lb is not None and lb == ub:
            status = STATUS_OPTIMAL
        else:
            status = STATUS_BEST
        if proc.returncode is not None and proc.returncode < 0:
            status = STATUS_TIMEOUT

        reported = TIME_RE.search(combined)
        return SolveOutcome(
            value=value,
            status=status,
            time_s=float(reported.group(1)) if reported else wall_s,
            threads=1,
            extra={"returncode": proc.returncode, "wall_s": wall_s, "best_lb": lb, "stderr": (proc.stderr or "")[-2000:]},
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
