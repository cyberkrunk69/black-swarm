# recursive_improvement_engine.py
# Core engine for recursive self‑improvement with depth tracking and safety checks.

import logging
from typing import Callable, Any

# Import safety parameters
from safety.recursion_bounds import (
    MAX_RECURSION_DEPTH,
    depth_allowed,
    improvement_safe,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RecursiveImprovementEngine:
    """
    Engine that orchestrates recursive self‑improvement across multiple depths.
    Each depth corresponds to a higher‑order meta‑tool that builds the tools of the
    previous level.
    """

    def __init__(self,
                 initial_tool_builder: Callable[[int], Any],
                 capability_evaluator: Callable[[Any], float]):
        """
        :param initial_tool_builder: Callable that, given a depth, returns a tool
                                     (or description) for that depth.
        :param capability_evaluator: Callable that evaluates the capability score
                                     of a given tool.
        """
        self.current_depth = 1
        self.prev_capability_score = 0.0
        self.tool_builder = initial_tool_builder
        self.capability_evaluator = capability_evaluator
        self.history = []  # Records (depth, capability_score)

    def run(self):
        """
        Run the recursive improvement loop until convergence, safety violation,
        or the maximum allowed depth is reached.
        """
        while depth_allowed(self.current_depth):
            logger.info(f"=== Starting recursion depth {self.current_depth} ===")
            tool = self._build_tool_for_current_depth()
            capability_score = self._evaluate_tool(tool)

            # Record the outcome
            self.history.append((self.current_depth, capability_score))
            logger.info(
                f"Depth {self.current_depth} capability score: {capability_score:.4f}"
            )

            # Safety check: ensure improvement is sufficient
            if not improvement_safe(self.prev_capability_score, capability_score):
                logger.warning(
                    f"Improvement below safety threshold at depth {self.current_depth}. "
                    "Halting recursion."
                )
                break

            # Convergence detection: if improvement is negligible, stop.
            if self._has_converged(self.prev_capability_score, capability_score):
                logger.info(
                    f"Convergence detected at depth {self.current_depth}. "
                    "No significant further gains."
                )
                break

            # Prepare for next depth
            self.prev_capability_score = capability_score
            self.current_depth += 1

        logger.info("Recursive improvement process completed.")
        return self.history

    def _build_tool_for_current_depth(self) -> Any:
        """
        Invokes the provided tool builder to construct a tool for the current depth.
        The builder is expected to understand the depth argument and return a
        representation of the newly created tool (e.g., a function, model spec, etc.).
        """
        try:
            tool = self.tool_builder(self.current_depth)
            logger.debug(f"Built tool at depth {self.current_depth}: {tool}")
            return tool
        except Exception as e:
            logger.exception(
                f"Tool building failed at depth {self.current_depth}: {e}"
            )
            raise

    def _evaluate_tool(self, tool: Any) -> float:
        """
        Uses the capability evaluator to obtain a numeric score representing the
        tool's performance/utility. Higher scores indicate better capability.
        """
        try:
            score = self.capability_evaluator(tool)
            logger.debug(
                f"Capability evaluation for depth {self.current_depth}: {score}"
            )
            return score
        except Exception as e:
            logger.exception(
                f"Capability evaluation failed at depth {self.current_depth}: {e}"
            )
            raise

    @staticmethod
    def _has_converged(prev_score: float, new_score: float, epsilon: float = 1e-3) -> bool:
        """
        Determines convergence based on absolute change being smaller than epsilon.
        """
        return abs(new_score - prev_score) < epsilon
import logging
from safety.recursion_bounds import MAX_DEPTH, check_depth

class RecursiveImprovementEngine:
    """
    Core engine that drives recursive self‑improvement across multiple
    abstraction layers (depths).  Each depth represents a “tool that builds
    tools” level.  The engine tracks depth, measures a placeholder capability,
    and stops when the safety‑defined maximum depth is reached or convergence
    is detected.
    """

    def __init__(self):
        self.current_depth: int = 1
        self.capability_log: dict[int, float] = {}

    # --------------------------------------------------------------------- #
    # Capability measurement (stub – replace with real evaluation metrics)
    # --------------------------------------------------------------------- #
    def _measure_capability(self) -> float:
        """
        Placeholder capability evaluator.
        In a real system this would run benchmarks, cost‑benefit analysis,
        or other performance metrics.  Here we simply return a value that
        grows with depth to illustrate improvement.
        """
        return self.current_depth * 10.0

    # --------------------------------------------------------------------- #
    # Core recursive improvement loop
    # --------------------------------------------------------------------- #
    def run(self):
        """
        Execute recursive improvement from the current depth up to
        MAX_DEPTH, respecting safety checks and logging progress.
        """
        while True:
            if not check_depth(self.current_depth):
                logging.warning(
                    f"Depth {self.current_depth} out of safe bounds; aborting."
                )
                break

            logging.info(f"=== Starting improvement at depth {self.current_depth} ===")
            capability = self._measure_capability()
            self.capability_log[self.current_depth] = capability
            logging.info(
                f"Depth {self.current_depth} capability measured: {capability}"
            )

            if self.current_depth >= MAX_DEPTH:
                logging.info("Reached maximum safe recursion depth.")
                break

            # Simulate construction of the next‑level meta‑tool.
            self._build_next_level_tool()
            self.current_depth += 1

    def _build_next_level_tool(self):
        """
        Stub for the meta‑tool construction logic.
        In practice this would invoke AutoML/NAS, meta‑learning, or
        self‑play curricula to generate the next abstraction layer.
        """
        logging.debug(
            f"Building meta‑tool for depth {self.current_depth + 1}"
        )

    # --------------------------------------------------------------------- #
    # Reporting utilities
    # --------------------------------------------------------------------- #
    def report(self) -> str:
        """Generate a human‑readable report of capability across depths."""
        lines = ["Recursive Self‑Improvement Report:"]
        for depth in sorted(self.capability_log):
            lines.append(
                f"Depth {depth}: Capability = {self.capability_log[depth]}"
            )
        return "\n".join(lines)
\"\"\"recursive_improvement_engine.py
----------------------------------

Core engine that orchestrates recursive self‑improvement across multiple
depths. It tracks the current depth, invokes the appropriate builder tool,
measures capability gains, and enforces safety bounds defined in
`safety.recursion_bounds`.

Depth hierarchy (example):
    Depth 1: atomizer.py
    Depth 2: task_builder.py
    Depth 3: meta_builder.py
    Depth 4: architecture_evolver.py
\"\"\"

from importlib import import_module
from typing import Callable, Any, Tuple

# Safety utilities
from safety.recursion_bounds import safety_check, MAX_DEPTH

# Simple capability logger – in a real system this would query
# performance metrics, benchmark suites, etc.
def measure_capability(state: Any) -> float:
    \"\"\"Return a scalar representing the system's capability.

    The placeholder implementation assumes `state` provides a `score`
    attribute. Replace with domain‑specific measurement logic.
    \"\"\"
    return getattr(state, "score", 0.0)

class RecursiveImprovementEngine:
    \"\"\"Engine to perform recursive self‑improvement up to a safe depth.\"

    def __init__(self):
        self.current_depth = 1
        self.last_capability = 0.0
        self.history = []  # Records (depth, capability, improvement)

    def _builder_module_name(self, depth: int) -> str:
        \"\"\"Map a recursion depth to its corresponding builder module name.\"\"\"
        mapping = {
            1: "atomizer",
            2: "task_builder",
            3: "meta_builder",
            4: "architecture_evolver",
        }
        return mapping.get(depth, "")

    def _load_builder(self, depth: int) -> Callable[[Any], Any]:
        \"\"\"Dynamically import the builder for the given depth and return its `improve` function.\"

        module_name = self._builder_module_name(depth)
        if not module_name:
            raise ValueError(f"No builder defined for depth {depth}")

        module = import_module(module_name)
        if not hasattr(module, "improve"):
            raise AttributeError(f"Module '{module_name}' must expose an `improve(state)` function")
        return getattr(module, "improve")

    def _run_step(self, state: Any) -> Tuple[Any, float]:
        \"\"\"Execute a single improvement step and return the new state and relative improvement.\"\"\"
        improve_fn = self._load_builder(self.current_depth)
        new_state = improve_fn(state)

        new_capability = measure_capability(new_state)
        improvement = (
            (new_capability - self.last_capability) / self.last_capability
            if self.last_capability > 0 else new_capability
        )
        return new_state, improvement

    def run(self, initial_state: Any) -> Any:
        \"\"\"Run recursive improvement until convergence, safety limit, or max depth.\"

        state = initial_state
        self.last_capability = measure_capability(state)

        while True:
            # Execute improvement at the current depth
            state, improvement = self._run_step(state)

            # Log the result
            self.history.append((self.current_depth, measure_capability(state), improvement))

            # Safety & convergence checks
            if not safety_check(self.current_depth, improvement):
                # Either reached max depth or improvement too small
                break

            # Prepare for next recursion level
            self.current_depth += 1
            self.last_capability = measure_capability(state)

        return state

    def report(self) -> str:
        \"\"\"Generate a human‑readable report of the recursive run.\"\"\"
        lines = ["Recursive Self‑Improvement Report", "=" * 35]
        for depth, capability, improvement in self.history:
            lines.append(
                f"Depth {depth}: Capability={capability:.4f}, "
                f"Improvement={improvement * 100:.2f}%"
            )
        lines.append(f"Final depth reached: {self.current_depth}")
        lines.append(f"Safety max depth limit: {MAX_DEPTH}")
        return "\n".join(lines)
"""
Recursive Self‑Improvement Engine
---------------------------------

This module implements a lightweight recursive improvement loop that
coordinates the existing tool‑building components (atomizer, task_builder,
meta_builder, architecture_evolver) and tracks improvement depth,
capability gains, convergence, and safety bounds.

Depth mapping (example):
    1 → atomizer.py          – builds low‑level tasks
    2 → task_builder.py      – improves atomizer
    3 → meta_builder.py      – improves task_builder
    4 → architecture_evolver.py – improves meta_builder

The engine can be imported and invoked from a higher‑level orchestrator
or used in experimental notebooks.
"""

import importlib
import logging
from typing import Any, Callable, Dict

from safety.recursion_bounds import check_depth, RecursionSafetyError, MIN_IMPROVEMENT_DELTA

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RecursiveImprovementEngine:
    """
    Core engine that runs recursive self‑improvement up to a configurable depth.
    """

    # Mapping from depth level to the module that implements that level's improvement.
    DEPTH_MODULE_MAP: Dict[int, str] = {
        1: "atomizer",
        2: "task_builder",
        3: "meta_builder",
        4: "architecture_evolver",
    }

    def __init__(self, max_depth: int = 4):
        """
        Initialise the engine.

        Args:
            max_depth: Upper bound on recursion depth (must respect safety limits).
        """
        self.max_depth = max_depth
        self.current_depth = 0
        self.last_capability_score = 0.0

        # Validate safety constraints at construction time.
        try:
            check_depth(self.max_depth)
        except RecursionSafetyError as e:
            logger.error("Safety check failed during engine initialisation: %s", e)
            raise

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def run(self) -> None:
        """
        Execute the recursive improvement loop until convergence or the
        maximum safe depth is reached.
        """
        logger.info("Starting recursive self‑improvement (max depth = %d)", self.max_depth)

        while self.current_depth < self.max_depth:
            self.current_depth += 1
            logger.info("=== Depth %d ===", self.current_depth)

            # Safety guard – ensure we never exceed the global safe limit.
            try:
                check_depth(self.current_depth)
            except RecursionSafetyError as e:
                logger.error("Safety violation at depth %d: %s", self.current_depth, e)
                break

            # Execute the improvement stage for the current depth.
            improvement_successful = self._execute_stage(self.current_depth)

            # Measure capability after this stage.
            new_score = self._measure_capability()
            delta = new_score - self.last_capability_score
            logger.info(
                "Capability score: %.6f (Δ = %.6f)", new_score, delta
            )

            # Determine convergence.
            if not improvement_successful:
                logger.warning(
                    "Improvement stage at depth %d reported failure – stopping recursion.",
                    self.current_depth,
                )
                break

            if delta < MIN_IMPROVEMENT_DELTA:
                logger.info(
                    "Improvement delta %.6f below threshold %.6f – convergence reached.",
                    delta,
                    MIN_IMPROVEMENT_DELTA,
                )
                break

            self.last_capability_score = new_score

        logger.info("Recursive improvement terminated at depth %d.", self.current_depth)

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _execute_stage(self, depth: int) -> bool:
        """
        Dynamically load and run the module responsible for the given depth.

        The target module must expose a callable named ``run_improvement`` that
        returns ``True`` on success and ``False`` otherwise.

        Args:
            depth: Current recursion depth (1‑based).

        Returns:
            bool: ``True`` if the stage completed successfully.
        """
        module_name = self.DEPTH_MODULE_MAP.get(depth)
        if not module_name:
            logger.error("No module mapped for depth %d.", depth)
            return False

        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            logger.error("Failed to import module '%s' for depth %d: %s", module_name, depth, e)
            return False

        run_fn: Callable[[], Any] = getattr(module, "run_improvement", None)
        if not callable(run_fn):
            logger.error(
                "Module '%s' does not define a callable 'run_improvement' for depth %d.",
                module_name,
                depth,
            )
            return False

        logger.info("Running improvement stage via %s.run_improvement()", module_name)
        try:
            result = run_fn()
            if isinstance(result, bool):
                return result
            # If the function returns a non‑bool, treat truthiness as success.
            return bool(result)
        except Exception as e:
            logger.exception(
                "Exception raised during improvement stage in module '%s': %s", module_name, e
            )
            return False

    def _measure_capability(self) -> float:
        """
        Placeholder capability measurement.

        In a production system this would query a benchmark suite,
        evaluate task performance, or compute a learned utility metric.
        For now we return a simple monotonic counter based on depth.

        Returns:
            float: Simulated capability score.
        """
        # Simple deterministic proxy: each depth adds a diminishing return.
        base = 1.0
        decay = 0.5
        score = base * (1 - decay ** self.current_depth) / (1 - decay)
        return score
\"\"\"recursive_improvement_engine
================================

Implements a lightweight recursive self‑improvement (RSI) engine
that tracks improvement depth, builds meta‑tools, measures capability,
and respects safety bounds defined in ``safety.recursion_bounds``.
\"\"\"

from __future__ import annotations
from typing import Any, Dict, List, Callable
import logging
import time

# Safety utilities
from safety.recursion_bounds import (
    enforce_depth_limit,
    has_converged,
    MAX_RECURSION_DEPTH,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RecursiveImprovementEngine:
    \"\"\"Core engine for recursive self‑improvement up to a configurable depth.\n\n    The engine is deliberately modular so that each *depth* can be\n    associated with a concrete tool (e.g., ``atomizer.py`` at depth‑1,\n    ``task_builder.py`` at depth‑2, etc.).  The implementation below\n    provides the scaffolding; concrete tool implementations can be\n    plugged in via the ``tool_registry`` mapping.\n    \"\"\"

    def __init__(self, start_depth: int = 1):
        self.current_depth: int = start_depth
        self.capability_history: List[float] = []   # Simple scalar capability metric
        self.improvement_history: List[float] = []  # Fractional improvement per step
        self.tool_registry: Dict[int, Callable[[], Any]] = {}
        self._register_builtin_tools()

    # --------------------------------------------------------------------- #
    # Tool registration
    # --------------------------------------------------------------------- #
    def _register_builtin_tools(self):
        \"\"\"Register placeholder tool factories for each depth.\n\n        In a full system these would import the actual modules\n        (e.g., ``atomizer``, ``task_builder``).  Here we provide simple\n        stubs that simulate work and return a dummy capability value.\n        \"\"\"
        self.tool_registry = {
            1: self._atomizer_stub,
            2: self._task_builder_stub,
            3: self._meta_builder_stub,
            4: self._architecture_evolver_stub,
        }

    # --------------------------------------------------------------------- #
    # Stub implementations (to be replaced by real tools later)
    # --------------------------------------------------------------------- #
    def _atomizer_stub(self) -> float:
        time.sleep(0.1)  # simulate work
        return 1.0  # baseline capability

    def _task_builder_stub(self) -> float:
        time.sleep(0.1)
        # modest improvement over depth‑1
        return self.capability_history[-1] * 1.2

    def _meta_builder_stub(self) -> float:
        time.sleep(0.1)
        return self.capability_history[-1] * 1.35

    def _architecture_evolver_stub(self) -> float:
        time.sleep(0.1)
        return self.capability_history[-1] * 1.5

    # --------------------------------------------------------------------- #
    # Core recursion logic
    # --------------------------------------------------------------------- #
    def run(self):
        \"\"\"Execute recursive improvement until convergence or depth limit.\n\n        The loop performs:\n        1. Safety depth check.\n        2. Invocation of the tool associated with the current depth.\n        3. Capability measurement.\n        4. Convergence detection.\n        5. Depth increment.\n        \"\"\"
        logger.info(\"Starting Recursive Self‑Improvement Engine (max depth %d)\", MAX_RECURSION_DEPTH)

        while True:
            enforce_depth_limit(self.current_depth)

            logger.info(\"--- Depth %d ---\", self.current_depth)
            tool = self.tool_registry.get(self.current_depth)
            if tool is None:
                raise RuntimeError(f\"No tool registered for depth {self.current_depth}\")

            # Run the tool and obtain a new capability metric
            new_capability = tool()
            self.capability_history.append(new_capability)
            logger.info(\"Capability after depth %d: %.4f\", self.current_depth, new_capability)

            # Compute improvement fraction if we have a previous value
            if len(self.capability_history) > 1:
                prev = self.capability_history[-2]
                improvement = (new_capability - prev) / prev
                self.improvement_history.append(improvement)
                logger.info(
                    \"Improvement fraction at depth %d: %.4f\", self.current_depth, improvement
                )
                if has_converged(improvement):
                    logger.info(
                        \"Convergence detected (improvement %.4f < %.4f). Stopping.\",
                        improvement,
                        MIN_IMPROVEMENT_FRACTION,
                    )
                    break

            # Stop if we have reached the maximum allowed depth
            if self.current_depth >= MAX_RECURSION_DEPTH:
                logger.info(\"Reached maximum recursion depth (%d).\", MAX_RECURSION_DEPTH)
                break

            # Prepare for next depth
            self.current_depth += 1

        logger.info(\"Recursive improvement completed. Final capability: %.4f\", self.capability_history[-1])
        return {
            \"final_depth\": self.current_depth,
            \"final_capability\": self.capability_history[-1],
            \"capability_history\": self.capability_history,
            \"improvement_history\": self.improvement_history,
        }

# ------------------------------------------------------------------------- #
# Helper: simple capability measurement (placeholder)
# ------------------------------------------------------------------------- #
def measure_capability(dummy_output: Any) -> float:
    \"\"\"Placeholder for a real capability measurement routine.\n\n    In practice this could run benchmark suites, evaluate task\n    performance, or query external metrics.  Here we simply assume the\n    tool returns a float representing capability.\n    \"\"\"
    if isinstance(dummy_output, (int, float)):
        return float(dummy_output)
    raise TypeError(\"Capability measurement expects a numeric output\")

# ------------------------------------------------------------------------- #
# If executed as a script, run a quick demo
# ------------------------------------------------------------------------- #
if __name__ == \"__main__\":
    engine = RecursiveImprovementEngine()
    results = engine.run()
    print(\"RSI Results:\", results)
import time
import logging
import random
from typing import Callable, List

# Import safety bounds (will be created below)
try:
    from safety.recursion_bounds import safety_check, MAX_RECURSION_DEPTH
except ImportError:
    # Fallback values if safety module is not yet present
    MAX_RECURSION_DEPTH = 4
    def safety_check(depth: int) -> bool:
        return depth <= MAX_RECURSION_DEPTH

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

class RecursiveImprovementEngine:
    """
    Engine that orchestrates recursive self‑improvement across multiple depths.
    Each depth runs a *builder* callable that returns a new callable representing
    the improved tool for the next depth.
    """

    def __init__(self,
                 initial_builder: Callable[[], Callable],
                 max_depth: int = MAX_RECURSION_DEPTH,
                 improvement_threshold: float = 0.01,
                 safety_fn: Callable[[int], bool] = safety_check):
        """
        :param initial_builder: Callable that creates the depth‑1 tool (e.g., atomizer).
        :param max_depth: Upper bound on recursion depth (safety guard).
        :param improvement_threshold: Minimum relative gain required to continue recursing.
        :param safety_fn: Function that returns True if the given depth is allowed.
        """
        self.current_builder = initial_builder
        self.max_depth = max_depth
        self.improvement_threshold = improvement_threshold
        self.safety_fn = safety_fn
        self.depth = 0
        self.history: List[dict] = []

    def _measure_capability(self, tool_callable: Callable) -> float:
        """
        Placeholder capability measurement.
        In a real system this would run benchmarks, cost analysis, etc.
        Here we simulate with a random score that slightly improves each call.
        """
        base = random.uniform(0.5, 0.7)
        # Simulate that deeper tools are a bit better
        score = base + 0.05 * self.depth
        logger.debug(f"Measured capability at depth {self.depth}: {score:.4f}")
        return score

    def run(self):
        """
        Execute recursive improvement until convergence, safety limit, or max depth.
        """
        logger.info("Starting recursive self‑improvement loop.")
        previous_score = None

        while self.depth < self.max_depth:
            self.depth += 1
            logger.info(f"=== Depth {self.depth} ===")

            if not self.safety_fn(self.depth):
                logger.warning(f"Safety check failed at depth {self.depth}. Halting recursion.")
                break

            # Build the tool for this depth
            tool = self.current_builder()
            logger.info(f"Built tool at depth {self.depth}: {tool}")

            # Measure its capability
            current_score = self._measure_capability(tool)
            logger.info(f"Capability score at depth {self.depth}: {current_score:.4f}")

            # Record history
            self.history.append({
                "depth": self.depth,
                "tool": tool,
                "score": current_score,
                "timestamp": time.time()
            })

            # Check for convergence
            if previous_score is not None:
                relative_gain = (current_score - previous_score) / previous_score
                logger.info(f"Relative gain from depth {self.depth-1} to {self.depth}: {relative_gain:.4%}")
                if relative_gain < self.improvement_threshold:
                    logger.info("Improvement below threshold; convergence reached.")
                    break

            previous_score = current_score

            # Prepare builder for next depth (meta‑tool that builds the next tool)
            # For demonstration we wrap the current tool in a simple lambda.
            # Real implementations would invoke AutoML / NAS / meta‑learning here.
            def next_builder(prev_tool=tool):
                def improved_tool(*args, **kwargs):
                    # Placeholder: call previous tool then apply a tiny stochastic improvement
                    result = prev_tool(*args, **kwargs) if callable(prev_tool) else None
                    # Simulate improvement
                    return result
                return improved_tool
            self.current_builder = next_builder

        logger.info("Recursive improvement loop completed.")
        return self.history
import logging
from typing import Any, Dict

# Local safety module
from safety.recursion_bounds import is_safe_depth, MAX_DEPTH

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RecursiveImprovementEngine:
    """
    Core engine that orchestrates recursive self‑improvement.
    It tracks the current depth, invokes the appropriate builder,
    measures capability gains, and checks safety/convergence.
    """

    def __init__(self):
        self.current_depth: int = 1
        self.capability_history: Dict[int, float] = {}
        self.max_depth: int = MAX_DEPTH

    def run(self) -> None:
        """
        Execute the recursive improvement loop until convergence,
        safety bound, or the configured maximum depth is reached.
        """
        logger.info("Starting recursive self‑improvement (max depth=%d)", self.max_depth)
        while self.current_depth <= self.max_depth:
            if not is_safe_depth(self.current_depth):
                logger.warning("Safety bound violated at depth %d – aborting.", self.current_depth)
                break

            logger.info("=== Depth %d ===", self.current_depth)
            self._build_tool_at_current_depth()
            capability = self._measure_capability()
            self.capability_history[self.current_depth] = capability
            logger.info("Capability at depth %d: %.4f", self.current_depth, capability)

            if self._has_converged():
                logger.info("Convergence detected at depth %d – stopping recursion.", self.current_depth)
                break

            self.current_depth += 1

        logger.info("Recursive improvement finished. History: %s", self.capability_history)

    # --------------------------------------------------------------------- #
    # Implementation details – can be replaced with real builders later
    # --------------------------------------------------------------------- #
    def _build_tool_at_current_depth(self) -> None:
        """
        Dispatch to the appropriate builder based on depth.
        Currently these are placeholder stubs that log actions.
        """
        builder_map = {
            1: self._atomizer_builder,
            2: self._task_builder,
            3: self._meta_builder,
            4: self._architecture_evolver,
        }
        builder = builder_map.get(self.current_depth, self._noop_builder)
        builder()

    def _atomizer_builder(self) -> None:
        logger.info("[Depth 1] Atomizer builds tasks – simulated improvement.")

    def _task_builder(self) -> None:
        logger.info("[Depth 2] Task builder refines atomizer – simulated improvement.")

    def _meta_builder(self) -> None:
        logger.info("[Depth 3] Meta‑builder creates new task‑builder variants – simulated improvement.")

    def _architecture_evolver(self) -> None:
        logger.info("[Depth 4] Architecture evolver generates meta‑builder upgrades – simulated improvement.")

    def _noop_builder(self) -> None:
        logger.info("[Depth %d] No builder defined – noop.", self.current_depth)

    # --------------------------------------------------------------------- #
    # Capability measurement & convergence detection (simplified)
    # --------------------------------------------------------------------- #
    def _measure_capability(self) -> float:
        """
        Dummy capability metric: exponential growth with depth.
        Replace with real evaluation (e.g., benchmark scores) later.
        """
        base = 1.0
        growth_factor = 1.5
        return base * (growth_factor ** self.current_depth)

    def _has_converged(self) -> bool:
        """
        Simple convergence check: stop if improvement < 5% over previous depth.
        """
        if self.current_depth == 1:
            return False
        prev = self.capability_history[self.current_depth - 1]
        curr = self.capability_history[self.current_depth]
        improvement = (curr - prev) / prev
        logger.debug("Improvement from depth %d to %d: %.2f%%", self.current_depth - 1, self.current_depth, improvement * 100)
        return improvement < 0.05

# --------------------------------------------------------------------- #
# Entry‑point for manual execution
# --------------------------------------------------------------------- #
if __name__ == "__main__":
    engine = RecursiveImprovementEngine()
    engine.run()
import logging
from typing import Callable, Any, Dict

from safety.recursion_bounds import MAX_DEPTH, check_depth_allowed

logger = logging.getLogger(__name__)

class RecursiveImprovementEngine:
    """
    Core engine that orchestrates recursive self‑improvement across multiple
    abstraction layers (depths). Each depth is expected to expose a *builder*
    callable that knows how to improve the component from the previous depth.
    """

    def __init__(self):
        # Mapping depth -> builder callable
        self.builders: Dict[int, Callable[[Any], Any]] = {}
        # Track the current best artifact at each depth
        self.artifacts: Dict[int, Any] = {}
        # Depth we are currently evaluating
        self.current_depth: int = 1

    # --------------------------------------------------------------------- #
    # Builder registration
    # --------------------------------------------------------------------- #
    def register_builder(self, depth: int, builder: Callable[[Any], Any]) -> None:
        """
        Register a builder function for a specific depth.
        The builder receives the artifact from the previous depth and returns
        an improved artifact.
        """
        if depth < 1:
            raise ValueError("Depth must be >= 1")
        if depth > MAX_DEPTH:
            raise ValueError(f"Depth exceeds safety bound of {MAX_DEPTH}")
        self.builders[depth] = builder
        logger.debug(f"Registered builder for depth {depth}")

    # --------------------------------------------------------------------- #
    # Execution loop
    # --------------------------------------------------------------------- #
    def run(self, initial_artifact: Any) -> Any:
        """
        Run the recursive improvement loop starting from depth 1 up to the
        configured safety bound or until convergence is detected.
        """
        self.artifacts[0] = initial_artifact
        logger.info("Starting recursive self‑improvement loop")

        while self.current_depth <= MAX_DEPTH:
            check_depth_allowed(self.current_depth)

            builder = self.builders.get(self.current_depth)
            if not builder:
                logger.warning(f"No builder registered for depth {self.current_depth}; stopping.")
                break

            prev_artifact = self.artifacts[self.current_depth - 1]
            logger.info(f"Running builder at depth {self.current_depth}")
            new_artifact = builder(prev_artifact)

            self.artifacts[self.current_depth] = new_artifact

            if self._has_converged(self.current_depth):
                logger.info(f"Convergence detected at depth {self.current_depth}")
                break

            self.current_depth += 1

        final_depth = self.current_depth
        logger.info(f"Recursive improvement finished at depth {final_depth}")
        return self.artifacts[final_depth]

    # --------------------------------------------------------------------- #
    # Convergence detection (simple heuristic)
    # --------------------------------------------------------------------- #
    def _has_converged(self, depth: int) -> bool:
        """
        Determine whether improvement has plateaued. By default we compare
        a naive numeric metric if the artifact supports it, otherwise we
        assume no convergence.
        """
        prev = self.artifacts.get(depth - 1)
        curr = self.artifacts.get(depth)

        # If artifacts expose a 'score' attribute, use it.
        if hasattr(prev, "score") and hasattr(curr, "score"):
            improvement = curr.score - prev.score
            logger.debug(f"Depth {depth} improvement: {improvement}")
            return improvement <= 0  # no positive gain => converged

        # Fallback: no convergence detection
        return False
# recursive_improvement_engine.py
"""
Recursive Self‑Improvement Engine
Tracks improvement depth, builds meta‑tools, detects convergence,
and respects safety bounds.
"""

from typing import Any, Callable
import logging

# Import safety bounds
from safety.recursion_bounds import check_depth, MAX_RECURSION_DEPTH

# Import builder modules – they may not exist yet; guard import.
try:
    import atomizer
except ImportError:
    atomizer = None

try:
    import task_builder
except ImportError:
    task_builder = None

try:
    import meta_builder
except ImportError:
    meta_builder = None

try:
    import architecture_evolver
except ImportError:
    architecture_evolver = None


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RecursiveImprovementEngine:
    def __init__(self, start_depth: int = 1, improvement_threshold: float = 0.01):
        """
        :param start_depth: Depth at which the engine starts (normally 1).
        :param improvement_threshold: Minimum relative improvement required to continue recursion.
        """
        self.current_depth = start_depth
        self.improvement_threshold = improvement_threshold
        self.last_performance: float = 0.0

    def measure_performance(self) -> float:
        """
        Placeholder for a real capability measurement.
        Returns a float where higher is better.
        """
        # In a real system this would evaluate the current toolset on benchmark tasks.
        # Here we simulate a modest improvement per depth.
        simulated = 1.0 + 0.2 * self.current_depth
        logger.debug(f"Measured performance at depth {self.current_depth}: {simulated}")
        return simulated

    def run_step(self) -> None:
        """
        Execute one improvement step appropriate for the current depth.
        """
        check_depth(self.current_depth)

        logger.info(f"=== Recursion Depth {self.current_depth} ===")
        if self.current_depth == 1 and atomizer:
            logger.info("Running atomizer improvements.")
            atomizer.improve()
        elif self.current_depth == 2 and task_builder:
            logger.info("Running task_builder improvements.")
            task_builder.improve()
        elif self.current_depth == 3 and meta_builder:
            logger.info("Running meta_builder improvements.")
            meta_builder.improve()
        elif self.current_depth == 4 and architecture_evolver:
            logger.info("Running architecture_evolver improvements.")
            architecture_evolver.improve()
        else:
            logger.warning(
                f"No improvement module available for depth {self.current_depth}."
            )

    def has_converged(self, new_perf: float) -> bool:
        """
        Determine if improvement is below the threshold.
        """
        if self.last_performance == 0.0:
            return False
        relative_gain = (new_perf - self.last_performance) / self.last_performance
        logger.debug(
            f"Relative gain from depth {self.current_depth-1} to {self.current_depth}: {relative_gain}"
        )
        return relative_gain < self.improvement_threshold

    def run(self) -> None:
        """
        Drive recursive self‑improvement until convergence or safety limit.
        """
        while self.current_depth <= MAX_RECURSION_DEPTH:
            self.run_step()
            new_perf = self.measure_performance()
            if self.has_converged(new_perf):
                logger.info(
                    f"Convergence detected at depth {self.current_depth}. Stopping recursion."
                )
                break
            self.last_performance = new_perf
            self.current_depth += 1

        logger.info("Recursive improvement process completed.")


if __name__ == "__main__":
    engine = RecursiveImprovementEngine()
    engine.run()