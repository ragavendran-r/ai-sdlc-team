"""ServiceScaffold schema for backend agent."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class MethodStub(BaseModel):
    """Method stub for a service method."""

    name: str = Field(..., description="Method name")
    description: str = Field(..., description="What this method does")
    parameters: List[str] = Field(
        default_factory=list,
        description="Method parameters with types"
    )
    return_type: str = Field(..., description="Return type")
    business_rules: List[str] = Field(
        default_factory=list,
        description="Business rules this method must implement"
    )
    docstring: str = Field(..., description="Python docstring for the method")


class ServiceScaffold(BaseModel):
    """Service layer scaffold for a domain entity."""

    id: str = Field(..., description="Scaffold identifier")
    entity_name: str = Field(..., description="Domain entity this serves")
    class_name: str = Field(..., description="Service class name")

    # Generated code
    python_code: str = Field(..., description="Complete Python service class code")

    # Method stubs
    methods: List[MethodStub] = Field(
        ...,
        description="Method stubs in this service",
        min_items=1
    )

    # Dependencies
    dependencies: List[str] = Field(
        default_factory=list,
        description="External dependencies (imports)"
    )

    # Database operations
    database_queries: List[str] = Field(
        default_factory=list,
        description="Database queries this service uses"
    )

    # Error handling
    error_types: List[str] = Field(
        default_factory=list,
        description="Custom exception types to handle"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent creating this")

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"## {self.class_name}",
            f"**ID:** {self.id}",
            f"**Entity:** {self.entity_name}",
            "",
            "### Methods",
        ]

        for method in self.methods:
            lines.extend([
                f"- `{method.name}({', '.join(method.parameters)}) -> {method.return_type}`",
                f"  {method.description}",
            ])
            if method.business_rules:
                for rule in method.business_rules:
                    lines.append(f"  - {rule}")

        lines.extend([
            "",
            "### Implementation",
            "```python",
            self.python_code,
            "```",
        ])

        if self.error_types:
            lines.extend(["", "### Error Types"])
            for error in self.error_types:
                lines.append(f"- {error}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "entity_name": self.entity_name,
            "class_name": self.class_name,
            "python_code": self.python_code,
            "methods": [
                {
                    "name": m.name,
                    "description": m.description,
                    "parameters": m.parameters,
                    "return_type": m.return_type,
                    "business_rules": m.business_rules,
                    "docstring": m.docstring,
                }
                for m in self.methods
            ],
            "dependencies": self.dependencies,
            "database_queries": self.database_queries,
            "error_types": self.error_types,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
