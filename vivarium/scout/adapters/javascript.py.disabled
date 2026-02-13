"""
Scout JavaScript adapter — tree-sitter based parsing for .js files.

Parses ESM/CommonJS JavaScript into SymbolTree. Handles functions, classes,
and imports as dependencies. Requires: pip install tree-sitter-languages
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional

from vivarium.scout.adapters.base import LanguageAdapter, SymbolTree

logger = logging.getLogger(__name__)

# ESM/CommonJS import patterns for dependency extraction
_IMPORT_RE = re.compile(
    r"(?:import\s+(?:\{[^}]*\}|\* as \w+|\w+)\s+from\s+['\"]([^'\"]+)['\"]"
    r"|import\s+['\"]([^'\"]+)['\"]"
    r"|require\s*\(\s*['\"]([^'\"]+)['\"]\s*\))"
)
_IMPORT_SOURCE_RE = re.compile(
    r"(?:from|import)\s+['\"]([^'\"]+)['\"]|require\s*\(\s*['\"]([^'\"]+)['\"]"
)


def _extract_imports(content: str) -> List[str]:
    """Extract import/require paths from JavaScript source."""
    deps: List[str] = []
    seen: set = set()
    for m in _IMPORT_SOURCE_RE.finditer(content):
        path = m.group(1) or m.group(2)
        if path and not path.startswith(".") and path not in seen:
            seen.add(path)
            deps.append(path)
    return deps[:20]


class JavaScriptAdapter(LanguageAdapter):
    """Adapter for JavaScript files using tree-sitter."""

    def __init__(self) -> None:
        self._parser = None
        self._language = None

    def _ensure_parser(self) -> None:
        if self._parser is not None:
            return
        try:
            from tree_sitter_languages import get_language, get_parser

            self._language = get_language("javascript")
            self._parser = get_parser("javascript")
        except ImportError as e:
            raise ImportError(
                "tree-sitter-languages required for JavaScript. Install with: pip install tree-sitter-languages"
            ) from e

    @property
    def extensions(self) -> List[str]:
        return [".js", ".mjs", ".cjs"]

    def parse(self, file_path: Path) -> SymbolTree:
        file_path = Path(file_path).resolve()
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"Target file not found: {file_path}")
        if file_path.suffix not in (".js", ".mjs", ".cjs"):
            raise ValueError(f"Target is not a JavaScript file: {file_path}")

        self._ensure_parser()

        try:
            content = file_path.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError) as e:
            raise IOError(f"Could not read {file_path}: {e}") from e

        module_deps = _extract_imports(content)
        tree = self._parser.parse(content.encode())
        lines = content.splitlines()

        children: List[SymbolTree] = []
        _walk_js_tree(tree.root_node, content, lines, children, module_deps)

        module_name = file_path.stem
        return SymbolTree(
            name=module_name,
            type="module",
            children=children,
            dependencies=module_deps,
            lineno=1,
            end_lineno=len(lines) if lines else 1,
        )

    def get_tldr_prompt(self, symbol: SymbolTree, dependencies: List[str]) -> str:
        purpose_parts: List[str] = []
        if symbol.docstring:
            purpose_parts.append(f"JSDoc/Comment: {symbol.docstring}")
        if symbol.signature:
            purpose_parts.append(f"Signature: {symbol.signature}")
        purpose = "\n".join(f"- {p}" for p in purpose_parts) if purpose_parts else "- (infer from context)"
        deps_str = ", ".join(dependencies) if dependencies else "nothing specific"
        return f"""Provide a concise summary of the JavaScript {symbol.type} '{symbol.name}'.

Purpose: Based on the following information:
{purpose}

Interactions: Depends on {deps_str}.

Requirements:
- Keep it to 1-3 sentences max.
- Explain the primary purpose and key responsibilities.
- Briefly describe its relationship with the dependencies above (if any).
- Format as plain text or basic Markdown.

Output ONLY the summary, no preamble."""

    def get_deep_prompt(
        self,
        symbol: SymbolTree,
        dependencies: List[str],
        source_snippet: str,
    ) -> str:
        docstring = symbol.docstring or "(no docstring)"
        deps_str = ", ".join(dependencies) if dependencies else "None"
        return f"""Analyze the following JavaScript {symbol.type} '{symbol.name}'.

Context:
- Docstring/JSDoc: {docstring}
- Signature: {symbol.signature or 'N/A'}

Source Code:
```
{source_snippet}
```

Dependencies: {deps_str}

