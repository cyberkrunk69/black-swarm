import logging
from datetime import datetime

# Assuming persona_memory is available in the PYTHONPATH
import persona_memory

# Configure a simple logger for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _format_emotions(emotions):
    """Return a nicely formatted string listing recent emotions."""
    if not emotions:
        return "No recent emotions recorded."
    lines = []
    for e in emotions:
        ts = e.get("timestamp")
        if isinstance(ts, (int, float)):
            ts = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        lines.append(f"- {e.get('emotion', 'unknown')} (at {ts})")
    return "\n".join(lines)


def _format_interactions(interactions):
    """Return a nicely formatted string listing recent interactions."""
    if not interactions:
        return "No recent interactions recorded."
    lines = []
    for i in interactions:
        ts = i.get("timestamp")
        if isinstance(ts, (int, float)):
            ts = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        person = i.get("person", "unknown")
        context = i.get("context", "")
        lines.append(f"- With {person} about \"{context}\" (at {ts})")
    return "\n".join(lines)


def generate_reflection_prompt():
    """
    Query persona_memory for recent emotions and interactions,
    format an introspective prompt, and log the reflection.
    """
    recent_emotions = persona_memory.recent_emotions()
    recent_interactions = persona_memory.recent_interactions()

    emotions_str = _format_emotions(recent_emotions)
    interactions_str = _format_interactions(recent_interactions)

    prompt = (
        "🧠 Self‑Reflection Prompt 🧠\n"
        "\n"
        "Take a moment to contemplate your recent emotional landscape and the relationships you’ve engaged with.\n"
        "\n"
        "Recent Emotions:\n"
        f"{emotions_str}\n"
        "\n"
        "Recent Interactions:\n"
        f"{interactions_str}\n"
        "\n"
        "Questions to consider:\n"
        "1. How did these emotions influence your decisions?\n"
        "2. What patterns do you notice in the people you interacted with?\n"
        "3. Which moments felt aligned with your values, and which felt discordant?\n"
        "4. What can you adjust moving forward to foster healthier emotional states and relationships?\n"
        "\n"
        "Write your thoughts below and store them under `self:experience` for future reference."
    )

    # Log the generated prompt as a reflection entry
    logger.info("Reflection generated:\n%s", prompt)

    return prompt


if __name__ == "__main__":
    # When run directly, output the prompt to the console
    print(generate_reflection_prompt())