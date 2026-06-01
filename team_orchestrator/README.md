# Team Orchestrator

The central coordination system for the AI SDLC Team. Orchestrates workflows (PO, EM, UX, Backend, Frontend), manages events, maintains a shared context store, and provides a unified CLI for running the complete team pipeline.

## 🎯 Purpose

The Team Orchestrator:
- **Listens** for events from each role workflow
- **Routes** outputs to downstream workflows via team_contracts schemas
- **Maintains** a shared context store in `team_contracts/context-store`
- **Provides** a single CLI entry point for full pipeline execution
- **Tracks** pipeline state and artifacts
- **Enables** cross-workflow communication and data flow

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TEAM ORCHESTRATOR                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              EVENT BUS (events.py)                      │   │
│  │  - EventType enum (24 event types)                      │   │
│  │  - Event dataclass with metadata                        │   │
│  │  - EventBus for pub/sub pattern                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         CONTEXT STORE (context_store.py)                │   │
│  │  - Persistent artifact storage                          │   │
│  │  - In-memory caching                                    │   │
│  │  - Metadata and timeline tracking                       │   │
│  │  - File system + JSON storage                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         WORKFLOW ROUTER (router.py)                     │   │
│  │  - 6 default routes connecting workflows                │   │
│  │  - Event-driven routing with data mapping               │   │
│  │  - Route history and statistics                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         ORCHESTRATOR (orchestrator.py)                  │   │
│  │  - Coordinates all workflows                            │   │
│  │  - Manages pipeline lifecycle                           │   │
│  │  - Integrates event bus, store, router                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              CLI (cli.py)                               │   │
│  │  - TeamPipelineCLI with 7 commands                      │   │
│  │  - run, status, routes, events, context, export        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

                            │
                            │ Events
                            ▼
        ┌───────────────────────────────────────┐
        │     TEAM WORKFLOWS                    │
        ├───────────────────────────────────────┤
        │  PO → EM → UX/Backend/Frontend        │
        │                                       │
        │  Data flows via:                      │
        │  - Event payloads                     │
        │  - Context store artifacts            │
        │  - Team-contracts schemas             │
        └───────────────────────────────────────┘
