import ast
from pathlib import Path
from typing import List, Tuple


def validate_no_markdown_fences(code: str) -> bool:
    """
    Ensure the code does not contain Markdown code fences such as ````python`` or ````.
    Returns True if no fences are found.
    """
    fences = ["```python", "```"]
    return not any(fence in code for fence in fences)


def validate_no_placeholders(code: str) -> bool:
    """
    Detect common placeholder patterns that should not appear in production code.
    Checks for:
      - The literal string "TODO"
      - The comment pattern "# TODO"
      - Calls to ``random()`` that are often left as placeholders
    Returns True if none of these patterns are present.
    """
    placeholders = ["TODO", "# TODO", "random()"]
    return not any(placeholder in code for placeholder in placeholders)


def validate_syntax(code: str, language: str) -> bool:
    """
    Validate the syntax of the supplied code.
    Currently only Python is supported; other languages return True by default.
    """
    if language.lower() != "python":
        # No syntax validator for other languages – assume OK
        return True
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def validate_not_smaller(old_content: str, new_content: str) -> bool:
    """
    Ensure that the new content is not smaller than the old content.
    Size comparison is based on the number of characters.
    """
    return len(new_content) >= len(old_content)


def validate_all(code: str, filepath: str) -> Tuple[bool, List[str]]:
    """
    Run the full suite of quality checks on ``code``.
    Returns a tuple (passed, error_messages).
    """
    errors: List[str] = []

    # 1. Markdown fences
    if not validate_no_markdown_fences(code):
        errors.append("Markdown code fences (``` or ```python) detected.")

    # 2. Placeholders
    if not validate_no_placeholders(code):
        errors.append("Placeholder text (TODO, # TODO, random()) detected.")

    # 3. Syntax (only for Python files)
    ext = Path(filepath).suffix.lower()
    language = "python" if ext == ".py" else ext.lstrip(".")
    if not validate_syntax(code, language):
        errors.append(f"Syntax error detected for {language} code.")

    # 4. Size regression check – compare with existing file if it exists
    if Path(filepath).exists():
        old_content = Path(filepath).read_text(encoding="utf-8")
        if not validate_not_smaller(old_content, code):
            errors.append("New content is smaller than the existing file.")

    passed = not errors
    return passed, errors