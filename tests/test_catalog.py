from brpbench.catalog import discover_classes, iter_refs, load


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_iter_refs_layouts(tmp_path):
    _write(tmp_path, "zhu/3-6-15/00001.txt", "2 3\n1 1\n2 2 3\n")
    _write(tmp_path, "tanaka_dup/alpha=0.8/3-6-15/00001.txt", "2 3\n1 1\n2 2 3\n")

    refs = list(iter_refs(tmp_path))
    keys = sorted(r.key for r in refs)
    assert keys == ["tanaka_dup/alpha=0.8/3-6-15/00001", "zhu/3-6-15/00001"]

    zhu = [r for r in refs if r.dataset == "zhu"][0]
    assert (zhu.tiers, zhu.stacks, zhu.containers) == (3, 6, 15)
    inst = load(zhu)
    assert inst.max_tier == 3
    assert inst.alpha is None


def test_filters_and_limit(tmp_path):
    for i in range(5):
        _write(tmp_path, f"zhu/3-6-15/{i:05d}.txt", "1 1\n1 1\n")
    refs = list(iter_refs(tmp_path, datasets=["zhu"], klasses=["3-6-15"], limit_per_class=2))
    assert len(refs) == 2


def test_discover_classes(tmp_path):
    _write(tmp_path, "zhu/3-6-15/00001.txt", "1 1\n1 1\n")
    _write(tmp_path, "tanaka_dup/alpha=0.2/4-8-28/00001.txt", "1 1\n1 1\n")
    classes = discover_classes(tmp_path)
    assert classes == [("tanaka_dup", "0.2", "4-8-28"), ("zhu", None, "3-6-15")]
