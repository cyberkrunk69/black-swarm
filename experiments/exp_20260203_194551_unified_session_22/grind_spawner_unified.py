"""
Enhanced EngineSelector with adaptive logic for Claude/Groq selection.
"""

from typing import Dict, Any

class EngineSelector:
    """
    Decide which LLM engine (Claude or Groq) to use for a given task.
    Selection criteria:
      1. Explicit overrides in the task description.
      2. Complexity analysis based on task type.
      3. Budget awareness (low budget → Groq, critical+budget → Claude).
      4. Quality feedback – if Groq fails verification, fall back to Claude.
    """

    SIMPLE_TYPES = {"create_file", "fix_typo"}
    COMPLEX_TYPES = {"design", "refactor", "security"}

    def __init__(self):
        # Store a simple failure cache for learning patterns (task_type -> fail count)
        self.groq_failure_counts: Dict[str, int] = {}

    def _has_override(self, description: str) -> str | None:
        """Return forced engine name if an explicit override is present."""
        lowered = description.lower()
        if "use groq" in lowered:
            return "Groq"
        if "use claude" in lowered:
            return "Claude"
        return None

    def _complexity_engine(self, task_type: str) -> str:
        """Select based on task complexity."""
        if task_type in self.SIMPLE_TYPES:
            return "Groq"
        if task_type in self.COMPLEX_TYPES:
            return "Claude"
        # Default to Groq for unknown types (conservative)
        return "Groq"

    def _budget_engine(self, budget: float, critical: bool) -> str:
        """Select based on budget and critical flag."""
        LOW_BUDGET_THRESHOLD = 10.0  # arbitrary low‑budget cutoff
        if budget < LOW_BUDGET_THRESHOLD:
            return "Groq"
        if critical and budget >= LOW_BUDGET_THRESHOLD:
            return "Claude"
        # Fallback
        return "Groq"

    def select_engine(self, task: Dict[str, Any]) -> str:
        """
        Main entry point.
        `task` must contain at least:
            - type: str
            - description: str
            - budget: float
            - critical: bool
        Returns "Claude" or "Groq".
        """
        # 1️⃣ Explicit override
        override = self._has_override(task.get("description", ""))
        if override:
            return override

        # 2️⃣ Complexity analysis
        engine = self._complexity_engine(task.get("type", ""))

        # 3️⃣ Budget awareness – may override complexity decision
        budget_engine = self._budget_engine(task.get("budget", 0.0), task.get("critical", False))
        # If budget decision differs from complexity, give precedence to budget when critical
        if budget_engine != engine:
            if task.get("critical", False):
                engine = budget_engine
            else:
                # Non‑critical: keep complexity choice (cheaper by default)
                pass

        # 4️⃣ Quality feedback hook – callers should invoke `record_failure`
        #    when a Groq result fails verification. The selector itself does not
        #    re‑run the task; the orchestrator can call `select_engine` again after
        #    a failure, and the cached failure count will bias the choice toward Claude.
        if engine == "Groq":
            fail_count = self.groq_failure_counts.get(task.get("type", ""), 0)
            if fail_count >= 2:  # arbitrary threshold for “learned” pattern
                engine = "Claude"

        return engine

    # ----------------------------------------------------------------------
    # Helper for quality‑feedback loop
    # ----------------------------------------------------------------------
    def record_failure(self, task_type: str) -> None:
        """Call when a Groq output fails verification."""
        self.groq_failure_counts[task_type] = self.groq_failure_counts.get(task_type, 0) + 1


# ----------------------------------------------------------------------
# Example usage (for reference – not executed in production)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    selector = EngineSelector()

    sample_tasks = [
        {"type": "create_file", "description": "", "budget": 5, "critical": False},
        {"type": "design", "description": "", "budget": 20, "critical": True},
        {"type": "fix_typo", "description": "please use groq for this", "budget": 5, "critical": False},
        {"type": "refactor", "description": "use claude", "budget": 15, "critical": True},
    ]

    for t in sample_tasks:
        engine = selector.select_engine(t)
        print(f"Task {t['type']} → Engine: {engine}")

        # Simulate a Groq failure for demonstration
        if engine == "Groq" and t["type"] == "create_file":
            selector.record_failure(t["type"])