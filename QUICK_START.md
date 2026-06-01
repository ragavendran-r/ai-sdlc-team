# Quick Start Guide

Get the AI SDLC Team pipeline running in 5 minutes.

## Prerequisites

```bash
# Python 3.9+
python --version

# Install dependencies
pip install pydantic langchain langgraph anthropic python-dotenv
```

## Setup

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-your-api-key-here

# Or create .env file
echo "ANTHROPIC_API_KEY=sk-your-api-key-here" > .env
```

## Run Demo (1 minute)

```bash
# Run simulated team pipeline
python run_team_pipeline.py run --demo
```

**Output:**
- 5 workflows execute in sequence
- 30+ events published
- 15+ artifacts stored
- Full pipeline status

## Explore Results (2 minutes)

```bash
# Check pipeline status
python run_team_pipeline.py status

# View workflow routes
python run_team_pipeline.py routes

# See event history
python run_team_pipeline.py events --limit 50

# Browse artifacts
python run_team_pipeline.py context --timeline
python run_team_pipeline.py context --list
```

## View Code (2 minutes)

**Agent Workflows:**
- `po_agent_workspace/` - Product Owner agent
- `em_agent_workspace/` - Engineering Manager agent
- `ux_agent_workspace/` - UX Designer agent
- `backend_agent_workspace/` - Backend Engineer agent
- `frontend_agent_workspace/` - Frontend Engineer agent

**Orchestrator:**
- `team-orchestrator/` - Central coordination system

**Schemas:**
- `team_contracts/schemas/` - 23 shared data contracts

## Run Tests

```bash
# Test orchestrator
pytest team-orchestrator/tests/ -v

# Test individual agents
pytest po_agent_workspace/tests/ -v
pytest em_agent_workspace/tests/ -v
pytest ux_agent_workspace/tests/ -v
pytest backend_agent_workspace/tests/ -v
pytest frontend_agent_workspace/tests/ -v
```

## CLI Commands Reference

```bash
# Run workflows
python run_team_pipeline.py run --all              # Full pipeline
python run_team_pipeline.py run --demo             # Demo mode
python run_team_pipeline.py run --workflows po em  # Specific workflows

# Check status
python run_team_pipeline.py status                 # Human readable
python run_team_pipeline.py status --json          # JSON format

# View routes
python run_team_pipeline.py routes                 # ASCII diagram
python run_team_pipeline.py routes --json          # JSON format

# Events
python run_team_pipeline.py events                 # All events
python run_team_pipeline.py events --workflow po   # From PO only
python run_team_pipeline.py events --limit 50      # Last 50

# Context store
python run_team_pipeline.py context --list         # List artifacts
python run_team_pipeline.py context --timeline     # Show timeline
python run_team_pipeline.py context --list --workflow backend

# Export
python run_team_pipeline.py export --file state.json

# Configuration
python run_team_pipeline.py config
```

## Example: Trace a Feature

Feature request: "User Authentication"

### 1. PO Agent
```bash
cd po_agent_workspace
python agents/workflow.py
```
- Creates UserStory for "User login"
- Defines acceptance criteria
- Estimates complexity

### 2. EM Agent  
```bash
cd ../em_agent_workspace
python agents/workflow.py
```
- Ingests user stories
- Creates sprint plan
- Assigns tasks

### 3. UX Agent
```bash
cd ../ux_agent_workspace
python agents/workflow.py
```
- Designs login flow
- Creates component specs
- Defines design tokens

### 4. Backend Agent
```bash
cd ../backend_agent_workspace
python agents/workflow.py
```
- Designs domain model
- Generates database schema
- Creates API contract
- Reviews security

### 5. Frontend Agent
```bash
cd ../frontend_agent_workspace
python agents/workflow.py
```
- Scaffolds components
- Plans state management
- Generates tests
- Code review

## Integration Flow

```
User Story (PO)
   ↓
Sprint Plan (EM)
   ├→ Backend API Contract
   └→ UX Design Handoff
       ↓
   Frontend Components
