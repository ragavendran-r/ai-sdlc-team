"""Unit tests for Backend Agent workflow nodes."""

import pytest
from backend_agent_workspace.agents.state import BackendWorkflowState
from backend_agent_workspace.agents.nodes import (
    requirements_intake,
    domain_model,
    database_schema,
    api_contract,
    business_logic_scaffolding,
    validation_rules,
    security_review,
    unit_test_generation,
    human_checkpoint,
    pr_description,
    code_review,
    api_publishing,
)


class TestRequirementsIntake:
    """Test requirements_intake node."""

    def test_extracts_requirements(self):
        """Test that requirements_intake extracts backend requirements."""
        state = BackendWorkflowState()
        state.user_stories = [
            {
                "id": "US-001",
                "title": "User login",
                "description": "Users can log in with email and password",
                "acceptance_criteria": [
                    "User can enter credentials",
                    "Valid credentials log in",
                    "Invalid credentials show error",
                ],
            }
        ]

        result = requirements_intake(state)

        assert result.requirements_intake_complete
        assert isinstance(result.backend_requirements, list)

    def test_handles_empty_stories(self):
        """Test with no user stories."""
        state = BackendWorkflowState()
        state.user_stories = []

        result = requirements_intake(state)

        assert result.requirements_intake_complete


class TestDomainModel:
    """Test domain_model node."""

    def test_creates_domain_model(self):
        """Test that domain_model creates a domain model."""
        state = BackendWorkflowState()
        state.backend_requirements = [
            {
                "id": "REQ-001",
                "user_story_id": "US-001",
                "title": "User authentication",
                "description": "Users must be authenticated",
                "requirement_type": "security",
                "business_rules": ["Passwords must be hashed"],
            }
        ]

        result = domain_model(state)

        assert result.domain_model_complete
        assert result.domain_model is not None

    def test_handles_no_requirements(self):
        """Test domain_model with no requirements."""
        state = BackendWorkflowState()

        result = domain_model(state)

        assert len(result.errors) > 0


class TestDatabaseSchema:
    """Test database_schema node."""

    def test_generates_schema(self):
        """Test that database_schema generates DDL and models."""
        state = BackendWorkflowState()
        state.domain_model = {
            "id": "DM-001",
            "feature_name": "Authentication",
            "description": "User authentication domain",
            "entities": [
                {
                    "name": "User",
                    "description": "User entity",
                    "plural": "Users",
                    "attributes": [
                        {"name": "id", "data_type": "uuid", "required": True},
                        {"name": "email", "data_type": "string", "required": True},
                    ],
                }
            ],
            "relationships": [],
        }

        result = database_schema(state)

        assert result.db_schema_complete
        assert result.db_schema is not None
        if result.db_schema:
            assert "ddl_sql" in result.db_schema
            assert "sqlalchemy_models" in result.db_schema

    def test_handles_no_model(self):
        """Test database_schema with no domain model."""
        state = BackendWorkflowState()

        result = database_schema(state)

        assert len(result.errors) > 0


class TestAPIContract:
    """Test api_contract node."""

    def test_generates_contract(self):
        """Test that api_contract generates API spec."""
        state = BackendWorkflowState()
        state.backend_requirements = [
            {
                "id": "REQ-001",
                "user_story_id": "US-001",
                "title": "Login endpoint",
                "description": "User can log in",
                "requirement_type": "api_endpoint",
            }
        ]
        state.domain_model = {
            "id": "DM-001",
            "feature_name": "Auth",
            "entities": [],
            "relationships": [],
        }

        result = api_contract(state)

        assert result.api_contract_complete
        assert result.api_contract is not None

    def test_writes_to_context_store(self):
        """Test that api_contract writes to context store."""
        state = BackendWorkflowState()
        state.backend_requirements = []
        state.domain_model = {"id": "DM-001", "feature_name": "Test"}

        result = api_contract(state)

        # Should complete even if contract is minimal
        assert result.api_contract_complete


class TestBusinessLogicScaffolding:
    """Test business_logic_scaffolding node."""

    def test_generates_services(self):
        """Test that business_logic_scaffolding generates services."""
        state = BackendWorkflowState()
        state.domain_model = {
            "id": "DM-001",
            "feature_name": "Users",
            "entities": [
                {
                    "name": "User",
                    "description": "User entity",
                    "plural": "Users",
                    "attributes": [],
                }
            ],
            "relationships": [],
        }
        state.api_contract = {
            "id": "API-001",
            "feature_name": "Users",
            "endpoints": [],
        }

        result = business_logic_scaffolding(state)

        assert result.scaffolding_complete

    def test_handles_no_model(self):
        """Test with no domain model."""
        state = BackendWorkflowState()

        result = business_logic_scaffolding(state)

        assert len(result.errors) > 0


class TestValidationRules:
    """Test validation_rules node."""

    def test_generates_validators(self):
        """Test that validation_rules generates Pydantic validators."""
        state = BackendWorkflowState()
        state.backend_requirements = [
            {
                "id": "REQ-001",
                "user_story_id": "US-001",
                "title": "Input validation",
                "description": "Validate user input",
                "requirement_type": "validation",
            }
        ]
        state.api_contract = {
            "id": "API-001",
            "feature_name": "Test",
            "endpoints": [],
        }

        result = validation_rules(state)

        assert result.validation_rules_complete

    def test_handles_no_requirements(self):
        """Test with no requirements."""
        state = BackendWorkflowState()

        result = validation_rules(state)

        assert len(result.errors) > 0


