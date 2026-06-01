"""WireframeBrief schema: wireframe specifications for screens."""

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ComponentRequirement(BaseModel):
    """A component needed on the screen."""

    component_name: str = Field(...)
    purpose: str = Field(...)
    content: Optional[str] = Field(default=None)
    state: Optional[str] = Field(default=None, description="Initial state (default, active, disabled, etc.)")


class InteractionPattern(BaseModel):
    """An interaction pattern on the screen."""

    trigger: str = Field(..., description="What triggers this")
    action: str = Field(..., description="What happens")
    result: str = Field(..., description="Expected result")


class WireframeBrief(BaseModel):
    """
    WireframeBrief is a structured spec for a single screen.

    Describes components, content, interactions, and layout.
    Not visual design, but structural specifications.
    """

    id: str = Field(..., description="Screen identifier")
    screen_name: str = Field(..., description="Screen name")
    user_flow_id: str = Field(..., description="Which flow this screen appears in")

    # Structure
    purpose: str = Field(..., description="Purpose of this screen")
    description: str = Field(...)

    # Components and content
    components: List[ComponentRequirement] = Field(..., description="Components needed")
    content_requirements: List[str] = Field(default_factory=list)
    interactions: List[InteractionPattern] = Field(default_factory=list)

    # Layout
    layout_type: str = Field(default="standard", description="Layout pattern (standard, modal, side-panel, etc.)")
    viewport_sizes: List[str] = Field(default_factory=list, description="Supported viewports (mobile, tablet, desktop)")

    # Design system mapping
    design_system_mappings: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of briefs components to actual DS components"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent")

    def to_markdown(self) -> str:
        """Convert to Markdown."""
        lines = [
            f"### {self.screen_name}",
            f"**Purpose:** {self.purpose}",
            "",
            self.description,
            "",
            "#### Components",
        ]

        for comp in self.components:
            lines.append(f"- **{comp.component_name}** - {comp.purpose}")
            if comp.content:
                lines.append(f"  Content: {comp.content}")
            if comp.state:
                lines.append(f"  State: {comp.state}")

        if self.interactions:
            lines.extend(["", "#### Interactions"])
            for inter in self.interactions:
                lines.append(f"- {inter.trigger} → {inter.action} → {inter.result}")

        if self.content_requirements:
            lines.extend(["", "#### Content Requirements"])
            for req in self.content_requirements:
                lines.append(f"- {req}")

        if self.design_system_mappings:
            lines.extend(["", "#### Design System Mappings"])
            for brief_comp, ds_comp in self.design_system_mappings.items():
                lines.append(f"- {brief_comp} → {ds_comp}")

        lines.append(f"\n**Supports:** {', '.join(self.viewport_sizes) if self.viewport_sizes else 'All'}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "screen_name": self.screen_name,
            "user_flow_id": self.user_flow_id,
            "purpose": self.purpose,
            "description": self.description,
            "components": [
                {
                    "component_name": c.component_name,
                    "purpose": c.purpose,
                    "content": c.content,
                    "state": c.state,
                }
                for c in self.components
            ],
            "content_requirements": self.content_requirements,
            "interactions": [
                {
                    "trigger": i.trigger,
                    "action": i.action,
                    "result": i.result,
                }
                for i in self.interactions
            ],
            "layout_type": self.layout_type,
            "viewport_sizes": self.viewport_sizes,
            "design_system_mappings": self.design_system_mappings,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
