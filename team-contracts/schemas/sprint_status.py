"""SprintStatus schema: real-time sprint execution monitoring."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class SprintPhase(str, Enum):
    """Sprint execution phases."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    RETROSPECTIVE = "retrospective"
    COMPLETED = "completed"


class StoryStatusInSprint(str, Enum):
    """Status of a story within a sprint."""
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    BLOCKED = "blocked"
    DONE = "done"


class SprintStatus(BaseModel):
    """
    SprintStatus tracks real-time execution status of a sprint.

    Updated periodically by polling Jira or other task tracking systems.
    """

    id: str = Field(..., description="Unique status snapshot identifier")
    sprint_id: str = Field(..., description="Sprint being tracked")

    # Phase tracking
    phase: SprintPhase = Field(..., description="Current sprint phase")
    started_at: Optional[datetime] = Field(default=None, description="When sprint started")
    ended_at: Optional[datetime] = Field(default=None, description="When sprint ended")

    # Story counts
    total_stories: int = Field(..., ge=0, description="Total stories in sprint")
    stories_todo: int = Field(default=0, ge=0)
    stories_in_progress: int = Field(default=0, ge=0)
    stories_in_review: int = Field(default=0, ge=0)
    stories_done: int = Field(default=0, ge=0)
    stories_blocked: int = Field(default=0, ge=0)

    # Points tracking
    total_points: int = Field(default=0, ge=0, description="Total story points in sprint")
    points_completed: int = Field(default=0, ge=0, description="Story points completed")
    points_in_progress: int = Field(default=0, ge=0, description="Story points in progress")
    points_blocked: int = Field(default=0, ge=0, description="Story points blocked")

    # Burndown
    estimated_completion_date: Optional[datetime] = Field(
        default=None,
        description="Projected completion date"
    )
    days_remaining: Optional[int] = Field(
        default=None,
        description="Days left in sprint",
        ge=0
    )
    velocity: Optional[float] = Field(
        default=None,
        description="Current sprint velocity (points/day)",
        ge=0
    )

    # Health
    on_track: bool = Field(
        default=True,
        description="Is sprint on track to complete?"
    )
    health_status: str = Field(
        default="green",
        description="Health status (green, yellow, red)"
    )

    # Story details
    story_statuses: Dict[str, StoryStatusInSprint] = Field(
        default_factory=dict,
        description="Status of each story by ID"
    )

    # Notes
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes about sprint status"
    )

    # Metadata
    snapshot_time: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str = Field(..., description="Agent or system that updated this")

    def get_completion_percentage(self) -> float:
        """Calculate sprint completion percentage."""
        if self.total_points == 0:
            return 0.0
        return (self.points_completed / self.total_points) * 100

    def get_story_completion_percentage(self) -> float:
        """Calculate story completion percentage."""
        if self.total_stories == 0:
            return 0.0
        return (self.stories_done / self.total_stories) * 100

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        completion_pct = self.get_completion_percentage()
        story_pct = self.get_story_completion_percentage()

        lines = [
            f"# Sprint Status: {self.sprint_id}",
            f"**Phase:** {self.phase.value.upper()}",
            f"**Health:** {self.health_status.upper()}",
            f"**On Track:** {'✅ Yes' if self.on_track else '❌ No'}",
            "",
            "## Burndown",
            f"- **Story Points:** {self.points_completed}/{self.total_points} ({completion_pct:.1f}%)",
            f"- **Stories:** {self.stories_done}/{self.total_stories} ({story_pct:.1f}%)",
            "",
            "## Story Breakdown",
            f"- Todo: {self.stories_todo}",
            f"- In Progress: {self.stories_in_progress}",
            f"- In Review: {self.stories_in_review}",
            f"- Blocked: {self.stories_blocked}",
            f"- Done: {self.stories_done}",
            "",
            "## Metrics",
        ]

        if self.velocity:
            lines.append(f"- **Velocity:** {self.velocity:.2f} points/day")

        if self.days_remaining is not None:
            lines.append(f"- **Days Remaining:** {self.days_remaining}")

        if self.estimated_completion_date:
            lines.append(f"- **Est. Completion:** {self.estimated_completion_date.strftime('%Y-%m-%d')}")

        if self.notes:
            lines.extend([
                "",
                "## Notes",
                self.notes,
            ])

        lines.extend([
            "",
            f"**Last Updated:** {self.snapshot_time.isoformat()}",
            f"**Updated By:** {self.updated_by}",
        ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "sprint_id": self.sprint_id,
            "phase": self.phase.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "total_stories": self.total_stories,
            "stories_todo": self.stories_todo,
            "stories_in_progress": self.stories_in_progress,
            "stories_in_review": self.stories_in_review,
            "stories_done": self.stories_done,
            "stories_blocked": self.stories_blocked,
            "total_points": self.total_points,
            "points_completed": self.points_completed,
            "points_in_progress": self.points_in_progress,
            "points_blocked": self.points_blocked,
            "completion_percentage": self.get_completion_percentage(),
            "story_completion_percentage": self.get_story_completion_percentage(),
            "estimated_completion_date": self.estimated_completion_date.isoformat() if self.estimated_completion_date else None,
            "days_remaining": self.days_remaining,
            "velocity": self.velocity,
            "on_track": self.on_track,
            "health_status": self.health_status,
            "story_statuses": {k: v.value for k, v in self.story_statuses.items()},
            "notes": self.notes,
            "snapshot_time": self.snapshot_time.isoformat(),
            "updated_by": self.updated_by,
        }
