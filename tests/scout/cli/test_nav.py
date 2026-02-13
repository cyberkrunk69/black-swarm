"""
Tests for scout-nav CLI — navigation, file Q&A, output formats, validation flows.
"""

import asyncio
import json
from pathlib import Path
import pytest

from vivarium.scout.audit import AuditLog
from vivarium.scout.cli import nav
from vivarium.scout.config import ScoutConfig
from vivarium.scout.llm import NavResponse
from vivarium.scout.router import TriggerRouter


# --- Fixtures ---


@pytest.fixture
def tmp_repo(tmp_path):
    """Temp repo with python files."""
    (tmp_path / "vivarium" / "scout" / "cli").mkdir(parents=True)
    (tmp_path / "vivarium" / "scout" / "router.py").write_text(
        "def main(): pass\n\ndef refresh_token(): pass\n"
    )
    (tmp_path / "vivarium" / "scout" / "validator.py").write_text("def validate(): pass\n")
    return tmp_path


@pytest.fixture
def audit_path(tmp_path):
    return tmp_path / "audit.jsonl"


@pytest.fixture
def mock_llm_valid():
    """Mock LLM returning valid navigation suggestion."""

    async def _mock(prompt, model="llama-3.1-8b-instant", system=None, max_tokens=500, **kwargs):
        return NavResponse(
            content=json.dumps({
                "file": "vivarium/scout/router.py",
                "function": "main",
                "line": 1,
                "confidence": 92,
                "reasoning": "Token refresh handles timeout",
                "suggestion": "Check Redis WATCH/MULTI",
            }),
            cost_usd=0.0006,
            model=model,
            input_tokens=100,
            output_tokens=50,
        )

    return _mock


@pytest.fixture
def mock_llm_file_qa():
    """Mock LLM for file Q&A mode."""

    async def _mock(prompt, model="llama-3.1-8b-instant", system=None, max_tokens=500, **kwargs):
        return NavResponse(
            content=json.dumps({
                "file": "vivarium/scout/router.py",
                "line": 3,
                "function": "refresh_token",
                "explanation": "Token refresh is at line 3",
            }),
            cost_usd=0.0002,
            model=model,
            input_tokens=80,
            output_tokens=30,
        )

    return _mock


# --- Basic navigation ---


def test_basic_navigation(tmp_repo, audit_path, mock_llm_valid):
    """Basic navigation with --task returns target file and function."""
    router = TriggerRouter(
        config=ScoutConfig(search_paths=[]),  # Defaults only, no user config
        audit=AuditLog(path=audit_path),
        repo_root=tmp_repo,
    )
    result = asyncio.run(router.navigate_task(
        task="fix auth timeout bug",
        llm_client=mock_llm_valid,
    ))
    assert result is not None
    assert result["task"] == "fix auth timeout bug"
    assert "vivarium/scout/router.py" in result["target_file"]
    assert result["target_function"] == "main"
    assert result["confidence"] >= 90
    assert result["cost_usd"] > 0
    assert result["session_id"]


def test_with_entry_point(tmp_repo, audit_path, mock_llm_valid):
    """Navigation with --entry scopes file list."""
    router = TriggerRouter(
        config=ScoutConfig(search_paths=[]),
        audit=AuditLog(path=audit_path),
        repo_root=tmp_repo,
    )
    result = asyncio.run(router.navigate_task(
        task="find main function",
        entry=Path("vivarium/scout"),
        llm_client=mock_llm_valid,
    ))
    assert result is not None
    assert result["target_file"]
    assert result["target_function"] == "main"


def test_file_qa_mode(tmp_repo, mock_llm_file_qa):
    """File-specific Q&A mode answers question about file."""
    from vivarium.scout.validator import Validator

    file_path = tmp_repo / "vivarium" / "scout" / "router.py"
    validator = Validator()
    result = asyncio.run(nav.query_file(
        file_path=file_path,
        question="where is token refresh?",
        repo_root=tmp_repo,
        validator=validator,
        llm_client=mock_llm_file_qa,
    ))
    assert result["file"]
    assert "answer" in result
    assert result["cost"] > 0
    assert result["target_function"] == "refresh_token"


def test_file_qa_mode_with_validator(tmp_repo, mock_llm_file_qa):
    """File Q&A mode uses validator."""
    from vivarium.scout.validator import Validator

    file_path = tmp_repo / "vivarium" / "scout" / "router.py"
    validator = Validator()
    result = asyncio.run(nav.query_file(
        file_path=file_path,
        question="where is token refresh?",
        repo_root=tmp_repo,
        validator=validator,
        llm_client=mock_llm_file_qa,
    ))
    assert "validated" in result
    assert result["line_estimate"] == 3


def test_json_output(tmp_repo, audit_path, mock_llm_valid):
    """Result dict has JSON-serializable structure for --json output."""
    router = TriggerRouter(
        config=ScoutConfig(search_paths=[]),
        audit=AuditLog(path=audit_path),
        repo_root=tmp_repo,
    )
    result = asyncio.run(router.navigate_task(
        task="fix bug",
        llm_client=mock_llm_valid,
    ))
    assert result is not None
    # JSON round-trip
    serialized = json.dumps(result, indent=2)
    parsed = json.loads(serialized)
    assert parsed["task"] == "fix bug"
    assert "target_file" in parsed
    assert "cost_usd" in parsed


