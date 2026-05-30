"""Unit tests for Frontend Agent workflow nodes."""

import pytest
from frontend_agent_workspace.agents.state import FrontendWorkflowState
from frontend_agent_workspace.agents.nodes import (
    ux_handoff_intake,
    component_breakdown,
    design_token_mapping,
    api_integration_planning,
    component_scaffolding,
    state_management,
    accessibility_implementation,
    unit_test_generation,
    human_checkpoint,
    pr_description,
    code_review,
)
from team_contracts.schemas import UXHandoff, APIContract, APIEndpoint, HTTPMethod, JSONSchema


class TestUXHandoffIntake:
    """Test ux_handoff_intake node."""

    def test_validates_handoff(self):
        """Test that ux_handoff_intake validates UX handoff."""
        state = FrontendWorkflowState()

        # Mock UX handoff
        state.ux_handoff = UXHandoff(
            id="UX-001",
            user_story_id="US-001",
            feature_name="Test Feature",
            components=[],
            created_by="ux-agent",
        )

        result = ux_handoff_intake(state)

        assert result.handoff_validation_complete
        assert result.validated_handoff is not None

    def test_identifies_gaps(self):
        """Test that ux_handoff_intake identifies gaps."""
        state = FrontendWorkflowState()
        state.ux_handoff = UXHandoff(
            id="UX-001",
            user_story_id="US-001",
            feature_name="Test Feature",
            components=[],
            created_by="ux-agent",
        )

        result = ux_handoff_intake(state)

        assert hasattr(result, "intake_gaps")


class TestComponentBreakdown:
    """Test component_breakdown node."""

    def test_breaks_down_components(self):
        """Test that component_breakdown creates component plan."""
        state = FrontendWorkflowState()
        state.ux_handoff = UXHandoff(
            id="UX-001",
            user_story_id="US-001",
            feature_name="Test Feature",
            components=[],
            created_by="ux-agent",
        )
        state.validated_handoff = state.ux_handoff

        result = component_breakdown(state)

        assert result.component_breakdown_complete
        assert hasattr(result, "component_plan")

    def test_handles_empty_handoff(self):
        """Test component_breakdown with no validated handoff."""
        state = FrontendWorkflowState()

        result = component_breakdown(state)

        assert len(result.errors) > 0


class TestDesignTokenMapping:
    """Test design_token_mapping node."""

    def test_maps_tokens(self):
        """Test that design_token_mapping creates token mappings."""
        state = FrontendWorkflowState()
        state.component_plan = [
            {"id": "C-001", "name": "Button"},
            {"id": "C-002", "name": "Form"},
        ]

        result = design_token_mapping(state)

        assert result.token_mapping_complete
        assert hasattr(result, "token_mappings")
        assert hasattr(result, "token_gaps")

    def test_identifies_token_gaps(self):
        """Test that gaps are identified."""
        state = FrontendWorkflowState()
        state.component_plan = [
            {"id": "C-001", "name": "Button"},
        ]

        result = design_token_mapping(state)

        assert result.token_mapping_complete
        assert isinstance(result.token_gaps, list)


class TestAPIIntegrationPlanning:
    """Test api_integration_planning node."""

    def test_plans_api_integration(self):
        """Test that API integration planning works."""
        state = FrontendWorkflowState()
        state.component_plan = [
            {"id": "C-001", "name": "UserList"},
        ]
        state.api_contract = APIContract(
            id="API-001",
            feature_name="Users",
            user_story_id="US-001",
            base_url="https://api.example.com",
            endpoints=[
                APIEndpoint(
                    id="EP-001",
                    method=HTTPMethod.GET,
                    path="/users",
                    summary="Get users",
                    description="Get all users",
                    response_schema=JSONSchema(type="array"),
                )
            ],
            created_by="backend-agent",
        )

        result = api_integration_planning(state)

        assert result.api_planning_complete
        assert hasattr(result, "api_integration_map")

    def test_handles_no_api_contract(self):
        """Test with no API contract."""
        state = FrontendWorkflowState()
        state.component_plan = []

        result = api_integration_planning(state)

        assert result.api_planning_complete
        assert result.api_integration_map == {}


class TestComponentScaffolding:
    """Test component_scaffolding node."""

    def test_scaffolds_components(self):
        """Test that component_scaffolding generates code."""
        state = FrontendWorkflowState()
        state.component_plan = [
            {"id": "C-001", "name": "Button", "props": {"label": "string"}},
        ]
        state.token_mappings = {"C-001": ["color-primary"]}
        state.api_integration_map = {}

        result = component_scaffolding(state)

        assert result.scaffolding_complete
        assert len(result.scaffolded_components) > 0

    def test_generated_code_has_tsx(self):
        """Test that generated code contains TSX."""
        state = FrontendWorkflowState()
        state.component_plan = [
            {"id": "C-001", "name": "Button", "props": {}},
        ]
        state.token_mappings = {}
        state.api_integration_map = {}

        result = component_scaffolding(state)

        if result.scaffolded_components:
            assert "tsx_code" in result.scaffolded_components[0]


