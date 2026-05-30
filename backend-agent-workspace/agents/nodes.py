"""Backend Agent nodes for LangGraph workflow."""

import json
from datetime import datetime
from anthropic import Anthropic

from .state import BackendWorkflowState
from .tools import (
    ContextStoreTool,
    DatabaseTool,
    CodeGenerationTool,
    GitHubTool,
    ValidationTool,
    EventTool,
    ToolResult,
)

# LLM Configuration
MODEL = "claude-sonnet-4-20250514"
client = Anthropic()


def _log_message(state: BackendWorkflowState, agent: str, message: str) -> None:
    """Log a message to state."""
    state.current_agent = agent
    state.messages.append({
        "agent": agent,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    })


def _handle_error(state: BackendWorkflowState, agent: str, error: str) -> None:
    """Handle an error."""
    state.errors.append(f"[{agent}] {error}")
    _log_message(state, agent, f"ERROR: {error}")


def requirements_intake(state: BackendWorkflowState) -> BackendWorkflowState:
    """
    Node 1: requirements_intake
    Filters stories requiring backend work and extracts data requirements,
    business rules, and integration needs.
    """
    _log_message(state, "requirements_intake", "Starting backend requirements extraction...")

    try:
        # Prepare context from user stories
        stories_context = json.dumps([s for s in state.user_stories], default=str)

        prompt = f"""Analyze these user stories and extract backend requirements.
For each story requiring backend work, identify:
1. Data persistence needs
2. Business logic rules
3. API endpoints needed
4. External integrations
5. Validation requirements

User Stories:
{stories_context}

Return a JSON array of requirements with: id, user_story_id, title, description, requirement_type, data_needs, business_rules, external_integrations, constraints."""

        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        # Extract JSON from response
        try:
            reqs = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback: create minimal requirements
            reqs = [{
                "id": f"REQ-{i+1}",
                "user_story_id": story.get("id", f"US-{i+1}"),
                "title": story.get("title", "Backend Requirement"),
                "description": story.get("description", ""),
                "requirement_type": "api_endpoint",
                "business_rules": [],
                "data_needs": None,
                "external_integrations": [],
            } for i, story in enumerate(state.user_stories)]

        state.backend_requirements = reqs
        state.requirements_intake_complete = True
        _log_message(state, "requirements_intake", f"Extracted {len(reqs)} requirements")

    except Exception as e:
        _handle_error(state, "requirements_intake", str(e))

    return state


def domain_model(state: BackendWorkflowState) -> BackendWorkflowState:
    """
    Node 2: domain_model
    Identifies domain entities, their attributes, and relationships
    from the requirements.
    """
    _log_message(state, "domain_model", "Starting domain model generation...")

    try:
        if not state.backend_requirements:
            _handle_error(state, "domain_model", "No backend requirements available")
            return state

        reqs_context = json.dumps(state.backend_requirements, default=str)

        prompt = f"""Based on these backend requirements, design a domain model.
Identify:
1. Domain entities (aggregates, value objects)
2. Attributes with types (string, integer, datetime, etc.)
3. Relationships between entities (one-to-one, one-to-many, many-to-many)
4. Business invariants
5. Ubiquitous language terms

Requirements:
{reqs_context}

Return a JSON object with: id, feature_name, description, entities (list with name, description, plural, attributes), relationships (list with from_entity, to_entity, relation_type), ubiquitous_language (dict), invariants (list)."""

        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        try:
            model_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback model
            model_data = {
                "id": "DM-001",
                "feature_name": "Domain Model",
                "description": "Generated domain model",
                "entities": [],
                "relationships": [],
                "ubiquitous_language": {},
                "invariants": [],
            }

        state.domain_model = model_data
        state.domain_model_complete = True
        _log_message(state, "domain_model", "Domain model created")

    except Exception as e:
        _handle_error(state, "domain_model", str(e))

    return state


def database_schema(state: BackendWorkflowState) -> BackendWorkflowState:
    """
    Node 3: database_schema
    Generates database schema from domain model - produces DDL SQL
    and SQLAlchemy model code.
    """
    _log_message(state, "database_schema", "Generating database schema...")

    try:
        if not state.domain_model:
            _handle_error(state, "database_schema", "No domain model available")
            return state

        model_context = json.dumps(state.domain_model, default=str)

        prompt = f"""Generate a complete database schema from this domain model.
Produce:
1. DDL SQL for all tables with proper types, constraints, indexes
2. SQLAlchemy ORM model classes with relationships

Domain Model:
{model_context}

Return a JSON object with: id, feature_name, ddl_sql (complete SQL string), sqlalchemy_models (complete Python code string), migration_notes."""

        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        try:
            schema_data = json.loads(response_text)
        except json.JSONDecodeError:
            schema_data = {
                "id": "SCHEMA-001",
                "feature_name": "Database Schema",
                "ddl_sql": "-- Generated schema",
                "sqlalchemy_models": "# Generated models",
                "migration_notes": None,
            }

        state.db_schema = schema_data
        state.db_schema_complete = True
        _log_message(state, "database_schema", "Database schema generated")

    except Exception as e:
        _handle_error(state, "database_schema", str(e))

    return state


