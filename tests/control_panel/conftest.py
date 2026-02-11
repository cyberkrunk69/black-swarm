import pytest
import re
import sys
import tempfile
from pathlib import Path

# Add vivarium to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from vivarium.runtime.control_panel_app import app as _app

CREATIVE_SEED_PATTERN = re.compile(r"^[A-Z]{2}-\d{4}-[A-Z]{2}$")


@pytest.fixture
def app():
    """Create app with test config"""
    workspace = Path(tempfile.mkdtemp())
    swarm_dir = workspace / ".swarm"
    swarm_dir.mkdir(exist_ok=True)
    identities_dir = swarm_dir / "identities"
    identities_dir.mkdir(exist_ok=True)
    security_dir = workspace / "security"
    security_dir.mkdir(exist_ok=True)

    _app.config["TESTING"] = True
    _app.config["WORKSPACE"] = workspace
    _app.config["ACTION_LOG"] = workspace / "action_log.jsonl"
    _app.config["EXECUTION_LOG"] = workspace / "execution_log.jsonl"
    _app.config["QUEUE_FILE"] = workspace / "queue.json"
    _app.config["KILL_SWITCH"] = swarm_dir / "kill_switch.json"
    _app.config["FREE_TIME_BALANCES"] = swarm_dir / "free_time_balances.json"
    _app.config["IDENTITIES_DIR"] = identities_dir
    _app.config["GROQ_API_KEY_FILE"] = security_dir / "groq_key.txt"
    _app.config["RUNTIME_SPEED_FILE"] = swarm_dir / "runtime_speed.json"
    _app.config["MAILBOX_QUESTS_FILE"] = swarm_dir / "mailbox_quests.json"
    _app.config["CREATIVE_SEED_PATTERN"] = CREATIVE_SEED_PATTERN
    _app.config["CREATIVE_SEED_USED_FILE"] = swarm_dir / "creative_seed_used.json"
    _app.config["CREATIVE_SEED_USED_MAX"] = 5000
    _app.config["DISCUSSIONS_DIR"] = swarm_dir / "discussions"

    return _app


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """No auth needed for localhost, but structure for future"""
    return {}


@pytest.fixture
def localhost_kwargs():
    """Ensure requests appear from localhost for middleware"""
    return {"environ_overrides": {"REMOTE_ADDR": "127.0.0.1"}}
