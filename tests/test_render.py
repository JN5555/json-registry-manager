from json_registry_manager.render import _column_count


def test_adaptive_column_count():
    assert _column_count(60) == 1
    assert _column_count(100) == 2
    assert _column_count(150) == 3
