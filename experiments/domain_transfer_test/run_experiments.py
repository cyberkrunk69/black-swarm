```python
"""
experiments/domain_transfer_test/run_experiments.py

Convenient entry point to execute the cross‑domain transfer benchmarks
and report summary statistics.
"""

import subprocess
import sys
import pathlib

def main():
    suite_path = pathlib.Path(__file__).parent.parent / "benchmarks" / "transfer_learning_suite.py"
    result = subprocess.run([sys.executable, str(suite_path)], capture_output=True, text=True)
    print("=== Transfer Learning Benchmark Output ===")
    print(result.stdout)
    if result.stderr:
        print("=== Errors ===", file=sys.stderr)
        print(result.stderr, file=sys.stderr)

if __name__ == "__main__":
    main()
```