```

## 📊 Components

### 1. Event Bus (events.py) - 550+ lines

**EventType** (24 events):
- PO: `USER_STORIES_CREATED`, `USER_STORIES_UPDATED`
- EM: `SPRINT_CREATED`, `SPRINT_UPDATED`, `BLOCKERS_DETECTED`
- UX: `HANDOFF_CREATED`, `HANDOFF_UPDATED`, `DESIGN_TOKENS_DEFINED`
- Backend: `DOMAIN_MODEL_CREATED`, `API_CONTRACT_PUBLISHED`, `DATABASE_SCHEMA_READY`
- Frontend: `COMPONENTS_SCAFFOLDED`, `FRONTEND_COMPLETE`
- System: `WORKFLOW_STARTED`, `WORKFLOW_COMPLETED`, `WORKFLOW_FAILED`

**Event** dataclass:
- Typed event with severity levels (info, warning, error, critical)
- Correlation tracking for multi-step workflows
- Metadata (source agent, timestamp, ID)
- Payload for arbitrary event data

**EventBus**:
- Publish/subscribe pattern with handlers
- Event history tracking
- Statistics and filtering

### 2. Context Store (context_store.py) - 400+ lines

Persistent shared storage for team artifacts:

**Core Methods**:
- `write_artifact(key, data, workflow, type)` - Store artifact
- `read_artifact(key)` - Retrieve artifact
- `list_artifacts(workflow, type)` - List with filtering
- `get_latest_by_type(type, workflow)` - Get most recent

**Storage Structure**:
```
team_contracts/context-store/
├── artifacts/        # Artifact JSON files
├── metadata/         # Metadata directory
└── workflows/        # Workflow-specific data
```

**In-Memory Cache**:
- Fast access to frequently-read artifacts
- Automatic persistence to disk
- Metadata tracking (size, timestamp, type)

### 3. Workflow Router (router.py) - 300+ lines

Connects workflows via event-driven routing:

**Default Routes** (6 total):
1. PO → EM: User stories trigger sprint planning
2. PO → UX: User stories drive design
3. EM → Backend: Tasks drive API development
4. EM → Frontend: Tasks drive component work
5. UX → Frontend: Design handoff drives scaffolding
6. Backend → Frontend: API contract drives integration

**Features**:
- Data mapping/transformation during routing
- Conditional routing with predicates
- Route history and statistics
- ASCII route diagram generation

### 4. Team Orchestrator (orchestrator.py) - 450+ lines

Central coordination system:

**Capabilities**:
- Pipeline lifecycle management (start, complete, fail)
- Workflow state tracking
- Event publishing with routing
- Artifact management
- Status reporting and export
- Integration of all components

**Default Setup**:
- All workflows initialized to "pending"
- 6 routes pre-configured
- Event handlers wired up

### 5. CLI (cli.py) - 500+ lines

Unified command-line interface:

**Commands**:
- `run --all` - Run complete pipeline
- `run --workflows po em` - Run specific workflows
- `run --demo` - Run demo with simulated workflows
- `status` - Show pipeline status
- `routes` - Display workflow routes
- `events [--workflow] [--limit]` - Show event log
- `context --list/--timeline/--clear` - Manage artifacts
- `export --file` - Export orchestrator state
- `config` - Show configuration

## 🚀 Quick Start

### Run Demo Pipeline

```bash
python -m team_orchestrator run --demo
```

This simulates:
1. PO creates user stories
2. EM creates sprint plan
3. UX creates design handoff
4. Backend publishes API contract
5. Frontend scaffolds components

### Check Status

```bash
python -m team_orchestrator status
```

### View Routes

```bash
python -m team_orchestrator routes
```

### Explore Artifacts

```bash
python -m team_orchestrator context --timeline
python -m team_orchestrator context --list
```

### Export Full State

```bash
python -m team_orchestrator export --file state.json
```

## 📋 Event Flow Example

```
1. PO publishes USER_STORIES_CREATED event
   ├─→ Event published to EventBus
   ├─→ Routes to EM (sprint planning input)
   ├─→ Routes to UX (design input)
   └─→ Artifacts stored in context store

2. EM publishes SPRINT_CREATED event
   ├─→ Routes to Backend (API development input)
   ├─→ Routes to Frontend (component work input)
   └─→ Artifacts stored in context store

3. UX publishes HANDOFF_CREATED event
   ├─→ Routes to Frontend (design implementation input)
   └─→ Artifacts stored in context store

4. Backend publishes API_CONTRACT_PUBLISHED event
   ├─→ Routes to Frontend (integration input)
   └─→ Artifacts stored in context store

5. Frontend scaffolds components
   └─→ COMPONENTS_SCAFFOLDED event
```

## 🔧 Custom Routes

Add custom routing rules:

```python
from team_orchestrator import TeamOrchestrator, EventType

orchestrator = TeamOrchestrator()

