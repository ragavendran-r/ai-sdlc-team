"""ScaffoldedComponent schema for component scaffolding in frontend workflow."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ScaffoldedComponent(BaseModel):
    """
    Generated React component boilerplate with full TSX content.

    Created by component_scaffolding agent. Contains the actual generated code
    for the component including props interface, styling hooks, API integration stubs,
    and placeholder content.
    """

    id: str = Field(..., description="Component ID")
    name: str = Field(..., description="Component name")
    file_path: str = Field(
        ...,
        description="Generated file path (e.g., 'src/components/LoginForm.tsx')"
    )

    # Generated code
    tsx_code: str = Field(..., description="Complete generated .tsx file content")
    props_interface: str = Field(..., description="Generated TypeScript props interface")
    hook_stubs: List[str] = Field(
        default_factory=list,
        description="Generated hook stub names (e.g., 'useLoginForm', 'useFetchUser')"
    )

    # Design system integration
    tokens_used: List[str] = Field(
        default_factory=list,
        description="Design tokens mapped to this component"
    )
    token_imports: str = Field(
        default="",
        description="Generated token import statement"
    )

    # API integration
    api_calls: List[str] = Field(
        default_factory=list,
        description="API endpoints this component calls (endpoint IDs)"
    )
    api_hook_stubs: List[str] = Field(
        default_factory=list,
        description="Generated API hook stubs (e.g., 'useLoginMutation')"
    )

    # State management
    local_state_variables: List[str] = Field(
        default_factory=list,
        description="useState hooks defined in component"
    )
    context_dependencies: List[str] = Field(
        default_factory=list,
        description="Context providers this component uses"
    )

    # Accessibility
    aria_attributes: List[str] = Field(
        default_factory=list,
        description="ARIA attributes added to component"
    )
    keyboard_handlers: List[str] = Field(
        default_factory=list,
        description="Keyboard event handlers implemented"
    )

    # Testing
    test_notes: Optional[str] = Field(default=None)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"## {self.name}",
            f"**File:** `{self.file_path}`",
            "",
            "### Generated Code",
            "```typescript",
            self.tsx_code[:200] + ("..." if len(self.tsx_code) > 200 else ""),
            "```",
        ]

        if self.props_interface:
            lines.extend(["", "### Props Interface", "```typescript", self.props_interface, "```"])

        if self.hook_stubs:
            lines.extend(["", "### Hooks to Implement"])
            for hook in self.hook_stubs:
                lines.append(f"- `{hook}`")

        if self.tokens_used:
            lines.extend(["", "### Design Tokens"])
            for token in self.tokens_used:
                lines.append(f"- `{token}`")

        if self.api_calls:
            lines.extend(["", "### API Dependencies"])
            for api in self.api_calls:
                lines.append(f"- `{api}`")

        if self.local_state_variables:
            lines.extend(["", "### Local State"])
            for state_var in self.local_state_variables:
                lines.append(f"- `{state_var}`")

        if self.context_dependencies:
            lines.extend(["", "### Context Dependencies"])
            for ctx in self.context_dependencies:
                lines.append(f"- `{ctx}`")

        if self.aria_attributes:
            lines.extend(["", "### Accessibility (ARIA)"])
            for attr in self.aria_attributes:
                lines.append(f"- `{attr}`")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "file_path": self.file_path,
            "tsx_code": self.tsx_code,
            "props_interface": self.props_interface,
            "hook_stubs": self.hook_stubs,
            "tokens_used": self.tokens_used,
            "token_imports": self.token_imports,
            "api_calls": self.api_calls,
            "api_hook_stubs": self.api_hook_stubs,
            "local_state_variables": self.local_state_variables,
            "context_dependencies": self.context_dependencies,
            "aria_attributes": self.aria_attributes,
            "keyboard_handlers": self.keyboard_handlers,
            "test_notes": self.test_notes,
            "created_at": self.created_at.isoformat(),
        }
