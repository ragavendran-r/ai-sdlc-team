# PO Agent LangGraph Workflow - Getting Started

## Quick Overview

A complete LangGraph-based workflow for the Product Owner agent with:
- ✅ **9 agent nodes** - Requirements gathering to backlog organization
- ✅ **2 human checkpoints** - Approval gates with interactive feedback
- ✅ **Typed state** - Full workflow state management
- ✅ **Claude Sonnet 4** - LLM for natural language processing
- ✅ **Stubbed tools** - Clear interfaces ready for real integrations

## What's in Here?

```
agents/
├── state.py              # Workflow state definition
├── nodes.py              # 9 agent node implementations
├── tools.py              # 9 stubbed tool interfaces
├── checkpoints.py        # 2 human approval checkpoints
├── workflow.py           # LangGraph StateGraph
├── example.py            # Usage examples
├── requirements.txt      # Dependencies
├── README.md             # Detailed documentation
└── __init__.py           # Module exports
```

## 30-Second Start

### 1. Install
```bash
cd po-agent-workspace/agents
pip install -r requirements.txt
```

### 2. Set API Key
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Run
```bash
python workflow.py
```

### 4. Approve Stories
When prompted, type `y` to approve stories and backlog.

### 5. View Results
Check `workflow_output.json` for complete state.

## The Workflow

```
Interview Phase
    ↓
Stakeholder Interview → Extract Requirements
    ↓
Quality Assurance
    ↓
Ambiguity & Conflict Detection
    ↓
Story Generation
    ↓
✋ CHECKPOINT 1: Approve Stories (type y/n)
    ↓ (if approved)
Acceptance Criteria (BDD)
    ↓
Prioritization
    ↓
Backlog Grooming
    ↓
✋ CHECKPOINT 2: Approve Backlog (type y/n)
    ↓ (if approved)
Jira Population
    ↓
Done!
```

## The 9 Agents

1. **stakeholder_interview** - Conversational interviews to extract requirements
2. **requirements_extraction** - Structure raw input into formal specs
3. **ambiguity_detection** - Flag vague or unmeasurable requirements
4. **conflict_detection** - Find contradictions and duplicates
5. **story_generation** - Convert requirements to user stories
6. **acceptance_criteria** - Enrich with Given/When/Then (BDD)
7. **prioritization** - Score by business value and effort
8. **backlog_grooming** - Organize into themes and sprints
9. **jira_population** - Create Jira tickets (stubbed)

## Key Features

### Human Approval Gates

After story generation and backlog grooming, you approve in the CLI:

```
Do you approve these stories? (y/n): y
✅ Stories approved. Proceeding...
```

If you reject, provide feedback and the workflow loops back for revision.

### Complete State Tracking

All workflow data is stored in `PoWorkflowState`:
- Raw requirements → Structured requirements
- Ambiguity/conflict flags
- Generated stories → Enriched stories
- Prioritized stories → Groomed backlog
- Jira tickets created

### LLM Integration

Claude Sonnet 4 powers all agents for:
- Conversational interviews
- Requirement analysis
- Story generation
- Quality review

## Usage Examples

### Basic Execution
```python
from agents import run_po_workflow

final_state = run_po_workflow(
    initial_context="Building SaaS auth system",
    verbose=True,
)
```

### Access Results
```python
# Generated stories
for story in final_state.generated_stories:
    print(f"{story['id']}: {story['title']}")

# Prioritized stories
for story in final_state.prioritized_stories:
    print(f"Rank {story['priority_rank']}: {story['title']}")

# Groomed backlog
for theme in final_state.groomed_backlog:
    print(f"Theme: {theme['theme']}")
    for story in theme['stories']:
        print(f"  - {story['title']}")

# Jira tickets
print(f"Created: {final_state.jira_tickets_created}")
```

### Programmatic Use
```python
from agents import compile_po_workflow, PoWorkflowState

# Create workflow
compiled = compile_po_workflow()

# Custom initial state
initial = PoWorkflowState(
    interview_notes="Your custom context..."
)

# Execute
final = compiled.invoke(initial)

# Save to JSON
import json
with open("output.json", "w") as f:
    json.dump(final.to_dict(), f, indent=2)
```

## Understanding the Output

### Story Example
```python
{
    "id": "US-001",
    "title": "User login with email and password",
    "user_role": "Customer",
    "user_goal": "log in securely",
    "business_value": "enables personalization",
    "acceptance_criteria": [
        "User can enter email and password",
        "Valid credentials log in",
        "Invalid credentials show error"
    ],
    "priority": "high",
    "estimated_complexity": "m"
}
```

### Prioritized Story Example
```python
{
    "id": "US-001",
    "title": "User login with email and password",
    "business_value_score": 9,          # 1-10 scale
    "effort_estimate_hours": 8,         # Estimated effort
    "priority_score": 1.125,            # Value / Effort
    "priority_rank": 1,                 # 1 = highest priority
    "dependencies": []                  # Other story IDs
}
```

### Groomed Backlog Example
```python
{
    "theme": "User Authentication",
    "epic": "Secure Login System",
    "stories": [
        {
            "id": "US-001",
            "title": "User login with email and password",
            "priority_rank": 1,
            "sprint": 1,
            "effort_hours": 8
        }
    ],
    "total_effort_hours": 8
}
```

## Checkpoints Explained

