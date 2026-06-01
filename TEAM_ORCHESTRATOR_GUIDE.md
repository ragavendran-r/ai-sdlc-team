# Team Orchestrator - Complete Guide

Complete guide for the Team Orchestrator that coordinates all AI SDLC Team workflows.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Event System](#event-system)
5. [Context Store](#context-store)
6. [Workflow Routes](#workflow-routes)
7. [CLI Reference](#cli-reference)
8. [Integration Guide](#integration-guide)
9. [Examples](#examples)
10. [Best Practices](#best-practices)

## Overview

The Team Orchestrator is a central coordination system that:

- **Manages events** from each role workflow (PO, EM, UX, Backend, Frontend)
- **Routes data** between workflows using team_contracts schemas
- **Stores artifacts** in a shared context store
- **Tracks pipeline** state and execution
- **Provides CLI** for running the complete team pipeline

### Key Goals

✅ Single source of truth for team artifacts
✅ Event-driven data flow between workflows
✅ Automatic routing with data transformation
✅ Full observability and auditability
✅ Easy integration with role workflows

## Architecture

### High-Level Flow

```
PO Workflow          EM Workflow         UX Workflow
    │                   │                   │
    └──→ Event Bus ←────┴───────────────────┘
         │
         ├─→ Context Store (persistent)
         ├─→ Event History (tracking)
         ├─→ Workflow Router (routing)
         │
         └──→ Backend Workflow    Frontend Workflow
              │                   │
              └──────────────────┘
```

### Component Relationships

```
┌─────────────────────────────────────────┐
│        TeamOrchestrator                 │
│  (central coordinator)                  │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   EventBus                       │  │
│  │ - Publish/subscribe pattern      │  │
│  │ - Event history                  │  │
│  │ - 24 event types                 │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   ContextStore                   │  │
│  │ - Persistent artifact storage    │  │
│  │ - In-memory caching              │  │
│  │ - File system + JSON             │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   WorkflowRouter                 │  │
│  │ - Event-driven routing           │  │
│  │ - Data mapping/transformation    │  │
│  │ - 6 default routes               │  │
│  └──────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
         │
         └──→ TeamPipelineCLI (7 commands)
```

## Components

### 1. Event Bus (events.py)

Central pub/sub system for workflow events.

**Core Classes**:
- `EventType` - 24 event types across all workflows
- `Event` - Type-safe event with metadata
- `EventBus` - Publisher, subscriber, history

**Event Types**:

```python
# PO Events
USER_STORIES_CREATED
USER_STORIES_UPDATED

# EM Events  
SPRINT_CREATED
SPRINT_UPDATED
BLOCKERS_DETECTED

# UX Events
HANDOFF_CREATED
HANDOFF_UPDATED
DESIGN_TOKENS_DEFINED

# Backend Events
DOMAIN_MODEL_CREATED
API_CONTRACT_PUBLISHED
DATABASE_SCHEMA_READY

# Frontend Events
COMPONENTS_SCAFFOLDED
FRONTEND_COMPLETE

# System Events
WORKFLOW_STARTED
WORKFLOW_COMPLETED
WORKFLOW_FAILED
```

**Usage**:

```python
from team_orchestrator import Event, EventType, EventSeverity

# Create event
event = Event(
    event_type=EventType.USER_STORIES_CREATED,
    workflow="po",
    severity=EventSeverity.INFO,
    payload={
        "stories": [...],
        "context": {...}
    },
    source_agent="po-agent"
)

# Publish through orchestrator
orchestrator.publish_event(event)
```

### 2. Context Store (context_store.py)

Persistent shared storage for team artifacts.

**Core Methods**:

```python
# Write artifact
path = store.write_artifact(
    key="api_contract_001",
    data=contract_dict,
    workflow="backend",
    artifact_type="api_contract"
)

# Read artifact
data = store.read_artifact("api_contract_001")

# List artifacts
artifacts = store.list_artifacts(
    workflow="backend",  # optional
    artifact_type="api_contract"  # optional
)

# Get latest of type
latest = store.get_latest_by_type(
    artifact_type="api_contract",
    workflow="backend"  # optional
)
```

**Storage Structure**:

```
team_contracts/context-store/
├── artifacts/
│   ├── po_stories_1234567890.json
│   ├── em_sprint_1234567891.json
│   ├── ux_handoff_1234567892.json
│   ├── backend_contract_1234567893.json
│   └── frontend_components_1234567894.json
├── metadata/
└── workflows/
```

**File Format**:

```json
{
  "key": "api_contract_001",
  "workflow": "backend",
  "artifact_type": "api_contract",
  "created_at": "2026-05-31T12:34:56.789000",
  "data": {
    "id": "API-001",
    "feature_name": "User Authentication",
    ...
  }
}
```

### 3. Workflow Router (router.py)

Routes events between workflows with data transformation.

**Default Routes**:

```
1. PO → EM
   Event: USER_STORIES_CREATED
   Data: stories, planning_context

2. PO → UX
   Event: USER_STORIES_CREATED
   Data: stories, design_context

3. EM → Backend
   Event: SPRINT_CREATED
   Data: sprint_plan, user_stories

4. EM → Frontend
   Event: SPRINT_CREATED
   Data: sprint_plan, tasks

5. UX → Frontend
   Event: HANDOFF_CREATED
   Data: ux_handoff, design_tokens

6. Backend → Frontend
   Event: API_CONTRACT_PUBLISHED
   Data: api_contract
```

**Custom Routes**:

```python
orchestrator.router.add_route(
    source_workflow="po",
    source_event_type=EventType.USER_STORIES_CREATED,
    target_workflow="custom_service",
    data_mapper=lambda payload: {
        "stories": payload.get("stories", []),
        "filtered": [s for s in payload.get("stories", [])
                    if s.get("priority") == "high"]
    },
    condition=lambda event: event.severity != EventSeverity.ERROR
)
```

### 4. Team Orchestrator (orchestrator.py)

Central coordination system integrating all components.

**Key Methods**:

```python
# Pipeline lifecycle
orchestrator.start_pipeline()
orchestrator.complete_pipeline()
orchestrator.fail_pipeline("error message")

# Workflow tracking
orchestrator.mark_workflow_complete("po")
orchestrator.mark_workflow_failed("backend", "API error")

# Event handling
orchestrator.publish_event(event)

# Reporting
status = orchestrator.get_pipeline_status()
orchestrator.print_status_report()
orchestrator.export_state("state.json")
```

### 5. CLI (cli.py)

Command-line interface for the orchestrator.

**Commands**:

```bash
# Run workflows
run --all                          # Complete pipeline
run --workflows po em             # Specific workflows
run --demo                        # Demo with simulated workflows
run --verbose                     # Verbose output

# Query state
status                            # Pipeline status
status --json                     # JSON output

routes                            # Show workflow routes
routes --json                     # JSON output

events                            # Show event log
events --workflow backend         # Filter by workflow
events --limit 50                 # Limit results

context --list                    # List artifacts
context --timeline                # Show timeline
context --clear                   # Clear store

# Export/config
export --file state.json          # Export state
config                            # Show configuration
```

## Event System

### Event Structure

```python
@dataclass
class Event:
    event_type: EventType              # What happened
    workflow: str                      # Which workflow
    timestamp: datetime                # When
    severity: EventSeverity            # Info/Warning/Error/Critical
    payload: Dict[str, Any]            # Event data
    event_id: str                      # Unique ID
    correlation_id: str                # Multi-event tracking
    parent_event_id: Optional[str]     # Event chain
    source_agent: str                  # What agent published
    downstream_events: List[str]       # Triggered events
```

### Publishing Events

```python
# From a workflow agent
from team_orchestrator import Event, EventType

event = Event(
    event_type=EventType.USER_STORIES_CREATED,
    workflow="po",
    payload={
        "stories": [
            {"id": "US-001", "title": "Feature A"},
            {"id": "US-002", "title": "Feature B"},
        ],
        "context": {"sprint": "S-001"}
    },
    source_agent="po-agent"
)

# Publish via orchestrator
orchestrator.publish_event(event)

# Or via event bus directly
orchestrator.event_bus.publish(event)
```

### Subscribing to Events

```python
# Subscribe to specific event types
def handle_user_stories(event: Event):
    print(f"Stories created: {len(event.payload['stories'])}")

orchestrator.event_bus.subscribe(
    event_types=[EventType.USER_STORIES_CREATED],
    handler=handle_user_stories,
    name="user_stories_handler"
)

# When event is published, handler is called automatically
```

## Context Store

### Storing Artifacts

```python
# Write workflow output
orchestrator.context_store.write_artifact(
    key="api_contract_001",
    data=api_contract_dict,
    workflow="backend",
    artifact_type="api_contract"
)

# With Pydantic model (auto converts)
orchestrator.context_store.write_artifact(
    key="sprint_plan_001",
    data=sprint_plan_object,  # Has .to_dict() method
    workflow="em",
    artifact_type="sprint_plan"
)
```

### Reading Artifacts

```python
# Read by key
contract = orchestrator.context_store.read_artifact("api_contract_001")

# Get latest of type
latest_contract = orchestrator.context_store.get_latest_by_type(
    artifact_type="api_contract",
    workflow="backend"
)

# List all
all_artifacts = orchestrator.context_store.list_artifacts()

# List by type
contracts = orchestrator.context_store.list_artifacts(
    artifact_type="api_contract"
)

# List by workflow
backend_artifacts = orchestrator.context_store.list_artifacts(
    workflow="backend"
)
```

### Artifact Lifecycle

```
Write → Stored in file system
      → Cached in memory
      → Metadata indexed
      
Read  → Check cache (fast)
     → If not cached, read from disk
     → Update cache
     
List  → Query file system
     → Filter by workflow/type
     → Return metadata only (fast)
```

## Workflow Routes

### Route Structure

```python
WorkflowRoute(
    source_workflow="po",
    source_event_type=EventType.USER_STORIES_CREATED,
    target_workflow="em",
    data_mapper=lambda payload: {...},  # Transform data
    condition=lambda event: True,       # When to route
)
```

### Data Mapping

Transforms source payload to target input:

```python
# Default PO → EM mapping
data_mapper = lambda payload: {
    "user_stories": payload.get("stories", []),
    "planning_context": payload.get("context", {}),
}

# Custom mapping
data_mapper = lambda payload: {
    "high_priority_stories": [
        s for s in payload.get("stories", [])
        if s.get("priority") == "high"
    ],
    "estimated_velocity": len(payload.get("stories", [])) * 5,
}
```

### Conditional Routing

Route only when condition is met:

```python
orchestrator.router.add_route(
    source_workflow="backend",
    source_event_type=EventType.API_CONTRACT_PUBLISHED,
    target_workflow="frontend",
    condition=lambda event: event.payload.get("approved", False)
)
```

## CLI Reference

### Run Commands

```bash
# Full pipeline (all workflows)
python run_team_pipeline.py run --all

# Specific workflows
python run_team_pipeline.py run --workflows po em ux

# Demo mode (simulated)
python run_team_pipeline.py run --demo

# With verbose output
python run_team_pipeline.py run --all --verbose
```

### Status Commands

```bash
# Pipeline status
python run_team_pipeline.py status

# JSON output
python run_team_pipeline.py status --json
```

### Route Commands

```bash
# Show routes
python run_team_pipeline.py routes

# JSON format
python run_team_pipeline.py routes --json
```

### Event Commands

```bash
# All events
python run_team_pipeline.py events

# From specific workflow
python run_team_pipeline.py events --workflow backend

# Limited results
python run_team_pipeline.py events --limit 50

# Filter and limit
python run_team_pipeline.py events --workflow frontend --limit 10
```

### Context Commands

```bash
# List artifacts
python run_team_pipeline.py context --list

# Show timeline
python run_team_pipeline.py context --timeline

# Filter by workflow
python run_team_pipeline.py context --list --workflow backend

# Clear all (careful!)
python run_team_pipeline.py context --clear
```

### Export/Config

```bash
# Export state
python run_team_pipeline.py export --file state.json

# Show configuration
python run_team_pipeline.py config
```

## Integration Guide

### Integrating a Workflow

Each workflow should:

1. **Publish events** when it completes
2. **Read input** from context store
3. **Write output** to context store

### Example: Backend Workflow Integration

```python
from team_orchestrator import TeamOrchestrator, Event, EventType

# Get orchestrator (could be injected)
orchestrator = TeamOrchestrator()

# Read input from context store
api_spec = orchestrator.context_store.get_latest_by_type(
    artifact_type="api_spec"
)

# Run workflow...
# Generate API contract...

# Write output
orchestrator.context_store.write_artifact(
    key=f"api_contract_{timestamp}",
    data=api_contract,
    workflow="backend",
    artifact_type="api_contract"
)

# Publish event
event = Event(
    event_type=EventType.API_CONTRACT_PUBLISHED,
    workflow="backend",
    payload={"contract": api_contract},
    source_agent="backend-agent"
)
orchestrator.publish_event(event)
```

### Handling Routes

Workflows can subscribe to routes they're interested in:

```python
# Frontend wants to know when API contract is published
orchestrator.event_bus.subscribe(
    event_types=[EventType.API_CONTRACT_PUBLISHED],
    handler=lambda event: process_api_contract(event.payload),
    name="frontend_api_handler"
)
```

## Examples

### Example 1: Run Demo Pipeline

```bash
python run_team_pipeline.py run --demo
```

This simulates:
1. PO creates user stories
2. EM creates sprint plan
3. UX creates design handoff
4. Backend publishes API contract
5. Frontend scaffolds components

### Example 2: Check Pipeline Status

```bash
python run_team_pipeline.py status
```

Output:
```
================================================================================
 TEAM PIPELINE STATUS REPORT
================================================================================

Pipeline Status: running
✅ All systems operational

Started: 2026-05-31T12:34:56.789000
Completed: 2026-05-31T12:35:12.234000

Workflow States:
─────────────────────────────────────
✅ po          completed
✅ em          completed
✅ ux          completed
✅ backend     completed
✅ frontend    completed

Statistics:
─────────────────────────────────────
Events Published: 32
Artifacts Stored: 15
Routes Executed: 12
```

### Example 3: Export and Inspect State

```bash
python run_team_pipeline.py export --file pipeline_state.json

# Inspect with jq
cat pipeline_state.json | jq '.orchestrator_state.workflow_states'
```

### Example 4: Custom Route

```python
from team_orchestrator import TeamOrchestrator, EventType

orchestrator = TeamOrchestrator()

# Only route high-priority stories to UX
orchestrator.router.add_route(
    source_workflow="po",
    source_event_type=EventType.USER_STORIES_CREATED,
    target_workflow="ux",
    data_mapper=lambda p: {
        "stories": [s for s in p.get("stories", [])
                   if s.get("priority") == "high"]
    },
    condition=lambda e: any(
        s.get("priority") == "high"
        for s in e.payload.get("stories", [])
    )
)

# Run demo
orchestrator.start_pipeline()
# ... publish events ...
orchestrator.complete_pipeline()
```

## Best Practices

### Event Publishing

✅ **DO**:
- Include all relevant data in payload
- Use specific event types
- Set appropriate severity levels
- Include source agent name

❌ **DON'T**:
- Publish events synchronously from critical paths
- Include sensitive data in payloads
- Use generic event types
- Publish duplicate events

### Context Store

✅ **DO**:
- Use descriptive keys
- Set correct artifact types
- Write after major milestones
- Read latest version

❌ **DON'T**:
- Store credentials in artifacts
- Use overly long keys
- Store duplicate artifacts
- Assume artifact exists

### Routing

✅ **DO**:
- Define clear route conditions
- Transform data appropriately
- Use meaningful target workflows
- Test routes before production

❌ **DON'T**:
- Create circular routes
- Transform data incorrectly
- Route to invalid workflows
- Route critical errors

### Error Handling

✅ **DO**:
- Publish WORKFLOW_FAILED events
- Mark workflows as failed
- Export state before failing
- Include error messages

❌ **DON'T**:
- Silently fail
- Leave orchestrator in inconsistent state
- Lose error context
- Continue after critical errors

---

**Last Updated:** 2026-05-31
**Version:** 1.0
