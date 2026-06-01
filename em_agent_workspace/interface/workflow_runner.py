"""Background execution of the EM LangGraph workflow for the web interface.

The workflow is compiled with a checkpointer and an interrupt before the
human_checkpoint node (compile_em_workflow_web). This module runs it in a thread
pool, streams node progress into the EMSessionState, pauses at the interrupt for
human review of the draft sprint, and resumes on approve/reject.

Cross-process note: each interface process owns its own EventBus, so events
published here are local. Real cross-workspace handoff happens via the shared
context store on disk: this workspace reads the PO `backlog` artifact as input
and writes the `sprint-plan` artifact on approval.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List

from em_agent_workspace.agents import EMWorkflowState, compile_em_workflow_web

from team_contracts.schemas import UserStory
from team_orchestrator import ContextStore, Event, EventBus, EventSeverity, EventType

from .session import EMSessionState

# Single worker pool shared by all sessions in this process.
_executor = ThreadPoolExecutor(max_workers=4)

# One compiled web workflow (with MemorySaver checkpointer) reused across
# sessions; sessions are isolated by thread_id in the run config.
_compiled = None

# Map of common priority/complexity inputs to the schema enum values.
_PRIORITY_VALUES = {"critical", "high", "medium", "low"}
_COMPLEXITY_VALUES = {"xs", "s", "m", "l", "xl"}


def _get_compiled():
    global _compiled
    if _compiled is None:
        _compiled = compile_em_workflow_web()
    return _compiled


def _config(session_id: str) -> Dict[str, Any]:
    return {"configurable": {"thread_id": session_id}}


def _points_to_complexity(points: Any) -> str:
    """Map story points (if present) to a rough complexity bucket."""
    try:
        p = int(points)
    except (TypeError, ValueError):
        return "m"
    if p <= 1:
        return "xs"
    if p <= 2:
        return "s"
    if p <= 5:
        return "m"
    if p <= 8:
        return "l"
    return "xl"


def to_user_stories(story_dicts: List[Dict[str, Any]]) -> List[UserStory]:
    """Convert PO backlog story dicts into validated UserStory objects.

    The PO backlog stores plain dicts; the EM graph expects UserStory schema
    objects. Fill required fields with sensible defaults when the backlog does
    not carry them so a real run never fails schema validation.
    """
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

        complexity = str(raw.get("estimated_complexity") or "").lower()
        if complexity not in _COMPLEXITY_VALUES:
            complexity = _points_to_complexity(raw.get("story_points"))

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
    # LangGraph may hold the state as a dataclass or a dict depending on version.
    if hasattr(values, "to_dict"):
        return values.to_dict()
    if isinstance(values, dict):
        return values
    return dict(values)


def _risk_strings(state_values: Dict[str, Any]) -> List[str]:
    """Turn structured risk flags into display strings."""
    out: List[str] = []
    for flag in state_values.get("risk_flags", []) or []:
        if isinstance(flag, dict):
            title = flag.get("title") or flag.get("risk_type") or "Risk"
            severity = flag.get("severity", "")
            out.append(f"{title} ({severity})".strip(" ()"))
        else:
            out.append(str(flag))
    return out


def _capture_review(session: EMSessionState, values: Dict[str, Any]) -> None:
    session.draft_sprint = values.get("draft_sprint")
    session.capacity_report = values.get("capacity_report")
    session.risk_flags = _risk_strings(values)
    session.status = "awaiting_review"


def start_session(session: EMSessionState, story_dicts: List[Dict[str, Any]]) -> None:
    """Submit a session to run in the background up to the review interrupt."""
    _executor.submit(_run_until_interrupt, session, story_dicts)


def _run_until_interrupt(
    session: EMSessionState, story_dicts: List[Dict[str, Any]]
) -> None:
    try:
        compiled = _get_compiled()
        initial = EMWorkflowState(
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
    session: EMSessionState,
    context_store: ContextStore,
    event_bus: EventBus,
) -> None:
    """Resume the paused workflow with the sprint approved and publish the plan."""
    compiled = _get_compiled()
    config = _config(session.session_id)

    compiled.update_state(config, {"sprint_approved": True})
    final = compiled.invoke(None, config)
    values = final.to_dict() if hasattr(final, "to_dict") else dict(final)

    draft = values.get("draft_sprint") or session.draft_sprint or {}
    context_store.write_artifact(
        key="sprint-plan",
        data=draft,
        workflow="em",
        artifact_type="sprint-plan",
    )

    report = _build_report(draft, values)
    context_store.write_artifact(
        key="sprint-report",
        data={"report": report, "generated_at": datetime.utcnow().isoformat()},
        workflow="em",
        artifact_type="sprint-report",
    )

    task_count = len((draft.get("sprint") or {}).get("tasks", []))
    _publish(event_bus, EventType.SPRINT_PLANNED, {"task_count": task_count})

    session.draft_sprint = draft
    session.status = "approved"
    session.completed_at = datetime.utcnow()


def reject(session: EMSessionState, feedback: str) -> None:
    """Resume the workflow back through sprint composition with feedback applied."""
    compiled = _get_compiled()
    config = _config(session.session_id)

    compiled.update_state(
        config,
        {"sprint_approved": False, "approval_feedback": feedback},
    )
    session.status = "running"
    _executor.submit(_resume_after_reject, session)


def _resume_after_reject(session: EMSessionState) -> None:
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


def _build_report(draft: Dict[str, Any], values: Dict[str, Any]) -> str:
    """Build a stakeholder report markdown from the sprint plan."""
    sprint = (draft or {}).get("sprint") or {}
    tasks = sprint.get("tasks", [])
    lines = [
        f"# Sprint Report: {sprint.get('name', 'Sprint')}",
        "",
        f"**Sprint ID:** {sprint.get('id', '')}",
        f"**Tasks:** {len(tasks)}",
    ]
    capacity = values.get("capacity_report") or {}
    if capacity:
        lines.append(
            f"**Capacity:** {capacity.get('estimated_story_points_capacity', '—')} "
            "story points"
        )
    risks = values.get("risk_flags") or []
    lines.append(f"**Risks flagged:** {len(risks)}")
    lines.append("")
    lines.append("## Task assignments")
    lines.append("")
    for task in tasks:
        lines.append(
            f"- **{task.get('title', '')}** ({task.get('task_type', '')}, "
            f"{task.get('estimated_hours', 0)}h) → {task.get('assigned_to', '')}"
        )
    return "\n".join(lines)


def regenerate_report(context_store: ContextStore) -> str:
    """Rebuild the stakeholder report from the published sprint plan."""
    draft = context_store.read_artifact("sprint-plan") or {}
    report = _build_report(draft, {})
    context_store.write_artifact(
        key="sprint-report",
        data={"report": report, "generated_at": datetime.utcnow().isoformat()},
        workflow="em",
        artifact_type="sprint-report",
    )
    return report


def _publish(
    event_bus: EventBus, event_type: EventType, payload: Dict[str, Any]
) -> None:
    event_bus.publish(
        Event(
            event_type=event_type,
            workflow="em",
            severity=EventSeverity.INFO,
            payload=payload,
            source_agent="em-interface",
        )
    )
