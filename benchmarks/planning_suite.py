\"\"\"Benchmark suite for evaluating the StrategicPlanner.

Each benchmark returns a tuple:
    (strategic_goal: str, resources: dict, expected_min_steps: int)

The test harness can feed these into StrategicPlanner.generate_plan()
and compare against reference solutions.
\"\"\"

from typing import Tuple, Dict, List

def benchmark_full_stack_app() -> Tuple[str, Dict[str, float], int]:
    goal = (
        "Design and implement a full‑stack web application including "
        "frontend UI, backend API, database schema, CI/CD pipeline, and "
        "deployment to cloud."
    )
    resources = {"budget": 800.0, "time": 72.0}  # hours
    expected_min_steps = 30
    return goal, resources, expected_min_steps

def benchmark_paper_implementation() -> Tuple[str, Dict[str, float], int]:
    goal = (
        "Research, reproduce and extend the results of the 2023 "
        "\"Neural Architecture Search via Reinforcement Learning\" paper."
    )
    resources = {"budget": 1200.0, "time": 120.0}
    expected_min_steps = 25  # approximate lower bound
    return goal, resources, expected_min_steps

def benchmark_cost_optimized_deadline() -> Tuple[str, Dict[str, float], int]:
    goal = (
        "Deliver a set of three new features for the existing product "
        "while staying under $300 budget and completing within 40 hours."
    )
    resources = {"budget": 300.0, "time": 40.0}
    expected_min_steps = 15
    return goal, resources, expected_min_steps

def list_all_benchmarks() -> List[Tuple[str, Dict[str, float], int]]:
    return [
        benchmark_full_stack_app(),
        benchmark_paper_implementation(),
        benchmark_cost_optimized_deadline(),
    ]
import unittest
from typing import List

# Import the strategic planner and a dummy action registry
from strategic_planner import StrategicPlanner, GoalNode

# ----------------------------------------------------------------------
# Dummy atomic actions for testing – each returns a string and carries a
# ``success_prob`` attribute used by the planner's success estimator.
# ----------------------------------------------------------------------
def dummy_action(name: str, success: float = 0.95):
    def fn():
        return f"executed {name}"
    fn.success_prob = success
    fn.__name__ = name
    return fn

# Build a minimal registry that the planner can query.
ACTION_REGISTRY = {
    "setup_database": dummy_action("setup_database"),
    "implement_api": dummy_action("implement_api"),
    "write_frontend": dummy_action("write_frontend"),
    "run_tests": dummy_action("run_tests"),
    "deploy_to_prod": dummy_action("deploy_to_prod"),
    "research_paper": dummy_action("research_paper"),
    "write_summary": dummy_action("write_summary"),
    "optimize_cost": dummy_action("optimize_cost"),
}

# ----------------------------------------------------------------------
# Benchmark definitions
# ----------------------------------------------------------------------
def build_fullstack_goal() -> GoalNode:
    """
    Strategic goal: Build a full‑stack web application.
    Decomposes into 5 operational sub‑goals.
    """
    root = GoalNode("Build Full‑Stack App", "strategic")
    tactical = GoalNode("Develop Application", "tactical")
    root.add_subgoal(tactical)

    ops = [
        GoalNode("setup_database", "operational", resources={"time": 2}),
        GoalNode("implement_api", "operational", resources={"time": 4}),
        GoalNode("write_frontend", "operational", resources={"time": 5}),
        GoalNode("run_tests", "operational", resources={"time": 2}),
        GoalNode("deploy_to_prod", "operational", resources={"time": 1}),
    ]
    for op in ops:
        tactical.add_subgoal(op)
    return root

def build_research_goal() -> GoalNode:
    """
    Strategic goal: Research and implement a paper.
    Unknown number of steps – we model as two high‑level tasks.
    """
    root = GoalNode("Research & Implement Paper", "strategic")
    tactical = GoalNode("Complete Project", "tactical")
    root.add_subgoal(tactical)

    tactical.add_subgoal(GoalNode("research_paper", "operational", resources={"time": 6}))
    tactical.add_subgoal(GoalNode("write_summary", "operational", resources={"time": 3}))
    return root

def build_cost_optimization_goal() -> GoalNode:
    """
    Strategic goal: Optimize a system for cost under a deadline.
    Constraints are expressed via the GoalNode.constraints dict.
    """
    root = GoalNode("Cost‑Optimized Delivery", "strategic", constraints={"deadline": 10})
    tactical = GoalNode("Deliver Within Budget", "tactical", constraints={"budget": 1000})
    root.add_subgoal(tactical)

    tactical.add_subgoal(GoalNode("optimize_cost", "operational", resources={"time": 4, "budget": 200}))
    tactical.add_subgoal(GoalNode("run_tests", "operational", resources={"time": 2, "budget": 50}))
    return root

# ----------------------------------------------------------------------
# Unit tests that act as the benchmark harness
# ----------------------------------------------------------------------
class StrategicPlanningBenchmarks(unittest.TestCase):
    def setUp(self):
        self.planner = StrategicPlanner(
            action_registry=ACTION_REGISTRY,
            resource_budget={"time": 20, "budget": 1500},
            lookahead_depth=3,
        )

    def _run_and_check(self, goal: GoalNode, expected_steps: List[str]):
        plan = self.planner.plan(goal)
        # Verify length & ordering (simple containment check)
        self.assertEqual(len(plan), len(expected_steps))
        for step in expected_steps:
            self.assertIn(step, plan)
        # Verify success estimate is reasonable (>0.7 for these simple cases)
        self.assertGreaterEqual(self.planner.estimate_success(plan), 0.7)

    def test_fullstack_plan(self):
        goal = build_fullstack_goal()
        expected = [
            "setup_database",
            "implement_api",
            "write_frontend",
            "run_tests",
            "deploy_to_prod",
        ]
        self._run_and_check(goal, expected)

    def test_research_plan(self):
        goal = build_research_goal()
        expected = ["research_paper", "write_summary"]
        self._run_and_check(goal, expected)

    def test_cost_optimization_plan(self):
        goal = build_cost_optimization_goal()
        expected = ["optimize_cost", "run_tests"]
        self._run_and_check(goal, expected)

    def test_replanning_on_goal_change(self):
        # Initial plan
        goal = build_fullstack_goal()
        original_plan = self.planner.plan(goal)

        # Modify the strategic goal (replace one operational sub‑goal)
        goal.subgoals[0].subgoals[2] = GoalNode("write_frontend_v2", "operational")
        # Add a matching dummy action so mapping works
        ACTION_REGISTRY["write_frontend_v2"] = dummy_action("write_frontend_v2")
        replanned = self.planner.replan_if_needed(goal)

        self.assertNotEqual(original_plan, replanned)
        self.assertIn("write_frontend_v2", replanned)

if __name__ == "__main__":
    unittest.main()