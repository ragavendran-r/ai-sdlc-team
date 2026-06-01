"""Tests for UX interface session state transitions."""

from interface.session import UXSessionState


def test_initial_status_running():
    s = UXSessionState(session_id="s1", session_name="n")
    assert s.status == "running"


def test_to_status_dict_keys():
    s = UXSessionState(session_id="s1", session_name="n")
    d = s.to_status_dict()
    assert set(d) == {"status", "current_node", "completed_nodes", "error"}


def test_awaiting_review_transition():
    s = UXSessionState(session_id="s1", session_name="n")
    s.status = "awaiting_review"
    s.personas = [{"id": "P-1"}]
    assert s.status == "awaiting_review"
    assert s.personas[0]["id"] == "P-1"


def test_completed_nodes_tracking():
    s = UXSessionState(session_id="s1", session_name="n")
    s.completed_nodes.append("story_intake")
    s.completed_nodes.append("persona_agent")
    assert len(s.completed_nodes) == 2
