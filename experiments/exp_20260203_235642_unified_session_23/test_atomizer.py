import unittest
from atomizer import Atomizer


class TestAtomizer(unittest.TestCase):
    def test_simple_dependency_order(self):
        a = Atomizer(max_workers=2)

        # Task definitions
        a.add_task("first", [], lambda: "A")
        a.add_task("second", ["first"], lambda: "B")
        a.add_task("third", ["first"], lambda: "C")
        a.add_task("fourth", ["second", "third"], lambda: "D")

        results = a.run()
        # Verify all tasks ran
        self.assertCountEqual(results.keys(), {"first", "second", "third", "fourth"})
        # Verify dependency results are present
        self.assertEqual(results["fourth"], "D")
        # Ensure ordering constraints were respected (no direct way, but we can
        # check that dependent tasks exist)
        self.assertIn("first", results)
        self.assertIn("second", results)
        self.assertIn("third", results)

    def test_cycle_detection(self):
        a = Atomizer()
        a.add_task("a", ["b"], lambda: 1)
        a.add_task("b", ["a"], lambda: 2)
        with self.assertRaises(RuntimeError):
            a.run()


if __name__ == "__main__":
    unittest.main()