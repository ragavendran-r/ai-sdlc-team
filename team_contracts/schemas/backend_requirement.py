"""BackendRequirement schema for backend agent."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class RequirementType(str, Enum):
    """Types of backend requirements."""
    DATA_PERSISTENCE = "data_persistence"
    BUSINESS_LOGIC = "business_logic"
    API_ENDPOINT = "api_endpoint"
    INTEGRATION = "integration"
    SECURITY = "security"
    VALIDATION = "validation"


class BackendRequirement(BaseModel):
    """Backend requirement extracted from user story."""

    id: str = Field(..., description="Unique requirement identifier")
    user_story_id: str = Field(..., description="Parent user story ID")
    title: str = Field(..., description="Requirement title")
    description: str = Field(..., description="Full description")

    # Classification
    requirement_type: RequirementType = Field(..., description="Type of requirement")

    # Data requirements
    data_needs: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Data model needs"
    )
    business_rules: List[str] = Field(
        default_factory=list,
        description="Business rules to enforce"
    )

    # Integration requirements
    external_integrations: List[str] = Field(
        default_factory=list,
        description="Third-party integrations needed"
    )
    internal_dependencies: List[str] = Field(
        default_factory=list,
        description="Dependencies on other system components"
    )

    # Implementation notes
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description="How to validate this requirement"
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Constraints or limitations"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent creating this requirement")

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"## {self.title}",
            f"**ID:** {self.id}",
            f"**Type:** {self.requirement_type.value}",
            f"**User Story:** {self.user_story_id}",
            "",
            self.description,
        ]

        if self.business_rules:
            lines.extend(["", "### Business Rules"])
            for rule in self.business_rules:
                lines.append(f"- {rule}")

        if self.data_needs:
            lines.extend(["", "### Data Needs"])
            import json
            lines.append("```json")
            lines.append(json.dumps(self.data_needs, indent=2))
            lines.append("```")

        if self.external_integrations:
            lines.extend(["", "### External Integrations"])
            for integration in self.external_integrations:
                lines.append(f"- {integration}")

        if self.constraints:
            lines.extend(["", "### Constraints"])
            for constraint in self.constraints:
                lines.append(f"- {constraint}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "user_story_id": self.user_story_id,
            "title": self.title,
            "description": self.description,
            "requirement_type": self.requirement_type.value,
            "data_needs": self.data_needs,
            "business_rules": self.business_rules,
            "external_integrations": self.external_integrations,
            "internal_dependencies": self.internal_dependencies,
            "acceptance_criteria": self.acceptance_criteria,
            "constraints": self.constraints,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
