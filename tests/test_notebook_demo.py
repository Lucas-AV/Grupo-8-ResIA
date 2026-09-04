from validate_notebook_demo import validate_notebook


def test_notebook_is_ready_for_guided_demo():
    assert validate_notebook() == []
