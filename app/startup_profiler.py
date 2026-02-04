import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def profile_startup(func):
    """Decorator that logs the execution time of startup‑related functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.debug("Startup step %s took %.3f s", func.__name__, elapsed)
        return result
    return wrapper