"""Benchmark library for the Block / Container Relocation Problem (BRP/CRP)."""

from .catalog import InstanceRef, discover_classes, iter_refs, load
from .instance import Instance, load_instance, parse_class, parse_instance
from .results import (
    STATUS_BEST,
    STATUS_ERROR,
    STATUS_FEASIBLE,
    STATUS_OPTIMAL,
    STATUS_TIMEOUT,
    Result,
    ResultStore,
)

__all__ = [
    "Instance",
    "InstanceRef",
    "parse_instance",
    "load_instance",
    "parse_class",
    "iter_refs",
    "load",
    "discover_classes",
    "Result",
    "ResultStore",
    "STATUS_OPTIMAL",
    "STATUS_BEST",
    "STATUS_FEASIBLE",
    "STATUS_ERROR",
    "STATUS_TIMEOUT",
]
