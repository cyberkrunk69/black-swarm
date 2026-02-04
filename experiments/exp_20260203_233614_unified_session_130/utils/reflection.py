import json
import os
import re
from typing import List, Dict, Any

# Path to the episodic memory store (learned_lessons.json)
_LESSONS_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "learned_lessons.json"
    )
)


def _load_lessons() -> List[Dict[str, Any]]:
    """Load the episodic memory from disk. Returns an empty list if the file does not exist."""
    if not os.path.exists(_LESSONS_PATH):
        return []
    with open(_LESSONS_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # Corrupt file – start fresh
            return []


def _save_lessons(lessons: List[Dict[str, Any]]) -> None:
    """Persist the episodic memory back to disk."""
    os.makedirs(os.path.dirname(_LESSONS_PATH), exist_ok=True)
    with open(_LESSONS_PATH, "w", encoding="utf-8") as f:
        json.dump(lessons, f, indent=4, ensure_ascii=False)


def add_reflection(
    task_id: str,
    feedback_signal: Dict[str, Any],
    verbal_reflection: str,
    verification_result: bool
) -> None:
    """
    Record a new reflection (episodic memory entry).

    Parameters
    ----------
    task_id : str
        Identifier of the task/experiment.
    feedback_signal : dict
        Raw error/output that triggered the reflection. Expected keys:
        - ``trial_number`` (optional)
        - ``error_message`` or ``output`` (any string describing the failure)
    verbal_reflection : str
        Natural‑language summary of the insight.
    verification_result : bool
        Whether the insight proved useful in a subsequent trial.
    """
    lessons = _load_lessons()

    # Determine trial number – fall back to len(lessons)+1 if not supplied
    trial_number = feedback_signal.get("trial_number")
    if trial_number is None:
        trial_number = len(lessons) + 1

    # Extract the raw feedback text
    task_feedback = feedback_signal.get("error_message") or feedback_signal.get(
        "output"
    ) or str(feedback_signal)

    # Simple heuristic to generate retrieval cues: split on non‑alphanum,
    # lower‑case, and keep unique tokens longer than 2 characters.
    tokens = set(
        filter(
            lambda t: len(t) > 2,
            re.split(r"\W+", task_feedback.lower())
        )
    )
    retrieval_cues = list(tokens)

    lesson_entry = {
        "task_id": task_id,
        "trial_number": trial_number,
        "task_feedback": task_feedback,
        "self_verification": verification_result,
        "retrieval_cues": retrieval_cues,
        "reflection": verbal_reflection,
    }

    lessons.append(lesson_entry)
    _save_lessons(lessons)


def retrieve_relevant_lessons(task_description: str) -> List[Dict[str, Any]]:
    """
    Retrieve lessons whose ``retrieval_cues`` match keywords in the supplied
    task description.

    Parameters
    ----------
    task_description : str
        Natural‑language description of the current task.

    Returns
    -------
    List[dict]
        Subset of stored lessons deemed relevant.
    """
    lessons = _load_lessons()
    description_tokens = set(
        filter(
            lambda t: len(t) > 2,
            re.split(r"\W+", task_description.lower())
        )
    )

    relevant = []
    for lesson in lessons:
        cues = set(map(str.lower, lesson.get("retrieval_cues", [])))
        if cues & description_tokens:
            relevant.append(lesson)

    return relevant


def synthesize_lessons(lessons: List[Dict[str, Any]]) -> str:
    """
    Condense a collection of lessons into a single prompt‑injection string.
    The output can be prefixed to a LLM prompt to provide contextual memory.

    Parameters
    ----------
    lessons : List[dict]
        Lessons to be synthesized.

    Returns
    -------
    str
        Human‑readable summary ready for injection.
    """
    if not lessons:
        return ""

    synthesized_parts = []
    for idx, lesson in enumerate(lessons, start=1):
        part = (
            f"Lesson {idx} (Task {lesson.get('task_id', 'N/A')}, "
            f"Trial {lesson.get('trial_number', 'N/A')}): {lesson.get('reflection')}"
        )
        synthesized_parts.append(part)

    header = "Relevant past insights:\n"
    body = "\n".join(synthesized_parts)
    return header + body + "\nEnd of insights.\n"


# Example usage (remove or comment out in production)
if __name__ == "__main__":
    # Simulate adding a reflection
    add_reflection(
        task_id="demo_task",
        feedback_signal={"trial_number": 3, "error_message": "ValueError: could not convert string to float"},
        verbal_reflection="Validate numeric strings before casting to float.",
        verification_result=True,
    )

    # Retrieve and synthesize
    desc = "Need to parse user supplied numbers safely."
    relevant = retrieve_relevant_lessons(desc)
    prompt_injection = synthesize_lessons(relevant)
    print(prompt_injection)