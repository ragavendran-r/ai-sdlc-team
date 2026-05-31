"""Event system for team orchestrator."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional, Dict, List
from enum import Enum
import json


class EventType(str, Enum):
    """Supported event types from each workflow."""

    # PO Agent Events
    USER_STORIES_CREATED = "user_stories_created"
    USER_STORIES_UPDATED = "user_stories_updated"

    # EM Agent Events
    SPRINT_CREATED = "sprint_created"
    SPRINT_UPDATED = "sprint_updated"
    BLOCKERS_DETECTED = "blockers_detected"

    # UX Agent Events
    HANDOFF_CREATED = "ux_handoff_created"
    HANDOFF_UPDATED = "ux_handoff_updated"
    DESIGN_TOKENS_DEFINED = "design_tokens_defined"

    # Backend Agent Events
    DOMAIN_MODEL_CREATED = "domain_model_created"
    API_CONTRACT_PUBLISHED = "api_contract_published"
    DATABASE_SCHEMA_READY = "database_schema_ready"

    # Frontend Agent Events
    COMPONENTS_SCAFFOLDED = "components_scaffolded"
    FRONTEND_COMPLETE = "frontend_complete"

    # System Events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"


class EventSeverity(str, Enum):
    """Event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Event:
    """Represents a workflow event."""

    event_type: EventType
    workflow: str  # 'po', 'em', 'ux', 'backend', 'frontend'
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: EventSeverity = field(default=EventSeverity.INFO)

    # Event data
    payload: Dict[str, Any] = field(default_factory=dict)

    # Tracking
    event_id: str = field(default="")
    correlation_id: str = field(default="")  # Track related events
    parent_event_id: Optional[str] = field(default=None)

    # Metadata
    source_agent: str = field(default="")
    triggered_by: Optional[str] = field(default=None)  # What triggered this
    downstream_events: List[str] = field(default_factory=list)  # Events this should trigger

    def __post_init__(self):
        """Generate IDs if not provided."""
        if not self.event_id:
            self.event_id = f"{self.workflow}_{self.timestamp.timestamp()}"
        if not self.correlation_id:
            self.correlation_id = self.event_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        result = asdict(self)
        result['event_type'] = self.event_type.value
        result['severity'] = self.severity.value
        result['timestamp'] = self.timestamp.isoformat()
        return result

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)


@dataclass
class EventSubscription:
    """Subscription to specific event types."""

    event_types: List[EventType]
    handler: callable
    name: str = ""

    def matches(self, event: Event) -> bool:
        """Check if this subscription matches the event."""
        return event.event_type in self.event_types


class EventBus:
    """Central event bus for orchestrator."""

    def __init__(self):
        """Initialize event bus."""
        self.subscriptions: Dict[str, List[EventSubscription]] = {}
        self.event_history: List[Event] = []
        self.event_handlers: Dict[str, callable] = {}

    def subscribe(
        self,
        event_types: List[EventType],
        handler: callable,
        name: str = ""
    ) -> EventSubscription:
        """
        Subscribe to event types.

        Args:
            event_types: List of EventType to subscribe to
            handler: Callable to execute when event fires
            name: Optional name for subscription

        Returns:
            EventSubscription object
        """
        subscription = EventSubscription(
            event_types=event_types,
            handler=handler,
            name=name or f"handler_{len(self.subscriptions)}"
        )

        for event_type in event_types:
            key = event_type.value
            if key not in self.subscriptions:
                self.subscriptions[key] = []
            self.subscriptions[key].append(subscription)

        return subscription

    def publish(self, event: Event) -> None:
        """
        Publish an event and trigger handlers.

        Args:
            event: Event to publish
        """
        # Add to history
        self.event_history.append(event)

        print(f"\n📢 Event Published: {event.event_type.value}")
        print(f"   Workflow: {event.workflow}")
        print(f"   Severity: {event.severity.value}")
        print(f"   ID: {event.event_id}")

        # Trigger subscriptions
        event_key = event.event_type.value
        if event_key in self.subscriptions:
            for subscription in self.subscriptions[event_key]:
                try:
                    print(f"   ✓ Triggering: {subscription.name}")
                    subscription.handler(event)
                except Exception as e:
                    print(f"   ✗ Handler failed: {subscription.name} - {str(e)}")

    def unsubscribe(self, subscription: EventSubscription) -> None:
        """Unsubscribe from events."""
        for event_type in subscription.event_types:
            key = event_type.value
            if key in self.subscriptions:
                self.subscriptions[key] = [
                    s for s in self.subscriptions[key]
                    if s != subscription
                ]

    def get_history(
        self,
        workflow: Optional[str] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get event history with optional filtering.

        Args:
            workflow: Filter by workflow name
            event_type: Filter by event type
            limit: Maximum events to return

        Returns:
            List of events
        """
        filtered = self.event_history

        if workflow:
            filtered = [e for e in filtered if e.workflow == workflow]
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]

        return filtered[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        stats = {
            "total_events": len(self.event_history),
            "subscriptions": len(self.subscriptions),
            "events_by_workflow": {},
            "events_by_type": {},
        }

        for event in self.event_history:
            if event.workflow not in stats["events_by_workflow"]:
                stats["events_by_workflow"][event.workflow] = 0
            stats["events_by_workflow"][event.workflow] += 1

            event_type = event.event_type.value
            if event_type not in stats["events_by_type"]:
                stats["events_by_type"][event_type] = 0
            stats["events_by_type"][event_type] += 1

        return stats
