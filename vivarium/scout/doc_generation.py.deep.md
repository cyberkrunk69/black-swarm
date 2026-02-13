# doc_generation.py

## Function: `parse_python_file`

Detailed documentation (deep stub).

```python
def parse_python_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse a Python file and extract symbol info (classes, functions).

    Returns a list of dicts: {name, kind, line_start, line_end}.
    """
    if not file_path.exists() or not file_path.is_file():
        return []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(content, filename=str(file_path))
    except (OSError, SyntaxError) as e:
        logger.warning("Fa
```

## Function: `extract_source_snippet`

Detailed documentation (deep stub).

```python
def extract_source_snippet(file_path: Path, symbol: Dict[str, Any]) -> str:
    """Extract source code for a symbol from the file."""
    if not file_path.exists():
        return ""
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    line_start = symbol.get("line_start", 1)
    line_end = symbol.get("line_end", line_start)
    line_start = max(1, line_start)
    line_end = min(line_end, len(lines))
    snippet_l
```

## Function: `generate_tldr_content`

Detailed documentation (deep stub).

```python
def generate_tldr_content(symbol: Dict[str, Any], snippet: str, deps: Optional[Any] = None) -> str:
    """Generate tldr (summary) content for a symbol. Stub — replace with LLM call."""
    name = symbol.get("name", "?")
    kind = symbol.get("kind", "symbol")
    return f"## {kind.title()}: `{name}`\n\nBrief summary (tldr stub).\n"
```

## Function: `generate_deep_content`

Detailed documentation (deep stub).

```python
def generate_deep_content(symbol: Dict[str, Any], snippet: str, deps: Optional[Any] = None) -> str:
    """Generate deep (detailed) content for a symbol. Stub — replace with LLM call."""
    name = symbol.get("name", "?")
    kind = symbol.get("kind", "symbol")
    return f"## {kind.title()}: `{name}`\n\nDetailed documentation (deep stub).\n\n```python\n{snippet[:500]}\n```\n"
```

## Function: `validate_generated_docs`

Detailed documentation (deep stub).

```python
def validate_generated_docs(tldr_content: str, deep_content: str) -> Tuple[bool, Optional[str]]:
    """
    Validate generated documentation content.

    Returns (is_valid, error_message).
    """
    if not tldr_content or not tldr_content.strip():
        return False, "TLDR content is empty"
    if not deep_content or not deep_content.strip():
        return False, "Deep content is empty"
    if len(tldr_content) > 100_000 or len(deep_content) > 500_000:
        return False, "Content excee
```

## Function: `write_documentation_files`

Detailed documentation (deep stub).

```python
def write_documentation_files(
    file_path: Path,
    tldr_content: str,
    deep_content: str,
    output_dir: Optional[Path] = None,
) -> Tuple[Path, Path]:
    """
    Write documentation files for a Python file.

    If output_dir is provided:
        Writes filename.py.tldr.md and filename.py.deep.md inside output_dir.
    If output_dir is None:
        Writes file_path.tldr.md and file_path.deep.md adjacent to file_path.

    Creates output directory if needed. Overwrites existing files.
```

## Function: `process_single_file`

Detailed documentation (deep stub).

```python
def process_single_file(
    file_path: Path,
    output_dir: Optional[Path] = None,
    dependencies_func: Optional[Callable[[Path], Any]] = None,
) -> bool:
    """
    Process a single Python file: parse, generate, validate, write docs.

    Iterates through symbols, aggregates tldr and deep content per file,
    validates, and writes file.py.tldr.md and file.py.deep.md.

    Returns True if successful, False otherwise.
    """
    file_path = Path(file_path).resolve()
    if not file_path.ex
```

## Function: `process_directory`

Detailed documentation (deep stub).

```python
def process_directory(
    directory_path: Path,
    recursive: bool = True,
    output_dir: Optional[Path] = None,
    dependencies_func: Optional[Callable[[Path], Any]] = None,
) -> Tuple[int, int]:
    """
    Walk a directory and process all Python files.

    If recursive is True, processes subdirectories.
    Skips __pycache__, .git, and common non-source dirs.

    Returns (files_processed, files_failed).
    """
    directory_path = Path(directory_path).resolve()
    if not directory_pat
```