Provide a detailed breakdown using Markdown headings (##) for each section:

1. ## Logic Overview — Explain the code's flow and main steps.
2. ## Dependency Interactions — How does it use the listed dependencies?
3. ## Potential Considerations — Edge cases, error handling, performance notes from the code.
4. ## Signature — If applicable, include: `{symbol.signature or 'N/A'}`

Format using Markdown headings ## for each section. Be structured, detailed, and code-relevant."""

    def get_eliv_prompt(
        self,
        symbol: SymbolTree,
        dependencies: List[str],
        source_snippet: str,
    ) -> str:
        purpose_parts: List[str] = []
        if symbol.docstring:
            purpose_parts.append(f"JSDoc: {symbol.docstring}")
        if symbol.signature:
            purpose_parts.append(f"Signature: {symbol.signature}")
        purpose_desc = ", ".join(purpose_parts) if purpose_parts else "(infer from the code below)"
        deps_str = ", ".join(dependencies) if dependencies else "nothing special"
        return f"""Explain the JavaScript {symbol.type} '{symbol.name}' like I'm very young (around 5 years old).

Its job is to: {purpose_desc}.

It interacts with: {deps_str}.

Here is the code (don't repeat it, just understand it):
```
{source_snippet}
```

Use very simple words. Avoid technical jargon. Use analogies if helpful.
Focus on what it *does*, not how it does it (unless the "how" is very simple).
Keep it short and sweet. Output ONLY the explanation, no preamble."""


def _get_node_text(node: object, source: str) -> str:
    """Extract source text for a tree-sitter node."""
    return source[node.start_byte : node.end_byte]


def _get_jscdoc(node: object, source: str) -> Optional[str]:
    """Extract JSDoc comment preceding a node if present."""
    # Tree-sitter JS: look for comment nodes before this node
    # Simplified: scan backward in source for /** ... */
    start = node.start_byte
    if start <= 0:
        return None
    chunk = source[max(0, start - 500) : start]
    match = re.search(r"/\*\*([\s\S]*?)\*/", chunk)
    if match:
        return match.group(1).strip()
    return None


def _walk_js_tree(
    node: object,
    source: str,
    lines: List[str],
    out: List[SymbolTree],
    module_deps: List[str],
) -> None:
    """Recursively walk tree-sitter AST and collect symbols."""
    kind = getattr(node, "type", "")
    children_list = getattr(node, "children", []) or []

    if kind == "function_declaration":
        name_node = next(
            (c for c in children_list if getattr(c, "type", "") == "identifier"),
            None,
        )
        name = _get_node_text(name_node, source) if name_node else "anonymous"
        doc = _get_jscdoc(node, source)
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        node_src = source[node.start_byte : node.end_byte]
        sig = node_src.split("{")[0].strip() if "{" in node_src else None
        out.append(
            SymbolTree(
                name=name,
                type="function",
                lineno=start_line,
                end_lineno=end_line,
                docstring=doc,
                signature=sig,
                dependencies=module_deps[:5],
            )
        )
        return

    if kind == "class_declaration":
        # First child is often "class" keyword, then identifier
        name_node = next(
            (c for c in children_list if getattr(c, "type", "") == "identifier"),
            None,
        )
        name = _get_node_text(name_node, source) if name_node else "AnonymousClass"
        doc = _get_jscdoc(node, source)
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        method_children: List[SymbolTree] = []
        for c in children_list:
            if getattr(c, "type", "") == "class_body":
                for m in getattr(c, "children", []) or []:
                    if getattr(m, "type", "") == "method_definition":
                        mname_node = next(
                            (
                                x
                                for x in (getattr(m, "children", []) or [])
                                if getattr(x, "type", "") == "property_identifier"
                            ),
                            None,
                        )
                        mname = (
                            _get_node_text(mname_node, source)
                            if mname_node
                            else "constructor"
                        )
                        mdoc = _get_jscdoc(m, source)
                        ms = m.start_point[0] + 1
                        me = m.end_point[0] + 1
                        msrc = source[m.start_byte : m.end_byte]
                        msig = msrc.split("{")[0].strip() if "{" in msrc else None
                        method_children.append(
                            SymbolTree(
                                name=mname,
                                type="method",
                                lineno=ms,
                                end_lineno=me,
                                docstring=mdoc,
                                signature=msig,
                            )
                        )
                break
        out.append(
            SymbolTree(
                name=name,
                type="class",
                children=method_children,
                lineno=start_line,
                end_lineno=end_line,
                docstring=doc,
                dependencies=module_deps[:5],
            )
        )
        return

    if kind == "variable_declarator":
        # const foo = () => {} or const foo = function() {}
        name_node = next(
            (c for c in children_list if getattr(c, "type", "") == "identifier"),
            None,
        )
        init_node = next(
            (
                c
                for c in children_list
                if getattr(c, "type", "") in ("arrow_function", "function")
            ),
            None,
        )
        if init_node and name_node:
            name = _get_node_text(name_node, source)
            doc = _get_jscdoc(init_node, source)
            start_line = init_node.start_point[0] + 1
            end_line = init_node.end_point[0] + 1
            node_src = source[init_node.start_byte : init_node.end_byte]
            sig = node_src.split("{")[0].strip() if "{" in node_src else None
            out.append(
                SymbolTree(
                    name=name,
                    type="function",
                    lineno=start_line,
                    end_lineno=end_line,
                    docstring=doc,
                    signature=sig,
                    dependencies=module_deps[:5],
                )
            )
        return

    # Recurse into children
    for c in children_list:
        ckind = getattr(c, "type", "")
        if ckind in (
            "function_declaration",
            "class_declaration",
            "variable_declarator",
        ):
            _walk_js_tree(c, source, lines, out, module_deps)
        elif ckind in ("lexical_declaration", "variable_declaration"):
            for d in getattr(c, "children", []) or []:
                if getattr(d, "type", "") == "variable_declarator":
                    _walk_js_tree(d, source, lines, out, module_deps)
