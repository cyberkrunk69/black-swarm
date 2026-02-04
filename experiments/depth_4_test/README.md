# Depth‑4 Recursive Self‑Improvement Test

This directory contains the results of running the recursive improvement
engine with a maximum depth of **4**.

## Contents
- `run.log` – Full stdout/stderr captured from the experiment.
- `capability.csv` – Tab‑separated values: `depth,score,delta`.
- `notes.md` – Human‑written observations about emergent capabilities.

## How to Re‑run
```bash
mkdir -p experiments/depth_4_test
python - <<'PY'
import sys, os
from recursive_improvement_engine import RecursiveImprovementEngine

log_path = os.path.join("experiments", "depth_4_test", "run.log")
with open(log_path, "w") as f:
    sys.stdout = f
    sys.stderr = f
    engine = RecursiveImprovementEngine(max_depth=4)
    engine.run()
PY
```

The log file will be overwritten with each execution.
# Depth‑4 Test Suite

This directory contains artifacts for the depth‑4 recursive improvement experiment.

## Contents
- `run.sh` – convenience script to execute the experiment.
- `expected_output.md` – snapshot of a successful run for regression checks.

## Running the Test
```bash
cd experiments/depth_4_test
./run.sh
```

The script invokes `python ../../recursive_improvement_engine.py` and
compares the output against `expected_output.md`. Adjust expectations
if the capability measurement model changes.