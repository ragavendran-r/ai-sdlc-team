"""In-memory session state for the UX web interface.

A session represents one run of the UX LangGraph workflow triggered from the
browser: it takes the EM sprint plan, generates personas, user flows, and
wireframe briefs, pauses for human review, and on approval publishes a UX
handoff to the shared context store. The workflow runs in a background thread
(see workflow_runner.py); the session is the shared record the HTTP routes read.
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
    ("story_intake", "Filtering UX stories"),
    ("persona_agent", "Generating personas"),
    ("user_flow_mapping", "Mapping user flows"),
    ("information_architecture", "Building IA"),
    ("wireframe_brief", "Drafting wireframe briefs"),
    ("design_system_compliance", "Checking design system"),
    ("accessibility_review", "Reviewing accessibility"),
]


@dataclass
class UXSessionState:
    """State for a single UX design session."""

    session_id: str
    session_name: str

    status: SessionStatus = "running"

    # Outputs populated when the workflow pauses for review.
    personas: List[Dict[str, Any]] = field(default_factory=list)
    user_flows: List[Dict[str, Any]] = field(default_factory=list)
    wireframe_briefs: List[Dict[str, Any]] = field(default_factory=list)
    a11y_flags: List[str] = field(default_factory=list)

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
sessions: Dict[str, UXSessionState] = {}
