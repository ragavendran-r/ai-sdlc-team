# PO Agent Workflow - LangGraph Implementation

A complete LangGraph-based workflow for the Product Owner agent in the AI SDLC Team. This workflow automates the entire requirements gathering and user story generation pipeline with human approval checkpoints.

## Architecture Overview

### 9 Agent Nodes + 2 Human Checkpoints

```
stakeholder_interview (1)
        ↓
requirements_extraction (2)
        ↓
ambiguity_detection (3)  ←→  conflict_detection (4)
        ↓
story_generation (5)
        ↓
[CHECKPOINT 1: Human Story Approval]
        ↓ (if approved)
acceptance_criteria (6)
        ↓
prioritization (7)
        ↓
backlog_grooming (8)
        ↓
[CHECKPOINT 2: Human Backlog Approval]
        ↓ (if approved)
jira_population (9)
        ↓
    [END]
```

## Agent Nodes

### 1. **stakeholder_interview**
Conducts conversational interviews with stakeholders to extract requirements.

**Input:** Initial context/project description
**Output:** Interview notes + raw requirements
**LLM:** Claude Sonnet - generates realistic interview questions and responses
**Tools:** StakeholderInterviewTool

### 2. **requirements_extraction**
Structures raw interview notes into formal requirement specifications.

**Input:** Interview notes + raw requirements
**Output:** Structured requirements with title, description, category, signals
**LLM:** Claude Sonnet - refines and structures requirements
**Tools:** RequirementsStructuringTool

### 3. **ambiguity_detection**
Flags vague, unmeasurable, or incomplete requirements.

**Input:** Structured requirements
**Output:** Ambiguity flags with severity and suggested clarifications
**LLM:** Claude Sonnet - identifies unclear language and missing criteria
**Tools:** AmbiguityDetectionTool

### 4. **conflict_detection**
Identifies contradictions, duplicates, or incompatible requirements.

**Input:** Structured requirements
**Output:** Conflict flags with conflict type and resolution suggestions
**LLM:** Claude Sonnet - detects logical contradictions
**Tools:** ConflictDetectionTool

### 5. **story_generation**
Converts requirements into user stories following the standard format: "As a [role], I want [goal], so that [value]"

**Input:** Structured requirements (with quality flags)
**Output:** Generated user stories with acceptance criteria
**LLM:** Claude Sonnet - generates stories and reviews for clarity
**Tools:** StoryGenerationTool

### 6. **acceptance_criteria**
Enriches stories with detailed Given/When/Then (BDD) acceptance criteria.

**Input:** Generated user stories
**Output:** Stories with BDD-format acceptance criteria
**LLM:** Claude Sonnet - validates BDD format for completeness
**Tools:** AcceptanceCriteriaTool

### 7. **prioritization**
Scores stories by business value and effort to determine priority order.

**Input:** Stories with acceptance criteria
**Output:** Prioritized stories with scores and ranking
**LLM:** Claude Sonnet - reviews priority reasoning
**Tools:** PrioritizationTool

### 8. **backlog_grooming**
Organizes stories into epics, themes, and sprints with dependency management.

**Input:** Prioritized stories
**Output:** Groomed backlog organized by theme and sprint
**LLM:** Claude Sonnet - reviews sprint organization and dependencies
**Tools:** BacklogGroomingTool

### 9. **jira_population**
(Stubbed) Creates Jira tickets from the groomed backlog. Ready for real API integration.

**Input:** Groomed backlog
**Output:** Created Jira ticket IDs
**Tools:** JiraPopulationTool (stubbed)

## Human Checkpoints

### Checkpoint 1: Story Generation Approval
**Location:** After story_generation, before acceptance_criteria

Displays all generated stories with:
- Story format (role/goal/value)
- Priority and complexity estimates
- Acceptance criteria
- Detected ambiguities and conflicts

**Options:**
- ✅ Approve - Proceed to acceptance criteria enrichment
- ❌ Reject - Return to story_generation with feedback loop

### Checkpoint 2: Backlog Grooming Approval
**Location:** After backlog_grooming, before jira_population

Displays organized backlog with:
- Prioritized story list with scores
- Theme and epic grouping
- Sprint organization
- Total effort and story counts
- Unresolved conflicts/ambiguities

**Options:**
- ✅ Approve - Proceed to Jira ticket creation
- ❌ Reject - Return to backlog_grooming with feedback loop

## Workflow State

The `PoWorkflowState` dataclass maintains complete workflow state:

```python
@dataclass
class PoWorkflowState:
    # Interview phase
    interview_notes: str
    raw_requirements: List[RawRequirement]
    interview_complete: bool
    
    # Structuring phase
    structured_requirements: List[StructuredRequirement]
    
    # Quality assurance
    ambiguity_flags: List[AmbiguityFlag]
    conflict_flags: List[ConflictFlag]
    
    # Story generation phase
    generated_stories: List[Dict[str, Any]]
    stories_approved: bool
    approval_notes: str
    
    # Acceptance criteria phase
    enriched_stories: List[Dict[str, Any]]
    
    # Prioritization phase
    prioritized_stories: List[Dict[str, Any]]
    
    # Backlog grooming phase
    groomed_backlog: List[Dict[str, Any]]
    themes: List[str]
    backlog_approved: bool
    backlog_approval_notes: str
    
    # JIRA population
    jira_tickets_created: List[str]
    jira_sync_complete: bool
    
    # Metadata
    workflow_start: datetime
    current_agent: str
    messages: List[Dict[str, str]]
    errors: List[str]
```

## Files

