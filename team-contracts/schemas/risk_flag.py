"""RiskFlag schema: risk identification in sprint planning."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class RiskSeverity(str, Enum):
    """Risk severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(str, Enum):
    """Types of risks in sprint planning."""
    COMPLEXITY = "complexity"              # Story is too complex
    DEPENDENCY = "dependency"              # Unknown/risky dependencies
    CAPACITY = "capacity"                  # Risk of overrun
    TECHNICAL = "technical"                # Technical risk
    RESOURCE = "resource"                  # Resource availability risk
    INTEGRATION = "integration"            # Integration risk
    PERFORMANCE = "performance"            # Performance risk
    SECURITY = "security"                  # Security risk


class RiskFlag(BaseModel):
    """
    RiskFlag identifies potential risks in sprint planning.

    Flags stories or sprints that need attention or mitigation.
    """

    id: str = Field(..., description="Unique risk flag identifier")
    story_id: str = Field(..., description="Story this risk is associated with")
    risk_type: RiskType = Field(..., description="Type of risk")
    severity: RiskSeverity = Field(..., description="Risk severity level")

    # Description
    title: str = Field(..., description="Short risk title")
    description: str = Field(..., description="Detailed risk description")

    # Mitigation
    mitigation: Optional[str] = Field(
        default=None,
        description="Suggested mitigation strategy"
    )
    mitigation_effort_hours: Optional[float] = Field(
        default=None,
        description="Hours needed for mitigation",
        ge=0
    )

    # Impact
    impact: str = Field(
        ...,
        description="What happens if this risk occurs?"
    )

    # Responsibility
    owner: Optional[str] = Field(
        default=None,
        description="Who owns this risk (agent or person)"
    )

    # Status
    status: str = Field(
        default="open",
        description="Risk status (open, mitigated, accepted, resolved)"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent that created this flag")

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"### ⚠️ {self.title}",
            f"**Story:** {self.story_id}",
            f"**Type:** {self.risk_type.value.upper()}",
            f"**Severity:** {self.severity.value.upper()}",
            "",
            self.description,
            "",
        ]

        if self.mitigation:
            lines.extend([
                "**Mitigation:**",
                self.mitigation,
                "",
            ])

            if self.mitigation_effort_hours:
                lines.append(f"Effort: {self.mitigation_effort_hours}h")
                lines.append("")

        lines.extend([
            "**Impact:**",
            self.impact,
            "",
        ])

        if self.owner:
            lines.append(f"**Owner:** {self.owner}")

        lines.append(f"**Status:** {self.status.upper()}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "story_id": self.story_id,
            "risk_type": self.risk_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "mitigation": self.mitigation,
            "mitigation_effort_hours": self.mitigation_effort_hours,
            "impact": self.impact,
            "owner": self.owner,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
