"""Route tests for the PO interface using FastAPI TestClient."""


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_empty(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "PO Workspace" in response.text


def test_new_session_form(client):
    response = client.get("/sessions/new")
    assert response.status_code == 200
    assert "Run requirements pipeline" in response.text


def test_run_creates_session_and_redirects(client):
    response = client.post(
        "/sessions/run",
        data={
            "session_name": "Test session",
            "source_type": "meeting_notes",
            "raw_input": "We need login.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/progress" in response.headers["location"]


def test_status_after_run(client):
    client.post(
        "/sessions/run",
        data={"session_name": "S", "source_type": "other", "raw_input": "x"},
        follow_redirects=False,
    )
    from po_agent_workspace.interface.session import sessions

    session_id = next(iter(sessions))
    status = client.get(f"/sessions/{session_id}/status").json()
    assert status["status"] == "awaiting_review"
    assert "story_generation" in status["completed_nodes"]


def test_status_not_found(client):
    assert client.get("/sessions/nope/status").status_code == 404


def test_review_page_ready(client):
    client.post(
        "/sessions/run",
        data={"session_name": "S", "source_type": "other", "raw_input": "x"},
        follow_redirects=False,
    )
    from po_agent_workspace.interface.session import sessions

    session_id = next(iter(sessions))
    response = client.get(f"/sessions/{session_id}/review")
    assert response.status_code == 200
    assert "US-001" in response.text


def test_review_not_ready_message(client):
    from po_agent_workspace.interface.session import SessionState, sessions

    s = SessionState(
        session_id="abc", session_name="N", source_type="other", raw_input="x"
    )
    s.status = "running"
    sessions["abc"] = s
    response = client.get("/sessions/abc/review")
    assert "not ready for review" in response.text


def test_approve_publishes_backlog(client):
    client.post(
        "/sessions/run",
        data={"session_name": "S", "source_type": "other", "raw_input": "x"},
        follow_redirects=False,
    )
    from po_agent_workspace.interface.session import sessions

    session_id = next(iter(sessions))
    response = client.post(
        f"/sessions/{session_id}/approve",
        json={
            "approved_stories": [{"id": "US-001", "title": "Login"}],
            "feedback": None,
        },
    )
    assert response.json() == {"status": "approved", "redirect": "/backlog"}

    backlog = client.get("/backlog")
    assert backlog.status_code == 200
    assert "US-001" in backlog.text


def test_approve_requires_stories(client):
    client.post(
        "/sessions/run",
        data={"session_name": "S", "source_type": "other", "raw_input": "x"},
        follow_redirects=False,
    )
    from po_agent_workspace.interface.session import sessions

    session_id = next(iter(sessions))
    response = client.post(
        f"/sessions/{session_id}/approve",
        json={"approved_stories": [], "feedback": None},
    )
    assert response.status_code == 400


def test_reject_sets_running(client):
    client.post(
        "/sessions/run",
        data={"session_name": "S", "source_type": "other", "raw_input": "x"},
        follow_redirects=False,
    )
    from po_agent_workspace.interface.session import sessions

    session_id = next(iter(sessions))
    response = client.post(f"/sessions/{session_id}/reject", json={"feedback": "redo"})
    assert response.json()["status"] == "rejected"
    assert sessions[session_id].status == "running"


def test_backlog_csv_export(client):
    _publish_backlog(client)
    response = client.get("/backlog/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "US-001" in response.text


def test_backlog_markdown_export(client):
    _publish_backlog(client)
    response = client.get("/backlog/export/markdown")
    assert response.status_code == 200
    assert "# Product Backlog" in response.text


def _publish_backlog(client):
    client.post(
        "/sessions/run",
        data={"session_name": "S", "source_type": "other", "raw_input": "x"},
        follow_redirects=False,
    )
    from po_agent_workspace.interface.session import sessions

    session_id = next(iter(sessions))
    client.post(
        f"/sessions/{session_id}/approve",
        json={
            "approved_stories": [
                {
                    "id": "US-001",
                    "title": "Login",
                    "description": "d",
                    "priority": "high",
                    "story_points": 5,
                    "theme": "Auth",
                    "acceptance_criteria": ["works"],
                }
            ],
            "feedback": None,
        },
    )
