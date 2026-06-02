"""Blocker schema: stories blocked during sprint execution."""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class BlockerStatus(str, Enum):
    """Status of a blocker."""
    OPEN = "open"
    IN_RESOLUTION = "in_resolution"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class BlockerType(str, Enum):
    """Types of blockers."""
    DEPENDENCY = "dependency"              # Blocked on another story
    RESOURCE = "resource"                  # Resource not available
    DESIGN = "design"                      # Design not ready
    EXTERNAL = "external"                  # Blocked on external system/person
    TECHNICAL = "technical"                # Technical blocker
    INTEGRATION = "integration"            # Integration issue
    UNKNOWN = "unknown"                    # Unknown blocker


class Blocker(BaseModel):
    """
    Blocker represents a story that is blocked and cannot progress.

    Tracked during sprint execution for monitoring and escalation.
    """

    id: str = Field(..., description="Unique blocker identifier")
    story_id: str = Field(..., description="Story that is blocked")
    sprint_id: Optional[str] = Field(default=None, description="Sprint this blocker is in")

    # Blocker details
    blocker_type: BlockerType = Field(..., description="Type of blocker")
    title: str = Field(..., description="Short blocker title")
    description: str = Field(..., description="Detailed blocker description")

    # Impact
    days_blocked: int = Field(
        default=0,
        ge=0,
        description="Number of days this story has been blocked"
    )
    developer_impact: str = Field(
        ...,
        description="Who/what is blocked? (person, team, other story, etc.)"
    )
    business_impact: Optional[str] = Field(
        default=None,
        description="What is the business impact?"
    )

    # Resolution
    status: BlockerStatus = Field(default=BlockerStatus.OPEN)
    resolution_plan: Optional[str] = Field(
        default=None,
        description="Plan to resolve this blocker"
    )
    blocker_owner: Optional[str] = Field(
        default=None,
        description="Who is responsible for resolving? (agent or person)"
    )
    estimated_resolution_date: Optional[datetime] = Field(
        default=None,
        description="When do we expect this to be resolved?"
    )

    # Escalation
    escalated: bool = Field(
        default=False,
        description="Has this been escalated?"
    )
    escalated_to: Optional[str] = Field(
        default=None,
        description="Who was this escalated to?"
    )
    escalation_date: Optional[datetime] = Field(
        default=None,
        description="When was this escalated?"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent that created this blocker")
    resolved_at: Optional[datetime] = Field(default=None)

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"### 🚫 {self.title}",
            f"**Story:** {self.story_id}",
            f"**Type:** {self.blocker_type.value.upper()}",
            f"**Status:** {self.status.value.upper()}",
            "",
            self.description,
            "",
            "## Impact",
            f"- **Developer:** {self.developer_impact}",
        ]

        if self.business_impact:
            lines.append(f"- **Business:** {self.business_impact}")

        lines.extend([
            f"- **Days Blocked:** {self.days_blocked}",
            "",
        ])

        if self.resolution_plan:
            lines.extend([
                "## Resolution Plan",
                self.resolution_plan,
                "",
            ])

        if self.blocker_owner:
            lines.append(f"**Owner:** {self.blocker_owner}")

        if self.estimated_resolution_date:
            lines.append(f"**Est. Resolution:** {self.estimated_resolution_date.strftime('%Y-%m-%d')}")

        if self.escalated:
            lines.append("")
            lines.append("⚠️ **ESCALATED**")
            if self.escalated_to:
                lines.append(f"Escalated to: {self.escalated_to}")
            if self.escalation_date:
                lines.append(f"Escalated on: {self.escalation_date.strftime('%Y-%m-%d %H:%M')}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "story_id": self.story_id,
            "sprint_id": self.sprint_id,
            "blocker_type": self.blocker_type.value,
            "title": self.title,
            "description": self.description,
            "days_blocked": self.days_blocked,
            "developer_impact": self.developer_impact,
            "business_impact": self.business_impact,
            "status": self.status.value,
            "resolution_plan": self.resolution_plan,
            "blocker_owner": self.blocker_owner,
            "estimated_resolution_date": (
                self.estimated_resolution_date.isoformat() if self.estimated_resolution_date else None
            ),
            "escalated": self.escalated,
            "escalated_to": self.escalated_to,
            "escalation_date": self.escalation_date.isoformat() if self.escalation_date else None,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
