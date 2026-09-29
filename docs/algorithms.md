# State of the art: algorithms for the Block / Container Relocation Problem

Living inventory used to drive solver integration. Status legend:

- **integrated** — vendored/adapted and runnable through `brpbench.run`.
- **available** — open-source implementation exists and is a candidate to integrate.
- **reimplement** — no public code; would need an implementation here.
- **literature** — results only (used for curated comparisons, not executed).

Objective legend: `R` = number of relocations, `T` = crane working time / travel
distance, `E` = energy, `MO` = multi-objective (Pareto).

Variants: **rBRP** restricted (Assumption A1, only blockers of the target move),
**uBRP** unrestricted, **dup** duplicate/group priorities, **SP** stowage plan.

Primary survey: Lersteau & Shen (2022), *A survey of optimization methods for
block relocation and premarshalling problems*, Computers & Industrial
Engineering 172:108529. Recent systematic review: Zhou et al. (2026), *Container
relocation problem: a systematic review and bibliometric analysis*.

## 1. Mathematical formulations

| method | reference | variant | obj | availability |
|---|---|---|---|---|
| MRIP | Wan, Liu & Tang (2009) | rBRP | R | literature; models reimplemented in `jinboszu/crp-ip` |
| BRP-I / BRP-II | Caserta, Voß & Sniedovich (2012) | uBRP / rBRP | R | literature; `crp-ip` |
| BRP-II* | Expósito-Izquierdo, Melián-Batista & Moreno-Vega (2015) | rBRP | R | literature; `crp-ip` |
| BRP-II-A | Zehendner, Caserta, Feillet, Schwarze & Voß (2015) | rBRP | R | literature; `crp-ip` |
| CRP-I (binary encoding) | Galle, Barnhart & Jaillet (2018) | rBRP | R | literature; `crp-ip` |
| BRP-III | Petering & Hussein (2013) | uBRP | R | literature; `crp-ip` |
| BRP-m1 / BRP-m2 | de Melo da Silva, Toulouse & Wolfler Calvo (2018) | uBRP, dup | R | literature |
| BRP-m3 (adjacency) | Lu et al. (2020) | 8 variants | R | literature; `crp-ip` |
| Relocation-sequence IP | Tanaka & Voß (2022) | rBRP | R | **integrated** (`tanaka_restricted_distinct_ip_1.0`, needs Gurobi) |
| Branch-and-price | Zehendner & Feillet (2014) | rBRP | R | literature |
| Column generation | Zehendner & Feillet (2014) | rBRP | R | literature |
| Multi-objective ILP (slab warehouse) | Ge et al. (2022) | SLP+PMP | MO | literature |

## 2. Tree-search / exact

| method | reference | variant | obj | availability |
|---|---|---|---|---|
| Depth-first B&B + DP | Kim & Hong (2006) | rBRP | R | literature |
| IDA* (LB1/LB2/LB3) | Zhu, Qin, Lim & Zhang (2012) | r/uBRP | R | **integrated** (`zhu_restricted_distinct_ida_2012`, `zhu_unrestricted_distinct_ida_2012`; reimplemented from the paper, not vendored) |
| B&B | Tanaka & Takii (2016) | rBRP, distinct | R | **integrated** (`tanaka_restricted_distinct_1.11`) |
| B&B | Tanaka & Takii (2016) | rBRP, dup | R | **integrated** (`tanaka_restricted_duplicate_1.01`) |
| B&B | Tanaka & Mizuno (2018) | uBRP, distinct | R | **integrated** (`tanaka_unrestricted_distinct_1.01`) |
| IDB&B + dominance | Jin & Tanaka (2023) | uBRP, dup | R | **integrated** (`jin_tanaka_unrestricted_distinct_jt23`) |
| IDB&B | Jin & Tanaka (2023) | rBRP, distinct | R | **integrated** (`jin_tanaka_restricted_distinct_jt23`) |
| B&B (new LBs) | Quispe, Lintzmayer & Xavier (2018) | rBRP | R | literature |
| B&C (compact model) | Bacci, Mattia & Ventura (2020) | rBRP | R | literature |
| Bounded beam search | Bacci, Mattia & Ventura (2019) | rBRP | R | literature |
| Corridor method | Caserta, Voß & Sniedovich (2011) | rBRP | R | literature |
| A* (CRP with storage plan) | Tanaka & Voß (2019) | SP | R | literature |
| DFBB / DFBB-L | Tricoire, Scagnetti & Beham (2018) | uBRP | R | `fa-bien/block-relocation` (C++14, GPL-3) |

## 3. Heuristics

