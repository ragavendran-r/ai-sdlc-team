"""StatePlan schema for state management planning in frontend workflow."""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class StateManagementType(str, Enum):
    """State management approach for a component group."""
    LOCAL_STATE = "local_state"
    CONTEXT_API = "context_api"
    REDUX = "redux"
    ZUSTAND = "zustand"
    JOTAI = "jotai"
    RECOIL = "recoil"


class StateGroup(BaseModel):
    """Group of components sharing state management strategy."""

    id: str = Field(..., description="Group identifier")
    name: str = Field(..., description="Group name (e.g., 'Authentication')")
    components: List[str] = Field(
        ...,
        min_items=1,
        description="Component IDs in this group"
    )

    # State management approach
    recommended_strategy: StateManagementType = Field(
        ...,
        description="Recommended state management approach"
    )
    rationale: str = Field(
        ...,
        description="Why this approach for this group"
    )

    # Shared state properties
    shared_state_properties: List[str] = Field(
        default_factory=list,
        description="State properties shared across components"
    )

    # Actions/mutations
    actions: List[str] = Field(
        default_factory=list,
        description="Actions or mutations for this state"
    )

    # Implementation notes
    implementation_notes: Optional[str] = Field(default=None)

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"### {self.name}",
            f"**ID:** `{self.id}`",
            f"**Strategy:** {self.recommended_strategy.value}",
            "",
            f"**Components:** {', '.join(f'`{c}`' for c in self.components)}",
            "",
            f"**Rationale:** {self.rationale}",
        ]

        if self.shared_state_properties:
            lines.extend(["", "**Shared State:**"])
            for prop in self.shared_state_properties:
                lines.append(f"- {prop}")

        if self.actions:
            lines.extend(["", "**Actions:**"])
            for action in self.actions:
                lines.append(f"- {action}")

        if self.implementation_notes:
            lines.extend(["", "**Implementation Notes:**", self.implementation_notes])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "components": self.components,
            "recommended_strategy": self.recommended_strategy.value,
            "rationale": self.rationale,
            "shared_state_properties": self.shared_state_properties,
            "actions": self.actions,
            "implementation_notes": self.implementation_notes,
        }


class StatePlan(BaseModel):
    """
    Complete state management plan for all components.

    Created by state_management agent. Identifies groups of components
    that share state and recommends state management approach for each group.
    """

    id: str = Field(..., description="Plan identifier")
    title: str = Field(..., description="Plan title")

    # State groups
    state_groups: List[StateGroup] = Field(
        ...,
        min_items=1,
        description="Groups of components with shared state management"
    )

    # Global state
    requires_global_state_store: bool = Field(
        default=False,
        description="Does the app need a global state store?"
    )
    global_store_recommendation: Optional[str] = Field(
        default=None,
        description="Recommended global store (Redux, Zustand, etc.)"
    )
    global_store_rationale: Optional[str] = Field(default=None)

    # Context layers
    recommended_context_layers: List[str] = Field(
        default_factory=list,
        description="Context providers to create (e.g., 'AuthContext', 'ThemeContext')"
    )

    # API layer
    api_layer_needed: bool = Field(
        default=True,
        description="Should separate API/data layer be created?"
    )
    api_layer_pattern: str = Field(
        default="hooks",
        description="Pattern for API layer (hooks, services, RTK Query, etc.)"
    )

    # Implementation roadmap
    implementation_order: List[str] = Field(
        default_factory=list,
        description="Recommended order to implement state groups"
    )

    # General notes
    general_notes: Optional[str] = Field(default=None)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"# {self.title}",
            f"**ID:** {self.id}",
            "",
        ]

        if self.global_store_recommendation:
            lines.extend([
                "## Global State Store",
                f"**Recommendation:** {self.global_store_recommendation}",
                f"**Rationale:** {self.global_store_rationale}",
                "",
            ])

        if self.recommended_context_layers:
            lines.extend([
                "## Context Providers to Create",
            ])
            for ctx in self.recommended_context_layers:
                lines.append(f"- {ctx}")
            lines.append("")

        lines.append("## State Groups")
        for group in self.state_groups:
            lines.append(group.to_markdown())

        if self.implementation_order:
            lines.extend([
                "",
                "## Implementation Order",
            ])
            for i, group_id in enumerate(self.implementation_order, 1):
                lines.append(f"{i}. `{group_id}`")

        if self.general_notes:
            lines.extend(["", "## Notes", self.general_notes])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "state_groups": [g.to_dict() for g in self.state_groups],
            "requires_global_state_store": self.requires_global_state_store,
            "global_store_recommendation": self.global_store_recommendation,
            "global_store_rationale": self.global_store_rationale,
            "recommended_context_layers": self.recommended_context_layers,
            "api_layer_needed": self.api_layer_needed,
            "api_layer_pattern": self.api_layer_pattern,
            "implementation_order": self.implementation_order,
            "general_notes": self.general_notes,
            "created_at": self.created_at.isoformat(),
        }
