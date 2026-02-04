import datetime
from pathlib import Path

# Expected external API
# from persona_memory import recent_emotions, recent_interactions
# For safety during import, we import lazily inside the function.

def generate_self_reflection():
    """
    Build an introspective prompt using the persona's recent emotions and
    recent interactions, then log the prompt to the self‑experience store.
    Returns the formatted prompt string.
    """
    # Lazy import to avoid import errors if persona_memory is unavailable at load time
    from persona_memory import recent_emotions, recent_interactions

    emotions = recent_emotions()          # Expected: list of strings or objects convertible to str
    interactions = recent_interactions()  # Expected: list of dicts with keys like 'person' and 'summary'

    # ---------- Build Prompt ----------
    lines = [
        "=== Self‑Reflection ===",
        "",
        "Recent Emotions:",
    ]

    for emo in emotions:
        lines.append(f"- {emo}")

    lines.extend(["", "Recent Interactions and Relationships:"])

    for inter in interactions:
        person = inter.get("person", "Unknown")
        summary = inter.get("summary", "")
        lines.append(f"- With {person}: {summary}")

    lines.extend([
        "",
        "Take a moment to consider how these emotions and relationships influence your "
        "current goals, values, and actions. What insights arise?"
    ])

    prompt = "\n".join(lines)

    # ---------- Log Prompt ----------
    _log_experience(prompt)

    return prompt


def _log_experience(text: str):
    """
    Append the reflection text to the self‑experience log.
    The log lives under the experiment's `data/experience.log` file.
    """
    # Resolve path: <workspace>/data/experience.log
    log_path = Path(__file__).resolve().parents[2] / "data" / "experience.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.utcnow().isoformat()
    entry = f"[{timestamp}] {text}\n{'=' * 40}\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


if __name__ == "__main__":
    # When run directly, output a sample reflection to stdout.
    print(generate_self_reflection())