### Checkpoint 1: Story Generation Approval
**What You See:**
- All generated stories formatted nicely
- Priority and complexity estimates
- Acceptance criteria preview
- Quality flags (ambiguities, conflicts)

**What You Do:**
- Review stories
- Type `y` to approve and proceed
- Type `n` to reject and provide feedback
- Feedback loops back to story_generation

### Checkpoint 2: Backlog Grooming Approval
**What You See:**
- Prioritized story list with scores
- Theme and epic organization
- Sprint allocation
- Total effort and story counts

**What You Do:**
- Review backlog organization
- Type `y` to approve and create Jira tickets
- Type `n` to reject and provide feedback
- Feedback loops back to backlog_grooming

## Common Tasks

### Run Full Workflow
```bash
python workflow.py
```

### Run Examples
```bash
python example.py
```

### Visualize Graph
```python
from agents import print_workflow_graph, compile_po_workflow

compiled = compile_po_workflow()
print_workflow_graph(compiled)
```

### Custom Initial Context
```python
from agents import run_po_workflow

final_state = run_po_workflow(
    initial_context="Your product description here",
    verbose=True,
)
```

### Save State to JSON
```python
import json

with open("workflow_state.json", "w") as f:
    json.dump(final_state.to_dict(), f, indent=2)
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'anthropic'"
```bash
pip install -r requirements.txt
```

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY="your-key"
```

### "No module named 'langgraph'"
```bash
pip install langgraph
```

### Workflow Hangs at Checkpoint
Press Enter or type `y`/`n` to respond to the prompt.

## File Guide

### `state.py` - State Management
Defines `PoWorkflowState` dataclass with all workflow fields:
- Interview data
- Requirements (raw + structured)
- Quality flags (ambiguities, conflicts)
- Stories (raw → enriched → prioritized)
- Backlog (groomed)
- Jira tickets
- Metadata (messages, errors)

### `nodes.py` - Agent Implementations
The 9 agent node functions:
1. `stakeholder_interview` - Conversational interview
2. `requirements_extraction` - Structure requirements
3. `ambiguity_detection` - Flag ambiguities
4. `conflict_detection` - Find conflicts
5. `story_generation` - Generate stories
6. `acceptance_criteria` - Add BDD criteria
7. `prioritization` - Score and rank
8. `backlog_grooming` - Organize backlog
9. `jira_population` - Create tickets

### `tools.py` - Stubbed Tool Interfaces
All 9 tools with clear `ToolResult` responses:
- StakeholderInterviewTool
- RequirementsStructuringTool
- AmbiguityDetectionTool
- ConflictDetectionTool
- StoryGenerationTool
- AcceptanceCriteriaTool
- PrioritizationTool
- BacklogGroomingTool
- JiraPopulationTool

### `checkpoints.py` - Human Approval
Two checkpoint nodes with CLI interaction:
- `checkpoint_story_generation` - Review stories
- `checkpoint_backlog_grooming` - Review backlog
- `HumanCheckpoint` class with display/input methods

### `workflow.py` - LangGraph Definition
The complete LangGraph StateGraph:
- `create_po_workflow()` - Build graph
- `compile_po_workflow()` - Compile for execution
- `run_po_workflow()` - Execute with logging
- `print_workflow_graph()` - Visualize structure

### `example.py` - Usage Examples
Complete working examples:
1. Basic execution
2. Graph visualization
3. Result access
4. State serialization

## For Developers

### Adding a New Agent
1. Implement node function in `nodes.py`
2. Add to workflow graph in `workflow.py`
3. Add edge connections
4. Export from `__init__.py`

### Integrating Real Tools
1. Replace tool stubs in `tools.py`
2. Update return format (keep ToolResult)
3. Add error handling
4. Test with actual APIs

### Custom Checkpoints
1. Create in `checkpoints.py`
2. Add to workflow graph
3. Implement approval logic
4. Create guard functions

### Changing LLM
In `nodes.py`, change:
```python
llm = ChatAnthropic(
    model="claude-opus-4-20250805",  # Change here
    temperature=0.7,
    max_tokens=2048,
)
```

## Performance Notes

- Typical workflow: 2-5 minutes
- Bottleneck: LLM inference time
- Tools: Instant (stubbed)
- Checkpoints: Waits for user input

## Next Steps

1. **Run It**
   ```bash
   python workflow.py
   ```

2. **Explore Results**
   ```bash
   cat workflow_output.json
   ```

3. **Review Code**
   - Check `nodes.py` for agent logic
   - See `workflow.py` for graph structure
   - Browse `tools.py` for tool interfaces

4. **Integrate Tools**
   - Replace stubs in `tools.py`
   - Connect to real APIs
   - Add error handling

5. **Deploy**
   - Add persistence layer
   - Build web UI
   - Set up batch processing

## Documentation

- **README.md** - Detailed documentation
- **WORKFLOW_IMPLEMENTATION.md** - Architecture deep dive
- **PO_WORKFLOW_SUMMARY.md** - Quick reference
- **GETTING_STARTED.md** - This file

## Support

For more details:
1. Read README.md for comprehensive docs
2. Check WORKFLOW_IMPLEMENTATION.md for architecture
3. Review nodes.py for agent implementations
4. See example.py for usage patterns

---

**Ready to go!** Run `python workflow.py` to see the workflow in action.
