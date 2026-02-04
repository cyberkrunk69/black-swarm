import json
import time
import threading
from pathlib import Path
from typing import Dict, Any, List

# Configuration ---------------------------------------------------------------
RESEARCH_INDEX_PATH = Path("/app/research_index.json")
INSIGHTS_OUTPUT_PATH = Path("/app/insights.json")
REINDEX_INTERVAL_SECONDS = 300  # 5 minutes; adjust as needed

# -----------------------------------------------------------------------------


def load_json(path: Path) -> Any:
    """Safely load JSON from a file."""
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_json(data: Any, path: Path) -> None:
    """Write JSON data to a file atomically."""
    temp_path = path.with_suffix(".tmp")
    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    temp_path.replace(path)


def extract_insights(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Placeholder for the actual insight extraction logic.
    For demonstration, we simply return entries that contain a non‑empty
    'insight' field.
    """
    insights = []
    for entry in entries:
        if entry.get("insight"):
            insights.append(
                {
                    "id": entry.get("id"),
                    "title": entry.get("title"),
                    "insight": entry["insight"],
                }
            )
    return insights


class MetaLearningLoop(threading.Thread):
    """
    A background thread that periodically re‑indexes the research index
    and updates the insights file.
    """

    def __init__(self, interval: int = REINDEX_INTERVAL_SECONDS):
        super().__init__(daemon=True)
        self.interval = interval
        self._stop_event = threading.Event()
        self._last_index_snapshot: Dict[str, Any] = {}

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._reindex()
            except Exception as exc:
                # In production you'd log this; for now we just print.
                print(f"[MetaLearningLoop] Unexpected error: {exc}")
            self._stop_event.wait(self.interval)

    def stop(self) -> None:
        self._stop_event.set()

    def _reindex(self) -> None:
        # Load the current research index
        current_index = load_json(RESEARCH_INDEX_PATH)

        # Detect changes – simple shallow compare; can be enhanced.
        if current_index == self._last_index_snapshot:
            # No changes detected; skip processing.
            return

        # Extract insights from the new/updated entries.
        entries = current_index.get("entries", [])
        new_insights = extract_insights(entries)

        # Merge with existing insights (avoid duplicates)
        existing_insights = load_json(INSIGHTS_OUTPUT_PATH).get("insights", [])
        merged = {ins["id"]: ins for ins in existing_insights}
        for ins in new_insights:
            merged[ins["id"]] = ins

        # Save the updated insights
        save_json({"insights": list(merged.values())}, INSIGHTS_OUTPUT_PATH)

        # Update snapshot
        self._last_index_snapshot = current_index
        print("[MetaLearningLoop] Re‑indexed research data and updated insights.")


def start_meta_learning_loop() -> MetaLearningLoop:
    """
    Helper to start the loop from other modules or entry points.
    """
    loop = MetaLearningLoop()
    loop.start()
    return loop


if __name__ == "__main__":
    # Running as a standalone script will keep the process alive.
    loop = start_meta_learning_loop()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down meta‑learning loop...")
        loop.stop()
        loop.join()