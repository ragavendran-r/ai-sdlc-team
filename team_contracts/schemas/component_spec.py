"""ComponentSpec schema for component breakdown in frontend workflow."""

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ComponentSpec(BaseModel):
    """
    Complete specification for a component breakdown item.

    Created by component_breakdown agent from UX handoff components.
    Identifies atomic components and whether they are new builds or library reuse.
    """

    id: str = Field(..., description="Unique component identifier")
    name: str = Field(..., description="Component name (e.g., 'LoginForm')")
    parent_screen: str = Field(..., description="Screen/wireframe this belongs to")

    # Component type and nature
    component_type: str = Field(..., description="Type (form, button, card, modal, etc.)")
    is_new_build: bool = Field(
        ...,
        description="True if new component, False if reuses library component"
    )
    library_component_id: Optional[str] = Field(
        default=None,
        description="ID of library component to reuse (if not new build)"
    )

    # Scope and complexity
    description: str = Field(..., description="What this component does")
    estimated_lines_of_code: int = Field(..., gt=0, description="Estimated LOC")
    complexity: str = Field(
        ...,
        description="Complexity level: simple, moderate, complex"
    )

    # Required props
    props: Dict[str, str] = Field(
        default_factory=dict,
        description="Required props and their types"
    )

    # State requirements
    requires_local_state: bool = Field(default=False)
    requires_context_state: bool = Field(default=False)
    requires_global_state: bool = Field(default=False)
    state_properties: List[str] = Field(
        default_factory=list,
        description="State properties this component needs"
    )

    # API dependencies
    api_dependencies: List[str] = Field(
        default_factory=list,
        description="API endpoint IDs this component depends on"
    )

    # Accessibility requirements
    a11y_requirements: List[str] = Field(
        default_factory=list,
        description="Accessibility requirements"
    )

    # Testing notes
    testing_notes: Optional[str] = Field(default=None)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"### {self.name}",
            f"**ID:** `{self.id}` | **Parent:** {self.parent_screen}",
            f"**Type:** {self.component_type} | **Status:** "
            f"{'New Build' if self.is_new_build else f'Reuse (#{self.library_component_id})'}",
            "",
            self.description,
            "",
            f"**Complexity:** {self.complexity}",
            f"**Estimated LOC:** {self.estimated_lines_of_code}",
        ]

        if self.props:
            lines.extend(["", "**Props:**"])
            for prop_name, prop_type in self.props.items():
                lines.append(f"- `{prop_name}`: {prop_type}")

        if self.api_dependencies:
            lines.extend(["", "**API Dependencies:**"])
            for api_id in self.api_dependencies:
                lines.append(f"- `{api_id}`")

        state_needs = []
        if self.requires_local_state:
            state_needs.append("local state")
        if self.requires_context_state:
            state_needs.append("context")
        if self.requires_global_state:
            state_needs.append("global store")

        if state_needs:
            lines.append("")
            lines.append(f"**State:** {', '.join(state_needs)}")
            if self.state_properties:
                for prop in self.state_properties:
                    lines.append(f"  - {prop}")

        if self.a11y_requirements:
            lines.extend(["", "**Accessibility:**"])
            for req in self.a11y_requirements:
                lines.append(f"- {req}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "parent_screen": self.parent_screen,
            "component_type": self.component_type,
            "is_new_build": self.is_new_build,
            "library_component_id": self.library_component_id,
            "description": self.description,
            "estimated_lines_of_code": self.estimated_lines_of_code,
            "complexity": self.complexity,
            "props": self.props,
            "requires_local_state": self.requires_local_state,
            "requires_context_state": self.requires_context_state,
            "requires_global_state": self.requires_global_state,
            "state_properties": self.state_properties,
            "api_dependencies": self.api_dependencies,
            "a11y_requirements": self.a11y_requirements,
            "testing_notes": self.testing_notes,
            "created_at": self.created_at.isoformat(),
        }
