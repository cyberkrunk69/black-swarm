import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, Any

# Configure basic logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]  # /app
INDEX_PATH = BASE_DIR / "research_index.json"
CACHE_PATH = BASE_DIR / "cache" / "research_index_cache.json"

# Ensure cache directory exists
CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Dict[str, Any]:
    """Safely load a JSON file."""
    if not path.is_file():
        logging.warning(f"File not found: {path}")
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from {path}: {e}")
        return {}


def save_json(data: Dict[str, Any], path: Path) -> None:
    """Write JSON data to a file."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_insights(index_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for insight extraction logic.
    Currently performs a shallow copy; replace with domain‑specific processing.
    """
    # Example: keep only entries that have a non‑empty "insight" field
    insights = {
        key: value
        for key, value in index_data.items()
        if isinstance(value, dict) and value.get("insight")
    }
    return insights


def reindex() -> None:
    """Re‑index the research data and cache new insights."""
    logging.info("Starting re‑indexing cycle.")
    raw_index = load_json(INDEX_PATH)
    if not raw_index:
        logging.warning("Empty or missing research index; skipping cycle.")
        return

    new_insights = extract_insights(raw_index)

    # Load previous cache to detect changes
    cached_insights = load_json(CACHE_PATH)

    # Simple diff: if new insights differ from cached, update cache and log
    if new_insights != cached_insights:
        logging.info("New insights detected; updating cache.")
        save_json(new_insights, CACHE_PATH)
        # Hook for downstream meta‑learning components:
        # e.g., trigger_model_update(new_insights)
    else:
        logging.info("No new insights found; cache is up‑to‑date.")


def meta_learning_loop(interval_seconds: int = 300) -> None:
    """
    Periodic loop that re‑indexes the research index.
    :param interval_seconds: How often to run the re‑index (default: 5 minutes).
    """
    logging.info(f"Meta‑learning loop started; interval={interval_seconds}s.")
    try:
        while True:
            start = time.time()
            reindex()
            elapsed = time.time() - start
            sleep_time = max(0, interval_seconds - elapsed)
            logging.debug(f"Cycle completed in {elapsed:.2f}s; sleeping {sleep_time:.2f}s.")
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        logging.info("Meta‑learning loop terminated by user.")
    except Exception as exc:
        logging.exception(f"Unexpected error in meta‑learning loop: {exc}")


if __name__ == "__main__":
    # Default interval can be overridden via environment variable
    interval = int(os.getenv("META_LEARNING_INTERVAL", "300"))
    meta_learning_loop(interval_seconds=interval)