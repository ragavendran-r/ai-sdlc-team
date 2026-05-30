# E-Commerce Platform - User Authentication Example

Complete example demonstrating the full AI SDLC Team pipeline building a user authentication system for an e-commerce platform.

## Overview

This example shows how a team of specialized AI agents collaborate to design and scaffold a complete authentication system from initial requirements through ready-to-implement code.

**Feature:** Secure user login, signup, and password reset
**Complexity:** Intermediate
**Duration:** 2-3 minutes (demo mode)
**Components Generated:** 4 React components + 1 service layer + 3 API endpoints

## Quick Start

### Run the Complete Pipeline

```bash
# From project root
python examples/ecommerce-platform/run.py
```

**Expected Output:**
1. 5 workflows execute in sequence (PO → EM → UX → Backend → Frontend)
2. 60+ event publications
3. Final status report showing all components

### View Results

After running, explore what was created:

```bash
# Check pipeline status
python run_team_pipeline.py status

# View event history
python run_team_pipeline.py events

# Browse artifacts
python run_team_pipeline.py context --timeline
python run_team_pipeline.py context --list

# Export complete state
python run_team_pipeline.py export --file ecommerce_state.json
```

## What This Example Demonstrates

### 1. PO Agent: Requirements Analysis
- Analyzes market needs for user authentication
- Creates 3 user stories:
  - US-AUTH-001: User login
  - US-AUTH-002: User signup
  - US-AUTH-003: Password reset
- Includes acceptance criteria, security considerations
- **Output:** USER_STORIES_CREATED event with complete specifications

### 2. EM Agent: Sprint Planning
- Ingests user stories
- Breaks down into 6 implementable tasks
- Estimates effort: 26 story points
- Team capacity: 32 points (achievable)
- Identifies risks: security audit, API complexity
- **Output:** SPRINT_CREATED event with full task breakdown

### 3. UX Agent: Design & User Flows
- Designs 5 components:
  - LoginForm (email + password fields)
  - SignupForm (with password validation)
  - ForgotPasswordForm (password reset)
  - ErrorMessage (feedback)
  - SuccessMessage (feedback)
- Creates user flows:
  - Login flow (5 steps)
  - Signup flow (5 steps)
- Defines design tokens:
  - Colors (primary, danger, success, warning)
  - Spacing (xs to xl)
  - Typography (heading, body, small)
  - Border radius (sm, md, lg)
- Specifies accessibility:
  - WCAG 2.1 Level AA compliance
  - Keyboard navigation
  - ARIA labels
  - Screen reader support
- **Output:** HANDOFF_CREATED event with complete design spec

### 4. Backend Agent: API & Database Design
- Designs REST API:
  - POST /auth/login (credentials → token)
  - POST /auth/signup (registration)
  - POST /auth/logout (session end)
  - GET /auth/me (current user)
- Database schema:
  - users table (id, email, password_hash, etc.)
  - sessions table (tokens, expiration)
  - login_attempts table (security logging)
- Security features:
  - HTTPS required
  - Password hashing (bcrypt, 12 salt rounds)
  - JWT token expiration (24 hours)
  - Rate limiting (100 req/hour per IP)
  - CSRF protection
- Password policy:
  - Minimum 8 characters
  - Uppercase, numbers, special characters required
- **Output:** API_CONTRACT_PUBLISHED event with complete OpenAPI spec

### 5. Frontend Agent: Component Scaffolding
- Generates 4 React components:
  - LoginForm.tsx (with full implementation outline)
  - SignupForm.tsx
  - ForgotPasswordForm.tsx
  - ErrorMessage.tsx
- Plans state management:
  - Use Context API (not Redux needed)
  - AuthContext with user, loading, error state
  - Actions: login, logout, signup, resetPassword
- API integration:
  - LoginForm calls POST /auth/login
  - Handles success (redirect) and error cases
- Accessibility implementation:
  - ARIA labels on all inputs
  - Keyboard navigation support
  - Error announcements for screen readers
- Test plan: 24 tests
  - 20 unit tests
  - 4 integration tests
  - 80% coverage target
- **Output:** COMPONENTS_SCAFFOLDED event with component specs and test outline

## Architecture Diagram

```
REQUIREMENTS (Market research, user need)
    ↓
PO AGENT ─→ User Stories (3 stories)
    ↓
EM AGENT ─→ Sprint Plan (6 tasks, 26 points)
    ├─→ UX AGENT ─→ Design Handoff (5 components, flows, tokens)
    ├─→ Backend AGENT ─→ API Contract (4 endpoints, DB schema)
    │        ↓ (routes to)
    └─→ Frontend AGENT ─→ Components (4 scaffolded components)
         ↓
    TEAM CONTEXT STORE
    (all artifacts stored and referenced)
         ↓
    OUTPUT: Complete specification ready for implementation
```

