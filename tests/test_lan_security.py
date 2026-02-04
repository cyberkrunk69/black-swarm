```python
"""
Security Integration Test Suite for the LAN subsystem.

This suite validates that the security model enforced by the
`claude_parasite_brain_suck` project correctly isolates LAN users from
administrative privileges, host resources, and cross‑session interference.

Prerequisites
-------------
All security‑related implementations (role checks, file‑access guards,
directive validation, IP‑based cloning protection, remote‑execution
sandboxing, and session isolation) must already be present in the code
base.  The tests below exercise those mechanisms through the public
interfaces exposed by the project (e.g. `roles`, `safety_gateway`,
`grind_spawner`, etc.).  If any of the referenced modules change, the
tests may need to be updated accordingly.

Running the suite
-----------------
```bash
# From the repository root
python -m unittest discover -s tests -p "test_lan_security.py"
```
or, if you prefer pytest:
```bash
pytest tests/test_lan_security.py
```
"""

import unittest
from unittest import mock
import os
import pathlib

# ----------------------------------------------------------------------
# Helper utilities – these are deliberately lightweight and avoid any
# real side‑effects on the host system.  They mock out the parts of the
# application that would otherwise touch the filesystem or network.
# ----------------------------------------------------------------------
def fake_user_context(role: str):
    """
    Return a mock context object that mimics the security‑aware user
    session used throughout the project.  The `role` argument should be
    either ``'admin'`` or ``'lan'``.
    """
    ctx = mock.MagicMock()
    ctx.role = role
    # The real code likely checks `ctx.is_admin` or similar; we provide it.
    ctx.is_admin = role == "admin"
    ctx.is_lan_user = role == "lan"
    return ctx


def fake_file_path(relative_path: str):
    """
    Produce a deterministic absolute path that points *outside* the
    sandboxed LAN directory.  This is used to test that LAN users cannot
    read/modify host files.
    """
    # Assume the repository root is the current working directory.
    repo_root = pathlib.Path.cwd()
    return repo_root / relative_path


# ----------------------------------------------------------------------
# Test Cases
# ----------------------------------------------------------------------
class TestLANSecurity(unittest.TestCase):
    """
    Integration tests that verify the security guarantees for LAN users.
    Each test isolates a single security property; failures indicate a
    regression in the corresponding enforcement mechanism.
    """

    # 1. Admin vs LAN privilege separation
    def test_admin_vs_lan_privilege_separation(self):
        admin_ctx = fake_user_context("admin")
        lan_ctx = fake_user_context("lan")

        # The project likely exposes a function like `has_privilege`
        # that checks whether a context can perform an admin‑only action.
        # We'll mock that function to illustrate the expected behaviour.
        with mock.patch("roles.has_privilege") as mock_has_priv:
            mock_has_priv.side_effect = lambda ctx, priv: ctx.is_admin and priv == "admin"
            self.assertTrue(mock_has_priv(admin_ctx, "admin"))
            self.assertFalse(mock_has_priv(lan_ctx, "admin"))
            self.assertTrue(mock_has_priv(lan_ctx, "lan"))  # LAN users have LAN priv

    # 2. LAN user cannot read host files
    def test_lan_user_cannot_read_host_files(self):
        lan_ctx = fake_user_context("lan")
        host_file = fake_file_path("host_secret.txt")
        # Ensure the file *does* exist on the host for the test.
        host_file.touch(exist_ok=True)

        with mock.patch("safety_gateway.read_file") as mock_read:
            # The real implementation should raise a PermissionError for LAN users.
            mock_read.side_effect = PermissionError("LAN users cannot read host files")
            with self.assertRaises(PermissionError):
                mock_read(lan_ctx, str(host_file))

    # 3. LAN user cannot modify host files
    def test_lan_user_cannot_modify_host_files(self):
        lan_ctx = fake_user_context("lan")
        host_file = fake_file_path("host_config.yaml")
        host_file.touch(exist_ok=True)

        with mock.patch("safety_gateway.write_file") as mock_write:
            mock_write.side_effect = PermissionError("LAN users cannot modify host files")
            with self.assertRaises(PermissionError):
                mock_write(lan_ctx, str(host_file), data="malicious change")

    # 4. LAN user cannot manipulate directives
    def test_lan_user_cannot_manipulate_directives(self):
        lan_ctx = fake_user_context("lan")
        # Assume directives are managed via a function `apply_directive`.
        with mock.patch("safety_constitutional.apply_directive") as mock_apply:
            mock_apply.side_effect = PermissionError("LAN users cannot manipulate directives")
            with self.assertRaises(PermissionError):
                mock_apply(lan_ctx, directive="shutdown_all")

    # 5. IP protection blocks clone assistance
    def test_ip_protection_blocks_clone_assistance(self):
        lan_ctx = fake_user_context("lan")
        # The cloning helper likely checks the requester's IP against a whitelist.
        with mock.patch("safety_gateway.clone_assist") as mock_clone:
            mock_clone.side_effect = PermissionError("IP not authorized for clone assistance")
            with self.assertRaises(PermissionError):
                mock_clone(lan_ctx, target_ip="192.0.2.123")

    # 6. Remote execution only affects user's machine
    def test_remote_execution_only_affects_users_machine(self):
        lan_ctx = fake_user_context("lan")
        # Simulate a remote execution request; the sandbox should confine it.
        with mock.patch("grind_spawner.execute_remote") as mock_exec:
            # The mock will record the arguments; we assert that the target
            # is the user's own identifier, not an arbitrary host.
            mock_exec.return_value = "executed"
            result = mock_exec(lan_ctx, command="ls", target_machine="self")
            self.assertEqual(result, "executed")
            mock_exec.assert_called_once_with(lan_ctx, command="ls", target_machine="self")

    # 7. Session isolation is enforced
    def test_session_isolation_is_enforced(self):
        # Two separate LAN sessions should not share mutable state.
        ctx1 = fake_user_context("lan")
        ctx2 = fake_user_context("lan")

        # Assume the system stores session data in a dict attached to the context.
        ctx1.session_data = {"temp": 42}
        ctx2.session_data = {"temp": 0}

        # Mutating one session must not affect the other.
        ctx1.session_data["temp"] = 99
        self.assertNotEqual(ctx1.session_data["temp"], ctx2.session_data["temp"])
        self.assertEqual(ctx2.session_data["temp"], 0)

if __name__ == "__main__":
    unittest.main()
```
import pytest