| method | reference | variant | obj | availability |
|---|---|---|---|---|
| Greedy + expected reshuffle index | Kim & Hong (2006) | rBRP | R | **integrated** (`greedy`, baseline) |
| Reshuffle index / MinMax rules | Ku & Arthanari | rBRP | R | reimplement |
| Beam search | Wu & Ting (2010); Ting & Wu (2017) | rBRP | R | reimplement |
| Corridor method | Caserta et al. (2011) | rBRP | R | reimplement |
| Domain-knowledge heuristic | Expósito-Izquierdo et al. (2014) | rBRP | R | reimplement |
| Chain heuristic (ChainF) | Jovanovic & Voß (2014) | rBRP | R | reimplement |
| GLAH (greedy look-ahead) | Jin, Zhu & Lim (2015) | rBRP | R | `jinboszu/crp-glah` (Java 8, GPL-3) |
| LA-N (look-ahead) | Petering & Hussein (2013) | rBRP | R | `fa-bien/block-relocation` |
| SM-1 / SM-2 / SmSEQ-1 / SmSEQ-2 | Tricoire, Scagnetti & Beham (2018) | uBRP | R | `fa-bien/block-relocation` |
| Pilot method (PM) | Tricoire et al. (2018) | uBRP | R | `fa-bien/block-relocation` |
| Rake search (RS) | Tricoire et al. (2018) | uBRP | R | `fa-bien/block-relocation` |
| Three-stage heuristic (3SH) | Zhu et al. (2024) | rBRP | R | reimplement |
| Relocation rules (RR) + GP | Đurasević & Đumić (2022) | rBRP/uBRP | R, T | `jivancevic/cgp-block-relocation-problem` (CGP, MIT) |

## 4. Metaheuristics and learning

| method | reference | variant | obj | availability |
|---|---|---|---|---|
| Tabu search | Wu et al. (2010) | rBRP | R | reimplement |
| Ant colony optimization | Jovanovic, Tuba & Voß (2019) | r/uBRP | R, T | `jiholee255/ACO_BRP` (Python, no license) |
| Reactive GRASP | da Silva Firmino et al.; Lej et al. | r/uBRP | R, T | `rubenlej/block-relocation-problem` (Java, MIT) |
| Local search (Feillet et al. 2019) | Feillet, Parragh & Tricoire (2019) | uBRP | R | `fa-bien/block-relocation` |
| Genetic programming / hyperheuristics | Đurasević & Đumić (2022) | r/uBRP | R, T, E | `jivancevic/cgp-block-relocation-problem` |
| Variable neighborhood search | Wang et al. (2024, refrigerated) | dup | R | reimplement |
| Q-learning | Liu, Feng, Zeng, Chen & Li (2025) | rBRP dup | R | reimplement |
| RL (PPO) + A* | Wang et al. (2025) | SP | R | reimplement |
| ML-driven B&B speedup | Zhang et al. (2020) | rBRP | R | reimplement |

## 5. Multi-objective / energy / crane time

The multi-objective side is **far less standardized** than the single-objective
one: there is no canonical benchmark with energy parameters. The review above
explicitly notes that energy consumption remains understudied.

| objective pair | reference | variant | notes |
|---|---|---|---|
| relocations vs crane working time | Voß & Schwarze; Lej et al.; Tricoire et al. | r/uBRP | crane time derived from stack geometry, parameter-free |
| energy consumption (single) | Covic; Đurasević, Đumić, Čorić & Gil-Gala (2023) | r/uBRP | energy = Σ weight·(tiers + stacks crossed); needs container weights + crane params |
| energy-aware relocation rules (GP) | Đurasević et al. (2023) | r/uBRP | priority functions evolved to minimise energy |
| used stacks / blockages / relocations | Ge et al. (2022) | SLP+PMP | weighted-sum ILP |
| makespan vs energy (QCSP, not CRP) | Li & Li (2022) | quay cranes | bi-objective B&B, related problem |
| (energy, relocations) bi-objective | local `crp` project | rBRP | BOA*; see that repo for the model |

Open design question: to benchmark multi-objective algorithms we must fix the
objective model (which second objective, and how energy is parameterised) since
none of the standard instance sets carry energy data. See `docs/multiobjective.md`.

## Integration priorities

1. **Exact, easy builds**: `fa-bien/block-relocation` (C++14, fetched via
   `scripts/fetch_solvers.py`). `jinboszu/rcrp-idbb` and `ucrp-idbb` are already
   vendored and integrated.
2. **Heuristics with broad coverage**: Beham et al. methods above (one binary,
   many `-m` methods) give ~10 heuristics in a single integration.
3. **Java**: `jinboszu/crp-glah`, `jinboszu/ucrp-java`, `rubenlej/block-relocation-problem`.
4. **Python**: `jivancevic/cgp-block-relocation-problem`, `jiholee255/ACO_BRP`
   (no license — keep external, do not vendor). IDA\* was reimplemented from the
   paper instead of vendoring `KeelyXu/IDA-STAR-for-CRP` (unlicensed).
5. **Multi-objective**: define the objective model, then implement Pareto-capable
   solvers (NSGA-II style) on top of the relocation machinery.

## Licensing

Most integrated solvers are **GPL-3.0** (`rcrp-idbb`, `ucrp-idbb`, `ucrp-java`,
`crp-glah`, `fa-bien/block-relocation`, Tanaka's IP solver). Vendoring them means
the combined repository must be distributed under GPL-3.0. Two options:

- distribute the whole repo under GPL-3.0, or
- keep GPL solvers as **external** downloads (fetched, not vendored) and keep the
  harness permissive.

Repos without a license (`IDA-STAR-for-CRP`, `ACO_BRP`) must not be vendored.
