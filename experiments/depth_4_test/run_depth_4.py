import sys
import os

# Ensure the repository root is on the PYTHONPATH
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.append(repo_root)

from recursive_improvement_engine import RecursiveImprovementEngine

def dummy_atomizer():
    """
    Depth‑1 placeholder tool. In the real system this would be the existing
    atomizer that builds tasks.
    """
    def tool(*args, **kwargs):
        # Simple mock behaviour
        return "atomized_output"
    return tool

if __name__ == "__main__":
    engine = RecursiveImprovementEngine(
        initial_builder=dummy_atomizer,
        max_depth=4,
        improvement_threshold=0.005  # tighter threshold for the experiment
    )
    history = engine.run()
    for record in history:
        print(f"Depth {record['depth']}: score={record['score']:.4f}")