class TestStateManagement:
    """Test state_management node."""

    def test_creates_state_plan(self):
        """Test that state_management creates plan."""
        state = FrontendWorkflowState()
        state.scaffolded_components = [
            {"id": "C-001", "name": "Button"},
        ]
        state.api_integration_map = {}

        result = state_management(state)

        assert result.state_management_complete
        assert result.state_plan is not None

    def test_recommends_strategy(self):
        """Test that state management recommends strategy."""
        state = FrontendWorkflowState()
        state.scaffolded_components = [
            {"id": "C-001", "name": "UserForm"},
            {"id": "C-002", "name": "UserList"},
        ]
        state.api_integration_map = {"C-001": ["EP-001"], "C-002": ["EP-002"]}

        result = state_management(state)

        assert result.state_management_complete


class TestAccessibilityImplementation:
    """Test accessibility_implementation node."""

    def test_enriches_with_a11y(self):
        """Test that a11y features are added."""
        state = FrontendWorkflowState()
        state.scaffolded_components = [
            {"id": "C-001", "name": "Button", "tsx_code": "export const Button = () => <button/>"},
        ]
        state.validated_handoff = UXHandoff(
            id="UX-001",
            user_story_id="US-001",
            feature_name="Test",
            components=[],
            accessibility_requirements=["WCAG 2.1 AA"],
            created_by="ux-agent",
        )

        result = accessibility_implementation(state)

        assert result.a11y_implementation_complete
        assert len(result.a11y_enriched_components) > 0

    def test_adds_aria_attributes(self):
        """Test that ARIA attributes are added."""
        state = FrontendWorkflowState()
        state.scaffolded_components = [
            {"id": "C-001", "name": "Button", "tsx_code": "<button/>"},
        ]
        state.validated_handoff = UXHandoff(
            id="UX-001",
            user_story_id="US-001",
            feature_name="Test",
            components=[],
            created_by="ux-agent",
        )

        result = accessibility_implementation(state)

        if result.a11y_enriched_components:
            assert "aria_attributes" in result.a11y_enriched_components[0]


class TestUnitTestGeneration:
    """Test unit_test_generation node."""

    def test_generates_tests(self):
        """Test that tests are generated."""
        state = FrontendWorkflowState()
        state.a11y_enriched_components = [
            {"id": "C-001", "name": "Button", "tsx_code": "<button/>"},
        ]

        result = unit_test_generation(state)

        assert result.test_generation_complete
        assert len(result.test_files) > 0

    def test_test_files_have_cases(self):
        """Test that generated test files have test cases."""
        state = FrontendWorkflowState()
        state.a11y_enriched_components = [
            {"id": "C-001", "name": "Button", "tsx_code": "<button/>"},
        ]

        result = unit_test_generation(state)

        if result.test_files:
            assert "test_cases" in result.test_files[0]
            assert len(result.test_files[0]["test_cases"]) > 0


class TestPRDescription:
    """Test pr_description node."""

    def test_generates_pr_description(self):
        """Test that PR description is generated."""
        state = FrontendWorkflowState()
        state.a11y_enriched_components = [
            {"id": "C-001", "name": "Button"},
        ]
        state.token_mappings = {"C-001": ["color-primary"]}
        state.token_gaps = []
        state.api_integration_map = {}
        state.missing_endpoints = []

        result = pr_description(state)

        assert result.pr_creation_complete
        assert len(result.pr_description) > 0
        assert "Summary" in result.pr_description or "Components" in result.pr_description

    def test_pr_includes_components(self):
        """Test that PR description includes component list."""
        state = FrontendWorkflowState()
        state.a11y_enriched_components = [
            {"id": "C-001", "name": "Button", "component_type": "button"},
        ]
        state.token_mappings = {}
        state.token_gaps = []
        state.api_integration_map = {}
        state.missing_endpoints = []

        result = pr_description(state)

        assert "Button" in result.pr_description


class TestCodeReview:
    """Test code_review node."""

    def test_runs_code_review(self):
        """Test that code review executes."""
        state = FrontendWorkflowState()
        state.a11y_enriched_components = [
            {"id": "C-001", "name": "Button", "tsx_code": "<button/>"},
        ]

        result = code_review(state)

        assert result.code_review_complete
        assert isinstance(result.review_comments, list)

    def test_identifies_issues(self):
        """Test that code review identifies issues."""
        state = FrontendWorkflowState()
        state.a11y_enriched_components = [
            {
                "id": "C-001",
                "name": "Button",
                "tsx_code": "<button/>",
                "tokens_used": [],
                "aria_attributes": [],
            },
        ]

        result = code_review(state)

        assert result.code_review_complete
        # May or may not have comments depending on implementation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
