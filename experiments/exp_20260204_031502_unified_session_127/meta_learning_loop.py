import json
import time
import threading
from pathlib import Path
from typing import Any, Dict, List

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
RESEARCH_INDEX_PATH = Path("/app/research_index.json")
REFRESH_INTERVAL_SECONDS = 300  # 5 minutes – adjust as needed
INSIGHT_OUTPUT_PATH = Path(
    "/app/experiments/exp_20260204_031502_unified_session_127/insights.json"
)

# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------
def load_research_index() -> List[Dict[str, Any]]:
    """Load the research index JSON file."""
    if not RESEARCH_INDEX_PATH.is_file():
        return []
    with RESEARCH_INDEX_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_insights(insights: List[Dict[str, Any]]) -> None:
    """Persist extracted insights to a JSON file."""
    with INSIGHT_OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)


def extract_insights(index_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Very lightweight insight extraction.
    For demonstration, we treat each entry's ``summary`` field as an insight.
    Real implementations would use LLM calls, clustering, etc.
    """
    insights = []
    for entry in index_entries:
        summary = entry.get("summary")
        if summary:
            insights.append(
                {
                    "id": entry.get("id"),
                    "title": entry.get("title"),
                    "insight": summary,
                }
            )
    return insights


def reindex_loop(stop_event: threading.Event) -> None:
    """
    Periodic loop that reloads the research index, extracts insights,
    and writes them to a dedicated file.
    """
    while not stop_event.is_set():
        try:
            index = load_research_index()
            insights = extract_insights(index)
            save_insights(insights)
            print(
                f"[MetaLearning] Re‑indexed {len(index)} entries, "
                f"generated {len(insights)} insights."
            )
        except Exception as e:
            print(f"[MetaLearning] Error during re-indexing: {e}")

        # Wait for the next interval or early termination
        stop_event.wait(REFRESH_INTERVAL_SECONDS)


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def start_meta_learning() -> threading.Event:
    """
    Starts the background meta‑learning thread.
    Returns an ``Event`` that can be set to request shutdown.
    """
    stop_event = threading.Event()
    thread = threading.Thread(
        target=reindex_loop, args=(stop_event,), daemon=True, name="MetaLearningThread"
    )
    thread.start()
    print("[MetaLearning] Background re‑indexing thread started.")
    return stop_event


def stop_meta_learning(stop_event: threading.Event) -> None:
    """
    Signals the background thread to stop and waits briefly for cleanup.
    """
    stop_event.set()
    # Give the thread a moment to finish its current iteration
    time.sleep(0.1)
    print("[MetaLearning] Background re‑indexing thread stopped.")


# ----------------------------------------------------------------------
# If executed directly, run a simple demo loop.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    stop_evt = start_meta_learning()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_meta_learning(stop_evt)