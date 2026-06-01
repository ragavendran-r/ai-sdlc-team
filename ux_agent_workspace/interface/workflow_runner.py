"""Background execution of the UX LangGraph workflow for the web interface.

The workflow is compiled with a checkpointer and an interrupt before the
human_checkpoint node (compile_ux_workflow_web). This module runs it in a thread
pool, streams node progress into the UXSessionState, pauses at the interrupt for
human review of personas / flows / wireframe briefs, and resumes on approve/reject.

Cross-process note: each interface process owns its own EventBus, so events
published here are local. Real cross-workspace handoff happens via the shared
context store on disk: this workspace reads the EM `sprint-plan` artifact as
input and writes the `ux-handoff` artifact on approval.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List

from agents import UXWorkflowState, compile_ux_workflow_web

from team_contracts.schemas import UserStory
from team_orchestrator import ContextStore, Event, EventBus, EventSeverity, EventType

from .session import UXSessionState

# Single worker pool shared by all sessions in this process.
_executor = ThreadPoolExecutor(max_workers=4)

# One compiled web workflow (with MemorySaver checkpointer) reused across
# sessions; sessions are isolated by thread_id in the run config.
_compiled = None

_PRIORITY_VALUES = {"critical", "high", "medium", "low"}
_COMPLEXITY_VALUES = {"xs", "s", "m", "l", "xl"}


def _get_compiled():
    global _compiled
    if _compiled is None:
        _compiled = compile_ux_workflow_web()
    return _compiled


def _config(session_id: str) -> Dict[str, Any]:
    return {"configurable": {"thread_id": session_id}}


def sprint_plan_stories(sprint_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract story dicts from an EM sprint-plan artifact.

    The sprint plan carries `user_stories` as a dict keyed by story id; fall back
    to deriving story stubs from the sprint tasks when that map is empty.
    """
    if not sprint_plan:
        return []
    stories = list((sprint_plan.get("user_stories") or {}).values())
    if stories:
        return stories
    # Derive minimal stories from tasks so the UX graph has something to chew on.
    tasks = (sprint_plan.get("sprint") or {}).get("tasks", []) or []
    derived: Dict[str, Dict[str, Any]] = {}
    for task in tasks:
        sid = task.get("user_story_id") or task.get("id")
        if sid and sid not in derived:
            derived[sid] = {
                "id": sid,
                "title": task.get("title", sid),
                "description": task.get("description", ""),
            }
    return list(derived.values())


def to_user_stories(story_dicts: List[Dict[str, Any]]) -> List[UserStory]:
    """Convert sprint-plan story dicts into validated UserStory objects."""
    stories: List[UserStory] = []
    for i, raw in enumerate(story_dicts or [], start=1):
        title = (raw.get("title") or f"Story {i}").strip()
        if len(title) < 5:
            title = f"{title} story".ljust(5)
        description = (raw.get("description") or title).strip()
        if len(description) < 20:
            description = (description + " — details to be refined").ljust(20)

        priority = str(raw.get("priority") or "medium").lower()
        if priority not in _PRIORITY_VALUES:
            priority = "medium"

        complexity = str(raw.get("estimated_complexity") or "m").lower()
        if complexity not in _COMPLEXITY_VALUES:
            complexity = "m"

        criteria = raw.get("acceptance_criteria") or ["To be defined"]
        if not isinstance(criteria, list):
            criteria = [str(criteria)]

        stories.append(
            UserStory(
                id=raw.get("id") or f"US-{i:03d}",
                title=title,
                description=description,
                user_role=raw.get("user_role") or "User",
                user_goal=raw.get("user_goal") or title,
                business_value=raw.get("business_value") or "Delivers user value",
                acceptance_criteria=criteria,
                priority=priority,
                estimated_complexity=complexity,
                depends_on=raw.get("depends_on") or [],
                created_by=raw.get("created_by") or "po-agent",
            )
        )
    return stories


def _state_values(compiled, session_id: str) -> Dict[str, Any]:
    """Read the current checkpointed state values as a dict."""
    snapshot = compiled.get_state(_config(session_id))
    values = snapshot.values
    if hasattr(values, "to_dict"):
        return values.to_dict()
    if isinstance(values, dict):
        return values
    return dict(values)


