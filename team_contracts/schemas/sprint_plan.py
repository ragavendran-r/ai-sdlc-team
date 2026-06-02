"""SprintPlan handoff contract: EM → all dev workflows."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


class TaskType(str, Enum):
    """Types of tasks in a sprint."""
    DESIGN = "design"
    FRONTEND = "frontend"
    BACKEND = "backend"
    INTEGRATION_TEST = "integration_test"
    DEVOPS = "devops"


class TaskStatus(str, Enum):
    """Task status."""
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"


class SprintTask(BaseModel):
    """Individual task within a sprint."""

    id: str = Field(..., description="Unique task identifier")
    user_story_id: str = Field(..., description="Reference to parent user story")
    title: str = Field(..., description="Task title", min_length=5, max_length=200)
    description: str = Field(..., description="Detailed task description")

    # Assignment
    assigned_to: str = Field(..., description="Agent responsible (e.g., 'frontend-agent')")
    task_type: TaskType = Field(..., description="Type of work")

    # Planning
    estimated_hours: float = Field(..., gt=0, le=40, description="Estimated effort in hours")
    acceptance_criteria: List[str] = Field(
        ...,
        description="Specific, testable criteria for completion",
        min_items=1
    )

    # Dependencies
    depends_on_tasks: List[str] = Field(
        default_factory=list,
        description="Task IDs that must complete first"
    )
    blocks_tasks: List[str] = Field(
        default_factory=list,
        description="Task IDs that cannot start until this completes"
    )

    # Status
    status: TaskStatus = Field(default=TaskStatus.ASSIGNED)
    actual_hours: Optional[float] = Field(default=None, ge=0, description="Hours actually spent")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('acceptance_criteria')
    @classmethod
    def validate_criteria(cls, v: List[str]) -> List[str]:
        """Ensure all acceptance criteria are non-empty."""
        for criterion in v:
            if not criterion.strip():
                raise ValueError("Acceptance criteria cannot be empty strings")
        return [c.strip() for c in v]

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"### {self.title}",
            f"**ID:** {self.id} | **Type:** {self.task_type.value} | **Status:** {self.status.value}",
            f"**Assigned to:** {self.assigned_to}",
            f"**Story:** {self.user_story_id}",
            "",
            self.description,
            "",
            f"**Estimated:** {self.estimated_hours}h",
        ]

        if self.actual_hours is not None:
            lines.append(f"**Actual:** {self.actual_hours}h")

        lines.extend([
            "",
            "**Acceptance Criteria:**",
        ])

        for i, criterion in enumerate(self.acceptance_criteria, 1):
            lines.append(f"- [ ] {criterion}")

        if self.depends_on_tasks:
            lines.append("")
            lines.append(f"**Depends on:** {', '.join(f'`{t}`' for t in self.depends_on_tasks)}")

        if self.blocks_tasks:
            lines.append(f"**Blocks:** {', '.join(f'`{t}`' for t in self.blocks_tasks)}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "user_story_id": self.user_story_id,
            "title": self.title,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "task_type": self.task_type.value,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "acceptance_criteria": self.acceptance_criteria,
            "depends_on_tasks": self.depends_on_tasks,
            "blocks_tasks": self.blocks_tasks,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Sprint(BaseModel):
    """A sprint containing multiple tasks."""

    id: str = Field(..., description="Unique sprint identifier")
    name: str = Field(..., description="Sprint name (e.g., 'Sprint 2.1')", min_length=3)
    description: Optional[str] = Field(default=None, description="Sprint theme or goals")

    # Timeline
    start_date: datetime = Field(..., description="Sprint start date")
    end_date: datetime = Field(..., description="Sprint end date")

    # Tasks
    tasks: List[SprintTask] = Field(
        ...,
        description="All tasks in this sprint",
        min_items=1
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent that created the plan")

    @model_validator(mode='after')
    def validate_dates(self):
        """Ensure end_date is after start_date."""
        if self.end_date <= self.start_date:
            raise ValueError("Sprint end_date must be after start_date")
        # Sprints are typically 1-4 weeks
        duration = self.end_date - self.start_date
        if duration.days > 30:
            raise ValueError("Sprint duration should not exceed 30 days")
        return self

    def get_tasks_by_agent(self) -> Dict[str, List[SprintTask]]:
        """Group tasks by assigned agent."""
        result = {}
        for task in self.tasks:
            if task.assigned_to not in result:
                result[task.assigned_to] = []
            result[task.assigned_to].append(task)
        return result

    def get_blocked_tasks(self) -> List[SprintTask]:
        """Return tasks that are currently blocked."""
        return [t for t in self.tasks if t.status == TaskStatus.BLOCKED]

    def total_estimated_hours(self) -> float:
        """Sum of all estimated hours."""
        return sum(t.estimated_hours for t in self.tasks)

    def total_actual_hours(self) -> float:
        """Sum of actual hours spent (for completed tasks)."""
        return sum(t.actual_hours or 0 for t in self.tasks)

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        duration = (self.end_date - self.start_date).days
        tasks_by_agent = self.get_tasks_by_agent()

        lines = [
            f"# {self.name}",
            f"**ID:** {self.id}",
            f"**Duration:** {duration} days",
            f"**Start:** {self.start_date.strftime('%Y-%m-%d')}",
            f"**End:** {self.end_date.strftime('%Y-%m-%d')}",
        ]

        if self.description:
            lines.extend(["", "## Goals", self.description])

        lines.extend([
            "",
            "## Summary",
            f"- **Total Tasks:** {len(self.tasks)}",
            f"- **Total Estimated Hours:** {self.total_estimated_hours()}h",
            f"- **Blocked Tasks:** {len(self.get_blocked_tasks())}",
        ])

        lines.append("")
        lines.append("## Tasks by Agent")

        for agent, agent_tasks in sorted(tasks_by_agent.items()):
            total_hours = sum(t.estimated_hours for t in agent_tasks)
            lines.append(f"\n### {agent} ({total_hours}h)")

            for task in agent_tasks:
                lines.append(task.to_markdown())

        lines.extend([
            "",
            f"**Created:** {self.created_at.isoformat()}",
            f"**Created By:** {self.created_by}",
        ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "summary": {
                "total_tasks": len(self.tasks),
                "total_estimated_hours": self.total_estimated_hours(),
                "total_actual_hours": self.total_actual_hours(),
                "blocked_tasks": len(self.get_blocked_tasks()),
                "tasks_by_agent": {
                    agent: len(tasks)
                    for agent, tasks in self.get_tasks_by_agent().items()
                },
            },
        }


class SprintPlan(BaseModel):
    """
    SprintPlan is the primary handoff contract from EM to all dev workflows.

    It contains a complete sprint plan with all tasks assigned and ready
    for team members (agents) to execute.
    """

    sprint: Sprint = Field(..., description="The sprint being planned")

    # Context for all agents
    user_stories: Dict[str, dict] = Field(
        default_factory=dict,
        description="UserStory data by ID for reference"
    )

    # Constraints and context
    shared_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Team context that may affect execution"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent that created the plan (typically 'em-agent')")

    def to_markdown(self) -> str:
        """Convert entire plan to Markdown."""
        lines = [self.sprint.to_markdown()]

        if self.shared_context:
            lines.extend([
                "",
                "## Shared Context",
                "```json",
            ])
            import json
            lines.append(json.dumps(self.shared_context, indent=2))
            lines.append("```")

        lines.extend([
            "",
            f"**Plan Created:** {self.created_at.isoformat()}",
            f"**Created By:** {self.created_by}",
        ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "sprint": self.sprint.to_dict(),
            "user_stories": self.user_stories,
            "shared_context": self.shared_context,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }


if __name__ == "__main__":
    # Example usage
    start = datetime.utcnow()
    end = start + timedelta(days=14)

    tasks = [
        SprintTask(
            id="T-001",
            user_story_id="US-001",
            title="Implement login form UI",
            description="Build the login form component with email and password fields.",
            assigned_to="frontend-agent",
            task_type=TaskType.FRONTEND,
            estimated_hours=4,
            acceptance_criteria=[
                "Form displays email and password fields",
                "Form validation prevents submission without both fields",
                "Form is responsive on mobile and desktop",
            ],
        ),
        SprintTask(
            id="T-002",
            user_story_id="US-001",
            title="Implement login API endpoint",
            description="Build the backend endpoint to authenticate users.",
            assigned_to="backend-agent",
            task_type=TaskType.BACKEND,
            estimated_hours=6,
            acceptance_criteria=[
                "Endpoint validates credentials against database",
                "Endpoint returns JWT token on success",
                "Endpoint returns 401 on invalid credentials",
                "Failed attempts are logged",
            ],
        ),
        SprintTask(
            id="T-003",
            user_story_id="US-001",
            title="Connect frontend to login API",
            description="Wire up the login form to call the backend endpoint.",
            assigned_to="frontend-agent",
            task_type=TaskType.FRONTEND,
            estimated_hours=3,
            depends_on_tasks=["T-002"],
            acceptance_criteria=[
                "Form submission calls API endpoint",
                "Success response saves token and redirects",
                "Error response displays message to user",
            ],
        ),
    ]

    sprint = Sprint(
        id="S-2.1",
        name="Sprint 2.1 - User Authentication",
        description="Implement core user authentication flow",
        start_date=start,
        end_date=end,
        tasks=tasks,
        created_by="em-agent",
    )

    plan = SprintPlan(
        sprint=sprint,
        user_stories={
            "US-001": {
                "title": "User login with email and password",
                "priority": "high",
            }
        },
        created_by="em-agent",
    )

    print(plan.to_markdown())
    print("\n" + "="*60 + "\n")
    import json
    print(json.dumps(plan.to_dict(), indent=2))
