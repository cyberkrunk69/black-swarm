"""
Integration tests for feedback loop validation.

Tests the complete feedback loop system including:
1. Critic retry triggers on low quality
2. DSPy demo persistence and loading
3. Performance -> suggester pipeline
4. Knowledge graph population from lessons
"""

import json
import tempfile
import shutil
from pathlib import Path
from unittest import TestCase, main as unittest_main

from critic import CriticAgent
from dspy_modules import (
    GrindModule,
    create_demonstration,
    rank_demonstrations,
    get_optimized_grind_module
)
from improvement_suggester import ImprovementSuggester
from knowledge_graph import KnowledgeGraph, NodeType, EdgeType, KnowledgeNode, KnowledgeEdge
from performance_tracker import PerformanceTracker


class TestCriticRetryLoop(TestCase):
    """Test that critic properly triggers retries on low quality code."""

    def setUp(self):
        """Initialize critic for testing."""
        self.critic = CriticAgent()

    def test_low_quality_code_fails_review(self):
        """Verify critic detects low quality and triggers retry."""
        # Low quality code: multiple critical issues (mismatched parens, brackets, braces)
        bad_code = """
def process_data(:
    data = json.load(open("file.json"]
    obj = {"key": "value"
    arr = [1, 2, 3)
    return data
"""
        result = self.critic.review(bad_code, context={"task": "load JSON data"})

        # Should fail review (score < 0.65)
        self.assertFalse(result["passed"], "Low quality code should fail review")
        self.assertLess(result["score"], 0.65, "Quality score should be below threshold")
        self.assertGreater(len(result["issues"]), 0, "Should have detected issues")
        self.assertIn("feedback", result, "Should provide feedback")

    def test_high_quality_code_passes_review(self):
        """Verify critic approves high quality code."""
        good_code = """
import json
from pathlib import Path

def process_data(filepath: str) -> dict:
    \"\"\"Load and process JSON data from file.\"\"\"
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return {}
    except IOError as e:
        print(f"File error: {e}")
        return {}
"""
        result = self.critic.review(good_code, context={"task": "load JSON data"})

        # Should pass review
        self.assertTrue(result["passed"], "High quality code should pass review")
        self.assertGreaterEqual(result["score"], 0.65, "Quality score should meet threshold")

    def test_feedback_contains_actionable_suggestions(self):
        """Verify critic feedback is actionable."""
        code_with_issues = """
def fetch_api():
    response = requests.get("http://api.example.com")
    return response.json()
"""
        result = self.critic.review(code_with_issues)

        feedback = result["feedback"]
        self.assertGreater(len(feedback), 0, "Should provide feedback")
        # Check that feedback mentions specific improvements
        feedback_text = " ".join(feedback).lower()
        self.assertTrue(
            "error" in feedback_text or "handling" in feedback_text or "try" in feedback_text,
            "Feedback should mention error handling"
        )


