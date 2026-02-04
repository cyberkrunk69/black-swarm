import os
import json
import datetime
import threading
from pathlib import Path

# ----------------------------------------------------------------------
# Configuration – define which files belong to which tier
# ----------------------------------------------------------------------
NEVER_TOUCH = {
    "safety_gateway.py",
    "safety_constitutional.py",
    "grind_spawner.py",
    "orchestrator.py",
    # add more core‑safety files here
}

ASK_PERMISSION = {
    "smart_executor.py",
    "inference_engine.py",
    # add more ask‑permission files here
}

AUDIT_LOG = Path(__file__).with_name("permission_audit.log")
AUDIT_LOCK = threading.Lock()


def _log_audit(entry: dict):
    """Thread‑safe append of a JSON line to the audit log."""
    with AUDIT_LOCK, open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _timestamp() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


class PermissionError(Exception):
    """Raised when a request violates the NEVER_TOUCH tier."""
    pass


class FilePermissionGateway:
    """
    Central gateway for self‑modification requests.
    """

    def __init__(self, reviewer_callable=None):
        """
        :param reviewer_callable: Optional function that receives a request dict
                                  and returns True (grant) or False (deny).
                                  If None, a default interactive reviewer is used.
        """
        self.reviewer = reviewer_callable or self._default_reviewer

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def request_edit(self, worker_id: str, file_path: str, reason: str) -> bool:
        """
        Main entry point for a worker that wants to edit a file.

        :param worker_id: Identifier of the requesting worker.
        :param file_path: Relative path to the target file.
        :param reason:    Human‑readable justification.
        :return: True if edit is permitted, False otherwise.
        """
        tier = self._determine_tier(file_path)

        audit_entry = {
            "timestamp": _timestamp(),
            "worker": worker_id,
            "file": file_path,
            "tier": tier,
            "reason": reason,
            "outcome": None,
        }

        if tier == "NEVER_TOUCH":
            audit_entry["outcome"] = "DENIED_NEVER_TOUCH"
            _log_audit(audit_entry)
            raise PermissionError(f"File '{file_path}' is in the NEVER_TOUCH tier and cannot be edited.")

        if tier == "OPEN":
            audit_entry["outcome"] = "GRANTED_OPEN"
            _log_audit(audit_entry)
            return True

        # ASK_PERMISSION flow
        request = {
            "worker": worker_id,
            "file": file_path,
            "reason": reason,
            "timestamp": _timestamp(),
        }

        # Step 1 – reviewer evaluates
        granted = self.reviewer(request)

        # Step 2 – optional brief debate (max 2 rounds)
        if not granted:
            # Simple automated debate: ask requester for clarification once
            clarification = self._request_clarification(worker_id, file_path, reason)
            if clarification:
                request["clarification"] = clarification
                granted = self.reviewer(request)

        audit_entry["outcome"] = "GRANTED" if granted else "DENIED"
        _log_audit(audit_entry)
        return granted

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _determine_tier(file_path: str) -> str:
        """Return the tier name for a given file."""
        name = os.path.basename(file_path)
        if name in NEVER_TOUCH:
            return "NEVER_TOUCH"
        if name in ASK_PERMISSION:
            return "ASK_PERMISSION"
        return "OPEN"

    @staticmethod
    def _default_reviewer(request: dict) -> bool:
        """
        Very simple interactive reviewer used when no custom reviewer is supplied.
        In a real deployment this would be replaced by an autonomous reviewer worker.
        """
        print("\n=== Permission Review ===")
        print(f"Worker: {request['worker']}")
        print(f"File  : {request['file']}")
        print(f"Reason: {request['reason']}")
        answer = input("Grant permission? (y/n): ").strip().lower()
        return answer == "y"

    @staticmethod
    def _request_clarification(worker_id: str, file_path: str, original_reason: str) -> str:
        """
        Prompt the requester for a short clarification. Returns the clarification
        string or an empty string if the requester declines.
        """
        print(f"\n[Debate] Worker '{worker_id}' requested edit on '{file_path}'.")
        print(f"Original reason: {original_reason}")
        clarification = input("Provide a brief clarification (or press Enter to skip): ").strip()
        return clarification

    # ------------------------------------------------------------------
    # Convenience method for performing the actual edit (optional)
    # ------------------------------------------------------------------
    @staticmethod
    def apply_edit(file_path: str, new_content: str):
        """
        Overwrites the target file with new_content.
        Caller must have already obtained permission via `request_edit`.
        """
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)