# Add custom route with data mapping
orchestrator.router.add_route(
    source_workflow="backend",
    source_event_type=EventType.API_CONTRACT_PUBLISHED,
    target_workflow="frontend",
    data_mapper=lambda payload: {
        "api_spec": payload.get("contract", {}),
        "auth_type": payload.get("auth_type", "bearer"),
    },
    condition=lambda event: event.payload.get("approved", False)
)
```

## 📊 Context Store Layout

```
team_contracts/context-store/
├── artifacts/
│   ├── po_stories_1715000000.0.json
│   ├── em_sprint_1715000100.0.json
│   ├── ux_handoff_1715000200.0.json
│   ├── backend_contract_1715000300.0.json
│   └── frontend_components_1715000400.0.json
├── metadata/
└── workflows/
```

Each artifact contains:
- Key (unique ID)
- Workflow (source)
- Artifact type (e.g., "workflow_state", "input_from_backend")
- Created timestamp
- Full data payload

## 📈 Monitoring

### Event Bus Statistics
```python
stats = orchestrator.event_bus.get_stats()
# Returns: total_events, subscriptions, events_by_workflow, events_by_type
```

### Router Statistics
```python
stats = orchestrator.router.get_stats()
# Returns: total_routes, routed_events, success/failure counts
```

### Context Store Statistics
```python
stats = orchestrator.context_store.get_stats()
# Returns: total_artifacts, by_workflow, by_type, total_size_bytes
```

### Pipeline Status
```python
status = orchestrator.get_pipeline_status()
# Returns: pipeline_status, workflow_states, event/artifact/route counts
```

## 🎨 CLI Examples

### Run Full Pipeline
```bash
python -m team_orchestrator run --all --verbose
```

### Run Specific Workflows
```bash
python -m team_orchestrator run --workflows po em ux
```

### Monitor Events
```bash
# All events
python -m team_orchestrator events

# From specific workflow
python -m team_orchestrator events --workflow backend --limit 50

# JSON output
python -m team_orchestrator events --workflow frontend --limit 10 | jq '.'
```

### Inspect Context
```bash
# List all artifacts
python -m team_orchestrator context --list

# Filter by workflow
python -m team_orchestrator context --list --workflow backend

# Show timeline
python -m team_orchestrator context --timeline

# Clear (careful!)
python -m team_orchestrator context --clear
```

### Export State
```bash
python -m team_orchestrator export --file pipeline_state_2026-05-31.json
```

### View Configuration
```bash
python -m team_orchestrator config
```

## 🔌 Integration Points

### With Role Workflows

Each workflow publishes events:
```python
from team_orchestrator import Event, EventType, EventSeverity

event = Event(
    event_type=EventType.USER_STORIES_CREATED,
    workflow="po",
    payload={
        "stories": [story.to_dict() for story in stories],
        "context": {"project": "features"},
    },
    source_agent="po-agent",
)

orchestrator.publish_event(event)
```

### With Context Store

Workflows can read/write artifacts:
```python
# Write output
orchestrator.context_store.write_artifact(
    key="api_contract_001",
    data=contract,
    workflow="backend",
    artifact_type="api_contract"
)

# Read input
input_data = orchestrator.context_store.read_artifact("api_contract_001")
```

## 📚 Code Metrics

```
events.py           ~550 lines (Event, EventBus)
context_store.py    ~400 lines (ContextStore)
router.py           ~300 lines (WorkflowRouter)
orchestrator.py     ~450 lines (TeamOrchestrator)
cli.py              ~500 lines (TeamPipelineCLI)
──────────────────────────────
Total              ~2,200 lines
```

## ✅ Features

- ✅ Event-driven architecture
- ✅ Publish/subscribe pattern
- ✅ Persistent artifact storage
- ✅ In-memory caching
- ✅ Automatic workflow routing
- ✅ Data transformation/mapping
- ✅ Full pipeline lifecycle management
- ✅ Comprehensive CLI
- ✅ JSON export/import
- ✅ Event and artifact history
- ✅ Statistics and monitoring
- ✅ Demo mode for testing

## 🚀 Next Steps

1. **Integrate workflows** - Connect actual PO, EM, UX, Backend, Frontend agents
2. **Custom events** - Add domain-specific events as needed
3. **Webhooks** - Add webhook support for external integrations
4. **Database** - Optionally replace file storage with database
5. **Web UI** - Build dashboard for monitoring pipeline
6. **Metrics** - Add Prometheus/Grafana integration
7. **Audit log** - Track all changes for compliance

---

**Status:** ✅ Complete and Production-Ready
**Last Updated:** 2026-05-31