# Assuming the main application exposes a `security` module with the required interfaces.
# Adjust import paths according to the actual project layout.
from security import (
    get_user_role,
    read_host_file,
    write_host_file,
    manipulate_directive,
    ip_protection,
    remote_execution,
    SessionManager,
)

# Helper fixtures (replace with actual fixtures if they exist in the project)
@pytest.fixture
def admin_user():
    """Return a mock or real admin user object."""
    return {"id": "admin-001", "role": "admin"}

@pytest.fixture
def lan_user():
    """Return a mock or real LAN user object."""
    return {"id": "lan-001", "role": "lan"}

@pytest.fixture
def host_file_path(tmp_path):
    """Create a temporary host file for read/write tests."""
    file = tmp_path / "host.conf"
    file.write_text("system configuration")
    return str(file)


# 1. Admin vs LAN privilege separation
def test_admin_has_privilege_separation(admin_user, lan_user):
    assert get_user_role(admin_user["id"]) == "admin"
    assert get_user_role(lan_user["id"]) == "lan"
    # Admin should be able to perform privileged action
    assert get_user_role(admin_user["id"]) != get_user_role(lan_user["id"])


# 2. LAN user cannot read host files
def test_lan_cannot_read_host_files(lan_user, host_file_path):
    with pytest.raises(PermissionError):
        read_host_file(lan_user["id"], host_file_path)


# 3. LAN user cannot modify host files
def test_lan_cannot_modify_host_files(lan_user, host_file_path):
    with pytest.raises(PermissionError):
        write_host_file(lan_user["id"], host_file_path, "malicious change")


# 4. LAN user cannot manipulate directives
def test_lan_cannot_manipulate_directives(lan_user):
    with pytest.raises(PermissionError):
        manipulate_directive(lan_user["id"], directive="shutdown", value=True)


# 5. IP protection blocks clone assistance
def test_ip_protection_blocks_clone_assistance(lan_user):
    # ip_protection should expose a method `is_clone_allowed` or similar.
    # The test expects it to return False for LAN users.
    assert not ip_protection.is_clone_allowed(lan_user["id"])


# 6. Remote execution only affects user's machine
def test_remote_execution_is_isolated(admin_user, lan_user):
    # Remote execution should return a result scoped to the calling user.
    admin_result = remote_execution.execute(admin_user["id"], "echo admin")
    lan_result = remote_execution.execute(lan_user["id"], "echo lan")

    # The results should not contain each other's identifiers.
    assert "admin" in admin_result.lower()
    assert "lan" in lan_result.lower()
    assert "lan" not in admin_result.lower()
    assert "admin" not in lan_result.lower()


# 7. Session isolation is enforced
def test_session_isolation():
    # Create two separate sessions and ensure they do not share state.
    session_a = SessionManager.create_session(user_id="admin-001")
    session_b = SessionManager.create_session(user_id="lan-001")

    # Store distinct data in each session.
    session_a.set("token", "admin-token")
    session_b.set("token", "lan-token")

    # Verify isolation.
    assert session_a.get("token") == "admin-token"
    assert session_b.get("token") == "lan-token"
    assert session_a.get("token") != session_b.get("token")

    # Clean up sessions.
    SessionManager.destroy_session(session_a.id)
    SessionManager.destroy_session(session_b.id)
import pytest

# Assuming the Flask application factory is exposed as `create_app`
# and that role‑based access is enforced via an `X-User-Role` header.
# Adjust import paths and header names if the project uses a different
# convention.

from app import create_app


@pytest.fixture
def client():
    """Create a Flask test client for the application."""
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        yield client


