"""Background execution of the PO LangGraph workflow for the web interface.

The workflow is compiled with a checkpointer and an interrupt before the
story-generation checkpoint (compile_po_workflow_web). This module runs it in a
thread pool, streams node progress into the SessionState, pauses at the
interrupt for human review, and resumes on approve/reject.

Cross-process note: each interface process owns its own EventBus, so events
published here are local. Real cross-workspace handoff happens via the shared
context store on disk (the backlog artifact written on approval).
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List

from po_agent_workspace.agents import PoWorkflowState, compile_po_workflow_web

from team_orchestrator import ContextStore, Event, EventBus, EventSeverity, EventType

from .session import SessionState

# Single worker pool shared by all sessions in this process.
_executor = ThreadPoolExecutor(max_workers=4)

# One compiled web workflow (with MemorySaver checkpointer) reused across
# sessions; sessions are isolated by thread_id in the run config.
_compiled = None


def _get_compiled():
    global _compiled
    if _compiled is None:
        _compiled = compile_po_workflow_web()
    return _compiled


def _config(session_id: str) -> Dict[str, Any]:
    return {"configurable": {"thread_id": session_id}}


def _extract_flag_strings(state_values: Dict[str, Any]) -> tuple:
    """Turn structured ambiguity/conflict flags into display strings."""
    ambiguity = []
    for flag in state_values.get("ambiguity_flags", []) or []:
        if isinstance(flag, dict):
            req = flag.get("requirement_id", "")
            issue = flag.get("issue", "")
            ambiguity.append(f"{req}: {issue}".strip(": "))
        else:
            ambiguity.append(str(flag))

    conflict = []
    for flag in state_values.get("conflict_flags", []) or []:
        if isinstance(flag, dict):
            ids = ", ".join(flag.get("requirement_ids", []) or [])
            desc = flag.get("description", flag.get("conflict_type", ""))
            conflict.append(f"{ids}: {desc}".strip(": "))
        else:
            conflict.append(str(flag))

    return ambiguity, conflict


def _state_values(compiled, session_id: str) -> Dict[str, Any]:
    """Read the current checkpointed state values as a dict."""
    snapshot = compiled.get_state(_config(session_id))
    values = snapshot.values
    # LangGraph may hold the state as a dataclass or a dict depending on version.
    if hasattr(values, "to_dict"):
        return values.to_dict()
    if isinstance(values, dict):
        return values
    return dict(values)


def start_session(session: SessionState) -> None:
    """Submit a session to run in the background up to the review interrupt."""
    _executor.submit(_run_until_interrupt, session)


def _run_until_interrupt(session: SessionState) -> None:
    try:
        compiled = _get_compiled()
        initial = PoWorkflowState(
            interview_notes=session.raw_input,
            web_mode=True,
        )
        for step in compiled.stream(initial, _config(session.session_id)):
            # Each streamed step is {node_name: state_update}.
            for node_name in step.keys():
                session.current_node = node_name
                if node_name not in session.completed_nodes:
                    session.completed_nodes.append(node_name)

        # Stream ended at the interrupt before checkpoint_story_generation.
        values = _state_values(compiled, session.session_id)
        session.generated_stories = values.get("generated_stories", []) or []
        ambiguity, conflict = _extract_flag_strings(values)
        session.ambiguity_flags = ambiguity
        session.conflict_flags = conflict
        session.status = "awaiting_review"
    except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
        session.status = "error"
        session.error = str(exc)


def approve(
    session: SessionState,
    approved_stories: List[Dict[str, Any]],
    context_store: ContextStore,
    event_bus: EventBus,
) -> None:
    """Resume the paused workflow with approved stories and publish the backlog."""
    compiled = _get_compiled()
    config = _config(session.session_id)

    compiled.update_state(
        config,
        {"generated_stories": approved_stories, "stories_approved": True},
    )
    # Resume from the interrupt; runs through to END (backlog checkpoint
    # auto-approves in web mode).
    final = compiled.invoke(None, config)

    values = final.to_dict() if hasattr(final, "to_dict") else dict(final)

    backlog = {
        "stories": approved_stories,
        "themes": values.get("themes", []),
        "groomed_backlog": values.get("groomed_backlog", []),
        "session_name": session.session_name,
        "published_at": datetime.utcnow().isoformat(),
    }
    context_store.write_artifact(
        key="backlog",
        data=backlog,
        workflow="po",
        artifact_type="backlog",
    )

    _publish(event_bus, EventType.USER_STORIES_CREATED, {"stories": approved_stories})
    _publish(
        event_bus, EventType.BACKLOG_PUBLISHED, {"story_count": len(approved_stories)}
    )

    session.status = "approved"
    session.completed_at = datetime.utcnow()


def reject(session: SessionState, feedback: str) -> None:
    """Resume the workflow back through story generation with feedback applied."""
    compiled = _get_compiled()
    config = _config(session.session_id)

    compiled.update_state(
        config,
        {"stories_approved": False, "approval_notes": feedback},
    )
    session.status = "running"
    # Re-run in the background; the graph loops to story_generation and
    # interrupts again for a fresh review.
    _executor.submit(_resume_after_reject, session)


def _resume_after_reject(session: SessionState) -> None:
    try:
        compiled = _get_compiled()
        config = _config(session.session_id)
        for step in compiled.stream(None, config):
            for node_name in step.keys():
                session.current_node = node_name
                if node_name not in session.completed_nodes:
                    session.completed_nodes.append(node_name)

        values = _state_values(compiled, session.session_id)
        session.generated_stories = values.get("generated_stories", []) or []
        ambiguity, conflict = _extract_flag_strings(values)
        session.ambiguity_flags = ambiguity
        session.conflict_flags = conflict
        session.status = "awaiting_review"
    except Exception as exc:  # noqa: BLE001
        session.status = "error"
        session.error = str(exc)


def _publish(
    event_bus: EventBus, event_type: EventType, payload: Dict[str, Any]
) -> None:
    event_bus.publish(
        Event(
            event_type=event_type,
            workflow="po",
            severity=EventSeverity.INFO,
            payload=payload,
            source_agent="po-interface",
        )
    )