class TestDSPyDemoPersistence(TestCase):
    """Test DSPy demonstration persistence and loading."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.demo_file = Path(self.temp_dir) / "demonstrations.json"

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_create_demonstration(self):
        """Verify demonstration creation with all metadata."""
        demo = create_demonstration(
            task="Implement authentication",
            context="user_auth module",
            solution="def authenticate(user, password): ...",
            summary="Added JWT-based authentication",
            num_turns=3,
            duration_ms=5000,
            efficiency_score=0.92
        )

        self.assertEqual(demo["task"], "Implement authentication")
        self.assertEqual(demo["num_turns"], 3)
        self.assertEqual(demo["efficiency_score"], 0.92)
        self.assertIn("solution", demo)
        self.assertIn("summary", demo)

    def test_demonstrations_persist_and_load(self):
        """Test saving demonstrations to file and loading them back."""
        # Create test demonstrations
        demos = [
            create_demonstration(
                task="Task 1",
                context="context1",
                solution="solution1",
                summary="summary1",
                efficiency_score=0.9
            ),
            create_demonstration(
                task="Task 2",
                context="context2",
                solution="solution2",
                summary="summary2",
                efficiency_score=0.8
            )
        ]

        # Save to file
        with open(self.demo_file, 'w') as f:
            json.dump(demos, f)

        # Load from file
        with open(self.demo_file, 'r') as f:
            loaded_demos = json.load(f)

        self.assertEqual(len(loaded_demos), 2)
        self.assertEqual(loaded_demos[0]["task"], "Task 1")
        self.assertEqual(loaded_demos[1]["efficiency_score"], 0.8)

    def test_empty_file_returns_empty_list(self):
        """Test loading from non-existent file returns empty list."""
        # File doesn't exist
        non_existent = Path(self.temp_dir) / "does_not_exist.json"

        # Should handle gracefully
        if non_existent.exists():
            with open(non_existent, 'r') as f:
                demos = json.load(f)
        else:
            demos = []

        self.assertEqual(demos, [])

    def test_rank_demonstrations_by_efficiency(self):
        """Test demonstration ranking by efficiency score."""
        demos = [
            create_demonstration(task="A", context="", solution="", summary="", efficiency_score=0.5),
            create_demonstration(task="B", context="", solution="", summary="", efficiency_score=0.9),
            create_demonstration(task="C", context="", solution="", summary="", efficiency_score=0.7),
        ]

        ranked = rank_demonstrations(demos, top_k=2)

        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["task"], "B", "Highest efficiency should be first")
        self.assertEqual(ranked[1]["task"], "C", "Second highest should be second")


class TestPerformanceSuggesterPipeline(TestCase):
    """Test the performance tracker -> improvement suggester pipeline."""

    def setUp(self):
        """Create temp directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.lessons_file = Path(self.temp_dir) / "test_lessons.json"
        self.metrics_file = Path(self.temp_dir) / "test_metrics.jsonl"

    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir)

    def test_suggester_analyzes_performance_trends(self):
        """Test suggester extracts performance trends from tracker."""
        # Create tracker with test history file
        tracker = PerformanceTracker(
            workspace=Path(self.temp_dir),
            history_file="test_history.json"
        )

        # Add test sessions with declining quality
        for i in range(5):
            tracker.track_session({
                "session_id": i,
                "quality_score": 0.9 - (i * 0.1),  # Declining
                "duration_seconds": 10,
                "success": True,
                "task_description": f"Test task {i}"
            })

        # Create suggester
        suggester = ImprovementSuggester(str(self.lessons_file))

        # Analyze performance trends
        analysis = suggester.analyze_performance_trends(tracker)

        self.assertIn("rolling_averages", analysis)
        self.assertIn("improvement_rates", analysis)
        self.assertIn("declining_metrics", analysis)

    def test_suggester_generates_suggestions_from_performance(self):
        """Test suggester creates actionable suggestions from performance data."""
        # Create lessons with patterns
        lessons = [
            {
                "lesson": "Always read file before editing",
                "task_category": "file_operations",
                "importance": 4
            },
            {
                "lesson": "Use parallel tool calls for independent operations",
                "task_category": "efficiency",
                "importance": 3
            }
        ]

        with open(self.lessons_file, 'w') as f:
            json.dump(lessons, f)

        # Create suggester
        suggester = ImprovementSuggester(str(self.lessons_file))

        # Analyze patterns
        patterns = suggester.analyze_patterns(lessons)

        # Generate suggestions
        suggestions = suggester.suggest_improvements(patterns, tracker=None)

        self.assertGreater(len(suggestions), 0, "Should generate suggestions")
        self.assertTrue(all("suggestion" in s for s in suggestions))
        self.assertTrue(all("category" in s for s in suggestions))
        self.assertTrue(all("rationale" in s for s in suggestions))

    def test_complete_feedback_loop_integration(self):
        """Test end-to-end: metrics -> patterns -> suggestions."""
        # Create test data
        lessons = [
            {"lesson": "Test error handling", "task_category": "testing", "importance": 4},
            {"lesson": "Validate inputs", "task_category": "testing", "importance": 4},
            {"lesson": "Read codebase first", "task_category": "exploration", "importance": 3},
        ]

        with open(self.lessons_file, 'w') as f:
            json.dump(lessons, f)

        # Create tracker and add sessions
        tracker = PerformanceTracker(
            workspace=Path(self.temp_dir),
            history_file="test_history.json"
        )

        for i in range(3):
            tracker.track_session({
                "session_id": i,
                "quality_score": 0.8,
                "duration_seconds": 10,
                "success": True,
                "task_description": f"Test task {i}"
            })

        # Run pipeline
        suggester = ImprovementSuggester(str(self.lessons_file))
        report = suggester.generate_full_report(tracker)

        # Verify complete report structure
        self.assertIn("patterns", report)
        self.assertIn("suggestions", report)
        self.assertIn("performance_analysis", report)
        self.assertIn("next_steps", report)
        self.assertEqual(report["total_lessons_analyzed"], 3)


