import os
import sys
import csv
import numpy as np

# Adjust PYTHONPATH so that imports resolve relative to the repo root
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.append(repo_root)

from meta_learner import MetaLearner
from strategy_performance_tracker import log_performance

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
RESULT_FILE = os.path.join(RESULTS_DIR, "comparison.csv")

def evaluate(learner, tasks, max_epochs=20):
    """
    Run the learner on `tasks` for a fixed number of epochs.
    Returns a list of final success metrics per epoch.
    """
    epoch_success = []
    for epoch in range(max_epochs):
        # For simplicity we reuse the same task list each epoch
        learner.train(tasks)
        # Assume learner exposes a `last_success` attribute (mocked here)
        success = getattr(learner, "last_success", np.random.rand())
        epoch_success.append(success)
        # Log for later analysis
        log_performance(epoch, "adaptive" if learner.meta_engine else "fixed",
                        success,
                        learner.meta_engine.get_learning_rate() if hasattr(learner, "meta_engine") else None)
    return epoch_success

def main():
    # Mock task list – in a real run this would be concrete few‑shot problems
    mock_tasks = ["task_a", "task_b", "task_c", "task_d"]

    # -------- Baseline (fixed strategy) ----------
    baseline_learner = MetaLearner()
    baseline_success = evaluate(baseline_learner, mock_tasks)

    # -------- Adaptive (meta‑learned strategy) ----------
    adaptive_learner = MetaLearner()
    # Force engine creation (the train() method will lazily create it)
    adaptive_success = evaluate(adaptive_learner, mock_tasks)

    # Save aggregated results
    with open(RESULT_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "baseline_success", "adaptive_success"])
        for epoch, (b, a) in enumerate(zip(baseline_success, adaptive_success)):
            writer.writerow([epoch, b, a])

    # Simple summary output
    baseline_final = baseline_success[-1]
    adaptive_final = adaptive_success[-1]
    improvement = (adaptive_final - baseline_final) / baseline_final * 100 if baseline_final != 0 else float('inf')
    print(f"Baseline final success: {baseline_final:.4f}")
    print(f"Adaptive final success: {adaptive_final:.4f}")
    print(f"Improvement: {improvement:.2f}%")

if __name__ == "__main__":
    main()
import logging
import copy
from meta_learner import MetaLearner
from meta_learning_engine import MetaLearningEngine
from strategy_performance_tracker import StrategyPerformanceTracker

# ----------------------------------------------------------------------
# Simple mock task class (replace with real task objects in production)
# ----------------------------------------------------------------------
class MockTask:
    _counter = 0
    def __init__(self):
        self.id = MockTask._counter
        MockTask._counter += 1
        # dummy validation set placeholder
        self.validation_set = None

# ----------------------------------------------------------------------
# Baseline: fixed strategy (no meta‑learning)
# ----------------------------------------------------------------------
def baseline_experiment(num_iterations=20):
    logging.info("Running baseline (fixed strategy) experiment")
    model = ...  # placeholder: instantiate your model here
    optimizer = ...  # placeholder: instantiate optimizer with lr=1e-3
    learner = MetaLearner(model, optimizer)

    # Force the meta‑engine to always pick the “default” strategy
    learner.meta_engine = MetaLearningEngine(base_lr=optimizer.param_groups[0]["lr"])
    learner.meta_engine.select_strategy = lambda candidates: "default"

    tasks = [MockTask() for _ in range(num_iterations)]
    learner.train(tasks)
    learner.finalize()
    return learner

# ----------------------------------------------------------------------
# Adaptive: meta‑learned strategy selection
# ----------------------------------------------------------------------
def adaptive_experiment(num_iterations=20):
    logging.info("Running adaptive (meta‑learned) experiment")
    model = ...  # placeholder
    optimizer = ...  # placeholder
    learner = MetaLearner(model, optimizer)

    tasks = [MockTask() for _ in range(num_iterations)]
    learner.train(tasks)
    learner.finalize()
    return learner

# ----------------------------------------------------------------------
# Simple metric aggregation
# ----------------------------------------------------------------------
def summarize(learner):
    # average of recorded metrics (stored in tracker)
    if not learner.tracker.records:
        return None
    avg = sum(r["metric"] for r in learner.tracker.records) / len(learner.tracker.records)
    return avg

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    baseline = baseline_experiment()
    adaptive = adaptive_experiment()

    base_score = summarize(baseline)
    adapt_score = summarize(adaptive)

    print(f"\n=== Results ===")
    print(f"Baseline average metric: {base_score:.4f}")
    print(f"Adaptive average metric: {adapt_score:.4f}")

    improvement = (adapt_score - base_score) / base_score * 100 if base_score else float('nan')
    print(f"Improvement: {improvement:.2f}%")
import os
import json
from meta_learning_engine import MetaLearningEngine
from meta_learner import FixedStrategyLearner  # existing baseline
from meta_learner import AdaptiveStrategyLearner  # will use the new engine
from strategy_performance_tracker import StrategyPerformanceTracker

def evaluate_engine(engine, tasks, iterations=20):
    results = []
    for i in range(iterations):
        task = tasks[i % len(tasks)]
        episode_result = engine.run_episode(task)
        results.append({
            "iteration": i,
            "task_id": task.id,
            "success": episode_result.get("success_metric", 0.0),
            "lr": engine.learning_rate,
        })
    return results

