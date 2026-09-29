"""Solver registry: maps solver names to ready-to-run solver objects."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .base import SolveOutcome, Solver
from .greedy import GreedySolver
from .ida_star import ZhuIdaStarSolver
from .tanaka import TanakaSolver
from .ucrp import JinTanakaSolver

REPO_ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = REPO_ROOT / "solvers" / "bin"

TANAKA_SPECS = [
    {
        "name": "tanaka_restricted_distinct_1.3",
        "binary": "tanaka_restricted_distinct_1.3",
        "capacity_mode": "E",
        "priority_kind": "distinct",
        "description": "Tanaka & Voss (2022) exact restricted BRP, distinct priorities",
    },
    {
        "name": "tanaka_restricted_distinct_1.11",
        "binary": "tanaka_restricted_distinct_1.11",
        "capacity_mode": "E",
        "priority_kind": "distinct",
        "description": "Tanaka & Mizuno (2018) exact restricted BRP, distinct priorities",
    },
    {
        "name": "tanaka_unrestricted_distinct_1.01",
        "binary": "tanaka_unrestricted_distinct_1.01",
        "capacity_mode": "E",
        "priority_kind": "distinct",
        "description": "Tanaka & Mizuno (2018) exact unrestricted BRP, distinct priorities",
    },
    {
        "name": "tanaka_restricted_duplicate_1.02",
        "binary": "tanaka_restricted_duplicate_1.02",
        "capacity_mode": "T",
        "priority_kind": "any",
        "description": "Tanaka & Takii (2016) exact restricted BRP, duplicate priorities",
    },
]

JIN_TANAKA_SPECS = [
    {
        "name": "jin_tanaka_unrestricted_distinct_jt23",
        "binary": "jin_tanaka_unrestricted_distinct_jt23",
        "priority_kind": "any",
        "description": "Jin & Tanaka (2023) exact unrestricted CRP, duplicate priorities",
    },
    {
        "name": "jin_tanaka_restricted_distinct_jt23",
        "binary": "jin_tanaka_restricted_distinct_jt23",
        "priority_kind": "distinct",
        "description": "Jin & Tanaka (2023) exact restricted CRP, distinct priorities",
    },
]

ZHU_IDA_STAR_SPECS = [
    {
        "name": "zhu_restricted_distinct_ida_2012",
        "restricted": True,
        "lower_bound": "LB3",
        "probe": "PR3",
        "description": "Zhu et al. (2012) exact restricted CRP via IDA*, distinct priorities",
    },
    {
        "name": "zhu_unrestricted_distinct_ida_2012",
        "restricted": False,
        "lower_bound": "LB1",
        "probe": "PR3",
        "description": "Zhu et al. (2012) exact unrestricted CRP via IDA*, distinct priorities",
    },
]


def build_registry() -> Dict[str, Solver]:
    registry: Dict[str, Solver] = {"greedy": GreedySolver()}
    for spec in TANAKA_SPECS:
        registry[spec["name"]] = TanakaSolver(
            name=spec["name"],
            binary=BIN_DIR / spec["binary"],
            capacity_mode=spec["capacity_mode"],
            priority_kind=spec["priority_kind"],
            description=spec["description"],
        )
    for spec in JIN_TANAKA_SPECS:
        registry[spec["name"]] = JinTanakaSolver(
            name=spec["name"],
            binary=BIN_DIR / spec["binary"],
            priority_kind=spec["priority_kind"],
            description=spec["description"],
        )
    for spec in ZHU_IDA_STAR_SPECS:
        registry[spec["name"]] = ZhuIdaStarSolver(
            name=spec["name"],
            restricted=spec["restricted"],
            lower_bound=spec["lower_bound"],
            probe=spec["probe"],
            description=spec["description"],
        )
    return registry


def list_solvers() -> List[Solver]:
    return list(build_registry().values())


__all__ = [
    "SolveOutcome",
    "Solver",
    "GreedySolver",
    "ZhuIdaStarSolver",
    "TanakaSolver",
    "JinTanakaSolver",
    "build_registry",
    "list_solvers",
]
