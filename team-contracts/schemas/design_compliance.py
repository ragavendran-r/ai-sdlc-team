"""DesignComplianceReport schema: design system compliance checking."""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ComplianceStatus(str, Enum):
    """Compliance status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"


class ComponentGap(BaseModel):
    """A missing component in the design system."""

    component_name: str = Field(...)
    requested_in_briefs: List[str] = Field(default_factory=list)
    closest_alternative: Optional[str] = Field(default=None)
    recommendation: str = Field(...)


class DesignComplianceReport(BaseModel):
    """
    DesignComplianceReport checks briefs against design system.

    Flags missing components and provides recommendations.
    """

    id: str = Field(...)
    total_briefs_checked: int = Field(..., ge=0)
    compliant_briefs: int = Field(default=0, ge=0)
    partial_briefs: int = Field(default=0, ge=0)
    non_compliant_briefs: int = Field(default=0, ge=0)

    # Findings
    component_gaps: List[ComponentGap] = Field(default_factory=list)
    compliance_percentage: float = Field(default=100.0)

    # Notes
    summary: str = Field(default="")
    recommendations: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(...)

    def to_markdown(self) -> str:
        """Convert to Markdown."""
        lines = [
            "# Design System Compliance Report",
            f"**Compliance: {self.compliance_percentage:.1f}%**",
            "",
            f"- Compliant: {self.compliant_briefs}/{self.total_briefs_checked}",
            f"- Partial: {self.partial_briefs}/{self.total_briefs_checked}",
            f"- Non-compliant: {self.non_compliant_briefs}/{self.total_briefs_checked}",
        ]

        if self.component_gaps:
            lines.extend(["", "## Component Gaps"])
            for gap in self.component_gaps:
                lines.append(f"\n### {gap.component_name}")
                lines.append(f"Used in: {', '.join(gap.requested_in_briefs)}")
                if gap.closest_alternative:
                    lines.append(f"Alternative: {gap.closest_alternative}")
                lines.append(f"Recommendation: {gap.recommendation}")

        if self.recommendations:
            lines.extend(["", "## Recommendations"])
            for rec in self.recommendations:
                lines.append(f"- {rec}")

        if self.summary:
            lines.extend(["", f"## Summary\n{self.summary}"])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "total_briefs_checked": self.total_briefs_checked,
            "compliant_briefs": self.compliant_briefs,
            "partial_briefs": self.partial_briefs,
            "non_compliant_briefs": self.non_compliant_briefs,
            "component_gaps": [{"component_name": g.component_name, "requested_in_briefs": g.requested_in_briefs, "closest_alternative": g.closest_alternative, "recommendation": g.recommendation} for g in self.component_gaps],
            "compliance_percentage": self.compliance_percentage,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
