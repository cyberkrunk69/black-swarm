# validator.py

## Class: `ValidationResult`

Detailed documentation (deep stub).

```python
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
```

## Function: `_levenshtein_distance`

Detailed documentation (deep stub).

```python
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
                    prev[
```

## Function: `_similarity`

Detailed documentation (deep stub).

```python
def _similarity(a: str, b: str) -> float:
    """Return similarity ratio 0-1 based on Levenshtein."""
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    max_len = max(len(a), len(b))
    return 1.0 - (_levenshtein_distance(a, b) / max_len)
```

## Function: `_resolve_path`

Detailed documentation (deep stub).

```python
def _resolve_path(path: Path, repo_root: Path) -> Path:
    """Resolve relative paths against repo_root, handle absolute."""
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()
```

## Function: `_path_exists_safe`

Detailed documentation (deep stub).

```python
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
    current = r
```

## Function: `_find_sibling_files`

Detailed documentation (deep stub).

```python
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

```

## Function: `_grep_symbol`

Detailed documentation (deep stub).

```python
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

```

## Function: `_get_symbol_snippet`

Detailed documentation (deep stub).

```python
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
```

## Class: `Validator`

Detailed documentation (deep stub).

```python
class Validator:
    """Thin wrapper around validate_location for dependency injection."""

    def validate(self, suggestion: dict, repo_root: Path) -> ValidationResult:
        return validate_location(suggestion, repo_root)
```

## Function: `validate_location`

Detailed documentation (deep stub).

```python
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

    # 1. Confidence check — reject before fi
```

## Function: `validate`

Detailed documentation (deep stub).

```python
    def validate(self, suggestion: dict, repo_root: Path) -> ValidationResult:
        return validate_location(suggestion, repo_root)
```