def api_contract(state: BackendWorkflowState) -> BackendWorkflowState:
    """
    Node 4: api_contract
    Generates OpenAPI 3.0 spec covering all endpoints implied by
    the requirements.
    """
    _log_message(state, "api_contract", "Generating API contract...")

    try:
        reqs_context = json.dumps(state.backend_requirements, default=str)
        model_context = json.dumps(state.domain_model or {}, default=str)

        prompt = f"""Generate an OpenAPI 3.0 specification for all API endpoints.
Include:
1. All CRUD endpoints for domain entities
2. Request/response schemas
3. Error responses with proper HTTP status codes
4. Authentication requirements
5. Rate limiting info

Requirements:
{reqs_context}

Domain Model:
{model_context}

Return a JSON object matching APIContract schema with: id, feature_name, user_story_id, base_url, endpoints (list), global_auth_requirements, global_headers, security_notes."""

        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        try:
            contract_data = json.loads(response_text)
        except json.JSONDecodeError:
            contract_data = {
                "id": "API-001",
                "feature_name": "API Contract",
                "user_story_id": "US-001",
                "base_url": "https://api.example.com/v1",
                "endpoints": [],
                "global_auth_requirements": "Bearer token",
                "global_headers": {"Content-Type": "application/json"},
            }

        state.api_contract = contract_data
        state.api_contract_complete = True

        # Write to context store
        ContextStoreTool.write_api_contract(contract_data)
        _log_message(state, "api_contract", "API contract generated and written to context store")

    except Exception as e:
        _handle_error(state, "api_contract", str(e))

    return state


def business_logic_scaffolding(state: BackendWorkflowState) -> BackendWorkflowState:
    """
    Node 5: business_logic_scaffolding
    Generates Python service layer scaffolding with method stubs
    for each API operation.
    """
    _log_message(state, "business_logic_scaffolding", "Generating service layer...")

    try:
        if not state.domain_model:
            _handle_error(state, "business_logic_scaffolding", "No domain model available")
            return state

        model_context = json.dumps(state.domain_model, default=str)
        contract_context = json.dumps(state.api_contract or {}, default=str)

        prompt = f"""Generate service layer scaffolding with method stubs.
For each domain entity, create a service class with:
1. CRUD operation method stubs (create, read, update, delete)
2. Business logic method stubs based on requirements
3. Detailed docstrings with business rules
4. Type hints

Domain Model:
{model_context}

API Contract:
{contract_context}

Return a JSON array of ServiceScaffold objects with: id, entity_name, class_name, python_code (complete class string), methods (list with name, description, parameters, return_type, business_rules), dependencies."""

        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        try:
            scaffolds = json.loads(response_text)
        except json.JSONDecodeError:
            scaffolds = []

        state.service_scaffolds = scaffolds if isinstance(scaffolds, list) else []
        state.scaffolding_complete = True
        _log_message(state, "business_logic_scaffolding", f"Generated {len(state.service_scaffolds)} services")

    except Exception as e:
        _handle_error(state, "business_logic_scaffolding", str(e))

    return state


def validation_rules(state: BackendWorkflowState) -> BackendWorkflowState:
    """
    Node 6: validation_rules
    Identifies validation rules from acceptance criteria and generates
    Pydantic validator code.
    """
    _log_message(state, "validation_rules", "Generating validation rules...")

    try:
        if not state.backend_requirements:
            _handle_error(state, "validation_rules", "No requirements available")
            return state

        reqs_context = json.dumps(state.backend_requirements, default=str)
        contract_context = json.dumps(state.api_contract or {}, default=str)

        prompt = f"""Generate Pydantic validators for request validation.
For each API endpoint, identify validation rules and generate:
1. Pydantic model classes with validators
2. Field-level validators (min/max length, patterns, etc.)
3. Cross-field validators
4. Error messages

Requirements:
{reqs_context}

API Contract:
{contract_context}

Return a JSON array of ValidationModule objects with: id, request_name, endpoint_id, python_code (complete Pydantic model string), rules (list), test_cases (list of valid/invalid examples)."""

        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        try:
            validators = json.loads(response_text)
        except json.JSONDecodeError:
            validators = []

        state.validation_modules = validators if isinstance(validators, list) else []
        state.validation_rules_complete = True
        _log_message(state, "validation_rules", f"Generated {len(state.validation_modules)} validators")

    except Exception as e:
        _handle_error(state, "validation_rules", str(e))

    return state


