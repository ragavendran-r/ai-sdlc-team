# Team Contracts - Inter-Agent Communication Layer

## Purpose

The team contracts define the **communication protocols, schemas, and shared state** that enable agents to collaborate reliably:

- **Schema Validation**: All handoffs between agents use Pydantic-validated Python models
- **Event-Driven Communication**: Agents emit and subscribe to typed `Event` objects via `EventBus`
- **Shared Context**: A central `ContextStore` stores JSON artifacts on disk for cross-workspace handoff
- **Type Safety**: 26 Pydantic schemas ensure consistency across all agents

## Architecture

```
┌─────────────────────────────────────────────┐
│        Shared Context Store                 │
│  (JSON artifacts in context-store/          │
│   artifacts/ — read and written by each     │
│   agent workspace on approval)              │
└─────────────────────────────────────────────┘
         ↑                ↑
    ┌────────────┐  ┌──────────────┐
    │  schemas/  │  │  EventBus    │
    │  (Python   │  │  (Python,    │
    │  Pydantic) │  │  EventType)  │
    └────────────┘  └──────────────┘
```

## Folder Structure

```
team_contracts/
├── schemas/          # Python Pydantic models for all inter-agent artifacts
├── events/           # Event type documentation (implementation in team_orchestrator/events.py)
├── context-store/    # On-disk artifact storage (JSON files)
└── README.md
```

### Folders

**`schemas/`**
- Python Pydantic models (`BaseModel`) for all handoff data
- Examples:
  - `backlog.py` — PO → EM: user stories, priorities, acceptance criteria
  - `sprint_plan.py` — EM → UX/Backend: tasks, estimates, dependencies
  - `ux_handoff.py` — UX → Backend/Frontend: personas, user flows, wireframe briefs
  - `api_contract.py` — Backend → Frontend: endpoints, schemas, auth
- Each schema includes field validation, defaults, and a `to_dict()` helper

**`events/`**
- Documents the event types used for agent coordination
- Implementation lives in `team_orchestrator/events.py` (`EventType` enum, `EventBus`)
- 24 event types: `USER_STORIES_CREATED`, `SPRINT_CREATED`, `HANDOFF_CREATED`,
  `API_CONTRACT_PUBLISHED`, `COMPONENTS_SCAFFOLDED`, and more

**`context-store/`**
- On-disk JSON artifact storage (`artifacts/`, `metadata/`, `workflows/` subdirs)
- Implemented in `team_orchestrator/context_store.py` (`ContextStore` class)
- Each web interface writes its artifact on approval; downstream interfaces read on load

## Key Principles

1. **Schema-First**: All inter-agent communication is validated against Pydantic models
2. **File-Based Handoff**: Artifacts are JSON files on disk — no network calls between workspaces
3. **Event Sourcing**: `EventBus` logs all events with timestamps for audit and replay
4. **Context as Source of Truth**: `ContextStore` is the single source of truth for team state

## Artifact Flow

| Artifact | Produced by | Consumed by | Schema |
|----------|-------------|-------------|--------|
| `backlog` | PO Agent | EM Agent | `schemas/backlog.py` |
| `sprint-plan` | EM Agent | UX Agent, Backend Agent | `schemas/sprint_plan.py` |
| `ux-handoff` | UX Agent | Backend Agent, Frontend Agent | `schemas/ux_handoff.py` |
| `api-contract` | Backend Agent | Frontend Agent | `schemas/api_contract.py` |
| `frontend-output` | Frontend Agent | — | `schemas/frontend_output.py` |

## Usage

### Reading an artifact

```python
from team_orchestrator import ContextStore

context_store = ContextStore(base_path="team_contracts/context-store")
sprint_plan = context_store.read_artifact("sprint-plan")  # returns dict or None
```

### Writing an artifact

```python
context_store.write_artifact(
    key="backlog",
    data=backlog_dict,
    artifact_type="backlog",
    source_workflow="po",
)
```

### Publishing an event

```python
from team_orchestrator import EventBus, Event, EventType

event_bus = EventBus()
event_bus.publish(Event(
    event_type=EventType.USER_STORIES_CREATED,
    workflow="po",
    payload={"stories": [...]},
    source_agent="po-agent",
))
```

## Development Notes

- Add new schemas to `schemas/` as Pydantic `BaseModel` subclasses
- Register new artifacts in `team_orchestrator/context_store.py`
- Add new `EventType` values in `team_orchestrator/events.py`
- Keep schemas simple and focused — one artifact type per file
