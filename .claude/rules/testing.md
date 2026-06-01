# Testing Standards

## Test Organization

### File Structure
```
component/
├── agents/
│   ├── __init__.py
│   ├── nodes.py
│   ├── workflow.py
│   └── requirements.txt
└── tests/
    ├── __init__.py
    ├── test_nodes.py
    ├── test_workflow.py
    └── test_tools.py
```

### File Naming
- Test files: `test_*.py` (not `*_test.py`)
- Test classes: `Test<ComponentName>` (e.g., `TestEventBus`)
- Test methods: `test_<action>_<scenario>` (e.g., `test_publish_event`)

## Import Configuration

### conftest.py at Repository Root

MUST exist at the root of the repository:

```python
"""Root pytest configuration for all tests."""

import sys
from pathlib import Path

# Add repository root to sys.path so all packages can be imported
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))
```

**Why:** Allows pytest to find underscore-based package names:
- Without this: pytest can't import `team_orchestrator`
- With this: `from team_orchestrator import ...` works

### Test Imports

Use standard imports (not relative imports):

✅ Good:
```python
import pytest
from team_orchestrator import TeamOrchestrator, Event
from backend_agent_workspace.agents.state import BackendWorkflowState
```

❌ Bad:
```python
from .. import TeamOrchestrator  # Relative imports fail with hyphens
import importlib
team_orch = importlib.import_module('team-orchestrator')  # Too complex
```

## Running Tests

### From Repository Root
```bash
# Run all tests
pytest . -v

# Run specific workspace
pytest team_orchestrator/tests/ -v

# Run specific test file
pytest po_agent_workspace/tests/test_nodes.py -v

# Run with coverage
pytest . -v --cov=. --cov-report=html
```

### In CI/CD
```bash
pytest team_orchestrator/tests/ -v --cov=team_orchestrator --cov-report=xml
```

## Test Quality

### No Test Violations

All tests must pass:
```bash
# Before committing
pytest . -v
```

### Mocking External Dependencies

Use mocks for:
- External API calls
- Database operations
- File system operations
- Long-running operations

### Test Names Are Documentation

Good test names explain what's being tested:

✅ Good:
- `test_publish_event_to_subscribers`
- `test_route_with_mapper_transforms_data`
- `test_filter_by_workflow_returns_matching_routes`

❌ Bad:
- `test_event`
- `test_route`
- `test_filter`

## Common Testing Patterns

### Testing State Changes
```python
def test_publish_event_updates_history(self):
    """Test that publishing event adds to history."""
    orchestrator = TeamOrchestrator()
    initial_count = len(orchestrator.event_history)
    
    orchestrator.publish_event(test_event)
    
    assert len(orchestrator.event_history) == initial_count + 1
```

### Testing Error Handling
```python
def test_invalid_workflow_raises_error(self):
    """Test that invalid workflow raises ValueError."""
    orchestrator = TeamOrchestrator()
    
    with pytest.raises(ValueError):
        orchestrator.mark_workflow_complete("invalid-workflow")
```

### Testing with Fixtures
```python
@pytest.fixture
def orchestrator():
    """Create a test orchestrator."""
    return TeamOrchestrator()

def test_start_pipeline(orchestrator):
    """Test pipeline startup."""
    orchestrator.start_pipeline()
    assert orchestrator.pipeline_started
```
