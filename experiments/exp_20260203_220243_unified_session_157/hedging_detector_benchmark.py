"""
Hedging Detector Benchmark
--------------------------

This module implements a benchmark for evaluating hedging‑detector models
using the self_observer pattern infrastructure already present in the
project. The benchmark focuses on:

* Consistent data loading via the `SelfObserverDataset`.
* Metric calculation that includes precision, recall, F1 and a
  false‑positive reduction target of 30 % compared to the baseline.
* Reporting in a JSON‑serialisable format for downstream aggregation.

The benchmark can be invoked from the command line:

    python -m experiments.exp_20260203_220243_unified_session_157.hedging_detector_benchmark \
        --model_path path/to/model.pt \
        --dataset_path path/to/dataset.json \
        --baseline_fp_rate 0.15 \
        --output results.json

The `baseline_fp_rate` argument represents the false‑positive rate of a
reference implementation. The benchmark will compute the achieved false‑positive
rate and assert that it is at least a 30 % reduction relative to the baseline.
"""

import argparse
import json
import os
from typing import Dict, Any, List

import torch
from torch.utils.data import DataLoader

# Import the self_observer dataset and utilities from the core package.
# These imports assume that the core package is on the PYTHONPATH.
from self_observer.dataset import SelfObserverDataset
from self_observer.metrics import compute_precision_recall_f1, compute_false_positive_rate


def load_model(model_path: str) -> torch.nn.Module:
    """Load a torch model from the given path."""
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    model = torch.load(model_path, map_location="cpu")
    model.eval()
    return model


def evaluate_model(
    model: torch.nn.Module,
    dataloader: DataLoader,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Run inference on the dataset and collect predictions and ground truth
    labels needed for metric computation.
    """
    all_preds: List[int] = []
    all_labels: List[int] = []

    model.to(device)

    with torch.no_grad():
        for batch in dataloader:
            inputs = batch["input"].to(device)
            labels = batch["label"].to(device)

            logits = model(inputs)
            preds = torch.argmax(logits, dim=1)

            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())

    precision, recall, f1 = compute_precision_recall_f1(all_preds, all_labels)
    fp_rate = compute_false_positive_rate(all_preds, all_labels)

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fp_rate,
        "total_samples": len(all_labels),
        "positive_predictions": sum(all_preds),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Hedging detector benchmark")
    parser.add_argument("--model_path", required=True, help="Path to the trained model file")
    parser.add_argument("--dataset_path", required=True, help="Path to the self_observer JSON dataset")
    parser.add_argument(
        "--baseline_fp_rate",
        type=float,
        required=True,
        help="False‑positive rate of the baseline system (e.g., 0.15 for 15 %)",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        help="Batch size for evaluation",
    )
    parser.add_argument(
        "--output",
        default="benchmark_results.json",
        help="File to write benchmark results",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Device to run inference on (cpu or cuda)",
    )
    args = parser.parse_args()

    # Load dataset via the self_observer wrapper
    dataset = SelfObserverDataset(args.dataset_path)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False)

    # Load model
    model = load_model(args.model_path)

    # Evaluate
    results = evaluate_model(model, dataloader, device=args.device)

    # Compute reduction relative to baseline
    baseline_fp = args.baseline_fp_rate
    achieved_fp = results["false_positive_rate"]
    reduction = (baseline_fp - achieved_fp) / baseline_fp if baseline_fp > 0 else 0.0
    results["baseline_false_positive_rate"] = baseline_fp
    results["false_positive_reduction"] = reduction
    results["target_reduction_met"] = reduction >= 0.30

    # Persist results
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Simple console feedback
    print(f"Benchmark completed. Results written to {args.output}")
    print(f"False‑positive reduction: {reduction:.2%} (target ≥ 30 %)")
    if results["target_reduction_met"]:
        print("✅ Target achieved.")
    else:
        print("⚠️ Target not achieved.")


if __name__ == "__main__":
    main()