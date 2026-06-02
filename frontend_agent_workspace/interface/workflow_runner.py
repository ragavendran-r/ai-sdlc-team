"""Background execution of the Frontend LangGraph workflow for the web interface.

The workflow is compiled with a checkpointer and an interrupt before the
human_checkpoint node (compile_frontend_workflow_web). This module runs it in a
thread pool, streams node progress into the FrontendSessionState, pauses at the
interrupt for human review of components / tests / state plan, and resumes on
approve/reject.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, Optional

from frontend_agent_workspace.agents import FrontendWorkflowState, compile_frontend_workflow_web

from team_orchestrator import ContextStore, Event, EventBus, EventSeverity, EventType

from .session import FrontendSessionState

# Single worker pool shared by all sessions in this process.
_executor = ThreadPoolExecutor(max_workers=4)

# One compiled web workflow (with MemorySaver checkpointer) reused across
# sessions; sessions are isolated by thread_id in the run config.
_compiled = None


def _get_compiled():
    global _compiled
    if _compiled is None:
        _compiled = compile_frontend_workflow_web()
    return _compiled


def _config(session_id: str) -> Dict[str, Any]:
    return {"configurable": {"thread_id": session_id}}


def _serialize(obj: Any) -> Any:
    """Recursively serialize Pydantic/dataclass objects to plain dicts."""
    if obj is None:
        return None
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj


def _state_values(compiled, session_id: str) -> Dict[str, Any]:
    """Read the current checkpointed state values as a fully-serialized dict."""
    snapshot = compiled.get_state(_config(session_id))
    values = snapshot.values
    if hasattr(values, "to_dict"):
        return values.to_dict()
    if isinstance(values, dict):
        return {k: _serialize(v) for k, v in values.items()}
    return {k: _serialize(v) for k, v in dict(values).items()}


def _capture_review(session: FrontendSessionState, values: Dict[str, Any]) -> None:
    """Populate session from checkpointed state values at the interrupt point."""
    session.component_plan = _serialize(values.get("component_plan") or [])
    session.scaffolded_components = _serialize(values.get("scaffolded_components") or [])
    session.a11y_enriched_components = _serialize(values.get("a11y_enriched_components") or [])
    session.test_files = _serialize(values.get("test_files") or [])
    session.state_plan = _serialize(values.get("state_plan"))
    session.token_gaps = values.get("token_gaps") or []
    session.intake_gaps = values.get("intake_gaps") or []
    session.status = "awaiting_review"


def start_session(session: FrontendSessionState, ux_handoff_data: Dict[str, Any]) -> None:
    """Submit a session to run in the background up to the review interrupt."""
    _executor.submit(_run_until_interrupt, session, ux_handoff_data)


def _build_ux_handoff(ux_handoff_data: Dict[str, Any]) -> Optional[Any]:
    """Build a UXHandoff object from the context-store artifact dict."""
    from team_contracts.schemas import UXHandoff, ComponentSpec, ComponentType, DesignToken, InteractionSpec

    # The ux-handoff artifact may contain a nested 'ux_handoff' dict (the actual
    # UXHandoff payload) or top-level component/persona data from the UX workspace.
    raw = ux_handoff_data.get("ux_handoff") or {}
    if not raw:
        # Try to construct from available fields
        raw = ux_handoff_data

    components_raw = raw.get("components") or []
    components = []
    for c in components_raw:
        if not isinstance(c, dict):
            continue
        try:
            ctype = c.get("component_type", "custom")
            # Normalize component_type to a valid enum value
            valid_types = {t.value for t in ComponentType}
            if ctype not in valid_types:
                ctype = "custom"
            interactions = []
            for i in (c.get("interactions") or []):
                if isinstance(i, dict):
                    try:
                        interactions.append(
                            InteractionSpec(
                                name=i.get("name", "interaction"),
                                trigger=i.get("trigger", "on-click"),
                                behavior=i.get("behavior", "default"),
                            )
                        )
                    except Exception:
                        pass
            components.append(
                ComponentSpec(
                    id=c.get("id", "C-001"),
                    name=c.get("name", "Component"),
                    component_type=ComponentType(ctype),
                    description=c.get("description", "Component"),
                    design_notes=c.get("design_notes", "See UX handoff"),
                    states=c.get("states") or {},
                    props=c.get("props") or {},
                    interactions=interactions,
                )
            )
        except Exception:
            pass

    if not components:
        # Build a minimal placeholder component so the workflow has something
        components.append(
            ComponentSpec(
                id="C-001",
                name="PlaceholderComponent",
                component_type=ComponentType.CUSTOM,
                description="Derived from UX handoff",
                design_notes="See UX handoff for details",
            )
        )

    design_tokens_raw = raw.get("design_tokens") or []
    design_tokens = []
    for t in design_tokens_raw:
        if isinstance(t, dict):
            try:
                design_tokens.append(
                    DesignToken(
                        name=t.get("name", "token"),
                        category=t.get("category", "color"),
                        value=t.get("value", "#000000"),
                    )
                )
            except Exception:
                pass

    try:
        return UXHandoff(
            id=raw.get("id", "UX-001"),
            user_story_id=raw.get("user_story_id", "US-001"),
            feature_name=raw.get("feature_name") or ux_handoff_data.get("session_name", "Feature"),
            components=components,
            design_tokens=design_tokens,
            accessibility_requirements=raw.get("accessibility_requirements") or [],
            created_by=raw.get("created_by", "ux-agent"),
        )
    except Exception:
        return None


def _run_until_interrupt(
    session: FrontendSessionState, ux_handoff_data: Dict[str, Any]
) -> None:
    try:
        compiled = _get_compiled()
        ux_handoff_obj = _build_ux_handoff(ux_handoff_data)
        initial = FrontendWorkflowState(
            ux_handoff=ux_handoff_obj,
            web_mode=True,
        )
        # Capture the last node output directly from the stream — this is the raw
        # FrontendWorkflowState returned by the node, with no checkpoint
        # serialization involved. Checkpoint reading (_state_values) can silently
        # lose fields for dataclass states with non-JSON-serializable members
        # (datetime, Pydantic models), so we prefer the stream output.
        last_state: Optional[Any] = None
        for step in compiled.stream(initial, _config(session.session_id)):
            for node_name, node_output in step.items():
                session.current_node = node_name
                if node_name not in session.completed_nodes:
                    session.completed_nodes.append(node_name)
                last_state = node_output

        if last_state is not None and hasattr(last_state, "to_dict"):
            values = last_state.to_dict()
        elif last_state is not None and isinstance(last_state, dict):
            values = {k: _serialize(v) for k, v in last_state.items()}
        else:
            values = _state_values(compiled, session.session_id)

        _capture_review(session, values)
    except Exception as exc:  # noqa: BLE001
        session.status = "error"
        session.error = str(exc)


def approve(
    session: FrontendSessionState,
    context_store: ContextStore,
    event_bus: EventBus,
) -> None:
    """Resume the paused workflow with components approved and capture the output."""
    compiled = _get_compiled()
    config = _config(session.session_id)

    compiled.update_state(config, {"components_approved": True})
    final = compiled.invoke(None, config)
    if hasattr(final, "to_dict"):
        values = final.to_dict()
    else:
        values = {k: _serialize(v) for k, v in dict(final).items()}

    session.pr_description = values.get("pr_description") or ""
    session.review_comments = _serialize(values.get("review_comments") or [])

    output = {
        "component_plan": _serialize(values.get("component_plan") or session.component_plan),
        "scaffolded_components": _serialize(
            values.get("scaffolded_components") or session.scaffolded_components
        ),
        "a11y_enriched_components": _serialize(
            values.get("a11y_enriched_components") or session.a11y_enriched_components
        ),
        "test_files": _serialize(values.get("test_files") or session.test_files),
        "state_plan": _serialize(values.get("state_plan") or session.state_plan),
        "pr_description": session.pr_description,
        "review_comments": session.review_comments,
        "session_name": session.session_name,
        "published_at": datetime.utcnow().isoformat(),
    }
    context_store.write_artifact(
        key="frontend-output",
        data=output,
        workflow="frontend",
        artifact_type="frontend-output",
    )

    _publish(
        event_bus,
        EventType.FRONTEND_COMPLETE,
        {"component_count": len(output["scaffolded_components"])},
    )

    session.status = "approved"
    session.completed_at = datetime.utcnow()


def reject(session: FrontendSessionState, feedback: str) -> None:
    """Reject the current components and resume from component_scaffolding."""
    compiled = _get_compiled()
    config = _config(session.session_id)

    compiled.update_state(
        config,
        {"components_approved": False, "approval_feedback": feedback},
    )
    session.status = "running"
    _executor.submit(_resume_after_reject, session)


def _resume_after_reject(session: FrontendSessionState) -> None:
    try:
        compiled = _get_compiled()
        config = _config(session.session_id)
        last_state: Optional[Any] = None
        for step in compiled.stream(None, config):
            for node_name, node_output in step.items():
                session.current_node = node_name
                if node_name not in session.completed_nodes:
                    session.completed_nodes.append(node_name)
                last_state = node_output

        if last_state is not None and hasattr(last_state, "to_dict"):
            values = last_state.to_dict()
        elif last_state is not None and isinstance(last_state, dict):
            values = {k: _serialize(v) for k, v in last_state.items()}
        else:
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
            workflow="frontend",
            severity=EventSeverity.INFO,
            payload=payload,
            source_agent="frontend-interface",
        )
    )
