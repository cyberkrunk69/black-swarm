# safety/recursion_bounds.py
# Safety bounds for recursive self‑improvement engine

# Maximum allowed recursion depth to prevent runaway behavior
MAX_RECURSION_DEPTH = 4

# Minimum acceptable improvement ratio between successive depths.
# If the relative improvement falls below this threshold, we consider the process converged.
SAFETY_IMPROVEMENT_THRESHOLD = 0.05  # 5 % improvement

def depth_allowed(current_depth: int) -> bool:
    """
    Returns True if the current recursion depth is within safe limits.
    """
    return current_depth <= MAX_RECURSION_DEPTH

def improvement_safe(prev_score: float, new_score: float) -> bool:
    """
    Checks whether the improvement from prev_score to new_score meets the safety threshold.
    """
    if prev_score == 0:
        # First measurement, always considered safe
        return True
    relative_improvement = (new_score - prev_score) / prev_score
    return relative_improvement >= SAFETY_IMPROVEMENT_THRESHOLD
"""
Safety bounds for recursive self‑improvement.

The maximum allowed recursion depth is deliberately low (4) to keep
experiments controllable while still demonstrating multi‑level bootstrapping.
These constants can be tuned after thorough safety review.
"""

# Maximum safe recursion depth for the experiment
MAX_DEPTH: int = 4

def check_depth(depth: int) -> bool:
    """
    Verify that the requested depth is within the safe operating window.

    Returns:
        True if 1 ≤ depth ≤ MAX_DEPTH, otherwise False.
    """
    return 1 <= depth <= MAX_DEPTH
# Recursion safety bounds for the recursive self‑improvement engine
# ---------------------------------------------------------------
# These parameters define safe limits for the recursive improvement process.
# Adjust with extreme caution – they are critical for preventing runaway
# behavior.

# Maximum allowed recursion depth (inclusive). Depth 4 corresponds to the
# architecture_evolver building improvements to meta_builder, etc.
MAX_DEPTH = 4

# Minimum relative improvement required to consider a recursion step
# successful. If the measured capability gain is below this threshold,
# the engine will treat the process as converged.
MIN_IMPROVEMENT = 0.01  # 1 % improvement

def safety_check(current_depth: int, improvement: float) -> bool:
    """
    Determine whether the recursive improvement step is safe to continue.

    Args:
        current_depth: The depth of the current improvement iteration.
        improvement: Measured relative improvement (e.g., 0.05 for 5 %).

    Returns:
        True if it is safe to proceed to the next depth, False otherwise.
    """
    if current_depth >= MAX_DEPTH:
        # Reached the predefined safe recursion limit.
        return False
    if improvement < MIN_IMPROVEMENT:
        # Improvement too small – treat as convergence.
        return False
    # All safety checks passed.
    return True
# Safety bounds for recursive self‑improvement
# -------------------------------------------------
# These constants and checks are used by the recursive improvement engine
# to ensure it never exceeds a safe recursion depth or proceeds when
# improvements are negligible.

MAX_RECURSION_DEPTH = 4          # Hard limit – never exceed this depth
MIN_IMPROVEMENT_DELTA = 0.001    # Minimum measurable gain required to continue

class RecursionSafetyError(RuntimeError):
    """Raised when a safety bound is violated during recursive improvement."""
    pass

def check_depth(depth: int):
    """
    Verify that the requested recursion depth is within safe limits.

    Args:
        depth: The current recursion depth (1‑based).

    Raises:
        RecursionSafetyError: If ``depth`` exceeds ``MAX_RECURSION_DEPTH``.
    """
    if depth > MAX_RECURSION_DEPTH:
        raise RecursionSafetyError(
            f"Recursion depth {depth} exceeds safe maximum of {MAX_RECURSION_DEPTH}."
        )
```
# Safety bounds for recursive self‑improvement
# -------------------------------------------------
# These constants and helper functions are used by the
# recursive improvement engine to prevent runaway recursion
# and to enforce simple safety limits.

# Maximum allowed recursion depth.  Depth 4 matches the
# target in the task description.
MAX_RECURSION_DEPTH = 4

# Minimal measurable improvement (as a fraction of previous
# capability) before the engine is considered converged.
MIN_IMPROVEMENT_FRACTION = 0.01

def enforce_depth_limit(current_depth: int):
    """
    Raise an exception if the current recursion depth exceeds the
    permitted maximum.
    """
    if current_depth > MAX_RECURSION_DEPTH:
        raise RuntimeError(
            f"Recursion depth {current_depth} exceeds safety limit of "
            f"{MAX_RECURSION_DEPTH}. Halting further self‑improvement."
        )

def has_converged(improvement_fraction: float) -> bool:
    """
    Determine whether the improvement between two consecutive depths
    is below the safety threshold.
    """
    return improvement_fraction < MIN_IMPROVEMENT_FRACTION
import logging

logger = logging.getLogger(__name__)

# Maximum allowed recursion depth – adjustable by operators
MAX_RECURSION_DEPTH = 4

def safety_check(current_depth: int) -> bool:
    """
    Simple safety guard that ensures the recursion does not exceed the
    configured maximum depth. More sophisticated checks (resource limits,
    alignment tests, etc.) can be added here.
    """
    if current_depth > MAX_RECURSION_DEPTH:
        logger.error(f"Depth {current_depth} exceeds safety limit of {MAX_RECURSION_DEPTH}.")
        return False
    return True
"""
Safety utilities for recursive self‑improvement.
Defines hard bounds to prevent runaway recursion and provides
simple checks that can be extended with resource‑budget monitoring.
"""

# Configurable safety limits
MAX_DEPTH: int = 4          # Desired maximum recursion depth
MAX_ITERATIONS: int = 20    # Upper bound on total builder invocations per run

def is_safe_depth(depth: int) -> bool:
    """
    Return True if the requested depth is within the allowed safety limits.
    This function can be expanded to include CPU/GPU budget, timeouts, etc.
    """
    return depth <= MAX_DEPTH

def is_safe_iteration(iteration: int) -> bool:
    """
    Guard against excessive loops inside a single depth level.
    """
    return iteration < MAX_ITERATIONS
"""
Safety utilities for recursive self‑improvement.

We enforce a hard ceiling on recursion depth to avoid runaway
behaviour. The bound can be tuned experimentally; the default is 4,
matching the task requirement.
"""

MAX_DEPTH: int = 4

def check_depth_allowed(depth: int) -> None:
    """
    Raise an exception if the requested depth exceeds the safety bound.
    """
    if depth > MAX_DEPTH:
        raise RuntimeError(
            f"Requested recursion depth {depth} exceeds safety bound of {MAX_DEPTH}. "
            "Aborting to prevent uncontrolled self‑improvement."
        )
# recursion_bounds.py
"""
Safety bounds for recursive self-improvement engine.
Defines maximum recursion depth and simple resource checks.
"""

MAX_RECURSION_DEPTH = 4  # Desired depth limit

def check_depth(depth: int):
    """
    Verify that the requested recursion depth is within safe limits.
    Raises RuntimeError if depth exceeds MAX_RECURSION_DEPTH.
    """
    if depth > MAX_RECURSION_DEPTH:
        raise RuntimeError(
            f"Recursion depth {depth} exceeds safe limit of {MAX_RECURSION_DEPTH}."
        )