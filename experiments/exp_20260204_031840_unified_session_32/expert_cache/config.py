"""
Configuration constants for the Expert Knowledge Cache system.
"""

# ----------------------------------------------------------------------
# Persistent cache (project‑level) location
# ----------------------------------------------------------------------
PROJECT_CACHE_PATH = "/app/experiments/exp_20260204_031840_unified_session_32/expert_cache/project_cache.db"

# ----------------------------------------------------------------------
# In‑memory session cache limits
# ----------------------------------------------------------------------
SESSION_CACHE_MAX_ITEMS = 10_000          # Maximum number of entries kept in RAM
SESSION_CACHE_PRUNE_BATCH = 500          # Number of items examined when pruning

# ----------------------------------------------------------------------
# Embedding model (placeholder – replace with actual model at runtime)
# ----------------------------------------------------------------------
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# ----------------------------------------------------------------------
# LRU / frequency weighting parameters
# ----------------------------------------------------------------------
LRU_DECAY_FACTOR = 0.9   # How quickly access counts decay during pruning
LRU_MIN_FREQUENCY = 1    # Minimum frequency count to keep an entry alive