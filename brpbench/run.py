"""CLI: run one or more solvers over discovered instances and store results."""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .catalog import InstanceRef, iter_refs, load
from .results import Result, ResultStore


def _run_one(ref: InstanceRef, solver_name: str, time_limit: Optional[float]):
    from .solvers import build_registry

    solver = build_registry()[solver_name]
    inst = load(ref)
    if not solver.supports(inst):
        return None
    outcome = solver.solve(inst, time_limit=time_limit, path=ref.path)
    return Result(
        dataset=ref.dataset,
        alpha=ref.alpha,
        klass=ref.klass,
        instance=ref.name,
        solver=solver_name,
        value=outcome.value,
        status=outcome.status,
        time_s=outcome.time_s,
        threads=outcome.threads,
        time_limit_s=time_limit,
        source="run",
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        extra=outcome.extra,
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="brpbench.run", description="Run BRP solvers over benchmark instances.")
    p.add_argument("--instances-root", default="instances")
    p.add_argument("--results", default="results/results.jsonl")
    p.add_argument("--dataset", action="append", default=[])
    p.add_argument("--class", dest="klass", action="append", default=[])
    p.add_argument("--alpha", action="append", default=[])
    p.add_argument("--solver", action="append", default=[])
    p.add_argument("--limit-per-class", type=int, default=None)
    p.add_argument("--time-limit", type=float, default=None)
    p.add_argument("--jobs", type=int, default=1)
    p.add_argument("--resume", action="store_true", help="skip (instance, solver) pairs already in results")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    from .solvers import build_registry

    registry = build_registry()
    solver_names = args.solver or sorted(registry)
    unknown = [s for s in solver_names if s not in registry]
    if unknown:
        print(f"unknown solvers: {unknown}. Available: {sorted(registry)}", file=sys.stderr)
        return 2

    refs = list(
        iter_refs(
            args.instances_root,
            datasets=args.dataset or None,
            klasses=args.klass or None,
            alphas=args.alpha or None,
            limit_per_class=args.limit_per_class,
        )
    )
    if not refs:
        print(f"no instances found under {args.instances_root}", file=sys.stderr)
        return 1

    store = ResultStore(args.results)
    if args.resume:
        store.load()

    tasks = []
    for ref in refs:
        for name in solver_names:
            if args.resume and store.has(ref.dataset, ref.alpha, ref.klass, ref.name, name):
                continue
            tasks.append((ref, name))

    print(f"{len(refs)} instances x {len(solver_names)} solvers -> {len(tasks)} runs", file=sys.stderr)
    if not tasks:
        return 0

    done = 0
    with ProcessPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = {pool.submit(_run_one, ref, name, args.time_limit): (ref, name) for ref, name in tasks}
        for fut in as_completed(futures):
            ref, name = futures[fut]
            try:
                result = fut.result()
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR {ref.key} [{name}]: {exc}", file=sys.stderr)
                continue
            if result is None:
                continue
            store.upsert(result)
            done += 1
            print(f"[{done}/{len(tasks)}] {ref.key} [{name}] -> {result.value} ({result.status})", file=sys.stderr)

    store.write()
    print(f"wrote {len(store)} results to {args.results}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
