# CI/CD Pipeline Rules

## GitHub Actions Workflow

All changes must pass the workflow defined in `.github/workflows/tests.yml`

### Workflow Stages

1. **Linting** - Code quality checks
2. **Testing** - Unit tests on Python 3.9, 3.10, 3.11
3. **Security** - Trivy vulnerability scanning
4. **Docker Build** - Docker image creation

### When to Update Workflow

Update `.github/workflows/tests.yml` when:
- Renaming directories/packages
- Adding new agent workspaces
- Changing test locations
- Updating dependencies

### Common Updates

#### Renaming Package
If renaming from hyphens to underscores:

```bash
# OLD
pytest team-orchestrator/tests/ -v

# NEW
pytest team_orchestrator/tests/ -v

# OLD
pip install -r team-orchestrator/requirements.txt

# NEW
pip install -r team_orchestrator/requirements.txt
```

#### Adding New Workspace
For a new agent, add to workflow:
```bash
- name: Run <Agent> Agent Tests
  env:
    PYTHONPATH: ${{ github.workspace }}
  run: |
    pytest <agent>-agent-workspace/tests/ -v --cov=<agent>_agent_workspace
  continue-on-error: true
```

## Local Testing Before Pushing

### Pre-Commit Checklist

Always run before `git push`:

```bash
# 1. Format code
black .

# 2. Sort imports
isort .

# 3. Run linters
flake8 . --max-line-length=127 --statistics

# 4. Type check
mypy .

# 5. Run tests
pytest . -v

# 6. Build Docker image
docker build -t ai-sdlc-team:test .
```

### Fixing Common Failures

#### Unused Imports (F401)
```bash
flake8 . --select=F401

# Fix: Remove the import line
```

#### Line Too Long (E501)
```bash
flake8 . --select=E501 --max-line-length=127

# Fix: Break line across multiple lines
old_string = "very long string that is over 127 characters which is too long"

new_string = (
    "very long string that is over 127 characters "
    "which is now split properly"
)
```

#### Unused Variables (F841)
```bash
flake8 . --select=F841

# Fix: Remove the assignment if truly unused
result = expensive_function()  # If result not used, remove this line
```

#### F-String Missing Placeholders (F541)
```bash
flake8 . --select=F541

# Fix: Use regular string instead
bad = f"Status: success"   # No placeholder
good = "Status: success"   # Regular string
```

## Dockerfile Updates

When renaming directories, update `Dockerfile`:

```dockerfile
# OLD
COPY team-orchestrator/requirements.txt ./orchestrator-requirements.txt
RUN pip install -r orchestrator-requirements.txt

# NEW
COPY team_orchestrator/requirements.txt ./orchestrator-requirements.txt
RUN pip install -r orchestrator-requirements.txt

# Also update the final command if it references the package
CMD ["python", "-m", "team_orchestrator"]
```

## Debugging CI/CD Failures

### If Tests Fail on GitHub

1. **Check the workflow run**: Go to Actions tab, click the failing run
2. **Read the error**: GitHub shows which step failed and why
3. **Reproduce locally**:
   ```bash
   # If it's a test failure
   pytest . -v --tb=short
   
   # If it's a lint failure
   flake8 . --max-line-length=127 --statistics
   ```
4. **Fix locally, test, then push**
5. **Push the fix**: GitHub will re-run the workflow

### Common Workflow Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'team_orchestrator'` | conftest.py missing or broken | Ensure conftest.py exists at repo root with sys.path setup |
| `ImportError: attempted relative import` | Invalid import in test | Use standard imports: `from team_orchestrator import ...` |
| Tests pass locally, fail on CI | PYTHONPATH not set | Check workflow sets `PYTHONPATH: ${{ github.workspace }}` |
| Flake8 fails | Unused imports, long lines, etc. | Run `flake8 . --max-line-length=127 --statistics` locally |
| Docker build fails | Path reference wrong | Check Dockerfile uses underscore names: `team_orchestrator/` |

## Security Scanning

Trivy vulnerability scanner runs on:
- `fs` (filesystem) scan of entire repo
- Checks for known vulnerabilities in dependencies

If Trivy finds issues:
1. Check the SARIF report in GitHub Security tab
2. Update vulnerable dependencies
3. Re-run the scan

## Continue-On-Error Rules

Tests marked with `continue-on-error: true` will not block the pipeline:

```yaml
- name: Run Tests
  run: pytest . -v
  continue-on-error: true  # Failure doesn't block rest of workflow
```

Use sparingly - typically only for optional integrations, not core tests.
