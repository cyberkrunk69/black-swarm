import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Keywords that indicate a successful task completion
_SUCCESS_KEYWORDS = {"done", "complete", "success"}

def _contains_success_keyword(output: str) -> bool:
    """
    Check if the result output contains any of the success keywords.
    """
    lowered = output.lower()
    return any(keyword in lowered for keyword in _SUCCESS_KEYWORDS)


def _any_files_modified(modified_paths: List[Path], session_start_ts: float) -> bool:
    """
    Determine if any of the given file paths have a modification time later than the session start.
    """
    for p in modified_paths:
        if not p.is_file():
            continue
        try:
            mtime = p.stat().st_mtime
            if mtime >= session_start_ts:
                return True
        except OSError:
            continue
    return False


def self_verify(session_id: int,
                result_output: str,
                modified_files: List[str],
                session_start_ts: float) -> Dict[str, Any]:
    """
    Perform self‑verification after a grind session finishes.

    Parameters
    ----------
    session_id : int
        Identifier of the grind session.
    result_output : str
        The textual output produced by the grind session.
    modified_files : List[str]
        List of file paths that the session claims to have touched.
    session_start_ts : float
        Unix timestamp (seconds) when the session started.

    Returns
    -------
    dict
        Verification report containing:
        - ``passed`` (bool): overall verification result.
        - ``reason`` (str): human‑readable explanation.
        - ``verified_files`` (list): files that were confirmed modified.
    """
    # 1. Check for success keywords in the textual output
    keyword_pass = _contains_success_keyword(result_output)

    # 2. Resolve file paths and check modification times
    file_paths = [Path(p).resolve() for p in modified_files]
    files_modified = _any_files_modified(file_paths, session_start_ts)

    # 3. Overall pass condition
    passed = keyword_pass and files_modified

    # 4. Build human‑readable reason
    if not keyword_pass and not files_modified:
        reason = "No success keywords found and no files were modified."
    elif not keyword_pass:
        reason = "Success keywords missing in output."
    elif not files_modified:
        reason = "No files were modified during the session."
    else:
        reason = "Self‑verification passed."

    # 5. Log the verification result
    status = "PASS" if passed else "FAIL"
    logger.info(f"[Session {session_id}] Self-verification: {status}")

    # 6. Return structured report
    return {
        "passed": passed,
        "reason": reason,
        "verified_files": [str(p) for p in file_paths if p.is_file() and p.stat().st_mtime >= session_start_ts],
    }

# Helper for easy integration with existing grind workflow
def verify_and_log(session_id: int,
                   result_output: str,
                   modified_files: List[str],
                   session_start_ts: float,
                   success_logger: Any) -> bool:
    """
    Wrapper that runs self‑verification and then forwards the result to the
    provided ``success_logger`` (the original success‑logging callable).

    Returns ``True`` if verification passed, otherwise ``False``.
    """
    report = self_verify(session_id, result_output, modified_files, session_start_ts)
    if report["passed"]:
        # Forward to the original success logger
        success_logger(session_id, result_output, modified_files)
    else:
        # Mark as partial completion – callers can decide what to do
        logger.warning(f"[Session {session_id}] Partial completion detected: {report['reason']}")
    return report["passed"]