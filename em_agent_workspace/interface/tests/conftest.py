"""Pytest fixtures for the EM interface tests.

The fixtures swap the workflow runner for fakes so tests never call the real
LangGraph workflow or the Anthropic API, and point the context store at a temp
dir so artifacts never touch the real store.
"""

import importlib

import pytest
from fastapi.testclient import TestClient


def _sample_draft_sprint():
    return {
        "sprint": {
            "id": "SPRINT-1",
            "name": "Sprint 1",
            "goal": "Ship auth",
            "tasks": [
                {
                    "id": "T-001",
                    "user_story_id": "US-1",
                    "title": "Build login form",
                    "description": "Login form UI",
                    "assigned_to": "frontend-agent",
                    "task_type": "frontend",
                    "estimated_hours": 8,
                    "acceptance_criteria": ["renders"],
                    "depends_on_tasks": [],
                    "status": "todo",
                }
            ],
        },
        "user_stories": {},
        "created_by": "em-agent",
    }


@pytest.fixture
def sample_backlog():
    return {
        "stories": [
            {
                "id": "US-1",
                "title": "Login with email",
                "description": "As a user I want to log in to my account",
                "acceptance_criteria": ["valid login works"],
                "priority": "high",
                "story_points": 3,
            }
        ]
    }


@pytest.fixture
def client(tmp_path, monkeypatch, sample_backlog):
    """TestClient with workflow_runner faked and context store in tmp_path."""
    monkeypatch.setenv("CONTEXT_STORE_PATH", str(tmp_path / "context-store"))

    # Import the app module fresh so it picks up the env var.
    from interface import app as app_module

    importlib.reload(app_module)

    # Reset the in-memory session registry.
    app_module.sessions.clear()

    # Seed the PO backlog so EM has input to plan from.
    app_module.context_store.write_artifact(
        key="backlog",
        data=sample_backlog,
        workflow="po",
        artifact_type="backlog",
    )

    # --- Fakes for the workflow runner ----------------------------------
    def fake_start_session(session, story_dicts):
        session.draft_sprint = _sample_draft_sprint()
        session.capacity_report = {
            "estimated_story_points_capacity": 30,
            "team_size": 5,
        }
        session.risk_flags = ["Tight timeline (high)"]
        session.status = "awaiting_review"

    def fake_approve(session, context_store, event_bus):
        draft = session.draft_sprint or _sample_draft_sprint()
        context_store.write_artifact(
            key="sprint-plan",
            data=draft,
            workflow="em",
            artifact_type="sprint-plan",
        )
        context_store.write_artifact(
            key="sprint-report",
            data={"report": "# Sprint Report\n\nDone."},
            workflow="em",
            artifact_type="sprint-report",
        )
        session.status = "approved"

    def fake_reject(session, feedback):
        session.status = "running"

    def fake_regenerate_report(context_store):
        context_store.write_artifact(
            key="sprint-report",
            data={"report": "# Sprint Report\n\nRegenerated."},
            workflow="em",
            artifact_type="sprint-report",
        )
        return "# Sprint Report\n\nRegenerated."

    monkeypatch.setattr("interface.workflow_runner.start_session", fake_start_session)
    monkeypatch.setattr("interface.workflow_runner.approve", fake_approve)
    monkeypatch.setattr("interface.workflow_runner.reject", fake_reject)
    monkeypatch.setattr(
        "interface.workflow_runner.regenerate_report", fake_regenerate_report
    )

    from interface.app import app

    return TestClient(app)