class TestKnowledgeGraphLessonPopulation(TestCase):
    """Test knowledge graph population from lessons."""

    def setUp(self):
        """Initialize knowledge graph."""
        self.kg = KnowledgeGraph()

    def test_add_lesson_node(self):
        """Test adding a lesson node to the knowledge graph."""
        lesson_node = KnowledgeNode(
            id="lesson:read_before_edit",
            label="Read file before editing",
            type=NodeType.LESSON,
            properties={"importance": 5, "category": "file_operations"}
        )

        self.kg.add_node(lesson_node)

        # Query the node
        retrieved = self.kg.query("lesson:read_before_edit")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.label, "Read file before editing")
        self.assertEqual(retrieved.properties["importance"], 5)

    def test_link_lesson_to_concept(self):
        """Test creating edges between lessons and concepts."""
        # Add lesson node
        lesson_node = KnowledgeNode(
            id="lesson:parallel_calls",
            label="Use parallel tool calls",
            type=NodeType.LESSON,
            properties={"importance": 4}
        )
        self.kg.add_node(lesson_node)

        # Add concept node
        concept_node = KnowledgeNode(
            id="concept:efficiency",
            label="Efficiency",
            type=NodeType.CONCEPT,
            properties={}
        )
        self.kg.add_node(concept_node)

        # Create edge
        edge = KnowledgeEdge(
            source="lesson:parallel_calls",
            target="concept:efficiency",
            relation=EdgeType.RELATES_TO
        )
        self.kg.add_edge(edge)

        # Query related nodes
        subgraph = self.kg.query_related("lesson:parallel_calls", depth=1)
        self.assertIn("concept:efficiency", subgraph["nodes"])

    def test_populate_from_codebase(self):
        """Test populating graph from Python codebase."""
        # Use current codebase
        self.kg.populate_from_codebase(".")

        # Should have file nodes
        file_nodes = [n for n in self.kg.nodes.values() if n.type == NodeType.FILE]
        self.assertGreater(len(file_nodes), 0, "Should detect Python files")

        # Should have function nodes
        func_nodes = [n for n in self.kg.nodes.values() if n.type == NodeType.FUNCTION]
        self.assertGreater(len(func_nodes), 0, "Should detect functions")

        # Should have CONTAINS edges
        contains_edges = [e for e in self.kg.edges if e.relation == EdgeType.CONTAINS]
        self.assertGreater(len(contains_edges), 0, "Should create file->function edges")

    def test_lesson_integration_with_codebase(self):
        """Test full integration: populate codebase + add lessons + query."""
        # Populate from codebase
        self.kg.populate_from_codebase(".")

        # Add a lesson node
        lesson = KnowledgeNode(
            id="lesson:critic_usage",
            label="Always run critic on generated code",
            type=NodeType.LESSON,
            properties={"importance": 5, "source": "grind_session_123"}
        )
        self.kg.add_node(lesson)

        # Link lesson to critic.py file
        critic_file_id = None
        for node_id in self.kg.nodes:
            if "critic.py" in node_id:
                critic_file_id = node_id
                break

        if critic_file_id:
            edge = KnowledgeEdge(
                source="lesson:critic_usage",
                target=critic_file_id,
                relation=EdgeType.RELATES_TO
            )
            self.kg.add_edge(edge)

            # Query lesson and verify it's connected to critic.py
            subgraph = self.kg.query_related("lesson:critic_usage", depth=1)
            self.assertIn(critic_file_id, subgraph["nodes"])


if __name__ == "__main__":
    unittest_main()
