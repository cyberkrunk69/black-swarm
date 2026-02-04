import os
import ast
import re

class QualityValidator:
    """
    Enforces the quality rules defined in QUALITY_RULES.md.
    """

    MARKDOWN_FENCE_PATTERN = re.compile(r"```")
    TODO_PATTERN = re.compile(r"#\s*TODO\b")
    MARKDOWN_FORMATTING_PATTERN = re.compile(r"(\*\*|\*|__|_)")

    def __init__(self, file_path: str):
        self.file_path = file_path

    def _read_content(self) -> str:
        with open(self.file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _check_markdown_fences(self, content: str):
        if self.MARKDOWN_FENCE_PATTERN.search(content):
            raise ValueError("Markdown code fences are not allowed in code files.")

    def _check_todo_comments(self, content: str):
        if self.TODO_PATTERN.search(content):
            raise ValueError("TODO comments must be implemented before committing.")

    def _validate_syntax(self, content: str):
        try:
            ast.parse(content)
        except SyntaxError as e:
            raise ValueError(f"Syntax error detected: {e}")

    def _check_overwrite_safety(self, new_content: str):
        if os.path.exists(self.file_path):
            existing_size = os.path.getsize(self.file_path)
            new_size = len(new_content.encode("utf-8"))
            if existing_size > new_size:
                raise ValueError(
                    "Refusing to overwrite a larger file with a smaller one."
                )

    def _strip_markdown_formatting(self, content: str) -> str:
        # Remove simple markdown formatting symbols; more complex cases can be added later.
        return self.MARKDOWN_FORMATTING_PATTERN.sub("", content)

    def validate_and_clean(self) -> str:
        """
        Runs all quality checks and returns cleaned content ready for saving.
        """
        raw_content = self._read_content()
        self._check_markdown_fences(raw_content)
        self._check_todo_comments(raw_content)
        self._validate_syntax(raw_content)
        self._check_overwrite_safety(raw_content)
        cleaned_content = self._strip_markdown_formatting(raw_content)
        return cleaned_content


# Example usage (for manual testing only)
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python quality_validator.py <path_to_code_file>")
        sys.exit(1)

    validator = QualityValidator(sys.argv[1])
    try:
        cleaned = validator.validate_and_clean()
        print("Validation passed. Cleaned content:")
        print(cleaned)
    except ValueError as err:
        print(f"Validation failed: {err}")