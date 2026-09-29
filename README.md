# BRP / CRP Benchmark Library

A standalone benchmark repository for the **Block / Container Relocation Problem
(BRP/CRP)**: the standard instances, a harness to run several published solvers,
the collected results, and a static site to browse and download everything.

This repo is independent from any application code. It is meant to be published
as a data + results website.

## What is the problem

Given a bay of `W` stacks with capacity `T` tiers holding `N` containers, each
with a retrieval priority, find the sequence of crane operations that retrieves
all containers in priority order while minimising the number of **relocations**
(containers moved out of the way). See the citations below.

Two common variants are covered:

* **distinct priorities** - every container has a unique priority.
* **duplicate / group priorities** - containers share priorities within a group.

## Datasets

| dataset | source | variants | instances |
|---|---|---|---|
| `zhu` | Zhu et al. (2012) | distinct priorities | 12,500 (125 classes x 100) |
| `tanaka_dup` | Tanaka & Takii (2016) | group priorities, `alpha` = 0.2/0.4/0.6/0.8 | 50,000 (4 x 125 classes x 100) |

Fetch them with:

```bash
make fetch          # or: python scripts/fetch_instances.py
```

### Instance format

```
W N
k1 p11 p12 ... p1k1
k2 p21 p22 ... p2k2
...
```

`W` stacks, `N` containers; each stack line gives its container count followed by
the priorities bottom -> top. Lines may contain `#` comments (the duplicate set
does). The **bay capacity is not in the file**: it is the first component of the
class directory name `T-S-C` (tiers, stacks, containers), e.g. `7-9-62` means
`T=7, S=9, C=62`. All classes satisfy `C in [T*S - T, T*S - 1]`.

## Solvers

Vendored from their authors (see `solvers/README.md` and each source header):

| name | reference | variant |
|---|---|---|
| `tanaka_restricted_distinct_1.3` | Tanaka & Voss (2022) | restricted, distinct |
| `tanaka_restricted_distinct_1.11` | Tanaka & Mizuno (2018) | restricted, distinct |
| `tanaka_unrestricted_distinct_1.01` | Tanaka & Mizuno (2018) | unrestricted, distinct |
| `jin_tanaka_restricted_distinct_jt23` | Jin & Tanaka (2023) | restricted, distinct |
| `jin_tanaka_unrestricted_distinct_jt23` | Jin & Tanaka (2023) | unrestricted, duplicate |
| `tanaka_restricted_duplicate_1.02` | Tanaka & Takii (2016) | restricted, group |
| `zhu_restricted_distinct_ida_2012` | Zhu et al. (2012) | restricted, distinct |
| `zhu_unrestricted_distinct_ida_2012` | Zhu et al. (2012) | unrestricted, distinct |
| `greedy` | this repo | constructive baseline (all datasets) |

The two `zhu_*` IDA\* solvers are an independent pure-Python reimplementation of
the paper (see `brpbench/solvers/ida_star.py`), like `greedy`; the remaining
solvers are vendored native binaries.

A full inventory of state-of-the-art algorithms (exact, heuristic, metaheuristic,
learning, multi-objective) with integration status lives in
[`docs/algorithms.md`](docs/algorithms.md).

Build the native binaries:

```bash
make solvers        # or: bash scripts/build_solvers.sh
```

The original C sources predate GCC's `-fno-common` default and declare globals in
headers, so they are compiled with `-fcommon`. The integer-programming solver
needs Boost + Gurobi and is skipped unless `GUROBI_ROOT` is set.

## Usage

```bash
# run one exact solver + the greedy baseline on 10 instances per class
python -m brpbench.run --dataset zhu --limit-per-class 10 --jobs 4 --time-limit 60 \
    --solver tanaka_restricted_distinct_1.3 --solver greedy --resume

# build the static site from results/results.jsonl
python -m brpbench.site
```

`--resume` skips `(instance, solver)` pairs already present, so long runs can be
restarted. Exact solvers are invoked with a per-instance time limit; when the
limit is hit the best feasible value is recorded with status `best`.

## Repository layout

```
brpbench/            Python package (parser, catalog, results, solvers, runner, site)
brpbench/solvers/    solver adapters + registry
solvers/             vendored native solver sources + build script
scripts/             fetch_instances.py, build_solvers.sh
instances/           datasets (downloaded; gitignored)
results/             results.jsonl (committed)
site/                generated static site (gitignored, deployable)
```

## Results schema

`results/results.jsonl`, one JSON object per `(instance, solver)` run:

```json
{"dataset":"zhu","alpha":null,"klass":"3-6-15","instance":"00001",
 "solver":"tanaka_restricted_distinct_1.3","value":7,"status":"optimal",
 "time_s":0.01,"threads":1,"time_limit_s":60,"source":"run","timestamp":"..."}
```

`status` is one of `optimal`, `best` (feasible, not proven), `feasible`
(heuristic), `timeout`, `error`.

## Licensing

* Harness code (`brpbench/`, `scripts/`): MIT (see `LICENSE`).
* Vendored solvers: retain their authors' licenses (BSD-style headers; the
  integer-programming solver is GPL-3.0). See `solvers/README.md`.
* Instances: distributed by their original authors for research use; cite the
  corresponding papers.

## References

* W. Zhu, H. Qin, A. Lim, H. Zhang. *Iterative deepening A\* algorithms for the
  container relocation problem.* IEEE T-ASE 9(4):710-722, 2012.
* S. Tanaka, K. Takii. *A faster branch-and-bound algorithm for the block
  relocation problem.* IEEE T-ASE 13(1):181-190, 2016.
* S. Tanaka, F. Mizuno. *An exact algorithm for the unrestricted block relocation
  problem.* Computers & Operations Research 95:12-31, 2018.
* S. Tanaka, S. Voss. *An exact approach to the restricted block relocation
  problem based on a new integer programming formulation.* EJOR 296(2):485-503, 2022.
* B. Jin, S. Tanaka. *An exact algorithm for the unrestricted container
  relocation problem with new lower bounds and dominance rules.* EJOR
  304(2):494-514, 2023.
* M. Caserta, S. Voss, M. Sniedovich. *Applying the corridor method to a blocks
  relocation problem.* OR Spectrum 33:915-929, 2011.

Instance mirrors: <https://sites.google.com/site/shunjitanaka/brp>,
<http://www.zhuwb.com/crp>.
