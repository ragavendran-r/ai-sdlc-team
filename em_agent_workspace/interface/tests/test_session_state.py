"""Tests for EM interface session state transitions."""

from interface.session import EMSessionState


def test_initial_status_running():
    s = EMSessionState(session_id="s1", session_name="n", sprint_goal="g")
    assert s.status == "running"


def test_to_status_dict_keys():
    s = EMSessionState(session_id="s1", session_name="n", sprint_goal="g")
    d = s.to_status_dict()
    assert set(d) == {"status", "current_node", "completed_nodes", "error"}


def test_awaiting_review_transition():
    s = EMSessionState(session_id="s1", session_name="n", sprint_goal="g")
    s.status = "awaiting_review"
    assert s.status == "awaiting_review"


def test_completed_nodes_tracking():
    s = EMSessionState(session_id="s1", session_name="n", sprint_goal="g")
    s.completed_nodes.append("backlog_intake")
    s.completed_nodes.append("sprint_composition")
    assert len(s.completed_nodes) == 2