def test_output_to_file(tmp_repo, audit_path, mock_llm_valid):
    """--output saves briefing to file."""
    from vivarium.scout.audit import AuditLog

    async def run():
        router = TriggerRouter(
            config=ScoutConfig(search_paths=[]),
            audit=AuditLog(path=audit_path),
            repo_root=tmp_repo,
        )
        result = await router.navigate_task(
            task="fix bug",
            llm_client=mock_llm_valid,
        )
        if result:
            brief = await nav.generate_brief(result, "fix bug")
            (tmp_repo / "briefing.md").write_text(brief)
        return 0

    asyncio.run(run())
    brief_path = tmp_repo / "briefing.md"
    assert brief_path.exists()
    content = brief_path.read_text()
    assert "Scout Briefing" in content
    assert "fix bug" in content


def test_validation_failure_and_retry(tmp_repo, audit_path):
    """Validation failure triggers retry with alternatives."""
    call_count = 0

    async def mock_invalid_then_valid(prompt, model="llama-3.1-8b-instant", system=None, max_tokens=500, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return NavResponse(
                content=json.dumps({
                    "file": "vivarium/scout/nonexistent.py",
                    "function": "main",
                    "line": 1,
                    "confidence": 90,
                    "reasoning": "x",
                    "suggestion": "y",
                }),
                cost_usd=0.0002,
                model=model,
                input_tokens=100,
                output_tokens=50,
            )
        return NavResponse(
            content=json.dumps({
                "file": "vivarium/scout/router.py",
                "function": "main",
                "line": 1,
                "confidence": 92,
                "reasoning": "x",
                "suggestion": "y",
            }),
            cost_usd=0.0002,
            model=model,
            input_tokens=100,
            output_tokens=50,
        )

    router = TriggerRouter(
        config=ScoutConfig(search_paths=[]),
        audit=AuditLog(path=audit_path),
        repo_root=tmp_repo,
    )
    result = asyncio.run(router.navigate_task(
        task="fix bug",
        llm_client=mock_invalid_then_valid,
    ))
    assert result is not None
    assert call_count >= 2
    assert "vivarium/scout/router.py" in result["target_file"]


def test_escalation_to_70b(tmp_repo, audit_path):
    """Persistent validation failure escalates to 70B model."""
    async def mock_always_invalid(prompt, model="llama-3.1-8b-instant", system=None, max_tokens=500, **kwargs):
        return NavResponse(
            content=json.dumps({
                "file": "vivarium/scout/hallucinated.py",
                "function": "main",
                "line": 1,
                "confidence": 85,
                "reasoning": "x",
                "suggestion": "y",
            }),
            cost_usd=0.0002 if "8b" in model else 0.0009,
            model=model,
            input_tokens=100,
            output_tokens=50,
        )

    router = TriggerRouter(
        config=ScoutConfig(search_paths=[]),
        audit=AuditLog(path=audit_path),
        repo_root=tmp_repo,
    )
    result = asyncio.run(router.navigate_task(
        task="fix bug",
        llm_client=mock_always_invalid,
    ))
    assert result is not None
    assert result["escalated"] is True
    assert "70b" in result["model_used"].lower()


def test_cost_reporting_accuracy(tmp_repo, audit_path, mock_llm_valid):
    """Cost is reported and matches LLM response."""
    router = TriggerRouter(
        config=ScoutConfig(search_paths=[]),
        audit=AuditLog(path=audit_path),
        repo_root=tmp_repo,
    )
    result = asyncio.run(router.navigate_task(
        task="fix bug",
        llm_client=mock_llm_valid,
    ))
    assert result is not None
    assert result["cost_usd"] > 0
    assert result["cost_usd"] < 0.01  # Single 8B call should be cheap
    assert result["duration_ms"] >= 0


def test_cost_limit_respected(tmp_repo, audit_path, mock_llm_valid):
    """When cost limit exceeded, navigate_task returns None."""
    config = ScoutConfig(search_paths=[])
    config.set("limits.max_cost_per_event", 0.00001)  # Very low
    config.set("limits.hourly_budget", 0.0001)

    router = TriggerRouter(
        config=config,
        audit=AuditLog(path=audit_path),
        repo_root=tmp_repo,
    )
    result = asyncio.run(router.navigate_task(
        task="fix bug",
        llm_client=mock_llm_valid,
    ))
    assert result is None


def test_print_pretty(tmp_repo):
    """print_pretty produces structured output."""
    result = {
        "task": "fix auth",
        "target_file": "vivarium/runtime/auth.py",
        "target_function": "refresh_token",
        "line_estimate": 67,
        "signature": "async def refresh_token(...)",
        "confidence": 92,
        "model_used": "llama-3.1-8b-instant",
        "cost_usd": 0.0006,
        "duration_ms": 1200,
        "retries": 0,
        "escalated": False,
        "reasoning": "Token refresh handles timeout",
        "suggestion": "Check Redis WATCH/MULTI",
        "related_files": [],
    }
    nav.print_pretty(result)
    # No assertion needed — just ensure no exception


def test_parse_args(monkeypatch):
    """parse_args handles CLI arguments."""
    monkeypatch.setattr("sys.argv", ["scout-nav", "--task", "fix bug", "--json"])
    args = nav.parse_args()
    assert args.task == "fix bug"
    assert args.json is True
