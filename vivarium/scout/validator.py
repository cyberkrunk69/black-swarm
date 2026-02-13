"""
Scout validator: zero-cost validation layer that prevents LLMs from inventing
file paths that don't exist.

All operations are filesystem/git — $0 cost, <10ms.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


# Error category codes for retry logic
HALLUCINATED_PATH = "HALLUCINATED_PATH"
HALLUCINATED_SYMBOL = "HALLUCINATED_SYMBOL"
WRONG_LINE = "WRONG_LINE"
LOW_CONFIDENCE = "LOW_CONFIDENCE"
VALID = "VALID"


@dataclass
class ValidationResult:
    """Result of validate_location() — captures truth and alternatives for retry."""

    is_valid: bool
    adjusted_confidence: int  # 0-100
    actual_file: Optional[Path]  # None if hallucinated
    actual_line: Optional[int]  # None if symbol not found
    symbol_snippet: Optional[str]  # First 3 lines of function
    alternatives: List[str]  # Suggested corrections
    validation_time_ms: float
    error_code: str = VALID


def _levenshtein_distance(a: str, b: str) -> int:
    """Pure Python Levenshtein distance. O(n*m), fine for short strings."""
    if len(a) < len(b):
        return _levenshtein_distance(b, a)
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(
                min(
                    prev[j + 1] + 1,
                    curr[j] + 1,
                    prev[j] + (0 if ca == cb else 1),
                )
            )
        prev = curr
    return prev[-1]


def _similarity(a: str, b: str) -> float:
    """Return similarity ratio 0-1 based on Levenshtein."""
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    max_len = max(len(a), len(b))
    return 1.0 - (_levenshtein_distance(a, b) / max_len)


def _resolve_path(path: Path, repo_root: Path) -> Path:
    """Resolve relative paths against repo_root, handle absolute."""
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _path_exists_safe(path: Path, repo_root: Path) -> tuple[bool, Optional[Path], bool]:
    """
    Check path existence. Returns (exists, resolved_path, symlink_loop_detected).
    Follows symlinks but detects loops via visited set or Path.resolve() RuntimeError.
    """
    try:
        resolved = _resolve_path(path, repo_root)
    except RuntimeError:
        # Path.resolve() raises RuntimeError for symlink loops
        return False, None, True
    visited: set[Path] = set()
    current = resolved
    while current.is_symlink():
        if current in visited:
            return False, None, True  # symlink loop
        visited.add(current)
        try:
            current = current.resolve()
        except (OSError, RuntimeError):
            return False, None, False
    return current.exists(), (current if current.exists() else resolved), False


def _find_sibling_files(
    parent_dir: Path, suggested_name: str, repo_root: Path, limit: int = 5
) -> List[str]:
    """
    Scan sibling files for similar names using Levenshtein distance.
    Returns paths relative to repo_root.
    """
    if not parent_dir.exists():
        return []
    candidates: List[tuple[float, str]] = []
    for p in parent_dir.iterdir():
        if p.is_file():
            sim = _similarity(p.name, suggested_name)
            if sim > 0.3:  # reasonable threshold
                try:
                    rel = str(p.relative_to(repo_root))
                except ValueError:
                    rel = str(p)
                candidates.append((sim, rel))
    candidates.sort(key=lambda x: (-x[0], x[1]))
    return [c[1] for c in candidates[:limit]]


def _grep_symbol(
    file_path: Path, symbol: str
) -> tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Grep for def {symbol} or class {symbol} in file.
    Returns (line_number, symbol_found, snippet) or (None, None, None) if not found.
    Handles multiple matches — returns first match; caller can disambiguate by line.
    """
    pattern_def = re.compile(rf"^\s*def\s+{re.escape(symbol)}\s*\(")
    pattern_class = re.compile(rf"^\s*class\s+{re.escape(symbol)}\s*[:(]")
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None, None, None
    for i, line in enumerate(lines):
        if pattern_def.match(line) or pattern_class.match(line):
            snippet_lines = lines[i : i + 3]
            snippet = "\n".join(snippet_lines) if snippet_lines else None
            return i + 1, symbol, snippet
    # Fuzzy match: find def/class with similar name
    base_name = symbol.split("_")[0] if "_" in symbol else symbol
    for i, line in enumerate(lines):
        m = re.match(r"^\s*(def|class)\s+(\w+)\s*[:(]", line)
        if m:
            found_name = m.group(2)
            if _similarity(found_name, symbol) >= 0.6:
                snippet_lines = lines[i : i + 3]
                snippet = "\n".join(snippet_lines) if snippet_lines else None
                return i + 1, found_name, snippet
    return None, None, None