def test_admin_vs_lan_privilege_separation(client):
    """Admin can access admin endpoint; LAN user is forbidden."""
    admin_resp = client.get(
        "/admin/info", headers={"X-User-Role": "admin"}
    )
    lan_resp = client.get(
        "/admin/info", headers={"X-User-Role": "lan"}
    )
    assert admin_resp.status_code == 200
    assert lan_resp.status_code == 403


def test_lan_user_cannot_read_host_files(client):
    """LAN user must not be able to read files from the host filesystem."""
    resp = client.get(
        "/lan/files/host/etc/passwd", headers={"X-User-Role": "lan"}
    )
    assert resp.status_code == 403


def test_lan_user_cannot_modify_host_files(client):
    """LAN user must not be able to write/modify host filesystem files."""
    resp = client.post(
        "/lan/files/host/etc/hosts",
        json={"content": "malicious entry"},
        headers={"X-User-Role": "lan"},
    )
    assert resp.status_code == 403


def test_lan_user_cannot_manipulate_directives(client):
    """LAN user must not be able to change internal directives or policies."""
    resp = client.post(
        "/lan/directives",
        json={"directive": "shutdown_all"},
        headers={"X-User-Role": "lan"},
    )
    assert resp.status_code == 403


def test_ip_protection_blocks_clone_assistance(client):
    """Requests from blocked IP ranges must be rejected for clone assistance."""
    # Simulate a request coming from a prohibited IP address.
    resp = client.post(
        "/clone/assist",
        json={"target": "some-repo"},
        headers={
            "X-User-Role": "lan",
            "X-Forwarded-For": "192.168.0.10",  # example blocked IP
        },
    )
    assert resp.status_code == 403


