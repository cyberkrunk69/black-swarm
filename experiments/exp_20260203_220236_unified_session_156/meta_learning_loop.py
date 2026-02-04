"""
Meta‑Learning Loop for Periodic Re‑indexing

This module implements a lightweight meta‑learning loop that:
1. Loads the current `research_index.json`.
2. Detects new entries since the last run.
3. Runs a placeholder “insight extraction” routine on the new entries.
4. Updates the index with any new insights and writes it back to disk.
5. Sleeps for a configurable interval before repeating.

The loop is deliberately simple – it can be imported and started with
`run_meta_learning_loop()` or used as an asyncio task in a larger system.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Directory containing the index file (relative to the workspace root)
INDEX_DIR = Path(__file__).resolve().parents[2]  # experiments/exp_.../
INDEX_PATH = INDEX_DIR / "research_index.json"

# How often (in seconds) to re‑index. Adjust as needed.
REINDEX_INTERVAL = 300  # 5 minutes

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #


def load_index() -> Dict[str, Any]:
    """Load the research index from disk. Returns an empty dict if missing."""
    if not INDEX_PATH.is_file():
        logging.warning("Index file not found – creating a new one.")
        return {"entries": [], "insights": [], "metadata": {"last_run": None}}
    with INDEX_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_index(index: Dict[str, Any]) -> None:
    """Persist the index back to disk."""
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    logging.info("Research index saved (%d entries, %d insights).", len(index.get("entries", [])), len(index.get("insights", [])))


def detect_new_entries(old_index: Dict[str, Any], new_index: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a list of entries present in `new_index` but not in `old_index`."""
    old_ids = {entry.get("id") for entry in old_index.get("entries", [])}
    return [e for e in new_index.get("entries", []) if e.get("id") not in old_ids]


def extract_insights_from_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for a real insight extraction routine.
    For now we simply echo the title and a timestamp.
    """
    insight = {
        "source_id": entry.get("id"),
        "summary": f"Insight derived from '{entry.get('title', 'Untitled')}'",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    return insight


async def reindex_once() -> None:
    """Perform a single re‑indexing pass."""
    # Load the current persisted index
    persisted_index = load_index()

    # Load a fresh copy of the raw research data.
    # In a real system this could be a separate file or a DB query.
    # Here we assume the same file holds the raw entries.
    raw_index = load_index()  # For demo purposes; replace with actual source.

    new_entries = detect_new_entries(persisted_index, raw_index)
    if not new_entries:
        logging.info("No new entries detected.")
        return

    logging.info("Detected %d new entries – extracting insights.", len(new_entries))
    new_insights = [extract_insights_from_entry(e) for e in new_entries]

    # Update the persisted index
    persisted_index.setdefault("entries", []).extend(new_entries)
    persisted_index.setdefault("insights", []).extend(new_insights)
    persisted_index.setdefault("metadata", {})["last_run"] = datetime.utcnow().isoformat() + "Z"

    save_index(persisted_index)


async def meta_learning_loop(stop_event: asyncio.Event) -> None:
    """
    Main loop that periodically re‑indexes the research data.
    The loop runs until `stop_event` is set.
    """
    logging.info("Starting meta‑learning re‑index loop (interval=%ds).", REINDEX_INTERVAL)
    while not stop_event.is_set():
        try:
            await reindex_once()
        except Exception as exc:  # pragma: no cover
            logging.exception("Unexpected error during re‑indexing: %s", exc)
        # Wait for the next interval or early termination
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=REINDEX_INTERVAL)
        except asyncio.TimeoutError:
            continue
    logging.info("Meta‑learning loop stopped.")


def run_meta_learning_loop() -> None:
    """
    Convenience entry‑point for running the loop from the command line.
    Press Ctrl‑C to stop.
    """
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def _handle_sigint():
        logging.info("SIGINT received – shutting down...")
        stop_event.set()

    try:
        import signal

        loop.add_signal_handler(signal.SIGINT, _handle_sigint)
    except NotImplementedError:
        # Windows may not support add_signal_handler; fallback to KeyboardInterrupt handling.
        pass

    try:
        loop.run_until_complete(meta_learning_loop(stop_event))
    finally:
        loop.close()


if __name__ == "__main__":
    run_meta_learning_loop()