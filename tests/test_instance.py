import pytest

from brpbench.instance import parse_class, parse_instance


def test_parse_basic():
    text = "3 4\n2 1 2\n1 3\n1 4\n"
    inst = parse_instance(text, name="x", klass="3-3-4", max_tier=3)
    assert inst.num_stacks == 3
    assert inst.num_blocks == 4
    assert inst.stacks == ((1, 2), (3,), (4,))
    assert inst.max_tier == 3
    assert inst.initial_height == 2
    assert inst.distinct_priorities


def test_capacity_defaults_to_observed_height():
    inst = parse_instance("2 3\n1 1\n2 2 3\n")
    assert inst.max_tier == 2


def test_comments_and_whitespace():
    text = "# converted from x\n# ratio=0.8 seed=1\n 3 4\n 2 1 2\n 1 3\n 1 4\n"
    inst = parse_instance(text)
    assert inst.num_blocks == 4


def test_duplicate_priorities():
    inst = parse_instance("2 4\n2 1 1\n2 2 1\n")
    assert not inst.distinct_priorities


def test_roundtrip():
    inst = parse_instance("3 4\n2 1 2\n1 3\n1 4\n", max_tier=3)
    again = parse_instance(inst.to_text(), max_tier=3)
    assert again.stacks == inst.stacks


def test_rejects_declared_count_mismatch():
    with pytest.raises(ValueError):
        parse_instance("2 5\n1 1\n1 2\n")


def test_rejects_stack_over_capacity():
    with pytest.raises(ValueError):
        parse_instance("1 2\n2 1 2\n", max_tier=1)


def test_parse_class():
    assert parse_class("7-9-62") == (7, 9, 62)
    with pytest.raises(ValueError):
        parse_class("not-a-class")
