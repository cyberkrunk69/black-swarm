"""
Scout adapter registry — routes file extensions to appropriate LanguageAdapter.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from vivarium.scout.adapters.base import LanguageAdapter
from vivarium.scout.adapters.plain_text import PlainTextAdapter
from vivarium.scout.adapters.python import PythonAdapter

try:
    from vivarium.scout.adapters.javascript import JavaScriptAdapter

    HAS_JAVASCRIPT = True
except ImportError:
    HAS_JAVASCRIPT = False

# Extension -> human-readable language name for plain-text fallback
_PLAIN_LANG_MAP: Dict[str, str] = {
    ".go": "Go",
    ".rs": "Rust",
    ".ts": "TypeScript",
    ".tsx": "TypeScript/React",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++",
    ".hpp": "C++",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".r": "R",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Bash",
    ".zsh": "Zsh",
}

_ADAPTERS: Dict[str, LanguageAdapter] = {
    ".py": PythonAdapter(),
}

if HAS_JAVASCRIPT:
    _ADAPTERS.update({
        ".js": JavaScriptAdapter(),
        ".mjs": JavaScriptAdapter(),
        ".cjs": JavaScriptAdapter(),
    })


def _ensure_registry() -> None:
    """No-op; registry is built at module load. Kept for API compatibility."""
    pass


def get_adapter_for_path(
    file_path: Path,
    language_override: Optional[str] = None,
) -> LanguageAdapter:
    """
    Return the appropriate adapter for the given file path.

    Args:
        file_path: Path to the source file.
        language_override: Optional explicit language (e.g., "python", "javascript").
            If set, bypasses extension-based detection.

    Returns:
        LanguageAdapter instance. Falls back to PlainTextAdapter for unknown extensions.
    """
    _ensure_registry()
    ext = Path(file_path).suffix.lower()

    if language_override:
        lang = language_override.lower()
        if lang in ("py", "python"):
            return _ADAPTERS.get(".py") or PythonAdapter()
        if lang in ("js", "javascript"):
            return _ADAPTERS.get(".js") or PlainTextAdapter(ext, "JavaScript")
        return PlainTextAdapter(ext, _PLAIN_LANG_MAP.get(ext, lang))

    if ext in _ADAPTERS:
        return _ADAPTERS[ext]

    lang_hint = _PLAIN_LANG_MAP.get(ext, ext.lstrip(".") or "unknown")
    return PlainTextAdapter(ext, lang_hint)


def get_supported_extensions() -> list[str]:
    """Return list of file extensions with dedicated adapters."""
    _ensure_registry()
    return sorted(_ADAPTERS.keys())