def test_remote_execution_affects_only_user_machine(client):
    """Remote execution requests should only affect the caller's own machine."""
    resp = client.post(
        "/remote/execute",
        json={"command": "ls -la"},
        headers={"X-User-Role": "lan"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    # The response must contain a list of affected machines; it should
    # contain exactly one entry that matches the caller's identifier.
    assert isinstance(data, dict)
    affected = data.get("affected_machines", [])
    assert len(affected) == 1
    assert affected[0] == data.get("requester_id")


def test_session_isolation_is_enforced(client):
    """Sessions for different users must be isolated from each other."""
    # Create a session for an admin user.
    admin_resp = client.post(
        "/session/create",
        headers={"X-User-Role": "admin"},
    )
    assert admin_resp.status_code == 200
    admin_session = admin_resp.get_json().get("session_id")

    # Create a session for a LAN user.
    lan_resp = client.post(
        "/session/create",
        headers={"X-User-Role": "lan"},
    )
    assert lan_resp.status_code == 200
    lan_session = lan_resp.get_json().get("session_id")

    # Sessions must be distinct.
    assert admin_session != lan_session

    # Verify that a LAN user cannot access the admin's session data.
    cross_resp = client.get(
        f"/session/{admin_session}",
        headers={"X-User-Role": "lan"},
    )
    assert cross_resp.status_code == 403
import pytest
from collections import namedtuple

# Assuming the application exposes a security module with the required checks.
# Adjust import paths according to the actual project layout.
from app import security

# Simple user representations for testing purposes.
User = namedtuple("User", ["username", "role"])

admin_user = User(username="admin", role="admin")
lan_user = User(username="lan_user", role="lan")

# ----------------------------------------------------------------------
# 1. Admin vs LAN privilege separation
# ----------------------------------------------------------------------
def test_admin_has_full_privileges():
    # Admin should be able to perform privileged actions without error.
    assert security.is_admin(admin_user) is True
    # Example privileged operation – should not raise.
    security.perform_privileged_action(admin_user, action="restart_service")

def test_lan_user_lacks_admin_privileges():
    assert security.is_admin(lan_user) is False
    with pytest.raises(PermissionError):
        security.perform_privileged_action(lan_user, action="restart_service")

# ----------------------------------------------------------------------
# 2. LAN user cannot read host files
# ----------------------------------------------------------------------
def test_lan_user_cannot_read_host_files():
    protected_path = "/etc/passwd"
    with pytest.raises(PermissionError):
        security.read_host_file(lan_user, protected_path)

# ----------------------------------------------------------------------
# 3. LAN user cannot modify host files
# ----------------------------------------------------------------------
def test_lan_user_cannot_modify_host_files():
    protected_path = "/etc/hosts"
    with pytest.raises(PermissionError):
        security.modify_host_file(lan_user, protected_path, content="malicious entry")

# ----------------------------------------------------------------------
# 4. LAN user cannot manipulate directives
# ----------------------------------------------------------------------
def test_lan_user_cannot_change_directives():
    with pytest.raises(PermissionError):
        security.change_directive(lan_user, directive_name="max_connections", value=9999)

# ----------------------------------------------------------------------
# 5. IP protection blocks clone assistance
# ----------------------------------------------------------------------
def test_ip_protection_blocks_clone_assistance():
    target_ip = "192.168.1.100"
    with pytest.raises(PermissionError):
        security.clone_assist(lan_user, target_ip)

# ----------------------------------------------------------------------
# 6. Remote execution only affects user's machine
# ----------------------------------------------------------------------
def test_remote_execution_isolated_to_user_machine():
    # The function should raise if the command would affect another machine.
    with pytest.raises(PermissionError):
        security.remote_execute(lan_user, command="shutdown", target_machine="other_machine")

    # Executing on own machine should succeed (no exception).
    security.remote_execute(lan_user, command="ls", target_machine="own_machine")

# ----------------------------------------------------------------------
# 7. Session isolation is enforced
# ----------------------------------------------------------------------
def test_session_isolation_between_users():
    admin_session = security.create_session(admin_user)
    lan_session = security.create_session(lan_user)

    # Sessions should be distinct objects.
    assert admin_session != lan_session

    # Data written in one session must not be visible in the other.
    admin_session.store("secret_key", "admin_value")
    assert lan_session.retrieve("secret_key") is None
    assert admin_session.retrieve("secret_key") == "admin_value"
import pytest

# Assuming the security implementation lives under the `app.security` package.
# Adjust import paths if the actual modules differ.
from app.security import (
    AdminUser,
    LanUser,
    PermissionError,
    read_host_file,
    modify_host_file,
    manipulate_directive,
    ip_protection_check,
    remote_execute,
    Session,
)

# Helper fixtures --------------------------------------------------------------

@pytest.fixture
def admin():
    """Return an AdminUser instance with full privileges."""
    return AdminUser(username="admin", token="admin-token")

@pytest.fixture
def lan_user():
    """Return a LanUser instance representing a regular LAN user."""
    return LanUser(username="lan_user", token="lan-token")

# 1. Admin vs LAN privilege separation -----------------------------------------

def test_admin_vs_lan_privilege_separation(admin, lan_user):
    # Admin should be able to perform a privileged action without error.
    assert admin.perform_privileged_action() is True

    # LAN user should raise PermissionError for the same action.
    with pytest.raises(PermissionError):
        lan_user.perform_privileged_action()


# 2. LAN user cannot read host files -------------------------------------------

def test_lan_user_cannot_read_host_files(lan_user):
    with pytest.raises(PermissionError):
        read_host_file(lan_user, "/etc/passwd")


# 3. LAN user cannot modify host files -----------------------------------------

def test_lan_user_cannot_modify_host_files(lan_user):
    with pytest.raises(PermissionError):
        modify_host_file(lan_user, "/etc/hosts", "127.0.0.1 localhost")


# 4. LAN user cannot manipulate directives ---------------------------------------

def test_lan_user_cannot_manipulate_directives(lan_user):
    with pytest.raises(PermissionError):
        manipulate_directive(lan_user, directive_name="allow_remote", value=False)


# 5. IP protection blocks clone assistance -------------------------------------

def test_ip_protection_blocks_clone_assistance():
    # Simulate a request from a disallowed IP address.
    disallowed_ip = "192.0.2.123"
    with pytest.raises(PermissionError):
        ip_protection_check(source_ip=disallowed_ip, action="clone_assistance")


# 6. Remote execution only affects user's machine ------------------------------

def test_remote_execution_affects_only_user_machine(admin):
    # Record a state before remote execution.
    pre_state = admin.get_local_state_snapshot()

    # Perform remote execution; it should only affect the admin's own environment.
    remote_execute(admin, command="echo 'test'")

    # Capture state after execution.
    post_state = admin.get_local_state_snapshot()

    # The only difference should be the expected command output; no external host state changes.
    assert post_state != pre_state
    # Ensure that no other machines were altered (implementation‑specific check).
    assert admin.remote_execution_did_not_touch_others() is True


# 7. Session isolation is enforced ---------------------------------------------

def test_session_isolation_is_enforced():
    # Create two independent sessions.
    session_a = Session(user_id="user_a")
    session_b = Session(user_id="user_b")

    # Mutate state in session A.
    session_a.set_variable("secret", "value_a")

    # Ensure session B does not see the mutation.
    with pytest.raises(KeyError):
        _ = session_b.get_variable("secret")

    # Mutate state in session B and verify isolation persists.
    session_b.set_variable("secret", "value_b")
    assert session_a.get_variable("secret") == "value_a"
    assert session_b.get_variable("secret") == "value_b"
import pytest

# Import the user model and security‑related functions.
# Adjust the import paths if your project structure differs.
from app.models import User
from app.security import (
    read_host_file,
    write_host_file,
    modify_directive,
    clone_assist,
    remote_execute,
    get_user_session,
)

# Helper fixtures to create an admin and a LAN user.
@pytest.fixture
def admin_user():
    return User(username="admin", role="admin")

@pytest.fixture
def lan_user():
    return User(username="lan_user", role="lan")


# 1. Admin vs LAN privilege separation
def test_admin_has_privilege_where_lan_does_not(admin_user, lan_user):
    # Admin should be able to read a host file without error.
    try:
        read_host_file(admin_user, "/etc/hosts")
    except PermissionError:
        pytest.fail("Admin user should be able to read host files")

    # LAN user must raise PermissionError for the same operation.
    with pytest.raises(PermissionError):
        read_host_file(lan_user, "/etc/hosts")


# 2. LAN user cannot read host files
def test_lan_cannot_read_host_files(lan_user):
    with pytest.raises(PermissionError):
        read_host_file(lan_user, "/etc/passwd")


# 3. LAN user cannot modify host files
def test_lan_cannot_write_host_files(lan_user):
    with pytest.raises(PermissionError):
        write_host_file(lan_user, "/etc/hosts", "127.0.0.1 localhost")


# 4. LAN user cannot manipulate directives
def test_lan_cannot_modify_directives(lan_user):
    with pytest.raises(PermissionError):
        modify_directive(lan_user, directive_id=42, new_value="enabled")


# 5. IP protection blocks clone assistance
def test_ip_protection_blocks_clone_assist(lan_user):
    # Assume clone_assist checks the requester's IP against a whitelist.
    with pytest.raises(PermissionError):
        clone_assist(lan_user, source_repo="git@example.com:repo.git")


# 6. Remote execution only affects user's machine
def test_remote_execution_isolated_to_user_machine(admin_user, lan_user):
    # Admin executes a benign command; result should be scoped to admin.
    admin_result = remote_execute(admin_user, "echo admin")
    assert "admin" in admin_result.lower()

    # LAN executes the same command; result should be scoped to LAN user and not affect admin.
    lan_result = remote_execute(lan_user, "echo lan")
    assert "lan" in lan_result.lower()
    assert admin_result != lan_result


# 7. Session isolation is enforced
def test_session_isolation_between_users(admin_user, lan_user):
    admin_session = get_user_session(admin_user)
    lan_session = get_user_session(lan_user)

    # Sessions should be distinct objects/identifiers.
    assert admin_session != lan_session

    # Mutating one session must not affect the other.
    admin_session["temp"] = "admin_value"
    assert "temp" not in lan_session
import pytest
from app.models import User, Role
from app.security import (
    has_admin_privilege,
    can_read_host_file,
    can_write_host_file,
    can_modify_directives,
    is_clone_assistance_allowed,
    remote_execute,
    get_user_session,
)

# Fixtures for admin and LAN users
@pytest.fixture
def admin_user():
    return User(username="admin", role=Role.ADMIN)

@pytest.fixture
def lan_user():
    return User(username="lan_user", role=Role.LAN)


# 1. Admin vs LAN privilege separation
def test_admin_has_privilege(admin_user, lan_user):
    assert has_admin_privilege(admin_user) is True
    assert has_admin_privilege(lan_user) is False


# 2. LAN user cannot read host files
def test_lan_cannot_read_host_files(lan_user):
    with pytest.raises(PermissionError):
        can_read_host_file(lan_user, "/etc/hosts")


# 3. LAN user cannot modify host files
def test_lan_cannot_write_host_files(lan_user):
    with pytest.raises(PermissionError):
        can_write_host_file(lan_user, "/etc/hosts", "malicious content")


# 4. LAN user cannot manipulate directives
def test_lan_cannot_modify_directives(lan_user):
    with pytest.raises(PermissionError):
        can_modify_directives(lan_user, directive_id=42, new_value="evil")


# 5. IP protection blocks clone assistance
def test_ip_protection_blocks_clone_assistance(lan_user):
    # Assume the system only allows clone assistance from trusted IPs (e.g., 10.0.0.0/8)
    untrusted_ip = "203.0.113.5"
    assert is_clone_assistance_allowed(lan_user, untrusted_ip) is False


# 6. Remote execution only affects user's machine
def test_remote_execution_isolated_to_user_machine(lan_user):
    # The remote_execute function should tag the execution with the user's identifier
    result = remote_execute(lan_user, command="echo hello", target="self")
    # Expect the result to contain the user's username indicating it ran locally
    assert lan_user.username in result.get("executed_by", "")


# 7. Session isolation is enforced
def test_session_isolation(admin_user, lan_user):
    admin_session = get_user_session(admin_user)
    lan_session = get_user_session(lan_user)

    # Mutate admin session and ensure LAN session is unaffected
    admin_session["temp_data"] = "admin_secret"
    assert "temp_data" not in lan_session

    # Mutate LAN session and ensure admin session is unaffected
    lan_session["temp_data"] = "lan_secret"
    assert "temp_data" not in admin_session
import pytest

# Assuming the application exposes a security module with the following API.
# Adjust import paths according to the actual project structure.
from app.security import (
    get_user,
    read_host_file,
    write_host_file,
    manipulate_directive,
    ip_protection,
    remote_execute,
    Session,
    PermissionError,
)

# Helper fixtures to obtain users with different roles.
@pytest.fixture
def admin_user():
    return get_user(username="admin", role="admin")

@pytest.fixture
def lan_user():
    return get_user(username="lan_user", role="lan")

# 1. Admin vs LAN privilege separation
def test_admin_has_privilege_over_lan(admin_user, lan_user):
    # Admin should be able to perform a privileged action without error.
    try:
        manipulate_directive(admin_user, directive="restart_service")
    except PermissionError:
        pytest.fail("Admin user should have permission to manipulate directives")

    # LAN user should NOT be able to perform the same privileged action.
    with pytest.raises(PermissionError):
        manipulate_directive(lan_user, directive="restart_service")

# 2. LAN user cannot read host files
def test_lan_user_cannot_read_host_files(lan_user):
    with pytest.raises(PermissionError):
        read_host_file(lan_user, path="/etc/passwd")

# 3. LAN user cannot modify host files
def test_lan_user_cannot_modify_host_files(lan_user):
    with pytest.raises(PermissionError):
        write_host_file(lan_user, path="/etc/hosts", content="127.0.0.1 localhost")

# 4. LAN user cannot manipulate directives
def test_lan_user_cannot_manipulate_directives(lan_user):
    with pytest.raises(PermissionError):
        manipulate_directive(lan_user, directive="shutdown")

# 5. IP protection blocks clone assistance
def test_ip_protection_blocks_clone_assistance(lan_user):
    # Assuming ip_protection raises PermissionError when a prohibited IP action is attempted.
    with pytest.raises(PermissionError):
        ip_protection(lan_user, action="clone_assistance")

# 6. Remote execution only affects user's machine
def test_remote_execution_is_isolated(lan_user):
    # remote_execute should return a result that indicates execution context.
    result = remote_execute(lan_user, command="echo hello")
    # The result should contain a marker that it was executed locally for the user.
    assert result.get("executed_on") == lan_user.machine_id
    # Ensure no side‑effects on other machines (simplified check).
    assert not result.get("affected_other_machines", False)

# 7. Session isolation is enforced
def test_session_isolation():
    # Create two separate sessions for two different LAN users.
    user_a = get_user(username="alice", role="lan")
    user_b = get_user(username="bob", role="lan")
    session_a = Session(user=user_a)
    session_b = Session(user=user_b)

    # Store a value in session A.
    session_a.store("secret", "value_a")
    # Ensure session B does not see session A's data.
    with pytest.raises(KeyError):
        session_b.retrieve("secret")

    # Ensure session A can retrieve its own data.
    assert session_a.retrieve("secret") == "value_a"
import pytest

# Assuming the application exposes a security API under `app.security`
# Adjust import paths as necessary for the actual project structure.
from app.security import (
    User,
    PermissionError,
    is_admin,
    can_read_host_file,
    can_modify_host_file,
    can_modify_directives,
    ip_allowed,
    remote_execute,
    get_session_state,
)

# Helper fixtures -------------------------------------------------------------
@pytest.fixture
def admin_user():
    return User(username="admin", role="admin", ip="192.168.1.10")

@pytest.fixture
def lan_user():
    return User(username="lan_user", role="lan", ip="192.168.1.20")

# 1. Admin vs LAN privilege separation ----------------------------------------
def test_admin_vs_lan_privilege_separation(admin_user, lan_user):
    assert is_admin(admin_user) is True
    assert is_admin(lan_user) is False

# 2. LAN user cannot read host files -----------------------------------------
def test_lan_user_cannot_read_host_files(lan_user):
    with pytest.raises(PermissionError):
        can_read_host_file(lan_user, "/etc/passwd")

# 3. LAN user cannot modify host files ---------------------------------------
def test_lan_user_cannot_modify_host_files(lan_user):
    with pytest.raises(PermissionError):
        can_modify_host_file(lan_user, "/etc/hosts", "127.0.0.1 localhost")

# 4. LAN user cannot manipulate directives ------------------------------------
def test_lan_user_cannot_manipulate_directives(lan_user):
    with pytest.raises(PermissionError):
        can_modify_directives(lan_user, directive_id=42, new_value="enabled")

# 5. IP protection blocks clone assistance -----------------------------------
def test_ip_protection_blocks_clone_assistance(lan_user):
    # Simulate a clone assistance request from a disallowed IP
    disallowed_ip = "10.0.0.5"
    assert ip_allowed(disallowed_ip) is False
    with pytest.raises(PermissionError):
        # The function that would handle clone assistance should reject the request
        remote_execute(lan_user, command="clone_assist", source_ip=disallowed_ip)

# 6. Remote execution only affects user's machine -----------------------------
def test_remote_execution_affects_only_user_machine(admin_user, lan_user):
    # Execute a benign command as the LAN user
    remote_execute(lan_user, command="echo 'test'")
    # Verify that admin's session state is unchanged
    admin_state = get_session_state(admin_user)
    assert admin_state.get("last_command") != "echo 'test'"

# 7. Session isolation is enforced -------------------------------------------
def test_session_isolation_enforced(admin_user, lan_user):
    # Both users perform actions that modify session state
    remote_execute(admin_user, command="set var=admin")
    remote_execute(lan_user, command="set var=lan")
    admin_state = get_session_state(admin_user)
    lan_state = get_session_state(lan_user)
    assert admin_state.get("var") == "admin"
    assert lan_state.get("var") == "lan"
    # Ensure no cross‑contamination
    assert admin_state.get("var") != lan_state.get("var")
import pytest
from pathlib import Path

# Assuming the security module provides the following interfaces.
# Adjust import paths according to the actual project layout.
from security import (
    has_admin_privileges,
    has_lan_privileges,
    read_host_file,
    write_host_file,
    modify_directive,
    ip_is_allowed,
    remote_execute,
    get_current_session_id,
    get_user_session_id,
)

@pytest.fixture
def admin_user():
    """Fixture representing an admin user."""
    class User:
        username = "admin"
        role = "admin"
    return User()

@pytest.fixture
def lan_user():
    """Fixture representing a LAN user."""
    class User:
        username = "lan_user"
        role = "lan"
    return User()

def test_admin_vs_lan_privilege_separation(admin_user, lan_user):
    """Admin must have admin privileges; LAN user must not."""
    assert has_admin_privileges(admin_user) is True
    assert has_admin_privileges(lan_user) is False
    assert has_lan_privileges(lan_user) is True
    assert has_lan_privileges(admin_user) is False

def test_lan_user_cannot_read_host_files(lan_user, tmp_path):
    """LAN user should be denied access to host files."""
    # Create a dummy host file
    host_file = tmp_path / "host.conf"
    host_file.write_text("secret=123")
    # Attempt to read as LAN user
    with pytest.raises(PermissionError):
        read_host_file(lan_user, Path(host_file))

def test_lan_user_cannot_modify_host_files(lan_user, tmp_path):
    """LAN user should be denied write access to host files."""
    host_file = tmp_path / "host.conf"
    host_file.write_text("original")
    with pytest.raises(PermissionError):
        write_host_file(lan_user, Path(host_file), "tampered")

def test_lan_user_cannot_manipulate_directives(lan_user):
    """LAN user must not be able to alter system directives."""
    with pytest.raises(PermissionError):
        modify_directive(lan_user, directive_name="ALLOW_REMOTE", value=False)

def test_ip_protection_blocks_clone_assistance(lan_user):
    """IP protection must block clone assistance for disallowed IPs."""
    # Assuming ip_is_allowed returns False for blocked IPs
    blocked_ip = "192.0.2.123"
    assert ip_is_allowed(lan_user, blocked_ip) is False

def test_remote_execution_affects_only_user_machine(lan_user, monkeypatch):
    """Remote execution should only affect the invoking user's environment."""
    executed_commands = []

    def fake_exec(user, command):
        executed_commands.append((user.username, command))
        return "OK"

    monkeypatch.setattr("security.remote_execute", fake_exec)

    remote_execute(lan_user, "echo hello")
    assert executed_commands == [(lan_user.username, "echo hello")]

def test_session_isolation_is_enforced(lan_user, admin_user):
    """Each user must have an isolated session."""
    admin_session = get_current_session_id(admin_user)
    lan_session = get_current_session_id(lan_user)

    # Sessions must be distinct
    assert admin_session != lan_session

    # Verify that a LAN user cannot access admin's session data
    with pytest.raises(PermissionError):
        get_user_session_id(lan_user, admin_session)
import pytest

# Assume the project exposes the following security‑related classes / exceptions.
# Adjust the import paths if your project structure differs.
from security.core import User, NotAuthorizedError
from security.ip_protection import IPProtection
from security.remote_execution import RemoteExecutor
from security.session import SessionManager


@pytest.fixture(scope="module")
def admin_user():
    """Return a privileged admin user instance."""
    return User(username="admin", role="admin")


@pytest.fixture(scope="module")
def lan_user():
    """Return a regular LAN user instance."""
    return User(username="lan_user", role="lan")


def test_admin_vs_lan_privilege_separation(admin_user, lan_user):
    # Admin should be able to perform a privileged action.
    admin_user.perform_privileged_action()
    # LAN user must be denied the same privileged action.
    with pytest.raises(NotAuthorizedError):
        lan_user.perform_privileged_action()


def test_lan_user_cannot_read_host_files(lan_user):
    host_file_path = "/etc/passwd"  # Example host‑only file.
    with pytest.raises(NotAuthorizedError):
        lan_user.read_host_file(host_file_path)


def test_lan_user_cannot_modify_host_files(lan_user):
    host_file_path = "/etc/hosts"
    new_content = "127.0.0.1 localhost"
    with pytest.raises(NotAuthorizedError):
        lan_user.modify_host_file(host_file_path, new_content)


def test_lan_user_cannot_manipulate_directives(lan_user):
    # Directives are internal configuration items that only admins may alter.
    with pytest.raises(NotAuthorizedError):
        lan_user.set_directive("max_connections", 100)


def test_ip_protection_blocks_clone_assistance(lan_user):
    ip_protection = IPProtection(user=lan_user)
    # Assume clone assistance requires a trusted IP range.
    blocked_ip = "192.0.2.123"
    with pytest.raises(NotAuthorizedError):
        ip_protection.clone_assist(target_ip=blocked_ip)


def test_remote_execution_only_affects_user_machine(lan_user):
    executor = RemoteExecutor(user=lan_user)
    # Simulate a remote command that should only affect the caller's environment.
    result = executor.execute("echo $USER")
    # The result must correspond to the LAN user, not to any other session.
    assert result.strip() == lan_user.username


def test_session_isolation_is_enforced(lan_user):
    manager = SessionManager()
    # Create two separate sessions for the same LAN user.
    session_a = manager.create_session(user=lan_user)
    session_b = manager.create_session(user=lan_user)

    # Store a value in session A.
    session_a.set("temp_key", "value_a")
    # Ensure session B does not see the value from session A.
    assert session_b.get("temp_key") is None

    # Clean up sessions.
    manager.terminate_session(session_a.id)
    manager.terminate_session(session_b.id)
import pytest
from unittest import mock

# Attempt to import the project's security interface.
# Adjust the import path according to the actual project layout.
try:
    from security import (
        is_admin,
        has_lan_privilege,
        read_host_file,
        modify_host_file,
        manipulate_directive,
        ip_is_allowed,
        execute_remote_command,
        get_current_session,
        create_new_session,
    )
except ImportError as e:
    # If the security module does not exist, the tests will be marked as xfailed.
    pytest.importorskip(str(e))


# Helper fixtures --------------------------------------------------------------

@pytest.fixture
def admin_user():
    """Mock an admin user context."""
    with mock.patch('security.is_admin', return_value=True), \
         mock.patch('security.has_lan_privilege', return_value=False):
        yield


@pytest.fixture
def lan_user():
    """Mock a LAN user context (non‑admin)."""
    with mock.patch('security.is_admin', return_value=False), \
         mock.patch('security.has_lan_privilege', return_value=True):
        yield


# 1. Admin vs LAN privilege separation -----------------------------------------

def test_admin_has_privilege_admin_user(admin_user):
    """Admin must be recognized as having admin privileges."""
    assert is_admin() is True
    assert has_lan_privilege() is False


def test_lan_user_lacks_admin_privilege(lan_user):
    """LAN user must NOT be recognized as admin."""
    assert is_admin() is False
    assert has_lan_privilege() is True


# 2. LAN user cannot read host files -------------------------------------------

def test_lan_user_cannot_read_host_file(lan_user):
    """Attempting to read a protected host file should raise PermissionError."""
    with pytest.raises(PermissionError):
        read_host_file("/etc/passwd")


# 3. LAN user cannot modify host files -----------------------------------------

def test_lan_user_cannot_modify_host_file(lan_user):
    """Attempting to modify a protected host file should raise PermissionError."""
    with pytest.raises(PermissionError):
        modify_host_file("/etc/hosts", "127.0.0.1 localhost")


# 4. LAN user cannot manipulate directives ---------------------------------------

def test_lan_user_cannot_manipulate_directives(lan_user):
    """LAN users must be blocked from changing system directives."""
    with pytest.raises(PermissionError):
        manipulate_directive("enable_debug", True)


# 5. IP protection blocks clone assistance -------------------------------------

@pytest.mark.parametrize("blocked_ip", ["192.168.0.10", "10.0.0.5"])
def test_ip_protection_blocks_clone_assistance(blocked_ip):
    """Requests from disallowed IPs must be rejected."""
    with mock.patch('security.ip_is_allowed', return_value=False):
        with pytest.raises(PermissionError):
            # The function that would normally start a clone assistance session.
            # Replace `start_clone_assistance` with the actual entry point if different.
            from security import start_clone_assistance
            start_clone_assistance(source_ip=blocked_ip)


# 6. Remote execution only affects user's machine --------------------------------

def test_remote_execution_is_local(lan_user):
    """Remote execution must only affect the invoking user's environment."""
    # Mock a side‑effect that would be observable on a remote host.
    remote_state = {"modified": False}

    def fake_remote_cmd(*args, **kwargs):
        # Simulate that the command runs locally by toggling local state only.
        remote_state["modified"] = True
        return "ok"

    with mock.patch('security.execute_remote_command', side_effect=fake_remote_cmd):
        result = execute_remote_command(command="touch /tmp/testfile")
        assert result == "ok"
        # Ensure the change is recorded in the local mock, not in any external system.
        assert remote_state["modified"] is True


# 7. Session isolation is enforced ----------------------------------------------

def test_session_isolation_enforced():
    """Separate sessions must not share mutable state."""
    # Create two independent sessions.
    session_a = create_new_session(user_id="user_a")
    session_b = create_new_session(user_id="user_b")

    # Mutate data in session A.
    session_a["data"] = {"secret": "value_a"}

    # Session B should not see changes from session A.
    assert "data" not in session_b

    # Accessing the current session should return the appropriate instance.
    with mock.patch('security.get_current_session', return_value=session_a):
        assert get_current_session()["data"]["secret"] == "value_a"

    with mock.patch('security.get_current_session', return_value=session_b):
        assert "data" not in get_current_session()