def security_review(state: BackendWorkflowState) -> BackendWorkflowState:
    """
    Node 7: security_review
    Reviews API contract against OWASP API Security Top 10.
    Routes to human_checkpoint immediately if critical flags found.
    """
    _log_message(state, "security_review", "Reviewing security...")

    try:
        contract_context = json.dumps(state.api_contract or {}, default=str)
        reqs_context = json.dumps(state.backend_requirements, default=str)

        prompt = f"""Review this API contract for security issues against OWASP API Top 10.
Identify issues with:
1. Authentication/Authorization (broken auth, missing auth)
2. Injection risks (SQL injection, NoSQL injection)
3. Sensitive data exposure (PII in URLs, unencrypted data)
4. Insufficient logging
5. Rate limiting
6. CORS misconfiguration
7. Other OWASP risks

API Contract:
{contract_context}

Requirements:
{reqs_context}

Return a JSON array of SecurityFlag objects with: id, endpoint_id, title, description, severity (critical/high/medium/low), category, vulnerable_code, remediation, reference_url."""

        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        try:
            flags = json.loads(response_text)
        except json.JSONDecodeError:
            flags = []

        state.security_flags = flags if isinstance(flags, list) else []
        state.security_review_complete = True

        # Check for critical flags
        critical_flags = [f for f in state.security_flags if f.get("severity") == "critical"]
        if critical_flags:
            state.has_critical_security_flags = True
            state.checkpoint_triggered_early_for_security = True
            _log_message(state, "security_review", f"⚠️ CRITICAL: Found {len(critical_flags)} critical security flags!")
        else:
            _log_message(state, "security_review", f"Security review complete. Found {len(state.security_flags)} issues")

    except Exception as e:
        _handle_error(state, "security_review", str(e))

    return state


def unit_test_generation(state: BackendWorkflowState) -> BackendWorkflowState:
    """
    Node 8: unit_test_generation
    Generates pytest test stubs - unit tests per service, integration tests
    per endpoint.
    """
    _log_message(state, "unit_test_generation", "Generating test stubs...")

    try:
        scaffolds_context = json.dumps(state.service_scaffolds, default=str)
        contract_context = json.dumps(state.api_contract or {}, default=str)
        validators_context = json.dumps(state.validation_modules, default=str)

        prompt = f"""Generate pytest test stubs for the services and API.
Generate:
1. Unit tests for each service method
2. Integration tests for each API endpoint
3. Validation tests for request validation
4. Edge case tests

Service Scaffolds:
{scaffolds_context}

API Contract:
{contract_context}

Validators:
{validators_context}

Return a JSON array of test file objects with: id, service_name, file_path, test_code (complete pytest string), test_methods (list with name, type, description), mocks_required."""

        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        try:
            tests = json.loads(response_text)
        except json.JSONDecodeError:
            tests = []

        state.test_files = tests if isinstance(tests, list) else []
        state.test_generation_complete = True
        _log_message(state, "unit_test_generation", f"Generated {len(state.test_files)} test files")

    except Exception as e:
        _handle_error(state, "unit_test_generation", str(e))

    return state


