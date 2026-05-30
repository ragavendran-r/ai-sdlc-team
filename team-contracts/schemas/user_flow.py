"""UserFlow schema: user flows for UX design."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class FlowStep(BaseModel):
    """A single step in a user flow."""

    step_number: int = Field(..., description="Step number in sequence")
    action: str = Field(..., description="What the user does")
    system_response: str = Field(..., description="What the system does")
    screen_or_state: Optional[str] = Field(default=None, description="Screen/state shown")


class DecisionPoint(BaseModel):
    """A decision point in the flow."""

    step_number: int = Field(..., description="Where decision occurs")
    question: str = Field(..., description="What decision must be made?")
    option_a: str = Field(..., description="First option")
    option_b: str = Field(..., description="Second option")
    other_options: List[str] = Field(default_factory=list)


class UserFlow(BaseModel):
    """
    UserFlow maps a user story to a detailed user interaction flow.

    Shows entry point, steps, decision points, and exit point.
    """

    id: str = Field(..., description="Unique flow identifier")
    user_story_id: str = Field(..., description="Related UserStory")
    persona_id: str = Field(..., description="Target persona")

    # Flow definition
    title: str = Field(..., description="Flow title")
    description: str = Field(..., description="Flow description")

    # Flow structure
    entry_point: str = Field(..., description="How user enters this flow")
    steps: List[FlowStep] = Field(..., description="Sequence of user actions")
    decision_points: List[DecisionPoint] = Field(default_factory=list)
    exit_point: str = Field(..., description="How flow ends / goal achieved")

    # Metadata
    complexity: str = Field(default="medium", description="Flow complexity")
    error_scenarios: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Agent that created this flow")

    def to_markdown(self) -> str:
        """Convert to Markdown."""
        lines = [
            f"### {self.title}",
            f"**Story:** {self.user_story_id} | **Persona:** {self.persona_id}",
            "",
            self.description,
            "",
            f"**Entry Point:** {self.entry_point}",
            "",
            "#### Steps",
        ]

        for step in self.steps:
            lines.append(f"{step.step_number}. {step.action}")
            lines.append(f"   → System: {step.system_response}")
            if step.screen_or_state:
                lines.append(f"   → Screen: {step.screen_or_state}")

        if self.decision_points:
            lines.extend(["", "#### Decision Points"])
            for dp in self.decision_points:
                lines.append(f"At step {dp.step_number}: {dp.question}")
                lines.append(f"- {dp.option_a}")
                lines.append(f"- {dp.option_b}")
                for opt in dp.other_options:
                    lines.append(f"- {opt}")

        lines.extend([
            "",
            f"**Exit Point:** {self.exit_point}",
        ])

        if self.error_scenarios:
            lines.extend(["", "#### Error Scenarios"])
            for error in self.error_scenarios:
                lines.append(f"- {error}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_story_id": self.user_story_id,
            "persona_id": self.persona_id,
            "title": self.title,
            "description": self.description,
            "entry_point": self.entry_point,
            "steps": [{"step_number": s.step_number, "action": s.action, "system_response": s.system_response, "screen_or_state": s.screen_or_state} for s in self.steps],
            "decision_points": [{"step_number": dp.step_number, "question": dp.question, "option_a": dp.option_a, "option_b": dp.option_b, "other_options": dp.other_options} for dp in self.decision_points],
            "exit_point": self.exit_point,
            "complexity": self.complexity,
            "error_scenarios": self.error_scenarios,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
