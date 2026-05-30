"""TestFile schema for unit test generation in frontend workflow."""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class TestType(str, Enum):
    """Type of test."""
    RENDER = "render"
    INTERACTION = "interaction"
    API = "api"
    STATE = "state"
    ACCESSIBILITY = "accessibility"
    SNAPSHOT = "snapshot"


class TestCase(BaseModel):
    """Individual test case."""

    name: str = Field(..., description="Test case name")
    type: TestType = Field(..., description="Type of test")
    description: str = Field(..., description="What this test verifies")
    code_snippet: str = Field(..., description="Generated test code")
    mocks_required: List[str] = Field(
        default_factory=list,
        description="Functions/modules to mock (e.g., 'useLoginMutation')"
    )

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        return f"- **{self.name}** ({self.type.value}): {self.description}"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "code_snippet": self.code_snippet,
            "mocks_required": self.mocks_required,
        }


class TestFile(BaseModel):
    """
    Generated unit test file for a component.

    Created by unit_test_generation agent. Contains complete test stubs
    for render tests, interaction tests, and API mock tests.
    """

    id: str = Field(..., description="Test file identifier")
    component_id: str = Field(..., description="Component being tested")
    component_name: str = Field(..., description="Component name")
    file_path: str = Field(
        ...,
        description="Generated test file path (e.g., 'src/components/__tests__/LoginForm.test.tsx')"
    )

    # Test setup
    imports: str = Field(..., description="Generated import statements")
    setup_code: str = Field(..., description="Test setup (describe block, setup functions)")

    # Test cases
    test_cases: List[TestCase] = Field(
        ...,
        min_items=1,
        description="Individual test cases"
    )

    # Mocks
    mock_definitions: str = Field(
        default="",
        description="Generated mock definitions"
    )

    # Generated test file
    complete_test_code: str = Field(..., description="Complete generated .test.tsx file content")

    # Coverage notes
    coverage_notes: Optional[str] = Field(default=None)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_markdown(self) -> str:
        """Convert to human-readable Markdown."""
        lines = [
            f"## {self.component_name}",
            f"**File:** `{self.file_path}`",
            "",
            "### Test Cases",
        ]

        for test in self.test_cases:
            lines.append(test.to_markdown())

        if self.coverage_notes:
            lines.extend(["", "### Coverage Notes", self.coverage_notes])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "component_id": self.component_id,
            "component_name": self.component_name,
            "file_path": self.file_path,
            "imports": self.imports,
            "setup_code": self.setup_code,
            "test_cases": [tc.to_dict() for tc in self.test_cases],
            "mock_definitions": self.mock_definitions,
            "complete_test_code": self.complete_test_code,
            "coverage_notes": self.coverage_notes,
            "created_at": self.created_at.isoformat(),
        }
