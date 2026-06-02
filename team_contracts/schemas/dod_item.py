"""DoDItem schema: Definition of Done checklist items."""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class DoDCategory(str, Enum):
    """Categories of Definition of Done items."""
    CODE = "code"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REVIEW = "review"
    INTEGRATION = "integration"
    DEPLOYMENT = "deployment"
    SECURITY = "security"
    PERFORMANCE = "performance"


class DoDItem(BaseModel):
    """
    DoDItem represents a single item in the Definition of Done checklist.

    Used to define what "done" means for stories in a sprint.
    """

    id: str = Field(..., description="Unique item identifier")
    category: DoDCategory = Field(..., description="Category of DoD item")

    # Content
    description: str = Field(..., description="What must be done?")
    acceptance_criteria: str = Field(
        ...,
        description="How do we verify it's done?"
    )

    # Applicability
    applies_to_story_types: List[str] = Field(
        default_factory=list,
        description="Story types this applies to (e.g., 'feature', 'bug', 'infrastructure')"
    )
    applies_to_all: bool = Field(
        default=False,
        description="If true, applies to all stories in this sprint"
    )

    # Details
    mandatory: bool = Field(
        default=True,
        description="Is this item mandatory or optional?"
    )
    effort_estimate_hours: Optional[float] = Field(
        default=None,
        description="Estimated hours for this item",
        ge=0
    )

    # Notes
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes or context"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent that created this item")

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        checkbox = "✅" if self.mandatory else "○"

        lines = [
            f"{checkbox} {self.description}",
            f"   **Category:** {self.category.value}",
            f"   **Acceptance:** {self.acceptance_criteria}",
        ]

        if self.effort_estimate_hours:
            lines.append(f"   **Effort:** {self.effort_estimate_hours}h")

        if self.applies_to_story_types:
            types_str = ", ".join(self.applies_to_story_types)
            lines.append(f"   **Applies to:** {types_str}")
        elif self.applies_to_all:
            lines.append("   **Applies to:** All stories")

        if self.notes:
            lines.append(f"   **Notes:** {self.notes}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "category": self.category.value,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "applies_to_story_types": self.applies_to_story_types,
            "applies_to_all": self.applies_to_all,
            "mandatory": self.mandatory,
            "effort_estimate_hours": self.effort_estimate_hours,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }


class DefinitionOfDone(BaseModel):
    """
    DefinitionOfDone is a complete checklist for sprint completion.

    Groups DoD items by category and tracks applicability.
    """

    id: str = Field(..., description="Unique DoD identifier")
    sprint_id: Optional[str] = Field(default=None, description="Sprint this DoD is for")

    # Items
    items: List[DoDItem] = Field(
        ...,
        description="All DoD checklist items",
        min_items=1
    )

    # Metadata
    total_effort_hours: Optional[float] = Field(
        default=None,
        description="Total effort estimated across all mandatory items"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent that created this DoD")

    def get_items_by_category(self) -> dict:
        """Group items by category."""
        grouped = {}
        for item in self.items:
            cat = item.category.value
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(item)
        return grouped

    def get_mandatory_items(self) -> List[DoDItem]:
        """Get only mandatory items."""
        return [item for item in self.items if item.mandatory]

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown checklist."""
        lines = [
            "# Definition of Done",
            f"**Sprint:** {self.sprint_id or 'General'}",
            "",
        ]

        grouped = self.get_items_by_category()

        for category in sorted(grouped.keys()):
            items = grouped[category]
            lines.append(f"## {category.title()}")
            lines.append("")

            for item in items:
                lines.append(item.to_markdown())
                lines.append("")

        if self.total_effort_hours:
            lines.extend([
                "---",
                f"**Total Estimated Effort:** {self.total_effort_hours}h",
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
            "items": [item.to_dict() for item in self.items],
            "total_effort_hours": self.total_effort_hours,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
