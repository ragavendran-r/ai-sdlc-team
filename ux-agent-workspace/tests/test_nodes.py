"""Unit tests for UX Agent workflow nodes."""

import pytest
from team_contracts.schemas import UserStory, Priority, Complexity
from ux_agent_workspace.agents.state import UXWorkflowState
from ux_agent_workspace.agents.nodes import (
    story_intake,
    persona_agent,
    user_flow_mapping,
    information_architecture,
    wireframe_brief,
    design_system_compliance,
    accessibility_review,
)


class TestStoryIntake:
    """Test story_intake node."""

    def test_filters_ux_relevant_stories(self):
        """Test that story_intake filters UX-relevant stories."""
        state = UXWorkflowState()
        state.input_stories = [
            UserStory(
                id="US-001",
                title="User login",
                description="Login flow",
                user_role="Customer",
                user_goal="log in",
                business_value="auth",
                acceptance_criteria=["Works"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            ),
            UserStory(
                id="US-002",
                title="Database optimization",
                description="Backend optimization",
                user_role="Engineer",
                user_goal="optimize",
                business_value="perf",
                acceptance_criteria=["Fast"],
                priority=Priority.MEDIUM,
                estimated_complexity=Complexity.L,
                created_by="po-agent",
            ),
        ]

        result = story_intake(state)

        assert len(result.ux_relevant_stories) >= 1
        assert "US-001" in [s.id for s in result.ux_relevant_stories]

    def test_handles_empty_input(self):
        """Test story_intake handles empty input."""
        state = UXWorkflowState()
        result = story_intake(state)
        assert result is not None


class TestPersonaAgent:
    """Test persona_agent node."""

    def test_generates_personas(self):
        """Test that persona_agent generates personas."""
        state = UXWorkflowState()
        state.ux_relevant_stories = [
            UserStory(
                id="US-001",
                title="User login",
                description="Login",
                user_role="Customer",
                user_goal="log in",
                business_value="auth",
                acceptance_criteria=["Works"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            ),
        ]

        result = persona_agent(state)

        assert len(result.personas) > 0
        assert result.personas[0].role == "Customer"

    def test_personas_have_required_fields(self):
        """Test that generated personas have all required fields."""
        state = UXWorkflowState()
        state.ux_relevant_stories = [
            UserStory(
                id="US-001",
                title="User login",
                description="Login",
                user_role="Admin",
                user_goal="manage",
                business_value="control",
                acceptance_criteria=["Works"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            ),
        ]

        result = persona_agent(state)

        for persona in result.personas:
            assert persona.id is not None
            assert persona.name is not None
            assert persona.role is not None
            assert len(persona.goals) > 0


class TestUserFlowMapping:
    """Test user_flow_mapping node."""

    def test_creates_user_flows(self):
        """Test that user_flow_mapping creates flows."""
        state = UXWorkflowState()
        state.ux_relevant_stories = [
            UserStory(
                id="US-001",
                title="Login",
                description="Login flow",
                user_role="Customer",
                user_goal="log in",
                business_value="auth",
                acceptance_criteria=["Works"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            ),
        ]
        state.personas = persona_agent(state).personas

        result = user_flow_mapping(state)

        assert len(result.user_flows) > 0
        assert result.user_flows[0].user_story_id == "US-001"

    def test_flows_have_steps(self):
        """Test that flows have steps."""
        state = UXWorkflowState()
        state.ux_relevant_stories = [
            UserStory(
                id="US-001",
                title="Login",
                description="Login",
                user_role="Customer",
                user_goal="log in",
                business_value="auth",
                acceptance_criteria=["Works"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            ),
        ]
        state.personas = persona_agent(state).personas

        result = user_flow_mapping(state)

        for flow in result.user_flows:
            assert len(flow.steps) > 0


class TestInformationArchitecture:
    """Test information_architecture node."""

    def test_creates_ia_structure(self):
        """Test that IA node creates structure."""
        state = UXWorkflowState()
        state.user_flows = []

        result = information_architecture(state)

        assert result.ia_structure is not None
        assert len(result.ia_structure.root_nodes) > 0
        assert len(result.ia_structure.nodes) > 0


class TestWireframeBrief:
    """Test wireframe_brief node."""

    def test_generates_briefs(self):
        """Test that wireframe_brief generates briefs."""
        state = UXWorkflowState()
        # Setup prerequisite state
        state.ux_relevant_stories = [
            UserStory(
                id="US-001",
                title="Login",
                description="Login",
                user_role="Customer",
                user_goal="log in",
                business_value="auth",
                acceptance_criteria=["Works"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            ),
        ]
        state.personas = persona_agent(state).personas
        state.user_flows = user_flow_mapping(state).user_flows

        result = wireframe_brief(state)

        assert len(result.wireframe_briefs) > 0
        assert len(result.wireframe_briefs[0].components) > 0

    def test_briefs_have_interactions(self):
        """Test that briefs have interaction patterns."""
        state = UXWorkflowState()
        state.ux_relevant_stories = [
            UserStory(
                id="US-001",
                title="Login",
                description="Login",
                user_role="Customer",
                user_goal="log in",
                business_value="auth",
                acceptance_criteria=["Works"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            ),
        ]
        state.personas = persona_agent(state).personas
        state.user_flows = user_flow_mapping(state).user_flows

        result = wireframe_brief(state)

        for brief in result.wireframe_briefs:
            assert brief.interactions is not None


class TestDesignSystemCompliance:
    """Test design_system_compliance node."""

    def test_generates_compliance_report(self):
        """Test that compliance node generates report."""
        state = UXWorkflowState()
        state.ux_relevant_stories = [
            UserStory(
                id="US-001",
                title="Login",
                description="Login",
                user_role="Customer",
                user_goal="log in",
                business_value="auth",
                acceptance_criteria=["Works"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            ),
        ]
        state.personas = persona_agent(state).personas
        state.user_flows = user_flow_mapping(state).user_flows
        state.wireframe_briefs = wireframe_brief(state).wireframe_briefs

        result = design_system_compliance(state)

        assert result.compliance_report is not None
        assert result.compliance_report.total_briefs_checked > 0


class TestAccessibilityReview:
    """Test accessibility_review node."""

    def test_identifies_a11y_issues(self):
        """Test that accessibility review finds issues."""
        state = UXWorkflowState()
        state.ux_relevant_stories = [
            UserStory(
                id="US-001",
                title="Login",
                description="Login",
                user_role="Customer",
                user_goal="log in",
                business_value="auth",
                acceptance_criteria=["Works"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            ),
        ]
        state.personas = persona_agent(state).personas
        state.user_flows = user_flow_mapping(state).user_flows
        state.wireframe_briefs = wireframe_brief(state).wireframe_briefs

        result = accessibility_review(state)

        assert result.a11y_flags is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
