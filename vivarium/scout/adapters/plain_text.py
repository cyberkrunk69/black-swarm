"""
Scout plain-text adapter — fallback for unsupported languages.

Treats entire file as single "module" symbol. Uses generic prompts.
Logs warning about limited accuracy. Works for .go, .rs, .ts, etc.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from vivarium.scout.adapters.base import LanguageAdapter, SymbolTree

logger = logging.getLogger(__name__)


class PlainTextAdapter(LanguageAdapter):
    """Fallback adapter for any file type. Treats file as single module symbol."""

    def __init__(self, extension: str, language_hint: str = "unknown") -> None:
        """
        Args:
            extension: File extension (e.g., ".go", ".rs").
            language_hint: Human-readable language name for prompts.
        """
        self._ext = extension if extension.startswith(".") else f".{extension}"
        self._lang = language_hint

    @property
    def extensions(self) -> List[str]:
        return [self._ext]

    def parse(self, file_path: Path) -> SymbolTree:
        file_path = Path(file_path).resolve()
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"Target file not found: {file_path}")

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            raise IOError(f"Could not read {file_path}: {e}") from e

        lines = content.splitlines()
        num_lines = len(lines) if lines else 1

        logger.warning(
            "Using plain-text adapter for %s — limited accuracy (no AST parsing)",
            file_path.name,
        )

        return SymbolTree(
            name=file_path.stem,
            type="module",
            lineno=1,
            end_lineno=num_lines,
            docstring=None,
        )

    def get_tldr_prompt(self, symbol: SymbolTree, dependencies: List[str]) -> str:
        deps_str = ", ".join(dependencies) if dependencies else "nothing specific"
        return f"""Summarize this {self._lang} file '{symbol.name}'.

Interactions: Depends on {deps_str}.

Requirements:
- Keep it to 1-3 sentences max.
- Explain the primary purpose of the file.
- Format as plain text or basic Markdown.

Output ONLY the summary, no preamble."""

    def get_deep_prompt(
        self,
        symbol: SymbolTree,
        dependencies: List[str],
        source_snippet: str,
    ) -> str:
        deps_str = ", ".join(dependencies) if dependencies else "None"
        return f"""Analyze the following {self._lang} file '{symbol.name}'.

Source Code:
```
{source_snippet}
```

Dependencies: {deps_str}

Provide a detailed breakdown using Markdown headings (##) for each section:

1. ## Logic Overview — Explain the code's flow and main steps.
2. ## Dependency Interactions — How does it use the listed dependencies?
3. ## Potential Considerations — Edge cases, error handling, performance notes.

Format using Markdown headings ## for each section. Be structured and detailed."""

    def get_eliv_prompt(
        self,
        symbol: SymbolTree,
        dependencies: List[str],
        source_snippet: str,
    ) -> str:
        deps_str = ", ".join(dependencies) if dependencies else "nothing special"
        return f"""Explain this {self._lang} file '{symbol.name}' like I'm very young (around 5 years old).

It interacts with: {deps_str}.

Here is the code (don't repeat it, just understand it):
```
{source_snippet}
```

Use very simple words. Avoid technical jargon. Use analogies if helpful.
Focus on what it *does*, not how it does it.
Keep it short and sweet. Output ONLY the explanation, no preamble."""
