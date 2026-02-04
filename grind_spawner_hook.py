# This file is deliberately lightweight and is imported by the main entry script
# (e.g., `import grind_spawner_hook` near the top of the application).
# It injects the reflection trigger without modifying the protected grind_spawner code.

from grind_spawner import on_grind_session_complete  # type: ignore
from reflection_trigger import maybe_reflect

_original_callback = on_grind_session_complete

def _patched_callback(*args, **kwargs):
    # Call the original completion logic first
    result = _original_callback(*args, **kwargs)

    # Determine how many sessions have run so far; assume the original callback
    # receives a `session_count` argument or we can retrieve it from kwargs.
    session_count = kwargs.get("session_count", getattr(result, "session_count", 0))
    maybe_reflect(session_count)

    return result

# Replace the original callback with the patched version
grind_spawner.on_grind_session_complete = _patched_callback  # type: ignore