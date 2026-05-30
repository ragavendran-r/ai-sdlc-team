"""Test suite for handoff contract schemas."""

import json
from datetime import datetime, timedelta
from pydantic import ValidationError
import pytest

from user_story import UserStory, Priority, Complexity
from sprint_plan import SprintPlan, Sprint, SprintTask, TaskType, TaskStatus
from ux_handoff import UXHandoff, ComponentSpec, ComponentType, DesignToken, InteractionSpec
from api_contract import APIContract, APIEndpoint, HTTPMethod, HTTPStatus, JSONSchema, ErrorResponse
from design_decision import DesignDecision, DecisionCategory, DecisionStatus, DecisionImpact, Alternative, Consequence


class TestUserStory:
    """Test UserStory schema."""

    def test_valid_user_story(self):
        """Create a valid user story."""
        story = UserStory(
            id="US-001",
            title="User login with email and password",
            description="Users should be able to log in to the application.",
            user_role="Customer",
            user_goal="log in to my account",
            business_value="secure authentication enables personalization",
            acceptance_criteria=[
                "User can enter email and password",
                "Valid credentials log in successfully",
            ],
            priority=Priority.HIGH,
            estimated_complexity=Complexity.M,
            created_by="po-agent",
        )
        assert story.id == "US-001"
        assert story.priority == Priority.HIGH

    def test_user_story_validation(self):
        """Test validation rules."""
        # Title too short
        with pytest.raises(ValidationError):
            UserStory(
                id="US-001",
                title="Bad",  # Too short
                description="Valid description here",
                user_role="Customer",
                user_goal="test",
                business_value="test",
                acceptance_criteria=["Valid"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            )

    def test_user_story_to_markdown(self):
        """Test markdown conversion."""
        story = UserStory(
            id="US-001",
            title="User login with email and password",
            description="Users should be able to log in.",
            user_role="Customer",
            user_goal="log in securely",
            business_value="enables personalization",
            acceptance_criteria=["User can enter credentials", "Valid login succeeds"],
            priority=Priority.HIGH,
            estimated_complexity=Complexity.M,
            created_by="po-agent",
        )
        markdown = story.to_markdown()
        assert "# User Story:" in markdown
        assert "US-001" in markdown
        assert "User can enter credentials" in markdown

    def test_user_story_to_dict(self):
        """Test dict conversion."""
        story = UserStory(
            id="US-001",
            title="User login with email and password",
            description="Users should be able to log in.",
            user_role="Customer",
            user_goal="log in securely",
            business_value="enables personalization",
            acceptance_criteria=["Valid"],
            priority=Priority.HIGH,
            estimated_complexity=Complexity.M,
            created_by="po-agent",
        )
        data = story.to_dict()
        assert data["id"] == "US-001"
        assert data["priority"] == "high"
        assert isinstance(data["created_at"], str)


class TestSprintPlan:
    """Test SprintPlan schema."""

    def test_valid_sprint_plan(self):
        """Create a valid sprint plan."""
        start = datetime.utcnow()
        end = start + timedelta(days=14)

        task = SprintTask(
            id="T-001",
            user_story_id="US-001",
            title="Implement login form",
            description="Build the login form component.",
            assigned_to="frontend-agent",
            task_type=TaskType.FRONTEND,
            estimated_hours=4,
            acceptance_criteria=["Form displays", "Validation works"],
        )

        sprint = Sprint(
            id="S-2.1",
            name="Sprint 2.1",
            start_date=start,
            end_date=end,
            tasks=[task],
            created_by="em-agent",
        )

        plan = SprintPlan(
            sprint=sprint,
            user_stories={"US-001": {"title": "Login"}},
            created_by="em-agent",
        )
        assert plan.sprint.id == "S-2.1"

    def test_sprint_validation(self):
        """Test sprint date validation."""
        start = datetime.utcnow()
        end = start - timedelta(days=1)  # End before start

        task = SprintTask(
            id="T-001",
            user_story_id="US-001",
            title="Task",
            description="Task description",
            assigned_to="agent",
            task_type=TaskType.FRONTEND,
            estimated_hours=4,
            acceptance_criteria=["Criterion"],
        )

        with pytest.raises(ValidationError):
            Sprint(
                id="S-001",
                name="Bad Sprint",
                start_date=start,
                end_date=end,
                tasks=[task],
                created_by="em-agent",
            )

    def test_sprint_summary_methods(self):
        """Test sprint summary methods."""
        start = datetime.utcnow()
        end = start + timedelta(days=14)

        tasks = [
            SprintTask(
                id="T-001",
                user_story_id="US-001",
                title="Task 1",
                description="Description",
                assigned_to="frontend-agent",
                task_type=TaskType.FRONTEND,
                estimated_hours=4,
                acceptance_criteria=["Done"],
            ),
            SprintTask(
                id="T-002",
                user_story_id="US-001",
                title="Task 2",
                description="Description",
                assigned_to="backend-agent",
                task_type=TaskType.BACKEND,
                estimated_hours=6,
                acceptance_criteria=["Done"],
            ),
        ]

        sprint = Sprint(
            id="S-001",
            name="Test Sprint",
            start_date=start,
            end_date=end,
            tasks=tasks,
            created_by="em-agent",
        )

        # Test summary methods
        assert sprint.total_estimated_hours() == 10
        assert len(sprint.get_tasks_by_agent()) == 2
        assert sprint.get_tasks_by_agent()["frontend-agent"][0].id == "T-001"

    def test_sprint_plan_to_dict(self):
        """Test sprint plan dict conversion."""
        start = datetime.utcnow()
        end = start + timedelta(days=14)

        task = SprintTask(
            id="T-001",
            user_story_id="US-001",
            title="Task",
            description="Description",
            assigned_to="agent",
            task_type=TaskType.FRONTEND,
            estimated_hours=4,
            acceptance_criteria=["Done"],
        )

        sprint = Sprint(
            id="S-001",
            name="Sprint",
            start_date=start,
            end_date=end,
            tasks=[task],
            created_by="em-agent",
        )

        plan = SprintPlan(sprint=sprint, created_by="em-agent")
        data = plan.to_dict()

        assert data["sprint"]["id"] == "S-001"
        assert data["sprint"]["summary"]["total_tasks"] == 1
        assert data["sprint"]["summary"]["total_estimated_hours"] == 4


class TestUXHandoff:
    """Test UXHandoff schema."""

    def test_valid_ux_handoff(self):
        """Create a valid UX handoff."""
        component = ComponentSpec(
            id="C-001",
            name="LoginForm",
            component_type=ComponentType.FORM,
            description="Login form component",
            design_notes="Clean minimal design",
            states={"default": "Empty form", "filled": "All fields filled"},
            props={"onSubmit": "Callback"},
        )

        handoff = UXHandoff(
            id="UX-001",
            user_story_id="US-001",
            feature_name="User Login",
            components=[component],
            created_by="ux-agent",
        )
        assert handoff.id == "UX-001"

    def test_component_spec_to_markdown(self):
        """Test component markdown conversion."""
        component = ComponentSpec(
            id="C-001",
            name="LoginForm",
            component_type=ComponentType.FORM,
            description="Login form",
            design_notes="Minimal",
            states={"default": "Empty"},
            props={"onSubmit": "Callback"},
        )
        markdown = component.to_markdown()
        assert "LoginForm" in markdown
        assert "form" in markdown

    def test_ux_handoff_to_dict(self):
        """Test UX handoff dict conversion."""
        component = ComponentSpec(
            id="C-001",
            name="LoginForm",
            component_type=ComponentType.FORM,
            description="Login form",
            design_notes="Minimal",
            states={"default": "Empty"},
        )

        handoff = UXHandoff(
            id="UX-001",
            user_story_id="US-001",
            feature_name="Login",
            components=[component],
            created_by="ux-agent",
        )
        data = handoff.to_dict()
        assert data["id"] == "UX-001"
        assert len(data["components"]) == 1


class TestAPIContract:
    """Test APIContract schema."""

    def test_valid_api_contract(self):
        """Create a valid API contract."""
        endpoint = APIEndpoint(
            id="EP-001",
            method=HTTPMethod.POST,
            path="/api/v1/auth/login",
            summary="Login",
            description="Authenticate user",
            auth_required=False,
            response_schema=JSONSchema(type="object"),
        )

        contract = APIContract(
            id="API-001",
            feature_name="Authentication",
            user_story_id="US-001",
            base_url="https://api.example.com/v1",
            endpoints=[endpoint],
            created_by="backend-agent",
        )
        assert contract.id == "API-001"

    def test_endpoint_path_validation(self):
        """Test endpoint path validation."""
        with pytest.raises(ValidationError):
            APIEndpoint(
                id="EP-001",
                method=HTTPMethod.GET,
                path="no-leading-slash",  # Invalid
                summary="Test",
                description="Test",
                response_schema=JSONSchema(type="object"),
            )

    def test_api_contract_to_markdown(self):
        """Test API contract markdown conversion."""
        endpoint = APIEndpoint(
            id="EP-001",
            method=HTTPMethod.GET,
            path="/api/v1/users",
            summary="Get users",
            description="List all users",
            response_schema=JSONSchema(type="array"),
        )

        contract = APIContract(
            id="API-001",
            feature_name="Users",
            user_story_id="US-001",
            base_url="https://api.example.com/v1",
            endpoints=[endpoint],
            created_by="backend-agent",
        )
        markdown = contract.to_markdown()
        assert "API Contract:" in markdown
        assert "GET /api/v1/users" in markdown


class TestDesignDecision:
    """Test DesignDecision schema."""

    def test_valid_decision(self):
        """Create a valid design decision."""
        decision = DesignDecision(
            id="ADR-001",
            title="Use JWT for authentication",
            category=DecisionCategory.API_DESIGN,
            impact=DecisionImpact.SYSTEM,
            context="Need stateless authentication",
            decision="Use JWT tokens",
            rationale="Scalable and stateless",
            created_by="backend-agent",
        )
        assert decision.id == "ADR-001"

    def test_decision_with_alternatives(self):
        """Create decision with alternatives."""
        alt = Alternative(
            name="Session-based",
            description="Use server-side sessions",
            pros=["Simpler"],
            cons=["Not scalable"],
        )

        decision = DesignDecision(
            id="ADR-001",
            title="Auth method",
            category=DecisionCategory.API_DESIGN,
            impact=DecisionImpact.SYSTEM,
            context="Choose auth method",
            decision="Use JWT",
            rationale="Scalable",
            alternatives=[alt],
            created_by="backend-agent",
        )
        assert len(decision.alternatives) == 1

    def test_decision_with_consequences(self):
        """Create decision with consequences."""
        consequence = Consequence(
            type="scalability",
            description="Stateless tokens allow scaling",
            is_positive=True,
        )

        decision = DesignDecision(
            id="ADR-001",
            title="Auth method",
            category=DecisionCategory.API_DESIGN,
            impact=DecisionImpact.SYSTEM,
            context="Choose auth",
            decision="Use JWT",
            rationale="Scalable",
            consequences=[consequence],
            created_by="backend-agent",
        )

        assert len(decision.get_positive_consequences()) == 1
        assert len(decision.get_negative_consequences()) == 0

    def test_decision_to_markdown(self):
        """Test decision markdown conversion (ADR format)."""
        decision = DesignDecision(
            id="ADR-001",
            title="Use JWT authentication",
            category=DecisionCategory.API_DESIGN,
            impact=DecisionImpact.SYSTEM,
            context="Need authentication",
            decision="Use JWT tokens",
            rationale="Stateless and scalable",
            created_by="backend-agent",
        )
        markdown = decision.to_markdown()
        assert "ADR-001" in markdown
        assert "Context" in markdown
        assert "Decision" in markdown
        assert "Rationale" in markdown


def test_all_schemas_are_serializable():
    """Verify all schemas can be converted to dict and back."""
    # UserStory
    story = UserStory(
        id="US-001",
        title="Test story for serialization",
        description="Testing serialization",
        user_role="Tester",
        user_goal="test",
        business_value="testing",
        acceptance_criteria=["Test passes"],
        priority=Priority.HIGH,
        estimated_complexity=Complexity.M,
        created_by="po-agent",
    )
    story_dict = story.to_dict()
    assert isinstance(story_dict, dict)
    assert json.dumps(story_dict)  # Should be JSON serializable

    # APIContract
    endpoint = APIEndpoint(
        id="EP-001",
        method=HTTPMethod.GET,
        path="/test",
        summary="Test",
        description="Test",
        response_schema=JSONSchema(type="object"),
    )
    contract = APIContract(
        id="API-001",
        feature_name="Test",
        user_story_id="US-001",
        base_url="https://api.test.com",
        endpoints=[endpoint],
        created_by="backend-agent",
    )
    contract_dict = contract.to_dict()
    assert isinstance(contract_dict, dict)
    assert json.dumps(contract_dict)  # Should be JSON serializable

    # DesignDecision
    decision = DesignDecision(
        id="ADR-001",
        title="Test decision",
        category=DecisionCategory.ARCHITECTURE,
        impact=DecisionImpact.LOCAL,
        context="Test",
        decision="Test",
        rationale="Test",
        created_by="backend-agent",
    )
    decision_dict = decision.to_dict()
    assert isinstance(decision_dict, dict)
    assert json.dumps(decision_dict)  # Should be JSON serializable


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
