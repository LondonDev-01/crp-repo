import pytest

from brpbench.instance import parse_instance
from brpbench.solvers import BIN_DIR, GreedySolver, build_registry
from brpbench.results import STATUS_ERROR, STATUS_FEASIBLE, STATUS_OPTIMAL

INSTANCE_TEXT = "6 15\n 1  1\n 2 15 14\n 3  4  9 12\n 3 13  5  8\n 3  3 10  6\n 3  2 11  7\n"
DUPLICATE_TEXT = "6 15\n 2  1  1\n 3  2  2 14\n 3  4  9 12\n 3 13  5  8\n 2  3 10\n 2  3 11\n"


def _instance(text, max_tier=3):
    return parse_instance(text, klass="3-6-15", max_tier=max_tier)


def test_greedy_is_feasible_upper_bound():
    outcome = GreedySolver().solve(_instance(INSTANCE_TEXT))
    assert outcome.status == STATUS_FEASIBLE
    assert outcome.value is not None and outcome.value >= 7


def test_greedy_supports_duplicate_priorities():
    outcome = GreedySolver().solve(_instance(DUPLICATE_TEXT))
    assert outcome.status == STATUS_FEASIBLE
    assert outcome.value is not None


def test_zhu_ida_star_restricted_finds_optimum():
    solver = build_registry()["zhu_restricted_distinct_ida_2012"]
    assert solver.available
    assert solver.supports(_instance(INSTANCE_TEXT))
    assert not solver.supports(_instance(DUPLICATE_TEXT))
    outcome = solver.solve(_instance(INSTANCE_TEXT), time_limit=30)
    assert outcome.status == STATUS_OPTIMAL
    assert outcome.value == 7


def test_zhu_ida_star_unrestricted_finds_optimum():
    solver = build_registry()["zhu_unrestricted_distinct_ida_2012"]
    assert solver.supports(_instance(INSTANCE_TEXT))
    outcome = solver.solve(_instance(INSTANCE_TEXT), time_limit=30)
    assert outcome.status == STATUS_OPTIMAL
    assert outcome.value == 7


def test_zhu_ida_star_rejects_duplicate_priorities():
    solver = build_registry()["zhu_restricted_distinct_ida_2012"]
    outcome = solver.solve(_instance(DUPLICATE_TEXT), time_limit=5)
    assert outcome.status == STATUS_ERROR
    assert outcome.value is None


@pytest.mark.skipif(
    not (BIN_DIR / "tanaka_restricted_distinct_1.3").exists(),
    reason="native solver not built (run scripts/build_solvers.sh)",
)
def test_tanaka_restricted_distinct_finds_optimum():
    solver = build_registry()["tanaka_restricted_distinct_1.3"]
    outcome = solver.solve(_instance(INSTANCE_TEXT), time_limit=30)
    assert outcome.status == STATUS_OPTIMAL
    assert outcome.value == 7


@pytest.mark.skipif(
    not (BIN_DIR / "tanaka_restricted_distinct_1.3").exists(),
    reason="native solver not built (run scripts/build_solvers.sh)",
)
def test_zhu_ida_star_matches_tanaka_optimum():
    inst = _instance(INSTANCE_TEXT)
    tanaka = build_registry()["tanaka_restricted_distinct_1.3"].solve(inst, time_limit=30)
    zhu = build_registry()["zhu_restricted_distinct_ida_2012"].solve(inst, time_limit=30)
    assert tanaka.status == STATUS_OPTIMAL
    assert zhu.status == STATUS_OPTIMAL
    assert zhu.value == tanaka.value


@pytest.mark.skipif(
    not (BIN_DIR / "tanaka_restricted_duplicate_1.02").exists(),
    reason="native solver not built (run scripts/build_solvers.sh)",
)
def test_tanaka_duplicate_supports_group_priorities():
    solver = build_registry()["tanaka_restricted_duplicate_1.02"]
    outcome = solver.solve(_instance(DUPLICATE_TEXT), time_limit=30)
    assert outcome.value is not None
    assert solver.supports(_instance(DUPLICATE_TEXT))
    assert not build_registry()["tanaka_restricted_distinct_1.3"].supports(_instance(DUPLICATE_TEXT))


@pytest.mark.skipif(
    not (BIN_DIR / "jin_tanaka_unrestricted_distinct_jt23").exists(),
    reason="native solver not built (run scripts/build_solvers.sh)",
)
def test_jin_tanaka_unrestricted_finds_optimum():
    solver = build_registry()["jin_tanaka_unrestricted_distinct_jt23"]
    assert solver.supports(_instance(INSTANCE_TEXT))
    outcome = solver.solve(_instance(INSTANCE_TEXT), time_limit=30)
    assert outcome.status == STATUS_OPTIMAL
    assert outcome.value == 7


@pytest.mark.skipif(
    not (BIN_DIR / "jin_tanaka_restricted_distinct_jt23").exists(),
    reason="native solver not built (run scripts/build_solvers.sh)",
)
def test_jin_tanaka_restricted_finds_optimum():
    solver = build_registry()["jin_tanaka_restricted_distinct_jt23"]
    assert solver.supports(_instance(INSTANCE_TEXT))
    assert not solver.supports(_instance(DUPLICATE_TEXT))
    outcome = solver.solve(_instance(INSTANCE_TEXT), time_limit=30)
    assert outcome.status == STATUS_OPTIMAL
    assert outcome.value == 7
