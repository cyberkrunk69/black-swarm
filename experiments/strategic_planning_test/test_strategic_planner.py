import unittest
from strategic_planner import StrategicPlanner
from benchmarks.planning_suite import (
    benchmark_full_stack_app,
    benchmark_paper_implementation,
    benchmark_cost_optimized_deadline,
)

class TestStrategicPlanner(unittest.TestCase):
    def _run_benchmark(self, goal, resources, min_steps):
        planner = StrategicPlanner(resources=resources)
        plan = planner.generate_plan(goal, horizon=min_steps)
        # Basic sanity checks
        self.assertTrue(len(plan) >= min_steps // 2)  # we expect at least half the steps
        prob = planner.estimate_success(plan)
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)

    def test_full_stack_app(self):
        goal, resources, min_steps = benchmark_full_stack_app()
        self._run_benchmark(goal, resources, min_steps)

    def test_paper_implementation(self):
        goal, resources, min_steps = benchmark_paper_implementation()
        self._run_benchmark(goal, resources, min_steps)

    def test_cost_optimized_deadline(self):
        goal, resources, min_steps = benchmark_cost_optimized_deadline()
        self._run_benchmark(goal, resources, min_steps)

    def test_replanning(self):
        goal, resources, _ = benchmark_full_stack_app()
        planner = StrategicPlanner(resources=resources)
        initial_plan = planner.generate_plan(goal, horizon=10)
        # Simulate a goal change after a few steps
        state = {
            "resources": {"budget": resources["budget"] - 200, "time": resources["time"] - 10},
            "completed_steps": initial_plan[:3],
        }
        new_goal = "Add real‑time chat feature to the previously built app"
        new_plan = planner.replan(state, [new_goal], horizon=10)
        # Ensure completed steps are preserved and new steps are added
        self.assertEqual(new_plan[:3], state["completed_steps"])
        self.assertTrue(len(new_plan) > 3)

if __name__ == "__main__":
    unittest.main()