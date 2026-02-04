import pytest
from app.v2 import run_v2

def test_run_v2_basic():
    assert run_v2("hello") == "olleh [processed by V2]"

def test_run_v2_empty_string():
    assert run_v2("") == " [processed by V2]"

def test_run_v2_non_string():
    with pytest.raises(TypeError):
        run_v2(123)