# Vendored solvers

Third-party sources, unmodified except for build flags. Each keeps its own
license in the file headers.

| directory | binary | reference | license |
|---|---|---|---|
| `tanaka_restricted_distinct_1.3` | `rbrp_bb` | Tanaka & Voss (2022) | see headers (BSD-style) |
| `tanaka_restricted_distinct_1.11` | `brp_bb` | Tanaka & Mizuno (2018) | see headers (BSD-style) |
| `tanaka_unrestricted_distinct_1.01` | `ubrp_bb` | Tanaka & Mizuno (2018) | see headers (BSD-style) |
| `tanaka_restricted_duplicate_1.02` | `brp_bb` | Tanaka & Takii (2016) | see headers (BSD-style) |
| `tanaka_restricted_distinct_ip_1.0` | `rbrp_ip` | Tanaka & Voss (2022) | GPL-3.0 (needs Boost + Gurobi) |
| `ucrp_idbb_jt23` | `main-solve` | Jin & Tanaka (2023) | GPL-3.0 |

Sources: <https://sites.google.com/site/shunjitanaka/brp>,
<https://github.com/jinboszu/ucrp-idbb>

## Build notes

The C sources declare globals in headers (`uchar verbose;` etc.). Modern GCC
defaults to `-fno-common`, which makes those tentative definitions collide at
link time. Compile with `-fcommon`:

```bash
bash ../scripts/build_solvers.sh
```

## CLI summary

All binaries read an instance file (or stdin) and write results to stderr:

* `brp_bb` / `rbrp_bb` / `ubrp_bb`: `-v|-s`, `-E E` (extra empty tiers),
  `-S S`, `-T T`, `-t L` (time limit), `-b` (backtrack, v1.3), `-m M`
  (threads, OpenMP build).
* `rbrp_ip`: `-E E`, `-t L`; needs `GUROBI_ROOT`.
* `main-solve` (JT23): `-i input_file`, `-t L`. Unlike the others it does **not**
  read stdin and its header is `n_stacks n_tiers n_blocks` (capacity explicit in
  the file). Writes a start/end report to stdout with `best_lb = ...` and
  `best_ub = ...`; `best_lb == best_ub` means proven optimal.

Output lines (Tanaka binaries): `opt=<value>` (proven optimal) or `best=<value>`
(time limit), plus `time=<seconds>` and `threads=<n>`.

## Capacity convention

For the Zhu dataset pass `-E 0` (stacks are filled up to capacity). For the
duplicate Tanaka dataset pass `-T <tiers>`. `brpbench.solvers` handles this
automatically via the class directory name. The JT23 solver takes the capacity
directly in its input header, so the adapter serializes it explicitly.
