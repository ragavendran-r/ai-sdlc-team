# AI SDLC Team Examples

Complete example projects showing the full pipeline in action.

## Available Examples

### 1. E-Commerce Platform
**Location:** `ecommerce-platform/`
**Complexity:** Intermediate
**Duration:** 2-3 minutes (demo mode)

Complete example of building a user authentication and product listing feature for an e-commerce platform, from requirements through frontend components.

**Demonstrates:**
- Full pipeline from PO → EM → UX → Backend → Frontend
- Human approval checkpoints
- Event routing and context store
- Security review (backend agent)
- Accessibility features (frontend agent)


## Running Examples

### Quick Start - E-Commerce Platform

```bash
cd examples/ecommerce-platform
python run.py

# Or use the main CLI
python ../../run_team_pipeline.py run --demo
```

### Step-by-Step Execution

Run each workflow individually to see the progression:

```bash
# 1. PO Agent creates user stories
python ../../run_team_pipeline.py run --workflows po

# 2. EM Agent creates sprint plan
python ../../run_team_pipeline.py run --workflows em

# 3. UX Agent designs interface
python ../../run_team_pipeline.py run --workflows ux

# 4. Backend Agent creates API
python ../../run_team_pipeline.py run --workflows backend

# 5. Frontend Agent scaffolds components
python ../../run_team_pipeline.py run --workflows frontend
```

### View Results

```bash
# Check what was created
python ../../run_team_pipeline.py status

# See the event flow
python ../../run_team_pipeline.py events

# Browse generated artifacts
python ../../run_team_pipeline.py context --timeline
python ../../run_team_pipeline.py context --list

# Export for review
python ../../run_team_pipeline.py export --file ecommerce_state.json
```

## Example: E-Commerce Platform - Detailed Walkthrough

### User Story: User Authentication

**Input:** Market research showing need for secure user accounts

