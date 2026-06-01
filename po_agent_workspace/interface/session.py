"""In-memory session state for the PO web interface.

A session represents one run of the PO LangGraph workflow triggered from the
browser. The workflow runs in a background thread (see workflow_runner.py); the
session is the shared record the HTTP routes read to render progress and review
pages.
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
    ("requirements_extraction", "Extracting requirements"),
    ("ambiguity_detection", "Detecting ambiguities"),
    ("conflict_detection", "Checking for conflicts"),
    ("story_generation", "Generating user stories"),
    ("acceptance_criteria", "Writing acceptance criteria"),
    ("prioritization", "Prioritizing backlog"),
]


@dataclass
class SessionState:
    """State for a single PO requirements session."""

    session_id: str
    session_name: str
    source_type: str
    raw_input: str

    status: SessionStatus = "running"

    # Outputs populated when the workflow pauses for review.
    generated_stories: List[Dict[str, Any]] = field(default_factory=list)
    ambiguity_flags: List[str] = field(default_factory=list)
    conflict_flags: List[str] = field(default_factory=list)

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
sessions: Dict[str, SessionState] = {}
