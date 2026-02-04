# experiments/exp_20260203_195349_unified_session_23/spawner_hooks.py

import requests
import json

def enrich_prompt(task_text: str, base_prompt: str) -> str:
    """Fetch relevant knowledge packs and prepend them to the prompt."""
    resp = requests.post(
        "http://localhost:8000/knowledge-packs/query",
        json={"task_text": task_text, "max_results": 3}
    )
    packs = resp.json()["results"]
    intro = "\n".join(
        f"# Lesson {p['id']}\n{p['snippet']}\n---" for p in packs
    )
    return f"{intro}\n\n{base_prompt}"