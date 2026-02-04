import os
import json
import datetime
from typing import List, Dict, Optional

# ----------------------------------------------------------------------
# Configuration – define the tier membership
# ----------------------------------------------------------------------
NEVER_TOUCH_FILES = {
    "safety_gateway.py",
    "safety_constitutional.py",
    # add any additional core safety files here
}

ASK_PERMISSION_FILES = {
    "smart_executor.py",
    "inference_engine.py",
    # add any additional ask‑permission files here
}

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _log_event(event: Dict) -> None:
    """Append a JSON line to the permission log."""
    log_path = os.path.join(
        "experiments",
        "exp_20260203_194356_unified_session_3",
        "permission_audit.log",
    )
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


# ----------------------------------------------------------------------
# Core gateway class
# ----------------------------------------------------------------------
class FilePermissionGateway:
    """
    Central authority for file‑permission decisions.
    """

    def __init__(self):
        self.never_touch = NEVER_TOUCH_FILES
        self.ask_permission = ASK_PERMISSION_FILES

    # ------------------------------------------------------------------
    # Tier lookup
    # ------------------------------------------------------------------
    def check_permission(self, file_name: str) -> str:
        """
        Return the tier for *file_name*:
        - "NEVER TOUCH"
        - "ASK PERMISSION"
        - "OPEN"
        """
        base = os.path.basename(file_name)
        if base in self.never_touch:
            return "NEVER TOUCH"
        if base in self.ask_permission:
            return "ASK PERMISSION"
        return "OPEN"

    # ------------------------------------------------------------------
    # Permission request workflow
    # ------------------------------------------------------------------
    def request_permission(
        self,
        requester_id: str,
        file_name: str,
        reason: str,
        reviewer_id: Optional[str] = None,
    ) -> bool:
        """
        Execute the ASK‑PERMISSION workflow.

        Parameters
        ----------
        requester_id: identifier of the worker making the request
        file_name: target file to edit
        reason: free‑text justification
        reviewer_id: optional identifier of the reviewer (if None, a default
                     reviewer is selected)

        Returns
        -------
        bool – True if permission granted, False otherwise.
        """
        tier = self.check_permission(file_name)
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        # ----------------------------------------------------------------
        # Tier handling
        # ----------------------------------------------------------------
        if tier == "NEVER TOUCH":
            _log_event(
                {
                    "timestamp": timestamp,
                    "requester": requester_id,
                    "file": file_name,
                    "tier": tier,
                    "action": "DENIED",
                    "reason": "File is in NEVER TOUCH tier",
                }
            )
            return False

        if tier == "OPEN":
            # No gatekeeping needed
            _log_event(
                {
                    "timestamp": timestamp,
                    "requester": requester_id,
                    "file": file_name,
                    "tier": tier,
                    "action": "GRANTED",
                    "reason": "Open tier – no review required",
                }
            )
            return True

        # ----------------------------------------------------------------
        # ASK PERMISSION workflow
        # ----------------------------------------------------------------
        # 1. Record the initial request
        request = {
            "timestamp": timestamp,
            "requester": requester_id,
            "file": file_name,
            "tier": tier,
            "reason": reason,
            "status": "PENDING",
        }
        _log_event(request)

        # 2. Simulated reviewer evaluation (placeholder)
        # In a real system this would involve IPC, a separate worker, etc.
        # Here we simply auto‑approve if the reason contains the word "fix"
        # – replace with proper logic as needed.
        approved = "fix" in reason.lower()

        # 3. Log the decision
        decision = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "reviewer": reviewer_id or "auto_reviewer",
            "file": file_name,
            "action": "GRANTED" if approved else "DENIED",
            "original_reason": reason,
        }
        _log_event(decision)

        return approved


# ----------------------------------------------------------------------
# Simple CLI demo (optional)
# ----------------------------------------------------------------------
def _demo():
    gateway = FilePermissionGateway()
    print("=== File Permission Gateway Demo ===")
    test_files = [
        "safety_gateway.py",
        "smart_executor.py",
        "new_experiment.py",
    ]
    for f in test_files:
        tier = gateway.check_permission(f)
        print(f"File: {f:25} → Tier: {tier}")

    # Example request
    granted = gateway.request_permission(
        requester_id="worker_42",
        file_name="smart_executor.py",
        reason="Fix bug in the retry loop",
    )
    print("\nPermission request result:", "GRANTED" if granted else "DENIED")


if __name__ == "__main__":
    _demo()