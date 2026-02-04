"""
hedging_detector_benchmark.py

Benchmark suite for evaluating hedging‑detector models using the
self_observer pattern. The benchmark measures precision, recall,
F1‑score and specifically tracks false‑positive rate (FPR).  An
adjustable post‑processing filter is provided to target a 30 %
reduction in false positives relative to a baseline configuration.

Usage
-----
>>> from hedging_detector_benchmark import HedgingBenchmark
>>> benchmark = HedgingBenchmark(detector, baseline_threshold=0.5)
>>> results = benchmark.run(test_dataset)
>>> print(results)

The benchmark is deliberately lightweight and has no external
dependencies beyond the standard library and `numpy`.
"""

import json
import math
from collections import defaultdict
from typing import Callable, Iterable, List, Tuple, Dict, Any

import numpy as np


class SelfObserver:
    """
    Minimal self‑observer implementation.  Objects register callbacks
    that are invoked when the observer records a new event.  This
    pattern enables the benchmark to emit granular telemetry without
    tightly coupling to the detector implementation.
    """

    def __init__(self):
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []

    def subscribe(self, fn: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback that receives a dict describing the event."""
        self._subscribers.append(fn)

    def notify(self, event: Dict[str, Any]) -> None:
        """Broadcast an event to all subscribers."""
        for fn in self._subscribers:
            fn(event)


class HedgingBenchmark:
    """
    Runs a hedging‑detector on a dataset and computes evaluation metrics.
    The benchmark uses a SelfObserver instance to emit per‑sample events
    (prediction, ground‑truth, confidence, etc.).  A simple
    post‑processing filter can be tuned to cut false positives by a
    target percentage.
    """

    def __init__(
        self,
        detector: Callable[[str], Tuple[bool, float]],
        baseline_threshold: float = 0.5,
        target_fp_reduction: float = 0.30,
    ):
        """
        Parameters
        ----------
        detector
            Callable that receives a text sample and returns a tuple:
            (is_hedging: bool, confidence: float in [0,1]).
        baseline_threshold
            Confidence threshold used for the baseline run.
        target_fp_reduction
            Desired fractional reduction in false‑positive rate (e.g. 0.30 for 30 %).
        """
        self.detector = detector
        self.baseline_threshold = baseline_threshold
        self.target_fp_reduction = target_fp_reduction
        self.observer = SelfObserver()

    # --------------------------------------------------------------------- #
    # Helper methods
    # --------------------------------------------------------------------- #
    @staticmethod
    def _apply_threshold(pred: bool, conf: float, thresh: float) -> bool:
        """Return the final binary decision after applying confidence threshold."""
        return pred and conf >= thresh

    def _collect_events(
        self,
        dataset: Iterable[Tuple[str, bool]],
        threshold: float,
    ) -> List[Dict[str, Any]]:
        """
        Run the detector on every sample, emit events, and collect them.

        Returns
        -------
        List of event dicts with keys:
            - text
            - gold (bool)
            - pred (bool)
            - confidence (float)
            - threshold (float)
        """
        events = []
        for text, gold in dataset:
            pred_raw, conf = self.detector(text)
            pred = self._apply_threshold(pred_raw, conf, threshold)
            event = {
                "text": text,
                "gold": gold,
                "pred_raw": pred_raw,
                "pred": pred,
                "confidence": conf,
                "threshold": threshold,
            }
            self.observer.notify(event)
            events.append(event)
        return events

    # --------------------------------------------------------------------- #
    # Metric computation
    # --------------------------------------------------------------------- #
    @staticmethod
    def _metrics_from_events(events: List[Dict[str, Any]]) -> Dict[str, float]:
        tp = sum(1 for e in events if e["gold"] and e["pred"])
        tn = sum(1 for e in events if not e["gold"] and not e["pred"])
        fp = sum(1 for e in events if not e["gold"] and e["pred"])
        fn = sum(1 for e in events if e["gold"] and not e["pred"])

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        fpr = fp / (fp + tn) if (fp + tn) else 0.0

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "false_positive_rate": fpr,
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
        }

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def run(
        self,
        dataset: Iterable[Tuple[str, bool]],
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute the benchmark.

        Steps
        -----
        1. Run baseline (no post‑processing) and compute baseline FPR.
        2. Search for a new threshold that reduces FPR by the target amount
           while keeping recall as high as possible.
        3. Return a report containing both baseline and tuned results.

        Returns
        -------
        dict with keys:
            - baseline: metric dict
            - tuned: metric dict
            - chosen_threshold: float
            - reduction_achieved: float
        """
        # 1. Baseline run
        baseline_events = self._collect_events(dataset, self.baseline_threshold)
        baseline_metrics = self._metrics_from_events(baseline_events)

        if verbose:
            print(f"Baseline metrics: {json.dumps(baseline_metrics, indent=2)}")

        # 2. Threshold search – simple linear scan over [0.0, 1.0] step 0.01
        #    We aim for at least target_fp_reduction relative to baseline.
        target_fpr = baseline_metrics["false_positive_rate"] * (
            1 - self.target_fp_reduction
        )
        best_threshold = self.baseline_threshold
        best_metrics = baseline_metrics
        best_recall = baseline_metrics["recall"]

        for thresh in np.arange(0.0, 1.01, 0.01):
            events = self._collect_events(dataset, float(thresh))
            metrics = self._metrics_from_events(events)

            if metrics["false_positive_rate"] <= target_fpr:
                # Prefer higher recall when multiple thresholds satisfy the target.
                if metrics["recall"] > best_recall:
                    best_threshold = float(thresh)
                    best_metrics = metrics
                    best_recall = metrics["recall"]

        reduction_achieved = (
            1
            - best_metrics["false_positive_rate"]
            / baseline_metrics["false_positive_rate"]
            if baseline_metrics["false_positive_rate"] > 0
            else 0.0
        )

        if verbose:
            print(f"Tuned threshold: {best_threshold}")
            print(f"Tuned metrics: {json.dumps(best_metrics, indent=2)}")
            print(f"Reduction achieved: {reduction_achieved:.2%}")

        report = {
            "baseline": baseline_metrics,
            "tuned": best_metrics,
            "chosen_threshold": best_threshold,
            "reduction_achieved": reduction_achieved,
        }

        return report


# -------------------------------------------------------------------------
# Example stub detector (to be replaced by a real model)
# -------------------------------------------------------------------------
def example_stub_detector(text: str) -> Tuple[bool, float]:
    """
    Very simple heuristic detector used for quick sanity checks.
    Returns (is_hedging, confidence).
    """
    hedging_cues = {"maybe", "perhaps", "possibly", "could be", "might"}
    tokens = set(text.lower().split())
    overlap = len(tokens & hedging_cues)
    confidence = min(1.0, overlap / 2.0)  # max confidence 1.0
    return (overlap > 0, confidence)


# -------------------------------------------------------------------------
# If run as script, perform a tiny demo
# -------------------------------------------------------------------------
if __name__ == "__main__":
    demo_data = [
        ("I think it might rain tomorrow.", True),
        ("The sky is blue.", False),
        ("Perhaps we should consider alternatives.", True),
        ("It is definitely sunny.", False),
        ("There could be a chance of snow.", True),
    ]

    bench = HedgingBenchmark(example_stub_detector, baseline_threshold=0.3)
    result = bench.run(demo_data, verbose=True)
    print("\n=== Benchmark Summary ===")
    print(json.dumps(result, indent=2))