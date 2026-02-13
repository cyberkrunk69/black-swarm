"""
Scout Python adapter — AST-based parsing and prompts for Python files.

Implements LanguageAdapter using Python's ast module for symbol extraction.
Extracts call graph, type annotations, and exports for grounded documentation.
"""

from __future__ import annotations

import ast
import builtins
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from vivarium.scout.adapters.base import LanguageAdapter, SymbolTree

logger = logging.getLogger(__name__)

# Common builtins: no LLM needed for symbols that only call these
_BUILTIN_NAMES = frozenset(
    name for name in dir(builtins)
    if not name.startswith("_")
)


def _build_import_map(tree: ast.Module) -> Dict[str, str]:
    """Build map from local name -> fully qualified module.symbol for imports."""
    import_map: Dict[str, str] = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name
                import_map[name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            base = node.module
            for alias in node.names:
                local = alias.asname or alias.name
                if alias.name == "*":
                    continue
                import_map[local] = f"{base}.{alias.name}"
    return import_map


def _qualify_call_name(
    node: ast.Call,
    import_map: Dict[str, str],
    local_scope: Set[str],
) -> str | None:
    """Resolve a call to a qualified name (module.path.func) when possible."""
    func = node.func
    parts: List[str] = []
    cur: ast.expr = func
    while isinstance(cur, ast.Attribute):
        parts.insert(0, cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.insert(0, cur.id)
    else:
        return None  # e.g. (lambda x: x)(1)
    name = ".".join(parts)
    if len(parts) == 1 and parts[0] in import_map:
        return import_map[parts[0]]
    if len(parts) > 1 and parts[0] in import_map:
        base = import_map[parts[0]]
        return f"{base}.{'.'.join(parts[1:])}"
    return name


def _extract_calls_from_body(
    body: list,
    import_map: Dict[str, str],
    local_scope: Set[str],
) -> List[str]:
    """Extract qualified call names from a function/class body."""
    calls: List[str] = []
    seen: Set[str] = set()

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.Call):
            q = _qualify_call_name(node, import_map, local_scope)
            if q and q not in seen:
                seen.add(q)
                calls.append(q)
        for child in ast.iter_child_nodes(node):
            visit(child)

    for stmt in body:
        visit(stmt)
    return sorted(calls)


def _extract_types_from_node(node: ast.AST) -> List[str]:
    """Extract type names from annotations (args, returns, AnnAssign)."""
    types: List[str] = []

    def _name_from_annotation(ann: ast.expr | None) -> str | None:
        if ann is None:
            return None
        if isinstance(ann, ast.Name):
            return ann.id
        if isinstance(ann, ast.Attribute):
            return f"{_name_from_annotation(ann.value)}.{ann.attr}" if isinstance(ann.value, ast.Name) else ann.attr
        if isinstance(ann, ast.Subscript):
            return _name_from_annotation(ann.slice) if isinstance(ann.slice, ast.Name) else None
        if isinstance(ann, ast.BinOp) and isinstance(ann.left, ast.Name):
            return ann.left.id  # Union[X, Y] -> X
        return None

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for arg in node.args.args:
            t = _name_from_annotation(arg.annotation)
            if t and t not in ("self", "cls"):
                types.append(t)
        t = _name_from_annotation(node.returns)
        if t:
            types.append(t)
    elif isinstance(node, ast.AnnAssign) and node.annotation:
        t = _name_from_annotation(node.annotation)
        if t:
            types.append(t)
    elif isinstance(node, ast.ClassDef):
        for base in node.bases:
            t = _name_from_annotation(base)
            if t:
                types.append(t)

    return types


def _extract_module_exports(tree: ast.Module) -> List[str]:
    """Extract exports from __all__ or top-level def/class names."""
    exports: List[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Str):
                                exports.append(elt.s)
                            elif isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                exports.append(elt.value)
                    return exports
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                exports.append(node.name)
    return exports


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


def _is_simple_symbol(symbol: SymbolTree) -> bool:
    """
    Return True if symbol can get auto-generated TL;DR (no LLM).

    Simple = function/method, ≤3 body lines, no control flow, only builtin calls.
    """
    if symbol.type not in ("function", "method", "async_function"):
        return False
    hints = getattr(symbol, "logic_hints", None) or []
    if any(h in hints for h in ("loop", "conditional", "exception_handling")):
        return False
    body_lines = (symbol.end_lineno or symbol.lineno) - symbol.lineno
    if body_lines > 3:
        return False
    calls = getattr(symbol, "calls", None) or []
    for c in calls:
        if "." in c:
            return False
        if c not in _BUILTIN_NAMES:
            return False
    return True


def _extract_return_expr(source_snippet: str) -> Optional[str]:
    """Parse source and return the expression from a single return stmt, or None."""
    try:
        tree = ast.parse(source_snippet)
        for node in ast.walk(tree):
            if isinstance(node, ast.Return) and node.value is not None:
                return ast.unparse(node.value)
    except (SyntaxError, ValueError):
        pass
    return None


def try_auto_tldr(symbol: SymbolTree, source_snippet: str) -> Optional[str]:
    """
    If symbol is simple, return a template TL;DR without LLM. Otherwise None.

    Template: "Returns {expr}." or "Simple {name} utility."
    """
    if not _is_simple_symbol(symbol):
        return None
    expr = _extract_return_expr(source_snippet)
    if expr:
        return f"Returns {expr}."
    return f"Simple {symbol.name} utility."


class PythonAdapter(LanguageAdapter):
    """Adapter for Python files using AST parsing."""

    @property
    def extensions(self) -> List[str]:
        return [".py"]

    def parse(self, file_path: Path) -> SymbolTree:
        file_path = Path(file_path).resolve()
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"Target file not found: {file_path}")
        if file_path.suffix != ".py":
            raise ValueError(f"Target is not a Python file: {file_path}")

        try:
            content = file_path.read_text(encoding="utf-8", errors="strict")
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(
                e.encoding, e.object, e.start, e.end, f"Could not read {file_path}: {e}"
            ) from e
        except OSError as e:
            raise IOError(f"Could not read {file_path}: {e}") from e

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            raise SyntaxError(
                e.msg, (e.filename, e.lineno, e.offset, e.text)
            ) from e

        import_map = _build_import_map(tree)
        module_exports = _extract_module_exports(tree)
        children: List[SymbolTree] = []

        def process_callable(
            node: ast.FunctionDef | ast.AsyncFunctionDef,
            symbol_type: str,
        ) -> SymbolTree:
            end_lineno = getattr(node, "end_lineno", None) or node.lineno
            local_scope = {a.arg for a in node.args.args}
            calls = _extract_calls_from_body(node.body, import_map, local_scope)
            uses_types = _extract_types_from_node(node)
            return SymbolTree(
                name=node.name,
                type=symbol_type,
                lineno=node.lineno,
                end_lineno=end_lineno,
                docstring=ast.get_docstring(node),
                signature=_build_signature(node),
                logic_hints=_extract_logic_hints(node),
                calls=calls,
                uses_types=uses_types,
            )

        def process_class(cls: ast.ClassDef) -> SymbolTree:
            end_lineno = getattr(cls, "end_lineno", None) or cls.lineno
            method_children: List[SymbolTree] = []
            for item in cls.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_children.append(
                        process_callable(item, "method")
                    )
            local_scope = {cls.name}
            class_calls = _extract_calls_from_body(cls.body, import_map, local_scope)
            class_types = _extract_types_from_node(cls)
            return SymbolTree(
                name=cls.name,
                type="class",
                children=method_children,
                lineno=cls.lineno,
                end_lineno=end_lineno,
                docstring=ast.get_docstring(cls),
                calls=class_calls,
                uses_types=class_types,
            )

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                children.append(process_callable(node, "function"))
            elif isinstance(node, ast.AsyncFunctionDef):
                children.append(process_callable(node, "async_function"))
            elif isinstance(node, ast.ClassDef):
                children.append(process_class(node))
            elif isinstance(node, ast.Assign):
                for name in _parse_assign_targets(node):
                    end_lineno = getattr(node, "end_lineno", None) or node.lineno
                    children.append(
                        SymbolTree(
                            name=name,
                            type="constant",
                            lineno=node.lineno,
                            end_lineno=end_lineno,
                        )
                    )

        module_name = file_path.stem
        return SymbolTree(
            name=module_name,
            type="module",
            children=children,
            exports=module_exports,
            lineno=1,
            end_lineno=len(content.splitlines()) if content else 1,
        )

    def try_auto_tldr(self, symbol: SymbolTree, source_snippet: str) -> Optional[str]:
        """If symbol is simple, return template TL;DR without LLM. Otherwise None."""
        return try_auto_tldr(symbol, source_snippet)

    def get_tldr_prompt(self, symbol: SymbolTree, dependencies: List[str]) -> str:
        calls = getattr(symbol, "calls", None) or []
        uses_types = getattr(symbol, "uses_types", None) or []
        exports = getattr(symbol, "exports", None) or []
        calls_str = "\n".join(f"  {c}" for c in calls) if calls else "  (none traced)"
        types_str = ", ".join(uses_types) if uses_types else "none"
        exports_str = ", ".join(exports) if exports else "(none)"

        return f"""You are a senior engineer. Summarize this Python {symbol.type} using ONLY the facts below. Do not guess or presume.

File symbol: {symbol.name}
Exports: {exports_str}
Calls (qualified):
{calls_str}
Uses types: {types_str}
Imports/deps: {', '.join(dependencies) if dependencies else 'none'}

Write a concise TL;DR (1-3 sentences) that explains its role in the system. Base it strictly on the traced calls and types above.
Output ONLY the summary, no preamble."""

    def get_deep_prompt(
        self,
        symbol: SymbolTree,
        dependencies: List[str],
        source_snippet: str,
    ) -> str:
        calls = getattr(symbol, "calls", None) or []
        uses_types = getattr(symbol, "uses_types", None) or []
        calls_str = "\n".join(f"- {c}" for c in calls) if calls else "- (none traced)"
        types_str = ", ".join(uses_types) if uses_types else "none"

        return f"""Analyze this Python {symbol.type} '{symbol.name}' using ONLY traced facts. Do not guess.

Traced facts:
Calls:
{calls_str}
Uses types: {types_str}
Imports: {', '.join(dependencies) if dependencies else 'none'}

Source Code:
```
{source_snippet}
```

Provide a detailed breakdown using Markdown headings (##):

1. ## Logic Overview — Flow and main steps from the code.
2. ## Dependency Interactions — How it uses the traced calls (reference qualified names).
3. ## Potential Considerations — Edge cases, error handling, performance from the code.
4. ## Signature — `{symbol.signature or 'N/A'}`

Base analysis strictly on the code and traced calls. No speculation."""

    def get_eliv_prompt(
        self,
        symbol: SymbolTree,
        dependencies: List[str],
        source_snippet: str,
    ) -> str:
        calls = getattr(symbol, "calls", None) or []
        calls_str = ", ".join(calls[:5]) if calls else "nothing specific"
        return f"""Explain the Python {symbol.type} '{symbol.name}' like I'm very young (around 5 years old).

Grounded facts (use these, do not guess):
- It calls: {calls_str}
- It uses imports: {', '.join(dependencies[:5]) if dependencies else 'none'}

Code:
```
{source_snippet}
```

Use very simple words. Explain what it *does* based on the traced calls. No jargon. Short and sweet.
Output ONLY the explanation, no preamble."""


def symbol_to_dict(symbol: SymbolTree) -> Dict[str, Any]:
    """Convert SymbolTree to legacy dict format for compatibility."""
    return {
        "name": symbol.name,
        "type": symbol.type,
        "lineno": symbol.lineno,
        "end_lineno": symbol.end_lineno,
        "docstring": symbol.docstring,
        "signature": symbol.signature,
        "logic_hints": symbol.logic_hints,
    }
