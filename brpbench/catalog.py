"""Discovery of BRP instance files on disk.

Expected layout under the instances root (nesting is flexible):

    <root>/<dataset>/<class>/<name>.txt
    <root>/<dataset>/<alpha>/<class>/<name>.txt

``<class>`` must match ``T-S-C`` (tiers, stacks, containers); the first
component is the bay capacity passed to solvers.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Sequence

from .instance import CLASS_RE, Instance, load_instance, parse_class

ALPHA_RE = re.compile(r"^alpha=(.+)$")


@dataclass(frozen=True)
class InstanceRef:
    path: Path
    dataset: str
    klass: str
    name: str
    tiers: int
    stacks: int
    containers: int
    alpha: Optional[str] = None

    @property
    def key(self) -> str:
        parts = [self.dataset]
        if self.alpha is not None:
            parts.append(f"alpha={self.alpha}")
        parts.extend([self.klass, self.name])
        return "/".join(parts)


def _classify(rel_parts: Sequence[str]) -> Optional[tuple]:
    dataset = rel_parts[0] if rel_parts else ""
    alpha = None
    klass = None
    for part in rel_parts[1:]:
        m = ALPHA_RE.match(part)
        if m:
            alpha = m.group(1)
            continue
        if CLASS_RE.match(part):
            klass = part
    if klass is None:
        return None
    return dataset, alpha, klass


def iter_refs(
    root: os.PathLike | str,
    *,
    datasets: Optional[Iterable[str]] = None,
    klasses: Optional[Iterable[str]] = None,
    alphas: Optional[Iterable[str]] = None,
    limit_per_class: Optional[int] = None,
) -> Iterator[InstanceRef]:
    root = Path(root)
    if not root.exists():
        return
    dataset_filter = set(datasets) if datasets else None
    klass_filter = set(klasses) if klasses else None
    alpha_filter = set(alphas) if alphas else None

    seen_per_class: dict = {}
    for path in sorted(root.rglob("*.txt")):
        rel = path.relative_to(root).parts
        classified = _classify(rel)
        if classified is None:
            continue
        dataset, alpha, klass = classified
        if dataset_filter and dataset not in dataset_filter:
            continue
        if klass_filter and klass not in klass_filter:
            continue
        if alpha_filter and (alpha or "") not in alpha_filter:
            continue
        tiers, stacks, containers = parse_class(klass)
        name = path.stem
        group = (dataset, alpha, klass)
        if limit_per_class is not None:
            count = seen_per_class.get(group, 0)
            if count >= limit_per_class:
                continue
            seen_per_class[group] = count + 1
        yield InstanceRef(
            path=path,
            dataset=dataset,
            klass=klass,
            name=name,
            tiers=tiers,
            stacks=stacks,
            containers=containers,
            alpha=alpha,
        )


def load(ref: InstanceRef) -> Instance:
    return load_instance(
        ref.path,
        name=ref.name,
        dataset=ref.dataset,
        klass=ref.klass,
        alpha=ref.alpha,
        max_tier=ref.tiers,
    )


def discover_classes(root: os.PathLike | str) -> List[tuple]:
    """Return sorted ``(dataset, alpha, klass)`` triples present on disk."""
    seen = set()
    for ref in iter_refs(root):
        seen.add((ref.dataset, ref.alpha, ref.klass))
    return sorted(seen)
