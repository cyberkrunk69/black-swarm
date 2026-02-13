"""
Scout doc generation — process Python files and directories for documentation sync.

Provides process_single_file and process_directory for use by doc_sync CLI.
"""

from __future__ import annotations

import asyncio
import ast
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from vivarium.scout.audit import AuditLog
from vivarium.scout.config import ScoutConfig
from vivarium.scout.ignore import IgnorePatterns
from vivarium.scout.llm import call_groq_async

logger = logging.getLogger(__name__)

# Default model for TL;DR generation
TLDR_MODEL = "llama-3.1-8b-instant"

# Default model for deep content (use 70b for more detail if needed)
DEEP_MODEL = "llama-3.1-8b-instant"

# Default model for ELIV (Explain Like I'm Very Young) generation
ELIV_MODEL = "llama-3.1-8b-instant"


def _extract_logic_hints(node: ast.FunctionDef | ast.AsyncFunctionDef) -> List[str]:
    """Extract logic hints from a function/method body by scanning AST nodes."""
    hints: List[str] = []
    for child in ast.walk(node):
        if isinstance(child, (ast.For, ast.While)):
            if "loop" not in hints:
                hints.append("loop")
        elif isinstance(child, ast.If):
            if "conditional" not in hints:
                hints.append("conditional")
        elif isinstance(child, (ast.Try, ast.With, ast.Raise)):
            if "exception_handling" not in hints:
                hints.append("exception_handling")
        elif isinstance(child, ast.Return):
            if "return" not in hints:
                hints.append("return")
        elif isinstance(child, (ast.Yield, ast.YieldFrom)):
            if "generator" not in hints:
                hints.append("generator")
        elif isinstance(child, ast.Await):
            if "async" not in hints:
                hints.append("async")
        elif isinstance(child, ast.Call):
            if "call" not in hints:
                hints.append("call")
    return hints


