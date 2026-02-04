import os
import sys
import unittest
from pathlib import Path

class BaseTestGate:
    """
    Base class for test gates. Sub‑classes define the directory that contains
    the tests to be executed. The `run` method discovers and runs the tests;
    it raises a RuntimeError if any test fails, causing the gate to be
    considered failed.
    """
    test_dir: str = ""

    def __init__(self):
        if not self.test_dir:
            raise ValueError("test_dir must be set in the subclass")
        # Ensure the test directory is on sys.path so that imports inside tests work.
        test_path = Path(self.test_dir).resolve()
        if str(test_path) not in sys.path:
            sys.path.insert(0, str(test_path))

    def _discover_tests(self) -> unittest.TestSuite:
        loader = unittest.TestLoader()
        # discover will look for files matching test*.py
        suite = loader.discover(start_dir=self.test_dir, pattern="test*.py")
        return suite

    def run(self) -> None:
        """
        Execute the tests. If any test fails, raise RuntimeError.
        """
        suite = self._discover_tests()
        runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
        result = runner.run(suite)
        if not result.wasSuccessful():
            raise RuntimeError(
                f"{self.__class__.__name__} failed: {len(result.failures)} failures, "
                f"{len(result.errors)} errors."
            )
        # Success path – nothing to return


class UnitTestGate(BaseTestGate):
    """
    Gate that runs unit tests located in `tests/unit`.
    """
    def __init__(self):
        # Resolve relative to the project root (assumed to be the cwd)
        project_root = Path(__file__).parents[2]  # experiments/... -> project root
        unit_test_dir = project_root / "tests" / "unit"
        self.test_dir = str(unit_test_dir)
        super().__init__()


class IntegrationTestGate(BaseTestGate):
    """
    Gate that runs integration tests located in `tests/integration`.
    """
    def __init__(self):
        project_root = Path(__file__).parents[2]
        integration_test_dir = project_root / "tests" / "integration"
        self.test_dir = str(integration_test_dir)
        super().__init__()


class E2ETestGate(BaseTestGate):
    """
    Gate that runs end‑to‑end tests located in `tests/e2e`.
    """
    def __init__(self):
        project_root = Path(__file__).parents[2]
        e2e_test_dir = project_root / "tests" / "e2e"
        self.test_dir = str(e2e_test_dir)
        super().__init__()


# Helper to run all gates sequentially if this file is executed directly.
if __name__ == "__main__":
    gates = [UnitTestGate(), IntegrationTestGate(), E2ETestGate()]
    for gate in gates:
        print(f"Running {gate.__class__.__name__}...")
        gate.run()
        print(f"{gate.__class__.__name__} passed.\n")