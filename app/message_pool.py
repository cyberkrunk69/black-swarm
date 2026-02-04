import os
import json
import uuid
from datetime import datetime
from threading import Lock

class MessagePool:
    """
    Simple JSON‑backed message pool for inter‑role communication.
    Messages are stored as a list of dicts in a JSON file.
    """

    def __init__(self, storage_path: str = "message_pool.json"):
        self.storage_path = storage_path
        self._lock = Lock()
        # Ensure the storage file exists and has the correct top‑level structure
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"messages": []}, f, indent=2)
        self._load()

    def _load(self):
        with self._lock, open(self.storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.messages = data.get("messages", [])

    def _save(self):
        with self._lock, open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump({"messages": self.messages}, f, indent=2)

    def publish(
        self,
        from_role: str,
        message_type: str,
        content: dict,
        subscribers: list,
    ) -> str:
        """
        Add a new message to the pool.

        Returns the generated message ID.
        """
        msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.utcnow().isoformat() + "Z"
        message = {
            "id": msg_id,
            "timestamp": timestamp,
            "from_role": from_role,
            "type": message_type,
            "content": content,
            "subscribers": subscribers,
        }
        self.messages.append(message)
        self._save()
        return msg_id

    def subscribe(self, role: str) -> list:
        """
        Retrieve all messages for which *role* is listed as a subscriber.
        """
        relevant = [msg for msg in self.messages if role in msg.get("subscribers", [])]
        return relevant

# Message type constants for easy reference
TASK_ASSIGNMENT = "TASK_ASSIGNMENT"
EXECUTION_PLAN = "EXECUTION_PLAN"
CODE_ARTIFACT = "CODE_ARTIFACT"
TEST_RESULT = "TEST_RESULT"
REVIEW_FEEDBACK = "REVIEW_FEEDBACK"