def _build_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Build a signature string for a function or async function."""
    try:
        # Create a minimal node with empty body for unparsing (Python 3.9+)
        if isinstance(node, ast.AsyncFunctionDef):
            sig_node: ast.AST = ast.AsyncFunctionDef(
                name=node.name,
                args=node.args,
                body=[ast.Pass()],
                decorator_list=[],
                returns=node.returns,
            )
        else:
            sig_node = ast.FunctionDef(
                name=node.name,
                args=node.args,
                body=[ast.Pass()],
                decorator_list=[],
                returns=node.returns,
            )
        ast.copy_location(sig_node, node)
        unparsed = ast.unparse(sig_node)
        idx = unparsed.find(":\n")
        sig = unparsed[:idx] if idx != -1 else unparsed.replace(": pass", "").rstrip()
        return sig
    except (AttributeError, TypeError):
        pass
    # Fallback: manual signature from args
    prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
    parts: List[str] = []
    for arg in node.args.args:
        if arg.arg == "self" or arg.arg == "cls":
            continue
        parts.append(arg.arg)
    for i, default in enumerate(node.args.defaults):
        arg_idx = len(node.args.args) - len(node.args.defaults) + i
        if arg_idx >= 0 and node.args.args[arg_idx].arg not in ("self", "cls"):
            if arg_idx < len(parts):
                parts[arg_idx] = f"{parts[arg_idx]}=..."
    return prefix + node.name + "(" + ", ".join(parts) + ")"


def _parse_assign_targets(node: ast.Assign) -> List[str]:
    """Extract names from an assignment target (handles tuple unpacking)."""
    names: List[str] = []
    for target in node.targets:
        if isinstance(target, ast.Name):
            names.append(target.id)
        elif isinstance(target, ast.Tuple):
            for elt in target.elts:
                if isinstance(elt, ast.Name):
                    names.append(elt.id)
    return names


def parse_python_file(file_path: Path) -> Dict[str, Any]:
    """
    Parse a Python file using the AST and extract top-level symbols.

    Extracts classes, functions, async functions, methods, and module-level
    constants. For each symbol, captures name, type, line range, docstring,
    signature (for callables), and logic hints (for callables).

    Args:
        file_path: Path to the Python file to parse.

    Returns:
        A dict with keys:
        - path: str, the file path as string
        - symbols: list of symbol dicts, each with name, type, lineno,
          end_lineno, docstring, signature (callables), logic_hints (callables)
        - error: str or None, set if parsing failed

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a .py file.
    """
    file_path = Path(file_path).resolve()
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"Target file not found: {file_path}")
    if file_path.suffix != ".py":
        raise ValueError(f"Target is not a Python file: {file_path}")

    result: Dict[str, Any] = {
        "path": str(file_path),
        "symbols": [],
        "error": None,
    }

    try:
        content = file_path.read_text(encoding="utf-8", errors="strict")
    except UnicodeDecodeError as e:
        result["error"] = f"UnicodeDecodeError: {e}"
        logger.warning("Could not read %s: %s", file_path, e)
        return result
    except OSError as e:
        result["error"] = f"OSError: {e}"
        logger.warning("Could not read %s: %s", file_path, e)
        return result

    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError as e:
        result["error"] = f"SyntaxError: {e}"
        logger.warning("Could not parse %s: %s", file_path, e)
        return result

    symbols: List[Dict[str, Any]] = []

    def process_callable(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        symbol_type: str,
    ) -> Dict[str, Any]:
        end_lineno = getattr(node, "end_lineno", None) or node.lineno
        return {
            "name": node.name,
            "type": symbol_type,
            "lineno": node.lineno,
            "end_lineno": end_lineno,
            "docstring": ast.get_docstring(node),
            "signature": _build_signature(node),
            "logic_hints": _extract_logic_hints(node),
        }

    def process_class(cls: ast.ClassDef) -> Dict[str, Any]:
        end_lineno = getattr(cls, "end_lineno", None) or cls.lineno
        class_info: Dict[str, Any] = {
            "name": cls.name,
            "type": "class",
            "lineno": cls.lineno,
            "end_lineno": end_lineno,
            "docstring": ast.get_docstring(cls),
            "signature": None,
            "logic_hints": [],
        }
        symbols.append(class_info)
        for item in cls.body:
            if isinstance(item, ast.FunctionDef):
                method_info = process_callable(item, "method")
                method_info["lineno"] = item.lineno
                method_info["end_lineno"] = getattr(item, "end_lineno", None) or item.lineno
                symbols.append(method_info)
            elif isinstance(item, ast.AsyncFunctionDef):
                method_info = process_callable(item, "method")
                method_info["lineno"] = item.lineno
                method_info["end_lineno"] = getattr(item, "end_lineno", None) or item.lineno
                symbols.append(method_info)

    def process_constant(node: ast.Assign, lineno: int) -> None:
        for name in _parse_assign_targets(node):
            end_lineno = getattr(node, "end_lineno", None) or lineno
            symbols.append({
                "name": name,
                "type": "constant",
                "lineno": lineno,
                "end_lineno": end_lineno,
                "docstring": None,
                "signature": None,
                "logic_hints": [],
            })

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            symbols.append(process_callable(node, "function"))
        elif isinstance(node, ast.AsyncFunctionDef):
            symbols.append(process_callable(node, "async_function"))
        elif isinstance(node, ast.ClassDef):
            process_class(node)
        elif isinstance(node, ast.Assign):
            process_constant(node, node.lineno)

    result["symbols"] = symbols
    return result


def extract_source_snippet(file_path: Path, start_line: int, end_line: int) -> str:
    """
    Read a specific Python file and return the raw source code lines between
    start_line and end_line inclusive.

    Relies on accurate line numbers from parse_python_file.

    Args:
        file_path: Path to the Python file to read.
        start_line: First line number (1-indexed, inclusive).
        end_line: Last line number (1-indexed, inclusive).

    Returns:
        The source code snippet as a string, preserving original line endings.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
        UnicodeDecodeError: If the file cannot be decoded as UTF-8.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="strict") as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except OSError as e:
        raise IOError(f"Could not read file {file_path}: {e}") from e
    except UnicodeDecodeError:
        raise

    if not lines:
        return ""

    # Convert to zero-indexed
    start_idx = start_line - 1
    end_idx = end_line - 1

    # Clamp to valid range
    num_lines = len(lines)
    start_idx = max(0, min(start_idx, num_lines - 1))
    end_idx = max(0, min(end_idx, num_lines - 1))

    # Ensure start <= end
    if start_idx > end_idx:
        start_idx, end_idx = end_idx, start_idx

    snippet_lines = lines[start_idx : end_idx + 1]
    return "".join(snippet_lines)


