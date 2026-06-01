"""Route tests for the UX web interface."""

from interface.session import UXSessionState, sessions


def _seed_awaiting():
    session = UXSessionState(session_id="sess-1", session_name="Checkout redesign")
    session.status = "awaiting_review"
    session.personas = [
        {"id": "P-1", "name": "Casual Carol", "role": "Customer", "goals": ["Log in"]}
    ]
    session.user_flows = [
        {
            "id": "F-1",
            "title": "Login flow",
            "description": "Logs in",
            "steps": [
                {
                    "step_number": 1,
                    "action": "Open login",
                    "system_response": "Show form",
                }
            ],
        }
    ]
    session.wireframe_briefs = [
        {
            "id": "W-1",
            "screen_name": "Login screen",
            "user_flow_id": "F-1",
            "layout_type": "form",
            "purpose": "Authenticate the user",
            "description": "Centered form",
            "components": [
                {"component_name": "EmailField", "purpose": "Capture email"}
            ],
        }
    ]
    sessions[session.session_id] = session
    return session


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_home_shows_sprint_ready(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "UX Workspace" in r.text
    assert "Sprint plan ready" in r.text


def test_new_session_form(client):
    r = client.get("/sessions/new")
    assert r.status_code == 200
    assert "session_name" in r.text


def test_run_redirects_to_progress(client):
    r = client.post(
        "/sessions/run",
        data={"session_name": "Checkout redesign"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "/progress" in r.headers["location"]


def test_status_json(client):
    _seed_awaiting()
    r = client.get("/sessions/sess-1/status")
    assert r.status_code == 200
    assert r.json()["status"] == "awaiting_review"


def test_status_not_found(client):
    assert client.get("/sessions/nope/status").status_code == 404


def test_review_three_tabs(client):
    _seed_awaiting()
    r = client.get("/sessions/sess-1/review")
    assert r.status_code == 200
    assert "Casual Carol" in r.text
    assert "Login flow" in r.text
    assert "Login screen" in r.text
    # Real schema fields render: flow step action, wireframe component name + purpose.
    assert "Open login" in r.text
    assert "EmailField" in r.text
    assert "Authenticate the user" in r.text


def test_approve_publishes_handoff(client):
    _seed_awaiting()
    r = client.post("/sessions/sess-1/approve", json={})
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
    assert "/summary" in r.json()["redirect"]


def test_approve_requires_awaiting(client):
    session = UXSessionState(session_id="sess-2", session_name="S2")
    session.status = "running"
    sessions[session.session_id] = session
    r = client.post("/sessions/sess-2/approve", json={})
    assert r.status_code == 400


def test_reject_sets_running(client):
    _seed_awaiting()
    r = client.post("/sessions/sess-1/reject", json={"feedback": "Add empty states"})
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_summary_page(client):
    s = _seed_awaiting()
    s.status = "approved"
    r = client.get("/sessions/sess-1/summary")
    assert r.status_code == 200
    assert "UX handoff" in r.text


def test_export_markdown(client):
    _seed_awaiting()
    r = client.get("/sessions/sess-1/export/markdown")
    assert r.status_code == 200
    assert "text/markdown" in r.headers["content-type"]
    assert "Casual Carol" in r.text


def test_export_csv(client):
    _seed_awaiting()
    r = client.get("/sessions/sess-1/export/csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "Login screen" in r.text
    # Header uses the real WireframeBrief field names.
    assert "screen_name" in r.text
    assert "layout_type" in r.text


def test_renders_real_schema_objects(client):
    """Drive the review page + exports with dicts produced by the real
    team_contracts schema .to_dict(), not hand-shaped fixtures, to prove the
    interface stays aligned with the actual UX schema."""
    from team_contracts.schemas.user_flow import FlowStep, UserFlow
    from team_contracts.schemas.user_persona import UserPersona
    from team_contracts.schemas.wireframe_brief import (
        ComponentRequirement,
        WireframeBrief,
    )

    persona = UserPersona(
        id="P-9",
        name="Power Paula",
        demographic_summary="35, ops lead",
        role="Operations Lead",
        goals=["Bulk edit records"],
        pain_points=["Too many clicks"],
        created_by="ux-agent",
    )
    flow = UserFlow(
        id="F-9",
        user_story_id="US-9",
        persona_id="P-9",
        title="Bulk edit flow",
        description="Select many and edit",
        entry_point="Records table",
        steps=[
            FlowStep(
                step_number=1,
                action="Select rows",
                system_response="Highlight selection",
            )
        ],
        exit_point="Changes saved",
        created_by="ux-agent",
    )
    brief = WireframeBrief(
        id="W-9",
        screen_name="Bulk edit panel",
        user_flow_id="F-9",
        purpose="Edit many records at once",
        description="Side panel with shared fields",
        components=[
            ComponentRequirement(component_name="FieldList", purpose="Editable fields")
        ],
        layout_type="side-panel",
        created_by="ux-agent",
    )

    session = UXSessionState(session_id="sess-real", session_name="Bulk edit")
    session.status = "awaiting_review"
    session.personas = [persona.to_dict()]
    session.user_flows = [flow.to_dict()]
    session.wireframe_briefs = [brief.to_dict()]
    sessions[session.session_id] = session

    review = client.get("/sessions/sess-real/review")
    assert review.status_code == 200
    assert "Power Paula" in review.text
    assert "Bulk edit flow" in review.text
    assert "Select rows" in review.text  # FlowStep.action
    assert "Bulk edit panel" in review.text  # WireframeBrief.screen_name
    assert "side-panel" in review.text  # WireframeBrief.layout_type
    assert "FieldList" in review.text  # ComponentRequirement.component_name

    md = client.get("/sessions/sess-real/export/markdown")
    assert "Bulk edit flow" in md.text
    assert "Bulk edit panel" in md.text
    assert "FieldList" in md.text

    csv_resp = client.get("/sessions/sess-real/export/csv")
    assert "Bulk edit panel" in csv_resp.text
    assert "side-panel" in csv_resp.text


def test_not_found_page(client):
    r = client.get("/sessions/does-not-exist/progress")
    assert r.status_code == 404