def _get_symbol_snippet(file_path: Path, line_number: int) -> Optional[str]:
    """Return first 3 lines of function/class at given line."""
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    i = line_number - 1
    if i < 0 or i >= len(lines):
        return None
    return "\n".join(lines[i : i + 3])


class Validator:
    """Thin wrapper around validate_location for dependency injection."""

    def validate(self, suggestion: dict, repo_root: Path) -> ValidationResult:
        return validate_location(suggestion, repo_root)


def validate_location(suggestion: dict, repo_root: Path) -> ValidationResult:
    """
    Returns (is_valid, confidence_adjusted, context_for_retry).
    All operations are filesystem/git — $0 cost, <10ms.
    """
    start = time.perf_counter()
    file_str = suggestion.get("file", "")
    symbol = suggestion.get("function") or suggestion.get("symbol", "")
    suggested_line = suggestion.get("line")
    confidence = suggestion.get("confidence", 100)

    # 1. Confidence check — reject before filesystem
    if confidence < 70:
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult(
            is_valid=False,
            adjusted_confidence=confidence,
            actual_file=None,
            actual_line=None,
            symbol_snippet=None,
            alternatives=[],
            validation_time_ms=elapsed,
            error_code=LOW_CONFIDENCE,
        )

    repo_root = Path(repo_root).resolve()
    path = Path(file_str)

    # 2. Path existence
    exists, resolved_path, symlink_loop = _path_exists_safe(path, repo_root)
    if symlink_loop:
        elapsed = (time.perf_counter() - start) * 1000
        parent = path.parent
        suggested_name = path.name
        alternative_files = _find_sibling_files(
            _resolve_path(parent, repo_root), suggested_name, repo_root
        )
        return ValidationResult(
            is_valid=False,
            adjusted_confidence=0,
            actual_file=None,
            actual_line=None,
            symbol_snippet=None,
            alternatives=alternative_files,
            validation_time_ms=elapsed,
            error_code=HALLUCINATED_PATH,
        )
    if not exists:
        elapsed = (time.perf_counter() - start) * 1000
        parent = path.parent
        suggested_name = path.name
        alternative_files = _find_sibling_files(
            _resolve_path(parent, repo_root), suggested_name, repo_root
        )
        return ValidationResult(
            is_valid=False,
            adjusted_confidence=0,
            actual_file=None,
            actual_line=None,
            symbol_snippet=None,
            alternatives=alternative_files,
            validation_time_ms=elapsed,
            error_code=HALLUCINATED_PATH,
        )

    # 3. Symbol validation (if symbol provided)
    actual_file = resolved_path
    actual_line = None
    symbol_snippet = None
    alternatives: List[str] = []
    adjusted = confidence

    if symbol:
        line_num, found_symbol, snippet = _grep_symbol(actual_file, symbol)
        if line_num is None:
            # Symbol not found — downgrade, search for similar
            adjusted = max(0, confidence - 30)
            elapsed = (time.perf_counter() - start) * 1000
            return ValidationResult(
                is_valid=False,
                adjusted_confidence=adjusted,
                actual_file=actual_file,
                actual_line=None,
                symbol_snippet=None,
                alternatives=alternatives,
                validation_time_ms=elapsed,
                error_code=HALLUCINATED_SYMBOL,
            )
        actual_line = line_num
        symbol_snippet = snippet
        if found_symbol != symbol:
            # Fuzzy match — still valid but note the correction
            pass
        if suggested_line is not None and suggested_line != actual_line:
            # WRONG_LINE — correct line, proceed as valid
            adjusted = min(100, confidence + 5)  # slight upgrade for correction
        else:
            adjusted = min(100, confidence + 10)  # exact match upgrade

    # 4. All valid
    elapsed = (time.perf_counter() - start) * 1000
    return ValidationResult(
        is_valid=True,
        adjusted_confidence=adjusted,
        actual_file=actual_file,
        actual_line=actual_line,
        symbol_snippet=symbol_snippet,
        alternatives=[],
        validation_time_ms=elapsed,
        error_code=VALID,
    )
