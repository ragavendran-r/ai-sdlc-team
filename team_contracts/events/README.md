# Event Definitions

Events are the coordination mechanism between agent workspaces. When a workspace
approves and publishes an artifact it emits a typed `Event` object to the central
`EventBus`; the `WorkflowRouter` in `team_orchestrator` matches the event to a
route and forwards the payload downstream.

## Implementation

Events are implemented in Python in `team_orchestrator/events.py`:

```python
from team_orchestrator import EventBus, Event, EventType, EventSeverity

event_bus = EventBus()

# Publish
event_bus.publish(Event(
    event_type=EventType.USER_STORIES_CREATED,
    workflow="po",
    severity=EventSeverity.INFO,
    payload={"stories": [...]},
    source_agent="po-agent",
))

# Subscribe
def on_stories(event: Event) -> None:
    print(event.payload["stories"])

event_bus.subscribe(EventType.USER_STORIES_CREATED, on_stories)
```

## Event Categories

### Workflow output events

| Event | Emitted by | Triggers |
|-------|-----------|---------|
| `USER_STORIES_CREATED` | PO workspace | EM sprint planning |
| `USER_STORIES_UPDATED` | PO workspace | EM re-plan |
| `SPRINT_CREATED` | EM workspace | UX design + Backend contract |
| `SPRINT_UPDATED` | EM workspace | Downstream refresh |
| `HANDOFF_CREATED` | UX workspace | Backend + Frontend consumption |
| `HANDOFF_UPDATED` | UX workspace | Re-design loop |
| `API_CONTRACT_PUBLISHED` | Backend CLI | Frontend scaffolding |
| `COMPONENTS_SCAFFOLDED` | Frontend workspace | Pipeline complete |
| `FRONTEND_COMPLETE` | Frontend workspace | Final handoff |

### System events

| Event | Meaning |
|-------|---------|
| `WORKFLOW_STARTED` | A workflow node began |
| `WORKFLOW_COMPLETED` | A workflow finished successfully |
| `WORKFLOW_FAILED` | A workflow encountered an error |
| `BLOCKERS_DETECTED` | EM agent flagged a blocker |
| `DESIGN_TOKENS_DEFINED` | UX published design token set |
| `DOMAIN_MODEL_CREATED` | Backend completed domain modeling |
| `DATABASE_SCHEMA_READY` | Backend completed schema design |

## Event Structure

```python
@dataclass
class Event:
    event_type: EventType       # Enum value
    workflow: str               # e.g. "po", "em", "ux"
    severity: EventSeverity     # INFO / WARNING / ERROR / CRITICAL
    payload: dict               # Artifact data
    source_agent: str           # e.g. "po-agent"
    timestamp: datetime         # Auto-set on creation
    event_id: str               # UUID, auto-generated
```

## Adding New Events

1. Add a new value to `EventType` in `team_orchestrator/events.py`
2. Emit it from the agent workspace on completion
3. Add a route in `team_orchestrator/orchestrator.py` if it should trigger a downstream workflow
4. Document it in this README

## Event History

The `EventBus` stores all events in memory for the session:

```bash
# CLI: view recent events
python run_team_pipeline.py events

# Filter by workflow
python run_team_pipeline.py events --workflow po --limit 10
```
