"""Pytest fixtures for the UX interface tests.

The fixtures swap the workflow runner for fakes so tests never call the real
LangGraph workflow or the Anthropic API, and point the context store at a temp
dir so artifacts never touch the real store.
"""

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def sample_sprint_plan():
    return {
        "sprint": {
            "id": "SPRINT-1",
            "name": "Sprint 1",
            "tasks": [
                {
                    "id": "T-001",
                    "user_story_id": "US-1",
                    "title": "Login form",
                    "description": "Login UI",
                }
            ],
        },
        "user_stories": {
            "US-1": {
                "id": "US-1",
                "title": "Login with email",
                "description": "As a user I want to log in to my account",
            }
        },
    }


def _sample_personas():
    return [
        {
            "id": "P-1",
            "name": "Casual Carol",
            "role": "Customer",
            "goals": ["Log in quickly"],
            "pain_points": ["Forgets passwords"],
        }
    ]


def _sample_flows():
    # Shapes match team_contracts.schemas.UserFlow.to_dict().
    return [
        {
            "id": "F-1",
            "user_story_id": "US-1",
            "persona_id": "P-1",
            "title": "Login flow",
            "description": "User logs in",
            "entry_point": "Landing page",
            "steps": [
                {
                    "step_number": 1,
                    "action": "Open login",
                    "system_response": "Show form",
                    "screen_or_state": "Login",
                },
            ],
            "exit_point": "Dashboard",
        }
    ]


def _sample_wireframes():
    # Shapes match team_contracts.schemas.WireframeBrief.to_dict().
    return [
        {
            "id": "W-1",
            "screen_name": "Login screen",
            "user_flow_id": "F-1",
            "layout_type": "form",
            "purpose": "Authenticate the user",
            "description": "Centered form",
            "components": [
                {"component_name": "EmailField", "purpose": "Capture email"},
                {"component_name": "PasswordField", "purpose": "Capture password"},
            ],
        }
    ]


@pytest.fixture
def client(tmp_path, monkeypatch, sample_sprint_plan):
    """TestClient with workflow_runner faked and context store in tmp_path."""
    monkeypatch.setenv("CONTEXT_STORE_PATH", str(tmp_path / "context-store"))

    from ux_agent_workspace.interface import app as app_module

    importlib.reload(app_module)
    app_module.sessions.clear()

    # Seed the EM sprint plan so UX has input.
    app_module.context_store.write_artifact(
        key="sprint-plan",
        data=sample_sprint_plan,
        workflow="em",
        artifact_type="sprint-plan",
    )

    # Keep the real story-extraction helper so the route can call it.
    real_sprint_plan_stories = app_module.workflow_runner.sprint_plan_stories

    def fake_start_session(session, story_dicts):
        session.personas = _sample_personas()
        session.user_flows = _sample_flows()
        session.wireframe_briefs = _sample_wireframes()
        session.a11y_flags = ["Low contrast on submit button (high)"]
        session.status = "awaiting_review"

    def fake_approve(session, context_store, event_bus):
        context_store.write_artifact(
            key="ux-handoff",
            data={
                "personas": session.personas,
                "user_flows": session.user_flows,
                "wireframe_briefs": session.wireframe_briefs,
            },
            workflow="ux",
            artifact_type="ux-handoff",
        )
        session.status = "approved"

    def fake_reject(session, feedback):
        session.status = "running"

    monkeypatch.setattr(
        "ux_agent_workspace.interface.workflow_runner.sprint_plan_stories", real_sprint_plan_stories
    )
    monkeypatch.setattr("ux_agent_workspace.interface.workflow_runner.start_session", fake_start_session)
    monkeypatch.setattr("ux_agent_workspace.interface.workflow_runner.approve", fake_approve)
    monkeypatch.setattr("ux_agent_workspace.interface.workflow_runner.reject", fake_reject)

    from ux_agent_workspace.interface.app import app

    return TestClient(app)
