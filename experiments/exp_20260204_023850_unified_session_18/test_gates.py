import os
import sys
import unittest
from pathlib import Path
from typing import List


class BaseTestGate:
    """
    Base class for all test gates. It discovers and runs tests
    in the repository and raises an AssertionError if any test fails.
    """

    def __init__(self, start_dir: str = None, pattern: str = "test_*.py"):
        """
        :param start_dir: Directory from which unittest discovery starts.
                          If None, defaults to the repository root (one level above this file).
        :param pattern:   Pattern used by unittest discovery.
        """
        self.start_dir = start_dir or str(Path(__file__).resolve().parents[2])
        self.pattern = pattern

    def _discover_tests(self) -> unittest.TestSuite:
        """Discover tests using unittest's discovery mechanism."""
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=self.start_dir, pattern=self.pattern)
        return suite

    def _run_suite(self, suite: unittest.TestSuite) -> unittest.result.TestResult:
        """Run a test suite and return the result."""
        runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
        result = runner.run(suite)
        return result

    def run(self) -> None:
        """
        Execute the gate. If any test fails or errors, raise AssertionError.
        Sub‑classes can override to add extra behaviour.
        """
        suite = self._discover_tests()
        result = self._run_suite(suite)

        if not result.wasSuccessful():
            failures = len(result.failures) + len(result.errors)
            raise AssertionError(f"{failures} test(s) failed or errored in {self.__class__.__name__}")

        print(f"[PASS] {self.__class__.__name__} – all tests passed.")


class UnitTestGate(BaseTestGate):
    """
    Gate that ensures unit tests (typically located in `tests/unit/`) pass.
    """
    def __init__(self):
        # Assuming unit tests follow the pattern test_*.py and are under the repository root.
        super().__init__(start_dir=str(Path(__file__).resolve().parents[2]), pattern="test_*.py")


class IntegrationTestGate(BaseTestGate):
    """
    Gate that ensures integration tests (typically located in `tests/integration/`) pass.
    """
    def __init__(self):
        # Look for integration tests specifically; they may be named test_integration_*.py
        super().__init__(start_dir=str(Path(__file__).resolve().parents[2]), pattern="test_integration_*.py")


class E2ETestGate(BaseTestGate):
    """
    Gate that ensures end‑to‑end tests (typically located in `tests/e2e/`) pass.
    """
    def __init__(self):
        # Look for e2e tests; they may be named test_e2e_*.py
        super().__init__(start_dir=str(Path(__file__).resolve().parents[2]), pattern="test_e2e_*.py")


def run_all_gates(gates: List[BaseTestGate] = None) -> None:
    """
    Utility to run a sequence of gates. If any gate fails, the function
    will raise an AssertionError and stop execution.
    """
    if gates is None:
        gates = [UnitTestGate(), IntegrationTestGate(), E2ETestGate()]

    for gate in gates:
        gate.run()


if __name__ == "__main__":
    # When executed directly, run all defined gates.
    run_all_gates()