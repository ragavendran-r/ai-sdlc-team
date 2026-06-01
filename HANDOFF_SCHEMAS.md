# Handoff Contract Schemas - Complete Reference

## Overview

The AI SDLC Team uses **Pydantic-based handoff contracts** to ensure type-safe, validated communication between agents. Each contract includes full validation, human-readable markdown output, and agent-friendly serialization.

## The 5 Core Contracts

### 1. 📋 UserStory (`user_story.py`)
**From:** PO Agent → **To:** EM Agent

The primary input to sprint planning. Contains everything needed for engineering to scope and prioritize work.

**Key fields:**
- User story format (role → goal → value)
- Acceptance criteria (testable, specific)
- Priority enum (critical, high, medium, low)
- Complexity enum (XS, S, M, L, XL)
- Dependencies and related stories

**Example:**
```python
story = UserStory(
    id="US-001",
    title="User login with email and password",
    description="Users should be able to log in securely",
    user_role="Customer",
    user_goal="log in to my account",
    business_value="enables personalization and data protection",
    acceptance_criteria=[
        "User can enter email and password",
        "Valid credentials log in successfully",
        "Invalid credentials show error message",
    ],
    priority=Priority.HIGH,
    estimated_complexity=Complexity.M,
    created_by="po-agent",
)
```

---

### 2. 📅 SprintPlan (`sprint_plan.py`)
**From:** EM Agent → **To:** Frontend, Backend, UX Agents

Complete sprint plan with all tasks assigned and ready for execution. Includes task graph with dependencies.

**Key structures:**
- **Sprint**: Container with start/end dates, duration validation
- **SprintTask**: Individual task with assignment, hours, dependencies
- **SprintPlan**: Sprint + context (user stories, shared context)

**TaskType enum:** design, frontend, backend, integration_test, devops
**TaskStatus enum:** assigned, in_progress, blocked, in_review, completed

**Helper methods:**
- `get_tasks_by_agent()` - Group tasks by assigned agent
- `get_blocked_tasks()` - Find tasks currently blocked
- `total_estimated_hours()` - Sum of effort estimates
- `total_actual_hours()` - Sum of actual work done

**Example:**
```python
plan = SprintPlan(
    sprint=Sprint(
        id="S-2.1",
        name="Sprint 2.1 - Authentication",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=14),
        tasks=[
            SprintTask(
                id="T-001",
                user_story_id="US-001",
                title="Implement login form UI",
                assigned_to="frontend-agent",
                task_type=TaskType.FRONTEND,
                estimated_hours=4,
                acceptance_criteria=["Form displays", "Validation works"],
            ),
        ],
        created_by="em-agent",
    ),
    created_by="em-agent",
)
```

---

### 3. 🎨 UXHandoff (`ux_handoff.py`)
**From:** UX Agent → **To:** Frontend Agent

Complete design specifications for implementation. Contains components, design tokens, interactions.

**Key structures:**
- **ComponentSpec**: Full component specification
- **DesignToken**: Design system tokens (colors, spacing, typography)
- **InteractionSpec**: Interactions and animations
- **ResponsiveBehavior**: Layout for different breakpoints

**ComponentType enum:** form, button, card, modal, navigation, list, table, chart, custom

**Example component:**
```python
component = ComponentSpec(
    id="C-001",
    name="LoginForm",
    component_type=ComponentType.FORM,
    description="Login form with email and password",
    design_notes="Minimal, clean form with primary action button",
    states={
        "default": "Both fields empty",
        "hover": "Field border highlighted",
        "filled": "Submit button enabled",
    },
    props={
        "onSubmit": "Callback when form submits",
        "isLoading": "Show loading state",
    },
    interactions=[
        InteractionSpec(
            name="field-focus",
            trigger="on-focus",
            behavior="label-slides-up",
            duration_ms=200,
        )
    ],
    accessibility_notes="WCAG 2.1 AA compliant",
)
```

---

### 4. 🔌 APIContract (`api_contract.py`)
**From:** Backend Agent → **To:** Frontend Agent

Complete API specification for integration. Contains endpoints with schemas, error handling, auth.

