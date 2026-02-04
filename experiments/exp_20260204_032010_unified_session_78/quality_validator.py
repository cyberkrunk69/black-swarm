import ast
import os
from typing import List, Tuple


def validate_no_markdown_fences(code: str) -> bool:
    """
    Ensure the supplied code does not contain markdown fenced code blocks.
    Returns ``True`` if no fences are found, ``False`` otherwise.
    """
    # Look for any triple back‑ticks.  `````python````` is a common pattern,
    # but we also block generic fences.
    return "```" not in code


def validate_no_placeholders(code: str) -> bool:
    """
    Detect common placeholder patterns that should not be committed.
    Returns ``True`` when the code contains none of the disallowed tokens.
    """
    placeholders = [
        "TODO",                # generic marker
        "pass  # TODO",       # explicit python placeholder
        "pass # TODO",        # variant with single space
        "random()",           # often used as a stub for real logic
    ]
    # Case‑insensitive check for TODO variants
    lowered = code.lower()
    for token in placeholders:
        if token.lower() in lowered:
            return False
    return True


def validate_syntax(code: str, language: str) -> bool:
    """
    Validate the syntax of ``code`` for the given ``language``.
    Currently only Python is supported; other languages always return ``True``.
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
    Ensure that the new content is not smaller (in characters) than the old content.
    """
    return len(new_content) >= len(old_content)


def validate_all(code: str, filepath: str) -> Tuple[bool, List[str]]:
    """
    Run the full suite of quality checks on ``code``.
    Returns a tuple ``(passed, errors)`` where ``passed`` is ``True`` only if
    every check succeeds. ``errors`` contains human‑readable messages for any
    failed checks.
    """
    errors: List[str] = []

    # 1. Markdown fences
    if not validate_no_markdown_fences(code):
        errors.append("Markdown fenced code block (``` ) detected.")

    # 2. Place‑holder tokens
    if not validate_no_placeholders(code):
        errors.append("Placeholder token (TODO, pass # TODO, random()) detected.")

    # 3. Syntax check – infer language from file extension
    _, ext = os.path.splitext(filepath)
    language = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".go": "go",
    }.get(ext.lower(), "unknown")
    if not validate_syntax(code, language):
        errors.append(f"Syntax error detected for language: {language}.")

    # 4. Size sanity – compare against any existing file on disk
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                old_content = f.read()
            if not validate_not_smaller(old_content, code):
                errors.append(
                    "New content is smaller than the existing file; possible data loss."
                )
        except Exception as exc:
            # If we cannot read the old file, we treat it as a non‑fatal warning.
            errors.append(f"Unable to read existing file for size check: {exc}")

    passed = not errors
    return passed, errors