import pytest
from siege_utils import build_changeset

def test_build_changeset_basic():
    changed = {
        'Alice': {'old': ['A'], 'new': ['B']},
        'Bob': {'old': ['C'], 'new': ['D']},
    }
    unchanged = {
        'Alice': ['E'],
        'Charlie': ['F']
    }
    result = build_changeset(changed, unchanged)
    assert result['Alice']['old'] == ['A']
    assert result['Alice']['new'] == ['B']
    assert result['Alice']['unchanged'] == ['E']
    assert result['Bob']['old'] == ['C']
    assert result['Bob']['new'] == ['D']
    assert result['Bob']['unchanged'] == []
    assert result['Charlie']['old'] == []
    assert result['Charlie']['new'] == []
    assert result['Charlie']['unchanged'] == ['F']

def test_build_changeset_empty():
    changed = {}
    unchanged = {}
    result = build_changeset(changed, unchanged)
    assert result == {}

def test_build_changeset_only_unchanged():
    changed = {}
    unchanged = {'Alice': ['A'], 'Bob': ['B']}
    result = build_changeset(changed, unchanged)
    assert result['Alice']['old'] == []
    assert result['Alice']['new'] == []
    assert result['Alice']['unchanged'] == ['A']
    assert result['Bob']['unchanged'] == ['B']

def test_build_changeset_only_changed():
    changed = {'Alice': {'old': ['A'], 'new': ['B']}}
    unchanged = {}
    result = build_changeset(changed, unchanged)
    assert result['Alice']['old'] == ['A']
    assert result['Alice']['new'] == ['B']
    assert result['Alice']['unchanged'] == []

def test_build_changeset_merges_lists():
    changed = {'Alice': {'old': ['A', 'B'], 'new': ['C']}}
    unchanged = {'Alice': ['D', 'E']}
    result = build_changeset(changed, unchanged)
    assert set(result['Alice']['old']) == {'A', 'B'}
    assert result['Alice']['new'] == ['C']
    assert set(result['Alice']['unchanged']) == {'D', 'E'}