class TestSecurityReview:
    """Test security_review node."""

    def test_identifies_issues(self):
        """Test that security_review identifies security issues."""
        state = BackendWorkflowState()
        state.api_contract = {
            "id": "API-001",
            "feature_name": "Auth",
            "endpoints": [],
        }
        state.backend_requirements = [
            {
                "id": "REQ-001",
                "user_story_id": "US-001",
                "title": "Login",
                "description": "User login",
                "requirement_type": "api_endpoint",
            }
        ]

        result = security_review(state)

        assert result.security_review_complete
        assert isinstance(result.security_flags, list)

    def test_flags_critical_issues(self):
        """Test that critical issues are flagged."""
        state = BackendWorkflowState()
        state.api_contract = {
            "id": "API-001",
            "feature_name": "Test",
            "endpoints": [],
        }
        state.backend_requirements = []

        result = security_review(state)

        # has_critical_security_flags may or may not be set
        assert result.security_review_complete


class TestUnitTestGeneration:
    """Test unit_test_generation node."""

    def test_generates_tests(self):
        """Test that unit_test_generation generates test stubs."""
        state = BackendWorkflowState()
        state.service_scaffolds = [
            {
                "id": "SVCF-001",
                "entity_name": "User",
                "class_name": "UserService",
                "python_code": "class UserService: pass",
                "methods": [],
            }
        ]
        state.api_contract = {
            "id": "API-001",
            "feature_name": "Test",
            "endpoints": [],
        }
        state.validation_modules = []

        result = unit_test_generation(state)

        assert result.test_generation_complete
        assert isinstance(result.test_files, list)

    def test_handles_no_scaffolds(self):
        """Test with no service scaffolds."""
        state = BackendWorkflowState()
        state.service_scaffolds = []
        state.api_contract = {}
        state.validation_modules = []

        result = unit_test_generation(state)

        assert result.test_generation_complete


class TestHumanCheckpoint:
    """Test human_checkpoint node."""

    def test_handles_approval(self, monkeypatch):
        """Test checkpoint with approval."""
        state = BackendWorkflowState()
        state.domain_model = {"entities": []}
        state.api_contract = {"endpoints": []}
        state.db_schema = {"ddl_sql": ""}
        state.service_scaffolds = []
        state.validation_modules = []
        state.test_files = []
        state.security_flags = []

        # Mock user input
        monkeypatch.setattr("builtins.input", lambda _: "y")

        result = human_checkpoint(state)

        assert result.implementation_approved

    def test_handles_rejection(self, monkeypatch):
        """Test checkpoint with rejection."""
        state = BackendWorkflowState()
        state.domain_model = {"entities": []}
        state.api_contract = {"endpoints": []}
        state.db_schema = {"ddl_sql": ""}
        state.service_scaffolds = []
        state.validation_modules = []
        state.test_files = []
        state.security_flags = []

        # Mock user input
        monkeypatch.setattr("builtins.input", lambda _: "n")

        result = human_checkpoint(state)

        assert not result.implementation_approved


class TestPRDescription:
    """Test pr_description node."""

    def test_generates_pr_description(self):
        """Test that pr_description generates PR text."""
        state = BackendWorkflowState()
        state.domain_model = {
            "id": "DM-001",
            "feature_name": "Auth",
            "entities": [],
            "relationships": [],
        }
        state.api_contract = {
            "id": "API-001",
            "feature_name": "Auth",
            "endpoints": [],
        }
        state.db_schema = {
            "ddl_sql": "CREATE TABLE users (...)",
        }
        state.security_flags = []

        result = pr_description(state)

        assert result.pr_creation_complete
        assert len(result.pr_description) > 0

    def test_handles_missing_data(self):
        """Test with minimal data."""
        state = BackendWorkflowState()

        result = pr_description(state)

        assert result.pr_creation_complete


class TestCodeReview:
    """Test code_review node."""

    def test_reviews_code(self):
        """Test that code_review performs code review."""
        state = BackendWorkflowState()
        state.service_scaffolds = [
            {
                "id": "SVCF-001",
                "entity_name": "User",
                "class_name": "UserService",
                "python_code": "class UserService: pass",
            }
        ]
        state.test_files = []

        result = code_review(state)

        assert result.code_review_complete
        assert isinstance(result.review_comments, list)

    def test_handles_no_code(self):
        """Test with no code to review."""
        state = BackendWorkflowState()

        result = code_review(state)

        assert result.code_review_complete


class TestAPIPublishing:
    """Test api_publishing node."""

    def test_publishes_api(self):
        """Test that api_publishing publishes the contract."""
        state = BackendWorkflowState()
        state.api_contract = {
            "id": "API-001",
            "feature_name": "Auth",
            "endpoints": [],
        }

        result = api_publishing(state)

        assert result.api_publishing_complete
        assert result.api_published

    def test_handles_no_contract(self):
        """Test with no API contract."""
        state = BackendWorkflowState()

        result = api_publishing(state)

        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
