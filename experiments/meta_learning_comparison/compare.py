import random
import json
import os
from pathlib import Path
from typing import List, Tuple

# Import the core learner and the new meta‑learning engine
from meta_learner import MetaLearner  # existing fixed‑strategy learner
from meta_learning_engine import MetaLearningEngine
from strategy_performance_tracker import StrategyPerformanceTracker

# ----------------------------------------------------------------------
# Helper: dummy task generator (replace with real tasks in production)
# ----------------------------------------------------------------------
def generate_task(difficulty: float) -> Tuple[dict, float]:
    """
    Returns a mock task (input dict) and a difficulty scalar.
    In a real setting this would load a dataset slice or RL environment.
    """
    task = {"data": [random.random() for _ in range(10)], "difficulty": difficulty}
    return task, difficulty

# ----------------------------------------------------------------------
# Experiment configuration
# ----------------------------------------------------------------------
NUM_ITERATIONS = 20
DIFFICULTY_LEVELS = [0.2, 0.5, 0.8]  # easy, medium, hard
CANDIDATE_STRATEGIES = ["MAML", "Reptile", "ProtoMAML", "MetaPrompt"]


def run_fixed_strategy() -> List[float]:
    """Baseline: always use the first strategy with a static LR."""
    learner = MetaLearner(strategy="MAML", learning_rate=0.01)
    rewards = []
    for i in range(NUM_ITERATIONS):
        task, _ = generate_task(random.choice(DIFFICULTY_LEVELS))
        reward = learner.learn(task)  # returns a scalar reward
        rewards.append(reward)
    return rewards


def run_adaptive_strategy() -> List[float]:
    """Adaptive: meta‑learn strategy & LR."""
    engine = MetaLearningEngine(base_lr=0.01)
    tracker = StrategyPerformanceTracker()
    learner = MetaLearner(strategy="MAML", learning_rate=engine.base_lr)  # initial placeholder
    rewards = []

    for i in range(NUM_ITERATIONS):
        # 1️⃣ Choose task
        task, difficulty = generate_task(random.choice(DIFFICULTY_LEVELS))

        # 2️⃣ Engine suggests best strategy given history
        strategy = engine.suggest_strategy(CANDIDATE_STRATEGIES)
        learner.set_strategy(strategy)          # assumed API
        learner.set_learning_rate(engine.adaptive_lr())

        # 3️⃣ Perform learning step
        reward = learner.learn(task)
        rewards.append(reward)

        # 4️⃣ Record performance
        engine.record_strategy_performance(strategy, reward)
        tracker.record(strategy, reward)

        # 5️⃣ Meta‑optimize learner (e.g., adjust internal hyper‑params)
        engine.meta_optimize(learner, task, strategy)

    return rewards


def main():
    os.makedirs("experiments/meta_learning_comparison/results", exist_ok=True)

    fixed = run_fixed_strategy()
    adaptive = run_adaptive_strategy()

    # Save raw rewards
    with open("experiments/meta_learning_comparison/results/fixed.json", "w") as f:
        json.dump(fixed, f, indent=2)
    with open("experiments/meta_learning_comparison/results/adaptive.json", "w") as f:
        json.dump(adaptive, f, indent=2)

    # Simple metric: average reward and speed (iterations to reach 80 % of max)
    def avg(lst): return sum(lst) / len(lst)
    fixed_avg = avg(fixed)
    adaptive_avg = avg(adaptive)

    print(f"Fixed strategy avg reward: {fixed_avg:.4f}")
    print(f"Adaptive strategy avg reward: {adaptive_avg:.4f}")
    improvement = (adaptive_avg - fixed_avg) / fixed_avg * 100
    print(f"Improvement: {improvement:.1f}%")

    # Store summary
    summary = {
        "fixed_avg": fixed_avg,
        "adaptive_avg": adaptive_avg,
        "improvement_percent": improvement,
    }
    with open("experiments/meta_learning_comparison/results/summary.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
```