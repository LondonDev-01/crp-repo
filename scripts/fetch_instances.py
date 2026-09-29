#!/usr/bin/env python3
"""Download and unpack the BRP benchmark datasets.

Sources (Google Drive mirrors published by their authors):

* ``zhu``        - Zhu et al. (2012), distinct priorities, 12,500 instances.
* ``tanaka_dup`` - Tanaka & Takii (2016), duplicate (group) priorities, 50,000
                   instances, four group-ratio levels (alpha = 0.2/0.4/0.6/0.8).

Usage:
    python scripts/fetch_instances.py [--root instances] [--force]
"""

from __future__ import annotations

import argparse
import io
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

DATASETS = {
    "zhu": {
        "id": "1vA7YBQLvgLg5fop5M6txJbN8AD33AAi8",
        "expected_files": 12500,
        "note": "Zhu et al. (2012) distinct priorities",
    },
    "tanaka_dup": {
        "id": "1Pw9EINDhgD2taFF3RIULQoaW2-HNm5-5",
        "expected_files": 50000,
        "note": "Tanaka & Takii (2016) duplicate priorities",
    },
}

DOWNLOAD_URL = "https://drive.usercontent.google.com/download?id={id}&export=download&confirm=t"


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 brpbench"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.read()


def fetch(name: str, spec: dict, root: Path, force: bool) -> None:
    target = root / name
    if target.exists() and any(target.iterdir()) and not force:
        count = sum(1 for _ in target.rglob("*.txt"))
        print(f"[{name}] already present ({count} files); use --force to redownload")
        return

    print(f"[{name}] downloading {spec['note']} ...")
    blob = download(DOWNLOAD_URL.format(id=spec["id"]))
    if not blob[:2] == b"PK":
        raise RuntimeError(f"[{name}] download is not a zip (got {blob[:16]!r}); Google Drive may have changed its link")

    if target.exists() and force:
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        zf.extractall(target)

    count = sum(1 for _ in target.rglob("*.txt"))
    print(f"[{name}] extracted {count} instances into {target}")
    expected = spec["expected_files"]
    if count != expected:
        print(f"[{name}] WARNING: expected {expected} instances, found {count}", file=sys.stderr)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Fetch BRP benchmark datasets.")
    p.add_argument("--root", default=str(REPO_ROOT / "instances"))
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)

    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    for name, spec in DATASETS.items():
        fetch(name, spec, root, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