- **`state.py`** - State definitions and workflow state dataclass
- **`nodes.py`** - 9 agent node implementations
- **`checkpoints.py`** - 2 human checkpoint nodes with CLI interaction
- **`tools.py`** - Stubbed tool interfaces for all integrations
- **`workflow.py`** - LangGraph StateGraph definition and execution
- **`__init__.py`** - Module exports

## LangGraph Design

### State Graph Structure
- **Node Type:** Function nodes (agents) and checkpoint nodes
- **State Type:** `PoWorkflowState` (typed Pydantic dataclass)
- **Edges:** 
  - Linear edges for sequential agents
  - Conditional edges for checkpoint approval gates
  - Revision loops for rejected checkpoints

### Conditional Routing
```python
# Checkpoint 1: Story approval
workflow.add_conditional_edges(
    "checkpoint_story_generation",
    should_proceed_to_acceptance_criteria,
    {
        True: "acceptance_criteria",   # Approved
        False: "story_generation",     # Rejected - revise
    }
)

# Checkpoint 2: Backlog approval
workflow.add_conditional_edges(
    "checkpoint_backlog_grooming",
    should_proceed_to_jira,
    {
        True: "jira_population",       # Approved
        False: "backlog_grooming",     # Rejected - revise
    }
)
```

## Usage

### Basic Execution
```python
from po_agent_workspace.agents import run_po_workflow

# Run with default settings
final_state = run_po_workflow(
    initial_context="Building a SaaS authentication system",
    verbose=True,
)
```

### Programmatic Use
```python
from po_agent_workspace.agents import compile_po_workflow

# Create and compile workflow
compiled_workflow = compile_po_workflow()

# Execute with custom initial state
from po_agent_workspace.agents import PoWorkflowState
initial_state = PoWorkflowState(
    interview_notes="Custom context here..."
)

final_state = compiled_workflow.invoke(initial_state)

# Access results
for story in final_state.generated_stories:
    print(f"Story: {story['title']}")
    print(f"  Priority: {story.get('priority', 'N/A')}")
    print(f"  Complexity: {story.get('estimated_complexity', 'N/A')}")
```

### Workflow Graph Visualization
```python
from po_agent_workspace.agents import print_workflow_graph

compiled = compile_po_workflow()
print_workflow_graph(compiled)
```

## LLM Configuration

All agents use **Claude Sonnet 4** (claude-sonnet-4-20250514):
- Temperature: 0.7 (balanced creativity and consistency)
- Max tokens: 2048 (sufficient for detailed analysis)
- Streaming: Disabled (for checkpoint integration)

To use a different model:
```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-opus-4-20250805",  # Change model here
    temperature=0.7,
    max_tokens=2048,
)
```

## Tool Stubs

All tools are stubbed with clear interfaces for future integration:

### Stakeholder Interview Tool
```python
StakeholderInterviewTool.conduct_interview(
    stakeholder_name: str,
    context: str
) -> ToolResult
```

### Requirements Structuring Tool
```python
RequirementsStructuringTool.extract_requirements(
    raw_text: str
) -> ToolResult
```

### Quality Assurance Tools
```python
AmbiguityDetectionTool.detect_ambiguities(
    requirements: List[Dict]
) -> ToolResult

ConflictDetectionTool.detect_conflicts(
    requirements: List[Dict]
) -> ToolResult
```

### Story Generation Tools
```python
StoryGenerationTool.generate_stories(
    requirements: List[Dict],
    themes: Optional[List[str]]
) -> ToolResult
```

### Acceptance Criteria Tool
```python
AcceptanceCriteriaTool.enrich_with_bdd_criteria(
    stories: List[Dict]
) -> ToolResult
```

### Prioritization Tool
```python
PrioritizationTool.score_and_prioritize(
    stories: List[Dict]
) -> ToolResult
```

### Backlog Grooming Tool
```python
BacklogGroomingTool.groom_backlog(
    stories: List[Dict],
    max_stories_per_sprint: int
) -> ToolResult
```

### Jira Population Tool
```python
JiraPopulationTool.create_jira_tickets(
    backlog: List[Dict],
    project_key: str
) -> ToolResult
```

## Setup

### Installation
```bash
pip install -r requirements.txt
```

### Environment
Requires `ANTHROPIC_API_KEY`:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

## Testing

Run the workflow with test data:
```bash
python -m po_agent_workspace.agents.workflow
```

This will:
1. Create a sample workflow with test context
2. Execute all agents sequentially
3. Present human checkpoints for approval
4. Save final state to `workflow_output.json`

## Integration Points

All tools are ready for real integrations:

1. **Stakeholder Interview** - Replace with real interview tool/API
2. **Requirements Analysis** - Integrate with document/wiki extraction
3. **Conflict Resolution** - Connect to requirements DB for duplicate detection
4. **Story Generation** - Extend with template library
5. **Acceptance Criteria** - Integrate with test automation tools
6. **Prioritization** - Connect to portfolio management tools
7. **Backlog Grooming** - Integrate with capacity planning
8. **Jira Population** - Implement real Jira API calls

## Notes

- All agents use Claude Sonnet for natural language understanding
- Checkpoints provide human control over critical decisions
- State is fully typed for safety and IDE support
- Tools follow consistent interface pattern for easy integration
- Workflow supports both linear execution and interactive refinement loops

## Future Enhancements

- [ ] Real stakeholder interview tool (recording/transcription)
- [ ] Jira API integration
- [ ] Story template library
- [ ] Integration with existing requirements databases
- [ ] Multi-language support
- [ ] Batch processing for multiple features
- [ ] Analytics and reporting
- [ ] A/B testing of prioritization algorithms
