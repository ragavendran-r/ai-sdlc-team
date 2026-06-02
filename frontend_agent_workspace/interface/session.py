"""In-memory session state for the Frontend web interface.

A session represents one run of the Frontend LangGraph workflow triggered from the
browser: it takes the UX handoff, generates scaffolded components, state plan,
a11y-enriched components, and test files, pauses for human review, and on approval
resumes to generate a PR description and code review output.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

SessionStatus = Literal[
    "running",
    "awaiting_review",
    "approved",
    "rejected",
    "error",
]

# Ordered node labels shown on the progress page. Keys are the LangGraph node
# names emitted by the workflow stream; values are the human-facing step labels.
PROGRESS_STEPS = [
    ("ux_handoff_intake", "Validating UX handoff"),
    ("component_breakdown", "Breaking down components"),
    ("design_token_mapping", "Mapping design tokens"),
    ("api_integration_planning", "Planning API integration"),
    ("component_scaffolding", "Scaffolding components"),
    ("state_management", "Planning state management"),
    ("accessibility_implementation", "Implementing accessibility"),
    ("unit_test_generation", "Generating tests"),
    ("pr_description", "Writing PR description"),
    ("code_review", "Reviewing code"),
]


@dataclass
class FrontendSessionState:
    """State for a single frontend implementation session."""

    session_id: str
    session_name: str

    status: SessionStatus = "running"

    # Workflow outputs populated when the workflow pauses for review.
    component_plan: List[Dict[str, Any]] = field(default_factory=list)
    scaffolded_components: List[Dict[str, Any]] = field(default_factory=list)
    a11y_enriched_components: List[Dict[str, Any]] = field(default_factory=list)
    test_files: List[Dict[str, Any]] = field(default_factory=list)
    state_plan: Optional[Dict[str, Any]] = None
    token_gaps: List[str] = field(default_factory=list)
    intake_gaps: List[str] = field(default_factory=list)
    review_comments: List[Dict[str, Any]] = field(default_factory=list)
    pr_description: str = ""

    # Progress tracking driven by the workflow stream.
    current_node: str = ""
    completed_nodes: List[str] = field(default_factory=list)
    error: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def to_status_dict(self) -> Dict[str, Any]:
        """Serialize the fields polled by the progress page."""
        return {
            "status": self.status,
            "current_node": self.current_node,
            "completed_nodes": self.completed_nodes,
            "error": self.error,
        }


# Module-level registry of all sessions for this process.
sessions: Dict[str, FrontendSessionState] = {}
