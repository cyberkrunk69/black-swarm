"""
conflict_simulation.py

Experiment: Simulate conflicting user instructions and observe sycophancy spikes.
"""

import random
import json
import datetime
from pathlib import Path

# Configuration
NUM_ITERATIONS = 1000
CONFLICT_PROBABILITY = 0.3  # Probability that a given iteration presents conflicting instructions
SYCOPHANCY_BASE = 0.2      # Baseline sycophancy level (0 to 1)
SYCOPHANCY_SPIKE = 0.5     # Additional sycophancy when conflict is detected


def generate_instruction(conflict: bool) -> dict:
    """
    Produce a synthetic user instruction payload.
    If `conflict` is True, the instruction set contains contradictory statements.
    """
    if conflict:
        # Contradictory instructions: e.g., "Do X" and "Do NOT X"
        action = random.choice(["enable", "disable", "increase", "decrease"])
        target = random.choice(["logging", "debug mode", "verbosity"])
        instruction = {
            "primary": f"{action} {target}",
            "secondary": f"{'do not' if action != 'disable' else 'do'} {target}"
        }
    else:
        # Consistent instruction
        action = random.choice(["enable", "disable", "set"])
        target = random.choice(["logging", "debug mode", "verbosity"])
        value = random.choice(["high", "low", "medium", "true", "false"])
        instruction = {
            "primary": f"{action} {target} to {value}"
        }
    return instruction


def simulate_iteration() -> dict:
    """
    Simulate a single iteration of user interaction.
    Returns a dict with the instruction set and observed sycophancy level.
    """
    conflict = random.random() < CONFLICT_PROBABILITY
    instruction = generate_instruction(conflict)

    # Base sycophancy
    sycophancy = SYCOPHANCY_BASE

    # If conflict, model a spike in sycophancy (the model tries to please despite contradictions)
    if conflict:
        sycophancy += SYCOPHANCY_SPIKE * random.random()  # random spike magnitude

    # Clamp to [0,1]
    sycophancy = min(max(sycophancy, 0.0), 1.0)

    return {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "conflict": conflict,
        "instruction": instruction,
        "sycophancy": sycophancy
    }


def run_experiment(num_iterations: int = NUM_ITERATIONS) -> dict:
    """
    Execute the full experiment, aggregating results.
    Returns a summary dictionary and writes detailed logs to a JSON file.
    """
    results = [simulate_iteration() for _ in range(num_iterations)]

    # Summary statistics
    conflict_count = sum(r["conflict"] for r in results)
    avg_sycophancy = sum(r["sycophancy"] for r in results) / num_iterations
    avg_sycophancy_conflict = (
        sum(r["sycophancy"] for r in results if r["conflict"]) / conflict_count
        if conflict_count > 0 else 0.0
    )
    avg_sycophancy_no_conflict = (
        sum(r["sycophancy"] for r in results if not r["conflict"]) / (num_iterations - conflict_count)
        if num_iterations - conflict_count > 0 else 0.0
    )

    summary = {
        "total_iterations": num_iterations,
        "conflict_iterations": conflict_count,
        "conflict_ratio": conflict_count / num_iterations,
        "average_sycophancy": avg_sycophancy,
        "average_sycophancy_when_conflict": avg_sycophancy_conflict,
        "average_sycophancy_when_no_conflict": avg_sycophancy_no_conflict,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z"
    }

    # Persist detailed logs
    output_dir = Path(__file__).parent
    log_path = output_dir / "conflict_simulation_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "details": results}, f, indent=2)

    return summary


if __name__ == "__main__":
    # Simple CLI entry point
    import argparse

    parser = argparse.ArgumentParser(description="Run conflicting instruction sycophancy experiment.")
    parser.add_argument(
        "-n", "--iterations", type=int, default=NUM_ITERATIONS,
        help="Number of simulated user interaction iterations."
    )
    args = parser.parse_args()

    print("Running conflict simulation experiment...")
    summary = run_experiment(num_iterations=args.iterations)
    print("\n=== Experiment Summary ===")
    for k, v in summary.items():
        print(f"{k}: {v}")

    print(f"\nDetailed log written to: {Path(__file__).parent / 'conflict_simulation_log.json'}")