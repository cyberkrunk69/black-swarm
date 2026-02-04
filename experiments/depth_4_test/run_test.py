\"\"\"Run a controlled depth‑4 recursive self‑improvement experiment.

This script is intended for quick verification that the recursive engine
operates safely and yields measurable improvements across all four levels.
\"\"\"

from types import SimpleNamespace
from recursive_improvement_engine import RecursiveImprovementEngine

def main():
    # Create a minimal initial state with a baseline capability score.
    initial_state = SimpleNamespace(score=1.0)

    engine = RecursiveImprovementEngine()
    final_state = engine.run(initial_state)

    # Output the detailed report.
    report = engine.report()
    print(report)

    # Persist the report for archival.
    with open("experiments/depth_4_test/report.txt", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    main()