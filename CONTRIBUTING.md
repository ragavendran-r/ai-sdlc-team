# Contributing to AI SDLC Team

Welcome! This guide explains how to customize, extend, and contribute to the AI SDLC Team system.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Project Structure](#project-structure)
4. [Making Changes](#making-changes)
5. [Customization Guide](#customization-guide)
6. [Extending the System](#extending-the-system)
7. [Testing](#testing)
8. [Submitting Changes](#submitting-changes)
9. [Code Standards](#code-standards)
10. [FAQ](#faq)

## Getting Started

### Prerequisites

- Python 3.9+
- Git
- Docker & Docker Compose (optional, for containerized development)
- An Anthropic API key

### Fork and Clone

```bash
# Fork the repository on GitHub
# https://github.com/your-org/ai-sdlc-team

# Clone your fork
git clone https://github.com/YOUR-USERNAME/ai-sdlc-team.git
cd ai-sdlc-team

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL-ORG/ai-sdlc-team.git
```

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install base requirements
pip install -r requirements.txt

# Install agent-specific requirements
pip install -r po-agent-workspace/agents/requirements.txt
pip install -r em-agent-workspace/agents/requirements.txt
pip install -r ux-agent-workspace/agents/requirements.txt
pip install -r backend-agent-workspace/agents/requirements.txt
pip install -r frontend-agent-workspace/agents/requirements.txt
pip install -r team-orchestrator/requirements.txt

# Install development tools
pip install pytest pytest-cov black flake8 isort mypy
```

### 3. Configure Environment

```bash
# Copy example file
cp .env.example .env

# Edit .env with your settings
nano .env  # or your favorite editor

# Minimum required
export ANTHROPIC_API_KEY=sk-your-key-here
```

### 4. Verify Setup

```bash
# Run a quick test
python run_team_pipeline.py run --demo

# Check all tests pass
pytest team-orchestrator/tests/ -v
```

## Project Structure

```
ai-sdlc-team/
├── po-agent-workspace/              # Product Owner agent
│   ├── agents/
│   │   ├── nodes.py                 # Agent implementations
│   │   ├── workflow.py              # LangGraph workflow
│   │   ├── state.py                 # Type-safe state
│   │   └── requirements.txt
│   └── tests/
│
├── em-agent-workspace/              # Engineering Manager agent
├── ux-agent-workspace/              # UX Designer agent
├── backend-agent-workspace/         # Backend Engineer agent
├── frontend-agent-workspace/        # Frontend Engineer agent
│
├── team-orchestrator/               # Central orchestrator
│   ├── events.py                    # Event system
│   ├── context_store.py             # Artifact storage
│   ├── router.py                    # Workflow routing
│   ├── orchestrator.py              # Coordination
│   ├── cli.py                       # CLI interface
│   └── tests/
│
├── team-contracts/                  # Shared schemas
│   └── schemas/
│       ├── user_story.py            # Core schemas
│       └── ...
│
├── examples/                        # Example projects
│   └── ecommerce-platform/          # Sample project walkthrough
│
├── .github/workflows/               # CI/CD pipelines
│   └── tests.yml
│
├── docker-compose.yml               # Local development
├── Dockerfile                       # Container image
├── .env.example                     # Configuration template
├── requirements.txt                 # Base dependencies
└── run_team_pipeline.py             # CLI entry point
```

## Making Changes

### 1. Create a Feature Branch

```bash
# Keep main branch clean
git checkout -b feature/my-feature
# or
git checkout -b bugfix/issue-description
```

### 2. Make Your Changes

```bash
# Edit files as needed
# Follow code standards (see below)

# Run tests frequently
pytest team-orchestrator/tests/ -v

# Check formatting
black . --check
isort . --check-only
```

### 3. Commit with Clear Messages

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add feature X to Y agent

- Describe what changed
- Explain why it was needed
- Reference any issues (#123)"
```

### 4. Push and Create PR

```bash
# Push to your fork
git push origin feature/my-feature

# Create Pull Request on GitHub
# - Fill in the PR template
# - Link any related issues
# - Describe testing done
```

## Customization Guide

### Scenario 1: Add New Agent Workflow

You want to add a new specialized agent (e.g., Security Auditor).

**Steps:**

1. **Copy template workspace**
   ```bash
   cp -r po-agent-workspace security-auditor-workspace
   cd security-auditor-workspace
   ```

2. **Update configuration**
   ```bash
   # Edit README.md
   # Change: "Product Owner Agent" → "Security Auditor Agent"
   
   # Edit agents/workflow.py
   # Update: node names, descriptions, entry point
   ```

3. **Implement nodes**
   ```python
   # Edit agents/nodes.py
   def security_audit(state: SecurityAuditorState) -> SecurityAuditorState:
       """Audit code for security issues."""
       # Your implementation
       return state
   ```

4. **Create types**
   ```python
   # Edit agents/state.py
   @dataclass
   class SecurityAuditorState:
       code_to_audit: str
       audit_results: List[SecurityIssue]
       # ... etc
   ```

5. **Add to orchestrator**
   ```python
   # In team-orchestrator/orchestrator.py
   
   # Add route from backend to security auditor
   orchestrator.router.add_route(
       source_workflow="backend",
       source_event_type=EventType.API_CONTRACT_PUBLISHED,
       target_workflow="security_auditor",
   )
   ```

6. **Add tests**
   ```python
   # Create tests/test_nodes.py
   class TestSecurityAudit:
       def test_identifies_vulnerabilities(self):
           # Your test
           pass
   ```

### Scenario 2: Customize an Existing Agent

You want to modify the Backend Agent to use your company's API standards.

**Steps:**

1. **Modify nodes**
   ```python
   # backend-agent-workspace/agents/nodes.py
   
   # Customize the api_contract node
   def api_contract(state: BackendWorkflowState) -> BackendWorkflowState:
       # Add your custom logic
       state.api_contract["your_company_policy"] = validate_against_policy(...)
       return state
   ```

2. **Update schemas if needed**
   ```python
   # team-contracts/schemas/api_contract.py
   # Add your custom fields
   
   class APIContract(BaseModel):
       # ... existing fields
       company_policies: List[str]
       security_scans: List[SecurityScan]
   ```

3. **Update tests**
   ```python
   # backend-agent-workspace/tests/test_nodes.py
   
   def test_applies_company_policies(self):
       # Test your customization
       pass
   ```

### Scenario 3: Change LLM Model

Switch from Claude Sonnet to a different model.

**Option A: Global change**

```bash
# Edit .env
CLAUDE_MODEL=claude-opus-4-8

# OR edit each agent's nodes.py
# MODEL = "claude-opus-4-8"
```

**Option B: Per-workflow change**

```python
# po-agent-workspace/agents/nodes.py
MODEL = "claude-opus-4-8"  # Use Opus for PO analysis

# backend-agent-workspace/agents/nodes.py
MODEL = "claude-sonnet-4-20250514"  # Keep Sonnet for speed
```

### Scenario 4: Add External Integration

Connect to GitHub for PR creation.

**Steps:**

1. **Update tools**
   ```python
   # backend-agent-workspace/agents/tools.py
   
   class GitHubTool:
       @staticmethod
       def create_pull_request(title: str, body: str) -> ToolResult:
           # Implement actual GitHub API call
           from github import Github
           g = Github(os.getenv("GITHUB_TOKEN"))
           # ... create PR
   ```

2. **Add configuration**
   ```bash
   # .env
   GITHUB_TOKEN=ghp_your-token
   GITHUB_OWNER=your-org
   GITHUB_REPO=your-repo
   ```

3. **Update workflows**
   ```python
   # Update api_publishing node
   def api_publishing(state: BackendWorkflowState) -> BackendWorkflowState:
       # Use real GitHub tool instead of stub
       GitHubTool.create_pull_request(...)
   ```

## Extending the System

### Add New Event Type

```python
# team-orchestrator/events.py

class EventType(str, Enum):
    # ... existing events
    YOUR_CUSTOM_EVENT = "your_custom_event"
```

### Add New Route

```python
# team-orchestrator/orchestrator.py

def _setup_default_routes(self) -> None:
    # ... existing routes
    
    self.router.add_route(
        source_workflow="your_source",
        source_event_type=EventType.YOUR_CUSTOM_EVENT,
        target_workflow="your_target",
        data_mapper=lambda p: {...},
        condition=lambda e: e.payload.get("enabled", False)
    )
```

### Add New Schema

```python
# team-contracts/schemas/your_schema.py

from pydantic import BaseModel, Field

class YourSchema(BaseModel):
    """Description."""
    field1: str = Field(..., description="...")
    field2: int = Field(..., description="...")
    
    def to_markdown(self) -> str:
        # For human-readable output
        pass
    
    def to_dict(self) -> dict:
        # For agent consumption
        pass
```

Then add to `team-contracts/schemas/__init__.py`:

```python
from .your_schema import YourSchema

__all__ = [
    # ... existing
    "YourSchema",
]
```

## Testing

### Run All Tests

```bash
# Orchestrator tests
pytest team-orchestrator/tests/ -v

# Individual agent tests
pytest po-agent-workspace/tests/ -v
pytest em-agent-workspace/tests/ -v
pytest ux-agent-workspace/tests/ -v
pytest backend-agent-workspace/tests/ -v
pytest frontend-agent-workspace/tests/ -v

# With coverage
pytest --cov=team_orchestrator --cov-report=html
```

### Write Tests

```python
# tests/test_your_feature.py

import pytest
from team_orchestrator import TeamOrchestrator, Event, EventType

class TestYourFeature:
    def test_basic_functionality(self):
        """Test basic feature."""
        orchestrator = TeamOrchestrator()
        
        # Setup
        event = Event(...)
        
        # Execute
        orchestrator.publish_event(event)
        
        # Assert
        assert len(orchestrator.event_bus.event_history) > 0

    def test_error_handling(self):
        """Test error cases."""
        # Test that errors are handled gracefully
        pass
```

### Test Your Changes

```bash
# Run specific test file
pytest tests/test_your_feature.py -v

# Run specific test class
pytest tests/test_your_feature.py::TestYourFeature -v

# Run specific test
pytest tests/test_your_feature.py::TestYourFeature::test_basic_functionality -v
```

## Submitting Changes

### Before Submitting

1. **Run all tests**
   ```bash
   pytest . -v --cov
   ```

2. **Check code formatting**
   ```bash
   black .
   isort .
   flake8 .
   ```

3. **Update documentation**
   - Update README files
   - Add examples if needed
   - Update CONTRIBUTING.md if adding workflows

4. **Test the demo**
   ```bash
   python run_team_pipeline.py run --demo
   ```

### Create Pull Request

1. **Push your branch**
   ```bash
   git push origin feature/my-feature
   ```

2. **Create PR on GitHub**
   - Use the PR template
   - Fill in description, testing, and checklist
   - Link related issues

3. **Respond to review feedback**
   - Make requested changes
   - Commit and push
   - Respond to comments

## Code Standards

### Python Style

```python
# Follow PEP 8
# Use type hints
def process_event(event: Event) -> dict[str, Any]:
    """Process an event.
    
    Args:
        event: The event to process
        
    Returns:
        Processed data
    """
    # Implementation
    pass

# Use docstrings for classes and public methods
class EventBus:
    """Central event distribution system."""
    
    def publish(self, event: Event) -> None:
        """Publish an event."""
        pass
```

### Formatting

Use tools automatically:

```bash
# Format code
black .

# Sort imports
isort .

# Lint
flake8 .
```

### Git Commits

```
Good:
- "Add security audit agent workflow"
- "Fix event routing in orchestrator"
- "Update documentation for custom routes"

Avoid:
- "fix stuff"
- "Update"
- "wip"
```

## FAQ

### Q: How do I customize the LLM temperature?

A: Edit `.env` or the agent's `nodes.py`:
```python
# In agents/nodes.py
client.messages.create(
    model=MODEL,
    max_tokens=2048,
    temperature=0.5,  # Adjust here (0.0-1.0)
    messages=[...]
)
```

### Q: How do I add a new event type?

A: Add to `team-orchestrator/events.py`:
```python
class EventType(str, Enum):
    MY_NEW_EVENT = "my_new_event"
```

### Q: How do I connect to a real database?

A: Update the connection string in `.env`:
```bash
DATABASE_URL=postgresql://user:pass@localhost/db
```

Then update context store initialization:
```python
# team-orchestrator/orchestrator.py
self.context_store = ContextStore(
    backend="postgresql",
    connection_string=os.getenv("DATABASE_URL")
)
```

### Q: Can I use a different LLM provider?

A: Yes! Replace the Anthropic imports:
```python
# agents/nodes.py
from openai import OpenAI  # or other provider

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

### Q: How do I run tests in Docker?

A: Use Docker Compose:
```bash
docker-compose run app pytest . -v
```

### Q: How do I debug a failing test?

A: Use pytest's debugging tools:
```bash
# Drop into debugger on failure
pytest --pdb tests/test_your_feature.py

# Verbose output
pytest -vv tests/test_your_feature.py

# Show print statements
pytest -s tests/test_your_feature.py
```

### Q: Can I extend the context store?

A: Yes! The context store is pluggable:
```python
# Create your own implementation
class CustomContextStore(ContextStore):
    def write_artifact(self, ...):
        # Your custom logic
        super().write_artifact(...)
        # Additional behavior
```

## Need Help?

- **Documentation**: See QUICK_START.md, PROJECT_COMPLETE.md
- **Examples**: Check the `/examples` folder
- **Issues**: Create a GitHub issue with details
- **Discussions**: Use GitHub Discussions for questions

---

**Thank you for contributing!** Your improvements make the AI SDLC Team better for everyone. 🚀
