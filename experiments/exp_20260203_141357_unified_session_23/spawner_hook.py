# experiments/exp_20260203_141357_unified_session_23/spawner_hook.py
from knowledge_packs import KnowledgePackStore
from embedder import openai_embed

def pre_task_hook(task_text: str) -> str:
    """
    Called by the spawner before the main execution.
    Returns additional prompt context to prepend.
    """
    store = KnowledgePackStore('data/learned_lessons.json', embedder=openai_embed)
    # Lazy load embeddings; they are cached after first build
    return store.assemble_context(task_text)