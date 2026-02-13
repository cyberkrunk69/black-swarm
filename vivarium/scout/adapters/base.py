"""
Scout language adapter base — interface and SymbolTree for doc generation.

Defines the common contract for language-specific parsers (Python, JavaScript,
plain-text fallback) used by doc_generation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional


@dataclass
class SymbolTree:
    """
    Structured representation of a code symbol (function, class, module, etc.).

    Attributes:
        name: Symbol name (e.g., function name, class name).
        type: One of "function", "class", "module", "method", "constant", etc.
        children: Nested symbols (e.g., methods inside a class).
        dependencies: List of dependency names/paths (imports, requires).
        calls: Qualified names of functions/callables invoked (e.g. vivarium.scout.audit.log).
        uses_types: Types from annotations or assignments (e.g. CostTracker, SymbolTree).
        exports: What this symbol exposes (for modules: __all__ or top-level defs).
        lineno: Starting line number (1-indexed).
        end_lineno: Ending line number (1-indexed).
        docstring: Docstring or comment block if available.
        signature: Call signature for functions/methods (e.g., "def foo(x: int)").
        logic_hints: Tags like "loop", "conditional", "async" for code analysis.
    """

    name: str
    type: str  # "function" | "class" | "module" | "method" | "constant" | ...
    children: List[SymbolTree] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)
    uses_types: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    lineno: int = 1
    end_lineno: int = 1
    docstring: Optional[str] = None
    signature: Optional[str] = None
    logic_hints: List[str] = field(default_factory=list)

    def iter_symbols(self) -> Iterator[SymbolTree]:
        """Yield this symbol and all descendants (flattened for doc generation)."""
        yield self
        for child in self.children:
            yield from child.iter_symbols()


class LanguageAdapter(ABC):
    """
    Base class for language-specific documentation adapters.

    Implementations parse files into SymbolTree and provide LLM prompts for
    TL;DR, deep, and ELIV content generation.
    """

    @property
    @abstractmethod
    def extensions(self) -> List[str]:
        """File extensions this adapter handles (e.g., ['.py'], ['.js'])."""
        ...

    @abstractmethod
    def parse(self, file_path: Path) -> SymbolTree:
        """
        Parse file into structured symbols (functions, classes, deps).

        Args:
            file_path: Path to the source file.

        Returns:
            Root SymbolTree (typically type="module") with children.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file type is not supported.
            SyntaxError: If parsing fails.
        """
        ...

    @abstractmethod
    def get_tldr_prompt(self, symbol: SymbolTree, dependencies: List[str]) -> str:
        """Return LLM prompt for .tldr.md generation."""
        ...

    @abstractmethod
    def get_deep_prompt(
        self,
        symbol: SymbolTree,
        dependencies: List[str],
        source_snippet: str,
    ) -> str:
        """Return LLM prompt for .deep.md generation."""
        ...

    @abstractmethod
    def get_eliv_prompt(
        self,
        symbol: SymbolTree,
        dependencies: List[str],
        source_snippet: str,
    ) -> str:
        """Return LLM prompt for .eliv.md (Explain Like I'm Very Young) generation."""
        ...
