import pytest
from app.v2 import V2Processor

@pytest.fixture
def processor():
    return V2Processor()

def test_process_simple_string(processor):
    result = processor.process("hello")
    assert result == "olleh [V2]"

def test_process_empty_string(processor):
    result = processor.process("")
    assert result == " []"

def test_process_non_string_raises(processor):
    with pytest.raises(TypeError):
        processor.process(123)
import unittest
from app.v2 import get_version

class TestV2Implementation(unittest.TestCase):
    def test_get_version(self):
        self.assertEqual(get_version(), "V2")

if __name__ == "__main__":
    unittest.main()