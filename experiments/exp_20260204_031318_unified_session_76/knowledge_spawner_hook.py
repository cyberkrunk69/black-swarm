# experiments/exp_20260204_031318_unified_session_76/knowledge_spawner_hook.py
from knowledge_pack import KnowledgePack

# Singleton for the current experiment
_knowledge_pack = KnowledgePack(
    lessons_path="experiments/exp_20260204_031318_unified_session_76/learned_lessons.json"
)

def pre_task_hook(task_text: str) -> str:
    """
    Called by the spawner before executing a task.
    - Retrieves relevant lessons.
    - Prepends them to the task prompt under a clear header.
    """
    relevant = _knowledge_pack.query(task_text, top_k=4)
    if not relevant:
        return task_text

    intro = "### Relevant Knowledge Pack\n"
    body = "\n".join(
        f"- **[{l['id']}]** ({', '.join(l['categories'])}): {l['text'][:200]}..."
        for l in relevant
    )
    return f"{intro}{body}\n\n---\n\n{task_text}"