```

## File Structure

```
ai-sdlc-team/
├── po_agent_workspace/           # Product Owner agent
│   ├── agents/
│   │   ├── workflow.py
│   │   ├── nodes.py
│   │   └── state.py
│   ├── tests/
│   └── README.md
│
├── em_agent_workspace/           # Engineering Manager agent
│   ├── agents/
│   └── tests/
│
├── ux_agent_workspace/           # UX Designer agent
│   ├── agents/
│   └── tests/
│
├── backend_agent_workspace/      # Backend Engineer agent
│   ├── agents/
│   └── tests/
│
├── frontend_agent_workspace/     # Frontend Engineer agent
│   ├── agents/
│   └── tests/
│
├── team-orchestrator/            # Central coordinator
│   ├── events.py
│   ├── context_store.py
│   ├── router.py
│   ├── orchestrator.py
│   ├── cli.py
│   └── tests/
│
├── team_contracts/               # Shared schemas
│   ├── schemas/                  # 23 Pydantic schemas
│   └── context-store/            # Artifact storage
│
├── run_team_pipeline.py          # Main CLI entry point
├── PROJECT_COMPLETE.md           # Full summary
├── TEAM_ORCHESTRATOR_GUIDE.md    # Detailed guide
└── QUICK_START.md               # This file
```

## Debugging

### Enable Verbose Output
```bash
python run_team_pipeline.py run --demo --verbose
```

### Check What's in Context Store
```bash
python run_team_pipeline.py context --list
# Shows all stored artifacts

python run_team_pipeline.py context --timeline
# Shows chronological timeline
```

### Export and Inspect State
```bash
python run_team_pipeline.py export --file debug_state.json

# Use jq to inspect
cat debug_state.json | jq '.event_history | length'  # Count events
cat debug_state.json | jq '.artifacts | group_by(.workflow)'  # Group by workflow
```

### Run Individual Test
```bash
pytest po_agent_workspace/tests/test_nodes.py::TestUserStoryIntake::test_creates_stories -v
```

## Troubleshooting

### API Key Issues
```bash
# Check key is set
echo $ANTHROPIC_API_KEY

# If not set, export it
export ANTHROPIC_API_KEY=sk-...
```

### Import Errors
```bash
# Add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use python -m
python -m team_orchestrator run --demo
```

### Context Store Full
```bash
# Clear all artifacts
python run_team_pipeline.py context --clear

# Backup first
python run_team_pipeline.py export --file backup.json
python run_team_pipeline.py context --clear
```

## Next Steps

1. **Read Documentation**
   - `PROJECT_COMPLETE.md` - Full project overview
   - `TEAM_ORCHESTRATOR_GUIDE.md` - Orchestrator details
   - Individual `README.md` files in each workspace

2. **Explore Code**
   - Look at agent `nodes.py` files
   - Check schema definitions
   - Review test files

3. **Customize**
   - Add custom routes in orchestrator
   - Modify event handling
   - Extend schemas as needed

4. **Integrate**
   - Connect real Claude API calls
   - Link to your tools
   - Add database backend

## Common Tasks

### Add Custom Route
```python
from team_orchestrator import TeamOrchestrator, EventType

orchestrator = TeamOrchestrator()
orchestrator.router.add_route(
    source_workflow="po",
    source_event_type=EventType.USER_STORIES_CREATED,
    target_workflow="my_service"
)
```

### Subscribe to Events
```python
def my_handler(event):
    print(f"Received: {event.event_type}")

orchestrator.event_bus.subscribe(
    event_types=[EventType.USER_STORIES_CREATED],
    handler=my_handler
)
```

### Read from Context Store
```python
latest = orchestrator.context_store.get_latest_by_type(
    artifact_type="api_contract",
    workflow="backend"
)
```

## Resources

- **GitHub:** https://github.com/your-repo/ai-sdlc-team
- **Docs:** See PROJECT_COMPLETE.md and TEAM_ORCHESTRATOR_GUIDE.md
- **Issues:** Report bugs and feature requests
- **Contributing:** See CONTRIBUTING.md

## Support

For issues or questions:
1. Check documentation files
2. Review test examples
3. Check issue tracker
4. Open new issue with details

---

**That's it!** You're ready to explore the AI SDLC Team pipeline.

Start with: `python run_team_pipeline.py run --demo`

Happy exploring! 🚀