def _build_tldr_prompt(symbol_info: Dict[str, Any], dependencies: List[str]) -> str:
    """Build the LLM prompt for TL;DR generation."""
    name = symbol_info.get("name", "unknown")
    symbol_type = symbol_info.get("type", "symbol")
    docstring = symbol_info.get("docstring") or "(no docstring)"
    signature = symbol_info.get("signature")
    logic_hints = symbol_info.get("logic_hints") or []

    purpose_parts = [f"Docstring: {docstring}"]
    if signature:
        purpose_parts.append(f"Signature: {signature}")
    if logic_hints:
        purpose_parts.append(f"Logic hints: {', '.join(logic_hints)}")

    deps_str = ", ".join(dependencies) if dependencies else "nothing specific"

    return f"""Provide a concise summary of the Python {symbol_type} '{name}'.

Purpose: Based on the following information:
{chr(10).join('- ' + p for p in purpose_parts)}

Interactions: Depends on {deps_str}.

Requirements:
- Keep it to 1-3 sentences max.
- Explain the primary purpose and key responsibilities.
- Briefly describe its relationship with the dependencies above (if any).
- Format as plain text or basic Markdown.

Output ONLY the summary, no preamble."""


async def _generate_tldr_async(symbol_info: Dict[str, Any], dependencies: List[str]) -> str:
    """Async implementation of TL;DR generation. Returns error string on non-RuntimeError failures."""
    try:
        prompt = _build_tldr_prompt(symbol_info, dependencies)
        response = await call_groq_async(
            prompt,
            model=TLDR_MODEL,
            system="You are a documentation assistant. Be concise and accurate.",
        )
        audit = AuditLog()
        audit.log(
            "tldr",
            cost=response.cost_usd,
            model=response.model,
            input_t=response.input_tokens,
            output_t=response.output_tokens,
            symbol=symbol_info.get("name"),
        )
        return response.content
    except RuntimeError:
        raise
    except Exception as e:
        logger.warning("TL;DR generation failed for %s: %s", symbol_info.get("name"), e)
        return f"[TL;DR generation failed: {e}]"


def generate_tldr_content(
    symbol_info: Dict[str, Any], dependencies: List[str]
) -> str:
    """
    Generate a concise, high-level summary (TL;DR) of a single symbol using an LLM.

    Synchronous wrapper that runs the async implementation via asyncio.run().
    Use _generate_tldr_async directly when already in an async context (e.g.
    within process_single_file_async) to avoid event loop conflicts.

    Uses Groq's llama-3.1-8b-instant to produce a 1-3 sentence summary based on
    the symbol's parsed information and dependencies. Cost is logged to the
    Scout audit trail.

    Args:
        symbol_info: Dict with name, type, docstring, signature, logic_hints.
        dependencies: List of dependency names/paths the symbol interacts with.

    Returns:
        The LLM-generated summary string, or an error message string on API failure.

    Raises:
        RuntimeError: If GROQ_API_KEY is not set.
    """
    return asyncio.run(_generate_tldr_async(symbol_info, dependencies))


def _build_deep_prompt(
    symbol_info: Dict[str, Any],
    dependencies: List[str],
    source_code_snippet: str,
) -> str:
    """Build the LLM prompt for deep content generation."""
    name = symbol_info.get("name", "unknown")
    symbol_type = symbol_info.get("type", "symbol")
    docstring = symbol_info.get("docstring") or "(no docstring)"
    signature = symbol_info.get("signature")
    logic_hints = symbol_info.get("logic_hints") or []

    deps_str = ", ".join(dependencies) if dependencies else "None"
    hints_str = ", ".join(logic_hints) if logic_hints else "None"

    return f"""Analyze the following Python {symbol_type} '{name}'.

Context:
- Docstring: {docstring}
- Signature: {signature or 'N/A'}

Source Code:
```
{source_code_snippet}
```

Dependencies: {deps_str}
Logic Hints: {hints_str}

Provide a detailed breakdown using Markdown headings (##) for each section:

1. ## Logic Overview — Explain the code's flow and main steps.
2. ## Dependency Interactions — How does it use the listed dependencies?
3. ## Potential Considerations — Edge cases, error handling, performance notes from the code.
4. ## Signature — If applicable, include: `{signature or 'N/A'}`

Format using Markdown headings ## for each section. Be structured, detailed, and code-relevant."""


