# Claude Code Rules for AI SDLC Team

This file is automatically read by Claude Code at the start of each session. Follow these rules when working on this project.

## Critical Rules

### 1. Python Naming - NEVER Use Hyphens in Package Names
- ✅ Use underscores: `team_orchestrator/`, `backend_agent_workspace/`
- ❌ Never hyphens: `team-orchestrator/`, `backend-agent/`
- **Why:** Python import system fails with hyphens; pytest can't collect tests

### 2. Update ALL References When Renaming
When renaming directories or modules, grep and update:
- Dockerfile (COPY statements)
- `.github/workflows/tests.yml` (pytest commands, pip installs)
- All documentation files
- Import statements throughout codebase
```bash
grep -r "old_name" . --exclude-dir=.git
```

### 3. Code Quality - No Unused Imports
- Remove ALL unused imports before committing
- Common: `Optional`, `List`, `Dict`, `Any` when not needed
- Run: `flake8 . --select=F401` to find them

### 4. Line Length Maximum 127 Characters
- Break long lines across multiple lines
- Enforce with: `flake8 . --select=E501 --max-line-length=127`

### 5. F-Strings Must Have Placeholders
- ✅ Good: `f"Status: {status}"`
- ❌ Bad: `f"Status: success"` (use regular string)

### 6. No Unused Variable Assignments
- If assigned but never used, remove it
- Run: `flake8 . --select=F841` to find them

## Before Committing

Always run this checklist:
```bash
# Format and lint
black .
isort .
flake8 . --max-line-length=127

# Run tests
pytest . -v

# Verify no unused code
grep -r "^import\|^from" . --include="*.py" | grep F401
```

## File Organization

```
ai-sdlc-team/
├── CLAUDE.md                 # This file - rules Claude follows (auto-loaded)
├── CODING_STANDARDS.md       # Detailed guidelines for all contributors
├── .claude/
│   └── rules/               # Detailed rule files (referenced in CLAUDE.md)
│       ├── naming.md        # Python naming conventions
│       ├── testing.md       # Testing standards
│       └── ci_cd.md         # CI/CD pipeline rules
├── po-agent-workspace/
├── em-agent-workspace/
├── ux-agent-workspace/
├── backend-agent-workspace/
├── frontend-agent-workspace/
├── team_orchestrator/       # IMPORTANT: underscore, not hyphen
└── team-contracts/
```

## Common Pitfalls to Avoid

| Issue | Impact | How to Fix |
|-------|--------|-----------|
| Hyphen in package name | Pytest import fails | Use underscores only |
| Rename dir, skip Dockerfile | Docker build fails | grep for all references |
| Unused imports | CI/CD lint fails | Remove before commit |
| Long lines (>127 chars) | CI/CD lint fails | Break across lines |
| Empty f-strings | CI/CD lint fails | Use regular strings |
| Unused variables | CI/CD lint fails | Remove assignment |

## If CI/CD Fails

1. Check the error message in GitHub Actions
2. Run locally: `flake8 . --max-line-length=127 --statistics`
3. Fix violations before pushing
4. If import errors: Check conftest.py is at repo root with sys.path setup

## Testing with Underscore Packages

- conftest.py MUST be at repository root:
  ```python
  import sys
  from pathlib import Path
  
  repo_root = Path(__file__).parent
  sys.path.insert(0, str(repo_root))
  ```
- Import with: `from team_orchestrator import ...` (not hyphens)
- Run pytest from repo root: `pytest team_orchestrator/tests/ -v`

## Helpful References

- See `CODING_STANDARDS.md` for detailed guidelines for all contributors
- See `.claude/rules/naming.md` for detailed Python naming conventions
- See `.claude/rules/testing.md` for testing organization and patterns
- See `.claude/rules/ci_cd.md` for CI/CD pipeline debugging and updates
- See `.github/workflows/tests.yml` for the actual CI/CD pipeline
