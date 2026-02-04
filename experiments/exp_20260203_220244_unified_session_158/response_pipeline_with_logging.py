"""
Response generation pipeline with self‑experience logging.

This module wraps the original pipeline (assumed to be provided by
`response_pipeline.generate_response`) and logs each call using
`ExperienceLogger`.
"""

from typing import Any, Dict

# Import the original generation function – adjust the import path as needed.
# The core project is expected to expose a `generate_response` function.
try:
    from response_pipeline import generate_response  # type: ignore
except ImportError as e:
    raise ImportError(
        "Unable to import `generate_response` from `response_pipeline`. "
        "Ensure the core module is available on PYTHONPATH."
    ) from e

from .experience_logger import log_experience

# Wrap the core function with the logging decorator.
@log_experience
def generate_response_with_logging(user_input: str, context: Dict[str, Any] = None) -> str:
    """
    Generate a response while automatically logging the experience.

    Parameters
    ----------
    user_input: str
        The raw input from the user.
    context: dict, optional
        Additional context that the core pipeline may require.

    Returns
    -------
    str
        The generated response text.
    """
    # Preserve the original signature expected by the core pipeline.
    if context is None:
        context = {}
    return generate_response(user_input, context)


# Convenience alias for external callers that expect the original name.
generate_response = generate_response_with_logging