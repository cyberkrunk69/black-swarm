import json
import re
import logging
from pathlib import Path
from typing import List, Tuple

# Configure a module‑level logger; the surrounding framework can replace handlers if needed.
logger = logging.getLogger(__name__)


def _has_success_indicator(output: str) -> bool:
    """
    Look for typical success keywords in the grind session output.
    """
    indicators = {"done", "complete", "success"}
    output_lower = output.lower()
    return any(word in output_lower for word in indicators)


def _files_were_modified(modified_paths: List[str]) -> bool:
    """
    Verify that at least one of the reported file paths actually exists on disk.
    """
    return any(Path(p).exists() for p in modified_paths)


def verify_grind_completion(output: str, modified_paths: List[str]) -> bool:
    """
    Perform self‑verification after a grind session.

    Returns:
        bool: True if verification passes, False otherwise.
    """
    indicator_ok = _has_success_indicator(output)
    files_ok = _files_were_modified(modified_paths)
    return indicator_ok and files_ok


def log_self_verification(session_id: int, passed: bool) -> None:
    """
    Emit a standardized log entry for the verification result.
    """
    status = "PASS" if passed else "FAIL"
    logger.info(f"[Session {session_id}] Self-verification: {status}")


def run_self_verification(session_id: int, output: str, modified_paths: List[str]) -> Tuple[bool, str]:
    """
    Convenience wrapper used by the grind orchestrator.

    Args:
        session_id: Identifier of the current grind session.
        output: The raw textual output produced by the grind.
        modified_paths: List of file system paths that the grind claimed to modify.

    Returns:
        Tuple[bool, str]: (verification_passed, human‑readable message)
    """
    passed = verify_grind_completion(output, modified_paths)
    log_self_verification(session_id, passed)

    if passed:
        message = "Self‑verification succeeded."
    else:
        message = (
            "Self‑verification failed: either no success indicator was found in the output "
            "or no files were actually modified."
        )
    return passed, message