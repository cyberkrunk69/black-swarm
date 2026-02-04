#!/usr/bin/env python3
"""
validation_pipeline.py

A lightweight validation harness used by the swarm to self‑test generated code
before it is merged into the main code‑base.

Features:
- Syntax validation for all *.py files in the experiment directory.
- Import validation (ensures modules can be imported without side effects).
- Executes existing pytest suite (if present).
- Runs optional smoke tests defined in a `smoke_tests.py` module.

The script exits with status 0 if all checks pass, otherwise non‑zero.
"""

import ast
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Root of the experiment (the directory containing this script)
EXPERIMENT_ROOT = Path(__file__).resolve().parent

# Optional module that can expose a `run_smoke_tests()` callable.
SMOKE_TEST_MODULE = "smoke_tests"

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #


def collect_python_files(root: Path) -> List[Path]:
    """Return a list of all .py files under *root* (excluding __pycache__)."""
    return [
        p
        for p in root.rglob("*.py")
        if "__pycache__" not in p.parts and p.name != Path(__file__).name
    ]


def check_syntax(file_path: Path) -> Tuple[bool, str]:
    """Parse *file_path* with ast to ensure valid Python syntax."""
    try:
        ast.parse(file_path.read_text(encoding="utf-8"))
        return True, ""
    except SyntaxError as exc:
        return False, f"SyntaxError in {file_path}: {exc}"


def check_importable(module_path: Path) -> Tuple[bool, str]:
    """
    Attempt to import a module given its file path.
    The module is imported under a temporary name to avoid polluting sys.modules.
    """
    module_name = f"_tmp_validation_{module_path.stem}_{abs(hash(str(module_path)))}"
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec is None or spec.loader is None:
        return False, f"Cannot create import spec for {module_path}"
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore
        return True, ""
    except Exception as exc:
        return False, f"ImportError in {module_path}: {exc}"


def run_pytest(root: Path) -> Tuple[bool, str]:
    """
    Execute pytest in *root* (or its parent if no tests are found).
    Returns a tuple (success, output).
    """
    # Detect if there are any test files
    test_files = list(root.rglob("test_*.py")) + list(root.rglob("*_test.py"))
    if not test_files:
        return True, "No pytest tests discovered."

    cmd = [sys.executable, "-m", "pytest", str(root)]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(root),
            check=False,
        )
        success = result.returncode == 0
        return success, result.stdout
    except Exception as exc:
        return False, f"Failed to invoke pytest: {exc}"


def run_smoke_tests(root: Path) -> Tuple[bool, str]:
    """
    If a module named ``smoke_tests.py`` exists in *root*, import it and execute
    a ``run_smoke_tests()`` callable that should return ``True`` on success.
    """
    candidate = root / f"{SMOKE_TEST_MODULE}.py"
    if not candidate.is_file():
        return True, "No smoke_tests module found."

    spec = importlib.util.spec_from_file_location(SMOKE_TEST_MODULE, str(candidate))
    if spec is None or spec.loader is None:
        return False, f"Cannot load smoke_tests module from {candidate}"

    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore
        if not hasattr(module, "run_smoke_tests"):
            return False, "smoke_tests module missing `run_smoke_tests` function."
        result = module.run_smoke_tests()
        if result is True:
            return True, "Smoke tests passed."
        else:
            return False, "Smoke tests reported failure."
    except Exception as exc:
        return False, f"Exception during smoke tests: {exc}"


# --------------------------------------------------------------------------- #
# Main validation routine
# --------------------------------------------------------------------------- #


def main() -> int:
    overall_success = True
    messages: List[str] = []

    # 1. Syntax check
    for py_file in collect_python_files(EXPERIMENT_ROOT):
        ok, msg = check_syntax(py_file)
        if not ok:
            overall_success = False
            messages.append(msg)

    # 2. Import validation
    for py_file in collect_python_files(EXPERIMENT_ROOT):
        ok, msg = check_importable(py_file)
        if not ok:
            overall_success = False
            messages.append(msg)

    # 3. Pytest suite
    ok, msg = run_pytest(EXPERIMENT_ROOT)
    if not ok:
        overall_success = False
    messages.append("[pytest] " + msg.strip())

    # 4. Smoke tests (optional)
    ok, msg = run_smoke_tests(EXPERIMENT_ROOT)
    if not ok:
        overall_success = False
    messages.append("[smoke] " + msg.strip())

    # Reporting
    separator = "\n" + ("=" * 60) + "\n"
    print(separator + "Validation Summary" + separator)
    for line in messages:
        print(line)

    if overall_success:
        print("\nAll checks passed. Ready for merge.")
        return 0
    else:
        print("\nValidation failed. Code will remain in the experiment folder for review.")
        return 1


if __name__ == "__main__":
    sys.exit(main())