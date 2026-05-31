"""Workflow routing and orchestration logic."""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json

from .events import Event, EventType, EventBus, EventSeverity
from .context_store import ContextStore


class WorkflowRoute:
    """Represents a route between workflows."""

    def __init__(
        self,
        source_workflow: str,
        source_event_type: EventType,
        target_workflow: str,
        data_mapper: Optional[Callable] = None,
        condition: Optional[Callable] = None,
    ):
        """
        Initialize a workflow route.

        Args:
            source_workflow: Source workflow name
            source_event_type: Event type that triggers route
            target_workflow: Target workflow name
            data_mapper: Optional function to transform data
            condition: Optional function to determine if route should fire
        """
        self.source_workflow = source_workflow
        self.source_event_type = source_event_type
        self.target_workflow = target_workflow
        self.data_mapper = data_mapper or (lambda x: x)
        self.condition = condition or (lambda x: True)

    def should_route(self, event: Event) -> bool:
        """Check if this route should fire for the event."""
        if event.workflow != self.source_workflow:
            return False
        if event.event_type != self.source_event_type:
            return False
        return self.condition(event)

    def route(self, event: Event) -> Any:
        """Execute the route and return mapped data."""
        return self.data_mapper(event.payload)


class WorkflowRouter:
    """Routes events and data between workflows."""

    def __init__(self, context_store: ContextStore, event_bus: EventBus):
        """
        Initialize router.

        Args:
            context_store: Shared context store
            event_bus: Event bus for publishing
        """
        self.context_store = context_store
        self.event_bus = event_bus
        self.routes: List[WorkflowRoute] = []
        self.route_history: List[Dict[str, Any]] = []

    def add_route(
        self,
        source_workflow: str,
        source_event_type: EventType,
        target_workflow: str,
        data_mapper: Optional[Callable] = None,
        condition: Optional[Callable] = None,
    ) -> WorkflowRoute:
        """
        Add a workflow route.

        Args:
            source_workflow: Source workflow name
            source_event_type: Event type that triggers route
            target_workflow: Target workflow name
            data_mapper: Optional data transformation function
            condition: Optional condition to check before routing

        Returns:
            WorkflowRoute object
        """
        route = WorkflowRoute(
            source_workflow=source_workflow,
            source_event_type=source_event_type,
            target_workflow=target_workflow,
            data_mapper=data_mapper,
            condition=condition,
        )
        self.routes.append(route)
        return route

    def route_event(self, event: Event) -> List[Dict[str, Any]]:
        """
        Route an event to all matching target workflows.

        Args:
            event: Event to route

        Returns:
            List of routing results
        """
        results = []

        for route in self.routes:
            if route.should_route(event):
                try:
                    mapped_data = route.route(event)

                    result = {
                        "route": f"{route.source_workflow} → {route.target_workflow}",
                        "source_event": event.event_type.value,
                        "target_workflow": route.target_workflow,
                        "status": "success",
                        "data": mapped_data,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    # Store in context
                    artifact_key = (
                        f"{route.target_workflow}_input_"
                        f"{datetime.utcnow().timestamp()}"
                    )
                    self.context_store.write_artifact(
                        key=artifact_key,
                        data=mapped_data,
                        workflow=route.target_workflow,
                        artifact_type=f"input_from_{route.source_workflow}",
                    )

                    print(
                        f"\n🔀 Routing: {route.source_workflow} → "
                        f"{route.target_workflow}"
                    )
                    print(f"   Event: {event.event_type.value}")
                    print("   Status: success")
                    print(f"   Stored as: {artifact_key}")

                    results.append(result)

                except Exception as e:
                    result = {
                        "route": f"{route.source_workflow} → {route.target_workflow}",
                        "source_event": event.event_type.value,
                        "target_workflow": route.target_workflow,
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    print(f"   ✗ Routing failed: {str(e)}")
                    results.append(result)

        self.route_history.extend(results)
        return results

    def get_routes_for_workflow(self, workflow: str) -> List[WorkflowRoute]:
        """Get all routes that target a specific workflow."""
        return [r for r in self.routes if r.target_workflow == workflow]

    def get_route_diagram(self) -> str:
        """Get ASCII diagram of all routes."""
        lines = ["Workflow Routes", "=" * 60]

        workflows = set()
        edges = []

        for route in self.routes:
            workflows.add(route.source_workflow)
            workflows.add(route.target_workflow)
            edges.append(
                f"{route.source_workflow} "
                f"[{route.source_event_type.value}] → "
                f"{route.target_workflow}"
            )

        lines.append(f"\nWorkflows: {', '.join(sorted(workflows))}\n")
        lines.append("Routes:")
        for edge in sorted(edges):
            lines.append(f"  {edge}")

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        stats = {
            "total_routes": len(self.routes),
            "routed_events": len(self.route_history),
            "routes_by_source": {},
            "routes_by_target": {},
            "successful_routes": 0,
            "failed_routes": 0,
        }

        for route in self.routes:
            source = route.source_workflow
            target = route.target_workflow

            if source not in stats["routes_by_source"]:
                stats["routes_by_source"][source] = 0
            stats["routes_by_source"][source] += 1

            if target not in stats["routes_by_target"]:
                stats["routes_by_target"][target] = 0
            stats["routes_by_target"][target] += 1

        for routing in self.route_history:
            if routing["status"] == "success":
                stats["successful_routes"] += 1
            else:
                stats["failed_routes"] += 1

        return stats
