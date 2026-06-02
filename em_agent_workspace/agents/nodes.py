"""Agent nodes for EM Agent workflow."""

import os
from datetime import datetime, timedelta
from langchain_anthropic import ChatAnthropic
from .state import EMWorkflowState
from .tools import ContextStoreTool, JiraIntegrationTool
from team_contracts.schemas import (
    UserStory,
    SprintPlan,
    Sprint,
    SprintTask,
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

llm = ChatAnthropic(
    model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
    temperature=float(os.getenv("CLAUDE_TEMPERATURE", "0.7")),
    max_tokens=int(os.getenv("CLAUDE_MAX_TOKENS", "2048")),
)


# ============================================================================
# NODE 1: BACKLOG INTAKE
# ============================================================================


def backlog_intake(state: EMWorkflowState) -> EMWorkflowState:
    """
    Validate incoming stories are complete and well-formed.

    Ensures all stories have required fields and meet quality standards.
    """
    state.current_agent = "backlog_intake"

    # Use tool to read stories from context store
    tool_result = ContextStoreTool.read_user_stories()

    if not tool_result.success:
        state.add_error(f"Failed to read stories: {tool_result.error}")
        return state

    # Validate each story
    validation_prompt = """Review these user stories for completeness:
- All required fields present?
- Title and description clear and specific?
- Acceptance criteria testable?
- Priority and complexity estimated?

Flag any stories that are incomplete or unclear."""

    llm.invoke(validation_prompt)

    # Simulate validated stories
    if state.input_stories:
        state.validated_stories = state.input_stories
    else:
        # For demo, create sample stories
        state.validated_stories = [
            UserStory(
                id="US-001",
                title="User login with email and password",
                description="Allow users to authenticate using email and password",
                user_role="Customer",
                user_goal="log in to my account",
                business_value="enables personalization",
                acceptance_criteria=["Form displays", "Valid login succeeds"],
                priority="high",
                estimated_complexity="m",
                created_by="po-agent",
            ),
            UserStory(
                id="US-002",
                title="OAuth social login",
                description="Support OAuth login with Google and GitHub",
                user_role="Customer",
                user_goal="log in with social account",
                business_value="faster onboarding",
                acceptance_criteria=["Google OAuth works", "GitHub OAuth works"],
                priority="medium",
                estimated_complexity="l",
                depends_on=["US-001"],
                created_by="po-agent",
            ),
        ]

    state.add_message("backlog_intake", f"Validated {len(state.validated_stories)} stories")
    return state


# ============================================================================
# NODE 2: DEPENDENCY MAPPING
# ============================================================================


def dependency_mapping(state: EMWorkflowState) -> EMWorkflowState:
    """
    Build dependency graph between stories.

    Identifies which stories block other stories.
    """
    state.current_agent = "dependency_mapping"

    # Build dependency graph
    graph = {}
    circular_deps = []

    for story in state.validated_stories:
        graph[story.id] = story.depends_on or []

    # Check for circular dependencies
    def has_circular_dep(story_id: str, visited: set = None) -> bool:
        if visited is None:
            visited = set()

        if story_id in visited:
            return True

        visited.add(story_id)

        for dep_id in graph.get(story_id, []):
            if has_circular_dep(dep_id, visited.copy()):
                circular_deps.append((story_id, dep_id))

        return False

    for story_id in graph:
        has_circular_dep(story_id)

    state.dependency_graph = graph
    state.circular_dependencies = circular_deps

    # Use LLM to review dependencies
    review_prompt = f"""Review these story dependencies for correctness:
{graph}

Are there any missing dependencies or logical issues?"""

    llm.invoke(review_prompt)

    state.add_message("dependency_mapping", f"Built dependency graph with {len(graph)} stories")
    return state


# ============================================================================
# NODE 3: CAPACITY ANALYSIS
# ============================================================================


def capacity_analysis(state: EMWorkflowState) -> EMWorkflowState:
    """
    Estimate sprint capacity based on team velocity and availability.

    Determines how many stories fit in the sprint.
    """
    state.current_agent = "capacity_analysis"

    # Read team velocity and leave calendar
    velocity_result = ContextStoreTool.read_team_velocity()
    leave_result = ContextStoreTool.read_leave_calendar()

    if not velocity_result.success or not leave_result.success:
        state.add_error("Failed to read team metrics")
        return state

    velocity_data = velocity_result.data
    leave_data = leave_result.data

    # Calculate capacity
    team_size = leave_data.get("team_members", 5)
    planned_leave_hours = leave_data.get("total_leave_hours", 0)
    team_velocity = velocity_data.get("average_velocity", 35.0)

    sprint_duration_days = 14
    available_hours_per_day = 6  # Account for meetings, overhead
    total_available_hours = team_size * available_hours_per_day * sprint_duration_days
    usable_capacity_hours = (
        total_available_hours - planned_leave_hours - (team_size * sprint_duration_days * 1)
    )  # 1h overhead

    # Estimate story points capacity
    velocity_per_day = team_velocity / 14
    estimated_capacity = int((usable_capacity_hours / available_hours_per_day) * velocity_per_day)

    state.capacity_report = CapacityReport(
        id="CAP-001",
        team_size=team_size,
        available_hours_per_day=available_hours_per_day,
        team_velocity=team_velocity,
        sprint_duration_days=sprint_duration_days,
        total_available_hours=total_available_hours,
        planned_leave_hours=planned_leave_hours,
        unplanned_overhead_hours=team_size * sprint_duration_days * 1,
        usable_capacity_hours=usable_capacity_hours,
        estimated_story_points_capacity=estimated_capacity,
        confidence_level="medium",
        confidence_reason="Based on 5-sprint average with current team composition",
        created_by="em-agent",
    )

    state.add_message(
        "capacity_analysis",
        f"Analyzed capacity: {estimated_capacity} story points available",
    )

    return state


# ============================================================================
# NODE 4: RISK ASSESSMENT
# ============================================================================


def risk_assessment(state: EMWorkflowState) -> EMWorkflowState:
    """
    Identify and flag stories with risks.

    Flags high complexity, unknown dependencies, and capacity overrun risks.
    """
    state.current_agent = "risk_assessment"

    risk_flags = []
    risk_counts = {}

    # Use LLM to assess risks
    assessment_prompt = f"""Assess risks in these stories:
{[s.title for s in state.validated_stories]}

Consider:
- Complexity (XL = high risk)
- Unknown dependencies
- Potential integration issues"""

    llm.invoke(assessment_prompt)

    # Create risk flags
    for story in state.validated_stories:
        # Check complexity
        if story.estimated_complexity in ["l", "xl"]:
            risk_type = RiskType.COMPLEXITY
            flag = RiskFlag(
                id=f"RISK-{story.id}-COMPLEXITY",
                story_id=story.id,
                risk_type=risk_type,
                severity=(
                    RiskSeverity.HIGH if story.estimated_complexity == "xl" else RiskSeverity.MEDIUM
                ),
                title=f"High complexity: {story.title}",
                description=f"Story estimated as {story.estimated_complexity.upper()} complexity",
                impact="May require additional testing and review",
                mitigation="Pair programming, early code reviews",
                created_by="em-agent",
            )
            risk_flags.append(flag)
            risk_counts[risk_type.value] = risk_counts.get(risk_type.value, 0) + 1

        # Check dependencies
        if story.depends_on:
            risk_type = RiskType.DEPENDENCY
            flag = RiskFlag(
                id=f"RISK-{story.id}-DEPENDENCY",
                story_id=story.id,
                risk_type=risk_type,
                severity=RiskSeverity.MEDIUM,
                title=f"Story dependency: {story.title}",
                description=f"Depends on: {', '.join(story.depends_on)}",
                impact="Cannot start until dependencies complete",
                mitigation="Prioritize dependencies early in sprint",
                created_by="em-agent",
            )
            risk_flags.append(flag)
            risk_counts[risk_type.value] = risk_counts.get(risk_type.value, 0) + 1

    state.risk_flags = risk_flags
    state.risk_summary = risk_counts

    state.add_message("risk_assessment", f"Identified {len(risk_flags)} potential risks")
    return state


# ============================================================================
# NODE 5: SPRINT COMPOSITION
# ============================================================================


def sprint_composition(state: EMWorkflowState) -> EMWorkflowState:
    """
    Compose sprint respecting dependencies, capacity, and risks.

    Groups stories into a draft sprint plan.
    """
    state.current_agent = "sprint_composition"

    # Use LLM to determine sprint composition
    composition_prompt = f"""Plan a sprint with these stories:
{[s.title for s in state.validated_stories]}

Constraints:
- Capacity: {state.capacity_report.estimated_story_points_capacity} points
- Dependencies: {state.dependency_graph}
- Risks: {[r.title for r in state.risk_flags[:3]]}

Assign each story to frontend or backend track."""

    llm.invoke(composition_prompt)

    # Create sprint tasks
    tasks = []
    sprint_stories = []

    for i, story in enumerate(state.validated_stories[:5]):  # Limit to capacity
        track = "frontend" if i % 2 == 0 else "backend"
        task_id = f"T-{i+1:03d}"

        task = SprintTask(
            id=task_id,
            user_story_id=story.id,
            title=story.title,
            description=story.description,
            assigned_to=f"{track}-agent",
            task_type="frontend" if track == "frontend" else "backend",
            estimated_hours=8 if story.estimated_complexity in ["m", "l"] else 4,
            acceptance_criteria=story.acceptance_criteria,
            depends_on_tasks=[],
        )
        tasks.append(task)
        sprint_stories.append(story)

    # Create draft sprint
    start = datetime.utcnow()
    end = start + timedelta(days=14)

    state.draft_sprint = SprintPlan(
        sprint=Sprint(
            id="SPRINT-1",
            name="Sprint 1",
            start_date=start,
            end_date=end,
            tasks=tasks,
            created_by="em-agent",
        ),
        user_stories={s.id: s.to_dict() for s in sprint_stories},
        created_by="em-agent",
    )

    state.add_message("sprint_composition", f"Composed sprint with {len(tasks)} tasks")
    return state


# ============================================================================
# NODE 6: DEFINITION OF DONE
# ============================================================================


def definition_of_done(state: EMWorkflowState) -> EMWorkflowState:
    """
    Generate DoD checklist tailored to sprint stories.

    Creates checklist based on story types in the sprint.
    """
    state.current_agent = "definition_of_done"

    # Use LLM to identify story types
    dod_prompt = """Given these sprint stories, what Definition of Done items are needed?
Consider: features, code quality, testing, documentation, integration."""

    llm.invoke(dod_prompt)

    # Create DoD items
    items = [
        DoDItem(
            id="DOD-001",
            category=DoDCategory.CODE,
            description="Code written with proper error handling",
            acceptance_criteria="Code review approved, no unhandled exceptions",
            applies_to_all=True,
            mandatory=True,
            created_by="em-agent",
        ),
        DoDItem(
            id="DOD-002",
            category=DoDCategory.TESTING,
            description="Unit tests written and passing",
            acceptance_criteria="Coverage > 80%, all tests green",
            applies_to_story_types=["feature"],
            mandatory=True,
            effort_estimate_hours=2,
            created_by="em-agent",
        ),
        DoDItem(
            id="DOD-003",
            category=DoDCategory.DOCUMENTATION,
            description="Code documented and README updated",
            acceptance_criteria="All public methods documented, design docs updated",
            applies_to_all=True,
            mandatory=True,
            created_by="em-agent",
        ),
        DoDItem(
            id="DOD-004",
            category=DoDCategory.REVIEW,
            description="Code reviewed and approved",
            acceptance_criteria="At least 1 approval from senior engineer",
            applies_to_all=True,
            mandatory=True,
            created_by="em-agent",
        ),
        DoDItem(
            id="DOD-005",
            category=DoDCategory.INTEGRATION,
            description="Integrated with main branch",
            acceptance_criteria="All CI/CD checks pass",
            applies_to_all=True,
            mandatory=True,
            created_by="em-agent",
        ),
    ]

    state.dod_checklist = DefinitionOfDone(
        id="DOD-SPRINT-1",
        sprint_id="SPRINT-1",
        items=items,
        total_effort_hours=sum(item.effort_estimate_hours or 0 for item in items if item.mandatory),
        created_by="em-agent",
    )

    state.add_message("definition_of_done", f"Generated DoD checklist with {len(items)} items")
    return state


# ============================================================================
# NODE 7: HUMAN CHECKPOINT
# ============================================================================


def human_checkpoint(state: EMWorkflowState) -> EMWorkflowState:
    """
    Human approval checkpoint for sprint plan.

    Displays draft sprint and risks, waits for approval.
    """
    state.current_agent = "human_checkpoint"
    state.checkpoint_reached = True

    # Web mode: the decision is injected by the web layer via update_state before
    # the graph resumes, so skip the blocking CLI prompt.
    if state.web_mode:
        return state

    # Display sprint for approval
    print("\n" + "=" * 80)
    print(" HUMAN CHECKPOINT: REVIEW SPRINT PLAN")
    print("=" * 80)

    if state.draft_sprint:
        print(state.draft_sprint.to_markdown())

    if state.risk_flags:
        print("\n" + "-" * 80)
        print("RISK FLAGS:")
        print("-" * 80)
        for flag in state.risk_flags[:5]:
            print(flag.to_markdown())

    # Get approval
    response = input("\nDo you approve this sprint plan? (y/n/modify): ").strip().lower()

    if response == "y":
        state.sprint_approved = True
        state.add_message("human_checkpoint", "Sprint approved by human")
    elif response == "n":
        state.sprint_approved = False
        feedback = input("Provide feedback: ").strip()
        state.approval_feedback = feedback
        state.add_message("human_checkpoint", f"Sprint rejected. Feedback: {feedback}")
    else:
        state.approval_feedback = "Requested modifications not yet implemented"
        state.add_message("human_checkpoint", "Modification request noted")

    return state


# ============================================================================
# NODE 8: SPRINT CREATION
# ============================================================================


def sprint_creation(state: EMWorkflowState) -> EMWorkflowState:
    """
    Create sprint in Jira and assign stories.

    Stub for real Jira API integration.
    """
    state.current_agent = "sprint_creation"

    if not state.draft_sprint or not state.sprint_approved:
        state.add_error("Cannot create sprint: not approved")
        return state

    sprint = state.draft_sprint.sprint

    # TODO: Real Jira integration needed
    # - Create sprint via Jira REST API
    # - Assign all tasks/stories to sprint
    # - Set sprint start/end dates
    # - Configure board view

    tool_result = JiraIntegrationTool.create_jira_sprint(
        sprint_name=sprint.name,
        start_date=sprint.start_date.isoformat(),
        end_date=sprint.end_date.isoformat(),
    )

    if tool_result.success:
        state.sprint_id = tool_result.data["sprint_id"]

        # Assign stories
        story_ids = [task.user_story_id for task in sprint.tasks]

        assign_result = JiraIntegrationTool.assign_stories_to_sprint(
            sprint_id=state.sprint_id,
            story_ids=story_ids,
        )

        if assign_result.success:
            state.jira_tickets_created = story_ids

    state.add_message("sprint_creation", f"Created sprint {state.sprint_id}")
    return state


# ============================================================================
# NODE 9: STATUS MONITORING
# ============================================================================


def status_monitoring(state: EMWorkflowState) -> EMWorkflowState:
    """
    Poll Jira for sprint status (runs in loop).

    Continuously monitors sprint progress.

    NOTE: This node runs on a polling loop with configurable interval.
    In production, would be triggered by timer/scheduler, not called once.
    """
    state.current_agent = "status_monitoring"

    if not state.sprint_id:
        state.add_error("No active sprint to monitor")
        return state

    # TODO: Real polling loop design
    # This should be:
    # - Triggered by scheduler/timer every N minutes
    # - Run continuously during sprint
    # - Update sprint_status_history with each poll
    # - Detect trends and regressions
    # - Trigger alerts if health degrades

    # Get current status from Jira
    status_result = JiraIntegrationTool.poll_jira_sprint_status(state.sprint_id)

    if status_result.success:
        # Convert to SprintStatus
        data = status_result.data

        sprint_status = SprintStatus(
            id=f"STATUS-{datetime.utcnow().isoformat()}",
            sprint_id=state.sprint_id,
            phase=SprintPhase.IN_PROGRESS,
            started_at=datetime.utcnow(),
            total_stories=data.get("total_issues", 10),
            stories_todo=data.get("todo_issues", 5),
            stories_in_progress=data.get("in_progress_issues", 3),
            stories_done=data.get("completed_issues", 2),
            stories_blocked=data.get("blocked_issues", 0),
            total_points=35,
            points_completed=15,
            points_in_progress=15,
            updated_by="em-agent",
        )

        state.current_sprint_status = sprint_status
        state.sprint_status_history.append(sprint_status)
        state.last_status_check = datetime.utcnow()
        state.status_monitoring_active = True

    state.add_message("status_monitoring", "Polled sprint status from Jira")
    return state


# ============================================================================
# NODE 10: BLOCKER DETECTION
# ============================================================================


def blocker_detection(state: EMWorkflowState) -> EMWorkflowState:
    """
    Identify blocked stories and escalate.

    Detects stories blocked, overdue, or at risk.
    """
    state.current_agent = "blocker_detection"

    if not state.current_sprint_status:
        state.add_message("blocker_detection", "No sprint status available")
        return state

    blockers = []

    # Use LLM to analyze sprint status for risks
    analysis_prompt = f"""Analyze this sprint status for blockers:
Stories blocked: {state.current_sprint_status.stories_blocked}
Velocity: {state.current_sprint_status.velocity}
On track: {state.current_sprint_status.on_track}

What stories are at risk of not completing?"""

    llm.invoke(analysis_prompt)

    # Create blocker records for blocked stories
    if state.current_sprint_status.stories_blocked > 0:
        blocker = Blocker(
            id="BLOCKER-001",
            story_id="US-001",
            sprint_id=state.sprint_id or "",
            blocker_type=BlockerType.UNKNOWN,
            title="Story blocked",
            description="Story is currently blocked",
            days_blocked=1,
            developer_impact="Engineer cannot progress",
            business_impact="May impact sprint completion",
            status="open",
            created_by="em-agent",
        )
        blockers.append(blocker)

    state.blockers = blockers

    state.add_message("blocker_detection", f"Detected {len(blockers)} blockers")
    return state


# ============================================================================
# NODE 11: STAKEHOLDER REPORTING
# ============================================================================


def stakeholder_reporting(state: EMWorkflowState) -> EMWorkflowState:
    """
    Generate sprint status report for stakeholders.

    Creates human-readable markdown report with metrics and issues.
    """
    state.current_agent = "stakeholder_reporting"

    # TODO: Real integration needed
    # - Post to Slack channel
    # - Send email to stakeholders
    # - Update dashboard
    # - Archive report in shared drive

    report_lines = [
        "# Sprint Status Report",
        f"**Sprint:** {state.sprint_id or 'N/A'}",
        "",
    ]

    if state.current_sprint_status:
        report_lines.append(state.current_sprint_status.to_markdown())

    if state.blockers:
        report_lines.extend(
            [
                "",
                "## Blockers",
            ]
        )
        for blocker in state.blockers:
            report_lines.append(blocker.to_markdown())

    if state.risk_flags:
        report_lines.extend(
            [
                "",
                "## Risks",
            ]
        )
        for flag in state.risk_flags[:3]:
            report_lines.append(flag.to_markdown())

    report_lines.extend(
        [
            "",
            f"**Report Generated:** {datetime.utcnow().isoformat()}",
            "**Generated By:** em-agent",
        ]
    )

    state.sprint_report = "\n".join(report_lines)
    state.report_generated = True

    # TODO: Send notifications
    # slack_result = NotificationTool.post_to_slack(
    #     channel="sprint-updates",
    #     message=state.sprint_report,
    # )
    #
    # email_result = NotificationTool.send_email(
    #     recipients=["team@company.com", "stakeholders@company.com"],
    #     subject=f"Sprint Status Report - {state.sprint_id}",
    #     html_body=state.sprint_report,
    # )

    state.add_message("stakeholder_reporting", "Generated and sent sprint report")
    return state
