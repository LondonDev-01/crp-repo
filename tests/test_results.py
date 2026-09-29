from brpbench.results import STATUS_OPTIMAL, Result, ResultStore


def test_upsert_and_load(tmp_path):
    path = tmp_path / "results.jsonl"
    store = ResultStore(path)
    store.upsert(Result("zhu", "3-6-15", "00001", "greedy", 7, "feasible"))
    store.upsert(Result("zhu", "3-6-15", "00001", "greedy", 6, STATUS_OPTIMAL))
    assert len(store) == 1
    store.write()

    reloaded = ResultStore(path).load()
    values = list(reloaded.values())
    assert len(values) == 1
    assert values[0].value == 6
    assert values[0].status == STATUS_OPTIMAL


def test_has_key_includes_alpha(tmp_path):
    store = ResultStore(tmp_path / "r.jsonl")
    store.upsert(Result("tanaka_dup", "3-6-15", "00001", "greedy", 5, "feasible", alpha="0.8"))
    assert store.has("tanaka_dup", "0.8", "3-6-15", "00001", "greedy")
    assert not store.has("tanaka_dup", None, "3-6-15", "00001", "greedy")


def test_json_roundtrip_preserves_extra(tmp_path):
    result = Result("zhu", "3-6-15", "00001", "greedy", 7, "feasible", extra={"note": "x"})
    parsed = Result.from_json(result.to_json())
    assert parsed.extra["note"] == "x"
    assert parsed.key == result.key
