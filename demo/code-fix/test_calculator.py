import pytest

from calculator import divide


def test_divide():
    assert divide(12, 3) == 4


def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(12, 0)
