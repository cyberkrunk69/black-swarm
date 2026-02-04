"""quality_validator.py

Utility module that provides a set of quality‑validation helpers for generated
code snippets. The functions are deliberately lightweight and avoid any
external dependencies.

Functions
---------
- `validate_no_markdown_fences(code: str) -> bool`
- `validate_no_placeholders(code: str) -> bool`
- `validate_syntax(code: str, language: str) -> bool`
- `validate_not_smaller(old_content: str, new_content: str) -> bool`
- `validate_all(code: str, filepath: str) -> Tuple[bool, List[str]]`
"""

from __future__ import annotations

import ast
import os
from typing import List, Tuple


def validate_no_markdown_fences(code: str) -> bool:
    """
    Ensure that the supplied source does **not** contain markdown fence
    delimiters (e.g. `````python`` or ````` ```).  Presence of such fences
    indicates that the snippet was copied directly from a markdown block
    rather than being pure source code.

    Returns
    -------
    bool
        ``True`` if no fences are found, ``False`` otherwise.
    """
    fence_markers = ["```python", "```"]
    lowered = code.lower()
    return not any(marker in lowered for marker in fence_markers)


def validate_no_placeholders(code: str) -> bool:
    """
    Detect obvious placeholder tokens that should not appear in production
    code.  The check is intentionally simple – it looks for common patterns
    such as ``TODO``, ``pass # TODO`` and the use of ``random()`` as a stub.

    Returns
    -------
    bool
        ``True`` if no placeholders are detected, ``False`` otherwise.
    """
    placeholders = ["todo", "pass # todo", "random()"]
    lowered = code.lower()
    return not any(ph in lowered for ph in placeholders)


def validate_syntax(code: str, language: str) -> bool:
    """
    Verify that the source code is syntactically valid for the given language.
    Currently only Python is supported; for other languages the function
    returns ``True`` (no validation performed).

    Parameters
    ----------
    code : str
        Source code to validate.
    language : str
        Programming language identifier (e.g. ``python``).

    Returns
    -------
    bool
        ``True`` if the syntax is valid (or language not supported), ``False``
        otherwise.
    """
    if language.lower() != "python":
        # No syntax validator for other languages at the moment.
        return True

    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def validate_not_smaller(old_content: str, new_content: str) -> bool:
    """
    Ensure that the new file content is at least as large as the previous
    version.  This prevents accidental truncation.

    Returns
    -------
    bool
        ``True`` if ``len(new_content) >= len(old_content)``, ``False`` otherwise.
    """
    return len(new_content) >= len(old_content)


def validate_all(code: str, filepath: str) -> Tuple[bool, List[str]]:
    """
    Run the full suite of validation checks on a code snippet.

    Parameters
    ----------
    code : str
        The source code to validate.
    filepath : str
        Destination path where the code would be written.  The file extension
        is used to infer the language for syntax validation.

    Returns
    -------
    Tuple[bool, List[str]]
        ``(passed, errors)`` where ``passed`` is ``True`` if *all* checks succeed
        and ``errors`` is a list of human‑readable messages for the failing
        checks.
    """
    errors: List[str] = []

    # 1. Markdown fences
    if not validate_no_markdown_fences(code):
        errors.append("Markdown fence detected (``` or ```python).")

    # 2. Placeholders
    if not validate_no_placeholders(code):
        errors.append("Placeholder text detected (TODO / random()).")

    # 3. Syntax (infer language from extension)
    _, ext = os.path.splitext(filepath)
    language = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".go": "go",
    }.get(ext.lower(), "unknown")

    if not validate_syntax(code, language):
        errors.append(f"Syntax error detected for language '{language}'.")

    # 4. Size check against existing file (if any)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                old_content = f.read()
            if not validate_not_smaller(old_content, code):
                errors.append(
                    "New content is smaller than existing file (possible truncation)."
                )
        except Exception as exc:
            # If we cannot read the old file, we treat it as a non‑fatal warning.
            errors.append(f"Unable to read existing file for size check: {exc}")

    passed = not errors
    return passed, errors