## Generated Artifacts

All artifacts are stored in `team-contracts/context-store/`:

1. **User Stories** (from PO)
   - Requirements and acceptance criteria
   - Security considerations
   - Priority and complexity estimates

2. **Sprint Plan** (from EM)
   - Task breakdown
   - Effort estimates
   - Dependencies and risks
   - Team capacity analysis

3. **Design Handoff** (from UX)
   - Component specifications
   - User flows
   - Design tokens
   - Accessibility requirements

4. **API Contract** (from Backend)
   - OpenAPI 3.0 specification
   - Database schema (DDL)
   - Security requirements
   - Authentication/authorization details

5. **Component Scaffolds** (from Frontend)
   - React component outlines
   - TypeScript interfaces
   - State management plan
   - Test specifications

## Key Learning Points

### 1. Workflow Integration
See how outputs from one workflow feed into the next:
- PO stories → EM sprint → Design & Backend work
- UX design → Frontend implementation
- Backend API → Frontend integration

### 2. Event-Driven Architecture
- Each workflow publishes events
- Events automatically route to dependent workflows
- Complete traceability of who created what and when

### 3. Security by Design
- Security concerns identified at PO level
- Backend validates all requirements
- Frontend implements WCAG accessibility
- Complete audit trail in context store

### 4. Team Collaboration
- Each agent has specialized focus
- Clear handoff points between teams
- Shared context store prevents miscommunication
- AI-driven consistency across all layers

## Customization Ideas

### Modify the Feature
Change what's being built:

```python
# In run.py, modify the user stories
"stories": [
    {
        "id": "US-FEATURE-001",
        "title": "Your new feature",
        "user_role": "...",
        # ... etc
    }
]
```

### Test Different Scenarios
Try different complexity levels:

```python
# Modify complexity in stories
"complexity": "simple",  # vs medium/complex
```

### Add More Workflows
Include additional specialized agents:

```python
# Add a security auditor workflow
security_event = Event(
    event_type=EventType.SECURITY_AUDIT_COMPLETED,
    workflow="security",
    payload={...},
)
orchestrator.publish_event(security_event)
```

### Use Real APIs
Replace stub tools with real implementations:

```python
# In backend-agent-workspace/agents/tools.py
class GitHubTool:
    @staticmethod
    def create_pull_request(title, body):
        # Call real GitHub API instead of stub
        from github import Github
        g = Github(os.getenv("GITHUB_TOKEN"))
        # ... create actual PR
```

## Expected Workflow

When you run this example, you should see:

```
✅ PO Agent creates 3 user stories
✅ EM Agent creates sprint plan with 6 tasks
✅ UX Agent designs 5 components + flows
✅ Backend Agent designs API (4 endpoints) + DB schema
✅ Frontend Agent scaffolds 4 React components
✅ All artifacts stored in context store
✅ Events routed automatically to downstream workflows
✅ Final status report shows complete pipeline
```

## Troubleshooting

### Problem: "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY=sk-your-key-here
```

### Problem: "Module not found"
```bash
# Ensure you're in project root and have installed dependencies
pip install -r requirements.txt
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Problem: "Connection refused"
If using Docker, ensure services are running:
```bash
docker-compose up -d
```

## Next Steps

### 1. Study the Output
```bash
python run_team_pipeline.py export --file study.json
# Open study.json and explore the artifact structures
```

### 2. Modify and Re-run
Change the user stories and re-run to see how changes propagate through the pipeline.

### 3. Create Your Own Example
Copy this example and customize it for your own feature:
```bash
cp -r examples/ecommerce-platform examples/your-feature
# Edit examples/your-feature/run.py
python examples/your-feature/run.py
```

### 4. Integrate Real Tools
Replace stub implementations with real API calls to GitHub, design tools, databases, etc.

### 5. Deploy the Result
Take the generated specifications and implement them with your team.

## Success Criteria

✅ **Complete**: All 5 workflows run successfully
✅ **Connected**: Events route correctly between workflows
✅ **Documented**: All artifacts describe implementation clearly
✅ **Security**: All security requirements identified and documented
✅ **Accessible**: Design meets WCAG 2.1 AA compliance
✅ **Testable**: Comprehensive test plan included
✅ **Production-Ready**: Output is ready for developer implementation

---

**Learning Resources:**
- See `QUICK_START.md` for 5-minute overview
- See `PROJECT_COMPLETE.md` for architecture details
- See `CONTRIBUTING.md` for how to customize further
- See `TEAM_ORCHESTRATOR_GUIDE.md` for orchestrator details