```
1. PO AGENT (Product Owner)
   ├─→ Analyzes requirements
   ├─→ Creates UserStory "User Login"
   │   - Title: "Users can securely log in with email and password"
   │   - User Role: "Customer"
   │   - Acceptance Criteria:
   │       1. Form accepts email and password
   │       2. Valid credentials log in successfully
   │       3. Invalid credentials show error
   │       4. Passwords never displayed in plain text
   │       5. Failed attempts are logged
   │   - Complexity: Medium
   │   - Priority: High
   └─→ Published: USER_STORIES_CREATED event

2. EM AGENT (Engineering Manager)
   ├─→ Ingests user stories
   ├─→ Analyzes dependencies
   ├─→ Estimates capacity
   ├─→ Creates Sprint Plan
   │   - Sprint: "S-2.1: User Authentication"
   │   - Duration: 2 weeks
   │   - Tasks:
   │       - T-001: Design login flow (UX, 4h)
   │       - T-002: Implement login API (Backend, 6h)
   │       - T-003: Create login form (Frontend, 4h)
   │       - T-004: Connect form to API (Frontend, 3h)
   │       - T-005: Security audit (2h)
   │       - T-006: Create tests (3h)
   └─→ Published: SPRINT_CREATED event

3. UX AGENT (UX Designer)
   ├─→ Receives user story
   ├─→ Creates UserFlow
   │   - Start: User arrives at login
   │   - Decision: Has account?
   │   - End: Logged in and redirected to dashboard
   ├─→ Designs LoginForm Component
   │   - Fields: Email, Password
   │   - Validation: Required fields
   │   - Error handling: Show error message
   │   - Accessibility: ARIA labels, keyboard support
   ├─→ Defines DesignTokens
   │   - color-primary: #007bff
   │   - color-danger: #dc3545
   │   - radius-md: 4px
   │   - spacing-md: 1rem
   ├─→ Creates ComponentSpec
   │   - Component: LoginForm
   │   - Props: onSubmit, isLoading, error
   │   - Type: Form input
   │   - Complexity: Simple
   └─→ Published: HANDOFF_CREATED event

4. BACKEND AGENT (Backend Engineer)
   ├─→ Extracts Requirements
   │   - Data: User credentials
   │   - Logic: Password verification
   │   - Integration: Database lookup
   │   - Security: Password hashing, HTTPS
   ├─→ Designs DomainModel
   │   - Entity: User
   │       - Attributes: id (UUID), email, password_hash, created_at
   │       - Rules: Email must be unique, password hashed with bcrypt
   │   - Entity: Session
   │       - Attributes: id, user_id, token, expires_at
   │       - Rules: Tokens expire after 24 hours
   ├─→ Generates Database Schema
   │   - Table: users
   │       - id UUID PRIMARY KEY
   │       - email VARCHAR UNIQUE NOT NULL
   │       - password_hash VARCHAR NOT NULL
   │       - created_at TIMESTAMP
   │   - Table: sessions
   │       - id UUID PRIMARY KEY
   │       - user_id UUID FOREIGN KEY
   │       - token VARCHAR UNIQUE NOT NULL
   │       - expires_at TIMESTAMP
   │   - Indexes: users(email), sessions(token), sessions(user_id)
   ├─→ Creates APIContract (OpenAPI 3.0)
   │   - Endpoint 1: POST /auth/login
   │       - Request: { email, password }
   │       - Response: { token, user }
   │       - Errors: 400 Invalid credentials, 422 Validation error
   │   - Endpoint 2: GET /auth/user
   │       - Auth: Bearer token required
   │       - Response: { id, email, created_at }
   │   - Endpoint 3: POST /auth/logout
   │       - Auth: Bearer token required
   │       - Response: { success }
   ├─→ Scaffolds Service Layer
   │   - Class: AuthService
   │       - Method: authenticate(email, password) → User
   │       - Method: create_session(user_id) → Session
   │       - Method: validate_token(token) → User
   │       - Method: logout(token)
   ├─→ Security Review
   │   - ✅ HTTPS enforced
   │   - ✅ Password hashing (bcrypt)
   │   - ✅ Token expiration
   │   - ✅ SQL injection protection (parameterized queries)
   │   - ✅ Rate limiting recommended (TODO)
   │   - ⚠️ CSRF protection (implement in frontend)
   ├─→ Generates Tests
   │   - Test: Valid credentials return token
   │   - Test: Invalid password returns 401
   │   - Test: Missing email returns 400
   │   - Test: Expired token rejected
   └─→ Published: API_CONTRACT_PUBLISHED event

5. FRONTEND AGENT (Frontend Engineer)
   ├─→ Receives UX Handoff + API Contract
   ├─→ Breaks Down Components
   │   - C-001: LoginForm
   │   - C-002: ErrorMessage
   │   - C-003: LoadingSpinner
   ├─→ Maps Design Tokens
   │   - LoginForm uses: color-primary, color-danger, spacing-md, radius-md
   │   - ErrorMessage uses: color-danger
   │   - LoadingSpinner: color-primary
   ├─→ Plans API Integration
   │   - LoginForm → POST /auth/login
   │   - Success → Redirect to dashboard
   │   - Error → Show error message
   ├─→ Scaffolds Components
   │   - File: components/LoginForm.tsx
   │     ```typescript
   │     interface LoginFormProps {
   │       onSuccess?: () => void;
   │     }
   │     
   │     export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
   │       const [email, setEmail] = useState('');
   │       const [password, setPassword] = useState('');
   │       const [error, setError] = useState('');
   │       const [isLoading, setIsLoading] = useState(false);
   │       
   │       const handleSubmit = async (e: React.FormEvent) => {
   │         e.preventDefault();
   │         setIsLoading(true);
   │         
   │         try {
   │           const response = await fetch('/auth/login', {
   │             method: 'POST',
   │             headers: { 'Content-Type': 'application/json' },
   │             body: JSON.stringify({ email, password }),
   │           });
   │           
   │           if (response.ok) {
   │             onSuccess?.();
   │           } else {
   │             setError('Invalid credentials');
   │           }
   │         } catch (err) {
   │           setError('Network error');
   │         } finally {
   │           setIsLoading(false);
   │         }
   │       };
   │       
   │       return (
   │         <form onSubmit={handleSubmit}>
   │           <input
   │             type="email"
   │             value={email}
   │             onChange={(e) => setEmail(e.target.value)}
   │             placeholder="Email"
   │             aria-label="Email address"
   │             required
   │           />
   │           <input
   │             type="password"
   │             value={password}
   │             onChange={(e) => setPassword(e.target.value)}
   │             placeholder="Password"
   │             aria-label="Password"
   │             required
   │           />
   │           {error && <ErrorMessage>{error}</ErrorMessage>}
   │           <button
   │             type="submit"
   │             disabled={isLoading}
   │             aria-label={isLoading ? 'Logging in...' : 'Log in'}
   │           >
   │             {isLoading ? <LoadingSpinner /> : 'Log In'}
   │           </button>
   │         </form>
   │       );
   │     };
   │     ```
   ├─→ Plans State Management
   │   - Use: Context API for user session
   │   - Provider: AuthContext
   │   - State: { user, isLoading, error }
   │   - Actions: login(email, password), logout()
   ├─→ Adds Accessibility
   │   - ARIA labels on all inputs
   │   - Keyboard navigation (Tab, Enter)
   │   - Error announcements
   │   - Focus management
   ├─→ Generates Tests
   │   - Test: Form renders correctly
   │   - Test: Submit calls API
   │   - Test: Error message displays
   │   - Test: Loading state shows spinner
   │   - Test: Keyboard navigation works
   ├─→ Code Review
   │   - ✅ No hardcoded API URLs (use config)
   │   - ✅ ARIA labels present
   │   - ✅ Tests cover happy path and errors
   │   - ✅ No console warnings
   └─→ Published: COMPONENTS_SCAFFOLDED event

FINAL OUTPUT:
- ✅ Complete user authentication system
- ✅ Secure API with password hashing
- ✅ Accessible React component
- ✅ Comprehensive tests
- ✅ Security review completed
- ✅ Ready for implementation
```

