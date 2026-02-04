\"\"\"Run the depth‑4 recursive self‑improvement experiment.

This script is a thin wrapper around ``RecursiveImprovementEngine`` that
captures the JSON‑serialisable results and writes them to
``depth_4_results.json`` for later analysis.
\"\"\"

import json
import pathlib
from recursive_improvement_engine import RecursiveImprovementEngine

def main():
    engine = RecursiveImprovementEngine()
    results = engine.run()

    out_path = pathlib.Path(__file__).with_name("depth_4_results.json")
    out_path.write_text(json.dumps(results, indent=2))
    print(f\"Results written to {out_path}\")

if __name__ == \"__main__\":
    main()