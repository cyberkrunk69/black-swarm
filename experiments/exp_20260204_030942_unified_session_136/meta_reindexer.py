import json
import time
import threading
from pathlib import Path
from typing import Any, Dict, List

# Configuration
INDEX_PATH = Path("/app/research_index.json")
REINDEX_INTERVAL_SECONDS = 300  # 5 minutes

# Placeholder for actual indexing logic.
def extract_insights(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process raw research entries and extract insights.
    This function should be replaced with the real meta‑learning logic.
    """
    # Example: simply return entries that contain a non‑empty "insight" field.
    return [entry for entry in data if entry.get("insight")]

def load_index() -> List[Dict[str, Any]]:
    """Load the current research index from JSON."""
    if not INDEX_PATH.is_file():
        return []
    with INDEX_PATH.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_index(updated_data: List[Dict[str, Any]]) -> None:
    """Write the updated index back to disk."""
    with INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)

def reindex() -> None:
    """Re‑index the research data to surface new insights."""
    raw_data = load_index()
    insights = extract_insights(raw_data)

    # Merge insights back into the index (simple example: add a top‑level "insights" key)
    updated_index = {
        "entries": raw_data,
        "insights": insights,
        "last_reindexed": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Save the merged structure
    with INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(updated_index, f, indent=2, ensure_ascii=False)

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Re‑indexing complete. {len(insights)} insights extracted.")

def _periodic_loop(stop_event: threading.Event) -> None:
    """Internal loop that runs reindexing at the configured interval."""
    while not stop_event.is_set():
        start = time.time()
        try:
            reindex()
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Re‑indexing error: {e}")

        # Sleep for the remainder of the interval
        elapsed = time.time() - start
        to_sleep = max(0, REINDEX_INTERVAL_SECONDS - elapsed)
        stop_event.wait(to_sleep)

def start_meta_learning_loop() -> threading.Event:
    """
    Start the background meta‑learning re‑indexing loop.
    Returns an Event that can be set to stop the loop.
    """
    stop_event = threading.Event()
    thread = threading.Thread(target=_periodic_loop, args=(stop_event,), daemon=True)
    thread.start()
    print(f"Meta‑learning re‑indexer started (interval: {REINDEX_INTERVAL_SECONDS}s).")
    return stop_event

if __name__ == "__main__":
    # Run once immediately, then continue looping.
    stop = start_meta_learning_loop()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping meta‑learning re‑indexer...")
        stop.set()