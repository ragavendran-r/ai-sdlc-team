"""ValidationModule schema for backend agent."""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class ValidatorFunction(BaseModel):
    """A single validator function."""

    name: str = Field(..., description="Validator function name")
    field_name: str = Field(..., description="Field being validated")
    rule: str = Field(..., description="Validation rule description")
    python_code: str = Field(..., description="Pydantic validator Python code")
    error_message: str = Field(..., description="Error message if validation fails")


class ValidationModule(BaseModel):
    """Generated Pydantic validation code for a request schema."""

    id: str = Field(..., description="Module identifier")
    request_name: str = Field(..., description="Request model name")
    endpoint_id: str = Field(..., description="API endpoint this validates")

    # Generated code
    python_code: str = Field(..., description="Complete Pydantic model with validators")

    # Validators
    validators: List[ValidatorFunction] = Field(
        default_factory=list,
        description="Individual validator functions"
    )

    # Validation rules
    rules: List[str] = Field(
        ...,
        description="Validation rules this implements",
        min_items=1
    )

    # Test cases
    test_cases: List[dict] = Field(
        default_factory=list,
        description="Example valid and invalid payloads"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent creating this")

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"## {self.request_name}",
            f"**ID:** {self.id}",
            f"**Endpoint:** {self.endpoint_id}",
            "",
            "### Validation Rules",
        ]

        for rule in self.rules:
            lines.append(f"- {rule}")

        lines.extend([
            "",
            "### Implementation",
            "```python",
            self.python_code,
            "```",
        ])

        if self.test_cases:
            lines.extend([
                "",
                "### Test Cases",
                "```json",
            ])
            import json
            for i, test in enumerate(self.test_cases):
                lines.append(f"# Test case {i+1}")
                lines.append(json.dumps(test, indent=2))
            lines.append("```")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent consumption."""
        return {
            "id": self.id,
            "request_name": self.request_name,
            "endpoint_id": self.endpoint_id,
            "python_code": self.python_code,
            "validators": [
                {
                    "name": v.name,
                    "field_name": v.field_name,
                    "rule": v.rule,
                    "python_code": v.python_code,
                    "error_message": v.error_message,
                }
                for v in self.validators
            ],
            "rules": self.rules,
            "test_cases": self.test_cases,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
