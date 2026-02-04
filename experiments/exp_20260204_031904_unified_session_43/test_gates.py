import subprocess
import sys
import os
import unittest
from pathlib import Path
from typing import List


class BaseGate:
    """
    Base class for all gates. Provides utility methods for running
    subprocesses and collecting test results.
    """

    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.output = ""

    def _run_subprocess(self, cmd: List[str]) -> int:
        """
        Run a command in a subprocess, capture stdout/stderr and store them.
        Returns the subprocess exit code.
        """
        try:
            completed = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            self.output = completed.stdout
            return completed.returncode
        except Exception as e:
            self.output = str(e)
            return 1

    def _discover_tests(self, start_dir: str) -> unittest.TestSuite:
        """
        Discover unittest tests in the given directory.
        """
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=start_dir, pattern="test_*.py")
        return suite

    def _run_unittest_suite(self, suite: unittest.TestSuite) -> bool:
        """
        Execute a unittest.TestSuite and return True if all tests pass.
        """
        runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
        result = runner.run(suite)
        self.passed = result.wasSuccessful()
        return self.passed

    def gate(self) -> bool:
        """
        Override in subclasses. Should return True if gate passes.
        """
        raise NotImplementedError

    def __bool__(self):
        return self.passed


class UnitTestGate(BaseGate):
    """
    Gate that runs unit tests located in the `tests/unit` directory.
    """

    def __init__(self):
        super().__init__("UnitTestGate")

    def gate(self) -> bool:
        test_dir = Path(__file__).parent / "tests" / "unit"
        if not test_dir.is_dir():
            # No unit tests – consider the gate passed by default.
            self.passed = True
            self.output = "No unit test directory found; gate passed by default."
            return True

        suite = self._discover_tests(str(test_dir))
        return self._run_unittest_suite(suite)


class IntegrationTestGate(BaseGate):
    """
    Gate that runs integration tests located in the `tests/integration` directory.
    """

    def __init__(self):
        super().__init__("IntegrationTestGate")

    def gate(self) -> bool:
        test_dir = Path(__file__).parent / "tests" / "integration"
        if not test_dir.is_dir():
            # No integration tests – consider the gate passed by default.
            self.passed = True
            self.output = "No integration test directory found; gate passed by default."
            return True

        suite = self._discover_tests(str(test_dir))
        return self._run_unittest_suite(suite)


class E2ETestGate(BaseGate):
    """
    Gate that runs end‑to‑end (E2E) tests located in the `tests/e2e` directory.
    It can also execute a custom script if provided.
    """

    def __init__(self, script_path: str = None):
        super().__init__("E2ETestGate")
        self.script_path = script_path

    def gate(self) -> bool:
        # Prefer a custom script if supplied.
        if self.script_path:
            script = Path(self.script_path)
            if not script.is_file():
                self.passed = False
                self.output = f"E2E script not found: {self.script_path}"
                return False
            exit_code = self._run_subprocess([sys.executable, str(script)])
            self.passed = exit_code == 0
            return self.passed

        # Fallback to unittest discovery in tests/e2e
        test_dir = Path(__file__).parent / "tests" / "e2e"
        if not test_dir.is_dir():
            self.passed = True
            self.output = "No E2E test directory found; gate passed by default."
            return True

        suite = self._discover_tests(str(test_dir))
        return self._run_unittest_suite(suite)


def run_all_gates() -> bool:
    """
    Utility function to run all defined gates sequentially.
    Returns True only if every gate passes.
    """
    gates = [UnitTestGate(), IntegrationTestGate(), E2ETestGate()]
    all_passed = True
    for gate in gates:
        print(f"\n=== Running {gate.name} ===")
        passed = gate.gate()
        print(gate.output if gate.output else "")
        if not passed:
            print(f"{gate.name} FAILED")
        else:
            print(f"{gate.name} PASSED")
        all_passed = all_passed and passed
    return all_passed


if __name__ == "__main__":
    success = run_all_gates()
    sys.exit(0 if success else 1)