def main():
    # Load a small suite of representative tasks (placeholder)
    from task_suite import load_demo_tasks
    tasks = load_demo_tasks()

    # Baseline: fixed strategy (no meta‑adaptation)
    baseline_engine = MetaLearningEngine({
        "learning_rate": 0.01,
        "use_adaptive": False,   # flag ignored by new engine but kept for compatibility
    })
    baseline_results = evaluate_engine(baseline_engine, tasks)

    # Adaptive meta‑learning engine
    adaptive_engine = MetaLearningEngine({
        "learning_rate": 0.01,
        "use_adaptive": True,
        "performance_window": 5,
        "min_lr": 1e-5,
        "max_lr": 0.1,
        "lr_step": 1.2,
    })
    adaptive_results = evaluate_engine(adaptive_engine, tasks)

    # Simple metrics
    def avg_success(res):
        return sum(r["success"] for r in res) / len(res)

    print("Baseline avg success:", avg_success(baseline_results))
    print("Adaptive avg success:", avg_success(adaptive_results))

    # Store results for later analysis
    os.makedirs("experiments/meta_learning_comparison/results", exist_ok=True)
    with open("experiments/meta_learning_comparison/results/baseline.json", "w") as f:
        json.dump(baseline_results, f, indent=2)
    with open("experiments/meta_learning_comparison/results/adaptive.json", "w") as f:
        json.dump(adaptive_results, f, indent=2)

if __name__ == "__main__":
    main()
import random
import time
from pathlib import Path
from typing import List, Dict

# Import the core components from the repository
from meta_learning_engine import MetaLearningEngine
from strategy_performance_tracker import StrategyPerformanceTracker
# Assume the existing meta‑learner logic lives in meta_learner.py
from meta_learner import run_task_with_strategy, FIXED_STRATEGY

def generate_candidate_strategies() -> List[Dict]:
    """
    Create a small pool of plausible strategies.
    Each strategy dict must contain a unique ``id`` and any meta‑data
    required by ``run_task_with_strategy`` (e.g., tool choice, decomposition flag).
    """
    return [
        {"id": "fixed", **FIXED_STRATEGY},
        {"id": "toolA_decomp", "tool": "search", "decompose": True},
        {"id": "toolB_no_decomp", "tool": "codegen", "decompose": False},
        {"id": "toolC_mix", "tool": "hybrid", "decompose": True},
    ]

def evaluate_strategy(strategy: Dict) -> float:
    """
    Run a single learning iteration using the supplied strategy and return a
    scalar reward (e.g., improvement in loss or quality score).
    For demonstration we simulate a reward with random noise plus a hidden bias.
    """
    # Hidden true quality of each strategy (unknown to the engine)
    true_quality = {
        "fixed": 0.5,
        "toolA_decomp": 0.7,
        "toolB_no_decomp": 0.4,
        "toolC_mix": 0.8,
    }
    base = true_quality.get(strategy["id"], 0.5)
    noise = random.gauss(0, 0.05)
    return max(0.0, base + noise)  # reward is non‑negative

def main(iterations: int = 20):
    # Initialise components
    engine = MetaLearningEngine()
    tracker = StrategyPerformanceTracker()

    candidates = generate_candidate_strategies()

    for it in range(1, iterations + 1):
        # -----------------------------------------------------------------
        # Fixed baseline (for comparison)
        # -----------------------------------------------------------------
        fixed_reward = evaluate_strategy(FIXED_STRATEGY)
        tracker.log(it, "fixed", fixed_reward, engine.get_current_lr())

        # -----------------------------------------------------------------
        # Adaptive meta‑learning step
        # -----------------------------------------------------------------
        chosen = engine.select_strategy(candidates)
        reward = evaluate_strategy(chosen)

        # Register outcome so the engine can adapt LR and update its value estimates
        engine.register_outcome(chosen["id"], reward)

        # Log the adaptive step
        tracker.log(it, chosen["id"], reward, engine.get_current_lr())

        print(f"Iter {it:02d} | Fixed={fixed_reward:.3f} | "
              f"Adaptive({chosen['id']})={reward:.3f} | LR={engine.get_current_lr():.5f}")

    # Persist engine state for future runs
    engine.save_state()
    print("\nExperiment completed. Performance logs saved to:", tracker.file_path)

if __name__ == "__main__":
    main()
```
import os
import json
import matplotlib.pyplot as plt
from meta_learning_engine import MetaLearningEngine

def run_comparison(iterations=20):
    results = {"fixed": [], "adaptive": []}

    # ---- Baseline: fixed strategy ----
    engine_fixed = MetaLearningEngine()
    engine_fixed.current_strategy = "default"
    engine_fixed.tracker = None  # disable adaptive tracking
    for i in range(iterations):
        loss = engine_fixed.run_iteration(i)
        results["fixed"].append(loss)

    # ---- Adaptive: meta‑learned strategy ----
    engine_adapt = MetaLearningEngine()
    for i in range(iterations):
        loss = engine_adapt.run_iteration(i)
        results["adaptive"].append(loss)

    # Save raw data
    os.makedirs("experiments/meta_learning_comparison/results", exist_ok=True)
    with open("experiments/meta_learning_comparison/results/summary.json", "w") as f:
        json.dump(results, f, indent=2)

    # Plot comparison
    plt.figure(figsize=(8,5))
    plt.plot(results["fixed"], label="Fixed Strategy")
    plt.plot(results["adaptive"], label="Adaptive Strategy")
    plt.xlabel("Iteration")
    plt.ylabel("Loss")
    plt.title("Meta‑Learning Strategy Comparison")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("experiments/meta_learning_comparison/results/comparison.png")
    plt.show()

if __name__ == "__main__":
    run_comparison()