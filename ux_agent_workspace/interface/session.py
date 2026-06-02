"""In-memory + on-disk session state for the UX web interface.

A session represents one run of the UX LangGraph workflow triggered from the
browser: it takes the EM sprint plan, generates personas, user flows, and
wireframe briefs, pauses for human review, and on approval publishes a UX
handoff to the shared context store. The workflow runs in a background thread
(see workflow_runner.py); the session is the shared record the HTTP routes read.

Sessions are persisted to disk so they survive server restarts.  Call
`configure_persistence(directory)` once at startup, then use `get_session()`
instead of `sessions.get()` in route handlers.
"""

import json
import os
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

    def to_dict(self) -> Dict[str, Any]:
        """Full serialization for disk persistence."""
        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "status": self.status,
            "personas": self.personas,
            "user_flows": self.user_flows,
            "wireframe_briefs": self.wireframe_briefs,
            "a11y_flags": self.a11y_flags,
            "current_node": self.current_node,
            "completed_nodes": self.completed_nodes,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UXSessionState":
        session = cls(session_id=data["session_id"], session_name=data["session_name"])
        session.status = data.get("status", "running")
        session.personas = data.get("personas") or []
        session.user_flows = data.get("user_flows") or []
        session.wireframe_briefs = data.get("wireframe_briefs") or []
        session.a11y_flags = data.get("a11y_flags") or []
        session.current_node = data.get("current_node", "")
        session.completed_nodes = data.get("completed_nodes") or []
        session.error = data.get("error")
        created = data.get("created_at")
        session.created_at = datetime.fromisoformat(created) if created else datetime.utcnow()
        completed = data.get("completed_at")
        session.completed_at = datetime.fromisoformat(completed) if completed else None
        return session


# Module-level registry of all sessions for this process.
sessions: Dict[str, UXSessionState] = {}

# Persistence directory — set via configure_persistence() at startup.
_persist_dir: Optional[str] = None


def configure_persistence(sessions_dir: str) -> None:
    """Set the directory for session JSON files and create it if needed."""
    global _persist_dir
    os.makedirs(sessions_dir, exist_ok=True)
    _persist_dir = sessions_dir


def persist(session: UXSessionState) -> None:
    """Write session to disk (no-op if persistence not configured)."""
    if _persist_dir is None:
        return
    path = os.path.join(_persist_dir, f"{session.session_id}.json")
    try:
        with open(path, "w") as f:
            json.dump(session.to_dict(), f, indent=2)
    except Exception:
        pass


def get_session(session_id: str) -> Optional[UXSessionState]:
    """Return session from memory, loading from disk on cache miss."""
    if session_id in sessions:
        return sessions[session_id]
    if _persist_dir is None:
        return None
    path = os.path.join(_persist_dir, f"{session_id}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        session = UXSessionState.from_dict(data)
        sessions[session_id] = session
        return session
    except Exception:
        return None


def load_all_from_disk() -> None:
    """Load all persisted sessions into memory on startup."""
    if _persist_dir is None:
        return
    try:
        for fname in os.listdir(_persist_dir):
            if fname.endswith(".json"):
                sid = fname[:-5]
                if sid not in sessions:
                    get_session(sid)
    except Exception:
        pass
