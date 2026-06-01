"""Tests for SessionState transitions and serialization."""

from interface.session import SessionState


def _make() -> SessionState:
    return SessionState(
        session_id="s1",
        session_name="Test",
        source_type="meeting_notes",
        raw_input="some notes",
    )


def test_initial_state_is_running():
    session = _make()
    assert session.status == "running"
    assert session.completed_nodes == []
    assert session.error is None


def test_transition_to_awaiting_review():
    session = _make()
    session.completed_nodes.append("story_generation")
    session.generated_stories = [{"id": "US-001"}]
    session.status = "awaiting_review"
    assert session.status == "awaiting_review"
    assert session.generated_stories[0]["id"] == "US-001"


def test_transition_to_approved():
    session = _make()
    session.status = "approved"
    assert session.status == "approved"


def test_transition_reject_to_running():
    session = _make()
    session.status = "awaiting_review"
    session.status = "running"
    assert session.status == "running"


def test_status_dict_shape():
    session = _make()
    session.current_node = "story_generation"
    session.completed_nodes = ["requirements_extraction"]
    payload = session.to_status_dict()
    assert set(payload.keys()) == {"status", "current_node", "completed_nodes", "error"}
    assert payload["current_node"] == "story_generation"


def test_error_state():
    session = _make()
    session.status = "error"
    session.error = "boom"
    assert session.to_status_dict()["error"] == "boom"
