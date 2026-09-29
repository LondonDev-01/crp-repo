# Multi-objective benchmarking: open design decisions

Unlike the single-objective side, there is **no canonical multi-objective BRP
benchmark** with published Pareto fronts. To benchmark multi-objective algorithms
we must first fix the objective model, because the standard instance sets carry
only priorities.

## What the harness already supports

`brpbench` result records now carry:

- `objective`: name of the primary objective (`relocations` for all current solvers).
- `objectives`: list of objective names for multi-objective solvers.
- `points`: the Pareto front as a list of objective vectors.

`Solver` exposes `objective` / `objectives` / `is_multi_objective`, and
`SolveOutcome` carries `objectives` + `points`. No multi-objective solver is
implemented yet.

## Decision 1 — which second objective?

| option | second objective | parameters needed | literature precedent |
|---|---|---|---|
| A | crane working time / travel distance | none (derived from stack/tier geometry) | Voß & Schwarze; Lej et al.; Tricoire et al. |
| B | energy consumption | container weights, crane weight, e_x/e_y, exit column | Covic; Đurasević et al. (2023) |
| C | number of stacks used / blockages | none | Ge et al. (2022) |

Option **A** is the only parameter-free choice and therefore the only one that can
run on the existing Zhu/Tanaka instances unchanged. Option **B** matches the
`crp` project's energy model but needs a parameter convention that we would be
defining ourselves (a research contribution, not a reproduction).

## Decision 2 — how to parameterise energy (only if B)

- fixed `(e_x, e_y)` per run and sweep? or per-instance random?
- `exit_column` at a bay end (0) or centre?
- container weights: unit, or random in a range?

## Decision 3 — solver families

- **exact bi-objective**: bi-objective A* / label-setting over `(relocations, X)`
  (like `crp`'s BOA*) — gives exact fronts on small instances.
- **metaheuristics**: NSGA-II / SPEA2 / MOEA/D with a relocation-sequence
  encoding; measure hypervolume, IGD, spread.
- **scalarised baselines**: weighted-sum A* for reference points.

## Decision 4 — metrics

Per instance, store the front plus derived metrics: hypervolume (needs a
reference point), number of non-dominated points, spread. Store the reference
point used so comparisons are reproducible.

## Recommendation

Start with **Option A** (relocations vs crane working time) because it needs no
invented parameters and has literature precedent, so results are comparable.
Add Option B later as a separate objective profile with an explicit, documented
energy convention.
