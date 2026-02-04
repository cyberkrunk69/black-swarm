"""
hedging_detector_benchmark.py

Benchmark suite for the hedging‑detector using the self_observer pattern.
The goal is to measure detection latency, precision, recall and to
demonstrate a ≥30 % reduction in false‑positive rate compared to the
baseline implementation.

Usage:
    python -m experiments.exp_20260204_031503_unified_session_128.hedging_detector_benchmark \
        --data-path /path/to/validation_set.jsonl \
        --baseline-module baseline.hedging_detector \
        --candidate-module my_project.hedging_detector

The script assumes each line of the data file is a JSON object:
{
    "utterance": "...",
    "is_hedging": true|false
}
"""

import argparse
import importlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Callable, Dict, List, Tuple

# ----------------------------------------------------------------------
# Self‑observer utilities
# ----------------------------------------------------------------------


class SelfObserver:
    """
    Minimal self‑observer implementation that records function calls,
    execution time and any raised exceptions.  It can be mixed into a
    detector class via multiple inheritance or monkey‑patched at runtime.
    """

    def __init__(self):
        self.call_log: List[Dict] = []

    def observe(self, func: Callable) -> Callable:
        """Wrap *func* so that each invocation is logged."""

        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                success = True
                exc = None
            except Exception as e:  # pragma: no cover – safety net
                result = None
                success = False
                exc = e
                raise
            finally:
                elapsed = time.perf_counter() - start
                self.call_log.append(
                    {
                        "func_name": func.__name__,
                        "args": args,
                        "kwargs": kwargs,
                        "result": result,
                        "success": success,
                        "exception": exc,
                        "elapsed": elapsed,
                    }
                )
            return result

        return wrapper

    def reset(self):
        self.call_log.clear()


def load_detector(module_path: str, class_name: str = "HedgingDetector") -> Tuple[object, SelfObserver]:
    """
    Dynamically import a detector class, instantiate it and attach a
    SelfObserver instance to it.  The returned tuple is (detector, observer).
    """
    module = importlib.import_module(module_path)
    detector_cls = getattr(module, class_name)
    detector = detector_cls()
    observer = SelfObserver()
    # Monkey‑patch the public `detect` method (if present)
    if hasattr(detector, "detect"):
        detector.detect = observer.observe(detector.detect)
    else:
        raise AttributeError(f"{module_path}.{class_name} does not implement a `detect` method")
    return detector, observer


# ----------------------------------------------------------------------
# Benchmark core
# ----------------------------------------------------------------------


def load_dataset(data_path: Path) -> List[Dict]:
    """Load a JSONL validation set."""
    with data_path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def evaluate(
    detector: object,
    dataset: List[Dict],
) -> Tuple[Counter, float]:
    """
    Run *detector* on *dataset* and return a Counter with TP/FP/FN/TN and
    the average latency per utterance (seconds).
    """
    stats = Counter()
    total_latency = 0.0

    for entry in dataset:
        utterance = entry["utterance"]
        gold = entry["is_hedging"]

        start = time.perf_counter()
        pred = detector.detect(utterance)
        latency = time.perf_counter() - start

        total_latency += latency

        if pred is True and gold is True:
            stats["TP"] += 1
        elif pred is True and gold is False:
            stats["FP"] += 1
        elif pred is False and gold is True:
            stats["FN"] += 1
        elif pred is False and gold is False:
            stats["TN"] += 1
        else:  # pragma: no cover – defensive
            stats["UNKNOWN"] += 1

    avg_latency = total_latency / len(dataset) if dataset else 0.0
    return stats, avg_latency


def compute_metrics(stats: Counter) -> Dict[str, float]:
    """Calculate precision, recall, f1 and false‑positive rate."""
    tp = stats["TP"]
    fp = stats["FP"]
    fn = stats["FN"]
    tn = stats["TN"]
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fpr,
    }


def compare_false_positive_rates(
    baseline_fpr: float, candidate_fpr: float
) -> float:
    """
    Return the percentage reduction in false‑positive rate.
    Positive numbers indicate improvement.
    """
    if baseline_fpr == 0:
        return 0.0
    reduction = (baseline_fpr - candidate_fpr) / baseline_fpr * 100.0
    return reduction


def run_benchmark(args: argparse.Namespace):
    # Load data
    dataset = load_dataset(Path(args.data_path))

    # Load baseline detector
    baseline, baseline_observer = load_detector(args.baseline_module)
    # Load candidate detector
    candidate, candidate_observer = load_detector(args.candidate_module)

    # Evaluate baseline
    base_stats, base_latency = evaluate(baseline, dataset)
    base_metrics = compute_metrics(base_stats)

    # Evaluate candidate
    cand_stats, cand_latency = evaluate(candidate, dataset)
    cand_metrics = compute_metrics(cand_stats)

    # Compute improvement
    fpr_reduction = compare_false_positive_rates(
        base_metrics["false_positive_rate"], cand_metrics["false_positive_rate"]
    )

    # Output summary
    print("\n=== Hedging‑Detector Benchmark ===")
    print(f"Dataset size: {len(dataset)} utterances")
    print("\n--- Baseline ---")
    print(f"  Precision: {base_metrics['precision']:.3f}")
    print(f"  Recall:    {base_metrics['recall']:.3f}")
    print(f"  F1:        {base_metrics['f1']:.3f}")
    print(f"  FPR:       {base_metrics['false_positive_rate']:.3%}")
    print(f"  Latency:   {base_latency*1000:.2f} ms/utterance")
    print("\n--- Candidate ---")
    print(f"  Precision: {cand_metrics['precision']:.3f}")
    print(f"  Recall:    {cand_metrics['recall']:.3f}")
    print(f"  F1:        {cand_metrics['f1']:.3f}")
    print(f"  FPR:       {cand_metrics['false_positive_rate']:.3%}")
    print(f"  Latency:   {cand_latency*1000:.2f} ms/utterance")
    print("\n--- Improvement ---")
    print(f"  False‑positive reduction: {fpr_reduction:.2f}%")

    if fpr_reduction >= 30.0:
        print("\n✅ Target achieved: ≥30 % reduction in false positives.")
    else:
        print("\n⚠️ Target not met: reduction < 30 %.")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark for hedging‑detector implementations using self_observer."
    )
    parser.add_argument(
        "--data-path",
        required=True,
        help="Path to a JSONL file containing validation utterances.",
    )
    parser.add_argument(
        "--baseline-module",
        required=True,
        help="Python import path for the baseline detector (e.g., baseline.hedging_detector).",
    )
    parser.add_argument(
        "--candidate-module",
        required=True,
        help="Python import path for the candidate detector to evaluate.",
    )
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    run_benchmark(args)