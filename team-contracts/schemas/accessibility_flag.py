"""AccessibilityFlag schema: WCAG accessibility issues."""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class WCAGLevel(str, Enum):
    """WCAG compliance level."""
    A = "a"
    AA = "aa"
    AAA = "aaa"


class AccessibilitySeverity(str, Enum):
    """Severity of accessibility issue."""
    BLOCKER = "blocker"
    MAJOR = "major"
    MINOR = "minor"
    NOTE = "note"


class AccessibilityFlag(BaseModel):
    """
    AccessibilityFlag identifies WCAG accessibility issues.

    Flags potential problems in proposed interactions and content.
    """

    id: str = Field(...)
    brief_id: str = Field(...)
    flow_id: Optional[str] = Field(default=None)

    # Issue details
    title: str = Field(...)
    description: str = Field(...)
    wcag_criterion: str = Field(..., description="WCAG criterion (e.g., 1.4.3 Contrast)")
    wcag_level: WCAGLevel = Field(default=WCAGLevel.AA)
    severity: AccessibilitySeverity = Field(...)

    # Guidance
    problem: str = Field(...)
    solution: str = Field(...)
    example: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(...)

    def to_markdown(self) -> str:
        """Convert to Markdown."""
        severity_icon = {
            "blocker": "🚫",
            "major": "⚠️",
            "minor": "💡",
            "note": "ℹ️",
        }

        lines = [
            f"{severity_icon.get(self.severity.value, '')} **{self.title}**",
            f"**Brief:** {self.brief_id}",
            f"**WCAG:** {self.wcag_criterion} ({self.wcag_level.value.upper()})",
            f"**Severity:** {self.severity.value.upper()}",
            "",
            f"**Problem:** {self.problem}",
            "",
            f"**Solution:** {self.solution}",
        ]

        if self.example:
            lines.extend(["", f"**Example:** {self.example}"])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "brief_id": self.brief_id,
            "flow_id": self.flow_id,
            "title": self.title,
            "description": self.description,
            "wcag_criterion": self.wcag_criterion,
            "wcag_level": self.wcag_level.value,
            "severity": self.severity.value,
            "problem": self.problem,
            "solution": self.solution,
            "example": self.example,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
