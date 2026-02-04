import os
import json
import re
from datetime import datetime
from typing import List, Dict

# Import the logging helper – assumed to exist in the workspace.
# The helper should expose a `log_experience` function that writes
# measurements into the self:experience store.
try:
    from self_observer import log_experience
except ImportError:
    # Fallback stub – in a real environment this will be provided.
    def log_experience(entry: Dict):
        """Fallback stub: prints the entry; real implementation logs to self:experience."""
        print("Logging experience:", json.dumps(entry, indent=2))


class IITMetrics:
    """
    Very light‑weight approximation of Integrated Information Theory (IIT) metrics.
    The implementation is intentionally simple:
      * Reads all text files from the knowledge base.
      * Tokenises the text and builds a crude “information integration” measure.
      * The phi approximation is based on the diversity of concepts (unique tokens)
        weighted by their frequency – a proxy for informational richness.
    The results are logged via `self_observer.log_experience`.
    """

    KNOWLEDGE_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "stripper", "knowledge", "self_awareness")
    )

    def __init__(self):
        self.papers = self._load_papers()

    def _load_papers(self) -> List[str]:
        """Load all .txt/.md files from the knowledge directory."""
        texts = []
        if not os.path.isdir(self.KNOWLEDGE_ROOT):
            raise FileNotFoundError(f"IIT knowledge directory not found: {self.KNOWLEDGE_ROOT}")

        for root, _, files in os.walk(self.KNOWLEDGE_ROOT):
            for fname in files:
                if fname.lower().endswith(('.txt', '.md')):
                    path = os.path.join(root, fname)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            texts.append(f.read())
                    except Exception as e:
                        # Skip unreadable files but continue processing.
                        print(f"Warning: could not read {path}: {e}")
        return texts

    @staticmethod
    def _tokenise(text: str) -> List[str]:
        """Very simple tokeniser – splits on non‑word characters."""
        return re.findall(r"\b\w+\b", text.lower())

    def _compute_phi_approx(self, tokens: List[str]) -> float:
        """
        Approximate phi:
            phi ≈ (unique_token_count / total_token_count) * log2(total_token_count + 1)

        This captures how much the corpus integrates distinct concepts relative to its size.
        """
        if not tokens:
            return 0.0
        total = len(tokens)
        unique = len(set(tokens))
        # Guard against division by zero and log of zero.
        phi = (unique / total) * (total.bit_length())
        return phi

    def compute_and_log(self) -> Dict:
        """
        Compute the phi approximation across all loaded papers and log the result.
        Returns the measurement dictionary for possible downstream use.
        """
        all_tokens = []
        for paper in self.papers:
            all_tokens.extend(self._tokenise(paper))

        phi_value = self._compute_phi_approx(all_tokens)

        measurement = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metric": "phi_approximation",
            "value": phi_value,
            "details": {
                "total_tokens": len(all_tokens),
                "unique_tokens": len(set(all_tokens)),
                "source_documents": len(self.papers)
            }
        }

        # Log using the self_observer helper.
        log_experience(measurement)

        return measurement


if __name__ == "__main__":
    # When executed directly, compute the metric and store it.
    iit = IITMetrics()
    iit.compute_and_log()