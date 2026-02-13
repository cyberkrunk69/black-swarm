"""
Scout language adapters — pluggable parsers for multi-language doc generation.

Adapters implement LanguageAdapter to parse files into SymbolTree and provide
LLM prompts for .tldr.md, .deep.md, and .eliv.md generation.
"""

from vivarium.scout.adapters.base import LanguageAdapter, SymbolTree

__all__ = ["LanguageAdapter", "SymbolTree"]
