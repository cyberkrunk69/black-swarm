"""
Test Gates for the unified session experiment.

Each gate discovers and runs a specific set of tests.  If any test fails,
the gate raises an exception, causing the overall task to be considered
incomplete.  Successful execution returns ``True``.
"""

import unittest
import sys
import io
import os
from typing import List


class _BaseGate:
    """Common functionality for all gates."""

    @classmethod
    def _discover_and_run(cls, pattern: str) -> bool:
        """
        Discover tests matching *pattern* and run them.

        Returns ``True`` if all discovered tests pass, otherwise ``False``.
        """
        # Ensure we run discovery from the workspace root.
        start_dir = os.getenv("WORKSPACE_ROOT", ".")
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=start_dir, pattern=pattern)

        # Capture output for debugging purposes.
        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(suite)

        # Echo the test run details to stdout – useful in CI logs.
        sys.stdout.write(stream.getvalue())

        return result.wasSuccessful()


class UnitTestGate(_BaseGate):
    """Gate that runs only unit tests (files matching ``test_unit_*.py``)."""

    @classmethod
    def gate(cls) -> bool:
        """Execute the unit‑test gate. Raises on failure."""
        if not cls._discover_and_run("test_unit_*.py"):
            raise RuntimeError("Unit tests failed")
        return True


class IntegrationTestGate(_BaseGate):
    """Gate that runs integration tests (files matching ``test_integration_*.py``)."""

    @classmethod
    def gate(cls) -> bool:
        """Execute the integration‑test gate. Raises on failure."""
        if not cls._discover_and_run("test_integration_*.py"):
            raise RuntimeError("Integration tests failed")
        return True


class E2ETestGate(_BaseGate):
    """Gate that runs end‑to‑end tests (files matching ``test_e2e_*.py``)."""

    @classmethod
    def gate(cls) -> bool:
        """Execute the E2E‑test gate. Raises on failure."""
        if not cls._discover_and_run("test_e2e_*.py"):
            raise RuntimeError("E2E tests failed")
        return True


# Convenience entry point for scripts that wish to run all gates sequentially.
def run_all_gates() -> List[bool]:
    """
    Run Unit, Integration, and E2E gates in order.

    Returns a list of booleans indicating success for each gate.
    """
    results = []
    results.append(UnitTestGate.gate())
    results.append(IntegrationTestGate.gate())
    results.append(E2ETestGate.gate())
    return results


if __name__ == "__main__":
    # When executed directly, run all gates and exit with an appropriate status code.
    try:
        run_all_gates()
        sys.exit(0)
    except Exception as exc:
        sys.stderr.write(f"Gate failure: {exc}\n")
        sys.exit(1)