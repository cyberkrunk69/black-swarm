import ast
import os
import re

def _strip_markdown(code: str) -> str:
    """Remove markdown fences and any surrounding markdown formatting."""
    # Remove triple backticks with optional language specifier
    code = re.sub(r"```(?:python)?\s*", "", code)
    code = re.sub(r"\s*```", "", code)
    return code.strip()

def validate_syntax(code: str) -> bool:
    """Return True if `code` parses without SyntaxError."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def is_complex_enough(existing_path: str, new_code: str) -> bool:
    """
    Return True if the existing file is at least as large (lines or characters)
    as the new content, preventing a complex file from being replaced by a simpler one.
    """
    if not os.path.exists(existing_path):
        return True
    with open(existing_path, "r", encoding="utf-8") as f:
        existing = f.read()
    return len(existing) >= len(new_code)

def safe_write(file_path: str, code: str) -> bool:
    """
    Validate and write `code` to `file_path` only if all quality rules pass.
    Returns True on success, False otherwise.
    """
    # 1. Strip markdown formatting
    clean_code = _strip_markdown(code)

    # 2. Validate syntax
    if not validate_syntax(clean_code):
        return False

    # 3. Ensure we are not overwriting a more complex file with a simpler one
    if not is_complex_enough(file_path, clean_code):
        return False

    # 4. Write safely (create directories if needed)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(clean_code)
    return True