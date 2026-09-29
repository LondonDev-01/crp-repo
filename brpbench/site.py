"""CLI: render a static HTML site from the collected results."""

from __future__ import annotations

import argparse
import csv
import html
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .results import STATUS_OPTIMAL, Result, ResultStore

GroupKey = Tuple[str, Optional[str], str]


def _is_solved(result: Result) -> bool:
    return result.value is not None


def _mean(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def _fmt(value: Optional[float], digits: int = 2) -> str:
    return "" if value is None else f"{value:.{digits}f}"


def aggregate(results: List[Result]):
    by_solver: Dict[Tuple[GroupKey, str], List[Result]] = defaultdict(list)
    by_instance: Dict[Tuple[GroupKey, str], Dict[str, int]] = defaultdict(dict)
    for r in results:
        group: GroupKey = (r.dataset, r.alpha, r.klass)
        by_solver[(group, r.solver)].append(r)
        if r.value is not None:
            current = by_instance[group].get(r.instance)
            if current is None or r.value < current:
                by_instance[group][r.instance] = r.value
    return by_solver, by_instance


def solver_stats(rows: List[Result]) -> dict:
    solved = [r for r in rows if _is_solved(r)]
    values = [r.value for r in solved]
    times = [r.time_s for r in rows if r.time_s is not None]
    optimal = sum(1 for r in solved if r.status == STATUS_OPTIMAL)
    return {
        "n": len(rows),
        "solved": len(solved),
        "mean_value": _mean(values),
        "min_value": min(values) if values else None,
        "max_value": max(values) if values else None,
        "optimal_pct": (optimal / len(rows) * 100) if rows else None,
        "mean_time_s": _mean(times),
    }


def build_summary(results: List[Result]):
    by_solver, by_instance = aggregate(results)
    solvers = sorted({r.solver for r in results})
    groups = sorted({(r.dataset, r.alpha, r.klass) for r in results})
    summary = []
    for group in groups:
        best = by_instance.get(group, {})
        for solver in solvers:
            rows = by_solver.get((group, solver))
            if not rows:
                continue
            stats = solver_stats(rows)
            gaps = []
            for r in rows:
                if r.value is None:
                    continue
                known = best.get(r.instance)
                if known is not None and known > 0:
                    gaps.append((r.value - known) / known * 100)
            stats.update(
                {
                    "dataset": group[0],
                    "alpha": group[1],
                    "klass": group[2],
                    "solver": solver,
                    "mean_gap_pct": _mean(gaps),
                }
            )
            summary.append(stats)
    return summary, solvers, groups


def write_csv(path: Path, summary: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "dataset",
        "alpha",
        "klass",
        "solver",
        "n",
        "solved",
        "mean_value",
        "min_value",
        "max_value",
        "optimal_pct",
        "mean_gap_pct",
        "mean_time_s",
    ]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in summary:
            writer.writerow({k: row.get(k) for k in fields})


def render_html(summary: List[dict], solvers: List[str], groups, title: str) -> str:
    datasets = sorted({g[0] for g in groups})
    alphas = sorted({g[1] for g in groups if g[1] is not None})

    def opts(values):
        return "".join(f'<option value="{html.escape(str(v))}">{html.escape(str(v))}</option>' for v in values)

    rows_html = []
    for row in sorted(summary, key=lambda r: (r["dataset"], r["alpha"] or "", r["klass"], r["solver"])):
        rows_html.append(
            "<tr data-dataset='{ds}' data-alpha='{al}' data-solver='{sv}'>"
            "<td>{ds}</td><td>{al}</td><td>{kl}</td><td>{sv}</td>"
            "<td class='num'>{n}</td><td class='num'>{solved}</td>"
            "<td class='num'>{mean_value}</td><td class='num'>{min_value}</td>"
            "<td class='num'>{optimal_pct}</td><td class='num'>{mean_gap_pct}</td>"
            "<td class='num'>{mean_time_s}</td></tr>".format(
                ds=html.escape(row["dataset"]),
                al=html.escape(row["alpha"] or ""),
                kl=html.escape(row["klass"]),
                sv=html.escape(row["solver"]),
                n=row["n"],
                solved=row["solved"],
                mean_value=_fmt(row["mean_value"]),
                min_value=row["min_value"] if row["min_value"] is not None else "",
                optimal_pct=_fmt(row["optimal_pct"], 1),
                mean_gap_pct=_fmt(row["mean_gap_pct"], 2),
                mean_time_s=_fmt(row["mean_time_s"], 3),
            )
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root {{ color-scheme: light dark; }}
body {{ font: 14px/1.5 system-ui, sans-serif; margin: 2rem auto; max-width: 1100px; padding: 0 1rem; }}
h1 {{ font-size: 1.5rem; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
th, td {{ border-bottom: 1px solid #8884; padding: .35rem .5rem; text-align: left; }}
th {{ position: sticky; top: 0; background: Canvas; cursor: pointer; }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.filters {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0; }}
.filters label {{ display: flex; flex-direction: column; font-size: .8rem; gap: .2rem; }}
code {{ background: #8882; padding: .1rem .3rem; border-radius: 4px; }}
</style>
</head>
<body>
<h1>{html.escape(title)}</h1>
<p>Per-class solver comparison. <strong>mean_value</strong> is the average number of
relocations over the instances in the class; <strong>optimal%</strong> counts solutions
proven optimal; <strong>gap%</strong> is the average relative gap to the best value found
by any solver on the same instance. Downloads:
<a href="data/results.json">results.json</a> &middot;
<a href="data/summary.csv">summary.csv</a></p>

<div class="filters">
  <label>Dataset <select id="f-dataset"><option value="">all</option>{opts(datasets)}</select></label>
  <label>Alpha <select id="f-alpha"><option value="">all</option>{opts(alphas)}</select></label>
  <label>Solver <select id="f-solver"><option value="">all</option>{opts(solvers)}</select></label>
</div>

<table id="t">
<thead><tr>
  <th>dataset</th><th>alpha</th><th>class</th><th>solver</th>
  <th class="num">n</th><th class="num">solved</th><th class="num">mean value</th>
  <th class="num">best</th><th class="num">optimal %</th><th class="num">gap %</th>
  <th class="num">mean time (s)</th>
</tr></thead>
<tbody>
{''.join(rows_html)}
</tbody>
</table>

<script>
const rows = [...document.querySelectorAll('#t tbody tr')];
function apply() {{
  const ds = document.getElementById('f-dataset').value;
  const al = document.getElementById('f-alpha').value;
  const sv = document.getElementById('f-solver').value;
  for (const r of rows) {{
    const ok = (!ds || r.dataset.dataset === ds) && (!al || r.dataset.alpha === al) && (!sv || r.dataset.solver === sv);
    r.style.display = ok ? '' : 'none';
  }}
}}
for (const id of ['f-dataset', 'f-alpha', 'f-solver']) document.getElementById(id).addEventListener('change', apply);
document.querySelectorAll('#t th').forEach((th, i) => th.addEventListener('click', () => {{
  const tbody = document.querySelector('#t tbody');
  const sorted = [...tbody.querySelectorAll('tr')].sort((a, b) => {{
    const x = a.children[i].textContent.trim(), y = b.children[i].textContent.trim();
    const nx = parseFloat(x), ny = parseFloat(y);
    if (!isNaN(nx) && !isNaN(ny)) return nx - ny;
    return x.localeCompare(y);
  }});
  sorted.forEach(r => tbody.appendChild(r));
}}));
</script>
</body>
</html>
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="brpbench.site", description="Build the static results site.")
    p.add_argument("--results", default="results/results.jsonl")
    p.add_argument("--out", default="site")
    p.add_argument("--title", default="BRP / CRP benchmark results")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    store = ResultStore(args.results).load()
    results = list(store.values())
    out = Path(args.out)
    (out / "data").mkdir(parents=True, exist_ok=True)

    summary, solvers, groups = build_summary(results)
    write_csv(out / "data" / "summary.csv", summary)
    with open(out / "data" / "results.json", "w", encoding="utf-8") as fh:
        json.dump([r.__dict__ for r in results], fh, indent=2, sort_keys=True)
    (out / "index.html").write_text(render_html(summary, solvers, groups, args.title), encoding="utf-8")
    print(f"wrote {out/'index.html'} ({len(results)} results, {len(summary)} summary rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
