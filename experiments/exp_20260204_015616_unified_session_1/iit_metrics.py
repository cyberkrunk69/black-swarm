import os
import json
import datetime
from pathlib import Path

# Assuming there is a helper in the repo that knows how to log experiences.
# The typical interface is a function `log_experience(data: dict)` in self_observer.py
# If the import fails (e.g., during isolated testing) we fall back to a no‑op.
try:
    from self_observer import log_experience  # type: ignore
except Exception:  # pragma: no cover
    def log_experience(data: dict):
        """Fallback stub – writes to a local JSON file for debugging."""
        data_path = Path(__file__).parents[2] / "data" / "self_experiences.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        if data_path.is_file():
            with data_path.open("r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []
        existing.append(data)
        with data_path.open("w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)


def _load_iit_papers(base_dir: Path) -> list[str]:
    """
    Load all text files from the IIT knowledge base.

    Parameters
    ----------
    base_dir: Path
        Directory that contains the IIT papers (normally
        ``../stripper/knowledge/self_awareness`` relative to the workspace root).

    Returns
    -------
    List[str]
        Raw textual content of each paper.
    """
    papers = []
    if not base_dir.is_dir():
        return papers

    for file_path in base_dir.rglob("*.txt"):
        try:
            with file_path.open("r", encoding="utf-8") as f:
                papers.append(f.read())
        except Exception:
            # Skip unreadable files silently – they are not critical for the demo.
            continue
    return papers


def _phi_approximation(text: str) -> float:
    """
    Very coarse proxy for integrated information (Φ).

    The approximation counts the number of unique tokens and normalises
    by the total token count, yielding a value in (0, 1].

    This is **not** a scientific implementation – it merely provides a
    deterministic, lightweight metric that can be tracked over time.
    """
    tokens = text.split()
    if not tokens:
        return 0.0
    unique = set(tokens)
    return len(unique) / len(tokens)


def compute_iit_metrics() -> dict:
    """
    Compute a simple IIT‑inspired metric suite.

    Returns
    -------
    dict
        Dictionary containing:
        - ``phi_estimate``: float – average Φ approximation across all papers.
        - ``paper_count``: int – number of papers considered.
        - ``timestamp``: ISO‑8601 string of the measurement time.
    """
    workspace_root = Path(__file__).parents[3]  # /app
    knowledge_dir = workspace_root / "stripper" / "knowledge" / "self_awareness"

    papers = _load_iit_papers(knowledge_dir)

    if not papers:
        phi = 0.0
    else:
        phi_values = [_phi_approximation(p) for p in papers]
        phi = sum(phi_values) / len(phi_values)

    result = {
        "phi_estimate": phi,
        "paper_count": len(papers),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
    return result


def log_iit_metrics():
    """
    Compute the metrics and log them to the self‑experience store.
    """
    metrics = compute_iit_metrics()
    # The self_observer is expected to handle persistence.
    log_experience(metrics)


if __name__ == "__main__":
    # Running the module directly will compute and log a single measurement.
    log_iit_metrics()
    print("IIT metrics logged:", compute_iit_metrics())