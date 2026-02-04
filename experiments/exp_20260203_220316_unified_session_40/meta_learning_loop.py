import json
import time
import threading
from pathlib import Path
from typing import Any, Dict, List

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
RESEARCH_INDEX_PATH = Path("research_index.json")
REINDEX_INTERVAL_SECONDS = 300  # 5 minutes; adjust as needed
OUTPUT_INDEX_PATH = Path("research_index_enhanced.json")

# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------
def load_index(path: Path) -> List[Dict[str, Any]]:
    """Load the research index JSON file."""
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_index(data: List[Dict[str, Any]], path: Path) -> None:
    """Write the (potentially enhanced) index back to disk."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_insights(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for a real insight extraction routine.
    For now we simply copy the entry and add a dummy `insights` field.
    """
    insights = {
        "summary": entry.get("title", "")[:150],
        "keywords": [kw.lower() for kw in entry.get("tags", [])],
        # Extend with actual NLP/ML models as needed.
    }
    new_entry = dict(entry)
    new_entry["insights"] = insights
    return new_entry


def reindex() -> None:
    """Re‑index the research data, adding/updating insights."""
    raw_entries = load_index(RESEARCH_INDEX_PATH)
    enhanced_entries = []

    for entry in raw_entries:
        enhanced = extract_insights(entry)
        enhanced_entries.append(enhanced)

    save_index(enhanced_entries, OUTPUT_INDEX_PATH)
    print(f"[Meta‑Learning] Re‑indexed {len(enhanced_entries)} entries at {time.strftime('%Y-%m-%d %H:%M:%S')}")


def periodic_reindex(stop_event: threading.Event) -> None:
    """Background thread that re‑indexes at a fixed interval."""
    while not stop_event.is_set():
        start = time.time()
        try:
            reindex()
        except Exception as exc:
            print(f"[Meta‑Learning] Error during re‑indexing: {exc}")

        # Compute remaining sleep time, respecting the interval.
        elapsed = time.time() - start
        sleep_time = max(0, REINDEX_INTERVAL_SECONDS - elapsed)
        stop_event.wait(sleep_time)


# ----------------------------------------------------------------------
# Entry Point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    stop_flag = threading.Event()
    worker = threading.Thread(target=periodic_reindex, args=(stop_flag,), daemon=True)
    worker.start()
    print("[Meta‑Learning] Background re‑indexer started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Meta‑Learning] Stopping background re‑indexer...")
        stop_flag.set()
        worker.join()
        print("[Meta‑Learning] Stopped.")