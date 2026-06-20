import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import calculator as calc  # noqa: E402


def test_add():
    assert calc.add(2, 3) == 5


def test_subtract():
    assert calc.subtract(5, 2) == 3


def test_multiply():
    assert calc.multiply(4, 3) == 12


def test_divide():
    assert calc.divide(10, 2) == 5


def test_mean():
    assert calc.mean([1, 2, 3, 4]) == 2.5
