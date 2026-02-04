# Meta‑Learning Comparison Experiments

This folder contains scripts and results for comparing the **fixed** learning
strategy against the **adaptive** meta‑learning engine.

## Running the Experiments

```bash
python run_meta_learning_experiment.py --variant fixed   # baseline
python run_meta_learning_experiment.py --variant adaptive   # meta‑learned
```

The script logs:
- Iteration‑wise loss curves
- Strategy selection frequencies
- Learning‑rate trajectory
- Final performance metrics (saved in `results/`)

## Expected Output

- `results/fixed.json`
- `results/adaptive.json`
- Plots in `results/plots/`

The adaptive run should show at least a 20 % improvement in convergence speed
or final quality over the fixed baseline.