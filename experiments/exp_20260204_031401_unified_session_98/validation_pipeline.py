#!/usr/bin/env python3
"""
validation_pipeline.py

A lightweight validation harness that the swarm can invoke before committing any
generated code. It performs:

1. **Syntax validation** – parses all ``.py`` files with ``ast``.
2. **Import validation** – attempts to import each module to catch missing
   dependencies or circular imports.
3. **Test suite execution** – runs existing ``pytest`` tests (if any).
4. **Basic smoke test** – imports the top‑level package (if a ``__init__.py`` is
   present) to ensure it loads without error.

If any step fails, the script exits with a non‑zero status code and prints a
summary. The swarm can then decide to keep the code in the experiment folder
or flag it for human review.
"""

import ast
import importlib
import os
import subprocess
import sys
import traceback
from pathlib import Path
from typing import List, Tuple

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
# Root of the experiment – all files under this directory are subject to validation.
EXPERIMENT_ROOT = Path(__file__).resolve().parent

# Patterns of files to ignore (e.g., virtualenv, compiled artefacts, etc.)
IGNORE_PATTERNS = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    "*.egg-info",
}

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def is_ignored(path: Path) -> bool:
    """Return True if *path* matches any ignore pattern."""
    for pattern in IGNORE_PATTERNS:
        if path.match(pattern):
            return True
    return False


def collect_python_files(root: Path) -> List[Path]:
    """Recursively collect all ``.py`` files under *root* that are not ignored."""
    python_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # prune ignored directories in‑place to speed up walk
        dirnames[:] = [d for d in dirnames if not is_ignored(Path(dirpath) / d)]
        for fname in filenames:
            if fname.endswith(".py") and not is_ignored(Path(dirpath) / fname):
                python_files.append(Path(dirpath) / fname)
    return python_files


def syntax_check(file_path: Path) -> Tuple[bool, str]:
    """Parse *file_path* with ``ast``; return (success, error_message)."""
    try:
        with file_path.open("r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source, filename=str(file_path))
        return True, ""
    except SyntaxError as exc:
        return False, f"SyntaxError in {file_path}: {exc}"
    except Exception as exc:
        return False, f"Unexpected error parsing {file_path}: {exc}"


def import_check(module_path: Path, root: Path) -> Tuple[bool, str]:
    """
    Attempt to import a module given its file path.

    *module_path* must be inside *root*. The function converts the file path to a
    dotted module name relative to *root* (handling ``__init__.py`` correctly).
    """
    try:
        rel_path = module_path.relative_to(root).with_suffix("")
        parts = list(rel_path.parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]  # package import, not a submodule file
        module_name = ".".join(parts)
        importlib.import_module(module_name)
        return True, ""
    except Exception as exc:
        tb = traceback.format_exc()
        return False, f"ImportError for module '{module_name}': {exc}\n{tb}"


def run_pytest(root: Path) -> Tuple[bool, str]:
    """Execute ``pytest`` in *root* and capture output."""
    try:
        # ``-q`` for quiet output; ``--maxfail=5`` to stop early on many failures.
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--maxfail=5"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300,
        )
        success = result.returncode == 0
        return success, result.stdout
    except subprocess.TimeoutExpired as exc:
        return False, f"pytest timed out: {exc}"
    except Exception as exc:
        return False, f"Failed to run pytest: {exc}"


def basic_smoke_test(root: Path) -> Tuple[bool, str]:
    """
    Perform a minimal smoke test:
    * If the experiment contains a top‑level package (a directory with ``__init__.py``),
      import it.
    * If there is a ``main.py`` at the root, attempt to import it as a module.
    """
    try:
        # Detect top‑level package(s)
        packages = [
            p for p in root.iterdir()
            if p.is_dir() and (p / "__init__.py").exists()
        ]
        for pkg in packages:
            importlib.import_module(pkg.name)

        # Attempt to import ``main`` if present
        main_path = root / "main.py"
        if main_path.is_file():
            spec = importlib.util.spec_from_file_location("main", main_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore

        return True, ""
    except Exception as exc:
        tb = traceback.format_exc()
        return False, f"Smoke test failure: {exc}\n{tb}"


# --------------------------------------------------------------------------- #
# Main validation routine
# --------------------------------------------------------------------------- #
def validate_experiment(root: Path = EXPERIMENT_ROOT) -> int:
    """
    Run the full validation pipeline.

    Returns:
        0 if all checks pass,
        non‑zero otherwise (the caller can interpret the value or just use the exit code).
    """
    overall_success = True

    # 1️⃣ Syntax check
    print("\n=== Syntax Validation ===")
    py_files = collect_python_files(root)
    for py_file in py_files:
        ok, msg = syntax_check(py_file)
        if not ok:
            overall_success = False
            print(f"[FAIL] {msg}")
        else:
            print(f"[OK]   {py_file}")

    # 2️⃣ Import validation
    print("\n=== Import Validation ===")
    for py_file in py_files:
        ok, msg = import_check(py_file, root)
        if not ok:
            overall_success = False
            print(f"[FAIL] {msg}")
        else:
            # Show only successful imports for brevity
            rel = py_file.relative_to(root)
            print(f"[OK]   Imported {rel}")

    # 3️⃣ Pytest execution (if any tests exist)
    test_dir = root / "tests"
    if test_dir.is_dir() or any(p.name.startswith("test_") and p.suffix == ".py" for p in py_files):
        print("\n=== Running pytest ===")
        ok, output = run_pytest(root)
        print(output)
        if not ok:
            overall_success = False
            print("[FAIL] pytest reported failures.")
        else:
            print("[OK]   pytest passed.")
    else:
        print("\n=== No pytest tests found – skipping ===")

    # 4️⃣ Basic smoke test
    print("\n=== Basic Smoke Test ===")
    ok, msg = basic_smoke_test(root)
    if not ok:
        overall_success = False
        print(f"[FAIL] {msg}")
    else:
        print("[OK]   Smoke test passed.")

    # Final status
    if overall_success:
        print("\n✅ Validation succeeded – code is ready for merge.")
        return 0
    else:
        print("\n❌ Validation failed – keep code in experiments/ for review.")
        return 1


if __name__ == "__main__":
    sys.exit(validate_experiment())