"""UXHandoff contract: UX/Design → Frontend workflow."""

from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field


class ComponentType(str, Enum):
    """Type of UI component."""
    FORM = "form"
    BUTTON = "button"
    CARD = "card"
    MODAL = "modal"
    NAVIGATION = "navigation"
    LIST = "list"
    TABLE = "table"
    CHART = "chart"
    CUSTOM = "custom"


class ResponsiveBreakpoint(str, Enum):
    """Standard responsive design breakpoints."""
    MOBILE = "mobile"      # < 640px
    TABLET = "tablet"      # 640px - 1024px
    DESKTOP = "desktop"    # > 1024px


class DesignToken(BaseModel):
    """A design token (color, spacing, typography, etc.)."""

    name: str = Field(..., description="Token name (e.g., 'color-primary')")
    category: str = Field(..., description="Category (color, spacing, typography, etc.)")
    value: str = Field(..., description="Token value (e.g., hex color, pixel size)")
    description: Optional[str] = Field(default=None, description="What this token is used for")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "value": self.value,
            "description": self.description,
        }


class InteractionSpec(BaseModel):
    """Specification for an interaction or animation."""

    name: str = Field(..., description="Interaction name (e.g., 'hover-effect')")
    trigger: str = Field(..., description="What triggers this (e.g., 'on-hover', 'on-click')")
    behavior: str = Field(..., description="What happens (e.g., 'fade-in', 'slide-up')")
    duration_ms: Optional[int] = Field(default=None, description="Animation duration in milliseconds")
    notes: Optional[str] = Field(default=None, description="Additional implementation notes")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "trigger": self.trigger,
            "behavior": self.behavior,
            "duration_ms": self.duration_ms,
            "notes": self.notes,
        }


class ResponsiveBehavior(BaseModel):
    """How a component behaves on different screen sizes."""

    breakpoint: ResponsiveBreakpoint = Field(..., description="Screen size breakpoint")
    layout: str = Field(..., description="Layout description for this breakpoint")
    visible: bool = Field(default=True, description="Is component visible at this breakpoint?")
    notes: Optional[str] = Field(default=None)

    def to_dict(self) -> dict:
        return {
            "breakpoint": self.breakpoint.value,
            "layout": self.layout,
            "visible": self.visible,
            "notes": self.notes,
        }


