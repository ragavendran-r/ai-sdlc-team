"""UserStory handoff contract: PO → EM workflow."""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class Priority(str, Enum):
    """Feature priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Complexity(str, Enum):
    """Complexity estimation."""
    XS = "xs"
    S = "s"
    M = "m"
    L = "l"
    XL = "xl"


class UserStory(BaseModel):
    """
    UserStory represents a feature requirement from the Product Owner.

    This is the primary handoff contract from PO workflow to EM workflow.
    It contains all information needed for the EM to plan work and assign tasks.
    """

    id: str = Field(..., description="Unique user story identifier")
    title: str = Field(..., description="Short title of the user story", min_length=5, max_length=200)
    description: str = Field(..., description="Full description of what needs to be built", min_length=20)

    # User and context
    user_role: str = Field(..., description="Who is the user? (e.g., 'Customer', 'Admin')")
    user_goal: str = Field(..., description="What does the user want to accomplish?")
    business_value: str = Field(..., description="Why is this valuable to the business?")

    # Acceptance criteria
    acceptance_criteria: List[str] = Field(
        ...,
        description="Specific, testable criteria for completion",
        min_items=1
    )

    # Planning metadata
    priority: Priority = Field(..., description="Business priority")
    estimated_complexity: Complexity = Field(..., description="Rough effort estimate")

    # Dependencies
    depends_on: List[str] = Field(
        default_factory=list,
        description="IDs of user stories that must be completed first"
    )
    related_stories: List[str] = Field(
        default_factory=list,
        description="IDs of related user stories"
    )

    # Context
    context_and_notes: Optional[str] = Field(
        default=None,
        description="Additional context, constraints, or notes"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent that created this story (typically 'po-agent')")

    @field_validator('acceptance_criteria')
    @classmethod
    def validate_criteria(cls, v: List[str]) -> List[str]:
        """Ensure all acceptance criteria are non-empty."""
        for criterion in v:
            if not criterion.strip():
                raise ValueError("Acceptance criteria cannot be empty strings")
        return [c.strip() for c in v]

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown format."""
        lines = [
            f"# User Story: {self.title}",
            f"**ID:** {self.id}",
            f"**Priority:** {self.priority.value.upper()}",
            f"**Complexity:** {self.estimated_complexity.value.upper()}",
            "",
            "## User Need",
            f"As a **{self.user_role}**, I want to **{self.user_goal}** so that **{self.business_value}**.",
            "",
            "## Description",
            self.description,
            "",
            "## Acceptance Criteria",
        ]

        for i, criterion in enumerate(self.acceptance_criteria, 1):
            lines.append(f"{i}. {criterion}")

        if self.depends_on:
            lines.extend([
                "",
                "## Dependencies",
                "This story depends on completion of:",
            ])
            for dep_id in self.depends_on:
                lines.append(f"- `{dep_id}`")

        if self.related_stories:
            lines.extend([
                "",
                "## Related Stories",
            ])
            for related_id in self.related_stories:
                lines.append(f"- `{related_id}`")

        if self.context_and_notes:
            lines.extend([
                "",
                "## Notes",
                self.context_and_notes,
            ])

        lines.extend([
            "",
            f"**Created:** {self.created_at.isoformat()}",
            f"**Last Updated:** {self.updated_at.isoformat()}",
            f"**Created By:** {self.created_by}",
        ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "user_role": self.user_role,
            "user_goal": self.user_goal,
            "business_value": self.business_value,
            "acceptance_criteria": self.acceptance_criteria,
            "priority": self.priority.value,
            "estimated_complexity": self.estimated_complexity.value,
            "depends_on": self.depends_on,
            "related_stories": self.related_stories,
            "context_and_notes": self.context_and_notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
        }


if __name__ == "__main__":
    # Example usage
    story = UserStory(
        id="US-001",
        title="User login with email and password",
        description="Users should be able to log in to the application using their email address and password.",
        user_role="Customer",
        user_goal="log in to my account securely",
        business_value="secure user authentication enables personalized experiences and data protection",
        acceptance_criteria=[
            "User can enter email and password",
            "Valid credentials log in successfully",
            "Invalid credentials show error message",
            "Password is never displayed in plain text",
            "Failed login attempts are logged",
        ],
        priority=Priority.HIGH,
        estimated_complexity=Complexity.M,
        created_by="po-agent",
    )

    print(story.to_markdown())
    print("\n" + "="*60 + "\n")
    print(story.to_dict())
