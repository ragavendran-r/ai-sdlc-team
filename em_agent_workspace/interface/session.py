"""In-memory session state for the EM web interface.

A session represents one run of the EM LangGraph workflow triggered from the
browser: it takes the PO backlog, plans a sprint, pauses for human review of the
draft sprint, and on approval publishes a sprint plan to the shared context
store. The workflow runs in a background thread (see workflow_runner.py); the
session is the shared record the HTTP routes read to render progress and review.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

SessionStatus = Literal[
    "running",
    "awaiting_review",
    "approved",
    "rejected",
    "monitoring",
    "error",
]

# Ordered node labels shown on the progress page. Keys are the LangGraph node
# names emitted by the workflow stream; values are the human-facing step labels.
PROGRESS_STEPS = [
    ("backlog_intake", "Validating backlog"),
    ("dependency_mapping", "Mapping dependencies"),
    ("capacity_analysis", "Analyzing capacity"),
    ("risk_assessment", "Assessing risks"),
    ("sprint_composition", "Composing sprint"),
    ("definition_of_done", "Defining Done"),
]


@dataclass
class EMSessionState:
    """State for a single EM sprint-planning session."""

    session_id: str
    session_name: str
    sprint_goal: str

    status: SessionStatus = "running"

    # Outputs populated when the workflow pauses for review.
    draft_sprint: Optional[Dict[str, Any]] = None
    capacity_report: Optional[Dict[str, Any]] = None
    risk_flags: List[str] = field(default_factory=list)

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
sessions: Dict[str, EMSessionState] = {}
