import os
import sys
import unittest
from pathlib import Path
from typing import List


class BaseTestGate:
    """
    Base class for test gates. Sub‑classes define a discovery pattern
    and optionally a custom test directory. The `run` method discovers
    tests, executes them and raises an exception if any test fails.
    """

    #: Directory where tests are located (relative to workspace root)
    test_dir: str = "tests"
    #: Glob pattern used by unittest discovery
    pattern: str = "test_*.py"

    def __init__(self):
        # Ensure the repository root is on sys.path so imports work
        repo_root = Path(__file__).resolve().parents[3]  # up to /app
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))

    def _discover_suite(self) -> unittest.TestSuite:
        """Discover tests based on the configured directory and pattern."""
        test_path = Path(__file__).resolve().parents[3] / self.test_dir
        if not test_path.is_dir():
            raise FileNotFoundError(f"Test directory not found: {test_path}")

        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=str(test_path), pattern=self.pattern)
        return suite

    def _run_suite(self, suite: unittest.TestSuite) -> unittest.result.TestResult:
        """Run the provided test suite and return the result."""
        runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
        result = runner.run(suite)
        return result

    def run(self) -> None:
        """Execute the gate. Raises RuntimeError if any test fails."""
        suite = self._discover_suite()
        if suite.countTestCases() == 0:
            raise RuntimeError(
                f"No tests were discovered with pattern '{self.pattern}' in '{self.test_dir}'."
            )
        result = self._run_suite(suite)

        if not result.wasSuccessful():
            failures = len(result.failures) + len(result.errors)
            raise RuntimeError(
                f"{self.__class__.__name__} failed: {failures} test(s) did not pass."
            )
        print(f"{self.__class__.__name__} passed successfully.")


class UnitTestGate(BaseTestGate):
    """
    Gate for unit tests. It looks for files matching the default
    ``test_*.py`` pattern inside the ``tests/unit`` directory.
    """

    test_dir = "tests/unit"
    pattern = "test_*.py"


class IntegrationTestGate(BaseTestGate):
    """
    Gate for integration tests. It looks for files matching
    ``*_integration.py`` inside the ``tests/integration`` directory.
    """

    test_dir = "tests/integration"
    pattern = "*_integration.py"


class E2ETestGate(BaseTestGate):
    """
    Gate for end‑to‑end tests. It looks for files matching
    ``*_e2e.py`` inside the ``tests/e2e`` directory.
    """

    test_dir = "tests/e2e"
    pattern = "*_e2e.py"


def run_all_gates() -> List[BaseTestGate]:
    """
    Helper to execute all three gates in order.
    Returns a list of instantiated gate objects that succeeded.
    """
    gates: List[BaseTestGate] = [
        UnitTestGate(),
        IntegrationTestGate(),
        E2ETestGate(),
    ]

    for gate in gates:
        gate.run()

    return gates


if __name__ == "__main__":
    # When executed directly, run all gates.
    try:
        run_all_gates()
    except Exception as exc:
        sys.exit(str(exc))