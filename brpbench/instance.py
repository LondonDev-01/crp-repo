"""Parser and model for Block/Container Relocation Problem (BRP/CRP) instances.

Canonical on-disk format (Zhu et al. 2012; Tanaka & Takii 2016):

    W N
    k1 p11 p12 ... p1k1
    k2 p21 p22 ... p2k2
    ...

where ``W`` is the number of stacks, ``N`` the number of blocks, and each stack
line lists its block count followed by the retrieval priorities bottom -> top.

The maximum stack height (bay capacity) is *not* part of the file: it is carried
by the class directory name ``T-S-C`` (tiers, stacks, containers). See
``parse_class``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

CLASS_RE = re.compile(r"^(\d+)-(\d+)-(\d+)$")


@dataclass(frozen=True)
class Instance:
    """A single BRP bay configuration.

    ``stacks[c]`` holds priorities bottom -> top. Priorities may repeat (group
    priorities, Tanaka & Takii 2016). ``max_tier`` is the bay capacity; a stack
    may never exceed it.
    """

    name: str
    stacks: Tuple[Tuple[int, ...], ...]
    max_tier: int
    dataset: str = ""
    klass: str = ""
    alpha: Optional[str] = None

    @property
    def num_stacks(self) -> int:
        return len(self.stacks)

    @property
    def num_blocks(self) -> int:
        return sum(len(s) for s in self.stacks)

    @property
    def initial_height(self) -> int:
        return max((len(s) for s in self.stacks), default=0)

    @property
    def distinct_priorities(self) -> bool:
        priorities = [p for s in self.stacks for p in s]
        return len(set(priorities)) == len(priorities)

    def to_text(self) -> str:
        lines = [f"{self.num_stacks} {self.num_blocks}"]
        for stack in self.stacks:
            lines.append(" ".join(str(p) for p in (len(stack),) + tuple(stack)))
        return "\n".join(lines) + "\n"


def parse_class(klass: str) -> Tuple[int, int, int]:
    """Parse a ``T-S-C`` class name into ``(tiers, stacks, containers)``."""
    m = CLASS_RE.match(klass)
    if not m:
        raise ValueError(f"not a T-S-C class name: {klass!r}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def strip_comments(text: str) -> str:
    out: List[str] = []
    for line in text.splitlines():
        cut = line.find("#")
        out.append(line if cut < 0 else line[:cut])
    return "\n".join(out)


def parse_instance(
    text: str,
    *,
    name: str = "",
    dataset: str = "",
    klass: str = "",
    alpha: Optional[str] = None,
    max_tier: Optional[int] = None,
) -> Instance:
    """Parse instance text. ``max_tier`` defaults to the observed initial height."""
    tokens = [int(t) for t in strip_comments(text).split()]
    if len(tokens) < 2:
        raise ValueError("instance needs at least the 'W N' header")
    num_stacks, num_blocks = tokens[0], tokens[1]
    pos = 2
    stacks: List[Tuple[int, ...]] = []
    for _ in range(num_stacks):
        if pos >= len(tokens):
            raise ValueError("truncated instance: missing stack line")
        count = tokens[pos]
        pos += 1
        if pos + count > len(tokens):
            raise ValueError("truncated instance: stack shorter than declared")
        stacks.append(tuple(tokens[pos : pos + count]))
        pos += count
    if pos != len(tokens):
        raise ValueError(f"trailing tokens after {num_stacks} stacks")
    total = sum(len(s) for s in stacks)
    if total != num_blocks:
        raise ValueError(f"declared {num_blocks} blocks but found {total}")
    if max_tier is None:
        max_tier = max((len(s) for s in stacks), default=0)
    if any(len(s) > max_tier for s in stacks):
        raise ValueError("initial stack exceeds max_tier")
    if max_tier < 1:
        raise ValueError("max_tier must be >= 1")
    return Instance(
        name=name,
        stacks=tuple(stacks),
        max_tier=max_tier,
        dataset=dataset,
        klass=klass,
        alpha=alpha,
    )


def load_instance(path, **kwargs) -> Instance:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    return parse_instance(text, **kwargs)
