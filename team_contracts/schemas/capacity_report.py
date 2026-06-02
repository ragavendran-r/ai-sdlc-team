"""CapacityReport schema: capacity planning for sprints."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CapacityReport(BaseModel):
    """
    CapacityReport estimates sprint capacity based on team velocity and availability.

    Used by EM workflow to determine how many stories fit in a sprint.
    """

    id: str = Field(..., description="Unique report identifier")
    sprint_id: Optional[str] = Field(default=None, description="Sprint this capacity is for")

    # Team metrics
    team_size: int = Field(..., description="Number of team members available")
    available_hours_per_day: float = Field(
        ...,
        description="Available hours per team member per day"
    )
    team_velocity: float = Field(
        ...,
        description="Historical points per sprint (from metrics)",
        ge=0
    )

    # Sprint duration
    sprint_duration_days: int = Field(
        default=14,
        description="Duration of sprint in days"
    )

    # Capacity calculations
    total_available_hours: float = Field(
        ...,
        description="Total person-hours available in sprint",
        ge=0
    )
    planned_leave_hours: float = Field(
        default=0,
        description="Hours lost to planned leave",
        ge=0
    )
    unplanned_overhead_hours: float = Field(
        default=0,
        description="Hours lost to meetings, interruptions, etc.",
        ge=0
    )
    usable_capacity_hours: float = Field(
        ...,
        description="Actual working hours available",
        ge=0
    )

    # Points capacity
    estimated_story_points_capacity: int = Field(
        ...,
        description="Estimated story points that fit in this sprint",
        ge=0
    )

    # Risk assessment
    confidence_level: str = Field(
        default="medium",
        description="Confidence in this estimate (low, medium, high)",
    )
    confidence_reason: Optional[str] = Field(
        default=None,
        description="Why we have this confidence level"
    )

    # Notes
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes about capacity planning"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent that created this report")

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            "# Capacity Report",
            f"**ID:** {self.id}",
            f"**Team Velocity:** {self.team_velocity} points/sprint",
            "",
            "## Team Availability",
            f"- Team Size: {self.team_size} members",
            f"- Hours/Day: {self.available_hours_per_day}h per member",
            f"- Sprint Duration: {self.sprint_duration_days} days",
            "",
            "## Capacity Calculation",
            f"- Total Available Hours: {self.total_available_hours}h",
            f"- Planned Leave: {self.planned_leave_hours}h",
            f"- Overhead: {self.unplanned_overhead_hours}h",
            f"- **Usable Capacity: {self.usable_capacity_hours}h**",
            "",
            "## Sprint Capacity",
            f"**Estimated Story Points Capacity: {self.estimated_story_points_capacity}**",
            f"Confidence: {self.confidence_level.upper()}",
            "",
        ]

        if self.confidence_reason:
            lines.extend([
                "## Confidence Rationale",
                self.confidence_reason,
                "",
            ])

        if self.notes:
            lines.extend([
                "## Notes",
                self.notes,
                "",
            ])

        lines.extend([
            f"**Created:** {self.created_at.isoformat()}",
            f"**Created By:** {self.created_by}",
        ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "sprint_id": self.sprint_id,
            "team_size": self.team_size,
            "available_hours_per_day": self.available_hours_per_day,
            "team_velocity": self.team_velocity,
            "sprint_duration_days": self.sprint_duration_days,
            "total_available_hours": self.total_available_hours,
            "planned_leave_hours": self.planned_leave_hours,
            "unplanned_overhead_hours": self.unplanned_overhead_hours,
            "usable_capacity_hours": self.usable_capacity_hours,
            "estimated_story_points_capacity": self.estimated_story_points_capacity,
            "confidence_level": self.confidence_level,
            "confidence_reason": self.confidence_reason,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
