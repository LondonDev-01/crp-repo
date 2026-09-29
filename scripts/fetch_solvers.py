#!/usr/bin/env python3
"""Clone external (mostly GPL-3) solver sources into solvers/external/.

These are kept out of the repository to avoid mixing licenses: the harness is
permissive, the solvers are not. They are cloned on demand and built by
scripts/build_solvers.sh.

Usage:
    python scripts/fetch_solvers.py [--force]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = REPO_ROOT / "solvers" / "external"

SOLVERS = {
    "block-relocation": {
        "url": "https://github.com/fa-bien/block-relocation.git",
        "license": "GPL-3.0",
        "note": "Tricoire, Scagnetti & Beham (2018) heuristics + metaheuristics + DFBB (C++14)",
    },
    "crp-glah": {
        "url": "https://github.com/jinboszu/crp-glah.git",
        "license": "GPL-3.0",
        "note": "Jin, Zhu & Lim (2015) GLAH heuristic (Java 8)",
    },
    "block-relocation-problem": {
        "url": "https://github.com/rubenlej/block-relocation-problem.git",
        "license": "MIT",
        "note": "reactive GRASP minimising crane working time (Java)",
    },
    "ucrp-java": {
        "url": "https://github.com/jinboszu/ucrp-java.git",
        "license": "GPL-3.0",
        "note": "Java port of the JT23 unrestricted duplicate IDB&B",
    },
}


def fetch(name: str, spec: dict, force: bool) -> None:
    dest = EXTERNAL / name
    if dest.exists() and not force:
        print(f"[{name}] already present ({spec['license']})")
        return
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        import shutil

        shutil.rmtree(dest)
    print(f"[{name}] cloning {spec['url']} ({spec['license']})")
    subprocess.run(["git", "clone", "--depth", "1", spec["url"], str(dest)], check=True)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Fetch external solver sources.")
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)
    for name, spec in SOLVERS.items():
        try:
            fetch(name, spec, args.force)
        except subprocess.CalledProcessError as exc:
            print(f"[{name}] clone failed: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
