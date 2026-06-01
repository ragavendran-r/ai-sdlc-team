"""Route tests for the EM web interface."""

from interface.session import EMSessionState, sessions


def _seed_awaiting():
    """Create a session in awaiting_review with a draft sprint, via the registry."""
    session = EMSessionState(
        session_id="sess-1",
        session_name="Sprint 1",
        sprint_goal="Ship auth",
    )
    session.status = "awaiting_review"
    session.draft_sprint = {
        "sprint": {
            "id": "SPRINT-1",
            "name": "Sprint 1",
            "tasks": [
                {
                    "id": "T-001",
                    "title": "Build login form",
                    "description": "Login form UI",
                    "assigned_to": "frontend-agent",
                    "task_type": "frontend",
                    "estimated_hours": 8,
                }
            ],
        }
    }
    session.capacity_report = {"estimated_story_points_capacity": 30, "team_size": 5}
    session.risk_flags = ["Tight timeline (high)"]
    sessions[session.session_id] = session
    return session


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_home_shows_backlog_ready(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "EM Workspace" in r.text
    assert "Backlog ready" in r.text


def test_sprint_plan_form(client):
    r = client.get("/sprint/plan")
    assert r.status_code == 200
    assert "session_name" in r.text


def test_sprint_run_redirects_to_progress(client):
    r = client.post(
        "/sprint/run",
        data={"session_name": "Sprint 1", "sprint_goal": "Ship auth"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "/progress" in r.headers["location"]


def test_progress_page_renders(client):
    _seed_awaiting()
    r = client.get("/sprint/sess-1/progress")
    assert r.status_code == 200
    assert "Sprint 1" in r.text


def test_status_json(client):
    _seed_awaiting()
    r = client.get("/sprint/sess-1/status")
    assert r.status_code == 200
    assert r.json()["status"] == "awaiting_review"


def test_status_json_not_found(client):
    r = client.get("/sprint/nope/status")
    assert r.status_code == 404


def test_review_page_shows_tasks(client):
    _seed_awaiting()
    r = client.get("/sprint/sess-1/review")
    assert r.status_code == 200
    assert "Build login form" in r.text


def test_approve_publishes_sprint_plan(client):
    _seed_awaiting()
    r = client.post("/sprint/sess-1/approve", json={})
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
    # Sprint plan artifact should now exist; dashboard should show tasks.
    d = client.get("/sprint/dashboard")
    assert "Build login form" in d.text


def test_approve_requires_awaiting(client):
    session = EMSessionState(session_id="sess-2", session_name="S2", sprint_goal="")
    session.status = "running"
    sessions[session.session_id] = session
    r = client.post("/sprint/sess-2/approve", json={})
    assert r.status_code == 400


def test_reject_sets_running(client):
    _seed_awaiting()
    r = client.post("/sprint/sess-1/reject", json={"feedback": "Too big"})
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_dashboard_empty(client):
    r = client.get("/sprint/dashboard")
    assert r.status_code == 200


def test_report_regenerate_requires_plan(client):
    r = client.post("/sprint/report/regenerate")
    assert r.status_code == 400


def test_report_regenerate_after_approve(client):
    _seed_awaiting()
    client.post("/sprint/sess-1/approve", json={})
    r = client.post("/sprint/report/regenerate")
    assert r.status_code == 200
    assert r.json()["status"] == "regenerated"


def test_report_download(client):
    _seed_awaiting()
    client.post("/sprint/sess-1/approve", json={})
    r = client.get("/sprint/report/download")
    assert r.status_code == 200
    assert "text/markdown" in r.headers["content-type"]


def test_not_found_page(client):
    r = client.get("/sprint/does-not-exist/progress")
    assert r.status_code == 404
