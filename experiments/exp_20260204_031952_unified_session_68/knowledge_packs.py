import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Optional: try to import a real embedding model; fall back to a simple hash‑based vector.
try:
    from sentence_transformers import SentenceTransformer
    _EMBEDDER = SentenceTransformer('all-MiniLM-L6-v2')
except Exception:  # pragma: no cover
    _EMBEDDER = None

log = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def _embed(text: str) -> List[float]:
    """
    Return a numeric embedding for *text*.
    If a SentenceTransformer model is available we use it, otherwise we
    generate a deterministic pseudo‑embedding using a simple hash.
    """
    if _EMBEDDER is not None:
        return _EMBEDDER.encode(text).tolist()
    # deterministic fallback: split into words, map each word to its ord sum
    # and pad/truncate to length 10.
    words = text.split()
    vec = [sum(ord(c) for c in w) for w in words[:10]]
    vec += [0] * (10 - len(vec))
    return vec


def _cosine_sim(a: List[float], b: List[float]) -> float:
    """Very small cosine similarity implementation (no external deps)."""
    import math
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# --------------------------------------------------------------------------- #
# Core data structures
# --------------------------------------------------------------------------- #
class KnowledgePack:
    """
    Represents a collection of lessons belonging to a single category.
    """
    def __init__(self, category: str, lessons: List[Dict[str, Any]] = None):
        self.category = category
        self.lessons = lessons if lessons is not None else []  # each lesson is a dict
        # Pre‑compute embeddings for fast lookup
        self._embeddings = [ _embed(l['text']) for l in self.lessons ]

    def add_lesson(self, lesson: Dict[str, Any]) -> None:
        """Add a lesson (expects a dict with at least a ``text`` key)."""
        self.lessons.append(lesson)
        self._embeddings.append(_embed(lesson['text']))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "lessons": self.lessons
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgePack':
        return cls(category=data.get('category', ''), lessons=data.get('lessons', []))

    def search(self, query: str, top_k: int = 3, min_score: float = 0.3) -> List[Tuple[Dict[str, Any], float]]:
        """Return the *top_k* lessons most relevant to *query*."""
        q_vec = _embed(query)
        scores = [_cosine_sim(q_vec, e) for e in self._embeddings]
        scored = sorted(
            [(lesson, score) for lesson, score in zip(self.lessons, scores)],
            key=lambda x: x[1],
            reverse=True
        )
        return [(lesson, score) for lesson, score in scored if score >= min_score][:top_k]


# --------------------------------------------------------------------------- #
# Pack manager
# --------------------------------------------------------------------------- #
class PackManager:
    """
    Handles loading, saving and searching across all knowledge packs.
    """
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent / "knowledge_packs"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.packs: Dict[str, KnowledgePack] = {}  # key = category

    # ------------------------------------------------------------------- #
    # Persistence
    # ------------------------------------------------------------------- #
    def load_all(self) -> None:
        """Load every ``*.json`` file inside ``knowledge_packs``."""
        for file in self.base_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                pack = KnowledgePack.from_dict(data)
                self.packs[pack.category] = pack
                log.debug("Loaded pack %s (%d lessons)", pack.category, len(pack.lessons))
            except Exception as exc:  # pragma: no cover
                log.error("Failed to load %s: %s", file, exc)

    def save_all(self) -> None:
        """Write each pack back to its category‑named JSON file."""
        for pack in self.packs.values():
            out_path = self.base_dir / f"{pack.category}.json"
            try:
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(pack.to_dict(), f, ensure_ascii=False, indent=2)
                log.debug("Saved pack %s (%d lessons)", pack.category, len(pack.lessons))
            except Exception as exc:  # pragma: no cover
                log.error("Failed to save %s: %s", out_path, exc)

    # ------------------------------------------------------------------- #
    # Search helpers
    # ------------------------------------------------------------------- #
    def get_pack(self, category: str) -> KnowledgePack:
        return self.packs.get(category)

    def ensure_pack(self, category: str) -> KnowledgePack:
        if category not in self.packs:
            self.packs[category] = KnowledgePack(category)
        return self.packs[category]

    def search_across_packs(self, query: str, top_k_per_pack: int = 2) -> List[Tuple[KnowledgePack, List[Tuple[Dict[str, Any], float]]]]:
        """Return relevant lessons per pack."""
        results = []
        for pack in self.packs.values():
            hits = pack.search(query, top_k=top_k_per_pack)
            if hits:
                results.append((pack, hits))
        return results


# --------------------------------------------------------------------------- #
# Simple categorisation logic
# --------------------------------------------------------------------------- #
_CATEGORY_KEYWORDS = {
    "claude": ["anthropic", "claude", "prompt", "conversation"],
    "groq": ["groq", "llama", "mixtral", "inference"],
    "safety": ["safety", "guardrails", "policy", "restriction"],
    "general": ["python", "code", "algorithm", "debug", "bug"],
    # Extend as needed
}


def auto_categorize_lesson(lesson_text: str) -> str:
    """
    Very lightweight rule‑based categoriser.
    Returns the first matching category or ``general`` as fallback.
    """
    lowered = lesson_text.lower()
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return cat
    return "general"


# --------------------------------------------------------------------------- #
# Public API for spawner integration
# --------------------------------------------------------------------------- #
_manager = PackManager()
_manager.load_all()


def get_relevant_packs(task_text: str, top_k_per_pack: int = 2) -> List[KnowledgePack]:
    """
    Given a *task_text*, return a list of KnowledgePack objects that contain
    lessons deemed relevant. The function also logs which packs were used.
    """
    hits = _manager.search_across_packs(task_text, top_k_per_pack=top_k_per_pack)
    used_packs = [pack.category for pack, _ in hits]
    log.info("Relevant knowledge packs for task: %s", ", ".join(used_packs) or "none")
    return [pack for pack, _ in hits]


def migrate_lessons(source_path: Path = None) -> None:
    """
    Read ``learned_lessons.json`` (or a custom *source_path*), auto‑categorise
    each lesson and persist them into the category‑specific JSON files under
    ``knowledge_packs/``.
    """
    source_path = source_path or Path(__file__).parent.parent / "learned_lessons.json"
    if not source_path.is_file():
        log.warning("No learned lessons file found at %s – migration skipped.", source_path)
        return

    try:
        with open(source_path, "r", encoding="utf-8") as f:
            lessons = json.load(f)  # expects a list of dicts with at least ``text``
    except Exception as exc:  # pragma: no cover
        log.error("Failed to read lessons from %s: %s", source_path, exc)
        return

    for lesson in lessons:
        text = lesson.get("text", "")
        if not text:
            continue
        category = auto_categorize_lesson(text)
        pack = _manager.ensure_pack(category)
        pack.add_lesson(lesson)

    _manager.save_all()
    log.info("Migrated %d lessons into knowledge packs.", len(lessons))


# --------------------------------------------------------------------------- #
# Auto‑run migration on first import (safe‑guarded)
# --------------------------------------------------------------------------- #
if not _manager.packs:  # pragma: no cover
    # If no packs are present we attempt a migration; failures are logged only.
    try:
        migrate_lessons()
    except Exception as e:  # pragma: no cover
        log.error("Automatic migration failed: %s", e)