async def _generate_deep_content_async(
    symbol_info: Dict[str, Any],
    dependencies: List[str],
    source_code_snippet: str,
) -> str:
    """Async implementation of deep content generation. Returns error string on non-RuntimeError failures."""
    try:
        prompt = _build_deep_prompt(symbol_info, dependencies, source_code_snippet)
        response = await call_groq_async(
            prompt,
            model=DEEP_MODEL,
            system="You are a documentation assistant. Provide structured, detailed analysis of Python code.",
            max_tokens=1500,
        )
        audit = AuditLog()
        audit.log(
            "deep",
            cost=response.cost_usd,
            model=response.model,
            input_t=response.input_tokens,
            output_t=response.output_tokens,
            symbol=symbol_info.get("name"),
        )
        return response.content
    except RuntimeError:
        raise
    except Exception as e:
        logger.warning("Deep content generation failed for %s: %s", symbol_info.get("name"), e)
        return f"[Deep content generation failed: {e}]"


def generate_deep_content(
    symbol_info: Dict[str, Any],
    dependencies: List[str],
    source_code_snippet: str,
) -> str:
    """
    Generate a detailed breakdown of a single symbol using an LLM.

    Synchronous wrapper that runs the async implementation via asyncio.run().
    Use _generate_deep_content_async directly when already in an async context.

    Uses Groq's llama-3.1-8b-instant to produce a structured analysis based on
    the symbol's parsed information, dependencies, and source code snippet.
    Cost is logged to the Scout audit trail.

    Args:
        symbol_info: Dict with name, type, docstring, signature, logic_hints.
        dependencies: List of dependency names/paths the symbol interacts with.
        source_code_snippet: Raw source code of the symbol.

    Returns:
        The LLM-generated Markdown content as a string, or an error message
        string on API failure.

    Raises:
        RuntimeError: If GROQ_API_KEY is not set.
    """
    return asyncio.run(
        _generate_deep_content_async(
            symbol_info,
            dependencies,
            source_code_snippet,
        )
    )


def _build_eliv_prompt(
    symbol_info: Dict[str, Any],
    dependencies: List[str],
    source_code_snippet: str,
) -> str:
    """Build the LLM prompt for ELIV (Explain Like I'm Very Young) generation."""
    name = symbol_info.get("name", "unknown")
    symbol_type = symbol_info.get("type", "symbol")
    docstring = symbol_info.get("docstring") or ""
    signature = symbol_info.get("signature")
    logic_hints = symbol_info.get("logic_hints") or []

    purpose_parts: List[str] = []
    if docstring:
        purpose_parts.append(f"Docstring: {docstring}")
    if signature:
        purpose_parts.append(f"Signature: {signature}")
    if logic_hints:
        purpose_parts.append(f"Logic hints: {', '.join(logic_hints)}")

    purpose_desc = (
        ", ".join(purpose_parts)
        if purpose_parts
        else "(infer from the code below)"
    )
    deps_str = ", ".join(dependencies) if dependencies else "nothing special"

    return f"""Explain the Python {symbol_type} '{name}' like I'm very young (around 5 years old).

Its job is to: {purpose_desc}.

It interacts with: {deps_str}.

Here is the code (don't repeat it, just understand it):
```
{source_code_snippet}
```

Use very simple words. Avoid technical jargon. Use analogies if helpful (like "it's like a key that opens a door").
Focus on what it *does*, not how it does it (unless the "how" is very simple).
Keep it short and sweet. Output ONLY the explanation, no preamble."""


async def _generate_eliv_async(
    symbol_info: Dict[str, Any],
    dependencies: List[str],
    source_code_snippet: str,
) -> str:
    """Async implementation of ELIV generation. Returns error string on non-RuntimeError failures."""
    try:
        prompt = _build_eliv_prompt(symbol_info, dependencies, source_code_snippet)
        response = await call_groq_async(
            prompt,
            model=ELIV_MODEL,
            system="You are a friendly assistant that explains code in very simple terms for young children.",
            max_tokens=450,
        )
        audit = AuditLog()
        audit.log(
            "eliv",
            cost=response.cost_usd,
            model=response.model,
            input_t=response.input_tokens,
            output_t=response.output_tokens,
            symbol=symbol_info.get("name"),
        )
        return response.content
    except RuntimeError:
        raise
    except Exception as e:
        logger.warning("ELIV generation failed for %s: %s", symbol_info.get("name"), e)
        return f"[ELIV generation failed: {e}]"


