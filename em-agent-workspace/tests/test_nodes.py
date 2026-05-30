"""Unit tests for EM Agent workflow nodes."""

import pytest
from datetime import datetime, timedelta
from team_contracts.schemas import (
    UserStory,
    Priority,
    Complexity,
    CapacityReport,
    RiskFlag,
    RiskType,
    RiskSeverity,
    DefinitionOfDone,
    DoDItem,
    DoDCategory,
    SprintStatus,
    SprintPhase,
    Blocker,
    BlockerType,
)
from em_agent_workspace.agents.state import EMWorkflowState
from em_agent_workspace.agents.nodes import (
    backlog_intake,
    dependency_mapping,
    capacity_analysis,
    risk_assessment,
    sprint_composition,
    definition_of_done,
    blocker_detection,
)


class TestBacklogIntake:
    """Test backlog_intake node."""

    def test_backlog_intake_validates_stories(self):
        """Test that backlog_intake validates incoming stories."""
        state = EMWorkflowState()

        # Create sample stories
        state.input_stories = [
            UserStory(
                id="US-001",
                title="User login with email and password",
                description="Allow users to authenticate using email and password",
                user_role="Customer",
                user_goal="log in to my account",
                business_value="enables personalization",
                acceptance_criteria=["Form displays", "Valid login succeeds"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            ),
        ]

        result = backlog_intake(state)

        assert result.validated_stories is not None
        assert len(result.validated_stories) > 0

    def test_backlog_intake_handles_empty_input(self):
        """Test backlog_intake handles empty input gracefully."""
        state = EMWorkflowState()
        state.input_stories = []

        result = backlog_intake(state)

        assert result is not None
        assert hasattr(result, "validated_stories")


class TestDependencyMapping:
    """Test dependency_mapping node."""

    def test_dependency_mapping_builds_graph(self):
        """Test that dependency_mapping builds a dependency graph."""
        state = EMWorkflowState()

        state.validated_stories = [
            UserStory(
                id="US-001",
                title="Login",
                description="User login",
                user_role="Customer",
                user_goal="log in",
                business_value="authentication",
                acceptance_criteria=["Works"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            ),
            UserStory(
                id="US-002",
                title="OAuth",
                description="Social login",
                user_role="Customer",
                user_goal="log in with OAuth",
                business_value="faster signup",
                acceptance_criteria=["Works"],
                priority=Priority.MEDIUM,
                estimated_complexity=Complexity.L,
                depends_on=["US-001"],
                created_by="po-agent",
            ),
        ]

        result = dependency_mapping(state)

        assert result.dependency_graph is not None
        assert "US-001" in result.dependency_graph
        assert "US-002" in result.dependency_graph
        assert "US-001" in result.dependency_graph.get("US-002", [])

    def test_dependency_mapping_detects_circular_deps(self):
        """Test that dependency_mapping detects circular dependencies."""
        state = EMWorkflowState()

        # Create circular dependency: US-001 depends on US-002, US-002 depends on US-001
        state.validated_stories = [
            UserStory(
                id="US-001",
                title="Feature A",
                description="Feature A",
                user_role="User",
                user_goal="goal",
                business_value="value",
                acceptance_criteria=["Done"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                depends_on=["US-002"],
                created_by="po-agent",
            ),
            UserStory(
                id="US-002",
                title="Feature B",
                description="Feature B",
                user_role="User",
                user_goal="goal",
                business_value="value",
                acceptance_criteria=["Done"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                depends_on=["US-001"],
                created_by="po-agent",
            ),
        ]

        result = dependency_mapping(state)

        # Should detect circular dependency
        assert result.dependency_graph is not None


class TestCapacityAnalysis:
    """Test capacity_analysis node."""

    def test_capacity_analysis_creates_report(self):
        """Test that capacity_analysis creates a capacity report."""
        state = EMWorkflowState()

        result = capacity_analysis(state)

        assert result.capacity_report is not None
        assert result.capacity_report.team_size > 0
        assert result.capacity_report.estimated_story_points_capacity > 0

    def test_capacity_report_has_required_fields(self):
        """Test that capacity report has all required fields."""
        state = EMWorkflowState()

        result = capacity_analysis(state)

        report = result.capacity_report
        assert report.id is not None
        assert report.team_velocity > 0
        assert report.usable_capacity_hours > 0
        assert report.created_by == "em-agent"


class TestRiskAssessment:
    """Test risk_assessment node."""

    def test_risk_assessment_identifies_complex_stories(self):
        """Test that risk_assessment identifies complex stories."""
        state = EMWorkflowState()

        state.validated_stories = [
            UserStory(
                id="US-001",
                title="Complex Feature",
                description="A complex feature",
                user_role="User",
                user_goal="accomplish something complex",
                business_value="high value",
                acceptance_criteria=["Done"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.XL,  # Very complex
                created_by="po-agent",
            ),
        ]
        state.dependency_graph = {"US-001": []}

        result = risk_assessment(state)

        assert result.risk_flags is not None
        assert len(result.risk_flags) > 0

    def test_risk_assessment_identifies_dependencies(self):
        """Test that risk_assessment identifies dependency risks."""
        state = EMWorkflowState()

        state.validated_stories = [
            UserStory(
                id="US-001",
                title="Feature",
                description="Feature",
                user_role="User",
                user_goal="goal",
                business_value="value",
                acceptance_criteria=["Done"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                depends_on=["US-002"],  # Has dependency
                created_by="po-agent",
            ),
        ]
        state.dependency_graph = {"US-001": ["US-002"]}

        result = risk_assessment(state)

        assert result.risk_flags is not None
        # Should have flagged the dependency
        assert any(flag.risk_type == RiskType.DEPENDENCY for flag in result.risk_flags)

    def test_risk_summary_counts_by_type(self):
        """Test that risk summary counts risks by type."""
        state = EMWorkflowState()

        state.validated_stories = [
            UserStory(
                id="US-001",
                title="Complex with dependency",
                description="Complex story with dependencies",
                user_role="User",
                user_goal="goal",
                business_value="value",
                acceptance_criteria=["Done"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.XL,
                depends_on=["US-002"],
                created_by="po-agent",
            ),
        ]
        state.dependency_graph = {"US-001": ["US-002"]}

        result = risk_assessment(state)

        assert result.risk_summary is not None
        assert len(result.risk_summary) > 0


class TestSprintComposition:
    """Test sprint_composition node."""

    def test_sprint_composition_creates_sprint_plan(self):
        """Test that sprint_composition creates a sprint plan."""
        state = EMWorkflowState()

        state.validated_stories = [
            UserStory(
                id="US-001",
                title="Login",
                description="User login",
                user_role="Customer",
                user_goal="log in",
                business_value="auth",
                acceptance_criteria=["Works"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            ),
        ]
        state.dependency_graph = {"US-001": []}
        state.capacity_report = CapacityReport(
            id="CAP-001",
            team_size=5,
            available_hours_per_day=6,
            team_velocity=35,
            total_available_hours=420,
            usable_capacity_hours=380,
            estimated_story_points_capacity=35,
            created_by="em-agent",
        )
        state.risk_flags = []

        result = sprint_composition(state)

        assert result.draft_sprint is not None
        assert result.draft_sprint.sprint.id is not None
        assert len(result.draft_sprint.sprint.tasks) > 0

    def test_sprint_respects_capacity(self):
        """Test that sprint composition respects team capacity."""
        state = EMWorkflowState()

        # Create more stories than capacity allows
        state.validated_stories = [
            UserStory(
                id=f"US-{i:03d}",
                title=f"Story {i}",
                description=f"Story {i}",
                user_role="User",
                user_goal="goal",
                business_value="value",
                acceptance_criteria=["Done"],
                priority=Priority.HIGH,
                estimated_complexity=Complexity.M,
                created_by="po-agent",
            )
            for i in range(20)
        ]
        state.dependency_graph = {s.id: [] for s in state.validated_stories}
        state.capacity_report = CapacityReport(
            id="CAP-001",
            team_size=5,
            available_hours_per_day=6,
            team_velocity=35,
            total_available_hours=420,
            usable_capacity_hours=380,
            estimated_story_points_capacity=5,  # Only 5 points capacity
            created_by="em-agent",
        )
        state.risk_flags = []

        result = sprint_composition(state)

        assert result.draft_sprint is not None
        # Sprint should have limited stories due to capacity
        assert len(result.draft_sprint.sprint.tasks) <= 5


class TestDefinitionOfDone:
    """Test definition_of_done node."""

    def test_dod_creates_checklist(self):
        """Test that definition_of_done creates a checklist."""
        state = EMWorkflowState()

        state.draft_sprint = sprint_composition(EMWorkflowState(
            validated_stories=[
                UserStory(
                    id="US-001",
                    title="Feature",
                    description="Feature",
                    user_role="User",
                    user_goal="goal",
                    business_value="value",
                    acceptance_criteria=["Done"],
                    priority=Priority.HIGH,
                    estimated_complexity=Complexity.M,
                    created_by="po-agent",
                ),
            ],
            dependency_graph={"US-001": []},
            capacity_report=CapacityReport(
                id="CAP-001",
                team_size=5,
                available_hours_per_day=6,
                team_velocity=35,
                total_available_hours=420,
                usable_capacity_hours=380,
                estimated_story_points_capacity=35,
                created_by="em-agent",
            ),
            risk_flags=[],
        )).draft_sprint

        result = definition_of_done(state)

        assert result.dod_checklist is not None
        assert len(result.dod_checklist.items) > 0

    def test_dod_items_have_mandatory_fields(self):
        """Test that DoD items have required fields."""
        state = EMWorkflowState()

        state.draft_sprint = sprint_composition(EMWorkflowState(
            validated_stories=[
                UserStory(
                    id="US-001",
                    title="Feature",
                    description="Feature",
                    user_role="User",
                    user_goal="goal",
                    business_value="value",
                    acceptance_criteria=["Done"],
                    priority=Priority.HIGH,
                    estimated_complexity=Complexity.M,
                    created_by="po-agent",
                ),
            ],
            dependency_graph={"US-001": []},
            capacity_report=CapacityReport(
                id="CAP-001",
                team_size=5,
                available_hours_per_day=6,
                team_velocity=35,
                total_available_hours=420,
                usable_capacity_hours=380,
                estimated_story_points_capacity=35,
                created_by="em-agent",
            ),
            risk_flags=[],
        )).draft_sprint

        result = definition_of_done(state)

        for item in result.dod_checklist.items:
            assert item.id is not None
            assert item.category is not None
            assert item.description is not None
            assert item.created_by == "em-agent"


class TestBlockerDetection:
    """Test blocker_detection node."""

    def test_blocker_detection_identifies_blocked_stories(self):
        """Test that blocker_detection identifies blocked stories."""
        state = EMWorkflowState()
        state.sprint_id = "SPRINT-1"

        # Create sprint status with blocked stories
        state.current_sprint_status = SprintStatus(
            id="STATUS-001",
            sprint_id="SPRINT-1",
            phase=SprintPhase.IN_PROGRESS,
            total_stories=10,
            stories_blocked=2,  # 2 stories blocked
            updated_by="em-agent",
        )

        result = blocker_detection(state)

        assert result.blockers is not None
        assert len(result.blockers) > 0

    def test_blocker_has_required_fields(self):
        """Test that blockers have all required fields."""
        state = EMWorkflowState()
        state.sprint_id = "SPRINT-1"

        state.current_sprint_status = SprintStatus(
            id="STATUS-001",
            sprint_id="SPRINT-1",
            phase=SprintPhase.IN_PROGRESS,
            total_stories=10,
            stories_blocked=1,
            updated_by="em-agent",
        )

        result = blocker_detection(state)

        for blocker in result.blockers:
            assert blocker.id is not None
            assert blocker.story_id is not None
            assert blocker.blocker_type is not None
            assert blocker.created_by == "em-agent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
