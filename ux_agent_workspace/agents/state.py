"""State definitions for UX Agent workflow."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from team_contracts.schemas import (
    UserStory,
    UXHandoff,
    UserPersona,
    UserFlow,
    IAStructure,
    WireframeBrief,
    DesignComplianceReport,
    AccessibilityFlag,
)


@dataclass
class UXWorkflowState:
    """Complete state for UX Agent workflow."""

    # Phase 1: Story Intake
    input_stories: List[UserStory] = field(default_factory=list)
    ux_relevant_stories: List[UserStory] = field(default_factory=list)
    excluded_stories: List[str] = field(default_factory=list)

    # Phase 2: Persona Generation
    personas: List[UserPersona] = field(default_factory=list)

    # Phase 3: User Flow Mapping
    user_flows: List[UserFlow] = field(default_factory=list)

    # Phase 4: Information Architecture
    ia_structure: Optional[IAStructure] = None

    # Phase 5: Wireframe Briefs
    wireframe_briefs: List[WireframeBrief] = field(default_factory=list)

    # Phase 6: Design System Compliance
    compliance_report: Optional[DesignComplianceReport] = None
    updated_wireframe_briefs: List[WireframeBrief] = field(default_factory=list)

    # Phase 7: Accessibility Review
    a11y_flags: List[AccessibilityFlag] = field(default_factory=list)

    # Phase 8: Human Checkpoint
    checkpoint_reached: bool = False
    briefs_approved: bool = False
    approval_feedback: str = ""

    # Phase 9: Figma Annotation
    figma_frames_created: List[str] = field(default_factory=list)
    figma_annotations_added: List[str] = field(default_factory=list)

    # Phase 10: Handoff Spec
    ux_handoff: Optional[UXHandoff] = None
    handoff_written: bool = False

    # Metadata
    workflow_start: datetime = field(default_factory=datetime.utcnow)
    current_agent: str = ""
    messages: List[Dict[str, str]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Web mode: when True the human_checkpoint node does not block on input();
    # the web layer injects the decision via update_state before resuming.
    web_mode: bool = False

    def add_message(self, agent: str, message: str) -> None:
        """Add a message to the workflow log."""
        self.messages.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "message": message,
        })

    def add_error(self, error: str) -> None:
        """Record an error in the workflow."""
        self.errors.append(f"[{datetime.utcnow().isoformat()}] {error}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "input_stories": [s.to_dict() for s in self.input_stories],
            "ux_relevant_stories": [s.to_dict() for s in self.ux_relevant_stories],
            "excluded_stories": self.excluded_stories,
            "personas": [p.to_dict() for p in self.personas],
            "user_flows": [f.to_dict() for f in self.user_flows],
            "ia_structure": self.ia_structure.to_dict() if self.ia_structure else None,
            "wireframe_briefs": [b.to_dict() for b in self.wireframe_briefs],
            "compliance_report": self.compliance_report.to_dict() if self.compliance_report else None,
            "updated_wireframe_briefs": [b.to_dict() for b in self.updated_wireframe_briefs],
            "a11y_flags": [f.to_dict() for f in self.a11y_flags],
            "checkpoint_reached": self.checkpoint_reached,
            "briefs_approved": self.briefs_approved,
            "approval_feedback": self.approval_feedback,
            "figma_frames_created": self.figma_frames_created,
            "figma_annotations_added": self.figma_annotations_added,
            "ux_handoff": self.ux_handoff.to_dict() if self.ux_handoff else None,
            "handoff_written": self.handoff_written,
            "workflow_start": self.workflow_start.isoformat(),
            "current_agent": self.current_agent,
            "messages": self.messages,
            "errors": self.errors,
            "web_mode": self.web_mode,
        }
