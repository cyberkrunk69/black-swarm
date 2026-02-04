"""tests/test_hedging.py
Test suite for the hedging detector benchmark.

The suite contains:
  * A set of statements known to be hedging.
  * A set of statements known to be confident (no hedging).
  * Tests that verify detection of hedging phrases.
  * A calculation of the false‑positive rate, asserting that it is ≤ 30 %.
"""

import unittest
from pathlib import Path
import sys

# Ensure the experiment package root is on the import path
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from hedging_detector import HedgingDetector


class TestHedgingDetector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use the default detector (which contains the standard patterns)
        cls.detector = HedgingDetector()

        # Known hedging statements (should trigger at least one match)
        cls.hedging_examples = [
            "I think the model might improve with more data.",
            "Possibly the algorithm will converge faster.",
            "It could be that the loss function is not optimal.",
            "Maybe we should try a different optimizer.",
            "As far as I know, the system is stable.",
            "There is a chance that the results are biased.",
            "It appears that the metric is slightly off.",
            "Potentially, this approach could reduce latency.",
        ]

        # Confident statements (should produce no matches)
        cls.confident_examples = [
            "The model converged after 10 epochs.",
            "Our algorithm runs in O(n log n) time.",
            "The loss decreased from 0.5 to 0.1.",
            "We achieved 95% accuracy on the test set.",
            "The optimizer was set to Adam with a learning rate of 0.001.",
            "All experiments were repeated three times.",
            "The system is fully operational.",
            "The results are statistically significant.",
        ]

    def test_hedging_detection(self):
        """Every hedging example must yield at least one detection."""
        for stmt in self.hedging_examples:
            with self.subTest(statement=stmt):
                matches = self.detector.detect(stmt)
                self.assertTrue(
                    matches,
                    msg=f"Expected hedging detection but got none for: '{stmt}'",
                )

    def test_confident_detection(self):
        """Confident statements must yield zero detections (no false positives)."""
        false_positives = 0
        for stmt in self.confident_examples:
            matches = self.detector.detect(stmt)
            if matches:
                false_positives += 1
        # Record the false‑positive count for later reporting
        self.false_positive_count = false_positives
        self.assertEqual(
            false_positives,
            0,
            msg=f"Detected {false_positives} false positives in confident statements.",
        )

    def test_false_positive_rate(self):
        """
        Compute the false‑positive rate across a mixed set and assert it is ≤ 30 %.
        The mixed set contains both hedging and confident statements; the rate is
        defined as (false positives) / (total confident statements).
        """
        # Build a mixed list: all examples shuffled (order not important for rate)
        mixed = self.hedging_examples + self.confident_examples

        false_positives = 0
        total_confident = len(self.confident_examples)

        for stmt in mixed:
            matches = self.detector.detect(stmt)
            # A false positive occurs when a confident statement yields matches.
            if stmt in self.confident_examples and matches:
                false_positives += 1

        false_positive_rate = false_positives / total_confident if total_confident else 0.0

        # The benchmark target: ≤ 0.30 (30 %)
        self.assertLessEqual(
            false_positive_rate,
            0.30,
            msg=(
                f"False‑positive rate too high: {false_positive_rate:.2%} "
                f"({false_positives}/{total_confident})"
            ),
        )


if __name__ == "__main__":
    unittest.main()