**Key structures:**
- **APIEndpoint**: Single endpoint specification
- **JSONSchema**: Simplified schema for request/response
- **QueryParameter**: Query parameter definition
- **ErrorResponse**: Error code and status

**HTTPMethod enum:** GET, POST, PUT, PATCH, DELETE
**HTTPStatus enum:** 200, 201, 400, 401, 403, 404, 500, 503, etc.
**AuthType enum:** none, bearer_token, api_key, oauth2, session

**Example endpoint:**
```python
endpoint = APIEndpoint(
    id="EP-001",
    method=HTTPMethod.POST,
    path="/api/v1/auth/login",
    summary="User login",
    description="Authenticate user with email and password",
    auth_required=False,
    request_schema=JSONSchema(
        type="object",
        properties={
            "email": {"type": "string"},
            "password": {"type": "string"},
        },
        required=["email", "password"],
    ),
    response_schema=JSONSchema(
        type="object",
        properties={
            "token": {"type": "string"},
            "user": {"type": "object"},
        },
    ),
    error_responses=[
        ErrorResponse(
            status=HTTPStatus.BAD_REQUEST,
            error_code="INVALID_CREDENTIALS",
            message="Email or password is incorrect",
        ),
    ],
)
```

---

### 5. 🏗️ DesignDecision (`design_decision.py`)
**From:** Any Agent → **To:** Team Record

Architecture Decision Records (ADR format) documenting important decisions with rationale and consequences.

**Key structures:**
- **Alternative**: Option considered with pros/cons
- **Consequence**: Positive/negative outcome with mitigation
- **DesignDecision**: Complete ADR record

**DecisionCategory enum:** architecture, data_model, api_design, ui_ux, infrastructure, process, technology_choice, security, performance

**DecisionStatus enum:** proposed, accepted, deprecated, superseded

**DecisionImpact enum:** local, feature, system, organization

**Helper methods:**
- `get_positive_consequences()` - Benefits of decision
- `get_negative_consequences()` - Drawbacks and mitigations

**Example:**
```python
decision = DesignDecision(
    id="ADR-001",
    title="Use JWT tokens for API authentication",
    category=DecisionCategory.API_DESIGN,
    impact=DecisionImpact.SYSTEM,
    context="Our application needs stateless authentication across multiple servers",
    decision="We will use JWT (JSON Web Tokens) for API authentication",
    rationale="JWT is stateless and scalable, works across distributed systems",
    alternatives=[
        Alternative(
            name="Session-based authentication",
            description="Store sessions on server, use cookies",
            pros=["Simpler initially", "Can revoke immediately"],
            cons=["Not scalable", "Server-side storage needed"],
        ),
    ],
    consequences=[
        Consequence(
            type="scalability",
            description="Stateless tokens allow horizontal scaling",
            is_positive=True,
        ),
        Consequence(
            type="security",
            description="Tokens can be stolen if localStorage is compromised",
            is_positive=False,
            mitigation="Use httpOnly cookies and implement CSRF protection",
        ),
    ],
    created_by="backend-agent",
)
```

---

## Schema Methods

Every schema implements two key methods:

### `to_markdown()` → String
Generates human-readable formatted documentation perfect for:
- Sharing with team
- Creating permanent records
- Generating documentation
- Code review comments

```python
print(story.to_markdown())  # Outputs formatted user story
with open("sprint.md", "w") as f:
    f.write(plan.to_markdown())  # Save sprint document
```

### `to_dict()` → Dict
Serializes to agent-friendly dictionary:
- All dates as ISO strings
- Enums as string values
- JSON-serializable
- Ready for agent processing

```python
agent_data = story.to_dict()
send_to_agent(agent_data)  # Pass to agent
save_json(agent_data)  # Persist as JSON
```

---

## Validation

All schemas include comprehensive validation:

### Type Checking
- Pydantic ensures all fields have correct types
- Enums constrained to allowed values
- List/dict structures validated

### Field Constraints
- Length checks (min/max)
- Numeric ranges
- Required vs optional fields
- Custom validators

### Cross-Field Validation
- Sprint end_date must be after start_date
- Sprint duration 1-30 days
- Task dependencies reference valid tasks
- Example: DesignDecision requires context + decision + rationale

