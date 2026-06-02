"""UserPersona schema: user personas for UX design."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class UserPersona(BaseModel):
    """
    UserPersona represents a distinct user type or segment.

    Used by UX workflow to understand who the product serves
    and design for their needs, behaviors, and goals.
    """

    id: str = Field(..., description="Unique persona identifier")
    name: str = Field(..., description="Persona name (e.g., 'Sarah, the Busy Manager')")

    # Demographics
    demographic_summary: str = Field(
        ...,
        description="Age, role, background summary"
    )
    role: str = Field(
        ...,
        description="User's role or job title"
    )

    # Behaviors and goals
    goals: List[str] = Field(
        ...,
        description="Primary user goals and outcomes they seek",
        min_items=1
    )
    pain_points: List[str] = Field(
        ...,
        description="Challenges and frustrations the user faces",
        min_items=1
    )
    behaviors: List[str] = Field(
        default_factory=list,
        description="Typical behaviors and patterns"
    )

    # Context
    experience_level: str = Field(
        default="intermediate",
        description="Technical/product experience level (novice, intermediate, expert)"
    )
    primary_devices: List[str] = Field(
        default_factory=list,
        description="Devices they primarily use (desktop, mobile, tablet)"
    )

    # Motivations
    motivations: List[str] = Field(
        default_factory=list,
        description="What motivates or drives this user"
    )

    # Success criteria
    success_metrics: List[str] = Field(
        default_factory=list,
        description="How we measure success for this persona"
    )

    # Notes
    notes: Optional[str] = Field(
        default=None,
        description="Additional context or insights"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent that created this persona")

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"## {self.name}",
            f"**Role:** {self.role}",
            f"**Demographics:** {self.demographic_summary}",
            f"**Experience Level:** {self.experience_level}",
            "",
            "### Goals",
        ]

        for goal in self.goals:
            lines.append(f"- {goal}")

        lines.extend([
            "",
            "### Pain Points",
        ])
        for pain in self.pain_points:
            lines.append(f"- {pain}")

        if self.behaviors:
            lines.extend([
                "",
                "### Behaviors",
            ])
            for behavior in self.behaviors:
                lines.append(f"- {behavior}")

        if self.primary_devices:
            lines.extend([
                "",
                f"**Primary Devices:** {', '.join(self.primary_devices)}",
            ])

        if self.motivations:
            lines.extend([
                "",
                "### Motivations",
            ])
            for motivation in self.motivations:
                lines.append(f"- {motivation}")

        if self.success_metrics:
            lines.extend([
                "",
                "### Success Metrics",
            ])
            for metric in self.success_metrics:
                lines.append(f"- {metric}")

        if self.notes:
            lines.extend([
                "",
                f"**Notes:** {self.notes}",
            ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "name": self.name,
            "demographic_summary": self.demographic_summary,
            "role": self.role,
            "goals": self.goals,
            "pain_points": self.pain_points,
            "behaviors": self.behaviors,
            "experience_level": self.experience_level,
            "primary_devices": self.primary_devices,
            "motivations": self.motivations,
            "success_metrics": self.success_metrics,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
