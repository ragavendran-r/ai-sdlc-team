# Coding Standards & Guidelines

This document outlines the coding standards and lessons learned from building the AI SDLC Team system.

## Python Naming Conventions

### Directory & Package Names
- **MUST use underscores, NOT hyphens** for Python package directories
  - ✅ Good: `team_orchestrator/`, `backend_agent/`
  - ❌ Bad: `team-orchestrator/`, `backend-agent/`
  - **Why:** Python's import system doesn't recognize hyphens as valid package names. This causes pytest collection errors and import failures.

### File Names
- Use lowercase with underscores: `test_nodes.py`, `workflow_state.py`
- Use descriptive names that indicate the file's purpose

## Code Quality Rules

### Imports
- **Remove all unused imports** - Every import must be used
  - Run: `flake8 . --select=F401` to find unused imports
  - Common offenders: `Optional`, `List`, `Dict`, `Any`, `datetime` when not needed

### Line Length
- **Maximum 127 characters per line** (enforced by flake8)
- For long lines:
  - Break at logical points (commas, operators)
  - Use line continuation with backslash or implicit line joining in parentheses
  - Example:
    ```python
    # Good: broken across lines
    result = function_with_long_name(
        argument_one,
        argument_two,
        argument_three
    )
    
    # Also good: logical break
    long_string = (
        "Part one "
        "Part two "
        "Part three"
    )
    ```

### F-Strings
- **F-strings MUST contain variable placeholders** - No empty f-strings
  - ✅ Good: `f"Status: {status}"`
  - ❌ Bad: `f"Status: success"` (use regular string instead)

### Variables
- **Remove unused variable assignments**
  - If a result is assigned but never used, remove the assignment
  - Example:
    ```python
    # Bad
    result = tool.read_data()  # Never used
    
    # Good - just call it or remove if unneeded
    process_data()
    ```

### Variable Naming
- Use descriptive names: `user_stories`, `workflow_state`, `compliance_report`
- Avoid: `temp`, `data`, `result` (unless in limited scope)

## Project Structure Rules

### When Renaming/Moving Components
- **Update ALL references**, not just the obvious ones:
  - Dockerfile COPY/RUN statements
  - CI/CD workflow files (.github/workflows/)
  - Documentation files
  - Requirements.txt references
  - Import statements throughout codebase
  - Example commands in CONTRIBUTING.md, QUICK_START.md, README.md

- **Tools to find all references:**
  ```bash
  grep -r "old-name" . --exclude-dir=.git --exclude-dir=__pycache__
  sed -i 's/old-name/new-name/g' <files>
  ```

### Configuration Files
- Every workspace should have its own `requirements.txt` in `agents/`
- Root `requirements.txt` contains base dependencies only
- Document any new configuration in `.env.example`

## Testing Rules

### Test Organization
- Keep test files with the code they test
- Pattern: `module/tests/test_*.py`
- Use conftest.py at repository root for shared pytest configuration

### Test Imports
- Import modules in the simplest way possible
- Standard imports: `from module_name import Class, Function`
- Avoid complex importlib workarounds unless absolutely necessary

### Conftest.py
- **MUST exist at repository root** for pytest to find modules with underscores
- Configures `sys.path` to include the repository root:
  ```python
  import sys
  from pathlib import Path
  
  repo_root = Path(__file__).parent
  sys.path.insert(0, str(repo_root))
  ```

## CI/CD Rules

### Workflow Updates
- When files move or rename, update `.github/workflows/tests.yml`
- Pattern examples:
  - `pytest po-agent-workspace/tests/` → `pytest po_agent_workspace/tests/`
  - `pip install -r team-orchestrator/requirements.txt` → `pip install -r team_orchestrator/requirements.txt`

### Linting & Code Quality
- All code MUST pass:
  - `flake8 . --max-line-length=127`
  - `black --check .`
  - `isort --check-only .`
  - `mypy .` (type checking)

- Commands to fix automatically:
  ```bash
  black .                    # Format code
  isort .                    # Sort imports
  flake8 . --statistics      # Show violations
  ```

## Documentation Rules

### Updating Documentation
- When renaming directories/modules, update:
  - README.md
  - QUICK_START.md
  - CONTRIBUTING.md
  - All code examples in docs
  - Example commands in docstrings

### Code Examples
- All example commands must work as written
- Test documentation examples in CI/CD before merging
- Use correct module names (underscores, not hyphens)

## Common Mistakes to Avoid

| ❌ Don't | ✅ Do | Why |
|---------|-------|-----|
| `from typing import List, Optional, Dict, Any` (unused) | `from typing import Dict` (only used) | Flake8 enforces no unused imports |
| `f"Status: success"` | `"Status: success"` | F-strings require placeholders |
| `team-orchestrator/` directory | `team_orchestrator/` directory | Python needs underscores for imports |
| `result = tool.read()` (unused) | Remove assignment or use the result | Flake8 enforces no unused variables |
| Long line (>127 chars) | Break into multiple lines | Flake8 enforces max line length |
| Update Dockerfile, skip requirements.txt | Update ALL references | One missed reference breaks the build |
| Relative imports in tests | Standard imports with sys.path setup | Conftest handles the path setup |

## Pre-Commit Checklist

Before pushing code:

```bash
# 1. Format and sort
black .
isort .

# 2. Check quality
flake8 . --max-line-length=127 --statistics
mypy .

# 3. Run tests
pytest . -v

# 4. Verify no unused imports
grep -r "^import\|^from" . --include="*.py" | grep F401

# 5. Check line length
flake8 . --select=E501 --statistics
```

## References

- [PEP 8 Style Guide](https://pep8.org/)
- [Flake8 Rules](https://flake8.pycqa.org/)
- [Python Package Naming](https://docs.python.org/3/reference/import_system.html)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
