# Pydantic Handoff Contract Schemas

All handoff contracts are implemented as Pydantic models with full validation, human-readable markdown output, and agent-friendly dict serialization.

## Summary

| Schema | From | To | Purpose |
|--------|------|-----|---------|
| **UserStory** | PO Agent | EM Agent | Feature requirements, acceptance criteria, complexity estimation |
| **SprintPlan** | EM Agent | All Dev Agents | Complete sprint with tasks, dependencies, time estimates |
| **UXHandoff** | UX Agent | Frontend Agent | Component specs, design tokens, interactions, responsive behavior |
| **APIContract** | Backend Agent | Frontend Agent | API endpoints, request/response schemas, error handling, auth |
| **DesignDecision** | Any Agent | Team Record | Architecture Decision Records (ADR format) with alternatives, consequences |

## Files

- **`user_story.py`** (275 lines) - UserStory contract with priorities and complexity
- **`sprint_plan.py`** (425 lines) - Sprint planning with tasks, assignments, dependencies
- **`ux_handoff.py`** (400 lines) - Design specs with components, tokens, interactions
- **`api_contract.py`** (500 lines) - API specs with endpoints, schemas, errors
- **`design_decision.py`** (475 lines) - ADR format decisions with alternatives
- **`__init__.py`** - Central imports for all schemas
- **`requirements.txt`** - Dependencies (pydantic>=2.0.0)
- **`test_schemas.py`** - Comprehensive test suite with 25+ test cases

## Quick Start

```python
from team_contracts.schemas import (
    UserStory, Priority, Complexity,
    SprintPlan, Sprint, SprintTask, TaskType,
    UXHandoff, ComponentSpec, ComponentType,
    APIContract, APIEndpoint, HTTPMethod,
    DesignDecision, DecisionCategory, DecisionImpact
)

# Create a user story
story = UserStory(
    id="US-001",
    title="User login with email and password",
    description="...",
    user_role="Customer",
    user_goal="log in securely",
    business_value="enables personalization",
    acceptance_criteria=["Form displays", "Valid login works"],
    priority=Priority.HIGH,
    estimated_complexity=Complexity.M,
    created_by="po-agent",
)

# Output for humans
print(story.to_markdown())

# Output for agents
agent_data = story.to_dict()
```

## Key Features

### 1. Full Validation
- Pydantic field validators ensure data quality
- Type checking on all fields
- Enum constraints (Priority, Complexity, TaskType, etc.)
- Cross-field validation (e.g., sprint end_date > start_date)

### 2. Human-Readable Output
Every schema has a `to_markdown()` method that generates formatted documentation:
- **UserStory**: Story template format with acceptance criteria
- **SprintPlan**: Sprint overview with task breakdown by agent
- **UXHandoff**: Component specs with design notes and interactions
- **APIContract**: OpenAPI-style documentation
- **DesignDecision**: ADR format with context, decision, rationale

### 3. Agent-Friendly Serialization
Every schema has a `to_dict()` method for agent consumption:
- All dates converted to ISO format strings
- Enums converted to string values
- Nested objects properly serialized
- JSON-serializable output

## Validation Rules

### UserStory
- Title: 5-200 chars
- Description: 20+ chars
- At least one acceptance criterion
- Priority and complexity enums

### SprintPlan
- Sprint duration: 1-30 days
- End date > start date
- At least one task per sprint
- Task dependencies must reference other tasks in sprint

### UXHandoff
- At least one component
- Component name: 2+ chars
- ResponsiveBreakpoint enums (mobile, tablet, desktop)
- ComponentType enums

### APIContract
- Base URL must be valid
- At least one endpoint
- Endpoint path must start with "/"
- HTTP method enums

### DesignDecision
- Title: 5+ chars
- Context, decision, rationale: 10+ chars each
- DecisionCategory enums
- DecisionImpact enums

## Usage Examples

### PO Workflow
```python
# PO creates user stories
stories = [
    UserStory(id="US-001", title="...", ...),
    UserStory(id="US-002", title="...", ...),
]

# Output for team
for story in stories:
    save_markdown(story.id, story.to_markdown())
    
# EM receives as dicts
for story in stories:
    em_agent.process(story.to_dict())
```

### EM Workflow
```python
# EM creates sprint plan from user stories
plan = SprintPlan(
    sprint=Sprint(
        id="S-2.1",
        tasks=[
            SprintTask(user_story_id="US-001", assigned_to="frontend-agent", ...),
            SprintTask(user_story_id="US-002", assigned_to="backend-agent", ...),
        ],
        ...
    ),
    user_stories={"US-001": {...}, "US-002": {...}},
    created_by="em-agent",
)

# Generate sprint document
with open("sprint.md", "w") as f:
    f.write(plan.to_markdown())

# Distribute to agents
frontend_agent.run(plan.to_dict())
backend_agent.run(plan.to_dict())
```

### Frontend Workflow
```python
# Frontend receives UX and API contracts
ux_data = ux_handoff.to_dict()
api_data = api_contract.to_dict()

# Use in implementation
for component in ux_handoff.components:
    generate_component(component)
    
for endpoint in api_contract.endpoints:
    generate_api_client(endpoint)
```

## Extending Schemas

To add a new handoff contract:

1. Create a new Python file with Pydantic models
2. Implement `to_markdown()` and `to_dict()` on all models
3. Add validators for domain rules
4. Export from `__init__.py`
5. Create corresponding event in `../events/`
6. Add test cases in `test_schemas.py`

## Testing

Run all tests:
```bash
pytest test_schemas.py -v
```

Run specific test class:
```bash
pytest test_schemas.py::TestUserStory -v
```

All schemas are tested for:
- Valid instantiation
- Field validation
- Markdown conversion
- Dict conversion
- JSON serialization
- Method correctness (e.g., `sprint.total_estimated_hours()`)

## Dependencies

```
pydantic>=2.0.0,<3.0.0
python-dateutil>=2.8.0
```

Install with:
```bash
pip install -r requirements.txt
```

## Next Steps

1. **Create events** - Define corresponding event types in `../events/`
2. **Implement agents** - Use these schemas in agent code
3. **Add integration tests** - Test full workflows using schemas
4. **Create context store** - Implement shared context storage
5. **Build agent SDK** - Provide agent SDK utilities for schema handling
