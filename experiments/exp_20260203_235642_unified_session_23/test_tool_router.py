import unittest
from tool_router import ToolRouter


def free_tool(task):
    return f"free:{task}"


def cheap_tool(task):
    return f"cheap:{task}"


def expensive_tool(task):
    return f"expensive:{task}"


class TestToolRouter(unittest.TestCase):
    def setUp(self):
        self.router = ToolRouter()
        self.router.register_tool(
            name="free_echo",
            cost_category="free",
            can_handle=lambda t: isinstance(t, str) and t.startswith("echo"),
            executor=free_tool,
        )
        self.router.register_tool(
            name="cheap_math",
            cost_category="cheap",
            can_handle=lambda t: isinstance(t, int),
            executor=cheap_tool,
        )
        self.router.register_tool(
            name="expensive_generic",
            cost_category="expensive",
            can_handle=lambda t: True,
            executor=expensive_tool,
        )

    def test_routing_to_free(self):
        result = self.router.route("echo hello")
        self.assertEqual(result, "free:echo hello")

    def test_routing_to_cheap(self):
        result = self.router.route(42)
        self.assertEqual(result, "cheap:42")

    def test_fallback_to_expensive(self):
        # Neither free nor cheap can handle a list, so we fall back
        result = self.router.route([1, 2, 3])
        self.assertEqual(result, "expensive:[1, 2, 3]")

    def test_no_tool(self):
        # Remove all tools and ensure proper error
        empty_router = ToolRouter()
        with self.assertRaises(RuntimeError):
            empty_router.route("anything")


if __name__ == "__main__":
    unittest.main()