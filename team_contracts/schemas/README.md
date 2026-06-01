# Handoff Schemas

This folder contains Pydantic models for all handoffs between agents. Each model includes:
- **Full validation** with Pydantic field validators
- **`to_markdown()`** method for human-readable output
- **`to_dict()`** method for agent consumption

## Core Handoff Models

### UserStory (`user_story.py`)
**From:** PO Agent | **To:** EM Agent

The primary input to sprint planning. Contains everything needed for engineering to scope work.

```python
from team_contracts.schemas import UserStory, Priority, Complexity

story = UserStory(
    id="US-001",
    title="User login with email and password",
    description="...",
    user_role="Customer",
    user_goal="log in to my account securely",
    business_value="enables personalized experiences",
    acceptance_criteria=[...],
    priority=Priority.HIGH,
    estimated_complexity=Complexity.M,
    created_by="po-agent",
)

# Use in agent code
print(story.to_markdown())  # Human-readable output
agent_data = story.to_dict()  # For agent consumption
```

**Key fields:**
- User story format: role, goal, business value
- Acceptance criteria (testable)
- Priority and complexity estimation
- Dependencies and related stories

---

### SprintPlan (`sprint_plan.py`)
**From:** EM Agent | **To:** All Dev Agents

Complete sprint plan with all tasks assigned and ready for execution. Includes:
- Sprint metadata (dates, name, goals)
- Individual tasks assigned to agents
- Task dependencies
- User story references

```python
from team_contracts.schemas import SprintPlan, Sprint, SprintTask, TaskType

plan = SprintPlan(
    sprint=Sprint(
        id="S-2.1",
        name="Sprint 2.1 - Authentication",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=14),
        tasks=[...],
        created_by="em-agent",
    ),
    user_stories={...},
    created_by="em-agent",
)

print(plan.to_markdown())  # Full sprint document
plan_dict = plan.to_dict()  # For agent use
```

**SprintTask fields:**
- User story reference
- Assigned agent
- Task type (design, frontend, backend, integration_test, devops)
- Estimated hours
- Acceptance criteria
- Dependencies (depends_on_tasks, blocks_tasks)

---

### UXHandoff (`ux_handoff.py`)
**From:** UX Agent | **To:** Frontend Agent

Complete design specifications for implementation. Contains components, design tokens, interactions.

```python
from team_contracts.schemas import UXHandoff, ComponentSpec, ComponentType, DesignToken

handoff = UXHandoff(
    id="UX-001",
    user_story_id="US-001",
    feature_name="User Login",
    components=[
        ComponentSpec(
            id="C-001",
            name="LoginForm",
            component_type=ComponentType.FORM,
            description="...",
            design_notes="...",
            states={"default": "...", "hover": "..."},
            props={...},
            interactions=[...],
        )
    ],
    design_tokens=[...],
    created_by="ux-agent",
)

print(handoff.to_markdown())  # Design document
handoff_dict = handoff.to_dict()  # For frontend agent
```

**ComponentSpec fields:**
- Component type and description
- Visual design notes
- States (default, hover, active, disabled, etc.)
- Responsive behavior for mobile/tablet/desktop
- Props and slots
- Interactions and animations
- Accessibility requirements
- Design tokens used

---

### APIContract (`api_contract.py`)
**From:** Backend Agent | **To:** Frontend Agent

Complete API specification for integration.

```python
from team_contracts.schemas import APIContract, APIEndpoint, HTTPMethod, HTTPStatus

contract = APIContract(
    id="API-001",
    feature_name="User Authentication",
    user_story_id="US-001",
    base_url="https://api.example.com/v1",
    endpoints=[
        APIEndpoint(
            id="EP-001",
            method=HTTPMethod.POST,
            path="/api/v1/auth/login",
            summary="User login",
            description="...",
            auth_required=False,
            request_schema=JSONSchema(...),
            response_schema=JSONSchema(...),
            error_responses=[...],
        )
    ],
    global_headers={...},
    created_by="backend-agent",
)

print(contract.to_markdown())  # API documentation
contract_dict = contract.to_dict()  # For frontend agent
```

**APIEndpoint fields:**
- Method and path
- Authentication requirements
- Query parameters
- Request/response schemas (with examples)
- Error responses and codes
- Rate limiting
- Idempotency

---

### DesignDecision (`design_decision.py`)
**From:** Any Agent | **To:** Team Record

Architecture Decision Record (ADR) format for documenting decisions.

```python
from team_contracts.schemas import DesignDecision, DecisionCategory, DecisionStatus, Alternative

decision = DesignDecision(
    id="ADR-001",
    title="Use JWT tokens for API authentication",
    category=DecisionCategory.API_DESIGN,
    impact=DecisionImpact.SYSTEM,
    status=DecisionStatus.PROPOSED,
    context="Our application needs stateless authentication...",
    decision="We will use JWT tokens...",
    rationale="JWT is stateless and scalable...",
    alternatives=[...],
    consequences=[...],
    affects_areas=["api", "frontend", "authentication"],
    created_by="backend-agent",
)

print(decision.to_markdown())  # ADR document
decision_dict = decision.to_dict()  # For decision tracking
```

**Key fields:**
- Context, decision, rationale (ADR format)
- Alternatives considered with pros/cons
- Positive and negative consequences
- Trade-offs
- Affected areas
- Implementation notes and follow-up actions
- Review date

---

## Usage Patterns

### Validating Handoffs

```python
from team_contracts.schemas import UserStory

# Pydantic automatically validates on instantiation
try:
    story = UserStory(
        id="US-001",
        title="A",  # Too short - will raise validation error
        description="...",
        ...
    )
except ValidationError as e:
    print(f"Invalid: {e}")
```

### Converting for Consumption

```python
# For human reading
markdown = story.to_markdown()
save_to_file("story.md", markdown)

# For agents
agent_data = story.to_dict()
send_to_agent(agent_data)
```

### Querying Data

```python
plan = SprintPlan(...)

# Get tasks by agent
tasks_by_agent = plan.sprint.get_tasks_by_agent()
frontend_tasks = tasks_by_agent["frontend-agent"]

# Get blocked tasks
blocked = plan.sprint.get_blocked_tasks()

# Get summary stats
total_hours = plan.sprint.total_estimated_hours()
actual_hours = plan.sprint.total_actual_hours()
```

---

## Adding New Schemas

1. Create a new Python file with Pydantic models
2. Implement `to_markdown()` for human output
3. Implement `to_dict()` for agent consumption
4. Export from `__init__.py`
5. Add documentation here
6. Create corresponding events in `../events/`

---

## Validation Rules

Each schema enforces:
- **Required fields:** Core information is always present
- **Field constraints:** Length checks, enum validation, numeric ranges
- **Type validation:** Pydantic ensures correct types
- **Custom validators:** Domain-specific rules (e.g., sprint end_date > start_date)
- **Cross-field validation:** Relationships between fields are checked

All validation happens at instantiation time, ensuring contracts are always valid.
