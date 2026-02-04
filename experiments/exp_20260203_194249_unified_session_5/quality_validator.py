import ast
import os
import re

def validate_code_syntax(code: str) -> bool:
    """
    Return True if ``code`` parses as valid Python, otherwise False.
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def is_complex_enough(old_content: str, new_content: str) -> bool:
    """
    Simple heuristic: consider the new content acceptable only if it is
    at least as long as the old content.  This can be replaced with a
    more sophisticated static‑analysis check if needed.
    """
    return len(new_content) >= len(old_content)


def contains_markdown_fences(text: str) -> bool:
    """Detect any markdown code fences (``` or ```python etc.)."""
    return bool(re.search(r"```", text))


def strip_markdown_formatting(text: str) -> str:
    """
    Remove markdown fences and any surrounding whitespace while preserving
    the raw code inside the fences.
    """
    # Remove leading/trailing fences and any language specifier
    cleaned = re.sub(r"```[a-zA-Z]*\n?", "", text)
    cleaned = re.sub(r"\n?```", "", cleaned)
    return cleaned.strip()


def validate_output(output: str, target_path: str) -> bool:
    """
    Apply all quality rules to ``output`` before it is written to ``target_path``.
    Returns True if the output passes every check.
    """
    # 1. No markdown fences
    if contains_markdown_fences(output):
        return False

    # 2. Syntax must be valid
    if not validate_code_syntax(output):
        return False

    # 3. If the file exists, ensure we are not overwriting a larger/complex file
    if os.path.exists(target_path):
        with open(target_path, "r", encoding="utf-8") as f:
            existing = f.read()
        if not is_complex_enough(existing, output):
            return False
        # Also ensure the existing file is not larger than the new one
        if os.path.getsize(target_path) > len(output.encode("utf-8")):
            return False

    return True


def write_validated_code(output: str, target_path: str) -> None:
    """
    Strip markdown, validate, and write ``output`` to ``target_path``.
    Raises RuntimeError if validation fails.
    """
    cleaned = strip_markdown_formatting(output)

    if not validate_output(cleaned, target_path):
        raise RuntimeError(f"Validation failed for {target_path}")

    # Ensure the directory exists
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(cleaned)


# Example usage (for manual testing)
if __name__ == "__main__":
    sample_output = "print('Hello, world!')"
    dest = "example.py"
    try:
        write_validated_code(sample_output, dest)
        print(f"Successfully wrote validated code to {dest}")
    except RuntimeError as e:
        print(str(e))