"""
Unit tests for the Atomizer implementation.
"""

import unittest
from typing import List

from ..atomizer import Atomizer, TaskSpec, atomize_and_execute


def _identity(x):
    return x


class TestAtomizer(unittest.TestCase):
    def setUp(self) -> None:
        # Simple DAG:
        #   A   B
        #    \ /
        #     C
        self.tasks = [
            TaskSpec(task_id="A", func=_identity, args=(1,)),
            TaskSpec(task_id="B", func=_identity, args=(2,)),
            TaskSpec(task_id="C", func=_identity, args=(3,), depends_on={"A", "B"}),
        ]

    def test_ready_batches(self):
        atomizer = Atomizer(self.tasks)
        batches = atomizer.ready_batches()
        # First batch should contain A and B (order not guaranteed)
        self.assertEqual(len(batches), 2)
        self.assertSetEqual(batches[0], {"A", "B"})
        self.assertSetEqual(batches[1], {"C"})

    def test_schedule_execution(self):
        results = Atomizer(self.tasks).schedule(max_workers=2)
        self.assertEqual(results, {"A": 1, "B": 2, "C": 3})

    def test_helper_function(self):
        results = atomize_and_execute(self.tasks, max_workers=2)
        self.assertEqual(results, {"A": 1, "B": 2, "C": 3})

    def test_cycle_detection(self):
        # Introduce a cycle: C depends on A, A depends on C
        cyclic_tasks = [
            TaskSpec(task_id="A", func=_identity, args=(1,), depends_on={"C"}),
            TaskSpec(task_id="C", func=_identity, args=(3,), depends_on={"A"}),
        ]
        with self.assertRaises(ValueError):
            Atomizer(cyclic_tasks)


if __name__ == "__main__":
    unittest.main()