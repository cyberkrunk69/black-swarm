"""Comprehensive tests for scout validator — the hallucination police."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from vivarium.scout.validator import (
    HALLUCINATED_PATH,
    HALLUCINATED_SYMBOL,
    LOW_CONFIDENCE,
    VALID,
    ValidationResult,
    validate_location,
)


def test_hallucinated_path(tmp_path: Path):
    """vivarium/core/auth_v2.py → reject, suggest auth.py or similar sibling."""
    # Create vivarium/core/ with auth.py (no auth_v2.py)
    core_dir = tmp_path / "vivarium" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "auth.py").write_text("def authenticate_user(): pass\n")
    (core_dir / "config.py").write_text("# config\n")

    result = validate_location(
        {"file": "vivarium/core/auth_v2.py", "confidence": 90},
        tmp_path,
    )

    assert result.is_valid is False
    assert result.error_code == HALLUCINATED_PATH
    assert result.actual_file is None
    assert "vivarium/core/auth.py" in result.alternatives
    assert result.validation_time_ms < 10


def test_wrong_symbol_name(tmp_path: Path):
    """authenticate vs authenticate_user → fuzzy match finds it."""
    core_dir = tmp_path / "vivarium" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "auth.py").write_text(
        "def authenticate_user(x):\n    return True\n"
    )

    result = validate_location(
        {
            "file": "vivarium/core/auth.py",
            "function": "authenticate",
            "confidence": 85,
        },
        tmp_path,
    )

    assert result.is_valid is True
    assert result.actual_file == (tmp_path / "vivarium" / "core" / "auth.py").resolve()
    assert result.actual_line == 1
    assert result.symbol_snippet is not None
    assert "authenticate_user" in (result.symbol_snippet or "")
    assert result.validation_time_ms < 10


def test_correct_location(tmp_path: Path):
    """Exact match → valid, 100 confidence."""
    core_dir = tmp_path / "vivarium" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "auth.py").write_text(
        "def authenticate_user(x):\n    return x\n"
    )

    result = validate_location(
        {
            "file": "vivarium/core/auth.py",
            "function": "authenticate_user",
            "line": 1,
            "confidence": 90,
        },
        tmp_path,
    )

    assert result.is_valid is True
    assert result.adjusted_confidence >= 90
    assert result.actual_file is not None
    assert result.actual_line == 1
    assert result.error_code == VALID
    assert result.validation_time_ms < 10


def test_low_confidence_input(tmp_path: Path):
    """65 confidence → reject before filesystem check."""
    result = validate_location(
        {"file": "vivarium/core/auth.py", "confidence": 65},
        tmp_path,
    )

    assert result.is_valid is False
    assert result.error_code == LOW_CONFIDENCE
    assert result.adjusted_confidence == 65
    assert result.actual_file is None
    assert result.validation_time_ms < 10


def test_wrong_line(tmp_path: Path):
    """Symbol exists, wrong line number → correct line, proceed valid."""
    core_dir = tmp_path / "vivarium" / "core"
    core_dir.mkdir(parents=True)
    content = """
# comment
def helper():
    pass

def authenticate_user(x):
    return x
"""
    (core_dir / "auth.py").write_text(content)

    result = validate_location(
        {
            "file": "vivarium/core/auth.py",
            "function": "authenticate_user",
            "line": 1,  # wrong — actual is line 6
            "confidence": 85,
        },
        tmp_path,
    )

    assert result.is_valid is True
    assert result.actual_line == 6
    assert result.error_code == VALID
    assert result.validation_time_ms < 10


def test_hallucinated_symbol(tmp_path: Path):
    """File exists, function doesn't → HALLUCINATED_SYMBOL."""
    core_dir = tmp_path / "vivarium" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "auth.py").write_text("def login(): pass\n")

    result = validate_location(
        {
            "file": "vivarium/core/auth.py",
            "function": "authenticate_user",
            "confidence": 90,
        },
        tmp_path,
    )

    assert result.is_valid is False
    assert result.error_code == HALLUCINATED_SYMBOL
    assert result.actual_file is not None
    assert result.actual_line is None
    assert result.adjusted_confidence <= 60
    assert result.validation_time_ms < 10


def test_did_you_mean_alternatives(tmp_path: Path):
    """Alternatives list provides 'did you mean' suggestions."""
    core_dir = tmp_path / "vivarium" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "auth.py").write_text("# auth\n")
    (core_dir / "auth_handler.py").write_text("# handler\n")
    (core_dir / "config.py").write_text("# config\n")

    result = validate_location(
        {"file": "vivarium/core/auth_v2.py", "confidence": 90},
        tmp_path,
    )

    assert result.is_valid is False
    assert len(result.alternatives) >= 1
    assert "vivarium/core/auth.py" in result.alternatives
    assert result.validation_time_ms < 10


def test_relative_vs_absolute_path(tmp_path: Path):
    """Both relative and absolute paths resolve correctly."""
    core_dir = tmp_path / "vivarium" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "foo.py").write_text("def bar(): pass\n")

    rel_result = validate_location(
        {"file": "vivarium/core/foo.py", "confidence": 90},
        tmp_path,
    )
    abs_result = validate_location(
        {"file": str(core_dir / "foo.py"), "confidence": 90},
        tmp_path,
    )

    assert rel_result.is_valid is True
    assert abs_result.is_valid is True
    assert rel_result.actual_file == abs_result.actual_file


def test_symlink_loop_detection(tmp_path: Path):
    """Symlink loops are detected and rejected."""
    core_dir = tmp_path / "vivarium" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "real.py").write_text("def foo(): pass\n")
    loop_link = core_dir / "loop.py"
    loop_link.symlink_to(loop_link)  # self-referential symlink

    result = validate_location(
        {"file": "vivarium/core/loop.py", "confidence": 90},
        tmp_path,
    )

    assert result.is_valid is False
    assert result.actual_file is None
    assert result.validation_time_ms < 10


def test_validation_time_under_10ms(tmp_path: Path):
    """Validation completes in <10ms."""
    core_dir = tmp_path / "vivarium" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "auth.py").write_text("def auth(): pass\n")

    result = validate_location(
        {"file": "vivarium/core/auth.py", "function": "auth", "confidence": 90},
        tmp_path,
    )

    assert result.validation_time_ms < 10, (
        f"Validation took {result.validation_time_ms}ms, must be <10ms"
    )