def human_checkpoint(state: BackendWorkflowState) -> BackendWorkflowState:
    """
    Node 9: human_checkpoint
    Single approval gate with rejection loop. If critical security flags
    exist and routed here early, clearly mark as SECURITY REVIEW REQUIRED.
    """
    _log_message(state, "human_checkpoint", "Waiting for human approval...")

    try:
        # Prepare summary
        summary = f"""
╔════════════════════════════════════════════════════════════════╗
║              BACKEND AGENT IMPLEMENTATION SUMMARY              ║
╚════════════════════════════════════════════════════════════════╝

📦 DOMAIN MODEL
  Entities: {len(state.domain_model.get('entities', []) if state.domain_model else [])}
  Relationships: {len(state.domain_model.get('relationships', []) if state.domain_model else [])}

🗄️  DATABASE SCHEMA
  Tables: {len(state.db_schema.get('ddl_sql', '').split('CREATE TABLE') if state.db_schema else 0) - 1}

🔌 API CONTRACT
  Endpoints: {len(state.api_contract.get('endpoints', []) if state.api_contract else [])}

⚙️  SERVICES
  Service Classes: {len(state.service_scaffolds)}

✅ VALIDATION
  Validators: {len(state.validation_modules)}

🧪 TESTS
  Test Files: {len(state.test_files)}

🔒 SECURITY REVIEW
  Issues Found: {len(state.security_flags)}
"""
        if state.checkpoint_triggered_early_for_security:
            summary += "\n⚠️  SECURITY REVIEW REQUIRED - Critical issues detected\n"

        critical_flags = [f for f in state.security_flags if f.get("severity") == "critical"]
        if critical_flags:
            summary += f"\n🔴 CRITICAL ISSUES ({len(critical_flags)}):\n"
            for flag in critical_flags[:3]:
                summary += f"  - {flag.get('title', 'Unknown issue')}\n"

        print(summary)

        # Get user input
        user_input = input("\n👤 Do you approve? (y/n/modify): ").strip().lower()

        if user_input == "y":
            state.implementation_approved = True
            _log_message(state, "human_checkpoint", "✅ Implementation approved by human")
        elif user_input == "n":
            feedback = input("📝 Feedback for revision: ").strip()
            state.approval_feedback = feedback
            _log_message(state, "human_checkpoint", f"❌ Implementation rejected. Feedback: {feedback}")
        else:
            feedback = input("📝 Modification request: ").strip()
            state.approval_feedback = feedback
            _log_message(state, "human_checkpoint", f"🔄 Modification requested: {feedback}")

    except Exception as e:
        _handle_error(state, "human_checkpoint", str(e))
        state.implementation_approved = False

    return state


def pr_description(state: BackendWorkflowState) -> BackendWorkflowState:
    """
    Node 10: pr_description
    Generates structured PR description with migration notes and
    security considerations.
    """
    _log_message(state, "pr_description", "Generating PR description...")

    try:
        model_context = json.dumps(state.domain_model or {}, default=str)
        contract_context = json.dumps(state.api_contract or {}, default=str)
        schema_context = json.dumps(state.db_schema or {}, default=str)
        sec_context = json.dumps(state.security_flags, default=str)

        prompt = f"""Generate a comprehensive PR description for backend implementation.
Include:
1. Summary of changes
2. API endpoints added
3. Database schema changes
4. Security considerations and fixes
5. Migration/deployment notes
6. Testing checklist

Domain Model:
{model_context}

API Contract:
{contract_context}

Database Schema:
{schema_context}

Security Issues:
{sec_context}

Write in markdown format suitable for GitHub PR."""

        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        state.pr_description = message.content[0].text
        state.pr_creation_complete = True
        _log_message(state, "pr_description", "PR description generated")

    except Exception as e:
        _handle_error(state, "pr_description", str(e))

    return state


def code_review(state: BackendWorkflowState) -> BackendWorkflowState:
    """
    Node 11: code_review
    Reviews code against team conventions - checks for missing tests,
    unhandled exceptions, N+1 queries, missing validation, security issues.
    """
    _log_message(state, "code_review", "Running code review...")

    try:
        scaffolds_context = json.dumps(state.service_scaffolds, default=str)
        tests_context = json.dumps(state.test_files, default=str)

        prompt = f"""Review the service code against these standards:
1. All methods have tests
2. All exceptions are handled
3. No N+1 query problems
4. Input validation on all endpoints
5. Security best practices followed
6. Type hints present
7. Docstrings complete

Service Code:
{scaffolds_context}

Tests:
{tests_context}

Return a JSON array of review comments with: id, severity (blocker/major/minor/suggestion), category, title, message, suggested_fix."""

        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        try:
            comments = json.loads(response_text)
        except json.JSONDecodeError:
            comments = []

        state.review_comments = comments if isinstance(comments, list) else []
        state.code_review_complete = True
        _log_message(state, "code_review", f"Code review complete. Found {len(state.review_comments)} items")

    except Exception as e:
        _handle_error(state, "code_review", str(e))

    return state


def api_publishing(state: BackendWorkflowState) -> BackendWorkflowState:
    """
    Node 12: api_publishing
    Publishes the API contract to context store and fires event for
    frontend workflow.
    """
    _log_message(state, "api_publishing", "Publishing API contract...")

    try:
        if state.api_contract:
            # Write to context store
            ContextStoreTool.write_api_contract(state.api_contract)

            # Fire event for frontend workflow
            EventTool.fire_event(
                "api_contract_published",
                {"contract_id": state.api_contract.get("id")}
            )

            state.api_published = True
            state.api_publishing_complete = True
            _log_message(state, "api_publishing", "✅ API contract published to context store and event fired")
        else:
            _handle_error(state, "api_publishing", "No API contract to publish")

    except Exception as e:
        _handle_error(state, "api_publishing", str(e))

    return state