def _a11y_strings(state_values: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for flag in state_values.get("a11y_flags", []) or []:
        if isinstance(flag, dict):
            issue = (
                flag.get("title")
                or flag.get("problem")
                or flag.get("description")
                or "Accessibility issue"
            )
            sev = flag.get("severity", "")
            out.append(f"{issue} ({sev})".strip(" ()"))
        else:
            out.append(str(flag))
    return out


def _capture_review(session: UXSessionState, values: Dict[str, Any]) -> None:
    session.personas = values.get("personas", []) or []
    session.user_flows = values.get("user_flows", []) or []
    briefs = values.get("updated_wireframe_briefs") or values.get("wireframe_briefs")
    session.wireframe_briefs = briefs or []
    session.a11y_flags = _a11y_strings(values)
    session.status = "awaiting_review"


def start_session(session: UXSessionState, story_dicts: List[Dict[str, Any]]) -> None:
    """Submit a session to run in the background up to the review interrupt."""
    _executor.submit(_run_until_interrupt, session, story_dicts)


def _run_until_interrupt(
    session: UXSessionState, story_dicts: List[Dict[str, Any]]
) -> None:
    try:
        compiled = _get_compiled()
        initial = UXWorkflowState(
            input_stories=to_user_stories(story_dicts),
            web_mode=True,
        )
        for step in compiled.stream(initial, _config(session.session_id)):
            for node_name in step.keys():
                session.current_node = node_name
                if node_name not in session.completed_nodes:
                    session.completed_nodes.append(node_name)

        values = _state_values(compiled, session.session_id)
        _capture_review(session, values)
    except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
        session.status = "error"
        session.error = str(exc)


def approve(
    session: UXSessionState,
    context_store: ContextStore,
    event_bus: EventBus,
) -> None:
    """Resume the paused workflow with briefs approved and publish the handoff."""
    compiled = _get_compiled()
    config = _config(session.session_id)

    compiled.update_state(config, {"briefs_approved": True})
    final = compiled.invoke(None, config)
    values = final.to_dict() if hasattr(final, "to_dict") else dict(final)

    handoff = {
        "personas": values.get("personas", []) or session.personas,
        "user_flows": values.get("user_flows", []) or session.user_flows,
        "wireframe_briefs": (
            values.get("updated_wireframe_briefs")
            or values.get("wireframe_briefs")
            or session.wireframe_briefs
        ),
        "ux_handoff": values.get("ux_handoff"),
        "session_name": session.session_name,
        "published_at": datetime.utcnow().isoformat(),
    }
    context_store.write_artifact(
        key="ux-handoff",
        data=handoff,
        workflow="ux",
        artifact_type="ux-handoff",
    )

    _publish(
        event_bus,
        EventType.UX_HANDOFF_READY,
        {"persona_count": len(handoff["personas"])},
    )

    session.status = "approved"
    session.completed_at = datetime.utcnow()


def reject(session: UXSessionState, feedback: str) -> None:
    """Resume the workflow back through wireframe briefs with feedback applied."""
    compiled = _get_compiled()
    config = _config(session.session_id)

    compiled.update_state(
        config,
        {"briefs_approved": False, "approval_feedback": feedback},
    )
    session.status = "running"
    _executor.submit(_resume_after_reject, session)


def _resume_after_reject(session: UXSessionState) -> None:
    try:
        compiled = _get_compiled()
        config = _config(session.session_id)
        for step in compiled.stream(None, config):
            for node_name in step.keys():
                session.current_node = node_name
                if node_name not in session.completed_nodes:
                    session.completed_nodes.append(node_name)

        values = _state_values(compiled, session.session_id)
        _capture_review(session, values)
    except Exception as exc:  # noqa: BLE001
        session.status = "error"
        session.error = str(exc)


def _publish(
    event_bus: EventBus, event_type: EventType, payload: Dict[str, Any]
) -> None:
    event_bus.publish(
        Event(
            event_type=event_type,
            workflow="ux",
            severity=EventSeverity.INFO,
            payload=payload,
            source_agent="ux-interface",
        )
    )