def generate_eliv_content(
    symbol_info: Dict[str, Any],
    dependencies: List[str],
    source_code_snippet: str,
) -> str:
    """
    Generate a simplified, "Explain Like I'm Very Young" (ELIV) explanation for a
    code symbol, suitable for beginners or those unfamiliar with the codebase.

    Synchronous wrapper that runs the async implementation via asyncio.run().
    Use _generate_eliv_async directly when already in an async context.

    Uses Groq's llama-3.1-8b-instant to produce a simple explanation based on
    the symbol's parsed information, dependencies, and source code. Cost is
    logged to the Scout audit trail.

    Args:
        symbol_info: Dict with name, type, docstring, signature, logic_hints.
        dependencies: List of dependency names/paths the symbol interacts with.
        source_code_snippet: Raw source code of the symbol.

    Returns:
        The LLM-generated ELIV content as a string, or an error message string
        on API failure.

    Raises:
        RuntimeError: If GROQ_API_KEY is not set.
    """
    return asyncio.run(
        _generate_eliv_async(
            symbol_info,
            dependencies,
            source_code_snippet,
        )
    )


def validate_generated_docs(
    symbol: Dict[str, Any],
    tldr_content: str,
    deep_content: str,
) -> Tuple[bool, List[str]]:
    """
    Validate generated documentation content for a symbol.

    Args:
        symbol: Symbol dict (for context in error messages).
        tldr_content: Generated TL;DR content.
        deep_content: Generated deep content.

    Returns:
        (is_valid, list of error messages).
    """
    errors: List[str] = []
    name = symbol.get("name", "?")

    if not tldr_content or not tldr_content.strip():
        errors.append(f"TL;DR content is empty for symbol '{name}'")
    elif tldr_content.strip().startswith("[TL;DR generation failed:"):
        errors.append(f"TL;DR generation failed for symbol '{name}'")
    elif len(tldr_content) > 100_000:
        errors.append(f"TL;DR content exceeds size limit for symbol '{name}'")

    if not deep_content or not deep_content.strip():
        errors.append(f"Deep content is empty for symbol '{name}'")
    elif deep_content.strip().startswith("[Deep content generation failed:"):
        errors.append(f"Deep content generation failed for symbol '{name}'")
    elif len(deep_content) > 500_000:
        errors.append(f"Deep content exceeds size limit for symbol '{name}'")

    return (len(errors) == 0, errors)


def write_documentation_files(
    file_path: Path,
    tldr_content: str,
    deep_content: str,
    eliv_content: str = "",
    output_dir: Optional[Path] = None,
) -> Tuple[Path, Path, Path]:
    """
    Write documentation files for a Python file.

    If output_dir is provided:
        Writes <stem>.tldr.md, <stem>.deep.md, and <name>.eliv.md inside output_dir.
    If output_dir is None (default):
        Writes to local .docs/ next to source (e.g. vivarium/scout/.docs/ignore.py.tldr.md)
        and mirrors to central docs/livingDoc/ (e.g. docs/livingDoc/vivarium/scout/ignore.py.tldr.md).

    ELIV path: file_path.with_suffix(file_path.suffix + ".eliv.md") (e.g. ignore.py.eliv.md).

    Creates output directory if needed. Overwrites existing files.

    Returns:
        Tuple of (tldr_path, deep_path, eliv_path) for the primary (local) files.
    """
    file_path = Path(file_path).resolve()
    repo_root = Path.cwd().resolve()

    if output_dir is not None:
        out = Path(output_dir).resolve()
        out.mkdir(parents=True, exist_ok=True)
        base_name = file_path.stem  # e.g. "ignore" for ignore.py
        tldr_path = out / f"{base_name}.tldr.md"
        deep_path = out / f"{base_name}.deep.md"
        eliv_path = (out / file_path.name).with_suffix(file_path.suffix + ".eliv.md")
        mirror_to_central = False
    else:
        local_dir = file_path.parent / ".docs"
        local_dir.mkdir(parents=True, exist_ok=True)
        base_name = file_path.name  # e.g. "ignore.py" -> ignore.py.tldr.md
        tldr_path = local_dir / f"{base_name}.tldr.md"
        deep_path = local_dir / f"{base_name}.deep.md"
        eliv_path = local_dir / f"{base_name}.eliv.md"
        mirror_to_central = True

    tldr_path.write_text(tldr_content, encoding="utf-8")
    deep_path.write_text(deep_content, encoding="utf-8")
    eliv_path.write_text(eliv_content, encoding="utf-8")

    if mirror_to_central:
        try:
            rel = file_path.relative_to(repo_root)
            central_dir = repo_root / "docs" / "livingDoc" / rel.parent
            central_dir.mkdir(parents=True, exist_ok=True)
            central_tldr = central_dir / f"{file_path.name}.tldr.md"
            central_deep = central_dir / f"{file_path.name}.deep.md"
            central_eliv = central_dir / f"{file_path.name}.eliv.md"
            central_tldr.write_text(tldr_content, encoding="utf-8")
            central_deep.write_text(deep_content, encoding="utf-8")
            central_eliv.write_text(eliv_content, encoding="utf-8")
        except (ValueError, OSError) as e:
            logger.warning(
                "Could not mirror docs to docs/livingDoc/ for %s: %s",
                file_path,
                e,
            )

    return (tldr_path, deep_path, eliv_path)


