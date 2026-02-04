import threading
from typing import Dict

class BudgetExceededError(RuntimeError):
    """Raised when the global budget limit is exceeded."""
    pass

class CostTracker:
    """
    Thread‑safe singleton that tracks monetary cost per skill execution.
    The global budget is $2.00 (configurable via `set_budget`).
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CostTracker, cls).__new__(cls)
                cls._instance._init_state()
            return cls._instance

    def _init_state(self):
        self.budget = 2.00               # default budget in USD
        self.total_spent = 0.0
        self.per_skill: Dict[str, float] = {}
        self.enabled = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_budget(self, amount: float):
        """Set a new budget (USD)."""
        with self._lock:
            self.budget = amount

    def enable(self):
        """Enable cost tracking (default)."""
        with self._lock:
            self.enabled = True

    def disable(self):
        """Temporarily disable cost tracking (e.g., cheap unit tests)."""
        with self._lock:
            self.enabled = False

    def add_cost(self, skill_name: str, cost: float):
        """
        Record cost for a skill. Raises BudgetExceededError if the new total
        would exceed the configured budget.
        """
        if not self.enabled:
            return  # no accounting when disabled

        with self._lock:
            new_total = self.total_spent + cost
            if new_total > self.budget:
                raise BudgetExceededError(
                    f"Budget of ${self.budget:.2f} exceeded. "
                    f"Attempted to add ${cost:.2f} for '{skill_name}'. "
                    f"Current spend: ${self.total_spent:.2f}"
                )
            self.total_spent = new_total
            self.per_skill[skill_name] = self.per_skill.get(skill_name, 0.0) + cost

    def reset(self):
        """Reset all accounting (useful between independent runs)."""
        with self._lock:
            self.total_spent = 0.0
            self.per_skill.clear()

    def report(self) -> str:
        """Human‑readable report of spend per skill and total."""
        lines = [f"Budget limit: ${self.budget:.2f}",
                 f"Total spent: ${self.total_spent:.2f}",
                 "Spend by skill:"]
        for skill, amt in sorted(self.per_skill.items(), key=lambda x: -x[1]):
            lines.append(f"  - {skill}: ${amt:.2f}")
        return "\n".join(lines)

# Export a ready‑to‑use singleton
cost_tracker = CostTracker()