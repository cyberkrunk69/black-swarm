import os

class EngineSelector:
    def __init__(self):
        self.budget = 100  # initial budget

    def select_engine(self, task):
        """
        Determine which LLM engine to use for a given task.

        task: dict with at least the keys:
            - description (str): human‑readable description
            - complexity (str): "low" or "high"
            - critical (bool): whether the task is critical
        Returns: "Groq" or "Claude"
        """
        # 3️⃣ Explicit Override (highest priority)
        desc = task.get("description", "").lower()
        if "use groq" in desc:
            return "Groq"
        if "use claude" in desc:
            return "Claude"

        # 1️⃣ Complexity Analysis
        comp = task.get("complexity", "").lower()
        if comp == "low":
            return "Groq"
        if comp == "high":
            return "Claude"

        # 2️⃣ Budget Awareness
        if self.budget < 20:
            return "Groq"
        if task.get("critical", False) and self.budget > 50:
            return "Claude"

        # Default fallback
        return "Groq"

    def update_budget(self, cost):
        """Deduct cost from the remaining budget."""
        self.budget -= cost

    def handle_quality_feedback(self, task, engine, success):
        """
        If the chosen engine (Groq) produced a failing result,
        retry with Claude. Otherwise keep the original engine.
        """
        if not success and engine == "Groq":
            return "Claude"
        return engine