import subprocess
import sys
from pathlib import Path


class _BaseTestGate:
    """
    Base class for test gates. Sub‑classes define a ``test_dir`` attribute that points
    to the directory containing the tests for that gate. The ``run`` method executes
    ``python -m unittest discover`` against that directory and raises an exception
    if any test fails.
    """

    #: Relative path (from the repository root) where the tests for this gate live.
    test_dir: str = ""

    def __init__(self, repo_root: Path | None = None):
        """
        Parameters
        ----------
        repo_root:
            Path to the repository root. If ``None`` the current working directory is
            used. This allows the gate to be instantiated from any location.
        """
        self.repo_root = Path(repo_root or Path.cwd()).resolve()
        if not self.test_dir:
            raise ValueError("Sub‑class must define a non‑empty ``test_dir``.")

    @property
    def _abs_test_dir(self) -> Path:
        """Absolute path to the directory that holds the tests."""
        return (self.repo_root / self.test_dir).resolve()

    def _run_unittest_discover(self) -> subprocess.CompletedProcess:
        """Execute ``python -m unittest discover`` for the configured test directory."""
        if not self._abs_test_dir.is_dir():
            raise FileNotFoundError(f"Test directory not found: {self._abs_test_dir}")

        # ``-s`` specifies the start directory, ``-p`` matches test files, ``-t`` sets the top level.
        cmd = [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(self._abs_test_dir),
            "-p",
            "test_*.py",
            "-t",
            str(self.repo_root),
        ]
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

    def run(self) -> bool:
        """
        Run the gate's tests.

        Returns
        -------
        bool
            ``True`` if all tests pass.

        Raises
        ------
        RuntimeError
            If any test fails.
        """
        result = self._run_unittest_discover()
        if result.returncode != 0:
            # Include the full unittest output for debugging.
            raise RuntimeError(
                f"{self.__class__.__name__} failed:\n{result.stdout}"
            )
        return True


class UnitTestGate(_BaseTestGate):
    """Gate that runs unit tests located in ``tests/unit``."""
    test_dir = "tests/unit"


class IntegrationTestGate(_BaseTestGate):
    """Gate that runs integration tests located in ``tests/integration``."""
    test_dir = "tests/integration"


class E2ETestGate(_BaseTestGate):
    """Gate that runs end‑to‑end tests located in ``tests/e2e``."""
    test_dir = "tests/e2e"


__all__ = [
    "UnitTestGate",
    "IntegrationTestGate",
    "E2ETestGate",
]