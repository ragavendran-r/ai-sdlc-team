# Python Naming Conventions

## Package & Directory Names

### CRITICAL: Use Underscores, Never Hyphens

**Why:** Python's import system doesn't recognize hyphens as valid in module names. This causes:
- `ModuleNotFoundError` when importing
- Pytest collection failures
- Relative import errors

### Correct Examples
✅ `team_orchestrator/`
✅ `po_agent_workspace/`
✅ `backend_agent_workspace/`
✅ `test_nodes.py`
✅ `user_story.py`

### Incorrect Examples
❌ `team-orchestrator/` (WILL BREAK)
❌ `po_agent_workspace/` (WILL BREAK)
❌ `test-nodes.py` (WILL BREAK)
❌ `user-story.py` (WILL BREAK)

## When Renaming

If you rename a package from hyphens to underscores:

1. Use git to rename: `git mv team-orchestrator team_orchestrator`
2. Find all references: `grep -r "team-orchestrator" . --exclude-dir=.git`
3. Update in these locations:
   - Dockerfile (`COPY` statements)
   - `.github/workflows/tests.yml` (pytest commands, pip install)
   - All `.md` files (documentation, examples)
   - Python imports throughout codebase
   - CI/CD configuration

### Example Checklist
- [ ] `Dockerfile` - COPY statements
- [ ] `.github/workflows/tests.yml` - all pytest and pip references
- [ ] `README.md` - code examples
- [ ] `QUICK_START.md` - setup examples
- [ ] `CONTRIBUTING.md` - development instructions
- [ ] All Python files - import statements
- [ ] `.env.example` - path references

## Variable & Function Names

Use lowercase with underscores (snake_case):
✅ `user_stories`, `workflow_state`, `api_contract`
❌ `userStories`, `WorkflowState`, `ApiContract`

## Class Names

Use PascalCase:
✅ `TeamOrchestrator`, `BackendWorkflowState`, `ContextStore`
❌ `team_orchestrator`, `backend_workflow_state`, `context_store`

## Module Files

Use lowercase with underscores:
✅ `orchestrator.py`, `workflow_state.py`, `test_nodes.py`
❌ `Orchestrator.py`, `WorkflowState.py`, `TestNodes.py`
