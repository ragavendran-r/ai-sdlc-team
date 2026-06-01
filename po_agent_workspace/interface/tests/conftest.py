"""Fixtures for PO interface tests.

The compiled LangGraph workflow makes Anthropic API calls, so tests patch the
workflow_runner functions to drive session state transitions directly without
running the real graph.
"""

import sys
from pathlib import Path

import pytest

# Make the workspace importable as the app expects (interface.app, agents.*).
_WORKSPACE = Path(__file__).resolve().parents[2]
if str(_WORKSPACE) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE))


@pytest.fixture
def sample_user_stories():
    return [
        {
            "id": "US-001",
            "title": "Email and password login",
            "description": "Users can log in with email and password.",
            "priority": "high",
            "story_points": 5,
            "theme": "Authentication",
            "acceptance_criteria": ["Valid credentials succeed", "Invalid show error"],
        },
        {
            "id": "US-002",
            "title": "OAuth login",
            "description": "Users can log in with Google or GitHub.",
            "priority": "medium",
            "story_points": 8,
            "theme": "Authentication",
            "acceptance_criteria": ["Google OAuth works"],
        },
    ]


@pytest.fixture
def client(monkeypatch, tmp_path, sample_user_stories):
    """A TestClient with the workflow runner stubbed and an isolated store."""
    monkeypatch.setenv("CONTEXT_STORE_PATH", str(tmp_path / "context-store"))

    # Import after env is set so the module-level ContextStore uses tmp_path.
    import importlib

    from interface import app as app_module

    importlib.reload(app_module)

    from interface import session as session_module

    session_module.sessions.clear()

    def fake_start(session):
        # Simulate the workflow pausing for review immediately.
        session.completed_nodes = [
            "stakeholder_interview",
            "requirements_extraction",
            "ambiguity_detection",
            "conflict_detection",
            "story_generation",
        ]
        session.current_node = "story_generation"
        session.generated_stories = sample_user_stories
        session.ambiguity_flags = ["SR-003: 'fast' is not measurable"]
        session.conflict_flags = []
        session.status = "awaiting_review"

    def fake_approve(session, approved_stories, context_store, event_bus):
        context_store.write_artifact(
            key="backlog",
            data={"stories": approved_stories, "themes": ["Authentication"]},
            workflow="po",
            artifact_type="backlog",
        )
        session.status = "approved"

    def fake_reject(session, feedback):
        session.status = "running"

    monkeypatch.setattr(app_module.workflow_runner, "start_session", fake_start)
    monkeypatch.setattr(app_module.workflow_runner, "approve", fake_approve)
    monkeypatch.setattr(app_module.workflow_runner, "reject", fake_reject)

    from fastapi.testclient import TestClient

    return TestClient(app_module.app)
