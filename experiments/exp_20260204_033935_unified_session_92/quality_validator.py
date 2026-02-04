import ast
import re
from typing import List, Tuple


def validate_no_markdown_fences(code: str) -> bool:
    """
    Ensure the code does not contain Markdown fence markers like ````python`` or ````.
    Returns True if no fences are found.
    """
    fence_pattern = re.compile(r"```(?:python)?", re.IGNORECASE)
    return not bool(fence_pattern.search(code))


def validate_no_placeholders(code: str) -> bool:
    """
    Ensure the code does not contain common placeholder patterns such as TODO comments,
    ``pass  # TODO`` and calls to ``random()`` that are often used as stubs.
    Returns True if no placeholders are found.
    """
    placeholders = [
        r"\bTODO\b",
        r"pass\s*#\s*TODO",
        r"\brandom\(\)",
    ]
    for pattern in placeholders:
        if re.search(pattern, code):
            return False
    return True


def validate_syntax(code: str, language: str) -> bool:
    """
    Validate the syntax of the supplied code for the given language.
    Currently only Python is supported; for other languages the function
    returns True (no validation performed).
    """
    if language.lower() != "python":
        # No syntax validation for non‑Python languages at the moment.
        return True
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def validate_not_smaller(old_content: str, new_content: str) -> bool:
    """
    Ensure that the new content is at least as large (in characters) as the old content.
    """
    return len(new_content) >= len(old_content)


def validate_all(code: str, filepath: str) -> Tuple[bool, List[str]]:
    """
    Run all validation checks on the supplied code.

    Parameters
    ----------
    code: str
        The source code to validate.
    filepath: str
        Path of the file that will receive the code. The file extension is used
        to infer the language (e.g., ``.py`` → Python).

    Returns
    -------
    Tuple[bool, List[str]]
        A tuple where the first element indicates overall success and the second
        element contains a list of error messages for the checks that failed.
    """
    errors: List[str] = []

    # 1. Markdown fences
    if not validate_no_markdown_fences(code):
        errors.append("Markdown fence markers (``` or ```python) detected.")

    # 2. Placeholders
    if not validate_no_placeholders(code):
        errors.append("Placeholder patterns (TODO, pass # TODO, random()) detected.")

    # 3. Syntax (infer language from file extension)
    language = "python" if filepath.lower().endswith(".py") else "unknown"
    if not validate_syntax(code, language):
        errors.append(f"Syntax validation failed for {language} code.")

    # 4. Size comparison – only if the file already exists
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            old_content = f.read()
        if not validate_not_smaller(old_content, code):
            errors.append("New content is smaller than the existing file content.")
    except FileNotFoundError:
        # No existing file – size check is not applicable.
        pass
    except OSError as e:
        errors.append(f"Unable to read existing file for size check: {e}")

    passed = not errors
    return passed, errors