async def _generate_single_symbol_docs(
    symbol_info: Dict[str, Any],
    dependencies: List[str],
    source_code_snippet: str,
    semaphore: asyncio.Semaphore,
) -> Tuple[str, bool, str, str, str]:
    """
    Generate TL;DR, deep, and ELIV content for a single symbol, respecting the
    per-file semaphore. Uses sync wrappers (each with internal asyncio.run) to
    avoid event loop conflicts when processing multiple files via process_directory.

    Returns:
        Tuple of (symbol_name, is_valid, tldr_content, deep_content, eliv_content).
    """
    async with semaphore:
        tldr_content = await asyncio.to_thread(
            generate_tldr_content, symbol_info, dependencies
        )
        deep_content = await asyncio.to_thread(
            generate_deep_content,
            symbol_info,
            dependencies,
            source_code_snippet,
        )
        eliv_content = await asyncio.to_thread(
            generate_eliv_content,
            symbol_info,
            dependencies,
            source_code_snippet,
        )

        is_valid, errors = validate_generated_docs(
            symbol_info, tldr_content, deep_content
        )
        if not is_valid:
            for err in errors:
                logger.warning(
                    "Validation failed for %s: %s",
                    symbol_info.get("name"),
                    err,
                )

        return (
            symbol_info["name"],
            is_valid,
            tldr_content,
            deep_content,
            eliv_content,
        )


