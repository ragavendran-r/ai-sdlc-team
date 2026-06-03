# Context Store - Shared Team State

## Purpose

The context store is the **single source of truth** for team-wide state. All agent workspaces read from and write to this shared directory, ensuring:

- **Consistency**: All agents see the same current artifacts
- **Traceability**: Each write is timestamped and attributed to a source workflow
- **Non-blocking Collaboration**: Agents read asynchronously — no synchronous handoff required
- **Easy Testing**: Tests can pre-populate artifact files and verify agent behavior

## Implementation

The context store is implemented in Python as `team_orchestrator.ContextStore`:

```python
from team_orchestrator import ContextStore

context_store = ContextStore(base_path="team_contracts/context-store")

# Write an artifact (called by each workspace on approval)
context_store.write_artifact(
    key="backlog",
    data={"stories": [...]},
    artifact_type="backlog",
    source_workflow="po",
)

# Read an artifact (called by downstream workspaces on load)
sprint_plan = context_store.read_artifact("sprint-plan")  # dict or None
```

## Directory Structure

```
context-store/
├── artifacts/    # JSON files — one per artifact key (backlog, sprint-plan, etc.)
├── metadata/     # JSON metadata for each artifact (timestamp, source, version)
├── workflows/    # Per-workflow state files
└── README.md
```

## Artifact Keys

| Key | Written by | Read by |
|-----|-----------|---------|
| `backlog` | PO workspace | EM workspace |
| `sprint-plan` | EM workspace | UX workspace, Backend CLI |
| `ux-handoff` | UX workspace | Backend CLI, Frontend workspace |
| `api-contract` | Backend CLI | Frontend workspace |
| `frontend-output` | Frontend workspace | — |

## API Reference

```python
class ContextStore:
    def write_artifact(self, key: str, data: dict, artifact_type: str, source_workflow: str) -> None: ...
    def read_artifact(self, key: str) -> Optional[dict]: ...
    def list_artifacts(self, workflow: Optional[str] = None) -> List[dict]: ...
    def get_stats(self) -> dict: ...
    def export_timeline(self) -> str: ...
    def clear(self) -> None: ...
```

## Consistency Guarantees

- **Write Isolation**: Each workspace owns one artifact key and is the sole writer
- **Read Consistency**: Multiple workspaces can read concurrently (file reads are atomic on most OSes)
- **Persistence**: Artifacts survive server restarts — they are plain JSON files on disk

## CLI Commands

```bash
# List all stored artifacts
python run_team_pipeline.py context --list

# Show artifact timeline
python run_team_pipeline.py context --timeline

# Clear all artifacts (destructive — use with caution)
python run_team_pipeline.py context --clear
```
