import ast
import os
from typing import List, Tuple


def validate_no_markdown_fences(code: str) -> bool:
    """
    Ensure the supplied code does not contain Markdown code fences.
    Detects both generic ``` and language‑specific ```python fences.
    """
    fences = ["```python", "```"]
    return not any(fence in code for fence in fences)


def validate_no_placeholders(code: str) -> bool:
    """
    Detect common placeholder patterns that should not be committed.
    Looks for:
        - TODO comments
        - pass # TODO
        - the literal string "random()" (often used as a stub)
    """
    placeholders = ["TODO", "pass # TODO", "random()"]
    lowered = code.lower()
    return not any(ph.lower() in lowered for ph in placeholders)


def validate_syntax(code: str, language: str) -> bool:
    """
    Validate syntax for the given language.
    Currently only Python is supported; other languages return True
    (they are assumed to be handled elsewhere).
    """
    if language.lower() != "python":
        return True
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def validate_not_smaller(old_content: str, new_content: str) -> bool:
    """
    Ensure that the new content is not smaller than the old content.
    This guards against accidental truncation.
    """
    return len(new_content) >= len(old_content)


def validate_all(code: str, filepath: str) -> Tuple[bool, List[str]]:
    """
    Run all validation checks on the supplied code.

    Returns:
        (passed, errors) where `passed` is True only if every check succeeds.
    """
    errors: List[str] = []

    # 1. Markdown fences
    if not validate_no_markdown_fences(code):
        errors.append("Markdown code fences (``` or ```python) detected.")

    # 2. Placeholders
    if not validate_no_placeholders(code):
        errors.append("Placeholder text (TODO, pass # TODO, random()) detected.")

    # 3. Syntax (Python only)
    _, ext = os.path.splitext(filepath)
    language = "python" if ext == ".py" else ext.lstrip(".")
    if not validate_syntax(code, language):
        errors.append(f"Syntax error detected for language '{language}'.")

    # 4. Size check – compare with existing file if it exists
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                old_content = f.read()
            if not validate_not_smaller(old_content, code):
                errors.append("New content is smaller than the existing file.")
        except Exception as exc:
            errors.append(f"Failed to read existing file for size check: {exc}")

    passed = len(errors) == 0
    return passed, errors