async def process_single_file_async(
    target_path: Path,
    *,
    output_dir: Optional[Path] = None,
    dependencies_func: Optional[Callable[[Path], List[str]]] = None,
    per_file_concurrency: int = 3,
) -> bool:
    """
    Process a single Python file for documentation generation (async).

    Parses the file, generates TL;DR and deep content for each symbol via LLM
    concurrently (limited by per_file_concurrency), validates, aggregates,
    and writes .tldr.md and .deep.md files.

    Args:
        target_path: Path to the Python file to process.
        output_dir: Optional directory to write generated docs. If None,
            writes to local .docs/ and mirrors to docs/livingDoc/.
        dependencies_func: Optional function to resolve dependencies for the
            file. Called with the file path, returns list of dependency paths.
        per_file_concurrency: Max concurrent symbol generations per file (default 3).

    Returns:
        True if parsing and writing succeeded, False otherwise.
    """
    if not target_path.exists() or not target_path.is_file():
        raise FileNotFoundError(f"Target file not found: {target_path}")

    if target_path.suffix != ".py":
        raise ValueError(f"Target is not a Python file: {target_path}")

    parsed_data = parse_python_file(target_path)
    if parsed_data.get("error") is not None:
        logger.warning("Parse error for %s: %s", target_path, parsed_data["error"])
        return False

    dependencies: List[str] = []
    if dependencies_func:
        dependencies = dependencies_func(target_path) or []

    per_file_semaphore = asyncio.Semaphore(per_file_concurrency)

    tasks: List[asyncio.Task[Tuple[str, bool, str, str, str]]] = []
    for symbol in parsed_data.get("symbols", []):
        source_snippet = extract_source_snippet(
            target_path,
            symbol["lineno"],
            symbol["end_lineno"],
        )
        task = asyncio.create_task(
            _generate_single_symbol_docs(
                symbol, dependencies, source_snippet, per_file_semaphore
            )
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    tldr_agg_content = ""
    deep_agg_content = ""
    eliv_agg_content = ""

    for symbol_name, is_valid, tldr_content, deep_content, eliv_content in results:
        if is_valid:
            header = f"# {symbol_name}\n\n"
            if tldr_agg_content:
                tldr_agg_content += "\n---\n\n"
            tldr_agg_content += header + tldr_content
            if deep_agg_content:
                deep_agg_content += "\n---\n\n"
            deep_agg_content += header + deep_content
            if eliv_agg_content:
                eliv_agg_content += "\n---\n\n"
            eliv_agg_content += f"# {symbol_name} ELIV\n\n{eliv_content}"

    if not tldr_agg_content.strip() and not deep_agg_content.strip():
        msg = (
            f"No valid content to write for {target_path}: "
            "all symbols failed validation (empty LLM response or generation error)."
        )
        logger.warning(msg)
        print(f"Warning: {msg}", file=sys.stderr)
        return False

    tldr_path, deep_path, eliv_path = write_documentation_files(
        target_path, tldr_agg_content, deep_agg_content, eliv_agg_content, output_dir
    )
    logger.info("Wrote %s, %s, and %s", tldr_path, deep_path, eliv_path)
    # Print to stdout so user sees where files were written (logger.info may be hidden)
    msg = f"Wrote {tldr_path}, {deep_path}, and {eliv_path}"
    if output_dir is None:
        try:
            rel = target_path.resolve().relative_to(Path.cwd().resolve())
            central = Path.cwd() / "docs" / "livingDoc" / rel.parent
            msg += f" (also mirrored to {central})"
        except ValueError:
            pass
    print(msg, file=sys.stdout)
    return True


def process_single_file(
    target_path: Path,
    *,
    output_dir: Optional[Path] = None,
    dependencies_func: Optional[Callable[[Path], List[str]]] = None,
) -> bool:
    """
    Process a single Python file for documentation generation (sync wrapper).

    Parses the file, generates TL;DR and deep content for each symbol via LLM,
    validates, aggregates, and writes .tldr.md and .deep.md files.

    Uses process_single_file_async internally for concurrent symbol processing.

    Args:
        target_path: Path to the Python file to process.
        output_dir: Optional directory to write generated docs. If None,
            writes to local .docs/ and mirrors to docs/livingDoc/.
        dependencies_func: Optional function to resolve dependencies for the
            file. Called with the file path, returns list of dependency paths.

    Returns:
        True if parsing and writing succeeded, False otherwise.
    """
    return asyncio.run(
        process_single_file_async(
            target_path,
            output_dir=output_dir,
            dependencies_func=dependencies_func,
        )
    )


def _update_module_brief(package_dir: Path, repo_root: Path) -> bool:
    """
    Generate module-level brief (__init__.py.module.md) from package .docs/ content.

    Reads all .tldr.md and .deep.md in package_dir/.docs/, sends to LLM for summary,
    writes to docs/livingDoc/<rel>/__init__.py.module.md and package_dir/.docs/__init__.py.module.md.

    Respects BUILT_IN_IGNORES (via IgnorePatterns) and drafts.enable_module_briefs config.
    Logs as "module_brief" audit event.

    Returns True if generated, False if skipped.
    """
    config = ScoutConfig()
    drafts = config.get("drafts") or {}
    if not drafts.get("enable_module_briefs", True):
        return False

    ignore = IgnorePatterns(repo_root=repo_root)
    init_py = package_dir / "__init__.py"
    if not init_py.exists():
        return False

    try:
        rel = package_dir.relative_to(repo_root)
    except ValueError:
        return False

    if ignore.matches(package_dir, repo_root):
        return False

    docs_dir = package_dir / ".docs"
    if not docs_dir.exists():
        return False

    tldr_parts: List[str] = []
    deep_parts: List[str] = []
    for md in sorted(docs_dir.glob("*.tldr.md")):
        try:
            tldr_parts.append(f"### {md.stem}\n\n{md.read_text(encoding='utf-8', errors='replace')}")
        except OSError:
            pass
    for md in sorted(docs_dir.glob("*.deep.md")):
        try:
            deep_parts.append(f"### {md.stem}\n\n{md.read_text(encoding='utf-8', errors='replace')}")
        except OSError:
            pass

    if not tldr_parts and not deep_parts:
        return False

    combined = "\n\n".join(tldr_parts + deep_parts)
    if len(combined) > 12000:
        combined = combined[:12000] + "\n\n[... truncated ...]"

    module_name = ".".join(rel.parts)
    prompt = f"""You are a documentation assistant. Given the following documentation for a Python package module "{module_name}",
write a concise module-level summary in Markdown that explains:

1. **Purpose** — What this module does and why it exists.
2. **Key components** — Main classes, functions, or types and their roles.
3. **Interaction flow** — How components work together.

Package: {rel}
Documentation excerpts:
{combined}

Output ONLY the module summary in Markdown. Use ## headings for each section."""

    try:
        response = asyncio.run(
            call_groq_async(
                prompt,
                model=TLDR_MODEL,
                system="You are a documentation assistant. Be concise and accurate.",
                max_tokens=800,
            )
        )
    except Exception as e:
        logger.warning("Module brief LLM failed for %s: %s", package_dir, e)
        return False

    audit = AuditLog()
    audit.log(
        "module_brief",
        cost=response.cost_usd,
        model=response.model,
        package=str(rel),
    )

    content = response.content.strip()
    module_md_name = "__init__.py.module.md"
    local_path = docs_dir / module_md_name
    central_dir = repo_root / "docs" / "livingDoc" / rel
    central_dir.mkdir(parents=True, exist_ok=True)
    central_path = central_dir / module_md_name
    try:
        local_path.write_text(content, encoding="utf-8")
        central_path.write_text(content, encoding="utf-8")
        logger.info("Wrote module brief: %s (mirrored to %s)", local_path, central_path)
    except OSError as e:
        logger.warning("Could not write module brief for %s: %s", package_dir, e)
        return False
    return True


def process_directory(
    target_path: Path,
    *,
    recursive: bool = False,
    output_dir: Optional[Path] = None,
    dependencies_func: Optional[Callable[[Path], List[str]]] = None,
) -> None:
    """
    Process a directory of Python files for documentation generation.

    After processing all files in a package (directory with __init__.py),
    auto-generates module brief (__init__.py.module.md) when enable_module_briefs is true.

    Args:
        target_path: Path to the directory to process.
        recursive: If True, process subdirectories recursively.
        output_dir: Optional directory to write generated docs. If None,
            writes to local .docs/ and mirrors to docs/livingDoc/.
        dependencies_func: Optional function to resolve dependencies for each
            file. Called with each file path, returns list of dependency paths.
    """
    if not target_path.exists() or not target_path.is_dir():
        raise NotADirectoryError(f"Target directory not found: {target_path}")

    if output_dir is not None:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    repo_root = Path.cwd().resolve()
    pattern = "**/*.py" if recursive else "*.py"
    processed_package_dirs: set[Path] = set()

    for py_file in target_path.glob(pattern):
        if py_file.is_file() and "__pycache__" not in str(py_file):
            try:
                process_single_file(
                    py_file,
                    output_dir=output_dir,
                    dependencies_func=dependencies_func,
                )
                if output_dir is None and (py_file.parent / "__init__.py").exists():
                    processed_package_dirs.add(py_file.parent)
            except (ValueError, OSError) as e:
                logger.warning("Skip %s: %s", py_file, e)

    if output_dir is None:
        for pkg_dir in sorted(processed_package_dirs):
            try:
                _update_module_brief(pkg_dir, repo_root)
            except Exception as e:
                logger.warning("Skip module brief for %s: %s", pkg_dir, e)

# Smoke test change 1770939297

# Smoke test change 1770939397

# Smoke test change 1770939517

# Smoke test change 1770939701
# Smoke test 1770939786

# Smoke test change 1770939947

# Smoke test change 1770940055

# Smoke test change 1770940083

# Smoke test change 1770940156
