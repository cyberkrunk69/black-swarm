import unittest
from unittest.mock import patch

from experimental_reasoning import ExperimentalReasoner


class TestExperimentalReasoner(unittest.TestCase):
    """
    Verify that the self‑consistency CoT pipeline returns the expected answer
    on a simple logical puzzle that requires multi‑step inference.
    """

    def setUp(self):
        # Use a small number of samples for speed in tests.
        self.reasoner = ExperimentalReasoner(n_samples=3, temperature=0.0)

    @patch.object(ExperimentalReasoner, "_call_llm")
    def test_solve_simple_logic(self, mock_call):
        """
        Question: All A are B. Some B are C. Are some A C?
        Expected answer: Yes
        """
        # Mock CoT responses – each ends with a line starting with "Answer:".
        mock_responses = [
            "First, all A are B. Then, some B are C, so those B that are also C may be A. "
            "Therefore, some A are C.\nAnswer: Yes",
            "We know that every A is a B. Since some B are also C, it is possible that "
            "the intersection includes A. Hence, some A are C.\nAnswer: Yes",
            "Reasoning step‑by‑step leads to the same conclusion: some A are C.\nAnswer: Yes",
        ]
        # The mock will return the above strings sequentially.
        mock_call.side_effect = mock_responses

        question = "All A are B. Some B are C. Are some A C?"
        answer = self.reasoner.solve(question)
        self.assertEqual(answer, "Yes")

    @patch.object(ExperimentalReasoner, "_call_llm")
    def test_evaluate_benchmark(self, mock_call):
        # All calls return the same deterministic answer.
        mock_call.return_value = "Answer: No"

        benchmark = [
            ("All X are Y. Some Y are Z. Are some X Z?", "No"),
            ("If it rains then the ground gets wet. It rains. Is the ground wet?", "Yes"),
        ]

        # Use the reasoner to evaluate accuracy.
        accuracy = self.reasoner.evaluate(benchmark)
        # Both predictions are "No", so only the first matches.
        self.assertAlmostEqual(accuracy, 0.5)


if __name__ == "__main__":
    unittest.main()
```python
import pytest
from experimental_reasoning import NovelReasoner

@pytest.fixture
def reasoner():
    return NovelReasoner()

def test_simple_transitive(reasoner):
    facts = ["A > B", "B > C"]
    query = "Is A > C?"
    assert reasoner.reason(facts, query) == "Yes"

def test_negative_transitive(reasoner):
    facts = ["A > B", "B > C"]
    query = "Is C > A?"
    assert reasoner.reason(facts, query) == "No"

def test_mixed_operators(reasoner):
    facts = ["X < Y", "Y > Z"]
    query = "Is X < Z?"
    # No transitive path from X to Z in the constructed graph
    assert reasoner.reason(facts, query) == "No"

def test_counterfactual(reasoner):
    # Counterfactual style: ask the opposite direction of the established order
    facts = ["M > N", "N > O"]
    query = "Is O > M?"
    assert reasoner.reason(facts, query) == "No"

def test_analogical_transfer(reasoner):
    # Same relational pattern as test_simple_transitive but with different symbols
    facts = ["P > Q", "Q > R"]
    query = "Is P > R?"
    assert reasoner.reason(facts, query) == "Yes"
```
import os
import importlib
import pytest

# --------------------------------------------------------------------------- #
# Configure a dummy API key so that the module does not abort at import time.
# The real LLM call will be monkey‑patched below.
# --------------------------------------------------------------------------- #
os.environ["OPENAI_API_KEY"] = "dummy-key"

# Import the module under test.
import experimental_reasoning
from experimental_reasoning import NovelReasoner

# --------------------------------------------------------------------------- #
# Mock implementation of the low‑level LLM call.
# Returns deterministic, easy‑to‑parse outputs for the test suite.
# --------------------------------------------------------------------------- #
def _mock_call_llm(prompt: str) -> str:
    if "Chain of Thought" in prompt:
        # Simulated chain‑of‑thought with a clear answer line.
        return (
            "Step 1: Understand the question.\n"
            "Step 2: Perform logical inference.\n"
            "Answer: 42"
        )
    if "Revised Answer" in prompt:
        # Simulated self‑reflection that confirms the original answer.
        return "Answer: 42"
    # Default fallback.
    return "Answer: unknown"

# Patch the private helper in the module.
experimental_reasoning._call_llm = _mock_call_llm  # type: ignore