class ComponentSpec(BaseModel):
    """Complete specification for a UI component."""

    id: str = Field(..., description="Unique component identifier")
    name: str = Field(..., description="Component name (e.g., 'LoginForm')", min_length=2)
    component_type: ComponentType = Field(..., description="Type of component")
    description: str = Field(..., description="What does this component do?")

    # Visual design
    design_notes: str = Field(..., description="Visual design description")
    states: Dict[str, str] = Field(
        default_factory=dict,
        description="Component states (e.g., 'default', 'hover', 'active', 'disabled') and their appearance"
    )

    # Layout and sizing
    default_width: Optional[str] = Field(default=None, description="Default width (e.g., '100%', '300px')")
    default_height: Optional[str] = Field(default=None, description="Default height")
    padding: Optional[str] = Field(default=None, description="Internal padding")

    # Responsive behavior
    responsive_behaviors: List[ResponsiveBehavior] = Field(
        default_factory=list,
        description="How component behaves on different screen sizes"
    )

    # Content and props
    props: Dict[str, str] = Field(
        default_factory=dict,
        description="Required props and their descriptions"
    )
    slots: List[str] = Field(
        default_factory=list,
        description="Content slots the component accepts"
    )

    # Interactions
    interactions: List[InteractionSpec] = Field(
        default_factory=list,
        description="Interactions and animations"
    )

    # Accessibility
    accessibility_notes: Optional[str] = Field(
        default=None,
        description="Accessibility requirements (ARIA labels, keyboard navigation, etc.)"
    )

    # Related tokens
    design_tokens_used: List[str] = Field(
        default_factory=list,
        description="IDs of design tokens used in this component"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_markdown(self) -> str:
        """Convert to Markdown for human consumption."""
        lines = [
            f"## {self.name}",
            f"**ID:** `{self.id}` | **Type:** {self.component_type.value}",
            "",
            self.description,
            "",
            "### Design",
            self.design_notes,
        ]

        if self.states:
            lines.extend([
                "",
                "### States",
            ])
            for state, description in self.states.items():
                lines.append(f"- **{state}:** {description}")

        if self.responsive_behaviors:
            lines.extend([
                "",
                "### Responsive Behavior",
            ])
            for behavior in self.responsive_behaviors:
                lines.append(f"- **{behavior.breakpoint.value}:** {behavior.layout}")
                if not behavior.visible:
                    lines.append("  (hidden at this breakpoint)")

        if self.props:
            lines.extend([
                "",
                "### Props",
            ])
            for prop, description in self.props.items():
                lines.append(f"- `{prop}`: {description}")

        if self.interactions:
            lines.extend([
                "",
                "### Interactions",
            ])
            for interaction in self.interactions:
                lines.append(f"- **{interaction.name}:** {interaction.trigger} → {interaction.behavior}")
                if interaction.duration_ms:
                    lines.append(f"  ({interaction.duration_ms}ms)")

        if self.accessibility_notes:
            lines.extend([
                "",
                "### Accessibility",
                self.accessibility_notes,
            ])

        if self.design_tokens_used:
            lines.extend([
                "",
                "### Design Tokens",
            ])
            for token_id in self.design_tokens_used:
                lines.append(f"- `{token_id}`")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "name": self.name,
            "component_type": self.component_type.value,
            "description": self.description,
            "design_notes": self.design_notes,
            "states": self.states,
            "default_width": self.default_width,
            "default_height": self.default_height,
            "padding": self.padding,
            "responsive_behaviors": [b.to_dict() for b in self.responsive_behaviors],
            "props": self.props,
            "slots": self.slots,
            "interactions": [i.to_dict() for i in self.interactions],
            "accessibility_notes": self.accessibility_notes,
            "design_tokens_used": self.design_tokens_used,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class UXHandoff(BaseModel):
    """
    UXHandoff is the primary handoff contract from UX/Design workflow to Frontend workflow.

    It contains complete design specifications for one or more components,
    design system tokens, and interaction specifications needed for frontend implementation.
    """

    id: str = Field(..., description="Unique handoff identifier")
    user_story_id: str = Field(..., description="Reference to the user story")
    feature_name: str = Field(..., description="Feature name")

    # Component specs
    components: List[ComponentSpec] = Field(
        ...,
        description="All components needed for this feature",
        min_items=1
    )

    # Design system
    design_tokens: List[DesignToken] = Field(
        default_factory=list,
        description="Design tokens for colors, spacing, typography, etc."
    )

    # Design system references
    design_system_notes: Optional[str] = Field(
        default=None,
        description="Notes about design system usage, exceptions, or deviations"
    )

    # User flows
    user_flow_diagram: Optional[str] = Field(
        default=None,
        description="ASCII or text description of user flow through the feature"
    )

    # Accessibility and standards
    accessibility_requirements: List[str] = Field(
        default_factory=list,
        description="Overall accessibility requirements (WCAG level, specific needs, etc.)"
    )

    browser_support: Optional[str] = Field(
        default=None,
        description="Required browser support (e.g., 'Chrome 90+, Safari 14+, Firefox 88+')"
    )

    # Implementation notes
    implementation_notes: Optional[str] = Field(
        default=None,
        description="Special considerations for implementation"
    )

    # Approval and status
    approved: bool = Field(default=False, description="Has this been approved by stakeholders?")
    approved_by: Optional[str] = Field(default=None, description="Who approved (or will approve)")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent that created (typically 'ux-agent')")

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"# Design Handoff: {self.feature_name}",
            f"**ID:** {self.id}",
            f"**User Story:** {self.user_story_id}",
            f"**Status:** {'✅ Approved' if self.approved else '⏳ Pending Approval'}",
            "",
            "## Components",
        ]

        for component in self.components:
            lines.append(component.to_markdown())

        if self.design_tokens:
            lines.extend([
                "",
                "## Design Tokens",
            ])
            for token in self.design_tokens:
                lines.append(f"- `{token.name}`: {token.value} ({token.category})")
                if token.description:
                    lines.append(f"  {token.description}")

        if self.design_system_notes:
            lines.extend([
                "",
                "## Design System Notes",
                self.design_system_notes,
            ])

        if self.user_flow_diagram:
            lines.extend([
                "",
                "## User Flow",
                "```",
                self.user_flow_diagram,
                "```",
            ])

        if self.accessibility_requirements:
            lines.extend([
                "",
                "## Accessibility",
            ])
            for req in self.accessibility_requirements:
                lines.append(f"- {req}")

        if self.browser_support:
            lines.extend([
                "",
                "## Browser Support",
                self.browser_support,
            ])

        if self.implementation_notes:
            lines.extend([
                "",
                "## Implementation Notes",
                self.implementation_notes,
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
            "user_story_id": self.user_story_id,
            "feature_name": self.feature_name,
            "components": [c.to_dict() for c in self.components],
            "design_tokens": [t.to_dict() for t in self.design_tokens],
            "design_system_notes": self.design_system_notes,
            "user_flow_diagram": self.user_flow_diagram,
            "accessibility_requirements": self.accessibility_requirements,
            "browser_support": self.browser_support,
            "implementation_notes": self.implementation_notes,
            "approved": self.approved,
            "approved_by": self.approved_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
        }


if __name__ == "__main__":
    component = ComponentSpec(
        id="C-001",
        name="LoginForm",
        component_type=ComponentType.FORM,
        description="Login form with email and password fields",
        design_notes="Clean, minimal form with clear visual hierarchy. Primary button for submit.",
        states={
            "default": "Both fields empty, submit button disabled",
            "focus": "Focused field has blue border, label moves up",
            "filled": "Submit button enabled and highlighted",
            "loading": "Submit button shows spinner",
            "error": "Error message below field, red border and text",
        },
        props={
            "onSubmit": "Callback function when form is submitted",
            "isLoading": "Whether the form is processing submission",
        },
        interactions=[
            InteractionSpec(
                name="field-focus",
                trigger="on-focus",
                behavior="label-slides-up",
                duration_ms=200,
            )
        ],
        accessibility_notes="Form labeled with <label> tags. Error messages linked to fields with aria-describedby.",
    )

    token = DesignToken(
        name="color-primary",
        category="color",
        value="#3B82F6",
        description="Primary action color (blue)",
    )

    handoff = UXHandoff(
        id="UX-001",
        user_story_id="US-001",
        feature_name="User Login",
        components=[component],
        design_tokens=[token],
        accessibility_requirements=[
            "WCAG 2.1 AA compliance",
            "Keyboard navigation support",
            "Screen reader compatible",
        ],
        browser_support="Chrome 90+, Firefox 88+, Safari 14+, Edge 90+",
        created_by="ux-agent",
    )

    print(handoff.to_markdown())
