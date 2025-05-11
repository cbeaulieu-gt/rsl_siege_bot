import pytest
from typing import Optional
from siege_planner import Position
from excel import compare_assignment_changes

def make_pos(building, position, group=None, building_number=None):
    return Position(building=building, position=position, group=group, building_number=building_number)

def test_no_changes():
    old = [
        (make_pos('Mana Shrine', 1, 1, 1), 'Alice'),
        (make_pos('Defense Tower', 2, 2, 2), 'Bob'),
    ]
    new = [
        (make_pos('Mana Shrine', 1, 1, 1), 'Alice'),
        (make_pos('Defense Tower', 2, 2, 2), 'Bob'),
    ]
    # Patch extract_positions_from_excel
    def fake_extract(file):
        return old if 'old' in file else new
    import excel
    excel.extract_positions_from_excel = fake_extract
    result = compare_assignment_changes('old_file', 'new_file')
    assert result == {}

def test_assignment_changed():
    old = [
        (make_pos('Mana Shrine', 1, 1, 1), 'Alice'),
    ]
    new = [
        (make_pos('Mana Shrine', 2, 1, 1), 'Alice'),
    ]
    def fake_extract(file):
        return old if 'old' in file else new
    import excel
    excel.extract_positions_from_excel = fake_extract
    result = compare_assignment_changes('old_file', 'new_file')
    assert 'Alice' in result
    assert result['Alice']['old'] == [make_pos('Mana Shrine', 1, 1, 1)]
    assert result['Alice']['new'] == [make_pos('Mana Shrine', 2, 1, 1)]

def test_assignment_added():
    old = []
    new = [
        (make_pos('Mana Shrine', 1, 1, 1), 'Alice'),
    ]
    def fake_extract(file):
        return old if 'old' in file else new
    import excel
    excel.extract_positions_from_excel = fake_extract
    result = compare_assignment_changes('old_file', 'new_file')
    assert 'Alice' in result
    assert result['Alice']['old'] == []
    assert result['Alice']['new'] == [make_pos('Mana Shrine', 1, 1, 1)]

def test_assignment_removed():
    old = [
        (make_pos('Mana Shrine', 1, 1, 1), 'Alice'),
    ]
    new = []
    def fake_extract(file):
        return old if 'old' in file else new
    import excel
    excel.extract_positions_from_excel = fake_extract
    result = compare_assignment_changes('old_file', 'new_file')
    assert 'Alice' in result
    assert result['Alice']['old'] == [make_pos('Mana Shrine', 1, 1, 1)]
    assert result['Alice']['new'] == []

def test_multiple_assignments_and_members():
    old = [
        (make_pos('Mana Shrine', 1, 1, 1), 'Alice'),
        (make_pos('Mana Shrine', 2, 1, 1), 'Alice'),
        (make_pos('Defense Tower', 1, 2, 2), 'Bob'),
    ]
    new = [
        (make_pos('Mana Shrine', 2, 1, 1), 'Alice'),  # Alice lost 1, kept 2
        (make_pos('Defense Tower', 1, 2, 2), 'Bob'),  # Bob unchanged
        (make_pos('Defense Tower', 2, 2, 2), 'Bob'),  # Bob new assignment
    ]
    def fake_extract(file):
        return old if 'old' in file else new
    import excel
    excel.extract_positions_from_excel = fake_extract
    result = compare_assignment_changes('old_file', 'new_file')
    # Alice lost position 1, kept 2
    assert 'Alice' in result
    assert set(result['Alice']['old']) == {make_pos('Mana Shrine', 1, 1, 1)}
    assert set(result['Alice']['new']) == {make_pos('Mana Shrine', 2, 1, 1)}
    # Bob gained a new assignment
    assert 'Bob' in result
    assert set(result['Bob']['old']) == set()
    assert set(result['Bob']['new']) == {make_pos('Defense Tower', 2, 2, 2)}

def test_edge_case_none_positions():
    old = [
        (make_pos('Mana Shrine', 1, 1, 1), 'Alice'),
    ]
    new = [
        (None, 'Alice'),
    ]
    def fake_extract(file):
        return old if 'old' in file else new
    import excel
    excel.extract_positions_from_excel = fake_extract
    result = compare_assignment_changes('old_file', 'new_file')
    # Should handle None gracefully
    assert 'Alice' in result
    assert result['Alice']['old'] == [make_pos('Mana Shrine', 1, 1, 1)]
    assert result['Alice']['new'] == []