### Examples
```python
# ❌ Too short title
try:
    UserStory(id="US-001", title="Bad", ...)
except ValidationError:
    print("Title must be 5+ characters")

# ❌ End before start
try:
    Sprint(start_date=tomorrow, end_date=today, ...)
except ValidationError:
    print("End date must be after start date")

# ✅ Valid
story = UserStory(
    id="US-001",
    title="Valid user story title",  # 5+ chars
    description="Valid description",  # 20+ chars
    ...
)
```

---

## File Structure

```
team_contracts/schemas/
├── user_story.py              # 275 lines
├── sprint_plan.py             # 425 lines
├── ux_handoff.py              # 400 lines
├── api_contract.py            # 500 lines
├── design_decision.py         # 475 lines
├── __init__.py                # Central imports
├── README.md                  # Detailed documentation
├── SCHEMAS_OVERVIEW.md        # Implementation overview
├── requirements.txt           # Dependencies
└── test_schemas.py            # Test suite (25+ tests)

Total: 2,527 lines of production code
```

---

## Usage in Workflows

### PO Workflow
```python
from team_contracts.schemas import UserStory, Priority, Complexity

# Create user stories
stories = [UserStory(...), UserStory(...)]

# Output for team
for story in stories:
    print(story.to_markdown())

# Send to EM as dicts
for story in stories:
    em_agent.receive_requirement(story.to_dict())
```

### EM Workflow
```python
from team_contracts.schemas import SprintPlan, Sprint, SprintTask

# Receive stories from PO
stories = [po_agent.get_stories()]

# Create sprint plan
plan = SprintPlan(
    sprint=Sprint(
        tasks=[
            SprintTask(assigned_to="frontend-agent", ...),
            SprintTask(assigned_to="backend-agent", ...),
        ],
        ...
    ),
    user_stories={s.id: s.to_dict() for s in stories},
)

# Document sprint
with open("sprint-plan.md", "w") as f:
    f.write(plan.to_markdown())

# Assign work to agents
frontend_agent.receive_plan(plan.to_dict())
backend_agent.receive_plan(plan.to_dict())
```

### Frontend Workflow
```python
from team_contracts.schemas import UXHandoff, APIContract

# Receive from UX and Backend
ux_spec = UXHandoff(**received_ux_data)
api_spec = APIContract(**received_api_data)

# Implement components
for component in ux_spec.components:
    build_component(component)

# Generate API client
for endpoint in api_spec.endpoints:
    generate_client(endpoint)
```

---

## Testing

All schemas include comprehensive tests:

```bash
# Run all tests
pytest test_schemas.py -v

# Run specific test class
pytest test_schemas.py::TestUserStory -v

# Run specific test
pytest test_schemas.py::TestUserStory::test_valid_user_story -v
```

Tests cover:
- Valid instantiation
- Field validation
- Invalid inputs
- Markdown generation
- Dict conversion
- JSON serialization
- Helper methods

---

## Dependencies

```
pydantic>=2.0.0,<3.0.0   # Data validation
python-dateutil>=2.8.0   # Date utilities
```

Install:
```bash
pip install -r team_contracts/schemas/requirements.txt
```

---

## Next Steps

1. **Create Events** - Define corresponding event types in `team_contracts/events/`
2. **Build Context Store** - Implement shared context storage using these schemas
3. **Implement Agents** - Use schemas in agent code with validated handoffs
4. **Create Tests** - Write integration tests for agent workflows
5. **Build Agent SDK** - Provide utilities for agents to work with schemas

---

## Quick Links

- [README.md](./team_contracts/schemas/README.md) - Detailed usage guide
- [SCHEMAS_OVERVIEW.md](./team_contracts/schemas/SCHEMAS_OVERVIEW.md) - Implementation details
- [user_story.py](./team_contracts/schemas/user_story.py) - UserStory source
- [sprint_plan.py](./team_contracts/schemas/sprint_plan.py) - SprintPlan source
- [ux_handoff.py](./team_contracts/schemas/ux_handoff.py) - UXHandoff source
- [api_contract.py](./team_contracts/schemas/api_contract.py) - APIContract source
- [design_decision.py](./team_contracts/schemas/design_decision.py) - DesignDecision source