## Creating Your Own Example

### 1. Create Example Directory

```bash
mkdir examples/your-feature
cd examples/your-feature
touch README.md run.py requirements.txt
```

### 2. Create Run Script

```python
# examples/your-feature/run.py
#!/usr/bin/env python
"""Run the complete pipeline for your feature."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from team_orchestrator import TeamOrchestrator, Event, EventType

def run_example():
    """Execute the complete example."""
    orchestrator = TeamOrchestrator()
    orchestrator.start_pipeline()
    
    # PO Agent: Create user stories
    po_event = Event(
        event_type=EventType.USER_STORIES_CREATED,
        workflow="po",
        payload={
            "stories": [
                {
                    "id": "US-001",
                    "title": "Your feature title",
                    "acceptance_criteria": [
                        "Criterion 1",
                        "Criterion 2",
                    ]
                }
            ]
        },
        source_agent="example-po-agent"
    )
    orchestrator.publish_event(po_event)
    
    # ... continue with other workflows
    
    orchestrator.complete_pipeline()
    orchestrator.print_status_report()

if __name__ == "__main__":
    run_example()
```

### 3. Document the Example

```markdown
# Your Feature Example

## Overview
Brief description of what this example demonstrates.

## Workflow
1. **PO Agent:** What the PO does
2. **EM Agent:** What the EM does
3. **UX Agent:** What the UX does
4. **Backend Agent:** What the backend does
5. **Frontend Agent:** What the frontend does

## Running the Example
\`\`\`bash
python run.py
\`\`\`

## Expected Output
Description of what should be created.

## Key Learnings
- Learning point 1
- Learning point 2
```

## Customizing Examples

Each example can be customized by:

1. **Changing the feature focus** - Edit the user stories in the event payload
2. **Modifying requirements** - Update acceptance criteria
3. **Using different tools** - Call actual APIs instead of stubs
4. **Testing variations** - Try different LLM temperatures or models
5. **Adding custom routes** - Create specialized workflows

## Understanding the Output

After running an example, check:

```bash
# Pipeline status
python ../../run_team_pipeline.py status

# Event history
python ../../run_team_pipeline.py events

# Artifact timeline
python ../../run_team_pipeline.py context --timeline

# Exported state
python ../../run_team_pipeline.py export --file example_state.json
cat example_state.json | jq '.orchestrator_state'
```

---

**Tips:**
- Start with `ecommerce-platform` for a complete example
- Read CONTRIBUTING.md to customize further
- Check PROJECT_COMPLETE.md for architecture details
- Use examples as templates for your own projects