@pytest.fixture
def reasoner():
    """Provide a fresh NovelReasoner for each test."""
    return NovelReasoner(max_reflections=1)

def test_basic_reasoning(reasoner):
    """A simple factual question should return the mocked answer."""
    ans = reasoner.reason("What is the answer to life, the universe, and everything?")
    assert ans == "42"

def test_counterfactual(reasoner):
    """Counterfactual queries should still produce a non‑empty answer."""
    ans = reasoner.reason(
        "If the moon were made of cheese, how would the tides be affected?"
    )
    assert isinstance(ans, str) and len(ans) > 0
```python
import unittest
from experimental_reasoning import ReasoningEngine

class TestNovelReasoning(unittest.TestCase):
    def setUp(self):
        # Seed the engine for deterministic behaviour
        self.engine = ReasoningEngine(seed=42)

    def test_multi_hop_inference(self):
        q = "What is the capital of France and what does gravity cause?"
        ans, _ = self.engine.solve(q)
        self.assertIn("Paris", ans)
        self.assertIn("Objects with mass attract each other.", ans)

    def test_counterfactual(self):
        q = "What if water boiled at 80°C?"
        ans, _ = self.engine.solve(q)
        self.assertIn("remain liquid", ans)

    def test_analogy(self):
        q = "How is photosynthesis like solar panels?"
        ans, _ = self.engine.solve(q)
        self.assertIn("analogous to solar panels", ans)

    def test_benchmark_accuracy(self):
        acc = ReasoningEngine.run_benchmark(seed=123)
        # Expect at least 60% accuracy on the three handcrafted tasks
        self.assertGreaterEqual(acc, 0.6)

if __name__ == "__main__":
    unittest.main()
```
import pytest
from experimental_reasoning import NovelReasoner

# ----------------------------------------------------------------------
# Test suite for novel reasoning capabilities
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def reasoner():
    # In production this would be a real LLM; for tests we keep the dummy.
    return NovelReasoner()

# Each entry: (question, expected_answer)
TEST_CASES = [
    # Multi‑hop logical inference
    (
        "All mammals are warm‑blooded. Whales are mammals. Are whales warm‑blooded?",
        "Yes",
    ),
    # Simple fact lookup
    (
        "All birds lay eggs. Penguins are birds. What is a penguin?",
        "lay eggs",
    ),
    # Counterfactual reasoning
    (
        "If cats were reptiles, could they climb trees?",
        "Unable to determine",
    ),
    # Analogical transfer (pattern similarity)
    (
        "All engineers build things. Alice is an engineer. What does Alice do?",
        "build things",
    ),
    # Unknown relation
    (
        "All fruits are sweet. Lemons are sour. Are lemons sweet?",
        "No",
    ),
]

@pytest.mark.parametrize("question,expected", TEST_CASES)
def test_novel_reasoning(reasoner: NovelReasoner, question: str, expected: str):
    answer = reasoner.reason(question)
    # Normalise whitespace and case for comparison
    norm = lambda s: s.strip().lower()
    assert norm(answer) == norm(expected), f"Failed on: {question}"
import pytest
from experimental_reasoning import ExperimentalReasoner

# ----------------------------------------------------------------------
# Benchmark problems for novel reasoning
# ----------------------------------------------------------------------
benchmark_cases = [
    # Simple transitive inference
    (
        """
        If a blork is a glim.
        All glims are slops.
        Question: Is a blork a slop?
        """,
        "Yes"
    ),
    # Multi‑hop (3 hops) inference
    (
        """
        If a quix is a zot.
        If a zot is a blip.
        All blips are frobs.
        Question: Is a quix a frob?
        """,
        "Yes"
    ),
    # Negative information (should resolve to No)
    (
        """
        All drims are not plops.
        If something is a drim then it is not a plop.
        Question: Is a drim a plop?
        """,
        "No"
    ),
    # Counterfactual style – one trace will be wrong, voting should win
    (
        """
        If a narl is a gorp.
        All gorp are wexes.
        Question: Is a narl a wex?
        """,
        "Yes"
    ),
    # Unknown / insufficient information
    (
        """
        If a foo is a bar.
        Question: Is a bar a foo?
        """,
        "No"
    ),
]

@pytest.mark.parametrize("problem,expected", benchmark_cases)
def test_experimental_reasoner(problem, expected):
    reasoner = ExperimentalReasoner(num_traces=5)
    answer = reasoner.reason(problem)
    assert answer == expected, f"Expected {expected}, got {answer}"