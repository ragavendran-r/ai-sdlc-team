"""Team Orchestrator - coordinates all workflows."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json

from .events import Event, EventType, EventBus, EventSeverity
from .context_store import ContextStore
from .router import WorkflowRouter


class TeamOrchestrator:
    """
    Central orchestrator that coordinates all team workflows.

    Manages:
    - Event publishing and subscriptions
    - Context store for shared artifacts
    - Workflow routing and data flow
    - Execution lifecycle and status
    """

    def __init__(self, context_store_path: str = "team_contracts/context-store"):
        """
        Initialize the orchestrator.

        Args:
            context_store_path: Path to context store directory
        """
        self.context_store = ContextStore(context_store_path)
        self.event_bus = EventBus()
        self.router = WorkflowRouter(self.context_store, self.event_bus)

        # Workflow states
        self.workflow_states: Dict[str, Dict[str, Any]] = {
            "po": {"status": "pending", "completed": False},
            "em": {"status": "pending", "completed": False},
            "ux": {"status": "pending", "completed": False},
            "backend": {"status": "pending", "completed": False},
            "frontend": {"status": "pending", "completed": False},
        }

        # Pipeline state
        self.pipeline_started: Optional[datetime] = None
        self.pipeline_completed: Optional[datetime] = None
        self.pipeline_failed = False
        self.pipeline_error: Optional[str] = None

        # Setup default routes
        self._setup_default_routes()

    def _setup_default_routes(self) -> None:
        """Setup default workflow routes."""

        # PO → EM: User stories trigger sprint planning
        self.router.add_route(
            source_workflow="po",
            source_event_type=EventType.USER_STORIES_CREATED,
            target_workflow="em",
            data_mapper=lambda payload: {
                "user_stories": payload.get("stories", []),
                "planning_context": payload.get("context", {}),
            },
        )

        # PO → UX: User stories drive UX design
        self.router.add_route(
            source_workflow="po",
            source_event_type=EventType.USER_STORIES_CREATED,
            target_workflow="ux",
            data_mapper=lambda payload: {
                "user_stories": payload.get("stories", []),
                "design_context": payload.get("context", {}),
            },
        )

        # EM → Backend: Sprint tasks drive backend work
        self.router.add_route(
            source_workflow="em",
            source_event_type=EventType.SPRINT_CREATED,
            target_workflow="backend",
            data_mapper=lambda payload: {
                "sprint_plan": payload.get("sprint", {}),
                "user_stories": payload.get("stories", []),
            },
        )

        # EM → Frontend: Sprint tasks drive frontend work
        self.router.add_route(
            source_workflow="em",
            source_event_type=EventType.SPRINT_CREATED,
            target_workflow="frontend",
            data_mapper=lambda payload: {
                "sprint_plan": payload.get("sprint", {}),
                "tasks": payload.get("tasks", []),
            },
        )

        # UX → Frontend: Design handoff drives component scaffolding
        self.router.add_route(
            source_workflow="ux",
            source_event_type=EventType.HANDOFF_CREATED,
            target_workflow="frontend",
            data_mapper=lambda payload: {
                "ux_handoff": payload.get("handoff", {}),
                "design_tokens": payload.get("tokens", {}),
            },
        )

        # Backend → Frontend: API contract drives integration
        self.router.add_route(
            source_workflow="backend",
            source_event_type=EventType.API_CONTRACT_PUBLISHED,
            target_workflow="frontend",
            data_mapper=lambda payload: {
                "api_contract": payload.get("contract", {}),
            },
        )

    def start_pipeline(self) -> None:
        """Start the team pipeline execution."""
        self.pipeline_started = datetime.utcnow()
        self.pipeline_failed = False
        self.pipeline_error = None

        event = Event(
            event_type=EventType.WORKFLOW_STARTED,
            workflow="system",
            severity=EventSeverity.INFO,
            payload={"pipeline": "team_pipeline"},
            source_agent="orchestrator",
        )
        self.event_bus.publish(event)

        print("\n" + "=" * 80)
        print(" TEAM PIPELINE STARTED")
        print("=" * 80)
        print(f"Started at: {self.pipeline_started.isoformat()}")

    def complete_pipeline(self) -> None:
        """Mark pipeline as completed."""
        self.pipeline_completed = datetime.utcnow()

        if self.pipeline_started:
            duration = (self.pipeline_completed - self.pipeline_started).total_seconds()
        else:
            duration = 0

        event = Event(
            event_type=EventType.WORKFLOW_COMPLETED,
            workflow="system",
            severity=EventSeverity.INFO,
            payload={
                "pipeline": "team_pipeline",
                "duration_seconds": duration,
            },
            source_agent="orchestrator",
        )
        self.event_bus.publish(event)

        print("\n" + "=" * 80)
        print(" TEAM PIPELINE COMPLETED")
        print("=" * 80)
        print(f"Completed at: {self.pipeline_completed.isoformat()}")
        print(f"Duration: {duration:.1f} seconds")

    def fail_pipeline(self, error: str) -> None:
        """Mark pipeline as failed."""
        self.pipeline_failed = True
        self.pipeline_error = error
        self.pipeline_completed = datetime.utcnow()

        event = Event(
            event_type=EventType.WORKFLOW_FAILED,
            workflow="system",
            severity=EventSeverity.CRITICAL,
            payload={
                "pipeline": "team_pipeline",
                "error": error,
            },
            source_agent="orchestrator",
        )
        self.event_bus.publish(event)

        print("\n" + "=" * 80)
        print(" TEAM PIPELINE FAILED")
        print("=" * 80)
        print(f"Error: {error}")

    def mark_workflow_complete(self, workflow: str, status: str = "completed") -> None:
        """Mark a workflow as complete."""
        if workflow in self.workflow_states:
            self.workflow_states[workflow]["status"] = status
            self.workflow_states[workflow]["completed"] = True
            print(f"\n✅ {workflow.upper()} workflow marked as {status}")

    def mark_workflow_failed(self, workflow: str, error: str) -> None:
        """Mark a workflow as failed."""
        if workflow in self.workflow_states:
            self.workflow_states[workflow]["status"] = "failed"
            self.workflow_states[workflow]["completed"] = True
            self.workflow_states[workflow]["error"] = error
            print(f"\n❌ {workflow.upper()} workflow failed: {error}")

    def publish_event(self, event: Event) -> None:
        """
        Publish an event through the orchestrator.

        Args:
            event: Event to publish
        """
        self.event_bus.publish(event)
        self.router.route_event(event)

    def register_workflow_handler(
        self,
        workflow: str,
        handler: callable,
    ) -> None:
        """
        Register a handler for workflow events.

        Args:
            workflow: Workflow name
            handler: Callable to execute on workflow events
        """
        # Subscribe to all events from this workflow
        event_types = [
            e for e in EventType
            if e.value.startswith(workflow)
        ]

        self.event_bus.subscribe(
            event_types=event_types or [EventType.WORKFLOW_STARTED],
            handler=handler,
            name=f"{workflow}_handler",
        )

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        status = {
            "pipeline_status": "running" if (
                self.pipeline_started and not self.pipeline_completed
            ) else "completed",
            "failed": self.pipeline_failed,
            "error": self.pipeline_error,
            "started_at": self.pipeline_started.isoformat() if self.pipeline_started else None,
            "completed_at": self.pipeline_completed.isoformat() if self.pipeline_completed else None,
            "workflow_states": self.workflow_states,
            "event_bus_stats": self.event_bus.get_stats(),
            "context_store_stats": self.context_store.get_stats(),
            "router_stats": self.router.get_stats(),
        }
        return status

    def print_status_report(self) -> None:
        """Print a formatted status report."""
        status = self.get_pipeline_status()

        print("\n" + "=" * 80)
        print(" TEAM PIPELINE STATUS REPORT")
        print("=" * 80)

        # Pipeline status
        print(f"\nPipeline Status: {status['pipeline_status']}")
        if status["failed"]:
            print(f"❌ Failed: {status['error']}")
        else:
            print("✅ All systems operational")

        # Timeline
        if status["started_at"]:
            print(f"\nStarted: {status['started_at']}")
        if status["completed_at"]:
            print(f"Completed: {status['completed_at']}")

        # Workflow states
        print("\nWorkflow States:")
        print("-" * 40)
        for workflow, state in status["workflow_states"].items():
            emoji = "✅" if state["completed"] else "⏳"
            print(f"{emoji} {workflow:12} {state['status']}")

        # Statistics
        print("\nStatistics:")
        print("-" * 40)
        print(f"Events Published: {status['event_bus_stats']['total_events']}")
        print(f"Artifacts Stored: {status['context_store_stats']['total_artifacts']}")
        print(f"Routes Executed: {status['router_stats']['routed_events']}")

        # Events by workflow
        if status["event_bus_stats"]["events_by_workflow"]:
            print("\nEvents by Workflow:")
            for workflow, count in sorted(
                status["event_bus_stats"]["events_by_workflow"].items()
            ):
                print(f"  {workflow}: {count}")

        # Artifacts by workflow
        if status["context_store_stats"]["by_workflow"]:
            print("\nArtifacts by Workflow:")
            for workflow, count in sorted(
                status["context_store_stats"]["by_workflow"].items()
            ):
                print(f"  {workflow}: {count}")

    def export_state(self, filepath: str) -> None:
        """
        Export orchestrator state to file.

        Args:
            filepath: Path to export to
        """
        state = {
            "orchestrator_state": self.get_pipeline_status(),
            "event_history": [e.to_dict() for e in self.event_bus.event_history],
            "route_history": self.router.route_history,
            "artifacts": self.context_store.list_artifacts(),
        }

        with open(filepath, "w") as f:
            json.dump(state, f, indent=2, default=str)

        print(f"\n💾 Orchestrator state exported to {filepath}")

    def print_event_log(self, limit: int = 20) -> None:
        """Print recent event log."""
        print("\n" + "=" * 80)
        print(" EVENT LOG")
        print("=" * 80)

        events = self.event_bus.event_history[-limit:]
        if not events:
            print("No events yet.")
            return

        for event in events:
            print(
                f"{event.timestamp.strftime('%H:%M:%S')} "
                f"[{event.workflow:8}] {event.event_type.value}"
            )

    def print_route_diagram(self) -> None:
        """Print route diagram."""
        print("\n" + self.router.get_route_diagram())

    def print_context_timeline(self) -> None:
        """Print context store timeline."""
        print("\n" + self.context_store.export_timeline())
